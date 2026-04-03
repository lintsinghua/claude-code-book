<div align="center">

**[English](en/README.md)** | **中文**

# 御舆：解码 Agent Harness

### Claude Code 架构深度剖析

<br/>

> *"一器而工聚焉者，车为多。"* ——《考工记》
>
> 两千年前，造一辆马车是最复杂的系统工程：**舆**承载乘者，辕定方向，辐传动力，軎辖为约束——每个构件各司其职，合而为一，车方能行。
>
> 今天，构建一个 AI Agent 亦是如此：对话循环为**辕**，工具系统为**辐**，权限管线为**軎辖**，而将这一切承载于其上、使智能体真正运转的运行时框架—— Agent Harness——正是那个**舆**。
>
> 古人御舆，驾驭的是天地之间最精密的机械；今人御舆，驾驭的是硅基时代最复杂的智能体系统。
>
> 本书因此得名 **舆书**。

<br/>

当所有人都在教你怎么 **用** AI Agent——**这本书带你拆开它。**

<br/>

[![在线阅读](https://img.shields.io/badge/在线阅读-lintsinghua.github.io-9f7aea?style=for-the-badge)](https://lintsinghua.github.io/)

[![GitHub Stars](https://img.shields.io/github/stars/lintsinghua/claude-code-book?style=flat-square&logo=github&label=Stars)](https://github.com/lintsinghua/claude-code-book/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/lintsinghua/claude-code-book?style=flat-square&logo=github&label=Forks)](https://github.com/lintsinghua/claude-code-book/network/members)
[![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-lightgrey?style=flat-square)](LICENSE)
[![中文](https://img.shields.io/badge/语言-中文-red?style=flat-square)](./)
[![English](https://img.shields.io/badge/lang-English-blue?style=flat-square)](en/README.md)
[![Last Commit](https://img.shields.io/github/last-commit/lintsinghua/claude-code-book?style=flat-square)](https://github.com/lintsinghua/claude-code-book/commits/main)

<br/>

<img width="480" src="cover.png" alt="御舆：解码 Agent Harness — Claude Code 架构深度剖析" />

<img width="2880" height="1558" alt="Decoding Agent Harness — A Deep Architectural Analysis of Claude Code" src="https://github.com/user-attachments/assets/39efa7d4-4521-444e-a222-fd0acb756e51" />

</div>

---

> **对话循环如何驱动？工具权限为何是四阶段管线？上下文压缩怎样在 token 预算内运转？子智能体如何通过 Fork 继承父级上下文？**
>
> 读懂 Claude Code 的设计决策，你就拥有了一套**可迁移到任何 Agent 框架**的心智模型。

---

## 这本书有什么不同

**不做使用教程，不列 Prompt 技巧。**

市面上充斥着"如何写好 Prompt"和"如何调用 Agent API"的指南。但如果你想知道一个生产级 Agent 系统的**骨架**是怎么搭的——几乎没有资料可查。这本书填补了这个空白。

|  | 特色 | 说明 |
|:-:|------|------|
| | **架构分析而非 API 文档** | 不讲"怎么调用"，讲"为什么这样设计"——追溯动机、分析权衡、指出反模式 |
| | **设计哲学而非使用教程** | 从异步生成器到断路器模式，每章提炼可迁移的设计原则 |
| | **可迁移的认知模型** | 无论你用 LangChain、AutoGen、CrewAI 还是从零构建，书中 139 张架构图直接复用 |

<details>
<summary><b>书中的数据一览</b></summary>

| 指标 | 数量 |
|------|------|
| 全书字数 | 42 万字（中文）/ 75K+ words（English） |
| 正文章节 | 15 章 + 4 篇附录 |
| Mermaid 架构图/流程图/状态机 | 139 张 |
| 覆盖核心子系统 | 工具系统、权限管线、上下文压缩、记忆系统、钩子系统、子智能体调度、MCP 集成、技能插件、流式架构、Plan 模式 |
| 分析的设计决策 | 50+ 个"为什么这样设计" |
| 术语条目（中英对照） | 100 条 |
| 功能标志 | 89 个 |
| 注册工具 | 50+ 个 |

</details>

> **声明：** 本书基于对 Claude Code 公开文档和产品行为的架构分析编写，未引用、未使用任何未公开或未授权的源码。Claude Code 为 Anthropic PBC 产品，本书不隶属于、未获授权于、也不代表 Anthropic。

---

## 快速导航

> **时间紧张？** 01 → 02 → 04 → 15，拿到核心认知和动手能力就够用
>
> **有经验？** 直接读 Part 2 + Part 3，遇到概念缺口回溯 Part 1
>
> **系统学习？** 从头到尾，每章做练习，最后 Ch15 构建自己的 Harness（约 2–3 周）
>
> **查资料？** 直接翻 [附录 A](#appendix--参考资料速查)（模块定位）/ [B](#appendix--参考资料速查)（工具）/ [C](#appendix--参考资料速查)（功能标志）/ [D](#appendix--参考资料速查)（术语）

---

## 目录

### Part 1. 基础篇 — 建立心智模型

> 理解 Agent 编程的范式转移，建立对 Agent Harness 的整体认知框架。

| # | 章节 | 核心内容 |
|:-:|------|---------|
| 01 | [智能体编程的新范式](第一部分-基础篇/01-智能体编程的新范式.md) | Copilot → Claude Code 演进；Agent Harness 五大设计原则；Bun + React/Ink + Zod v4 技术栈 |
| 02 | [对话循环 — Agent 的心跳](第一部分-基础篇/02-对话循环-Agent的心跳.md) | `while(true)` 异步生成器主循环；五种 yield 事件；十种终止原因；`QueryDeps` 依赖注入 |
| 03 | [工具系统 — Agent 的双手](第一部分-基础篇/03-工具系统-Agent的双手.md) | `Tool<I,O,P>` 五要素协议；`buildTool` 故障安全工厂；45+ 工具 × 12 类；并发分区贪心算法 |
| 04 | [权限管线 — Agent 的护栏](第一部分-基础篇/04-权限管线-Agent的护栏.md) | 四阶段管线；五种权限模式谱系；Bash 规则匹配；推测性分类器 2 秒 Promise.race |

### Part 2. 核心系统篇 — 深入子系统

> 拆解 Agent Harness 的四大核心子系统——配置、记忆、上下文、钩子。

| # | 章节 | 核心内容 |
|:-:|------|---------|
| 05 | [设置与配置 — Agent 的基因](第二部分-核心系统篇/05-设置与配置-Agent的基因.md) | 六层配置优先级链；合并规则；安全边界与供应链攻击防御；双层功能门控 |
| 06 | [记忆系统 — Agent 的长期记忆](第二部分-核心系统篇/06-记忆系统-Agent的长期记忆.md) | 四种封闭式记忆类型；"只保存无法推导的信息"；MEMORY.md 索引；Fork 记忆机制 |
| 07 | [上下文管理 — Agent 的工作记忆](第二部分-核心系统篇/07-上下文管理-Agent的工作记忆.md) | 有效窗口公式；四级渐进压缩（Snip→MicroCompact→Collapse→AutoCompact）；断路器模式 |
| 08 | [钩子系统 — Agent 的生命周期扩展点](第二部分-核心系统篇/08-钩子系统-Agent的生命周期扩展点.md) | 五种 Hook 类型；26 个生命周期事件；JSON 响应协议；六层优先级；三层安全机制 |

### Part 3. 高级模式篇 — Agent 的组合与扩展

> 探索 Agent 如何组合、编排和扩展——从子智能体到 MCP 协议桥接。

| # | 章节 | 核心内容 |
|:-:|------|---------|
| 09 | [子智能体与 Fork 模式](第三部分-高级模式篇/09-子智能体与Fork模式.md) | 三种 Agent 来源；四种内置 Agent；Fork 字节级上下文继承；递归 Fork 防护 |
| 10 | [协调器模式 — 多智能体编排](第三部分-高级模式篇/10-协调器模式-多智能体编排.md) | Coordinator-Worker 双重门控；"只编排不执行"约束；四种寻址模式；四阶段工作流 |
| 11 | [技能系统与插件架构](第三部分-高级模式篇/11-技能系统与插件架构.md) | 11 个核心技能；SKILL.md frontmatter；三级参数替换；分层加载；插件缓存 |
| 12 | [MCP 集成与外部协议](第三部分-高级模式篇/12-MCP集成与外部协议.md) | 8 种传输协议；五态连接管理；三段式工具命名；Bridge 双向通信系统 |

### Part 4. 工程实践篇 — 从原理到构建

> 性能优化的工程细节，以及从零构建一个完整 Harness 的实战路线图。

| # | 章节 | 核心内容 |
|:-:|------|---------|
| 13 | [流式架构与性能优化](第四部分-工程实践篇/13-流式架构与性能优化.md) | QueryEngine 生命周期管理；并发控制；启动优化 160ms→65ms（-59%）；惰性加载策略 |
| 14 | [Plan 模式与结构化工作流](第四部分-工程实践篇/14-Plan模式与结构化工作流.md) | "先想后做"哲学；计划文件三层恢复策略；本地调度与远程触发 |
| 15 | [构建你自己的 Agent Harness](第四部分-工程实践篇/15-构建你自己的Agent-Harness.md) | 六步实现路线图；循环依赖解决方案；四层可观测性体系；安全威胁模型 |

### Appendix 附录 — 参考资料速查

| # | 模块 | 内容 |
|:-:|------|------|
| A | [架构导航地图](附录/A-源码导航地图.md) |  16 个核心模块、依赖树、6 条数据流路径、四层架构、10 种设计模式 |
| B | [工具完整清单](附录/B-工具完整清单.md) | 50+ 工具 × 12 类，readOnly/destructive/concurrencySafe 属性 |
| C | [功能标志速查表](附录/C-功能标志速查表.md) | 89 个 Flag × 13 类，编译时/运行时类型，依赖关系图 |
| D | [术语表](附录/D-术语表.md) |  100 条中英对照术语，含交叉引用和章节定位 |

---

## 适合谁

| 适合人群 | 收获 |
|:-:|------|
|  **架构师** | 完整的 Agent 设计空间地图和工程权衡分析 |
|  **高级工程师** | 工具调用、流式处理、权限管控的底层机制 |
|  **研究者** | 可发表论文级别的 Agent 系统实现分析 |
|  **Claude Code 用户** | 理解设计意图，最大化利用其能力 |

---

## 背景

2026 年 3 月 31 日，安全研究员 [Chaofan Shou (@Fried_rice)](https://x.com/Fried_rice) 发现 npm registry 中的 `@anthropic-ai/claude-code` 包存在构建配置失误，source map 文件引用了未设访问控制的 Cloudflare R2 存储桶。披露推文获得超 1700 万次浏览，引发了技术社区对 Agent 架构的空前讨论。

这本书的诞生正是受到这场讨论的启发——当 Agent 架构成为热门话题，我们意识到需要一本系统性的书来讲解 Agent Harness 的设计原理。

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
