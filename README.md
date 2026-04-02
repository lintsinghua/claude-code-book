<div align="center">
  
# 解码 Agent Harness —— Claude Code 架构深度剖析
  
当所有人都在教你怎么 **用** AI Agent —— 这本书带你 **拆开** 它

[![GitHub Stars](https://img.shields.io/github/stars/lintsinghua/claude-code-book?style=social)](https://github.com/lintsinghua/claude-code-book/stargazers)
[![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-lightgrey)](LICENSE)

[![在线阅读](https://img.shields.io/badge/📖-在线阅读-9f7aea?style=for-the-badge)](https://lintsinghua.github.io/)

<img width="2880" height="1558" alt="image" src="https://github.com/user-attachments/assets/39efa7d4-4521-444e-a222-fd0acb756e51" />

</div>

---

对话循环如何驱动？工具权限为何是四阶段管线？上下文压缩怎样在 token 预算内运转？子智能体如何通过 Fork 继承父级上下文？

读懂 Claude Code 的设计决策，你就拥有了一套**可迁移到任何 Agent 框架**的心智模型。

> **声明：** 本书基于对 Claude Code 公开文档和产品行为的架构分析编写，未引用、未使用任何未公开或未授权的源码。Claude Code 为 Anthropic PBC 产品，本书不隶属于、未获授权于、也不代表 Anthropic。

---

## 这本书有什么不同

**不做使用教程，不列 Prompt 技巧。**

市面上充斥着"如何写好 Prompt"和"如何调用 Agent API"的指南。但如果你想知道一个生产级 Agent 系统的**骨架**是怎么搭的——为什么用异步生成器而不是回调？为什么权限检查要分四个阶段？上下文窗口用完了怎么办？——几乎没有资料可查。

这本书填补了这个空白。它以 Claude Code 为案例，拆解一个 Agent Harness 的**每一个**核心子系统，讲清楚每个工程决策背后的"为什么"。

### 三个核心特色

- **架构分析而非 API 文档** — 不讲"怎么调用"，讲"为什么这样设计"。每个模块都追溯设计动机、分析工程权衡、指出反模式陷阱
- **设计哲学而非使用教程** — 从异步生成器到断路器模式，从依赖注入到缓存感知架构，每一章都在提炼可迁移的设计原则
- **可迁移的认知模型** — 无论你用 LangChain、AutoGen、CrewAI 还是从零构建，书中的 139 张架构图和设计模式分析都能直接复用

### 书中的数据

| 指标 | 数量 |
|------|------|
| 正文章节 | 15 章 + 4 篇附录 |
| Mermaid 架构图/流程图/状态机 | 139 张 |
| 覆盖核心子系统 | 工具系统、权限管线、上下文压缩、记忆系统、钩子系统、子智能体调度、MCP 集成、技能插件、流式架构、Plan 模式 |
| 分析的设计决策 | 50+ 个"为什么这样设计" |
| 术语条目（中英对照） | 100 条 |
| 功能标志 | 89 个 |
| 注册工具 | 50+ 个 |

---

## 目录

### Part 1. 基础篇 — 建立心智模型

> 理解 Agent 编程的范式转移，建立对 Agent Harness 的整体认知框架。

| | 章节 | 你将学到 |
|:-:|------|---------|
| 01 | [智能体编程的新范式](第一部分-基础篇/01-智能体编程的新范式.md) | AI 编程工具从 Copilot 到 Claude Code 的演进时间线；Agent Harness 的五大设计原则（异步生成器优先、安全边界内嵌、缓存感知、渐进能力扩展、不可变状态流）；技术栈选型分析（Bun + React/Ink + Zod v4） |
| 02 | [对话循环 — Agent 的心跳](第一部分-基础篇/02-对话循环-Agent的心跳.md) | `while(true)` 异步生成器主循环的完整生命周期（初始化→预处理→API调用→工具执行→结果回填）；五种 yield 事件类型；十种终止原因与状态机模型；`QueryDeps` 依赖注入的可测试性设计 |
| 03 | [工具系统 — Agent 的双手](第一部分-基础篇/03-工具系统-Agent的双手.md) | `Tool<Input, Output, Progress>` 五要素协议（名称/Schema/权限/执行/渲染）；`buildTool` 故障安全工厂函数；45+ 工具按 12 类注册；并发分区的贪心算法；`StreamingToolExecutor` 四态状态机；延迟工具发现（ToolSearchTool） |
| 04 | [权限管线 — Agent 的护栏](第一部分-基础篇/04-权限管线-Agent的护栏.md) | 四阶段管线（Schema 验证→规则匹配→上下文评估→交互式确认）；五种权限模式谱系（default→plan→auto→bubble→bypass）；Bash 规则匹配（精确/前缀/通配符）；推测性分类器的 2 秒 Promise.race；`ResolveOnce` 并发安全原子声明 |

### Part 2. 核心系统篇 — 深入子系统

> 拆解 Agent Harness 的四大核心子系统——配置、记忆、上下文、钩子。

| | 章节 | 你将学到 |
|:-:|------|---------|
| 05 | [设置与配置 — Agent 的基因](第二部分-核心系统篇/05-设置与配置-Agent的基因.md) | 六层配置优先级链（plugin→user→project→local→flag→policy）；合并规则（数组拼接去重/对象深度合并/标量覆盖）；安全边界：为什么 `projectSettings` 被排除在安全检查之外（防恶意仓库供应链攻击）；编译时 `feature()` 与运行时 GrowthBook 双层功能门控 |
| 06 | [记忆系统 — Agent 的长期记忆](第二部分-核心系统篇/06-记忆系统-Agent的长期记忆.md) | 四种封闭式记忆类型（user/feedback/project/reference）；"只保存无法从当前状态推导出的信息"的设计哲学；MEMORY.md 索引文件（200 行/25KB 上限）；Fork 的自动记忆提取与主 Agent 互斥机制；`CacheSafeParams` 对提示缓存共享的影响 |
| 07 | [上下文管理 — Agent 的工作记忆](第二部分-核心系统篇/07-上下文管理-Agent的工作记忆.md) | 有效窗口公式与多级缓冲阈值；四级渐进压缩策略（Snip→MicroCompact→Collapse→AutoCompact）；断路器模式（连续 3 次失败后熔断，源自 1,279 个会话的真实数据）；压缩提示工程的双阶段输出（`<analysis>` 丢弃 + `<summary>` 保留）；压缩后令牌预算（50K 总额/5K 每文件） |
| 08 | [钩子系统 — Agent 的生命周期扩展点](第二部分-核心系统篇/08-钩子系统-Agent的生命周期扩展点.md) | 五种 Hook 类型（Command/Prompt/Agent/HTTP/Function）；26 个生命周期事件（工具调用/用户交互/会话/子Agent/压缩）；结构化 JSON 响应协议（approve/block + `updatedInput`/`additionalContext`）；Hook 来源六层优先级；三层安全机制（全局开关/企业控制/工作区信任） |

### Part 3. 高级模式篇 — Agent 的组合与扩展

> 探索 Agent 如何组合、编排和扩展——从子智能体到 MCP 协议桥接。

| | 章节 | 你将学到 |
|:-:|------|---------|
| 09 | [子智能体与 Fork 模式](第三部分-高级模式篇/09-子智能体与Fork模式.md) | `BaseAgentDefinition` 类型与三种 Agent 来源（内置/自定义/插件）；四种内置 Agent（Explore 只读/Plan 结构化/General 全量/Verification 对抗性）；Fork 模式的字节级上下文继承（`CacheSafeParams` 五维度 + 占位符工具结果最大化缓存命中面积）；递归 Fork 防护；自定义 Agent 的 Markdown frontmatter 格式 |
| 10 | [协调器模式 — 多智能体编排](第三部分-高级模式篇/10-协调器模式-多智能体编排.md) | Coordinator-Worker 架构的双重门控；协调器的"只编排不执行"约束；`INTERNAL_WORKER_TOOLS` 与工具隔离；`TeamCreateTool`/`SendMessageTool` 的四种寻址模式（点对点/广播/UDS/Bridge）；基于会话路径的 Scratchpad 协作空间；四阶段工作流（Research→Synthesis→Implementation→Verification） |
| 11 | [技能系统与插件架构](第三部分-高级模式篇/11-技能系统与插件架构.md) | 11 个核心内置技能；`SKILL.md` frontmatter 完整字段（name/description/arguments/allowed-tools/model/effort/context/agent/paths/hooks）；三级参数替换（`$ARGUMENTS`/位置`$0-$1`/命名`$foo`）；分层加载（managed→user→project→plugin→bundled）；`discoverSkillDirsForPaths` 动态技能发现；插件缓存优先加载与 MCP 间接注册 |
| 12 | [MCP 集成与外部协议](第三部分-高级模式篇/12-MCP集成与外部协议.md) | 8 种传输协议（stdio/sse/sse-ide/http/ws/ws-ide/sdk/claudeai-proxy）；`MCPConnectionManager` 五态连接管理；三段式工具命名（`mcp__{server}__{tool}`）；7 个配置范围与服务器审批/拒绝列表；Bridge 双向通信系统（SSE 序列号连续性/`BoundedUUIDSet` 回声去重/v1-v2 传输抽象/三重权限门控） |

### Part 4. 工程实践篇 — 从原理到构建

> 性能优化的工程细节，以及从零构建一个完整 Harness 的实战路线图。

| | 章节 | 你将学到 |
|:-:|------|---------|
| 13 | [流式架构与性能优化](第四部分-工程实践篇/13-流式架构与性能优化.md) | `QueryEngine` 有状态查询生命周期管理器；`StreamingToolExecutor` 并发控制（安全工具可并行/非安全工具独占）；启动性能优化（并行预取 160ms→65ms，节省 59%）；惰性 `require()` 与 Zod 惰性 schema 评估；`updateUsage` 的 `>0` 守卫；`CacheSafeParams` 五维度共享与 `skipCacheWrite` 一次性 Fork |
| 14 | [Plan 模式与结构化工作流](第四部分-工程实践篇/14-Plan模式与结构化工作流.md) | Plan 模式的"先想后做"哲学与建筑行业类比；`prepareContextForPlanMode` 模式切换；`ExitPlanModeV2Tool` 断路器防御；计划文件的三层恢复策略（直接读取→文件快照→消息历史）；`ScheduleCronTool` 本地调度（文件锁防重复/7天自动过期/Jitter 防惊群）；`RemoteTriggerTool` 远程 API 触发 |
| 15 | [构建你自己的 Agent Harness](第四部分-工程实践篇/15-构建你自己的Agent-Harness.md) | Agent Harness vs 简单 API 调用的决策矩阵；六步实现路线图（AsyncGenerator 对话循环→Fail-closed 工具系统→四阶段权限管线→Snip+Summary 上下文管理→记忆存储→Hook 执行器）；循环依赖解决方案（lazy require/集中类型导出）；功能开关分层策略；四层可观测性体系；多环境适配（CLI/IDE/SDK/Server）；安全威胁模型与审计 Checklist |

### Appendix — 参考资料速查

| | 内容 |
|:-:|------|
| [A](附录/A-源码导航地图.md) | **架构导航地图** — 16 个核心模块职责、模块依赖树、6 条数据流快速参考路径、四层架构分层说明、10 种设计模式速览 |
| [B](附录/B-工具完整清单.md) | **工具完整清单** — 50+ 工具按 12 类组织，标注 readOnly/destructive/concurrencySafe 属性，6 种工具组合使用模式，性能特征概览 |
| [C](附录/C-功能标志速查表.md) | **功能标志速查表** — 89 个 Feature Flag 按 13 类组织，标注编译时/运行时类型，含依赖关系图和 6 种常见配置场景推荐 |
| [D](附录/D-术语表.md) | **术语表** — 100 条中英对照术语定义，含交叉引用和章节定位 |

---

## 怎么读

**时间紧张？** Ch1（心智模型）→ Ch2（对话循环）→ Ch4（权限管线）→ Ch15（动手构建）。拿到核心认知和动手能力就够用。

**有经验的架构师？** 直接读 Part 2（核心系统）和 Part 3（高级模式），遇到概念缺口回溯 Part 1。重点关注每章的"设计哲学"和"反模式警告"段落。

**系统学习？** 从头到尾读一遍，完成每章实战练习，最后在 Ch15 动手构建自己的 Harness。预计 2–3 周深度阅读。

**只想查资料？** 直接翻附录——A 找模块定位，B 查工具属性，C 查功能标志，D 查术语定义。

---

## 适合谁

- **架构师** — 你想构建自己的 Agent 框架，需要一张完整的设计空间地图和工程权衡分析
- **高级工程师** — 你不满足于调 API，想理解工具调用、流式处理、权限管控的底层机制
- **研究者** — 你想从实现角度理解 Agent 系统的运作方式，获得可发表论文级别的系统分析
- **Claude Code 用户** — 你想理解设计意图，用得更准、调得更深，最大化利用其能力

---

## 背景

2026 年 3 月 31 日，安全研究员 [Chaofan Shou (@Fried_rice)](https://x.com/Fried_rice) 发现 npm registry 中的 `@anthropic-ai/claude-code` 包存在构建配置失误。披露推文获得超 1700 万次浏览，引发了技术社区对 Agent 架构的空前讨论。

这本书的诞生正是受到这场讨论的启发——当 Agent 架构成为开发者社区的热门话题，我们意识到需要一本系统性的书来讲解 Agent Harness 的设计原理。

---

## 贡献

欢迎 Issue 和 PR — 修正技术错误、补充实战案例、改进章节结构。

## 致谢

[Linux.Do](https://linux.do/) 社区

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lintsinghua/claude-code-book&type=Date)](https://star-history.com/#lintsinghua/claude-code-book&Date)

---

<p align="center">
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">
    <img src="https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-lightgrey" alt="CC BY-NC-SA 4.0" />
  </a>
  <br/><br/>
  可自由分享和改编，但须署名、非商业使用、并以相同协议共享。
</p>
