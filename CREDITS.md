# 来源与致谢

本书的每一项外部依据都登记在 [`yuyu-book/sources.json`](yuyu-book/sources.json)（49 条），整书构建时渲染为书内的「来源与许可」页（HTML/PDF 均可从目录跳转）。本书**不转载任何第三方正文或代码**：GitHub 条目钉到 tag 或完整 commit，社区条目一律标注访问日期并降级为非规范来源，`snapshot`/`scope` 字段只记录「何时以何种方式读到什么」。

以下核实动作均于 **2026-10-25** 完成（HTTPS 抓取 + GitHub API 认证查询）。

## 一、版本锚点

全书技术叙述的时间基准：

| 事实 | 取值 | 取证方式 |
| --- | --- | --- |
| Claude Code 最新 GitHub release | `v2.1.310`（2026-10-23T23:39Z） | Releases API `releases/latest` |
| `v2.1.310` tag 指向的 commit | `b70dc4113ad72e0ee44f7b1b95afaf510b53ee98` | `git/ref/tags/v2.1.310` |
| `anthropics/claude-code` main HEAD | `318b7e6ac4e726e88a4ad326214866a93c373b1b`（2026-10-24T02:18Z） | `commits/main` |
| 该 HEAD 下 CHANGELOG 首条版本 | `2.1.310`（与 release tag 一致） | raw.githubusercontent 按 commit 取文件，HTTP 200 |
| npm `@anthropic-ai/claude-code` | latest/next `2.1.310`，stable `2.1.308`，累计 550 个版本，`engines.node >= 22` | registry.npmjs.org 包元数据 |
| Agent SDK Python | `v0.2.174` → commit `0e89b298e771259378a6cd3734e00d323dff5703` | Releases API + `commits/<tag>` |
| Agent SDK TypeScript | `v0.3.310` → commit `019515d3268e6f94946eb2d8e9edc1ea79c5a6aa` | Releases API + `git/ref/tags` |
| MCP 规范最新定版 | `2026-07-28`（上一版 `2025-11-25`） | 规范页 HTTP 200 + 规范仓库 tags 序列 |
| 本书仓库 main HEAD | `12e29d6697993f5f6809c6d01755ff61dc6bb755`（2026-10-16） | `lintsinghua/claude-code-book` API |

SDK TypeScript 的版本尾号（`0.3.310`）与 CLI 版本尾号（`2.1.310`）同步递增，说明 SDK 与 CLI 同属一条发布列车——本书讨论「SDK 能力 vs CLI 内部机制」时以此为依据。

## 二、官方文档（21 条）

站点 `code.claude.com/docs`。核实方式：先用官方 `sitemap.xml`（2,713 个 `<loc>`，其中 `en/` 页面 227 个）与 `llms.txt` 确认页面存在，再对每个入选 URL 单独 GET 并记录 `<title>`，以排除单页应用的「软 404」。

| 登记 ID | 页面 | 支撑章节 |
| --- | --- | --- |
| `docs-how-it-works` | How Claude Code works | 前言、第 1、2 章、附录 D |
| `docs-best-practices` | Best practices for Claude Code | 前言、第 1 章 |
| `docs-interactive-mode` | Interactive mode | 第 2、14 章 |
| `docs-cli-reference` | CLI reference | 第 15 章、附录 C |
| `docs-tools-reference` | Tools reference | 第 3、14 章、附录 B |
| `docs-permissions` | Configure permissions | 第 3、4、8 章、附录 B |
| `docs-permission-modes` | Choose a permission mode | 第 4、14 章 |
| `docs-settings` | Settings files and precedence | 第 5 章、附录 A、C |
| `docs-env-vars` | Environment variables | 第 4、5、11 章、附录 C |
| `docs-memory` | How Claude remembers your project | 第 6、7 章 |
| `docs-context-window` | Explore the context window | 第 7、13 章 |
| `docs-hooks` | Hooks reference | 第 8 章 |
| `docs-sub-agents` | Create custom subagents | 第 9、10 章 |
| `docs-agent-teams` | Orchestrate teams of Claude Code sessions | 第 10 章 |
| `docs-skills` | Extend Claude with skills | 第 11 章 |
| `docs-plugins` | Plugins overview | 第 11、12 章 |
| `docs-mcp` | Connect Claude Code to tools via MCP | 第 12 章 |
| `docs-prompt-caching` | How Claude Code uses prompt caching | 第 7、13 章 |
| `docs-headless` | Run Claude Code programmatically | 第 15 章 |
| `docs-agent-sdk-overview` | Agent SDK overview | 第 9、13、15 章 |
| `docs-glossary` | Glossary | 第 2、6、7 章、附录 D |

