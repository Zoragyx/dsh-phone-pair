# DSH 手机版 · 配对版（dsh-phone-pair）

给**别人**用的手机 App：下载后不连任何人的电脑，首次打开让你粘贴**自己电脑**的配对链接，
配对成功才进入界面；之后界面资源全部从 App 包内直供（28.2 MB 内置前端），不用每次重下。

与 `..\dsh-phone-app`（个人版 1.4）的关系：**同一套代码，两种构建**。个人版把「你的中继域名 +
你的设备凭据」编译进包，所以只能连你的电脑；配对版把这两样东西全部去掉，改成运行期从配对链接
学习。个人版不动，两个 App 包名不同、可以同时装在手机上。

## 成品

| 项 | 值 |
| --- | --- |
| APK | `artifacts\dsh-phone-pair-1.0.apk` |
| 大小 | 12,369,252 字节（约 11.8 MiB） |
| SHA256 | `5690470F3668A2BDD85681CBFF12312BF000AFAEE55D7E82325AF04D76717B76` |
| 包名 / 版本 | `com.dsh.phone.pair` / versionCode 2、versionName 1.0.1 |
| 应用名 | `DSH 手机版 · 配对版` |
| minSdk / targetSdk | 26 / 34 |
| 权限 | 仅 `INTERNET`、`ACCESS_NETWORK_STATE` |
| 签名 | `CN=DSH Phone`，SHA-256 `b9204950d591bb3329ec137180673a98e2899e32fff91f23889585cc78ec1a0f`（与个人版同一把钥匙，可覆盖升级） |

## 首次使用

1. 电脑：在插件市场装 `@linxin666/dsh-remote-web-ui`，打开它的「自动隧道」（relay 默认就是开的）；
   想省掉手动开关就装配套插件 `plugin\dsh-phone-pair-kit`（见它自己的 README）。然后打开
   **设置 → 远程访问**，复制配对链接（形如 `https://<id>.dsh-market.com/pair-accept?pair=<code>`）。
2. 手机：装本 APK，把链接发到手机 → 直接点开（App 注册了 `https /pair-accept` 的 intent-filter），
   或者打开 App 在配对页粘贴。
3. 设置进入密码（至少 4 位，PBKDF2-HMAC-SHA256 100,000 次，只存本机）→ 自动完成配对并进入界面。
4. 之后每次打开：先输密码；退到后台再回来会重新要求输入（`RELOCK_GRACE_MS=0`）。

已经配对过的机器上，「重新配对」对话框会同时接受**完整链接**和**裸配对码**（裸码用当前站点补齐）。

「关于」里显示当前远程地址；「复位本机」会清掉密码、网页缓存与配对凭据，回到未配对状态。

## 运行期是怎么学会「自己的电脑」的

| 环节 | 个人版 1.4 | 配对版 1.0 |
| --- | --- | --- |
| 中继域名 | 编译期常量 `AppConfig.BASE_URL` | 未配对为 `null`，配对时 `PairLinks.siteOf(link)` 从链接推导，`LockStore.setSite()` 存本地 |
| 起始页 | `AppConfig.START_URL` | `siteUrl() + "/pair-app"`，未配对时先弹配对浮层 |
| Cookie | 常量 `AppConfig.DEVICE_ID` | 只用 `lock.credential()`（首次为 `null`，配对成功后写入） |
| 内置资源拦截 | 同源闸门比 `AppConfig.BASE_HOST` | 同源闸门比 `siteHost()`（`AssetIndex.canonical()` 本来就忽略 host） |
| UA | `DSH-Phone-App/1.4` | `DSH-Phone-Pair/1.0` |
| 包名 / 应用名 | `com.dsh.phone` / `DSH 手机版` | `com.dsh.phone.pair` / `DSH 手机版 · 配对版` |

配对成功与否由「配对后 Cookie 值是否与配对开始时不同」判定（`adoptIssuedCredential()`），
成功才写 `setCredential()` + `setCredentialRevoked(false)`，失败就退回配对浮层。

> **首个版本的真机必现 bug（已修）**：服务器兑换配对链接后是 **303 重定向**
> `/pair-accept → /pair-app?grant=…`，而 `shouldOverrideUrlLoading` 原来只放行
> `siteHost()`（配对完成后才存在）⇒ 未配对时重定向被丢给系统浏览器，WebView 不再跟随，
> Cookie 写不进去，首次配对必定显示「配对失败」。现在新增 `PairLinks.hostOf(url)`（带端口无关的
> 纯 host 提取，相对路径/`javascript:` 返回 `null`）与 `MainActivity.pairingHost()`：已配对看
> `siteHost()`，未配对看**待配对链接自己的 host**，所以 303 留在 WebView 里完成；
> `finishPairing()` 失败时清空 `pairingUrl`，避免旧 host 继续放行。
> 对应单测 +10 例（`hostOf`）⇒ `PairLinksTest` 由 40 例增到 50 例。

