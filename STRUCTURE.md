# 仓库结构

本仓库分两层：**书稿**（Markdown，全书唯一内容源）与**构建器** `yuyu-book/`（把书稿合成单文件 HTML / A4 PDF）。内容层保持只读，结构层（锚点、目录、图号、脚注、书签、页码）全部在构建时派生。本文只描述现状，路径均可在仓库中直接验证。

## 1. 顶层地图

```text
/
├── 00-前言.md                中文前言（全书第 1 个单元）
├── 第一部分-基础篇/           第 1–4 章
├── 第二部分-核心系统篇/        第 5–8 章
├── 第三部分-高级模式篇/        第 9–12 章
├── 第四部分-工程实践篇/        第 13–15 章
├── 附录/                    附录 A–D
├── en/                      英文镜像，目录与文件一一对应
├── cover.png                封面图（只上 README；整书扉页用的是自绘矢量车图）
├── README.md / en/README.md  双语门面与目录
├── LICENSE                  CC BY-NC-SA 4.0 法律文本
├── STRUCTURE.md             本文件
├── CONTRIBUTING.md          环境与协作规范
├── Makefile                 常用构建入口（help/book/book-pdf/check/index/clean）
├── package.json             Node 侧依赖与 check:diagrams 脚本（engines: node >=22）
├── package-lock.json
├── scripts/                 书稿检查、封面排版、Star History
├── tests/                   Python 单测（test_star_history.py）
├── docs/images/              star-history-light.svg / star-history-dark.svg
├── yuyu-book/               整书构建器（见下）
└── .github/workflows/       check-book.yml / book.yml / update-star-history.yml
```

## 2. 书稿：20 个单元

单元（unit）是构建器眼中的最小装配单位：1 个前言 + 15 章 + 4 篇附录 = 20。每个单元在 `yuyu-book/manifest.json` 里登记一个 `id` 和双语两个路径，两个路径都必须存在（`core.validate_configs()` 会逐个检查）。

| id | 中文路径 | 英文路径 |
|----|----------|----------|
| `front` | 00-前言.md | en/00-Foreword.md |
| `ch01` | 第一部分-基础篇/01-智能体编程的新范式.md | en/Part-1-Foundations/01-The-New-Paradigm-of-Agent-Programming.md |
| `ch02` | 第一部分-基础篇/02-对话循环-Agent的心跳.md | en/Part-1-Foundations/02-The-Dialog-Loop-Heartbeat-of-an-Agent.md |
| `ch03` | 第一部分-基础篇/03-工具系统-Agent的双手.md | en/Part-1-Foundations/03-The-Tool-System-Agent-Hands.md |
| `ch04` | 第一部分-基础篇/04-权限管线-Agent的护栏.md | en/Part-1-Foundations/04-The-Permission-Pipeline-Agent-Guardrails.md |
| `ch05` | 第二部分-核心系统篇/05-设置与配置-Agent的基因.md | en/Part-2-Core-Systems/05-Settings-and-Configuration-Agent-DNA.md |
| `ch06` | 第二部分-核心系统篇/06-记忆系统-Agent的长期记忆.md | en/Part-2-Core-Systems/06-The-Memory-System-Agent-Long-Term-Memory.md |
| `ch07` | 第二部分-核心系统篇/07-上下文管理-Agent的工作记忆.md | en/Part-2-Core-Systems/07-Context-Management-Agent-Working-Memory.md |
| `ch08` | 第二部分-核心系统篇/08-钩子系统-Agent的生命周期扩展点.md | en/Part-2-Core-Systems/08-The-Hook-System-Agent-Lifecycle-Extension-Points.md |
| `ch09` | 第三部分-高级模式篇/09-子智能体与Fork模式.md | en/Part-3-Advanced-Patterns/09-Sub-Agents-and-the-Fork-Pattern.md |
| `ch10` | 第三部分-高级模式篇/10-协调器模式-多智能体编排.md | en/Part-3-Advanced-Patterns/10-The-Coordinator-Pattern-Multi-Agent-Orchestration.md |
| `ch11` | 第三部分-高级模式篇/11-技能系统与插件架构.md | en/Part-3-Advanced-Patterns/11-The-Skill-System-and-Plugin-Architecture.md |
| `ch12` | 第三部分-高级模式篇/12-MCP集成与外部协议.md | en/Part-3-Advanced-Patterns/12-MCP-Integration-and-External-Protocols.md |
| `ch13` | 第四部分-工程实践篇/13-流式架构与性能优化.md | en/Part-4-Engineering-Practice/13-Streaming-Architecture-and-Performance-Optimization.md |
| `ch14` | 第四部分-工程实践篇/14-Plan模式与结构化工作流.md | en/Part-4-Engineering-Practice/14-Plan-Mode-and-Structured-Workflows.md |
| `ch15` | 第四部分-工程实践篇/15-构建你自己的Agent-Harness.md | en/Part-4-Engineering-Practice/15-Building-Your-Own-Agent-Harness.md |
| `apxa` | 附录/A-源码导航地图.md | en/Appendices/A-Architecture-Navigation-Map.md |
| `apxb` | 附录/B-工具完整清单.md | en/Appendices/B-Complete-Tool-Inventory.md |
| `apxc` | 附录/C-功能标志速查表.md | en/Appendices/C-Feature-Flag-Reference.md |
| `apxd` | 附录/D-术语表.md | en/Appendices/D-Glossary.md |

