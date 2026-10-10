# Rehearse the phone's first run against the live DSH instance, then clean up after ourselves.
#
#   1. ask DSH for the public base url and mint a one-time pairing link (loopback only)
#   2. check the app's own parser (PairLinks) against that link
#   3. redeem it from the public side and confirm the credential unlocks /pair-app
#   4. revoke the throwaway device and confirm the device count is back where it started
#
# The throwaway device is never left behind: step 4 runs even if step 3 fails.
$ErrorActionPreference = 'Stop'

$root  = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$curl  = Join-Path $env:SystemRoot 'System32\curl.exe'
$dsh   = if ($env:DSH_WEB_URL) { $env:DSH_WEB_URL } else { 'http://127.0.0.1:19387' }
$py    = 'C:\Users\Zora\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$work  = Join-Path $env:TEMP 'pair-e2e'
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $work | Out-Null

function Get-DeviceCount([string]$publicUrl) {
    $raw = & $curl -s --noproxy '*' "$dsh/api/pair/status" | ConvertFrom-Json
    return [int]$raw.deviceCount
}

$status = & $curl -s --noproxy '*' "$dsh/api/pair/status" | ConvertFrom-Json
$publicUrl = $status.publicUrl
if (-not $publicUrl) { throw 'DSH reported no publicUrl - start the relay first' }
$publicHost = ([Uri]$publicUrl).Host
$before = [int]$status.deviceCount
Write-Host "public url : $publicUrl"
Write-Host "devices    : $before"
Write-Host ''

Write-Host '=== 1. mint a one-time pairing link (loopback) ==='
$body = Join-Path $work 'issue.json'
[IO.File]::WriteAllText($body, '{}')
$issue = (& $curl -s --noproxy '*' -X POST -H 'content-type: application/json' --data-binary "@$body" "$dsh/api/pair/issue") | ConvertFrom-Json
if (-not $issue.ok) { throw "POST /api/pair/issue failed: $($issue | ConvertTo-Json -Compress)" }
Write-Host "link       : $($issue.url)"

$jar = Join-Path $work 'pair.cookies'
$deviceId = $null
try {
    Write-Host ''
    Write-Host '=== 2. the app parser vs the real link ==='
    $cls = Join-Path $work 'classes'
    & javac -encoding UTF-8 -d $cls "$root\java\com\dsh\phone\PairLinks.java" "$root\tools\PairLinkCheck.java"
    if ($LASTEXITCODE -ne 0) { throw 'javac failed' }
    & java -cp $cls com.dsh.phone.PairLinkCheck $issue.url $publicHost
    if ($LASTEXITCODE -ne 0) { throw 'the app would not accept this link' }
    Write-Host ''
    Write-Host '=== 3. redeem it from the public side ==='
    $code = (& $curl -s --noproxy '*' -c $jar -L -o (Join-Path $work 'landing.html') `
        -w '%{http_code} %{size_download} %{url_effective}' $issue.url)
    Write-Host "redirect   : $code"
    foreach ($line in (Get-Content $jar)) {
        # curl prefixes HttpOnly cookies with "#HttpOnly_" - those are real entries, not comments.
        if ($line.StartsWith('#') -and -not $line.StartsWith('#HttpOnly_')) { continue }
        if (-not $line.Trim()) { continue }
        $parts = $line -split "`t"
        if ($parts.Count -ge 7 -and $parts[5] -eq 'dsh_pair') { $deviceId = $parts[6] }
    }
    if (-not $deviceId) { throw "no dsh_pair cookie was issued (jar: $jar)" }
    Write-Host "device id  : $deviceId" -ForegroundColor Green
    $unlock = & $curl -s --noproxy '*' -H "Cookie: dsh_pair=$deviceId" -o NUL -w '%{http_code} %{size_download}' "$publicUrl/pair-app"
    Write-Host "pair-app   : $unlock (device credential)"
    if ($unlock -notmatch '^200 4') { throw "the issued credential does not unlock $publicUrl/pair-app" }
}
finally {
    Write-Host ''
    Write-Host '=== 4. revoke the throwaway device ==='
    if ($deviceId) {
        # PowerShell mangles inline JSON quotes when passing arguments to curl, so use a file.
        $revokeFile = Join-Path $work 'revoke.json'
        [IO.File]::WriteAllText($revokeFile, "{`"deviceId`":`"$deviceId`"}")
        $revoke = (& $curl -s --noproxy '*' -X POST -H 'content-type: application/json' `
            --data-binary "@$revokeFile" "$dsh/api/pair/revoke") | ConvertFrom-Json
        Write-Host "revoke     : $($revoke | ConvertTo-Json -Compress)"
        if (-not $revoke.ok) { Write-Host 'WARNING: revoke did not report ok' -ForegroundColor Yellow }
    } else {
        Write-Host 'nothing to revoke (no credential was issued)'
    }
    $after = Get-DeviceCount $publicUrl
    Write-Host "devices    : $before -> $after"
    if ($after -ne $before) { Write-Host 'WARNING: device count did not return to its starting value' -ForegroundColor Yellow }
}
