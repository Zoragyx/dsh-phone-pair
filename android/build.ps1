<#
    Build the DSH phone app APK without Gradle.

    Uses only the Android SDK build-tools (aapt2 / d8 / zipalign / apksigner) and a JDK:
      aapt2 compile -> aapt2 link -> javac -> d8 -> add classes.dex -> zipalign -> apksigner

    This is the *pairing-mode* build: no relay host and no device credential are compiled into the
    APK. The credential minted below is only used to download the client assets that get bundled
    (a pairing cookie is needed to fetch /pair-app once); the user's own phone learns its computer
    from the pairing link they paste at first run.
#>
[CmdletBinding()]
param(
    # Mint a brand new pairing credential instead of reusing device-id.txt.
    [switch]$Repair,
    # Use an explicit device id (skips minting entirely).
    [string]$DeviceId,
    # Keep the intermediate build directory.
    [switch]$KeepWork,
    # Where the bundled client assets are fetched from. Defaults to the public relay; pass the
    # local webserver (http://127.0.0.1:19387) to build even while the relay is unreachable.
    [string]$AssetsBase
)

$ErrorActionPreference = 'Stop'

$root       = $PSScriptRoot
$sdk        = 'C:\Users\Zora\Android\Sdk'
# build-tools 34.0.0 ships a broken R8/D8 dev build that dies with
# "NullPointerException: Cannot invoke String.length() because <parameter1> is null"
# on any class that implements/extends a library type. 35.0.1 works.
$buildTools = Join-Path $sdk 'build-tools\35.0.1'
$androidJar = Join-Path $sdk 'platforms\android-34\android.jar'
$work       = Join-Path $root 'build'
$artifacts  = Join-Path $root 'artifacts'
$dshUrl     = 'http://127.0.0.1:19387'
$curl       = Join-Path $env:SystemRoot 'System32\curl.exe'
$python     = 'C:\Users\Zora\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'

foreach ($tool in @(
        (Join-Path $buildTools 'aapt2.exe'),
        (Join-Path $buildTools 'd8.bat'),
        (Join-Path $buildTools 'zipalign.exe'),
        (Join-Path $buildTools 'apksigner.bat'),
        $androidJar, $curl, $python)) {
    if (-not (Test-Path $tool)) { throw "missing required tool: $tool" }
}

$javac   = (Get-Command javac).Source
$keytool = if (Test-Path "$env:JAVA_HOME\bin\keytool.exe") { "$env:JAVA_HOME\bin\keytool.exe" } else { (Get-Command keytool).Source }

function Invoke-Step {
    param([string]$Label, [scriptblock]$Body)
    Write-Host "==> $Label" -ForegroundColor Cyan
    & $Body
    if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

# ------------------------------------------------------------------ workspace

if ((Test-Path $work) -and -not $KeepWork) { Remove-Item $work -Recurse -Force }
foreach ($d in 'gen', 'classes', 'dex', 'res', 'libs') {
    New-Item -ItemType Directory -Force (Join-Path $work $d) | Out-Null
}
New-Item -ItemType Directory -Force $artifacts | Out-Null

# ------------------------------------------------------------------ pairing credential

function Get-PublicBaseUrl {
    $raw = & $curl -s --noproxy '*' "$dshUrl/api/pair/status"
    $status = $raw | ConvertFrom-Json
    if (-not $status.publicUrl) {
        throw "DSH did not report a publicUrl - is the remote-web-ui relay running? ($raw)"
    }
    return $status.publicUrl
}

function New-PairingDevice {
    Write-Host "==> minting a new pairing credential from $dshUrl" -ForegroundColor Cyan
    $bodyFile = Join-Path $work 'issue.json'
    [IO.File]::WriteAllText($bodyFile, '{}')
    $raw = & $curl -s --noproxy '*' -X POST -H 'content-type: application/json' `
        --data-binary "@$bodyFile" "$dshUrl/api/pair/issue"
    $issue = $raw | ConvertFrom-Json
    if (-not $issue.ok) { throw "POST /api/pair/issue failed: $raw" }

    $jar = Join-Path $work 'pair.cookies'
    & $curl -s --noproxy '*' -c $jar -o NUL $issue.url | Out-Null

    $value = $null
    foreach ($line in (Get-Content $jar)) {
        # curl prefixes HttpOnly cookies with "#HttpOnly_" - those are real entries, not comments.
        if ($line.StartsWith('#') -and -not $line.StartsWith('#HttpOnly_')) { continue }
        if (-not $line.Trim()) { continue }
        $parts = $line -split "`t"
        if ($parts.Count -ge 7 -and $parts[5] -eq 'dsh_pair') { $value = $parts[6] }
    }
    if (-not $value) { throw "pairing succeeded but no dsh_pair cookie was captured in $jar" }
    Write-Host "    device id: $value" -ForegroundColor Green
    return $value
}