第 14 章原本想钉 `/docs/en/plan-mode`，实测 **404**：Plan 模式已并入 `/docs/en/permission-modes`（该页讲 Shift+Tab 切模式与模式选择器），故改钉后者，不虚构链接。

## 三、GitHub 仓库与钉版（20 条）

| 登记 ID | 对象 | 钉到什么 |
| --- | --- | --- |
| `cc-changelog` | `anthropics/claude-code/CHANGELOG.md` | commit `318b7e6a…`（main 是分支不是快照，必须钉 HEAD） |
| `cc-release-v2-1-310` | 该 tag 的 Release 页 | tag `v2.1.310` + commit `b70dc411…`（防 tag 被移动） |
| `cc-issues` | Issue 列表 | 基线 commit `318b7e6a…`；列表流动，具体编号在引用时另记 |
| `gh-agent-sdk-python` | `anthropics/claude-agent-sdk-python` | tag `v0.2.174` + commit（MIT） |
| `gh-agent-sdk-typescript` | `anthropics/claude-agent-sdk-typescript` | tag `v0.3.310` + commit |
| `gh-cc-action` | `anthropics/claude-code-action` | tag `v1` + commit `925afb53…`（MIT）：官方把线束搬进 GitHub Actions |
| `gh-dxt` | `anthropics/dxt` | tag `v2.1.2` + commit `2a788100…`（MIT → Apache-2.0 过渡，均宽松）：插件分发包规范 |
| `gh-cc-router` | `musistudio/claude-code-router` | tag `v3.1.3` + commit `3b0aebf3…`（MIT）：在 Claude Code 前插一层模型/工具路由 |
| `gh-cc-templates` | `davila7/claude-code-templates` | tag `v1.29.7` + commit `ad49b119…`（MIT）：成批真实 agents / skills / hooks / MCP 配置 |
| `gh-opencode` | `anomalyco/opencode`（原 `sst/opencode`） | tag `v1.19.4` + commit `148842ef…`（MIT）：另一套从零搭的终端编码线束，仓库已改名迁移 |
| `gh-openhands` | `OpenHands/OpenHands` | tag `v1.33.0` + commit `b968abef…`（MIT）：把智能体全过程写成可回放事件流 |
| `gh-acp` | `zed-industries/agent-client-protocol` | tag `schema-v1.26.0` + commit `e2d83349…`（Apache-2.0）：编辑器与智能体进程之间的第二份协议 |
| `gh-playwright-mcp` | `microsoft/playwright-mcp` | tag `v0.0.83` + commit `f183dad4…`（Apache-2.0）：把浏览器能力摊成工具 schema 的 MCP 服务器 |
| `gh-mcp-servers` | `modelcontextprotocol/servers` | tag `v2.1.0` + commit `ef9808f7…`（MIT → Apache-2.0 过渡）：官方参考实现目录 |
| `gh-codex` | `openai/codex` | tag `rust-v0.164.0` + commit `6aaac694…`（Apache-2.0）：本地沙箱与审批独立成层 |
| `gh-gemini-cli` | `google-gemini/gemini-cli` | tag `v0.65.0` + commit `6006c14a…`（Apache-2.0）：README 已声明官方入口迁往 Antigravity CLI |
| `gh-superpowers` | `obra/superpowers` | tag `v7.0.1` + commit `2ce8aa15…`（MIT）：方法论装成 skills / 子智能体，多宿主分发 |
| `gh-claude-mem` | `thedotmack/claude-mem` | tag `v15.2.1` + commit `35e24ba7…`（Apache-2.0）：插件形态的跨会话记忆层 |
| `gh-learn-cc` | `shareAI-lab/learn-claude-code` | main HEAD `ce8f9f18…`（MIT，无 release，故钉当时分支头并在 `snapshot` 说明）：从零重建线束的双语教材 |
| `gh-book-repo` | `lintsinghua/claude-code-book` | commit `12e29d66…`：自我引用锚点，便于日后 diff 复盘哪些结论已过期 |

**摄取姿态**：这 14 条生态条目是**对照面，不是依据**。正文的每条技术论断仍只由官方文档、Anthropic 研究博客、MCP 规范与 Claude Code 仓库本身支撑；生态仓库回答的是另一类问题——同一层边界在别人手里会长成什么形状（可换的路由层、另一种上下文路线、第二份协议、无人值守时的权限退化）。所以 `scope` 一律写明「第几章的对照面」，`snapshot` 记下 star 量级、最近推送日期与是否归档，日后一眼能看出某个对照面是否已经停摆。候选里 `Aider-AI/aider`（最后一次推送 2026-05-22，已偏旧）、`github/github-mcp-server` 与 `modelcontextprotocol/typescript-sdk`（与已登记条目重合）经比对后未纳入。全部 14 条的 tag→commit 解析走 GitHub API（引用式 tag 再经 `/git/tags` 解引用取完整 40 位 SHA），许可按各仓库 LICENSE 原文核对，仅收 MIT / Apache-2.0 一类的宽松许可。