## 安全边界

- **配对成功的设备 = 完全控制凭据**（会话、设置、凭据、产出物）。手机丢了就在电脑的「远程访问」
  面板撤销该设备，或在手机 App 里「复位本机」。
- 配对/自更新/插件安装三个控制面仍然**只在回环**开放；服务只绑 `127.0.0.1`（`lanAvailable: false`），
  暴露面只有出站隧道。
- 本包**不含任何凭据**：`tools\audit_pair_build.py` 会扫描整个 zip（含 classes.dex）确认设备 id、
  `dsh_pair=<value>` 都不在里面。这是它能公开下载的前提。
- 包内 `assets/web/index.txt` 里保留的是**构建时**中继域名下的绝对 URL（指纹，不是凭据）：
  `AssetIndex.canonical()` 会剥掉 scheme+host，所以换电脑后照样命中。

## 构建

前置：JDK 21（`javac` 在 PATH）、Android SDK `build-tools;35.0.1` + `platforms;android-34`、Python。
构建脚本会向本机 DSH 要一次凭据（**只为下载 28 MB 前端资源**，不进包），并默认从
**本机 webserver**（`http://127.0.0.1:19387`）抓资源：

```powershell
# 不要直接 & build.ps1（执行策略）；用完整路径调 powershell
$ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
& $ps -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
# 期望末尾：built: …\artifacts\dsh-phone-pair-1.0.apk (12083.3 KB)
#          pairing-mode build: no credential baked in (assets fetched from http://127.0.0.1:19387)
& $ps -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Repair   # 凭据失效时重新 mint
& $ps -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -AssetsBase https://<你的固定域名>  # 改走公网
```

`-AssetsBase` 缺省就是 `http://127.0.0.1:19387`。**不要**在没必要时改成公网中继：它重新注册固定
域名期间会对长响应返回 `HTTP Error 530` / `405` 或截断，实测 relay 构建直接 `bundled 64/85` +
`MISSING EAGER: …/assets/index-5SrrfWpU.js` 而失败（旧 APK 不会被破坏，失败发生在 aapt2 之前）。
构建只在**真的**走公网时才要求 `Test-DeviceId` 通过；本机构建会打印
`relay check skipped (assets base is …)`，因此中继挂掉时不会去 mint 新凭据、白占 `maxDevices` 槽位。
之所以能这样混用：`AssetIndex.canonical()` 剥掉 scheme+host，index 里记 `http://127.0.0.1:19387/…`
与手机请求 `https://<你的域名>/…` 仍会命中同一条目（实测 loopback 85 条 URL vs relay 86 条，
多出的只有按设计不内置的 `/.webmcp/bridge.js`）。

流水线（无 Gradle）：`bundle web assets` → `aapt2 compile/link` → `javac` → `d8` → `add_dex.py`
→ `zipalign` → `apksigner`。

## 验证（改完代码请按顺序跑一遍）

```powershell
$ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
& $ps -NoProfile -ExecutionPolicy Bypass -File .\tools\verify_pair_build.ps1   # 单测 + 真数据对拍 + 包内字节比对
& $ps -NoProfile -ExecutionPolicy Bypass -File .\tools\pair_e2e.ps1            # 全新配对演练（用完自动撤销探测设备）
python tools\audit_pair_build.py --apk artifacts\dsh-phone-pair-1.0.apk        # 包内不得有凭据
```

`verify_pair_build.ps1` 默认整个流程都走本机 webserver（`-Base`，缺省 `http://127.0.0.1:19387`）：
中继在重新注册固定域名时会丢长响应（HTTP 530 / 截断），拿它做 28 MB 的比对不可靠，而
`AssetIndex.canonical()` 忽略 origin，所以本机取到的 URL 集合与手机实际请求的完全一致。
本轮实测（当前成品 `5690470F…7B76`）：

| 检查 | 结果 |
| --- | --- |
| `PairLinksTest` | `passed=50 failed=0`（任意 https host 都接受、带端口、`siteOf`、裸码需已知站点、`hostOf` 10 例） |
| `AssetIndexTest` | `passed=33 failed=0` |
| 真数据对拍（loopback 外壳 vs 包内索引） | `shell urls: 85 ; hits: 85 ; misses: 0`，`bridge.js served from bundle: false`（本条按设计不内置；同一脚本对中继外壳是 86 条 / `misses: 1`） |
| 包内资源逐字节 | `85/85 verified byte-identical, 29,546,654 bytes (28.2 MB)`、0 problem(s)、`verify exit=0` |
| `pair_e2e.ps1` | 解析真实配对链接 `OK`；公网兑换 → `/pair-app?grant=…` 200 + 新 Cookie；该 Cookie 解锁 `/pair-app` 200；撤销后 `devices: 3 -> 3` |
| `audit_pair_build.py` | `verdict : OK - no build-time credential or cookie inside the package` |
| `tools\validate_kit.mjs` | `kit checks: passed=26 failed=0`（插件契约，含 js-yaml 严格解析 + `apply()` 健壮性） |
| `aapt2 dump badging` | `package: name='com.dsh.phone.pair'`、versionCode 2 / versionName 1.0.1、label `DSH 手机版 · 配对版`、权限仅两项 |
| `zipalign -c -v 4` / `apksigner verify` | `Verification succesful` / 通过（同一把 `CN=DSH Phone`） |

