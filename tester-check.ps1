# tester-check.ps1 —— DSH 手机版「连不上」电脑端自检（只读，不改任何设置，不需要管理员）
# 用法：把本文件拷到测试员电脑上，右键 PowerShell 运行：
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\tester-check.ps1
# 报告会打印在屏幕上，同时保存到桌面 dsh-tester-check.txt，整段发给作者即可。

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'
$script:lines = New-Object System.Collections.Generic.List[string]

function Say([string]$s) { $script:lines.Add($s); Write-Host $s }
function HttpCode([string]$url, [bool]$useProxy) {
  $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
  if (-not $curl) { return 'curl-na' }
  $curlArgs = @('-s', '-o', 'NUL', '-m', '12', '-w', '%{http_code}')
  if (-not $useProxy) { $curlArgs += '--noproxy'; $curlArgs += '*' }
  $code = & curl.exe @curlArgs $url 2>$null
  if (-not $code) { return '000' }
  return $code
}

Say "==== DSH 手机版 · 电脑端配对自检 ===="
Say "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')    用户: $env:USERNAME    机器: $env:COMPUTERNAME"
Say ""

Say "--- 1) DSH Web 是否在监听 19387 ---"
$listens = Get-NetTCPConnection -LocalPort 19387 -State Listen -ErrorAction SilentlyContinue
if (-not $listens) {
  Say "[X] 没有进程监听 19387 —— 此刻 DSH 没在跑，或者它换了端口"
  Say "    >>> 请先打开 DSH 桌面 App（面板里能看到二维码），再重新跑一次本脚本 <<<"
  $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '(?i)dsh|electron|cloudflared' }
  if ($procs) {
    Say "    不过发现了这些相关进程（DSH 可能开着，只是端口不同）："
    foreach ($p in ($procs | Select-Object -First 8)) { Say ("      {0}  pid={1}" -f $p.ProcessName, $p.Id) }
    $ports = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $procs.Id -contains $_.OwningProcess }
    foreach ($lp in ($ports | Select-Object -First 12)) { Say ("      监听 {0}:{1}  pid={2}" -f $lp.LocalAddress, $lp.LocalPort, $lp.OwningProcess) }
  } else {
    Say "    也没有 dsh / electron / cloudflared 进程 —— 这台电脑上确实没在跑 DSH。"
  }
} else {
  foreach ($l in $listens) { Say "[OK] 监听 $($l.LocalAddress):$($l.LocalPort)  pid=$($l.OwningProcess)" }
  if (-not ($listens | Where-Object { $_.LocalAddress -eq '0.0.0.0' -or $_.LocalAddress -eq '::' })) {
    Say "[!] 只绑在回环地址 —— 手机连不进来。面板里开「局域网访问（绑定 0.0.0.0）」后重启 dsh web。"
  } else {
    Say "[OK] 已绑 0.0.0.0（局域网可达），下面第 3、4 条才是关键。"
  }
}

Say ""
Say "--- 2) 本机可用的地址（手机该用哪条）---"
$myIps = @()
Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -ne '127.0.0.1' } | ForEach-Object {
    $ip = $_.IPAddress
    if ($ip -like '192.168.*' -or $ip -like '10.*' -or $ip -match '^172\.(1[6-9]|2\d|3[01])\.') {
      $note = '<= 手机连同一 Wi-Fi 时用这条'
    } elseif ($ip -match '^100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.') {
      if ($_.InterfaceAlias -match '(?i)tailscale') {
        $note = '<= Tailscale 地址：手机也必须装 Tailscale 并登同一账号'
      } else {
        $note = '<= 100.64/10（CGNAT 段，挂在 Wi-Fi 网卡上）：手机连同一 Wi-Fi 时用它，手机不在同一网络就用不了'
      }
    } elseif ($ip -like '169.254.*') {
      $note = '<= 链路本地，别用'
    } else { $note = '' }
    if ($ip -notlike '169.254.*') { $script:myIps += $ip }
    Say ("  {0,-16} {1,-28} {2}" -f $ip, $_.InterfaceAlias, $note)
  }
if (-not ($script:myIps | Where-Object { $_ -match '^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)' })) {
  Say "  [!] 本机没有普通的 192.168.x / 10.x 内网地址 —— 局域网那条只能是上面 100.x 那条，"
  Say "      手机必须处在同一个 100.x 网络（同一 Wi-Fi 或同一 Tailscale 网络）才连得上。"
}

Say ""
Say "--- 3) Windows 防火墙有没有放行 19387 ---"
$fwHit = @()
Get-NetFirewallRule -Direction Inbound -Enabled True -Action Allow -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -match '(?i)dsh|19387|electron|node' } | ForEach-Object {
    $pf = $_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
    if ($pf -and ($pf.LocalPort -contains '19387' -or $pf.LocalPort -contains 'Any')) { $fwHit += $_ }
  }
if ($fwHit.Count -gt 0) {
  Say "[OK] 找到 $($fwHit.Count) 条允许入站的规则包含 19387"
} else {
  Say "[X] 没有找到放行 19387 的入站规则 —— 手机连不进来（面板底部会写「防火墙未放行」）"
  Say "    用【管理员】PowerShell 跑这一条，或直接用【管理员身份】重启一次 DSH："
  Say '    New-NetFirewallRule -DisplayName "DSH web 19387" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 19387 -Profile Private'
}