## 四、协议规范与工程博客（5 条）

| 登记 ID | 对象 | 发布日期 | 支撑章节 |
| --- | --- | --- | --- |
| `mcp-spec-2026-07-28` | `modelcontextprotocol.io/specification/2026-07-28` | 2026-07-28 | 第 12 章协议基线 |
| `blog-building-effective-agents` | Building Effective AI Agents | 2024-12-19 | 第 1 章、附录 D（workflow / agent 之辨） |
| `blog-multi-agent-research` | How we built our multi-agent research system | 2025-06-13 | 第 9、10 章（编排者—工作者、上下文隔离的代价） |
| `blog-writing-tools-for-agents` | Writing effective tools for AI agents | 2025-09-11 | 第 3、12 章（工具粒度与选择准确率） |
| `blog-context-engineering` | Effective context engineering for AI agents | 2025-09-29 | 第 6、7 章（上下文预算、compaction 的定位） |

MCP 规范以规范仓库的 tags 序列（`2026-07-28`、`2026-07-28-RC`、`2025-11-25`、`2025-06-18`、`2025-03-26`）确认它是定版而非草案；上一版 `…/specification/2025-11-25` 也已核实为 200，作为第 12 章版本协商的对照来源。

四条博客在抓取时均发生一次 `/engineering/*` → `/research/*` 的 301，登记时使用**跳转后的规范 URL**。早年的《Claude Code Best Practices》博客现已 301 到 `code.claude.com/docs/en/best-practices`，即内容已并入官方文档；为避免同一内容出现两个条目，只在 docs 族登记一次，重定向关系写进 `snapshot`。

## 五、npm（1 条）

`npm-claude-code` 指向 `registry.npmjs.org/@anthropic-ai/claude-code` 的包元数据（`www.npmjs.com` 页面被 Cloudflare 人机验证拦截，取不到可核实的正文）。注意 `stable` 与 `latest` 当时相差一个 patch：涉及「某行为从哪个版本开始」时必须区分安装渠道。

## 六、社区材料（非规范）