四个篇（`p1`–`p4`）在 manifest 里除 `units` 外还带 `no`/`title`/`motto`/`goal`，用于生成篇分隔页。中英文各有 157 个 Mermaid 围栏（合计 314），双语图源文本不同，因此分别渲染。

## 3. `yuyu-book/` 构建器

### 3.1 `build.py`（命令行入口）

从仓库根目录运行 `python yuyu-book/build.py`。参数就是它实际接受的那些：

| 参数 | 实际行为 |
|------|----------|
| `--lang zh\|en\|both` | 默认 `both`，按 zh、en 顺序各装配一版 |
| `--pdf` | 在 HTML 之后追加 PDF 工序；与 `--check` 同时给出时**不生效**（`do_pdf = args.pdf and not args.check`） |
| `--check` | 构建到临时目录 `yuyu-check-*`，只跑校验，不写 `dist/`、不出 PDF |
| `--out-dir <dir>` | 输出目录，默认 `yuyu-book/dist` |
| `--browser <path>` | 显式指定 msedge/chrome 可执行文件，mermaid 预渲染与 PDF 都用它 |
| `--edge <path>` | 只作用于 PDF，优先于 `--browser` |
| `--mermaid render\|source` | `render`（默认）启动浏览器把图源渲染为 SVG；`source` 不启动浏览器，把图源以 `<pre class="mermaid-source">` 排进去 |
| `--no-autolink` | 关闭"第 N 章 / Chapter N / 附录 X"的自动加链 |
| `--no-plain` | 整层关掉通俗层：不标术语、不出导读带与新词面板、不盖 tier 徽、书末不排「原理札记」与「按语集」、章末不坐驿卒（插图不受影响） |
| `--regen-index` | 从附录 D 的术语表重建 `subject-index.json`；注意它**不会**只生成索引——之后仍会继续走完整个构建流程 |

`build.py` 里还有一个 `glossary_to_index()`：它围栏敏感地读附录 D 的表格，把术语映射到章节 anchor。

装配完成后、落盘之前有两道全书级的笔：`render.glue_closer()` 在单元内部把章末车辙缝进它收束的那一段（见上表 `render.py`），`render.soften_long_names()` 则在拼好的整份正文上给长标识符下断点——放在装配之后而不是单元管线里，是因为前后附属页根本不走单元管线，而一条引用 `getFeatureValue_CACHED_MAY_BE_STALE` 的修订说明曾在 390px 屏幕上把整份文档顶出 37px。

### 3.2 `yuyu_book/` 包：一个模块一件事

