# dsh-phone-pair-kit

![DSH 手机版 · 配对版](icon.png)

> ### ⚠️ 先装手机端 App，否则这个插件没法用
>
> 本套件只是**电脑那一半**。手机那一半是一个单独的 Android App，请先下载安装：
> **[Releases → DSH-Phone-Pair-1.0.1.apk](https://github.com/Zoragyx/dsh-phone-pair/releases/latest)**
> （包名 `com.dsh.phone.pair`）。只装电脑端、没有手机端，是**没有任何东西可以配对的**。

让**这台电脑**变成可被手机配对的 DSH 主机 —— 也就是 `DSH 手机版 · 配对版` App 的服务端那一半。

> **灵感来源与致谢**：本套件只做「插入一段配置、把开关打开」这一件事；配对思路与配对服务端来自上游开源插件
> [`@linxin666/dsh-remote-web-ui`](https://www.npmjs.com/package/@linxin666/dsh-remote-web-ui)
> （作者 **linxin666**，源码仓库 <https://github.com/zhu1090093659/dsh-web>，许可 **Apache-2.0**）。感谢原作者；
> 本项目与该作者没有隶属关系，若有任何不妥会立即调整。完整的第三方清单见仓库根目录的 `NOTICE.md`。

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

**B. 从市场装（收录后）**

本套件已向 DSH 插件市场（`awesome-dsh-plugin` 目录）投稿，材料见仓库的 `market/` 目录；
**收录之后**在 设置 → 插件 里点一下即可。收录之前请用 A 或 C 方式安装 —— 并且别忘了
先装上面那个手机端 App，否则电脑端装好了也没得配。

**C. 从 GitHub 装**

```powershell
# 需要本机装了 git —— pnpm 会用 git ls-remote 去问默认分支；
# 没装 git 会报 "'git' 不是内部或外部命令"，那就用 A 方式：
# 在仓库页面点 Code → Download ZIP，解压后把路径指向 plugin\dsh-phone-pair-kit
pnpm add github:Zoragyx/dsh-phone-pair#path:plugin/dsh-phone-pair-kit
```

装完打开 **设置 → 远程访问**：面板会显示固定域名和二维码/配对链接。
如果面板提示「当前服务仅绑定在 127.0.0.1 且未配置公网地址」，说明隧道还没起来，看下面「排错」。

## 手机侧怎么用

1. 手机装 `DSH 手机版 · 配对版`（[Releases](https://github.com/Zoragyx/dsh-phone-pair/releases/latest)
   里的 `DSH-Phone-Pair-1.0.1.apk`，包名 `com.dsh.phone.pair`）。
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
