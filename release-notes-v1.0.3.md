# DSH 手机版 · 配对版 1.0.3 —— 局域网 http 配对（推翻 1.0.2 的一个判断）

1.0.2 的说明里写着「**局域网 http 仍然有意不支持**」。这一版把它改了，因为那个判断站不住：

- 上游 `@linxin666/dsh-remote-web-ui` **本来就支持局域网 http**。它签发的设备 Cookie 只在走 TLS 时才加 `Secure`，源码注释写得很直白：*LAN pairing runs on plain HTTP, where a Secure cookie is simply dropped by the browser and the phone would silently lose its session.* —— 也就是说"电脑走 http、手机走 https"这套组合从头到尾只有我们这一侧在挡。
- 后果是真实用户**整条路走不通**：一位测试员的电脑绑在 `0.0.0.0`，面板给的是 `http://100.68.26.79:19387/pair-accept?pair=…`（Tailscale 地址）。1.0.2 只会回一句「需要完整的配对链接」，他无论怎么复制都配不上。
- 我们当时的顾虑（打开 cleartext 明文流量会放宽信任边界）是对的，但解法不该是"要求所有人改用公网 https"，而是**只放行内网地址**。这一版就是这么做的。

## 修了什么

| 现象 | 1.0.2 | 1.0.3 |
| --- | --- | --- |
| 面板切到「局域网地址」，粘 `http://192.168.1.5:19387/pair-accept?pair=…` | 拒绝（只认 `https://`） | **接受**，直接配对 |
| Tailscale 用户（`http://100.68.x.x:19387/…`） | 拒绝，全流程走不通 | **接受**（`100.64.0.0/10` 是 CGNAT 私网段） |
| `http://` + 公网域名 | 拒绝 | **仍然拒绝**，提示改用 https / 面板的「公网地址」 |

放行范围写死在 `PairLinks.isPrivateHost()`：`10.` / `172.16-31.` / `192.168.` / `169.254.` / `100.64-127.` / `127.`、`*.local` / `.lan` / `.home` / `.internal` / `.ts.net`、以及单段主机名（mDNS/NetBIOS，如 `desktop`、`my-pc.local`）。

### 配套改动

- **Cookie 的 `Secure` 标志按 scheme 决定**：https 加 `; secure`，http 不加。不这样改，WebView 会直接丢弃这条 Cookie，表现为「配对成功、一刷新就掉线」。
- **内置资源拦截**（85 个客户端 bundle / 28.2 MB）从"仅 https 同源"放宽为"http 或 https，但 host 必须等于已配对主机"。
- **`AndroidManifest.xml` 打开 `usesCleartextTraffic`**（Android 默认禁止明文），但真正的门在代码里：只有内网地址的 http 链接能通过解析，WebView 的导航仍被 `shouldOverrideUrlLoading` 限制在已配对主机上，公网 http 站点进不来。
- 配对链接的 intent-filter 增加 `http` scheme：点开局域网链接也能直接进 App。
- 配对浮层引导文案写清"两种链接都能用"，`关于` 页版本号改 1.0.3。

## 顺手补的文档

- 新增 **`tester-troubleshooting.md`**（测试员版排查步骤，可直接转给测试员）：先看版本 → 再看面板顶部状态 → 同一网络直接走局域网 → 想走公网才去修中继红字 → 浏览器"无法保存确认状态"怎么办 → 还不行要提供哪 5 项信息。
- 工程树与发布树的 README「常见问题」表、插件 README「排错」表同步改成 1.0.3 的说法（局域网 http 从"不支持"改为"支持，仅限内网地址"）。

## 怎么升级

1. 下载本页的 `DSH-Phone-Pair-1.0.3.apk`，**直接覆盖安装**（与 1.0.0 / 1.0.1 / 1.0.2 同一把签名 key，不必先卸载，数据保留）；
2. 电脑上打开「远程访问」面板 → 选网络（同一网络用「局域网地址」，在外网用「公网地址」）→ 点『**复制链接**』 → 发到手机 → 在 App 的配对页粘贴；
3. 在 App「设置 / 帮助 → 关于」里看到 `DSH 手机版 · 配对版 1.0.3` 就装对了。

> 走局域网地址的前提是**手机和电脑在同一个网络**（同一个 Wi-Fi，或都在同一个 Tailscale 网络里）。公网地址则要求电脑侧的中继是正常的（面板顶部显示「固定域名：正常」）。

## 校验

| 项 | 值 |
| --- | --- |
| 文件 | `DSH-Phone-Pair-1.0.3.apk` |
| 大小 | 12,373,348 字节（约 11.8 MiB） |
| SHA256 | `60875A94160F3F736F5CAB1E829964D29BA0DF099FA221D3282576B2604D2CEB` |
| 包名 / 版本 | `com.dsh.phone.pair` / versionCode 4、versionName 1.0.3 |
| 最低系统 | Android 8.0（API 26），targetSdk 34 |
| 签名 | `CN=DSH Phone`，SHA-256 `b9204950d591bb3329ec137180673a98e2899e32fff91f23889585cc78ec1a0f`（可覆盖升级） |
| 内置资源 | 85 个文件 / 28.2 MB（离线也能画界面） |

单元测试（JVM，无 JUnit 依赖）：`PairLinksTest` **74 通过 / 0 失败**（新增 12 条局域网/私网地址用例：`192.168.`、`10.`、`172.20.`、`100.64.`、`100.68.26.79`（测试员那条）、`*.local`、单段主机名、无 scheme 补 http、公网 http 仍拒绝、`10.evil.com` 这类伪前缀不认），`AssetIndexTest` **33 通过 / 0 失败**。