| 模块 | 单一职责 |
|------|----------|
| `core.py` | 路径常量（`BOOK_DIR` / `REPO_ROOT` / `CACHE_DIR`）、统一 UTF-8 读写、manifest 与 sources 的加载和校验、`Unit` 数据类、**围栏敏感**的 H1 归一（`normalize_h1`）与 Mermaid 抽取（`extract_mermaid`，把每段图源换成 `@@MM:<12位sha1>@@` 占位符并记下代码围栏语言）。全部失败都抛 `BuildError` |
| `render.py` | 单个单元的 Markdown → HTML 管线：重建 H1 → python-markdown（`extra` + `sane_lists` + `toc(book_slug)` + `codehilite`）→ 游离尖括号转义（`Tool<I,O,P>` 不会被当标签吞掉）→ 引号排版 `curlify` → 代码板语言角标 `stamp_code_langs`（同一趟顺手给每块代码的滚动 `<pre>` 加 `tabindex="0"`：最长的一行伸出 1555px，没有停靠点键盘就到不了） → callout 分类 → 外链上标脚注与章末链接清单 → 表格外层滚动容器（`wrap_tables()` 给外壳带 `tabindex="0"`——屏幕上的宽表横向滚动，没有停靠点就摸不到被切掉的列；）→ 图版 `<figure>`（`floor_wide_svg()` 给 viewBox 宽 >1150 单位的图版加 `min-width`，屏幕侧横向滚动保住可读字号，打印侧由 `@media print` 归零回到整页可见；`plate_cap()` 按竖版版心 665×926px 算出这张图的高度上限写进 `--plate-cap`，`plate_landscape()` 判断竖着排版字号会掉到 6pt 以下、横过来能到 5pt 以上的图，加 `landscape` 类让它独占一张横向 A4）→ 章末缝合 `glue_closer()`（Chromium 认 `break-inside:avoid` 却不认 `break-before:avoid`：车辙孤零零排在单元末尾时，纸面上会为它那一小截挪不动的留白整张空着——现在车辙与它收束的那一段包进 `.ch-close` 一起搬页；尾巴超过一页高、或末尾本身就是图版/表格/大段代码的单元不缝，宁可空也不搬不动的东西）→ 全书长名断点 `soften_long_names()`（不在单元管线里，由 `build.py` 在整书装配后施加一次，前后附属页因此同样受益：术语匹配与目录都按原文读，不能被 `<wbr>` 切开。只查 ≥12 字符的连续串，且只在 `_`、`/` 与 camelCase 边界下刀，`<pre>`/`<svg>`/标题一律不动，普通英文词永不切断。`overflow-wrap` 既不产生“优先断点”也不参与 min-content，所以 390px 上一根 33 字符的名能把整行拉成字距空洞（`getFeatureValue_CACHED_MAY_BE_STALE` 占掉 96% 行宽），纸面上则能把整张表顶出版心；显式 `<wbr>` 两样都修好，且只在真放不下时才断）→ 单元 id 前缀 → `RefLinker` 交叉引用自动加链 |
| `pages.py` | 前后附属页与罗盘卡：封面、版本与许可、版本与修订、阅读路线、全书线路图、篇分隔页、目录、原理札记、按语集、来源与许可、主题索引，以及双语 UI 标签表。`compass()` 渲染"本章问题 / 读完交付 / 本章边界"三张卡加"来源锚点"chips；`principles_page()` 把每条 core 术语的 `why` 按章排成一页（纸面没有悬停，理由必须有另一条路走到读者眼前）；`notes_page()` 把 20 行按语按阅读顺序排成书末「按语集」，每行的章题链回正文——章末那一行只是它路过的位置，合集才是它能被检索、被读完的地方；`route_map_page()` 把全书画成一条路（前言是路头的辐轮，戴目录同一枚序号 `FRONT_NO`），图下再列一份带链接的站表——`aria-hidden` 的画里没有可达的编号，也没有链接；`part_divider()` 在篇分隔页起头放该篇题刻；`lead_band()` 放章首白话导读带；`fill_index_folios()` 把量好的页码写进主题索引每行预留的空位——按行自己链接的锚点认领而不按头词字面，空位没人填或多出一位都让构建失败；`note()` 把修订说明里的反引号排成真代码元素——这些笔记引用的是构建器自己的名字，一溜裸反引号在排好的书里读起来像笔误 |
| `plain.py` | 通俗层：加载并校验 `glosses.json` 与 `reading-paths.json`。给正文首现术语套 `<span class="gloss">`（屏幕上悬停出白话浮窗，纸面上退回章末「新词」面板（按单元类型改称「本章新词」「开篇新词」「本附录新词」）；浮窗有两种落位——屏幕宽过「版心 + 浮窗」= 67rem 才贴着术语浮起，否则钉在视口底部作说明条，而宽表里的术语任何宽度都用说明条，因为横向滚动的容器会把画在它里面的浮窗一并裁掉），给每个单元算新词清单，给每个 H2 按位置表盖「起步 / 主干 / 进阶」tier 徽，并把 manifest 里的 `plain`/`analogy` 装配成导读带；浮窗本身是三层——白话定义、`why`（它非这样不可的理由）、`analogy`（比方），`why` 排在定义之后、比方之前。白话不许自由发挥：`validate_plain()` 要求每条证据 `file:line` 落在代码围栏之外且该行确实含登记过的表面词形，core 词条与每条导读带在中英两侧都要有证据；`why` 另有自己的 `why_evidence`，中英各一行、同样要落进正文的散文——理由不能是构建器替书稿编的；按语另有 `validate_notes()`，它读的是**该单元自己的源文件**：一条按语必须含一个已注册词形，且那个词形真的站在它那一章的正文里（术语锁），中文 ≤36 字、英文 ≤130 字符，英文里出现汉字即错，20 个单元一个都不能缺、也不许多出一个没主的 |
| `art.py` | 插图装载：`illustrations/<unit-id>.svg` 是每单元一枚章徽，`illustrations/part-<id>.svg` 是每篇一幅题刻，`illustrations/cover.svg` 是扉页那幅四马古车图版。`_read()` 在装配前逐个把关——章徽/题刻不超过 6 KB、扉页图版另有 `PLATE_BYTES` 上限，都要带 `viewBox`、只用 `currentColor` 描线，且不得出现 `id=`、`href=`、`url(`、`<style>`、`<script>`。同一份图会被内联进单文件几十次，一个 id 就是一次重复 id；`currentColor` 则是"一张图同时管屏幕、暗色与纸面"的前提 |
| `mermaid.py` | 图版预渲染与缓存：`.cache/mermaid/` 下的 SVG 以 `sha1(配色指纹 + mermaid 版本 + 浏览器版本 + 图源)` 为键（指纹由 `_style_fingerprint()` 现算，改一个色值旧图就会失效，不会拿旧配色继续服务）；`THEME` 是全书统一的图板配色，但主题只及于作者没管过的节点——正文另有 696 条 `classDef`、192 条 `style` 自带 Material/Tailwind 色，`reink_colors()` 在渲染前按色相把它们并入 `BOOK_FAMILIES` 的七组书色（fill 决定角色，`color:` 一律换成该角色的墨色，因为映射后的底色都是浅色，作者原来写的白字会看不见），图源文件本身不改；`captions_for()` 取该图之上最近的 H2 作图题（`block.line` 就是文件行号，所以紧贴围栏的标题也算），其上什么都没有才回落为"架构示意"/"Architecture sketch"；`source_fallback()` 供 `--mermaid source` 使用。图版刻意保持 crisp 直线：mermaid 11 的顶层 `look:'handDrawn'` 实测把单张图从 16.8 KB 抬到 111 KB、最大那幅从 78 KB 抬到 1.26 MB（rough.js 每个形状多道抖动描边），314 张全换会让单文件整书涨到几十 MB，手绘气质因此由 `style.py` 的走线、车辙、道路与墨记承担 |
| `audit.py` | 落盘前的 HTML 契约检查，见第 6 节 |
| `style.py` | 整书样式表与页面外壳：`CSS`、`page()`，以及一整套内联矢量装饰——车轮纹样 `wheel()`、章眉下按单元 id 定种的手绘走线 `trace()`、章末渐次散开的车辙 `rut()`、分部过渡页的手绘道路 `route_map()`（后四者都按 id/部 id/种子定种，道路上的站圈数即该部的章数）、全书线路图 `itinerary()`（一条蛇形路走完四个部：路头一枚辐轮代表前言、一章一圈、附录走虚线岔线并以同心圆收车）、这张图的图例与侧栏入口共用的三枚小标记 `key_mark()`、提示块的手写墨记 `ink_mark()` 与小节分隔的耦合线 `knot()`。约定是"无 web 字体、无 JS，必须在 `file://` 离线可读并能 A4 打印"。屏幕与纸面是两套契约：屏幕让宽图版和宽表横向滚动、图题里的"可横向拖动"提示随窄屏换行、中文版正文在 ≤30rem 退回左对齐（一行放不下 `CompactionResult` 时，两端对齐会把剩下的汉字摊成一条条字距沟——英文有连字可退，中文没有），`@media print` 则把它们收回版心（图版 `min-width:0`、退掉卡片底与投影、隐藏拖动提示；表头 `white-space:normal` + `word-break:keep-all`，中文头不打断，单元格只在整词放不下时才 `break-word`，长标识符的断点由 `render.py` 的 `<wbr>` 负责；封面框线撑满整个版心、主题索引恢复双栏；`@page plate-landscape` 声明横版折页的纸张，`figure.landscape` 前后强制翻页并垂直居中；章块的 2.2rem 下边距在纸上归零——那是章与章之间的空气，画不进版心时 Chromium 会为一截够不着的内边距单独留一张纸，而下一单元的强制换页使它永久化）。纸面没有滚动条，宁可换行、宁可翻页，也不能丢内容或丢字号。纸上还锁着一套**视觉词汇**，由 `test_build_contracts.py` 的 `DesignVocabulary` 逐条钉住：圆角只有两枚加一个圆——`--r-1` 转一张标签、`--r-2` 转一个盒子，`999px` 留给真是胶囊的东西（3px 标题条、滚动条滑块），第五种圆角就是同一张纸上多出来的一本书；`dashed` 只表示"这个词有白话注"（`.gloss`）与构建自己报错的那块图版（`.mermaid-missing`），别处的分隔线一律实线；朱红在纸上重调成 `#9C4630`（屏幕上的亮度印在纸上会发灰）；章首的新词面板改到章末收束一章，正文第一句因此回到开篇那一页——`ChapterOpening` 拿一次真实装配断言面板必须排在正文之后 |
| `pdf.py` | PDF 后置工序：Chromium 打印 → PyMuPDF 依据打印留下的命名目标写书签树、奇偶页眉标、页脚页码、目录页码盖章，最后写元数据并 `subset_fonts()`。成品里混着两种纸张（竖版正文 + 横版折页图版），所以眉标、页码与装饰细线一律按 `page.rect` 逐页量，不假设 A4 竖版尺寸。主题索引是盖不出来的那一样：`search_for` 做子串匹配（`Session` 会把 `SessionStart` 那行也认成自己），一个锚点又常被几十行共用、行面几乎相同，落点无从唯一确定，所以索引走两趟——`measure()` 用第一趟量出每个单元落在哪张纸，页码由 `pages.fill_index_folios()` 写进行里本就预留的空位（按 `data-ref` 认领，不按字面），第二趟才是成品；`folio_drift()` 在第二趟重读目的地，任何页码与量到的不符即构建失败。落盘前 `empty_sheets()` 逐页扫一遍正文带（顶栏 60pt 与脚注 45pt 之间，文字、矢量、位图都算内容）：只要有一张纸剩下页眉与页码这种"纯家具"，构建直接失败——章必须收在它结束的那张纸上 |