Say ""
Say "--- 4) 从本机连自己的网卡地址（验证 DSH 真的可达 / 会不会被 Host 校验拒）---"
Say "    （401 = 通了但需要令牌，正常；000 = 根本连不上）"
foreach ($ip in $script:myIps) {
  $c = HttpCode "http://${ip}:19387/" $false
  Say ("  http://{0}:19387/  ->  http={1}" -f $ip, $c)
}

Say ""
Say "--- 5) 代理环境变量（走公网/固定域名时要靠它）---"
foreach ($v in @('HTTPS_PROXY', 'https_proxy', 'HTTP_PROXY', 'http_proxy', 'NO_PROXY', 'no_proxy')) {
  Say ("  {0,-12} = {1}" -f $v, [Environment]::GetEnvironmentVariable($v))
}

Say ""
Say "--- 6) 中继与固定域名 ---"
Say ("  连 dsh-market.com  直连 http={0}" -f (HttpCode 'https://dsh-market.com/' $false))
if ([Environment]::GetEnvironmentVariable('HTTPS_PROXY')) {
  Say ("  连 dsh-market.com  走代理 http={0}" -f (HttpCode 'https://dsh-market.com/' $true))
}
$relayId = $null
$idFile = Join-Path $env:USERPROFILE '.dsh\remote-web-ui-registry\desktop.json'
if (Test-Path $idFile) {
  $m = [regex]::Match((Get-Content $idFile -Raw), '"id"\s*:\s*"([^"]+)"')
  if ($m.Success) { $relayId = $m.Groups[1].Value }
}
if ($relayId) {
  Say ("  中继身份 id = {0}  ->  公开地址 https://{0}.dsh-market.com/" -f $relayId)
  $pub = HttpCode ("https://{0}.dsh-market.com/" -f $relayId) $false
  Say ("  连这个公开地址  直连 http={0}" -f $pub)
  if ($pub -eq '000') {
    Say "    [X] 连不上：说明这台电脑的隧道没登记成功（面板顶部多半是红字「固定域名同步失败」）"
  } elseif ($pub -eq '404') {
    Say "    [!] 404：中继收到了，但没找到你这条隧道（多半是 DSH 没在跑，或隧道刚重启）"
  } else {
    Say ("    [OK] http={0}：中继这条是通的（401/302 都算正常），手机应该能用 https 那条" -f $pub)
  }
} else {
  Say "  [X] 还没有中继身份文件 —— 插件从没成功登记过，面板只会给局域网 http 地址"
}

Say ""
Say "--- 7) 插件补丁与身份文件 ---"
$patch = Join-Path $env:USERPROFILE '.dsh\profiles\desktop\cordis.patch.yml'
if (Test-Path $patch) {
  $txt = Get-Content $patch -Raw
  foreach ($key in @('host:', 'autoTunnel:', 'relay:', 'publicBase', 'lanAccess', 'fixedTunnelToken', 'trustedHosts')) {
    $hit = ($txt -split "`n") | Where-Object { $_ -match [regex]::Escape($key) } | Select-Object -First 2
    foreach ($h in $hit) { Say ("  patch> {0}" -f $h.Trim()) }
  }
  if ($txt -notmatch 'remote-web-ui' -and $txt -notmatch 'linxin666') { Say "  [!] patch 里没看到 remote-web-ui / linxin666 —— 远程访问插件可能没启用" }
} else {
  Say "  [X] 没找到 $patch"
}
$regDir = Join-Path $env:USERPROFILE '.dsh\remote-web-ui-registry'
if (Test-Path $regDir) {
  Get-ChildItem $regDir -Filter *.json | ForEach-Object {
    $raw = (Get-Content $_.FullName -Raw).Trim() -replace '\s+', ' '
    $red = $raw -replace '("secret"\s*:\s*")[^"]+(")', '$1***(已隐去，不用发)$2'
    Say ("  身份 {0}: {1}" -f $_.Name, $red)
  }
} else {
  Say "  [X] 没找到 $regDir（插件还没生成过中继身份，说明从未成功登记）"
}
$devFile = Join-Path $env:USERPROFILE '.dsh\remote-web-ui-devices.json'
if (Test-Path $devFile) {
  $dev = Get-Content $devFile -Raw
  Say ("  已配对设备文件 {0} 字节" -f (Get-Item $devFile).Length)
  Say ("  内容摘要: {0}" -f ($dev.Trim() -replace '\s+', ' ').Substring(0, [Math]::Min(400, ($dev.Trim() -replace '\s+', ' ').Length)))
} else {
  Say "  已配对设备文件: 不存在（这台电脑还没被任何手机配对过）"
}

Say ""
Say "--- 8) 本机浏览器能不能打开自己的 19387 ---"
$loop = HttpCode 'http://127.0.0.1:19387/' $false
Say ("  http://127.0.0.1:19387/  ->  http={0}" -f $loop)

Say ""
Say "==== 以上整段复制发给作者即可（含第 3、6、7 条最关键）===="
$out = Join-Path ([Environment]::GetFolderPath('Desktop')) 'dsh-tester-check.txt'
$script:lines -join "`r`n" | Set-Content -Path $out -Encoding UTF8
Write-Host ""
Write-Host "报告已保存: $out"
