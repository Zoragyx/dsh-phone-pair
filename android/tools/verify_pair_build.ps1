[CmdletBinding()]
param(
    # Where the shell (and, unless -Loopback, the reference bytes) are fetched from. Defaults to the
    # local webserver: the public relay answers long responses with 530/truncation, and the recorded
    # absolute URLs in index.txt only differ by origin anyway (AssetIndex.canonical ignores it).
    [string]$Base = 'http://127.0.0.1:19387',
    # Fetch each packaged asset from the local webserver instead of $Base.
    [switch]$Loopback
)
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Zora\Documents\deepseek-harness\default-workspace\dsh-phone-pair'
$py   = 'C:\Users\Zora\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$apk  = "$root\artifacts\dsh-phone-pair-1.0.apk"
$cookie = (Get-Content "$root\device-id.txt" -Raw).Trim()
$loopArgs = @()
if ($Loopback) { $loopArgs = @('--loopback') }
Write-Host "base: $Base"

Write-Host '=== 1. extract index.txt from the apk ==='
$idxDir = Join-Path $env:TEMP 'pair-verify'
Remove-Item $idxDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $idxDir -Force | Out-Null
& $py -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); open(sys.argv[2],'wb').write(z.read('assets/web/index.txt'))" $apk "$idxDir\index.txt"
Write-Host ("index.txt bytes: " + (Get-Item "$idxDir\index.txt").Length)

Write-Host ''
Write-Host '=== 2. unit tests ==='
$t1 = Join-Path $env:TEMP 'pair-t1'; Remove-Item $t1 -Recurse -Force -ErrorAction SilentlyContinue
& javac -encoding UTF-8 -d $t1 "$root\java\com\dsh\phone\PairLinks.java" "$root\test\com\dsh\phone\PairLinksTest.java"
& java -cp $t1 com.dsh.phone.PairLinksTest
$t2 = Join-Path $env:TEMP 'pair-t2'; Remove-Item $t2 -Recurse -Force -ErrorAction SilentlyContinue
& javac -encoding UTF-8 -d $t2 "$root\java\com\dsh\phone\AssetIndex.java" "$root\test\com\dsh\phone\AssetIndexTest.java"
& java -cp $t2 com.dsh.phone.AssetIndexTest

Write-Host ''
Write-Host '=== 3. real shell urls vs the packaged index ==='
& $py "$root\tools\shell_urls.py" --base $Base --cookie $cookie --out "$idxDir\urls.txt"
$t3 = Join-Path $env:TEMP 'pair-t3'; Remove-Item $t3 -Recurse -Force -ErrorAction SilentlyContinue
& javac -encoding UTF-8 -d $t3 "$root\java\com\dsh\phone\AssetIndex.java" "$root\tools\IndexMatchCheck.java"
& java -cp $t3 com.dsh.phone.IndexMatchCheck "$idxDir\index.txt" "$idxDir\urls.txt"

Write-Host ''
Write-Host '=== 4. packaged assets vs the server, byte for byte ==='
& $py "$root\tools\verify_bundled_assets.py" --apk $apk --base $Base --cookie $cookie @loopArgs
Write-Host "verify exit=$LASTEXITCODE"