### 3.2.1 `tests/`：构建契约

`yuyu-book/tests/` 是构建器自己的单测（不启动浏览器、不渲染图、绝不写书稿）：`test_manifest`（20 单元 / 4 篇 / guides 覆盖与字段）、`test_sources`（登记完整性、钉版、许可与 CREDITS 一致性）、`test_mermaid`（围栏抽取、图题对位、缓存键、源码回落）、`test_render_anchors`（slug、id 前缀、callout、表格容器、语言角标、脚注）、`test_crossrefs`（`RefLinker` 的加链与跳过子树）、`test_audit`（第 6 节每条契约正反两面）、`test_pages`（结构页与罗盘/来源页锚点、原理札记的成页与归属、主题索引每行恰一枚页码空位与按锚点认领的填充）、`test_plain`（浮窗装配、新词面板与正文标记数一致、tier 位置表长度、`why` 的长度与双语证据门禁正反两面）、`test_notes`（按语的术语锁正反两面、长度上限、英文不许夹汉字、缺一条与多一条都算错、按语集成页与回链、驿卒图过装载器且小到能内联 20 次，最后拿真实的 `notes.json` 与 20 份单元源文件跑它自己的门禁）、`test_art`（26 份图齐全、每份都过装载器、体积上限、无重复 id，以及装载器对 `id=` / `href=` / `url(` / `<script>` / 非 `currentColor` 的拒绝）、`test_build_contracts`（WCAG 对比度、排版与打印契约、双宽度版心契约、依赖清单、仓库文档齐备，并跑一次真实的 `build.py --check --mermaid=source`）、`test_pdf`（正文带怎么算：只有页眉页码的纸是洞，图版与横版纸页不是；索引页码在量的一趟与打印的一趟之间是否还站得住）、`test_docclaims`（把 README / STRUCTURE / CREDITS / revisions 里引用的每个数字重算一遍：附录 D 词条数、白话注与 core 数、主题索引、手绘图、来源登记、每版图版、构建器测试总数；句子改了措辞导致正则找不到那句，同样算失败——数字悄悄烂掉才是真正的问题。另一半盯的是**正文声明的总数与它自己那张表**：第 8 章说的事件数必须等于汇总表行数、附录 B 数出的工具数必须等于全书每一处引用它的句子（连第 13 章 0.1–0.3ms × N 的算术一起核）、§13.5.1 的维度数以图版真正画出的枚数为准、附录 B 那行按语里的总数与附录 B 数出的行数对表（按语里宁可一个数字都不写，写了就必须能被重算），而被替换掉的旧措辞（`45+`、六十多个、26 个事件、三个维度）只要再出现就让测试红）。共享夹具（如 `test_pages.Config`）必须自己继承 `unittest.TestCase`：纯 mixin 基类会让 `discover` 静默跳过整批用例，这里曾因此有 22 个测试从未运行。跑法见 `CONTRIBUTING.md` 第 2 节。