function Test-DeviceId {
    param([string]$Id)
    if (-not $Id) { return $false }
    $raw = & $curl -s --noproxy '*' -H "Cookie: dsh_pair=$Id" -o NUL -w '%{http_code} %{size_download}' `
        "$publicUrl/pair-app"
    return ($raw -match '^200 4')
}

$publicUrl  = Get-PublicBaseUrl
$publicHost = ([Uri]$publicUrl).Host
Write-Host "public base url: $publicUrl" -ForegroundColor Green

# The assets only have to come from *a* copy of this webserver: AssetIndex.canonical() ignores the
# origin, so the phone's https request for /assets/x.js still matches an entry recorded as
# http://127.0.0.1:19387/assets/x.js. Bundling over loopback is therefore both correct and immune to
# the relay's 530s/truncation (which is what the fixed domain returns for long responses).
$assetsBase = if ($AssetsBase) { $AssetsBase.TrimEnd('/') } else { $publicUrl }
$assetsHost = ([Uri]$assetsBase).Host
$useRelay   = ($assetsBase -eq $publicUrl)
Write-Host "assets base: $assetsBase" -ForegroundColor Green

$idFile = Join-Path $root 'device-id.txt'
if (-not $DeviceId -and -not $Repair -and (Test-Path $idFile)) {
    $DeviceId = (Get-Content $idFile -Raw).Trim()
}
if ($DeviceId) {
    Write-Host "reusing device id $DeviceId"
    if (-not $useRelay) {
        # Assets come from the local webserver, so the credential is only a cookie for /pair-app;
        # never re-mint one (and spend a device slot) just because the relay is unreachable.
        Write-Host "    relay check skipped (assets base is $assetsBase)" -ForegroundColor Yellow
    } elseif (-not (Test-DeviceId $DeviceId)) {
        Write-Host "    credential no longer valid - minting a fresh one" -ForegroundColor Yellow
        $DeviceId = $null
    }
}
if (-not $DeviceId) { $DeviceId = New-PairingDevice }
Set-Content -Path $idFile -Value $DeviceId -NoNewline

if ($useRelay -and -not (Test-DeviceId $DeviceId)) { throw "device id $DeviceId does not unlock $publicUrl/pair-app" }
Write-Host "pairing credential ready for asset fetches from $assetsBase" -ForegroundColor Green

# ------------------------------------------------------------------ generated config

$appConfig = Join-Path $work 'AppConfig.java'
$appConfigSrc = @"
package com.dsh.phone;

/**
 * Generated by build.ps1 - do not edit by hand.
 *
 * <p>Pairing-mode build: nothing about a specific computer is compiled in. The relay host and the
 * device credential are learned at runtime from the pairing link the user pastes, and stored on the
 * phone (LockStore#setSite / #setCredential).
 */
final class AppConfig {
    /** Relay this APK was built against - used to fetch the bundled client assets, not at runtime. */
    static final String BUILD_RELAY = "$publicUrl";

    private AppConfig() {
    }
}
"@
[IO.File]::WriteAllText($appConfig, $appConfigSrc)

# ------------------------------------------------------------------ bundled web assets

# The client shell references ~28 MB of content-hashed bundles (two eager plugins/??<modules>
# combos, the lazy module URLs in __DSH_BOOT__, assets/*.js|css). Shipping them inside the APK
# turns a slow first load into an instant one; MainActivity serves them locally and anything the
# desktop has since rebuilt simply falls through to the network. /.webmcp/bridge.js is deliberately
# left out (its URL has no content hash; see tools/bundle_web_assets.py).
$assetsDir = Join-Path $work 'assets'
$webDir = Join-Path $assetsDir 'web'
New-Item -ItemType Directory -Force $webDir | Out-Null
$savedProxy = $env:NO_PROXY
$env:NO_PROXY = "$assetsHost,$($assetsHost -replace '^[^.]+\.', '')"
Invoke-Step 'bundle web assets' {
    & $python (Join-Path $root 'tools\bundle_web_assets.py') `
        --base $assetsBase --cookie $DeviceId --out $webDir
}
$env:NO_PROXY = $savedProxy
$bundledBytes = (Get-ChildItem $webDir -File | Measure-Object -Property Length -Sum).Sum
Write-Host ("    bundled {0:N1} MB into {1}" -f ($bundledBytes / 1MB), $webDir) -ForegroundColor Green

# ------------------------------------------------------------------ resources

Invoke-Step 'aapt2 compile' {
    & (Join-Path $buildTools 'aapt2.exe') compile --dir (Join-Path $root 'res') -o (Join-Path $work 'res\res.zip')
}

