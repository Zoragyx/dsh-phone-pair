# dsh-phone-pair-kit

让**这台电脑**变成可被手机配对的 DSH 主机 —— 也就是 `DSH 手机版 · 配对版` App 的服务端那一半。

装上它之后，电脑会自己开一条 Cloudflare 隧道，并把这条隧道登记成一个**固定域名**
`https://<id>.dsh-market.com`；手机只要配对一次，之后无论在家里还是在外面都能连回来，不用重新扫码。

## 它到底装了什么

| 组件 | 作用 |
| --- | --- |
| `@linxin666/dsh-remote-web-ui`（依赖，由本套件自动插入） | 提供配对端点：`/pair-accept?pair=<code>`（用一次性令牌换设备凭据）、`/pair-app`（手机版界面壳）、按设备可撤销的会话、设置页里的「远程访问」面板与二维码 |
| `cordis.patch.yml`（本套件） | 把上面那个插件插进来，并打开 `autoTunnel: true`（开机自动起隧道，不需要 Cloudflare 账号或域名）与 `relay: true`（登记固定域名，重启后手机不用重配对） |

本套件自己的 `lib/index.js` 不提供任何端点，只写一行日志，所以它不会和别的插件抢资源。

## 安装

DSH 的插件以「profile bundle」的形式挂载。任选一种：

**A. 从目录装（本地开发）**

```powershell
# 把本目录放进某个 profile 的 node_modules，并登记到 bundles
$profile = "$env:USERPROFILE\.dsh\profiles\desktop"
Copy-Item . "$profile\node_modules\dsh-phone-pair-kit" -Recurse -Force
# 然后编辑 $profile\package.json，把 "dsh-phone-pair-kit" 加进 dsh.profile.bundles 数组
```

**B. 从市场装（给别人的一键路径）**

把 `dsh-phone-pair-kit` 发布到 DSH 插件市场后，别人在设置 → 插件里点一下即可。
发布需要你自己的市场账号，本仓库不代替你发布。

装完打开 **设置 → 远程访问**：面板会显示固定域名和二维码/配对链接。
如果面板提示「当前服务仅绑定在 127.0.0.1 且未配置公网地址」，说明隧道还没起来，看下面「排错」。

## 手机侧怎么用

1. 手机装 `DSH 手机版 · 配对版`（`dsh-phone-pair-1.0.apk`，包名 `com.dsh.phone.pair`）。
2. 电脑上打开「远程访问」→ 复制配对链接（形如 `https://<id>.dsh-market.com/pair-accept?pair=xxxx`）。
3. 把链接发到手机，点开或在 App 的配对页粘贴，然后设置一个进入密码。
4. 之后每次打开 App：先输密码 → 界面直接用本机缓存渲染，不用重新下载。

## 前置条件

- DSH `>= 0.2.0-rc.2`
- Node `^22.19.0 || >= 24.0.0`
- 电脑能出网。**如果电脑走系统代理（Clash / v2ray 等）**：`cloudflared` 是 Go 程序，只认
  `HTTPS_PROXY` 环境变量，不读 Windows 的 IE/WinINET 代理设置。隧道起不来时先设：
  ```powershell
  [Environment]::SetEnvironmentVariable('HTTPS_PROXY','http://127.0.0.1:7897','User')
  [Environment]::SetEnvironmentVariable('NO_PROXY','localhost,127.0.0.1,::1','User')
  ```
  然后重启 DSH。不设代理也能用，就把这两个变量清空。

## 安全边界（务必读一遍）

- **配对成功的手机 = 完全控制凭据**：它能收发会话、改设置、看产出物。手机丢了就在「远程访问」
  面板里撤销那台设备，或者复位手机 App（设置 → 复位本机）。
- 配对/自更新/插件安装这三个**控制面仍然只在回环**上开放，公网拿不到。
- 服务**只绑 127.0.0.1**（`lanAvailable: false`），暴露面只有出站隧道，不需要开 `--host 0.0.0.0`。
- 一次性配对令牌默认 10 分钟失效；配对成功后手机拿到的是一年期的 HttpOnly Cookie。
- 想彻底关掉：删掉 profile `cordis.patch.yml` 里指向 `remote-web-ui` 的条目（或卸掉本套件），
  固定域名立刻失效。

## 排错

| 现象 | 原因 / 处理 |
| --- | --- |
| 面板说没有公网地址 | 隧道没起来：多为代理问题（见上），或云端 CF 边缘抖动，等 1 分钟看 `GET /api/pair/status` 的 `tunnel.state` / `relay.state` |
| 手机打不开 `https://<id>.dsh-market.com/pair-app`，返回 530 | 中继正在把固定域名重指到新隧道（隧道重启后常见），等十几秒重试；再不行重启 DSH |
| 隧道地址每次重启都变 | 这是快速隧道的正常行为；固定域名由 `relay` 负责，手机不用重配对 |
| 手机上白屏很久 | 首次要把约 10 MB 客户端拉下来（配对版已经把 28 MB 资源内置，正常不会遇到） |

## 卸载

1. 从 profile `package.json` 的 `dsh.profile.bundles` 里移除 `dsh-phone-pair-kit`。
2. 删掉 `node_modules\dsh-phone-pair-kit`（可选：一并删掉 `@linxin666/dsh-remote-web-ui`）。
3. 删掉 profile `cordis.patch.yml` 里对应的 `remote-web-ui` 条目，避免残留配置。