### 3.3 数据文件

| 文件 | 内容 |
|------|------|
| `manifest.json` | 书的骨架：`version` / `date` / `author` / `repository` / `license` / `title` / `subtitle` / `epigraph` / `start_reading` + `parts`(4) / `front` / `appendices`(4) / `guides`(20)。单元条目只有 `id`、`zh`、`en` 三个字段；`guides[<id>]` 除罗盘三卡与 `sources` 外，还带通俗层的 `plain`（章首导读带）、`analogy`（打个比方）与 `plain_evidence`（指回书稿的 `file:line`） |
| `glosses.json` | 术语白话注，当前 102 条（44 个 core 会在正文画虚线）。每条 `term` / `forms`（中英表面词形）/ `plain` / `analogy` / `why` + `why_evidence`（原理句与它的出处，44 个 core 各配一对，长度上限 zh 52 / en 190）/ `priority` / `evidence`。只有 `priority: "core"` 的词会在正文里画虚线并进入章末新词面板（面板与画线的是同一批词，构建时断言）；一个术语在某章只以行内代码现身时，虚线画在那段代码上——但只画读不成普通词的形状（带 `_`、数字或驼峰接缝的标识符），`Streaming` 这类普通词仍等正文，`<pre>` 图版一律不画（图版整块来读，虚线还会打断照抄）；`extra` 不上正文也不上面板，只在附录 D 里可查——一章最多 22 个新词，超了就下调 |
| `reading-paths.json` | 三层阅读路线（起步 / 主干 / 进阶）。按单元存**位置**列表：数组长度必须等于该单元实际渲染出的 `<h2>` 数，对不上 `plain.stamp_tiers()` 直接报错，宁可不产出也不盖错章 |
| `notes.json` | 按语层：以单元 id 为键的 20 条一句话旁白（中英各一份），由那位老驿卒在章末车辙上方说出来。门禁是 `plain.validate_notes()`：必须含一个已注册词形、且该词形出现在这一单元自己的正文里（术语锁），中文 ≤36 字、英文 ≤130 字符，英文不夹汉字，一个单元都不能缺。还有一道门在 `test_docclaims`：按语里写的数字必须能被重算——`KEEPER_TOTALS` 钉住附录 B 那行的工具总数与附录 B 真正数出来的行数相等，其余任何数字都要么不写、要么得先在表里登记它从哪算来；写成汉字的「五十五」测试读不到，正是这本书被约数骗过的原因 |
| `illustrations/` | 26 份手写 SVG：20 枚单元章徽（`<unit-id>.svg`，64×64 描线）+ 4 幅篇题刻（`part-<id>.svg`，200×140 小版画）+ 1 幅扉页车图（`cover.svg`，1000×470 横构图，四马一盖车、三十辐的轮，约 11.7 KB，故享 `PLATE_BYTES`）+ 1 枚驿卒（`keeper.svg`，64×64，斗笠与提灯；章章内联一次，测试把它的体积钉在 3 KB 以内）。全部 `currentColor`，无 id、无外链，见 `art.py` |
| `sources.json` | 以来源 id 为键的 49 条登记。字段：`title` `authority` `kind` `url` `pinned` `snapshot` `accessed` `license` `scope`，`community` 类另带 `normative`。凡本书自己写的中文注（快照、许可、用途，以及带中文括注的标题与社区帖标题）都配 `*_en` 镜像，渲染时按语言取字段——门禁：镜像缺失或镜像里仍有汉字即构建失败。kind 分布：`docs` 21、`github` 20、`blog` 4、`spec` 1、`npm` 1、`community` 2；49 条全部被 `guides.sources` 引用 |
| `revisions.json` | "版本与修订"页的条目，zh / en 各一份 |
| `subject-index.json` | 书末主题索引（生成物，当前 238 个词条 = 116 条英文原名 + 122 条中文译名），由 `--regen-index` 重建。中文块排在 Z 之后（`core.INDEX_CN_LETTER = "中"` 的字典序天然靠后），标题取 `ui("index_cn")`，块下一行 `ui("index_cn_note")` 说明排检法——全书只有这一块按部首笔画排；英文版只渲染英文块，没有本语言词条的行会被跳过。每行末尾预留的页码空位在屏幕上隐藏，出 PDF 时由两趟打印填上该单元真正所在的那一页 |