Invoke-Step 'aapt2 link' {
    & (Join-Path $buildTools 'aapt2.exe') link `
        -o (Join-Path $work 'base.apk') `
        -I $androidJar `
        -A $assetsDir `
        --manifest (Join-Path $root 'AndroidManifest.xml') `
        -R (Join-Path $work 'res\res.zip') `
        --java (Join-Path $work 'gen') `
        --min-sdk-version 26 `
        --target-sdk-version 34 `
        --version-code 1 `
        --version-name 1.0
}

# ------------------------------------------------------------------ java -> dex

$sources = @()
$sources += Get-ChildItem (Join-Path $root 'java') -Recurse -Filter *.java | ForEach-Object { $_.FullName }
$sources += Get-ChildItem (Join-Path $work 'gen') -Recurse -Filter *.java | ForEach-Object { $_.FullName }
$sources += $appConfig
Write-Host "==> javac ($($sources.Count) sources)" -ForegroundColor Cyan
# javac writes its "uses a deprecated API" note on stderr; with $ErrorActionPreference='Stop'
# PowerShell turns that note into a terminating error, so relax it for the native call only.
$savedEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$javacLog = & $javac -encoding UTF-8 -nowarn -source 8 -target 8 `
    -bootclasspath "$androidJar;$(Join-Path $buildTools 'core-lambda-stubs.jar')" `
    -d (Join-Path $work 'classes') @sources 2>&1
$javacCode = $LASTEXITCODE
$ErrorActionPreference = $savedEap
if ($javacCode -ne 0) {
    $javacLog | ForEach-Object { Write-Host $_ }
    throw "javac failed with exit code $javacCode"
}

$classes = Get-ChildItem (Join-Path $work 'classes') -Recurse -Filter *.class | ForEach-Object { $_.FullName }
Write-Host "==> d8 ($($classes.Count) classes)" -ForegroundColor Cyan
& (Join-Path $buildTools 'd8.bat') --lib $androidJar `
    --lib (Join-Path $buildTools 'core-lambda-stubs.jar') `
    --min-api 26 --output (Join-Path $work 'dex') @classes
if ($LASTEXITCODE -ne 0) { throw "d8 failed with exit code $LASTEXITCODE" }

# ------------------------------------------------------------------ package / align / sign

$dex = Join-Path $work 'dex\classes.dex'
if (-not (Test-Path $dex)) { throw "d8 produced no classes.dex" }

Write-Host '==> adding classes.dex to the resource apk' -ForegroundColor Cyan
& $python (Join-Path $root 'tools\add_dex.py') (Join-Path $work 'base.apk') $dex (Join-Path $work 'packed.apk')
if ($LASTEXITCODE -ne 0) { throw "add_dex failed with exit code $LASTEXITCODE" }

Invoke-Step 'zipalign' {
    & (Join-Path $buildTools 'zipalign.exe') -f -p 4 (Join-Path $work 'packed.apk') (Join-Path $work 'aligned.apk')
}

$keystore = Join-Path $root 'keystore\dsh-phone.jks'
if (-not (Test-Path $keystore)) {
    Write-Host '==> creating the signing keystore' -ForegroundColor Cyan
    New-Item -ItemType Directory -Force (Split-Path $keystore) | Out-Null
    & $keytool -genkeypair -keystore $keystore -storepass dshphone -keypass dshphone `
        -alias dshphone -keyalg RSA -keysize 2048 -validity 10950 `
        -dname 'CN=DSH Phone, OU=Personal, O=DSH Phone, L=Local, ST=Local, C=CN'
    if ($LASTEXITCODE -ne 0) { throw "keytool failed with exit code $LASTEXITCODE" }
}

$apk = Join-Path $artifacts 'dsh-phone-pair-1.0.apk'
if (Test-Path $apk) { Remove-Item $apk -Force }
Invoke-Step 'apksigner sign' {
    & (Join-Path $buildTools 'apksigner.bat') sign `
        --ks $keystore --ks-pass pass:dshphone --key-pass pass:dshphone --ks-key-alias dshphone `
        --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true `
        --out $apk (Join-Path $work 'aligned.apk')
}

Invoke-Step 'apksigner verify' {
    & (Join-Path $buildTools 'apksigner.bat') verify --print-certs $apk
}

if (-not $KeepWork) { Remove-Item $work -Recurse -Force }

$size = [math]::Round((Get-Item $apk).Length / 1KB, 1)
Write-Host ""
Write-Host "built: $apk ($size KB)" -ForegroundColor Green
Write-Host "pairing-mode build: no credential baked in (assets fetched from $assetsBase)" -ForegroundColor Green
