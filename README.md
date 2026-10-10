# DSH 手机版 · 配对版

把电脑上的 **DeepSeek Harness（DSH）** 界面装进手机的安卓 App：打开先要本机密码，解锁后连**你自己的**电脑。

这个仓库有两样东西：

| 东西 | 位置 | 说明 |
| --- | --- | --- |
| 📱 手机 App（APK） | 本仓库的 [Releases](../../releases) | 通用配对版：**不含任何凭据、不含任何电脑地址**，可以随便转发；每个人装完后配对自己电脑即可 |
| 🔌 配套插件 | [`plugin/dsh-phone-pair-kit`](plugin/dsh-phone-pair-kit) | 可选。装上后自动把「远程访问插件」按 `autoTunnel + relay` 打开，省掉手动开关 |

App 的安卓侧源码、构建脚本与验证工具在 [`android/`](android)；那里还有一份更详细的工程说明
（[`android/README.md`](android/README.md)）。

---

## 一、手机 App

### 下载

到 [Releases](../../releases) 下载 `DSH-Phone-Pair-1.0.apk`（12,373,348 字节 / 约 11.8 MiB）。

- SHA256：`863F7B3175EE089FAE9FD358F1DA43E7181DF3311E727C922A24E58C8C3FAB76`
- 包名 `com.dsh.phone.pair`，应用名「DSH 手机版 · 配对版」，versionName 1.0
- minSdk 26（Android 8.0）· targetSdk 34 · 权限只有 `INTERNET` 与 `ACCESS_NETWORK_STATE`
- 签名证书 SHA-256：`b9204950d591bb3329ec137180673a98e2899e32fff91f23889585cc78ec1a0f`
- 约 28 MB 前端界面已打进安装包（85 个内容哈希资源），所以第一次打开不必先下载界面

### 用它需要什么

1. **一台开着机的电脑**，上面跑着 DSH。
2. 电脑上装 DSH 插件 **`@linxin666/dsh-remote-web-ui`**（自带 cloudflared，不需要 Cloudflare 账号、
   不需要域名、不需要端口映射），打开它的「自动隧道」，relay 默认就是开的。
3. 电脑面板里复制配对链接：`https://<id>.dsh-market.com/pair-accept?pair=<pairing-code>`。

### 使用步骤

1. 手机安装 APK（需要允许「安装未知来源应用」）。
2. 打开 App → 设置一个**本机密码**（PBKDF2-HMAC-SHA256，10 万次迭代，只存在手机本地）。
3. 把配对链接发到手机点开（App 注册了 `https /pair-accept` 的 intent-filter），或在 App 里粘贴。
4. 显示配对成功即进入你自己的 DSH 界面；之后每次打开只需输密码。

配对成功后手机拿到一枚**一年有效**的 HttpOnly 设备凭据，电脑重启、换 IP、换网络都不用重新配对。

### 电脑关机之后还能用吗

**不能。** App 只是手机端界面，DSH 与 Agent 都跑在电脑上。关机、睡眠、退出 DSH（隧道由插件在 DSH
进程里拉起）都会导致手机连不上；唤醒电脑后 1~2 分钟自动恢复，不需要重新配对。「前端内置」只意味着
界面文件在包里，聊天内容与 Agent 产出物始终来自电脑。详见 [`HANDOFF.md`](HANDOFF.md) 第六节。

### 安全边界

- **配对成功的设备 = 完全控制凭据**（聊天、会话、设置、凭据、Agent 预设、产出物）。只在自己的手机上配对；
  配对链接默认 10 分钟过期，别贴到群里。
- 电脑侧始终保持 `127.0.0.1` 回环绑定，公网可达性完全由 cloudflared 出站隧道提供；不想要了就
  在电脑面板里撤销该设备，或在 App 里「复位本机」。
- 本 APK **不含任何凭据**：发布前会用 [`android/tools/audit_pair_build.py`](android/tools/audit_pair_build.py)
  扫描整个包（含 `classes.dex`），确认里面没有构建期设备 id 与 `dsh_pair=<值>`。

更多面向使用者的说明（含常见问题表）见 [`HANDOFF.md`](HANDOFF.md)。

---

## 二、配套插件 `dsh-phone-pair-kit`

它做的事只有一件：把远程访问插件按

```yaml
- id: remote-web-ui
  config:
    autoTunnel: true
    relay: true
```

插入你的 DSH profile，省掉手动打开开关那一步。它不碰别的东西，卸载就是删掉这段。

安装（三选一，细节见 [插件自己的 README](plugin/dsh-phone-pair-kit/README.md)）：

```powershell
# 1) 从本仓库目录安装（不需要 git，推荐）
pnpm add <本仓库路径>\plugin\dsh-phone-pair-kit
# 2) 从 GitHub 安装（需要本机装了 git，否则 pnpm 会报 "'git' 不是内部或外部命令"）
pnpm add github:Zoragyx/dsh-phone-pair#path:plugin/dsh-phone-pair-kit
# 3) 手动：把目录拷进 <DSH profile>\node_modules\，把包名加进 package.json 的 dsh.profile.bundles
```

> 没装 git 又想从 GitHub 装：在仓库页面点 `Code → Download ZIP`，解压后走第 1 种方式，把路径指向解压出来的 `plugin\dsh-phone-pair-kit`。

前置条件、排错（`HTTP 530`、`HTTPS_PROXY` 只认环境变量等）与卸载步骤都在那份 README 里。

---

## 三、从源码构建 App

代码在 [`android/`](android)，无 Gradle：`bundle web assets → aapt2 → javac → d8 → zipalign → apksigner`。