### 3.4 生成物（不要手改）

```text
yuyu-book/
├── dist/                          yuyu-agent-harness-{zh,en}.html / .pdf
└── .cache/mermaid/                渲染好的 SVG + _harness.html 渲染壳
```

这两个目录都是每次构建的产物（扉页与部题刻的车轮纹是 `style.py` 里的 `WHEEL_SVG`，按次生成、不落文件），`.gitignore` 已连同临时验证目录 `yuyu-book/.scratch/` 一起忽略，仓库只提交书稿与构建器。

### 3.5 输出

- `yuyu-book/dist/yuyu-agent-harness-zh.html` / `-en.html`：自包含单文件，图片走 data URI，无外链资源、无脚本。
- `yuyu-book/dist/yuyu-agent-harness-zh.pdf` / `-en.pdf`：A4，含书签树、奇偶眉标、页脚页码与带页码的目录。

## 4. 其他工具目录

| 路径 | 作用 |
|------|------|
| `scripts/check_book.py` | 零依赖检查：全仓库 `.md` 的相对链接是否有落点、代码围栏是否闭合、Mermaid 图里是否写了字面量 `\n`（应改用 `<br/>`） |
| `scripts/check_mermaid.mjs` | 用 `package.json` 锁定的 mermaid 解析器逐图 `parse()`，由 `npm run check:diagrams` 调用（需要 Node 22+ 与 `npm ci`） |
| `scripts/typeset_cover.py` | 用本机 CJK 字体在 `scripts/assets/cover-art.png` 上排版出根目录 `cover.png`（默认字体路径是 macOS 的） |
| `scripts/star_history.py` | 生成并增量维护 `docs/images/star-history-{light,dark}.svg` |
| `tests/test_star_history.py` | 上面那个脚本的单测（`python -m unittest discover -s tests`） |
| `.github/workflows/check-book.yml` | 既有内容门：`check_book.py` + `check:diagrams` + unittest |
| `.github/workflows/book.yml` | Book CI：内容门 + `build.py --check` + 双语 PDF 产物上传 |
| `.github/workflows/update-star-history.yml` | 定时刷新 Star History |

