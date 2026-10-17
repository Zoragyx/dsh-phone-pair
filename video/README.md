# DSH 手机版 · 配套讲解视频

给普通用户看的配套视频（**一支完整的片**：1 段使用声明 → 1 页时间节点 → 6 集讲解）：怎么下载安装、怎么配对、密码锁、电脑关机之后会怎样。
中文配音（edge-tts `zh-CN-XiaoxiaoNeural`）+ 中文字幕，1920x1080 / 25fps / H.264 + AAC。

**已发布**：B 站 [BV1RCpE6NEwu](https://www.bilibili.com/video/BV1RCpE6NEwu)（2026-10-11 投稿，8 分 13 秒，科技 → 计算机技术）。
投稿参数与可复制的标题/简介/标签见 `out/bilibili-投稿信息.md`，复核命令见下面「投稿到 B 站」。

## 成品

| 文件 | 内容 |
| --- | --- |
| `out/dsh-phone-pair-完整版.mp4` | **主交付**：使用声明 → 两个动手安装的时间节点 → 6 集顺序拼接（8 分 13 秒） |
| `out/01-这是什么-能干什么.mp4` | 这套东西是什么、能做什么、做不到什么、总共三步 |
| `out/02-电脑端准备.mp4` | 装插件、打开「远程访问」面板、面板没有域名时怎么办 |
| `out/03-手机端-下载与安装.mp4` | 下载 APK、安装、设置第一个密码、进去之后的界面 |
| `out/04-首次配对.mp4` | 把配对链接发到手机、点开配对、手动粘贴、配对失败排查 |
| `out/05-日常使用与安全.mp4` | 每次打开都上锁、设置菜单、安全边界、连不上时的排查顺序 |
| `out/06-电脑关机之后会怎样.mp4` | 四种电脑状态的对照表、五个常见误会、下载入口 |

声明与时间节点是**合辑的前两页**，不单独出片（`storyboard.py` 里 `ep0` 标了
`"standalone": False`）：`ep0` 第 1 幕是使用声明，第 2 幕是「两个动手安装的时间点」——
电脑端 `01:49`、手机端 `03:08`，数字由 `build.py` 按成片实测时长回填，改台词不用手改数字。

- 声明那一页的文案改 `storyboard.py` 里 `ep0` 第 1 幕的 `narration` / `visual.items` / `note`。
- 时间节点那一页的文案改 `ep0` 第 2 幕：条目里的 `"ep": "ep2"` / `"ep": "ep3"` 就是数字的来源。
- 核对数字对不对：`& $py scripts\check_chapters.py`（按节点时间从成片抽帧，和设计帧逐像素比对，
  并把那一页存成 `work/chapter_card.png`）。

每集旁边还有一个同名 `.srt` 字幕文件（画面里已经烧录了中文字幕，`.srt` 是给播放器开关用的）；
合辑另有一份 `dsh-phone-pair-完整版.srt`，时间轴按整支片算（共 25 条）。

**这些 MP4 不放进 git 仓库**：文件太大，它们作为 GitHub Release 的附件分发
（`https://github.com/Zoragyx/dsh-phone-pair/releases/latest`，可在网页上直接播放或下载）。
仓库里只保留生成它们的脚本，任何人都能按下面的命令重新出片。

## 目录结构

```
video/
  scripts/theme.py        画布、字体、卡片、手机/窗口示意图、字幕条、真实二维码
  scripts/visuals.py      9 种场景版式（title/notice/chapters/phone/panel/pair/bullets/steps/table/outro）+ 控件渲染器
  scripts/storyboard.py   声明页 + 时间节点页 + 6 集分镜与逐字旁白（所有事实都来自仓库文档与源码）
  scripts/build.py        流水线：渲染帧 → 合成配音 → 回填时间节点 → 每幕编码 → 拼接
  scripts/make_srt.py     从 work/manifest.json 生成每集与合辑的 .srt 字幕
  scripts/check_chapters.py  核对成片里的时间节点数字（抽帧比对）
  scripts/make_cover.py  生成投稿封面（1146x717 + 1920x1080；封面不放二维码/网址）
  scripts/bili_login_tv.py   B 站 TV 端扫码登录 → 写 biliup 用的 cookies.json
  scripts/bili_whoami.py     核对登录的是哪个账号
  scripts/bili_watch_audit.py  盯稿件审核状态（通过/打回就退出）
  scripts/tts_probe.py    列出可用中文音色并试听
  tools/ffmpeg.exe        编码器（见下）
  .deps/                  edge-tts、qrcode 等本地依赖
  work/                   中间产物（帧、配音、单幕视频、manifest.json）
  out/                    成品视频、字幕、封面、投稿信息
```

## 重新生成

```powershell
$py = "C:\Users\Zora\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
Set-Location <仓库>\video

& $py scripts\build.py --frames-only           # 只出帧，先肉眼检查排版
& $py scripts\build.py --episodes ep3          # 只做第 3 集
& $py scripts\build.py                         # 全量出片（含合辑，并把时间节点数字回填）
& $py scripts\make_srt.py                      # 生成每集 .srt 与合辑 .srt
& $py scripts\check_chapters.py                # 核对合辑里的时间节点
& $py scripts\build.py --voice zh-CN-YunxiNeural --rate +5% --force
```

- 时间节点的数字要在**各集配音都生成之后**才能算出来：单独跑 `--episodes ep0` 时显示 `--:--`，
  跑一次全量构建就会回填成真实时间（那一帧每次都会重画，不受缓存影响）。

- 帧、配音、单幕视频都会缓存；改了台词或版式要加 `--force`（或删掉对应的 `work/` 子目录）。
- `work/manifest.json` 记录每集每幕的标题、旁白与时长，方便核对。
- 换音色用 `--voice`，`scripts/tts_probe.py` 会列出全部 zh-CN 神经音色。
- **画面默认是静止的**（只有每集首尾 0.7s / 0.8s 淡入淡出）。早期版本用 `zoompan` 做缓慢推拉，
  但它在文字上表现为持续抖动（每帧亚像素重采样），所以已默认关闭——想要那种运镜再加 `--motion`。

## 画面运动（可选）

```powershell
& $py scripts\build.py --motion --force      # 恢复 Ken-Burns 推拉（三种变体轮换）
```

`zoom_filter()` 在 `scripts/build.py` 里，三种变体分别是缓慢放大、水平横移、缓慢缩小。

## 投稿到 B 站

用的是 [biliup-rs](https://github.com/biliup/biliup-rs) v0.2.4（单文件 `biliup.exe`，不随仓库分发）。
它的 `login` 第一步是交互式菜单、必须有真终端（在自动化环境里必然报
`Error: IO error: not a terminal`），所以登录走本项目脚本直连 B 站 **TV 端扫码**接口：

```powershell
& $py scripts\bili_login_tv.py            # 生成 out/bili-upload/qr-login-tv.png，手机 B 站客户端扫码
& $py scripts\bili_whoami.py              # 确认登录的是哪个账号
& $py scripts\bili_watch_audit.py --bvid BV1RCpE6NEwu   # 盯审核，开放浏览/被打回就退出
```

上传（就是这次用的参数；`tid 231` = 科技 → 计算机技术，见
[biliup 的 tid 表](https://biliup.github.io/tid-ref.html)）：

```powershell
biliup.exe -u C:\Users\Zora\.dsh\biliup\cookies.json upload --submit app `
  --tid 231 --copyright 1 --no-reprint 1 `
  --title "<标题>" --desc "<简介>" --tag "DSH,DeepSeek,远程控制,手机远程,安卓,开源软件,AI助手,效率工具,教程,软件应用" `
  --cover "out\封面-1146x717.png" "out\dsh-phone-pair-完整版.mp4"
```

四个坑：biliup v0.2.4 没有网页投稿通道（`--submit web` 会被降级成 APP 接口，所以 cookies.json
必须有 TV 端登录拿到的 `token_info.access_token`，纯网页扫码的 cookie 它连解析都过不了）；
`--tid` 默认 `171` 是电子竞技，不填会投错分区；中文参数给 Rust 程序没问题，但
**按 ANSI 读参数的程序（ffprobe 等）会乱码**。第四个是封面：**不能带二维码、网址、联系方式，也不写「扫码下载」**——
B 站封面最常见的打回原因就是这几样，下载入口只放简介正文和置顶评论（`out/封面-1146x717.png` 已按这条重画）。

## 外部依赖

- **ffmpeg**：`tools/ffmpeg.exe` + `tools/ffprobe.exe`，来自
  [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases)（`ffmpeg-master-latest-win64-gpl`，
  GPL 构建，含 libx264/aac）。这是外部二进制，不随仓库分发，需要时重新下载解压到 `tools/`。
- **Python 依赖**：`edge-tts`（语音合成）、`qrcode`（片尾真二维码），装在 `.deps/`：

  ```powershell
  # 本机 pip 会走注册表里的系统代理，需要临时关掉 ProxyEnable 或用直连
  & $py -m pip install --target .deps --index-url https://mirrors.aliyun.com/pypi/simple/ edge-tts qrcode
  ```

  运行时需要把 `.deps` 放进 `PYTHONPATH`（或在 `build.py` 里加 `sys.path`）。

## 事实来源

旁白和画面文字全部照抄项目自身的文档与源码，不做演绎：

- `android/java/com/dsh/phone/MainActivity.java`、`LockStore.java` —— 界面原文、密码规则（PBKDF2-HMAC-SHA256、10 万次迭代）、锁屏与错误提示、设置菜单五项、复位弹窗
- `android/java/com/dsh/phone/PairLinks.java` —— `dsh-market.com` 固定域名与 `/pair-accept` 链接形态
- `HANDOFF.md` —— 电脑关机/睡眠/退出 DSH/换网络的行为表、五个常见误会、安全提示
- `README.md`、`plugin/dsh-phone-pair-kit/README.md` —— 下载地址、包名 `com.dsh.phone.pair`、APK 大小与 SHA256、插件安装方式

画面里的手机与电脑界面是**示意图**（视频内带「示意图 · 非真机截图」角标）：项目没有真机截图，
本机也没有 Android 设备/模拟器可以录屏。
