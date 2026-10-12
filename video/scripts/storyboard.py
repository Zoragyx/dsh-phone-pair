"""The narration script + storyboard for the DSH 手机版 tutorial series.

Every fact here is quoted from the project's own docs and source:
- MainActivity.java / LockStore.java  → on-screen wording and lock behaviour
- HANDOFF.md                          → what happens when the computer is off
- README.md / plugin README.md        → download link, package name, install steps

Visual mockups are labelled 示意图 because no real-device screenshot exists yet.
"""
from __future__ import annotations

DOWNLOAD_PAGE = "https://github.com/Zoragyx/dsh-phone-pair/releases/latest"
REPO = "github.com/Zoragyx/dsh-phone-pair"
DOMAIN_SAMPLE = "https://7f3c9a12d0e4b6a8.dsh-market.com"
PAIR_LINK_SAMPLE = DOMAIN_SAMPLE + "/pair-accept?pair=8f2c1d4b6a9e7c30d5a1b8e4f6c2d0a7"
FOOTER = "下载页 " + DOWNLOAD_PAGE

# Same palette as theme.py, kept locally so the storyboard stays readable.
INK = (233, 240, 248)
INK_DIM = (152, 174, 198)
ACCENT = (77, 208, 225)
AMBER = (255, 176, 64)
OK = (94, 214, 138)
WARN = (255, 138, 128)

