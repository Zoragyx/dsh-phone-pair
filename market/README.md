# 提交到 DSH 插件市场（awesome-dsh-plugin 目录）

本目录是**投稿材料**，不是插件本体。插件本体在 `../plugin/dsh-phone-pair-kit/`。

## 为什么需要这一步

`dshmarket`（本机的市场 bundle）读的是一份**人工收录目录**，不是实时 npm 搜索：

- `node_modules/dshmarket/lib/regions.js:63` → `CATALOG_OFFICIAL = 'https://awesome-dsh-plugin.com/plugins.json'`
- 该 JSON 由 `https://github.com/awesome-dsh-plugin/awesome-dsh-plugin` 生成（4481 条，`updated=2026-10-10`）
- 收录方式只有一个：向那个仓库提一个 PR，**只加一个 YAML 文件**

所以市场里能不能搜到我们，取决于这个 PR 有没有被合并。

## 文件

| 文件 | 用途 |
| --- | --- |
| `entry.yml` | 投稿的唯一一个 YAML 文件，内容原样提交 |
| `PR-body.md` | PR 正文（含门槛核对表与「手机端必须先装」的说明） |
| 本文件 | 运行手册 |

条目文件名由脚本按下游规则生成：`data/plugins/Zoragyx__dsh-phone-pair--plugin-dsh-phone-pair-kit.yml`
（`<owner>__<repo>` + `--` + 子目录路径，斜杠换成 `-`）。

## 门槛（对照 `contributing.md`）

| 要求 | 我们的状态 |
| --- | --- |
| `package.json` 声明 `dsh.bundle`（只声明 `dsh.client` 会被拒） | ✅ `plugin/dsh-phone-pair-kit/package.json` |
| 仓库有真实代码 | ✅ APK 源码、测试与构建/校验工具在 `android/` |
| 仓库创建满 1 天（CI 自动检查） | ⏳ 创建于 2026-10-10 21:16（本地），**2026-10-11 21:16 之后**才满足 |
| 仓库带 `dsh-plugin` topic | ✅ 已设置 |
| 描述属实、不夸大 | ✅ 描述只讲开了哪些开关，并说明手机端必须先装 |
| 一个 PR 最多 3 条、只动自己那一个文件 | ✅ 本 PR 只加 1 个文件 |
| 依赖指向原作者（规则 8） | ✅ 依赖 npm 上的 `@linxin666/dsh-remote-web-ui`，不复制源码 |
| 规则 7：纯依赖清单聚合包不收录 | ⚠️ 我们属「**合成配置**」（开启 `autoTunnel`/`relay`），规则里明确算插件、按普通标准评审，但**不保证一次过** |

## 怎么提交

1. 门槛时间之后（**2026-10-11 21:16 本地起**），把 token 写进 `C:\Users\Zora\.dsh\github-token.txt`
   （classic token 需 `public_repo` 或 `repo` 权限；用完请到 <https://github.com/settings/tokens> 手动作废）。
   下面所有命令都在 `dsh-phone-pair` 目录里跑。
2. **先上传 tarball**（`entry.yml` 里声明了 `tarball:`，URL 必须已经能下载到）：

   ```
   python tools\upload_asset.py --token-file C:\Users\Zora\.dsh\github-token.txt --file dist\dsh-phone-pair-kit.tgz
   ```

   期望：`asset uploaded : dsh-phone-pair-kit.tgz (30997 bytes)` 与 `state : uploaded`；
   然后确认 <https://github.com/Zoragyx/dsh-phone-pair/releases/latest/download/dsh-phone-pair-kit.tgz> 是 200。
   ⚠️ **不变量**：以后每次发新 Release，都要用同一个命令把 `dist\dsh-phone-pair-kit.tgz` 重新挂上去，
   否则 `latest/download/` 会 404。tarball 由 `cd plugin\dsh-phone-pair-kit; npm.cmd pack` 生成
   （v1.0.3 在 2026-10-17 重挂过一次：README 加了「公开自测版」说明，现在是 30 997 字节，
   SHA256 `DD57B09290037E9C53D988EC42F918EDDEE75FC012927C746350F893B63DA9E4`；
   更早的 30 469 / `4CB07527…`（纯文案前）和 29 927 / `CCEC39E6…`（v1.0.1）都已作废）；
   改过插件内容就要重新 pack 覆盖 `dist\dsh-phone-pair-kit.tgz`。
3. **先推仓库更新**，再提 PR（市场详情页渲染插件 README，评审点进去要能立刻看到「先装手机端 App」）：

   ```
   python tools\publish_github.py --token-file C:\Users\Zora\.dsh\github-token.txt --src dsh-phone-pair-release
   ```

4. **匿名预检**（不需要 token）：

   ```
   python tools\submit_market.py
   ```

   期望看到：`dsh.bundle : {'patch': './cordis.patch.yml'}`、`topics : … dsh-plugin …`、
   `age … h`（≥24 才通过）、`entry upstream : free (HTTP 404)`，最后
   `all anonymous checks passed; add --token-file <path> to open the pull request`。
   仓库未满 1 天时会打印 `preconditions NOT met: - repository is younger than 1 day (…h); retry in … h`。
5. **正式提交**：

   ```
   python tools\submit_market.py --token-file C:\Users\Zora\.dsh\github-token.txt --delete-token-file
   ```

   脚本会：fork 目录仓库 → 在分支 `zoragyx__dsh-phone-pair--plugin-dsh-phone-pair-kit` 上写那一个 YAML →
   开 PR → 打印 `pull request : https://github.com/awesome-dsh-plugin/awesome-dsh-plugin/pull/<n>`
   → 删除 token 文件。

## 「先装手机端 App」这句话放在了哪里

市场里能被人看到的三处文字，都写了必须先装手机端：

1. `entry.yml` 的 `description.en` / `description.zh` —— 目录列表与详情页的简介；
2. `plugin/dsh-phone-pair-kit/README.md` **最顶部**的告示块（含 App 图标与 Releases 链接）——
   市场详情页会渲染这个 README（`dshmarket/client/client.js` 的 `readme` 字段）；
3. 仓库首页 `README.md` 的插件小节。

## 如果被以「规则 7」拒了

回复里说明我们做的是配置合成（`autoTunnel` + `relay`）而不是纯依赖清单；若维护者仍认为不算，
可选退路：把 kit 发布到 npm 并把 `repository` 指回本仓库，或者放弃市场、继续用 Release + ZIP 安装
（`README.md` 里已有本地目录安装与 ZIP 安装的说明）。
