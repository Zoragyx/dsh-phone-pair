# NOTICE —— 灵感来源、第三方组件与致谢

本仓库（`Zoragyx/dsh-phone-pair`）是一个**独立开发的社区项目**：手机端 App、内置前端与离线缓存、密码锁屏、配套插件、以及整套构建与验证脚本，都是本项目自己写的。它的**灵感与配对思路**来自下面这些优秀的开源作品，在此致谢。

## 一、灵感来源与依赖

### 1. `@linxin666/dsh-remote-web-ui` v0.4.5 —— 配对思路与配对服务端

- 作者：**linxin666**（npm 作用域 `@linxin666`）
- 源码仓库：<https://github.com/zhu1090093659/dsh-web>
- npm：<https://www.npmjs.com/package/@linxin666/dsh-remote-web-ui>
- 许可证：**Apache-2.0**
- 它给出的东西：把「扫码/一次链接把手机配到电脑上的 DSH」这件事件变得可行 —— `/pair-accept?pair=<code>`（一次性令牌换设备凭据）、`/pair-app`（手机版界面壳）、按设备可撤销的会话、固定域名中继 `<id>.dsh-market.com`、设置页里的「远程访问」面板与二维码、`/pair-app.sw.js` 重开后接管，以及可选的 Cloudflare 快速隧道。
- 本项目的做法：**受它启发、按它公开的行为与接口，独立实现了安卓端的 App**（Java 写的 WebView 外壳、PBKDF2 密码锁屏、离线优先缓存、把前端资源打进包内、从配对链接运行期学习主机），并实现了 `plugin/dsh-phone-pair-kit` 这段配置插入与 `android/tools/` 下的构建/验证工具链。**上游插件的源码没有被复制进本仓库**；`plugin/dsh-phone-pair-kit` 只是**声明依赖**并在 DSH profile 里打开它的开关。
- 谨向 **linxin666** 表示感谢 —— 没有这个插件，手机端的配对无从谈起。

### 2. `dsh-orb` v0.1.6 —— 插件骨架的写法

- 作者：**mini-yifan**
- 源码仓库：<https://github.com/mini-yifan/dsh-orb-cordis>
- 许可证：**MIT**
- 参考之处：`plugin/dsh-phone-pair-kit/lib/index.js` 的最小骨架（`name` / `inject = []` / `apply(ctx)` 只写一行日志、不抢资源）参考了它的写法。谨致谢意。

### 3. cloudflared

- <https://github.com/cloudflare/cloudflared> · 许可证 Apache-2.0。
- 隧道二进制由 `cloudflared` npm 包随上游插件分发，**本仓库与 APK 都不包含它**。

### 4. 构建期工具（不随仓库分发）

JDK 21、Android SDK `build-tools;35.0.1` 与 `platforms;android-34`、Python 3（仅标准库），各自遵循自己的许可。

## 二、关于 APK 内置的 DSH 前端资源

- APK 里内置的 **85 个内容哈希资源（约 28 MB）**，是构建时从**使用者自己电脑上**的 DSH Web GUI 抓取并缓存的静态文件，目的是让手机第一次打开不用等约 10 MB 的下载。它们来自 **DSH / DeepSeek Harness 自己的 Web 界面**，版权归其作者。
- 本仓库的源码里**不含**这些文件；它们只出现在 Release 的 APK 里。
- 如果 DSH 的作者认为这样随 APK 分发不合适，请提 issue —— 我们会立刻删除该 Release 资产，或改成不含内置前端的构建（构建脚本就在 `android/`）。

## 三、本项目自己完成的部分

- `android/java/com/dsh/phone/` 下的 `MainActivity.java`、`LockStore.java`、`AssetIndex.java`、`PairLinks.java`
- `android/test/` 的单元测试、`android/tools/` 的构建与验证脚本（资源抓取、包内逐字节比对、凭据审计、配对链路自检、发布脚本）
- `plugin/dsh-phone-pair-kit/` 的 `cordis.patch.yml` 与 `lib/index.js`
- 本 NOTICE、`README.md`、`HANDOFF.md` 与全部中文说明

功能上属于本项目新增的：安卓 WebView 外壳、本机密码锁屏（PBKDF2-HMAC-SHA256，10 万次迭代）、离线优先缓存、前端资源内置与同源闸门、从配对链接**运行期学习主机**（因此安装包不含任何凭据或电脑地址）、「重新配对 / 复位本机」等入口，以及构建、审计、验证、发布的全套工具。

## 四、声明

1. **友好、尊重**：本项目对上游作者只有感谢。如果上面任何一句描述、命名或做法让上游作者感到不妥，请提 issue 告诉我们，我们会第一时间修改说明或下架相关内容。
2. **没有隶属关系**：本项目是社区第三方作品，与 DeepSeek、DSH 官方、`@linxin666/dsh-remote-web-ui` 的作者、Cloudflare 都没有隶属或合作关系，也没有声称获得他们的背书。
3. **商标**：「DSH」「DeepSeek」「Cloudflare」「Android」等名称与商标归各自所有者，此处仅用于说明兼容性。
4. **安全提醒（责任自负）**：配对成功的手机等同于你电脑的完全控制凭据（可访问会话、设置、凭据、Agent 预设、产出物）。请只配对自己信任的手机；遗失时在电脑的「远程访问」面板撤销设备。本软件按「现状」提供，不附带任何担保。
5. **许可**：本项目自己写的代码以 MIT 发布，见 [LICENSE](LICENSE)。