## 5. 两层契约

**内容层是唯一真源，构建器从不写回书稿。** `yuyu-book/` 的写操作只有三处：`dist/` 下的 HTML/PDF、`subject-index.json`、`.cache/mermaid/`。除此之外，Markdown 只被读取。

结构层全部在构建时派生，因此书稿里不该出现任何手写的 HTML 锚点、图号或脚注编号：

| 你在成品里看到的 | 由谁派生 |
|------------------|----------|
| 章节锚点 `#ch09`、`#apxd`、`#front` | manifest 的单元 `id` |
| 小节锚点 `#ch02-21-异步生成器对话循环的骨骼` | `render.book_slug()` 由标题生成，再由 `prefix_ids()` 加单元前缀 |
| 图号"图 2-1" / 附录"图 A3" | `render.render_unit()` 的 `fig_no()` |
| 外链上标 `[1]` 与章末链接清单 | `render.process_links()` / `footnotes_html()` |
| "第 9 章"文字上的交叉链接 | `render.RefLinker`（`--no-autolink` 可关） |
| 侧栏导轨、目录页 | `build.build_edition()` 的 `rail` / `toc_entries` |
| PDF 书签、奇偶眉标、页脚页码、目录页码、主题索引每行的页码 | `pdf.measure()` 先量（第一趟打印只为读回命名目标），`pdf.build_pdf()` 后写；索引页码写回 HTML 预留的空位，因此出 PDF 的那趟会把数字印进同一份 HTML（屏幕仍隐藏） |
| 书末主题索引 | `build.glossary_to_index()` 读附录 D 的表格：英文原名进 A–Z，中文译名列（按 `/` 拆分）另立「中文」块，只服务中文版 |
| 代码板右上角的语言角标 | `render.stamp_code_langs()` 读围栏 info 串 |
| 术语上的虚线与悬停白话浮窗 | `plain` 层的首现标注（整层用 `--no-plain` 可关） |
| 书末「原理札记」页 | `build._principle_groups()` 按 `why_evidence` 把每条原理归到提出它的那一章，`pages.principles_page()` 排版——归属看的是**论证在哪**，不是词在哪第一次出现 |
| 章末车辙上方那行按语、书末「按语集」页 | `notes.json` 供文本；`build._article()` 把 `art.keeper()` 那枚斗笠与按语缝在车辙之前（`render.glue_closer()` 保证两者不落进同一张空纸），`pages.notes_page()` 按阅读顺序排版；`build.py` 断言正文里的 `<div class="keeper">` 数 = 合集里的 `<li class="kn-row">` 数 = 该语言有按语的单元数 |
| 章末「本章新词」面板 | `pages.new_terms_panel(hits, lang, kind)` 按单元类型选标题（本章 / 开篇 / 本附录），与正文标记数一一对应：`build.py` 断言 `n_marks == n_rows`；`build._article()` 把它排在正文与章末按语之后——它是收束一章的器具，不是开门的家具（摆在章首时它是开篇最高的一块，整张首纸花在家具上，正文第一句被推到第二页）；纸上面板整块不拆（`break-inside:avoid`），行与行的空气记在行首，注记排在词表之前——一张能跨页散开的清单最怕落单：曾经有一页只剩半句「every time」和一行注记，还有一页被 1.6px 画不进版心的行内边距整张占成空白 |
| 小节右侧的「起步 / 主干 / 进阶」徽 | `plain.stamp_tiers()` 按 `reading-paths.json` 的位置表盖章 |
| 章首白话导读带与「打个比方」 | `manifest.json` 的 `guides[<id>].plain` / `analogy` |
| 章名右侧的小图、篇分隔页的大题刻、章末的驿卒 | `yuyu-book/illustrations/`，经 `art.py` 内联；`build.py` 比对装配数与磁盘可装配数，少一枚即失败 |