感谢 [Linux.Do](https://linux.do/) 社区对本书的讨论、勘误与网页版衍生项目。帖级落点：

- [`ld-topic-1870593`](https://linux.do/t/topic/1870593) —— 【开源千星】《御舆：解码 Agent Harness——Claude Code 架构深度剖析》，板块「文档共建」，2026-03-31/04-01。
- [`ld-topic-1871393`](https://linux.do/t/topic/1871393) —— [开源] 基于站内项目构建的网页版 book，2026-04-01。

两条帖子的直连均为 **403**（Cloudflare 反爬，HTML 与 Discourse JSON 接口都封锁，换 UA 无效），标题/板块/作者/日期经搜索引擎索引的多个结果交叉确认。因此它们只记录来源谱系与社区脉络，`normative: false`，**不支撑任何技术事实**；技术事实一律由文档、GitHub、规范与博客条目承担。

## 七、未能核实，故不登记

| 尝试的 URL | 结果 |
| --- | --- |
| `code.claude.com/docs/en/plan-mode` | 404，改钉 `permission-modes` |
| `modelcontextprotocol.io/docs/getting-started/introduction` | 404，第 12 章只钉规范正文页 |
| `anthropic.com/engineering/managing-instruction-memory-hierarchical-technique` | 404，第 6 章改由 `docs-memory` + 上下文工程博客支撑 |
| `…/specification/2026-07-28/basic/lifecycle` | 301 → `/basic/versioning`，引用时用跳转后 URL |
| `www.npmjs.com/package/@anthropic-ai/claude-code` | 403，改用 registry JSON |
| `www.reddit.com/r/ClaudeAI/*.json`、`old.reddit.com/...` | 403；后者虽 200 但正文是登录墙页 —— 状态码 200 不等于内容可核实，故不登记 |
| `api.github.com` 匿名请求 | 403（速率限制），改用已认证的 `gh api`，不影响 URL 有效性 |

## 八、图形资产

- **封面**：仓库根 `cover.png` 由 [`scripts/typeset_cover.py`](scripts/typeset_cover.py) 在未署名版画 [`scripts/assets/cover-art.png`](scripts/assets/cover-art.png) 上排版生成，只用于 README。整书的扉页不借用这张位图：它用的是 [`yuyu-book/illustrations/cover.svg`](yuyu-book/illustrations/cover.svg)——四马单辕、圆盖三十辐（与第一篇题刻同数）、车厢内立戈的一乘古车白描，与章徽同一支笔法、同样只以 `currentColor` 上色，因此屏幕、暗色与纸面三种情形下都是同一套墨色，也不需要裁切、滤镜或 base64 内嵌。
- **图版**：全书 314 张图（中英各 157）源自正文内的 Mermaid 代码块，构建时用 Mermaid `11.17.2`（`package.json` 的 devDependency）在无头 Edge/Chromium 中预渲染为 SVG 并内嵌，套用统一的「舆」主题变量；渲染缓存位于 `yuyu-book/.cache/mermaid/`，缓存键含 Mermaid 版本、浏览器版本与图源哈希。
- **装饰与插图**：车轮（辐）纹样、分隔符与章节印章均为 `yuyu_book/style.py` 内联生成的矢量图形。每单元一枚章徽、每篇一幅题刻、扉页一幅车图（共 26 份，[`yuyu-book/illustrations/`](yuyu-book/illustrations/)）是本书自绘的单线白描，只用 `currentColor` 上色、不含 id 与任何外部引用，由 [`yuyu_book/art.py`](yuyu-book/yuyu_book/art.py) 在装配前逐个把关（体积上限、`viewBox`、禁用 `id=`/`href=`/`url()`/`<style>`/`<script>`）；车图铺满整个版面，故单独享有比章徽高数倍的体积上限。章眉之下另有一条按单元 id 定种的手绘走线（`trace()`，中文 20 枚、英文 20 枚，两两不同），章末收在两轮压出、渐次散成短划的双线上（`rut()`，中文 20 枚），分部过渡页的目标与章表之间横一条手绘道路——起点一枚辐轮，一站一圈正对应该部的一章（`route_map()`，4 条，4/4/4/3 站各不相同），提示块开头是手写墨记（`ink_mark()`，中文 74 处），小节之间的分隔线收在一对焊盘之间的耦合线（`knot()`，中文 111 处），目录之后另起一页把全书画成一条路（`itinerary()`，中英各 1 幅：路头一枚辐轮、15 枚站圈、4 个岔线点，由种子定形），它的图例与侧栏入口用同三支笔的三枚小标记（`key_mark()`，每版 4 枚），章末那行按语左边坐着同一位戴斗笠、提灯笼的老驿卒（`keeper()`，中英各 20 枚）——八者都走 `currentColor`，因此暗色与纸面上自动换成对应墨色。这些图形都不引用外部图标、字体或图片素材。
- **Star History**：`docs/images/star-history-{light,dark}.svg` 由 [`scripts/star_history.py`](scripts/star_history.py) 从 star-history.com 取数生成，仅用于 README，不进入整书产物。

## 九、引用姿态与准确性

1. **分析基准**：技术描述以 Claude Code `2.1.310`（tag commit `b70dc411…`）与仓库 main HEAD `318b7e6a…` 为核对基线，外部来源统一访问日期 2026-10-25。版本更新后，凡正文写「默认值/事件名/旗标拼写」的段落都应重新比对该三处锚点。
2. **许可姿态**：`anthropics/claude-code` 的 LICENSE 为「© Anthropic PBC. All rights reserved.」，npm 包内 license 字段为 `SEE LICENSE IN README.md`——均为专有。故对 Anthropic 的源码与文档一律**只链接、只摘录最小必要的字段名/事件名等事实性标识**；Agent SDK Python 为 MIT，TS 仓库以其自身 LICENSE 为准；MCP 规范以其自身声明为准。本书文字为 CC BY-NC-SA 4.0，第三方资料保留原许可。
3. **文档在快速改写**：同一能力可能从博客迁到文档（best-practices）、从独立页并入上级页（plan-mode → permission-modes；lifecycle → versioning）。凡引用「官方怎么说」，优先指向现行文档页，并把历史 URL 的重定向关系记在 `snapshot` 里。
4. **流动内容不作规范源**：issue 列表、论坛帖、星标数（本书仓库当日 `stargazers_count` 为 4324）只用于时间脉络。
5. **可复现性**：`sources.json` 对 GitHub 条目钉 tag + 完整 SHA，文档/博客条目记访问日期与页面标题，社区条目额外标 `normative:false`；`manifest.json` 的 `guides[*].sources` 把 20 个单元各自映射到 3–9 条来源，任何一条正文论断都能回溯到「当时可见的哪个快照」。

## 十、构建与校验

`yuyu-book/build.py` 在每次构建时执行契约校验：manifest 引用的文件必须存在、磁盘上的单元必须被 manifest 收录、罗盘（本章问题/读完交付/本章边界）中英双全、每条来源已登记且过许可门禁、通俗层的每一句白话都带指得回书稿的行号证据、磁盘上的每一枚插图都必须真的上了页面、HTML 产物零断链、零重复 id、零外部资源引用。CI 见 [`.github/workflows/book.yml`](.github/workflows/book.yml)。