EPISODES: list[dict] = [
    # ----------------------------------------------------------------- 声明
    {
        "id": "ep0",
        "file": "00-使用声明.mp4",
        # 不单独出片：这一段只作为合辑的开头（声明 + 时间节点）
        "standalone": False,
        "label": "使用声明 · 请先看这一页",
        "scenes": [
            {
                "title": "使用声明",
                "narration": "开头先说一件事。作者最近学业比较忙，暂时没有时间继续做更多的调试和改进；"
                             "这个项目是先做出来、先给你用的状态。使用中如果遇到问题，"
                             "请把问题直接交给 DSH，也就是你电脑上的这个助手，让它帮你排查和解决。"
                             "给你带来不便，请多谅解。",
                "subtitle": ["作者近期学业繁忙，暂时无法做更多调试", "有问题请直接交给 DSH 排查，敬请谅解"],
                "visual": {
                    "kind": "notice",
                    "lines": [
                        {"text": "使用声明", "size": 84, "fill": (255, 176, 64)},
                        {"text": "作者近期学业繁忙", "size": 62},
                    ],
                    "items": [
                        {"text": "暂时抽不出时间继续做更多调试、优化与答疑；",
                         "size": 42},
                        {"text": "本项目按「做出来能用」的状态提供，功能以你已经看到的行为为准；",
                         "size": 42},
                        {"text": "使用中遇到任何问题，请把问题直接交给 DSH（你电脑上的这个助手），"
                                 "它能读日志、复现步骤并给出修复；",
                         "size": 42, "dot": (94, 214, 138)},
                        {"text": "确实需要作者出面的事情，欢迎在仓库里留 Issue，能回的时候会回。",
                         "size": 42, "dot": (94, 214, 138)},
                    ],
                    "note": "一句话：视频和文档先看完，卡住了就把问题丢给 DSH，别自己硬扛；请多谅解。",
                },
            },
            {
                "title": "时间节点",
                # 旁白里刻意不念具体时间：那一页的数字由 build.py 按实际成片时长回填，
                # 念数字会让这一段的时长反过来影响数字本身。
                "narration": "这支片子把声明和六集讲解拼在了一起。中间有两个真正动手装东西的时间点，"
                             "我都标在这一页上：一个是电脑端开始装插件，一个是手机端开始下载安装。"
                             "想直接跳到哪一步，按这个时间点拖进度条就行。",
                "subtitle": ["两个动手安装的时间点", "电脑端先装插件，手机端再下载 APK"],
                "visual": {
                    "kind": "chapters",
                    "lines": [
                        {"text": "两个动手安装的时间点", "size": 84},
                        {"text": "按下面的时间拖进度条，可以直接跳过去", "size": 42,
                         "fill": (152, 174, 198)},
                    ],
                    "items": [
                        {"ep": "ep2", "time": "--:--", "label": "电脑端 · 开始装插件",
                         "note": "在电脑的 DSH 里装插件、打开「远程访问」，把配对链接发到手机；只做一次。",
                         "fill": (77, 208, 225)},
                        {"ep": "ep3", "time": "--:--", "label": "手机端 · 开始下载安装",
                         "note": "下载 APK、装好，第一次打开先设置进入密码（Android 8.0 或更高）。",
                         "fill": (94, 214, 138)},
                    ],
                },
            },
        ],
    },
    # ------------------------------------------------------------------ 1
    {
        "id": "ep1",
        "file": "01-这是什么-能干什么.mp4",
        "label": "第 1 集 / 共 6 集 · 这是什么",
        "scenes": [
            {
                "title": "这是什么",
                "narration": "这套东西分成两半：电脑上装一个插件，手机上装一个 App。"
                             "装好、配对一次之后，你在外面用手机，就能看到这台电脑上 DSH 的工作状态，"
                             "也能继续跟它说话。",
                "subtitle": ["电脑端插件 + 手机端 App", "配对一次，之后在外面也能连回来"],
                "visual": {
                    "kind": "title",
                    "art": "pair",
                    "lines": [
                        {"text": "DSH 手机版", "size": 108},
                        {"text": "在外面，也能看着它干活", "size": 58, "fill": (77, 208, 225)},
                    ],
                    "sub": [{"text": "电脑一半 + 手机一半，缺一半都用不了", "size": 42}],
                },
            },
            {
                "title": "它能做什么",
                "narration": "先说能做什么。你可以在外面看任务跑到哪一步，接着发消息、看它产出的文件；"
                             "App 里带着密码锁，别人拿起你的手机也进不去；界面本身已经打进安装包，打开不用等下载。",
                "subtitle": ["看进度 · 接着聊 · 看产出物", "带密码锁，界面已内置"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "随时随地查看任务进度", "mark": "ok"},
                        {"text": "在外面继续发消息、看 Agent 产出物", "mark": "ok"},
                        {"text": "每次打开都要输密码，别人拿到手机也进不去", "mark": "ok"},
                        {"text": "界面已内置在安装包里，打开很快", "mark": "ok"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "它做不到什么",
                "narration": "再说清楚一件事：电脑关机之后，它不能继续用。DSH 和 Agent 都跑在这台电脑上，"
                             "电脑关机、睡眠，或者只是退出 DSH，手机都会连不上；"
                             "唤醒电脑以后，大概一两分钟会自动恢复，不需要重新配对。",
                "subtitle": ["电脑关机 / 睡眠 / 退出 DSH", "手机都会连不上"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "关机或断电：手机打不开界面", "mark": "no"},
                        {"text": "睡眠或休眠：同样断开，唤醒后 1~2 分钟自动恢复", "mark": "no"},
                        {"text": "只退出 DSH：隧道跟着停，一样连不上", "mark": "no"},
                        {"text": "想在电脑关机后继续用，只能把 DSH 放在常年开机的机器上", "mark": "no"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "总共三步",
                "narration": "所以整套流程就三件事：电脑上装好插件、打开远程访问；"
                             "手机上装好 App、设一个进入密码；然后把电脑给的配对链接发到手机，点开就配对完成。"
                             "接下来几集，我一步一步带你走一遍。",
                "subtitle": ["电脑装插件 → 手机装 App → 配对一次"],
                "visual": {
                    "kind": "steps",
                    "items": [
                        {"text": "电脑上：装好插件，打开「远程访问」",
                         "note": "面板会显示一个固定域名和配对链接"},
                        {"text": "手机上：装好 App，设一个进入密码",
                         "note": "密码至少 4 位，只保存在这台手机上"},
                        {"text": "配对：把电脑给的链接发到手机，点开就完成",
                         "note": "配对链接默认 10 分钟内有效"},
                    ],
                },
                "footer": FOOTER,
            },
        ],
    },
    # ------------------------------------------------------------------ 2
    {
        "id": "ep2",
        "file": "02-电脑端准备.mp4",
        "label": "第 2 集 / 共 6 集 · 电脑端",
        "scenes": [
            {
                "title": "电脑端要装什么",
                "narration": "这一集看电脑这一半。插件叫 dsh-phone-pair-kit，它自己不做别的事，"
                             "只把「远程访问」能力打开，让这台电脑可以被你的手机配对。"
                             "注意顺序：电脑端装好之后，还要去手机上装 App，缺一半都用不了。",
                "subtitle": ["插件只是电脑那一半", "手机端 App 是单独安装的"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "插件名：dsh-phone-pair-kit（电脑端）", "mark": "ok"},
                        {"text": "它会把「远程访问」打开，并自动开一条出站隧道", "mark": "ok"},
                        {"text": "不需要 Cloudflare 账号，也不用改路由器", "mark": "ok"},
                        {"text": "手机端是单独的 APK，必须先装好", "mark": "no"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "怎么装插件",
                "narration": "装插件有三种方式。最省事的是让电脑上的 DSH 自己装：把仓库地址发给它，"
                             "让它把这个插件装好、并把远程访问打开。"
                             "第二种是等插件市场收录之后，在「设置 → 插件」里一键安装。"
                             "第三种是手动下载仓库里的插件目录，放进 profile 里。",
                "subtitle": ["推荐：让电脑上的 DSH 自己装", "或等插件市场收录后一键装"],
                "visual": {
                    "kind": "steps",
                    "items": [
                        {"text": "推荐：把仓库地址发给电脑上的 DSH，让它帮你装",
                         "note": REPO},
                        {"text": "插件市场收录后：设置 → 插件，搜 dsh-phone-pair-kit 一键安装",
                         "note": "已投稿到 awesome-dsh-plugin 目录，收录需要一点时间"},
                        {"text": "手动：在仓库页面 Code → Download ZIP，解压后放进 profile",
                         "note": "把 plugin\\dsh-phone-pair-kit 放进 profile 的 node_modules 并登记"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "打开「远程访问」面板",
                "narration": "装完打开「设置 → 远程访问」。面板上会出现一个固定域名，"
                             "形如 https://一串字符.dsh-market.com，还有一个配对链接和二维码。"
                             "点一下「复制配对链接」，它就是待会儿要发到手机上的东西。",
                "subtitle": ["面板显示固定域名 + 配对链接", "点「复制配对链接」"],
                "visual": {
                    "kind": "panel",
                    "title": "DSH · 设置 → 远程访问",
                    "height": 620, "width": 1240,
                    "widgets": [
                        {"t": "heading", "text": "远程访问", "size": 42},
                        {"t": "text", "text": "状态：已开启 · 隧道已连接 · 已登记固定域名",
                         "fill": (94, 214, 138), "size": 32},
                        {"t": "spacer", "h": 10},
                        {"t": "text", "text": "固定域名", "size": 30},
                        {"t": "address", "text": DOMAIN_SAMPLE, "size": 30},
                        {"t": "text", "text": "配对链接（默认 10 分钟内有效）", "size": 30},
                        {"t": "address", "text": PAIR_LINK_SAMPLE[:62] + "…", "size": 26},
                        {"t": "spacer", "h": 8},
                        {"t": "button", "text": "复制配对链接", "size": 32},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "面板没有域名怎么办",
                "narration": "如果面板提示「当前服务仅绑定在 127.0.0.1 且未配置公网地址」，"
                             "说明隧道还没起来：常见原因是这台电脑走了系统代理，"
                             "而 cloudflared 只认 HTTPS_PROXY 环境变量；先解决代理，或者等一分钟再看。",
                "subtitle": ["「仅绑定 127.0.0.1 且未配置公网地址」", "＝ 隧道没起来，先查代理"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "面板一直显示「隧道未连接」→ 先看电脑能不能正常出网", "mark": "no"},
                        {"text": "电脑走 Clash / v2ray 等系统代理 → cloudflared 只认 HTTPS_PROXY 环境变量", "mark": "no"},
                        {"text": "设置好 HTTPS_PROXY 后重启 DSH，再回面板看一次", "mark": "ok"},
                        {"text": "手机打不开域名、返回 530 → 中继正在重指，等十几秒重试", "mark": "ok"},
                    ],
                },
                "footer": FOOTER,
            },
        ],
    },
    # ------------------------------------------------------------------ 3
    {
        "id": "ep3",
        "file": "03-手机端-下载与安装.mp4",
        "label": "第 3 集 / 共 6 集 · 手机端",
        "scenes": [
            {
                "title": "下载手机端 App",
                "narration": "现在轮到手机。在手机上打开下载页：github 点 com 斜杠 Zoragyx 斜杠 dsh-phone-pair，"
                             "releases，latest。在列表里找到 DSH-Phone-Pair-1.0.apk，大小约十二兆，点它下载。",
                "subtitle": ["打开下载页，找到 .apk", "文件约 12 MB，只从这个页面下载"],
                "visual": {
                    "kind": "steps",
                    "items": [
                        {"text": "手机浏览器打开下载页", "note": DOWNLOAD_PAGE},
                        {"text": "在 Release 里找到 DSH-Phone-Pair-1.0.apk（约 12 MB）",
                         "note": "SHA256 校验值也写在同一页，可以核对"},
                        {"text": "只在官方页面下载，不要用来路不明的安装包",
                         "note": "包名 com.dsh.phone.pair · 版本 1.0"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "安装并设第一个密码",
                "narration": "下载完点安装。系统可能会提示「不允许安装未知来源的应用」，"
                             "按提示允许一次就好。装好后第一次打开，App 会先让你设置一个进入密码，至少四位，"
                             "输两遍，然后点「设置并进入」。这个密码只保存在手机上，用 PBKDF2 加密存放。",
                "subtitle": ["首次打开：先设进入密码", "密码只保存在这台手机上"],
                "visual": {
                    "kind": "phone",
                    "align": "left",
                    "widgets": [
                        {"t": "heading", "text": "DSH 手机版", "size": 44},
                        {"t": "text", "text": "首次使用 · 请为这台手机设置进入密码", "size": 28,
                         "fill": (255, 196, 92)},
                        {"t": "text", "text": "输入密码后才能进入", "size": 26},
                        {"t": "spacer", "h": 16},
                        {"t": "field", "text": "设置密码（至少 4 位）"},
                        {"t": "field", "text": "再输入一次"},
                        {"t": "spacer", "h": 10},
                        {"t": "button", "text": "设置并进入"},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "密码只保存在本机（PBKDF2 加密），忘记后可随时重设。",
                         "size": 24},
                    ],
                    "side": [
                        {"t": "heading", "text": "第一次打开会发生什么", "size": 42},
                        {"t": "text", "text": "App 里还没有密码，所以第一步一定是设密码："
                                                 "至少 4 位，输两遍，然后点「设置并进入」。", "size": 34,
                         "fill": INK},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "密码只在手机本地校验：PBKDF2-HMAC-SHA256、"
                                                 "10 万次迭代，只保存随机盐和派生键，"
                                                 "明文不会写进任何文件，也不会发给电脑。", "size": 30},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "设好之后，每次把 App 切回前台都要重新输一次。", "size": 30,
                         "fill": AMBER},
                        {"t": "spacer", "h": 12},
                        {"t": "callout", "color": AMBER,
                         "text": "小结：第一次打开 = 设密码（至少 4 位）→ 进入界面。"
                                 "密码忘了只能「复位本机」重设，密码和配对会一起清掉。"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "进去之后长这样",
                "narration": "设好密码就进入界面了。第一次打开会看到一句提示："
                             "客户端界面已内置在本机，首次打开无需下载大文件。"
                             "点右上角或返回键可以看到设置菜单，里面五项分别是：重新加载界面、修改进入密码、"
                             "重新配对、复位、以及关于本应用。",
                "subtitle": ["界面已内置在 App 里", "设置菜单一共五项"],
                "visual": {
                    "kind": "phone",
                    "align": "left",
                    "widgets": [
                        {"t": "heading", "text": "设置", "size": 42},
                        {"t": "text", "text": "正在加载界面…", "size": 24, "fill": (152, 174, 198)},
                        {"t": "spacer", "h": 10},
                        {"t": "rows", "size": 34, "items": [
                            {"text": "重新加载界面（清空缓存重下）", "ok": True},
                            {"text": "修改进入密码", "ok": True},
                            {"text": "重新配对（粘贴配对链接）", "ok": True},
                            {"text": "复位：清除密码和配对", "ok": False},
                            {"text": "关于本应用", "ok": True},
                        ]},
                        {"t": "spacer", "h": 14},
                        {"t": "text", "text": "客户端界面已内置在本机，首次打开无需下载大文件。",
                         "size": 24},
                    ],
                    "side": [
                        {"t": "heading", "text": "左侧五项分别是", "size": 42},
                        {"t": "text", "text": "① 重新加载界面（清空缓存重下）", "size": 32, "fill": INK},
                        {"t": "text", "text": "② 修改进入密码　③ 重新配对（粘贴配对链接）", "size": 32,
                         "fill": INK},
                        {"t": "text", "text": "④ 复位：清除密码和配对　⑤ 关于本应用", "size": 32,
                         "fill": INK},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "「重新加载界面」只是清掉网页缓存重新取一次；"
                                                 "界面本体已经在安装包里，所以正常打开很快。", "size": 30},
                        {"t": "spacer", "h": 12},
                        {"t": "callout", "color": OK,
                         "text": "小结：界面 28 MB 已经在安装包里，第一次打开不用先下载大文件；"
                                 "白屏或卡住时点「重新加载界面」。"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "手机侧的系统要求",
                "narration": "顺带说清版本要求：Android 8.0 及以上就能装，"
                             "App 的权限只有网络相关的两项，不会读你的通讯录、相册或者位置。"
                             "如果你在电脑面板上撤销了设备，App 里会提示「本机配对已清除」，重新配对一次就好。",
                "subtitle": ["Android 8.0 及以上", "权限只有网络，没有多余权限"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "系统要求：Android 8.0（minSdk 26）及以上", "mark": "ok"},
                        {"text": "权限：只有 INTERNET 与 ACCESS_NETWORK_STATE", "mark": "ok"},
                        {"text": "安装包里不含任何人的配对凭据", "mark": "ok"},
                        {"text": "电脑面板撤销设备后：打开 App 会提示「本机配对已清除」", "mark": "no"},
                    ],
                },
                "footer": FOOTER,
            },
        ],
    },
    # ------------------------------------------------------------------ 4
    {
        "id": "ep4",
        "file": "04-首次配对.mp4",
        "label": "第 4 集 / 共 6 集 · 配对",
        "scenes": [
            {
                "title": "把配对链接发到手机",
                "narration": "配对靠一条链接。回到电脑的「远程访问」面板，点「复制配对链接」，"
                             "然后用微信、QQ 或者文件传输把它发到手机上。这条链接默认十分钟内有效，"
                             "过期了就回面板重新生成一条。",
                "subtitle": ["电脑：复制配对链接 → 发到手机", "链接 10 分钟内有效"],
                "visual": {
                    "kind": "pair",
                    "arrow_label": "配对链接",
                    "panel": [
                        {"t": "heading", "text": "远程访问", "size": 34},
                        {"t": "text", "text": "固定域名", "size": 26},
                        {"t": "address", "text": "https://7f3c9a12…dsh-market.com", "size": 24},
                        {"t": "button", "text": "复制配对链接", "size": 28},
                    ],
                    "phone": [
                        {"t": "heading", "text": "聊天里收到的链接", "size": 30},
                        {"t": "address", "text": "https://…/pair-accept?pair=…", "size": 22},
                        {"t": "text", "text": "点开就会跳到 DSH 手机版", "size": 24},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "点开链接，输入密码",
                "narration": "在手机上点开这条链接，会直接跳到 DSH 手机版。"
                             "锁屏会提示「已收到配对链接 · 输入密码后自动完成配对」，输入你刚设置的密码，"
                             "配对就会自动完成，屏幕下方会出现「配对成功」，后面跟着你电脑的固定域名。",
                "subtitle": ["点开链接 → 跳到 App → 输密码", "自动完成配对"],
                "visual": {
                    "kind": "phone",
                    "align": "left",
                    "widgets": [
                        {"t": "heading", "text": "DSH 手机版", "size": 44},
                        {"t": "text", "text": "已收到配对链接 · 输入密码后自动完成配对",
                         "size": 26, "fill": (255, 196, 92)},
                        {"t": "spacer", "h": 18},
                        {"t": "dots", "count": 6},
                        {"t": "spacer", "h": 10},
                        {"t": "button", "text": "进入"},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "配对成功：https://7f3c9a12…dsh-market.com", "size": 24,
                         "fill": (94, 214, 138)},
                    ],
                    "side": [
                        {"t": "heading", "text": "点一下链接就够", "size": 42},
                        {"t": "text", "text": "手机上点开链接，系统会把链接交给 DSH 手机版，"
                                                 "App 里会先弹出密码界面。", "size": 32, "fill": INK},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "锁屏提示：已收到配对链接 · 输入密码后自动完成配对", "size": 30,
                         "fill": AMBER},
                        {"t": "text", "text": "输对密码 → 自动完成配对 → 提示「配对成功：<你的固定域名>」，"
                                                 "然后就进入 DSH 界面。", "size": 30, "fill": OK},
                        {"t": "spacer", "h": 12},
                        {"t": "callout", "color": OK,
                         "text": "小结：点链接 → 输密码 → 自动完成配对，手机上不用再做别的设置。"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "也可以手动粘贴",
                "narration": "如果链接不方便点开，也可以手动粘贴：在 App 里打开设置，"
                             "选「重新配对（粘贴配对链接）」，把整条链接粘进去，点确定，"
                             "再输入密码，一样能完成配对。",
                "subtitle": ["设置 → 重新配对（粘贴配对链接）", "粘贴整条链接再输密码"],
                "visual": {
                    "kind": "phone",
                    "align": "left",
                    "widgets": [
                        {"t": "heading", "text": "重新配对", "size": 40},
                        {"t": "text", "text": "把电脑「远程访问」面板里的完整配对链接发到这台手机，粘贴到这里。",
                         "size": 24},
                        {"t": "spacer", "h": 12},
                        {"t": "field", "text": "粘贴配对链接或配对码", "size": 26},
                        {"t": "spacer", "h": 8},
                        {"t": "button", "text": "确定"},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "提示：需要完整的配对链接，链接格式不对会提示重填。", "size": 22},
                    ],
                    "side": [
                        {"t": "heading", "text": "手动粘贴的规矩", "size": 42},
                        {"t": "text", "text": "必须粘整条链接（…/pair-accept?pair=…）："
                                                 "只粘一半会提示「链接格式不对」。", "size": 32, "fill": INK},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "粘贴后点「确定」，再输一次密码就完成配对。", "size": 30},
                        {"t": "text", "text": "链接默认 10 分钟内有效，过期就回电脑面板重新生成一条。", "size": 30,
                         "fill": AMBER},
                        {"t": "spacer", "h": 12},
                        {"t": "callout", "color": AMBER,
                         "text": "小结：粘贴必须完整；链接过期或格式不对时，回电脑面板重新生成一条再发过来。"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "配不上怎么办",
                "narration": "配对失败最常见的两种提示，一种是「配对链接可能已过期」，"
                             "回电脑面板重新生成一条再发过来；另一种是「连不上服务器」，"
                             "先确认电脑上的 DSH 还在运行、手机网络正常，然后点重试。",
                "subtitle": ["「配对链接可能已过期」→ 回电脑重新生成", "「连不上服务器」→ 查电脑和网络"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "配对失败：配对链接可能已过期，请在电脑上重新生成", "mark": "no"},
                        {"text": "连不上服务器：请确认电脑上的 DSH 正在运行、手机网络可用后重试", "mark": "no"},
                        {"text": "配对成功后手机拿到的凭据有效期一年", "mark": "ok"},
                        {"text": "配对链接等于你电脑的钥匙，别贴到群里", "mark": "no"},
                    ],
                },
                "footer": FOOTER,
            },
        ],
    },
    # ------------------------------------------------------------------ 5
    {
        "id": "ep5",
        "file": "05-日常使用与安全.mp4",
        "label": "第 5 集 / 共 6 集 · 使用与安全",
        "scenes": [
            {
                "title": "每次打开都上锁",
                "narration": "日常使用最需要注意的是密码锁：每次把 App 切回前台，都要重新输一次密码，"
                             "没有免密选项。密码只保存在手机上，输错五次开始递增等待，最长要等十分钟。"
                             "密码忘了不是找回，而是「复位本机」——它会同时清掉密码和配对信息。",
                "subtitle": ["每次切回前台都要重新输密码", "错 5 次开始递增等待，最长 10 分钟"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "切回前台就要重新输密码（没有免密选项）", "mark": "ok"},
                        {"text": "连错 5 次开始递增等待，最长 10 分钟", "mark": "no"},
                        {"text": "密码只存本机：PBKDF2 加密，服务端拿不到明文", "mark": "ok"},
                        {"text": "忘记密码只能「复位本机」：密码和配对一起清掉", "mark": "no"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "设置菜单五项",
                "narration": "设置菜单就是这五项：重新加载界面会清空缓存重下；"
                             "修改进入密码要输新密码两遍；重新配对用来换电脑；"
                             "复位会清除密码、网页缓存和配对凭据，复位之后必须重新配对；最后是关于本应用。",
                "subtitle": ["重新加载 / 改密码 / 重新配对 / 复位 / 关于"],
                "visual": {
                    "kind": "phone",
                    "align": "left",
                    "widgets": [
                        {"t": "heading", "text": "设置", "size": 42},
                        {"t": "rows", "size": 34, "items": [
                            {"text": "重新加载界面（清空缓存重下）", "ok": True},
                            {"text": "修改进入密码", "ok": True},
                            {"text": "重新配对（粘贴配对链接）", "ok": True},
                            {"text": "复位：清除密码和配对", "ok": False},
                            {"text": "关于本应用", "ok": True},
                        ]},
                        {"t": "spacer", "h": 16},
                        {"t": "text", "text": "复位会清除本机的密码、网页缓存和配对凭据，复位后必须重新配对。",
                         "size": 24},
                    ],
                    "side": [
                        {"t": "heading", "text": "平时真正会点到的", "size": 42},
                        {"t": "text", "text": "· 界面偶发白屏 / 卡住 → 重新加载界面（清空缓存重下）", "size": 32,
                         "fill": INK},
                        {"t": "text", "text": "· 想换密码 → 修改进入密码，输两遍新密码", "size": 32, "fill": INK},
                        {"t": "text", "text": "· 换电脑 / 配对掉了 → 重新配对（粘贴配对链接）", "size": 32,
                         "fill": INK},
                        {"t": "text", "text": "· 忘记密码、手机要送人 → 复位：清除密码和配对", "size": 32,
                         "fill": WARN},
                        {"t": "spacer", "h": 6},
                        {"t": "text", "text": "复位是最后手段：它同时清掉密码、网页缓存和配对凭据，"
                                                 "之后必须用电脑上的配对链接重新配一次。", "size": 30},
                        {"t": "spacer", "h": 12},
                        {"t": "callout", "color": AMBER,
                         "text": "小结：平时只会用到「重新加载界面」和「修改进入密码」；"
                                 "「复位」是忘记密码或要把手机送人时才用。"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "安全边界",
                "narration": "安全上有三句话要记住。第一，配对成功的手机等于这台电脑的完全控制凭据，"
                             "能看到聊天、会话、设置和产出物，所以只配对你自己的手机。"
                             "第二，配对链接别贴到群里。第三，手机丢了，就在电脑的「远程访问」面板里撤销那台设备，"
                             "或者在 App 里复位本机。",
                "subtitle": ["配对成功 = 完全控制凭据", "只配自己的手机；丢了就撤销"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "配对成功的手机 = 你电脑的完全控制凭据", "mark": "no"},
                        {"text": "配对链接默认 10 分钟过期，别贴到群里", "mark": "no"},
                        {"text": "手机丢了：电脑面板撤销该设备，或 App 里复位本机", "mark": "ok"},
                        {"text": "电脑始终只绑 127.0.0.1，公网只能通过出站隧道进来", "mark": "ok"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "连不上时的排查顺序",
                "narration": "连不上的时候，按这个顺序看：先确认电脑没关机、DSH 还在运行；"
                             "再看电脑的「远程访问」面板是不是还显示隧道已连接；"
                             "如果提示返回 530 或者白屏很久，等十几秒重试，隧道重建需要一点时间；"
                             "换了 Wi-Fi 或者路由器重启，固定域名不变，稍等就好。",
                "subtitle": ["先看电脑在不在跑 → 再看隧道状态", "换网络不用重新配对"],
                "visual": {
                    "kind": "steps",
                    "items": [
                        {"text": "电脑开着、DSH 正在运行", "note": "关机、睡眠、退出 DSH 都会让手机连不上"},
                        {"text": "电脑面板显示隧道已连接", "note": "没起来先查代理，见第 2 集"},
                        {"text": "返回 530 或白屏：等十几秒重试", "note": "中继正在把固定域名指向新隧道"},
                        {"text": "换 Wi-Fi / 路由器重启：固定域名不变", "note": "不用重新配对，稍等即可"},
                    ],
                },
                "footer": FOOTER,
            },
        ],
    },
    # ------------------------------------------------------------------ 6
    {
        "id": "ep6",
        "file": "06-电脑关机之后会怎样.mp4",
        "label": "第 6 集 / 共 6 集 · 关机之后",
        "scenes": [
            {
                "title": "四种情况，手机看到什么",
                "narration": "最后一集，把电脑状态和手机表现对一遍：电脑关机或者断电，手机打不开界面，"
                             "连接失败或者一直超时；睡眠和休眠一样，不过唤醒之后一两分钟会自动恢复；"
                             "只退出 DSH 也是断开，因为隧道是插件在 DSH 进程里拉起来的；"
                             "换 Wi-Fi、拔网线、路由器重启，隧道会重建，固定域名不变。",
                "subtitle": ["关机 / 睡眠 / 退出 DSH → 连不上", "换网络 → 自动重建，域名不变"],
                "visual": {
                    "kind": "table",
                    "head": ["电脑的状态", "手机侧会看到什么"],
                    "rows": [
                        {"state": "关机 / 断电", "phone": "打不开界面：连接失败或一直超时（隧道两端都没了）",
                         "color": (255, 138, 128)},
                        {"state": "睡眠 / 休眠", "phone": "同上；唤醒后 1~2 分钟自动恢复，不需要重新配对",
                         "color": (255, 176, 64)},
                        {"state": "只退出 DSH", "phone": "同上——隧道是插件在 DSH 进程里拉起的，DSH 一停隧道就停",
                         "color": (255, 176, 64)},
                        {"state": "换 Wi-Fi / 重启路由器", "phone": "隧道会重建，固定域名不变，稍等即可",
                         "color": (94, 214, 138)},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "五个常见误会",
                "narration": "再纠正几个常见误会。「前端内置」不等于离线可用，打进包里的二十八兆只是界面，"
                             "聊天内容和产出物全部来自电脑；本机密码锁在离线时仍然生效，电脑关着也能打开 App 并输密码，"
                             "只是输完会卡在失败页；配对不用重做，凭据有效期一年。"
                             "真要电脑关机后还能用，只能把 DSH 装在一台常年开机的机器上。",
                "subtitle": ["「界面内置」≠「离线可用」", "配对一年有效，不用重做"],
                "visual": {
                    "kind": "bullets",
                    "items": [
                        {"text": "「前端内置」不等于离线可用：聊天内容始终来自电脑", "mark": "no"},
                        {"text": "离线时密码锁仍然生效，只是输完会卡在失败页", "mark": "ok"},
                        {"text": "配对凭据有效期一年：重启、换 IP、换网络都不用重配", "mark": "ok"},
                        {"text": "想让电脑「看起来关着但服务还在」：用睡眠，但隧道仍会断", "mark": "no"},
                        {"text": "最稳的做法：保持开机 + 关闭自动睡眠", "mark": "ok"},
                    ],
                },
                "footer": FOOTER,
            },
            {
                "title": "去哪里下载",
                "narration": "到这里这套视频就讲完了。手机端 App、插件和完整说明都在同一个仓库里，"
                             "用手机相机扫这个二维码，或者直接打开下面这个地址就行。"
                             "记住：先装手机端，再装电脑端，最后配对一次。",
                "subtitle": ["先装手机端 → 再装电脑端 → 配对一次", "下载页在仓库的 Releases 里"],
                "visual": {
                    "kind": "outro",
                    "url": DOWNLOAD_PAGE,
                    "lines": [
                        {"text": "手机端 App + 电脑端插件", "size": 46, "bold": True},
                        {"text": "都在同一个仓库的 Releases 里", "size": 36},
                        {"text": " "},
                        {"text": "顺序：手机端 → 电脑端 → 配对一次", "size": 38, "fill": (77, 208, 225)},
                        {"text": "电脑关机之后不能继续用，请先看完第 6 集", "size": 32,
                         "fill": (255, 176, 64)},
                    ],
                },
            },
        ],
    },
]