由此可得三条实操结论：改了图源内容不必清缓存（uid 由内容哈希决定）；改了 manifest 的单元 `id` 就等于改了全书锚点；单元 `id` 同时是 HTML 里的 `article id`。

## 6. 落盘前的 HTML 契约

`audit.audit()` 在写出文件之前检查整份 HTML，任一项不过即 `BuildError`，构建不产出：

- 页内锚点指向不存在的 id；同一 id 出现两次
- `<script>` 标签，或非 `data:` URI 的 `<img>`（离线保证）
- 残留的 Markdown 围栏、未解析的 `@@MM:` 占位符、指向 `.md` 的残余链接
- 闭合标签不配对，或 `<pre>` / `<code>` 内部嵌了块级元素（未闭合围栏在吞正文的典型症状）
- 图版数量少于预期，或出现 `mermaid-missing`
- `article` 数量或 `compass` 卡数量少于单元数

`audit()` 之后 `build.py` 还有四道本层专属的对账，任何一道不过同样 `BuildError`：正文术语标记数必须等于章末面板行数；按语数在正文与「按语集」里必须相等、且等于该语言真有按语的单元数（写了却不排版、排了两遍都算失败）；导读带、罗盘、新词面板、tier 徽、章徽、题刻各自的数量要写进统计行并且和预期相等；磁盘上每一枚能装配的图都必须真的出现在书里（`want_emblems` / `want_heads`），画了却没上页面就算失败。

通俗层另有一道 `plain.validate_plain()`：证据指针必须落在代码围栏之外、且那一行真的含登记过的词形；core 词条与每条导读带要求中英两侧都有证据；core 词条还必须各有一句 `why`，并且这句 `why` 自己在中英两侧各有一行落入围栏外的散文（`why_evidence` 指到书外就是 `BuildError`）；一个单元的新词面板不超过 22 行；`reading-paths.json` 的位置表长度必须等于该单元的小节数。按语那一层由 `plain.validate_notes()` 把关：一条不许缺、一条不许多出来没主，中文 ≤36 字 / 英文 ≤130 字符，英文里出现汉字即错，而**术语锁**要求每句含一个已注册词形、且该词形就在它自己那一单元的源文件里——旁白可以借书的比喻，不能凭空造词，也不能指着别的章的词说自己说过。

配置层还有一道 `core.validate_configs()`：guides 必须覆盖全部单元且 `question`/`deliverable`/`boundary` 的 zh、en 两语都非空；来源引用的 id 必须存在；来源字段与 URL 规则见 `CONTRIBUTING.md`。

## 7. 改哪里（速查）

| 想做的事 | 位置 |
|----------|------|
| 改正文、加图、改表格 | 第 2 节表里的对应 Markdown，中英两份一起改 |
| 增删单元或调整篇章顺序 | `yuyu-book/manifest.json` 的 `parts` / `appendices` / `guides` |
| 改某章的问题·交付·边界卡 | `manifest.json` 的 `guides[<id>]` |
| 改某章的白话导读带或"打个比方" | `manifest.json` 的 `guides[<id>].plain` / `analogy`，改完给 `plain_evidence` 补上指得回书稿的 `file:line` |
| 加或改一条术语白话注 | `yuyu-book/glosses.json`（只想进面板、不在正文画虚线，就把 `priority` 降成 `extra`） |
| 调整某章哪些小节属于起步/主干/进阶 | `yuyu-book/reading-paths.json`（按小节顺序，长度必须等于小节数） |
| 加或改一条章末按语 | `yuyu-book/notes.json`（那句里得有一个本单元正文真的用过的注册词形，否则术语锁不让过；句中出现数字，就必须是 `test_docclaims` 重算得出来的那个） |
| 重画某章小图、某篇题刻或章末的驿卒 | `yuyu-book/illustrations/<id>.svg`（`currentColor` 描线，别加 id） |
| 新增或修订一条参考来源 | `yuyu-book/sources.json` |
| 改版本说明页 | `yuyu-book/revisions.json` |
| 改配色、版式、打印样式 | `yuyu-book/yuyu_book/style.py`（图版配色在 `mermaid.py` 的 `THEME` 与 `BOOK_FAMILIES`，后者管正文自带颜色的那 888 个节点） |
| 重生成书末索引 | `python yuyu-book/build.py --regen-index` |
| 只想知道有没有写坏 | `python yuyu-book/build.py --check`，或 `make check` |

协作流程、环境搭建与门禁细则见 [CONTRIBUTING.md](CONTRIBUTING.md)。