## 文件

| 路径 | 说明 |
| --- | --- |
| `java\com\dsh\phone\MainActivity.java` | Activity + 密码锁 + 配对浮层 + WebView + `shouldInterceptRequest` 本地直供 |
| `java\com\dsh\phone\LockStore.java` | PBKDF2 密码、失败退避、`siteUrl/siteHost/setSite`、`credential()`（本版不预置） |
| `java\com\dsh\phone\PairLinks.java` | 配对链接/裸码解析、`siteOf()`、Cookie 解析 |
| `java\com\dsh\phone\AssetIndex.java` | `assets/web/index.txt` 索引 + `canonical()/normalize()` 路径匹配 |
| `test\com\dsh\phone\PairLinksTest.java` | `PairLinks` JVM 单测（50 例） |
| `test\com\dsh\phone\AssetIndexTest.java` | `AssetIndex` JVM 单测（33 例） |
| `tools\bundle_web_assets.py` | 抓外壳 → 下载 85 个资源 → 写 `index.txt`（排除 `bridge.js`） |
| `tools\shell_urls.py` | 只抓一次外壳并输出去重的绝对 URL 列表（供对拍） |
| `tools\IndexMatchCheck.java` | 拿真数据逐条查索引，打印命中/未命中 |
| `tools\verify_bundled_assets.py` | 包内资源存在性、MIME、与服务器逐字节比对（`--loopback` 可绕开中继） |
| `tools\verify_pair_build.ps1` | 一键跑完「解索引 → 单测 → 真数据对拍 → 逐字节比对」（`-Base` 缺省本机） |
| `tools\validate_kit.mjs` | 不装进任何 profile 就校验配套插件契约（26 项）+ 扫重复插件 id |
| `tools\audit_pair_build.py` | 发布前凭据泄漏审计 |
| `tools\pair_e2e.ps1` | 全新配对演练 + 自动撤销探测设备 |
| `tools\PairLinkCheck.java` | 拿真实链接验 `PairLinks`（`pair_e2e.ps1` 调用） |
| `plugin\dsh-phone-pair-kit\` | 配套插件：一键让电脑可被配对（见其 README） |
| `build.ps1` | 无 Gradle 构建流水线 |

## 三个必须记住的坑

1. **绝不能用 PowerShell 的 `Get-Content`/`Set-Content` 改写含中文的源文件**。PS 5.1 按 cp936
   解码 UTF-8，会把每个中文字节的第一个当字符、第二个当问号，并且**吞掉紧随其后的 ASCII 字符**
   （通常是字符串的收尾引号），结果整个文件静默损坏。只能用编辑工具或 Python 显式 UTF-8（不写 BOM）。
2. **build-tools 34.0.0 里的 R8/D8 是坏开发版**（`R8_8.2.2-dev`），对任何继承/实现系统类的类抛
   `NullPointerException: Cannot invoke "String.length()" because "<parameter1>" is null`。
   用 `build-tools;35.0.1`。
3. **改了 `AndroidManifest.xml` 的 `package`，`R` 类就换了包**。配对版把 manifest package 改成
   `com.dsh.phone.pair` 之后，`aapt2` 生成的 `R.java` 落在 `com.dsh.phone.pair` 里，而 Java 源码仍在
   `com.dsh.phone`，于是 `MainActivity.java` 里的 `R.mipmap.ic_launcher` 报「找不到符号: 类 R」——
   在 `MainActivity.java` 顶部补 `import com.dsh.phone.pair.R;` 即可（activity 名本来就是全限定，
   所以只改 manifest package 是安全的）。

## 已知边界

- 没有相机入口，所以配对只能靠「点链接 / 粘贴」，不能扫码（扫码请用个人版或电脑版界面）。
- 本机不能跑 Android 模拟器（`HypervisorPresent=False`，开 WHPX 要管理员权限 + 重启），
  因此所有验证都是静态 + 服务端链路级，真机行为需要用户实测。
- 中继在重新注册固定域名期间会返回 530 或截断长响应；配对版的 85 个资源全部走包内，只有
  外壳 `/pair-app`（约 46 KB）需要走网络，所以受这件事影响很小。