```powershell
cd android
$ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
& $ps -NoProfile -ExecutionPolicy Bypass -File .\build.ps1            # 产出 artifacts\dsh-phone-pair-1.0.apk
& $ps -NoProfile -ExecutionPolicy Bypass -File .\tools\verify_pair_build.ps1   # 单测 + 真数据命中 + 逐字节比对
python tools\audit_pair_build.py --apk artifacts\dsh-phone-pair-1.0.apk --device-id-file device-id.txt
```

前置：JDK 21、Android SDK `build-tools;35.0.1` + `platforms;android-34`、Python。构建时脚本会自己生成
签名用的 keystore（不进仓库），并向本机 DSH 要一份**只用于下载前端资源**的凭据（同样不进包）。

本轮 1.0 的实测结果（`android/README.md` 有完整表格）：

| 检查 | 结果 |
| --- | --- |
| 单元测试 | `PairLinksTest passed=50`、`AssetIndexTest passed=33` |
| 真数据命中 | `shell urls: 85 ; hits: 85 ; misses: 0` |
| 包内资源逐字节 | `85/85 verified byte-identical, 29,546,654 bytes (28.2 MB)` |
| 全新配对链路 | 公网兑换 200 → `/pair-app?grant=…` → 新凭据解锁 200 → 撤销后 `devices: 3 -> 3` |
| 凭据审计 | `verdict : OK - no build-time credential or cookie inside the package` |
| 打包 | `zipalign` 通过、`apksigner` 通过、badging 版本/权限正确 |

---

## 四、灵感来源与致谢

这个 App 的**灵感与配对思路**来自开源插件
[`@linxin666/dsh-remote-web-ui`](https://www.npmjs.com/package/@linxin666/dsh-remote-web-ui)
（作者 **linxin666**，源码仓库 [zhu1090093659/dsh-web](https://github.com/zhu1090093659/dsh-web)，Apache-2.0）。
它把「用一次链接/一个二维码把手机配到电脑上的 DSH」这件事做了出来，并给出了公开的配对端点与设备会话机制。
**在这个思路上，本项目独立完成了手机端 App（WebView 外壳、密码锁屏、离线缓存、前端内置、从配对链接运行期学习主机）、配套插件与整套构建/验证工具链。**
**谨向原作者 linxin666 表示感谢与敬意** —— 同时声明：本项目与上游作者没有隶属关系，也没有声称获得其背书；若哪里的说明或做法让上游感到不妥，请告知，我们会立即调整。

| 用到了谁 | 许可证 | 它提供了什么 |
| --- | --- | --- |
| [`@linxin666/dsh-remote-web-ui`](https://www.npmjs.com/package/@linxin666/dsh-remote-web-ui) v0.4.5 · 作者 **linxin666** | Apache-2.0 | 配对服务端与公开接口：`/pair-accept?pair=<code>` 一次性令牌、`/pair-app` 手机版界面壳、按设备可撤销的会话、固定域名中继（`<id>.dsh-market.com`）、设置页里的「远程访问」面板与二维码、`/pair-app.sw.js` 重开接管。本项目在此基础上写的是**手机端客户端**与配置/工具 |
| [`dsh-orb`](https://github.com/mini-yifan/dsh-orb-cordis) · 作者 **mini-yifan** | MIT | 本仓库插件 `plugin/dsh-phone-pair-kit` 里 `lib/index.js` 的骨架写法参考了它（不注册端点、只写一行日志）。谨致谢意 |
| DSH / DeepSeek Harness 的 Web 前端 | 随 DSH 分发 | APK 里**内置的约 28 MB 前端资源**（85 个内容哈希文件）是构建时从使用者自己那台电脑的 DSH Web GUI 抓下来的静态文件，只为让手机首屏不用等下载 |
| [cloudflared](https://github.com/cloudflare/cloudflared) | Apache-2.0 | 隧道二进制；由 `cloudflared` npm 包随上游插件分发，**本仓库不含** |

**本项目自己完成的部分**：安卓 WebView 外壳、本机密码锁屏（PBKDF2-HMAC-SHA256）、离线优先缓存、前端资源内置与同源闸门、从配对链接**运行期学习主机**（所以安装包里没有任何凭据或电脑地址）、以及 `android/tools/` 下那套构建与三重验证脚本。

**声明**：

- 本项目是社区第三方作品，与 DeepSeek / DSH 官方、与 `@linxin666/dsh-remote-web-ui` 的作者都没有隶属关系。我们对上游只有感谢：**如果哪里的说明、命名或做法让上游作者感到不妥，请提 issue，我们会立即修改或下架。**
- 本仓库不包含上游插件的源码：`plugin/dsh-phone-pair-kit` 只是**声明依赖**并插入一段配置；手机端是按公开行为独立重写的客户端。各自许可见 [NOTICE.md](NOTICE.md)。
- 「DSH」「DeepSeek」「Cloudflare」等名称与商标归各自所有者，此处仅作说明用途。
- APK 内含上述前端资源。**如果 DSH 作者认为不宜随 APK 分发**，告诉我（或提 issue），我会立即处理 Release 资产（删除，或改成不含内置前端的构建 —— 构建脚本就在 `android/`）。
- 配对成功的手机**就是你电脑的完全控制凭据**（会话、设置、凭据、产出物）。只配对自己的手机；手机丢了就在电脑的「远程访问」面板撤销那台设备。

---

## 五、许可

本项目自己的代码是 MIT，见 [LICENSE](LICENSE)；第三方组件的许可与归属见 [NOTICE.md](NOTICE.md)。DSH 本身与 `@linxin666/dsh-remote-web-ui` 各有各的许可，本仓库不包含它们的源码。
