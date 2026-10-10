# Pick a Clash (mihomo) global node that can actually reach GitHub, and switch to it.
#
# Why: the current node answers google/npm/gitee but not github.com, so publishing to GitHub fails
# with a bare "000". Clash Verge exposes no TCP control port on this machine
# (`external-controller: ''`), only the named pipe `\\.\pipe\verge-mihomo`, so this script talks
# HTTP/1.1 over that pipe.
#
#   .\clash_github_node.ps1              # test the group, switch to the fastest GitHub-capable node
#   .\clash_github_node.ps1 -List        # only list what the group tested, change nothing
#   .\clash_github_node.ps1 -Pick <name> # switch to an explicit node
#   .\clash_github_node.ps1 -Restore     # switch back to the node recorded before the last switch
[CmdletBinding()]
param(
    [switch]$List,
    [string]$Pick,
    [switch]$Restore,
    [string]$Group = 'GLOBAL',
    [string]$ProbeUrl = 'https://api.github.com/',
    [int]$TimeoutMs = 6000
)
$ErrorActionPreference = 'Stop'
$pipeName = 'verge-mihomo'
$secret = 'set-your-secret'
$stateFile = Join-Path $PSScriptRoot '.clash-node-before.txt'

function Invoke-Mihomo {
    param([string]$Method, [string]$Path, [string]$Body)
    # The pipe needs byte-exact framing: a StreamReader.ReadToEnd() returns early (the server does
    # not close the pipe for you), so read the header byte-wise, honour Content-Length, and decode
    # the body as UTF-8 (node names contain emoji, i.e. multi-byte characters).
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
    $pipe.Connect(5000)
    $head = "$Method $Path HTTP/1.1`r`nHost: localhost`r`nAuthorization: Bearer $secret`r`nConnection: close`r`n"
    $payload = $null
    if ($Body) {
        $payload = [System.Text.Encoding]::UTF8.GetBytes($Body)
        $head += "Content-Type: application/json`r`nContent-Length: $($payload.Length)`r`n"
    }
    $head += "`r`n"
    $bytes = [System.Text.Encoding]::ASCII.GetBytes($head)
    $pipe.Write($bytes, 0, $bytes.Length)
    if ($payload) { $pipe.Write($payload, 0, $payload.Length) }
    $pipe.Flush()

    $header = New-Object System.Collections.Generic.List[byte]
    $one = New-Object byte[] 1
    while ($true) {
        $n = $pipe.Read($one, 0, 1)
        if ($n -le 0) { break }
        $header.Add($one[0])
        $c = $header.Count
        if ($c -ge 4 -and $header[$c - 4] -eq 13 -and $header[$c - 3] -eq 10 -and $header[$c - 2] -eq 13 -and $header[$c - 1] -eq 10) { break }
    }
    $headerText = [System.Text.Encoding]::ASCII.GetString($header.ToArray())
    if ($headerText -match '^HTTP/1\.1\s+(\d+)') {
        $code = [int]$Matches[1]
        if ($code -ne 200) { $pipe.Dispose(); throw "mihomo returned HTTP $code for $Method $Path" }
    }
    $len = 0
    if ($headerText -match '(?im)^Content-Length:\s*(\d+)') { $len = [int]$Matches[1] }
    if ($len -le 0) { $pipe.Dispose(); return $null }
    $body = New-Object byte[] $len
    $got = 0
    while ($got -lt $len) {
        $n = $pipe.Read($body, $got, $len - $got)
        if ($n -le 0) { break }
        $got += $n
    }
    $pipe.Dispose()
    if ($got -le 0) { return $null }
    return ([System.Text.Encoding]::UTF8.GetString($body, 0, $got) | ConvertFrom-Json)
}

$group = Invoke-Mihomo -Method GET -Path "/proxies/$Group"
if (-not $group) { throw "could not read group $Group over the named pipe" }
Write-Host "group $Group : now = $($group.now) ; $($group.all.Count) entries"

if ($Restore) {
    if (-not (Test-Path $stateFile)) { throw "no recorded previous node at $stateFile" }
    $prev = (Get-Content $stateFile -Raw).Trim()
    Invoke-Mihomo -Method PUT -Path "/proxies/$Group" -Body (@{ name = $prev } | ConvertTo-Json -Compress) | Out-Null
    Write-Host "restored to $prev"
    return
}

if ($Pick) {
    if (-not (Test-Path $stateFile)) { $group.now | Set-Content $stateFile -NoNewline -Encoding ASCII }
    Invoke-Mihomo -Method PUT -Path "/proxies/$Group" -Body (@{ name = $Pick } | ConvertTo-Json -Compress) | Out-Null
    Write-Host "switched $Group -> $Pick"
    return
}

Write-Host "probing $($group.all.Count) nodes against $ProbeUrl (timeout ${TimeoutMs}ms) ..."
$encoded = [uri]::EscapeDataString($ProbeUrl)
$result = Invoke-Mihomo -Method GET -Path "/group/$Group/delay?url=$encoded&timeout=$TimeoutMs"
if (-not $result) { throw "group delay probe returned nothing" }

$ok = @()
foreach ($p in $result.PSObject.Properties) {
    if ($p.Value -is [int] -or $p.Value -is [long] -or $p.Value -is [double]) {
        $ok += [pscustomobject]@{ node = $p.Name; delay = [int]$p.Value }
    } else {
        Write-Host ("  fail  {0,-42} {1}" -f $p.Name, $p.Value.message)
    }
}
if ($ok.Count -eq 0) { throw "no node in $Group can reach $ProbeUrl" }
$ok = $ok | Sort-Object delay
$ok | ForEach-Object { Write-Host ("  ok    {0,-42} {1} ms" -f $_.node, $_.delay) }

if ($List) { Write-Host "(-List: nothing switched)"; return }
$best = $ok[0].node
if (-not (Test-Path $stateFile)) { $group.now | Set-Content $stateFile -NoNewline -Encoding ASCII }
Invoke-Mihomo -Method PUT -Path "/proxies/$Group" -Body (@{ name = $best } | ConvertTo-Json -Compress) | Out-Null
Write-Host "switched $Group -> $best ($($ok[0].delay) ms) ; previous node saved in $stateFile"
