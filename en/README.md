<div align="center">

**English** | **[中文](../README.md)**

# Yù Yú: Decoding Agent Harness

### A Deep Architectural Analysis of Claude Code

<br/>

> *"Of all instruments, the chariot demands the most hands to build."* — *Kǎo Gōng Jì* (Rites of Zhou, c. 300 BC)
>
> In ancient China, the chariot was the most complex system ever engineered. The **yú** (舆, carriage) bears the rider; the shaft sets direction; the spokes transmit force; the linchpin constrains the wheel. Each part has its duty — only together can the vehicle move.
>
> Today, building an AI Agent is no different. The conversation loop is the **shaft**, the tool system the **spokes**, the permission pipeline the **linchpin**, and the runtime framework that bears it all — the Agent Harness — is the **yú**.
>
> This book is thus known as the **"Yú Shū"** (舆书, The Chariot Book).

<br/>

While everyone else teaches you how to **use** AI Agents — **This book dissects one.**

<br/>

[![Read Online](https://img.shields.io/badge/Read_Online-lintsinghua.github.io-9f7aea?style=for-the-badge)](https://lintsinghua.github.io/)

[![GitHub Stars](https://img.shields.io/github/stars/lintsinghua/claude-code-book?style=flat-square&logo=github&label=Stars)](https://github.com/lintsinghua/claude-code-book/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/lintsinghua/claude-code-book?style=flat-square&logo=github&label=Forks)](https://github.com/lintsinghua/claude-code-book/network/members)
[![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-lightgrey?style=flat-square)](LICENSE)
[![中文](https://img.shields.io/badge/语言-中文-red?style=flat-square)](../README.md)
[![English](https://img.shields.io/badge/lang-English-blue?style=flat-square)](./)
[![Last Commit](https://img.shields.io/github/last-commit/lintsinghua/claude-code-book?style=flat-square)](https://github.com/lintsinghua/claude-code-book/commits/main)

<br/>

<img width="2880" height="1558" alt="Decoding Agent Harness — A Deep Architectural Analysis of Claude Code" src="https://github.com/user-attachments/assets/39efa7d4-4521-444e-a222-fd0acb756e51" />

</div>

---

> **How does the dialog loop drive execution? Why is the permission system a four-stage pipeline? How does context compression operate within token budgets? How do sub-agents inherit parent context through Fork?**
>
> Understand Claude Code's design decisions, and you gain a **mental model transferable to any Agent framework**.

---

## What Makes This Book Different

**Not a usage tutorial. Not a list of prompt tricks.**

The market is saturated with guides on "how to write better prompts" and "how to call Agent APIs." But if you want to understand the **skeleton** of a production-grade Agent system — there's almost nothing to consult. This book fills that gap.

|  | Feature | Description |
|:-:|---------|-------------|
| | **Architecture Analysis, Not API Docs** | Not "how to call," but "why designed this way" — tracing motivations, analyzing trade-offs, identifying anti-patterns |
| | **Design Philosophy, Not Tutorials** | From async generators to circuit breakers, every chapter distills transferable design principles |
| | **Transferable Cognitive Models** | Whether you use LangChain, AutoGen, CrewAI, or build from scratch — 139 architecture diagrams apply directly |

<details>
<summary><b>By the Numbers</b></summary>

| Metric | Count |
|--------|-------|
| Total word count | 420K characters (Chinese) / 75K+ words (English) |
| Main chapters | 15 chapters + 4 appendices |
| Mermaid architecture/flow/state diagrams | 139 |
| Core subsystems covered | Tool system, permission pipeline, context compression, memory system, hook system, sub-agent dispatch, MCP integration, skill plugins, streaming architecture, Plan mode |
| Design decisions analyzed | 50+ "why designed this way" |
| Glossary terms (bilingual) | 100 |
| Feature flags | 89 |
| Registered tools | 50+ |

</details>

> **Disclaimer:** This book is based on architectural analysis of Claude Code's public documentation and product behavior. No unpublished or unauthorized source code was used. Claude Code is a product of Anthropic PBC. This book is not affiliated with, authorized by, or representative of Anthropic.

---

## Quick Navigation

> **Short on time?** 01 → 02 → 04 → 15 — get the core insights and hands-on skills
>
> **Experienced?** Jump to Part 2 + Part 3, backtrack to Part 1 for concept gaps
>
> **Systematic study?** Cover to cover with exercises, build your Harness in Ch15 (~2–3 weeks)
>
> **Just need reference?** Go straight to [Appendices](#appendix--reference-quick-lookup) — A (modules) / B (tools) / C (flags) / D (glossary)

---

## Table of Contents

### Part 1. Foundations — Building Mental Models

> Understand the paradigm shift in Agent programming and establish a holistic cognitive framework.

| # | Chapter | Core Content |
|:-:|---------|-------------|
| 01 | [The New Paradigm of Agent Programming](Part-1-Foundations/01-The-New-Paradigm-of-Agent-Programming.md) | Copilot → Claude Code evolution; five design principles; Bun + React/Ink + Zod v4 stack |
| 02 | [The Dialog Loop — Agent's Heartbeat](Part-1-Foundations/02-The-Dialog-Loop-Heartbeat-of-an-Agent.md) | `while(true)` async generator loop; five yield events; ten termination reasons; `QueryDeps` DI |
| 03 | [The Tool System — Agent's Hands](Part-1-Foundations/03-The-Tool-System-Agent-Hands.md) | `Tool<I,O,P>` five-element protocol; fail-safe `buildTool` factory; 45+ tools × 12 categories; concurrent partitioning |
| 04 | [The Permission Pipeline — Agent's Guardrails](Part-1-Foundations/04-The-Permission-Pipeline-Agent-Guardrails.md) | Four-stage pipeline; five permission modes; Bash rule matching; speculative classifier 2s Promise.race |

### Part 2. Core Systems — Deep Into Subsystems

> Dissect the four core subsystems — configuration, memory, context, and hooks.

| # | Chapter | Core Content |
|:-:|---------|-------------|
| 05 | [Settings & Configuration — Agent's DNA](Part-2-Core-Systems/05-Settings-and-Configuration-Agent-DNA.md) | Six-layer config priority chain; merge rules; security boundary & supply chain defense; dual-layer feature gating |
| 06 | [The Memory System — Agent's Long-Term Memory](Part-2-Core-Systems/06-The-Memory-System-Agent-Long-Term-Memory.md) | Four closed memory types; "only save non-derivable info"; MEMORY.md index; Fork memory mechanism |
| 07 | [Context Management — Agent's Working Memory](Part-2-Core-Systems/07-Context-Management-Agent-Working-Memory.md) | Effective window formula; four-level compression (Snip→MicroCompact→Collapse→AutoCompact); circuit breaker |
| 08 | [The Hook System — Agent's Lifecycle Extension Points](Part-2-Core-Systems/08-The-Hook-System-Agent-Lifecycle-Extension-Points.md) | Five hook types; 26 lifecycle events; JSON response protocol; six-layer priority; three-layer security |

### Part 3. Advanced Patterns — Composition & Extension

> Explore how Agents compose, orchestrate, and extend — from sub-agents to MCP protocol bridging.

| # | Chapter | Core Content |
|:-:|---------|-------------|
| 09 | [Sub-Agents and the Fork Pattern](Part-3-Advanced-Patterns/09-Sub-Agents-and-the-Fork-Pattern.md) | Three Agent sources; four built-in Agents; byte-level Fork context inheritance; recursive Fork protection |
| 10 | [The Coordinator Pattern — Multi-Agent Orchestration](Part-3-Advanced-Patterns/10-The-Coordinator-Pattern-Multi-Agent-Orchestration.md) | Coordinator-Worker dual gating; "orchestrate-only" constraint; four addressing modes; four-stage workflow |
| 11 | [The Skill System & Plugin Architecture](Part-3-Advanced-Patterns/11-The-Skill-System-and-Plugin-Architecture.md) | 11 core skills; SKILL.md frontmatter; three-level parameter substitution; layered loading; plugin cache |
| 12 | [MCP Integration & External Protocols](Part-3-Advanced-Patterns/12-MCP-Integration-and-External-Protocols.md) | 8 transport protocols; five-state connection management; three-part tool naming; Bridge bidirectional comms |

### Part 4. Engineering Practice — From Principles to Construction

> Performance optimization details and a practical roadmap for building a complete Harness from scratch.

| # | Chapter | Core Content |
|:-:|---------|-------------|
| 13 | [Streaming Architecture & Performance Optimization](Part-4-Engineering-Practice/13-Streaming-Architecture-and-Performance-Optimization.md) | QueryEngine lifecycle; concurrency control; startup optimization 160ms→65ms (-59%); lazy loading |
| 14 | [Plan Mode & Structured Workflows](Part-4-Engineering-Practice/14-Plan-Mode-and-Structured-Workflows.md) | "Think before you act" philosophy; plan file three-layer recovery; local scheduling & remote triggers |
| 15 | [Building Your Own Agent Harness](Part-4-Engineering-Practice/15-Building-Your-Own-Agent-Harness.md) | Six-step implementation roadmap; circular dependency solutions; four-layer observability; security threat model |

### Appendix — Reference Quick-Lookup

| | Content |
|:-:|---------|
| [A](Appendices/A-Architecture-Navigation-Map.md) | **Architecture Navigation Map** — 16 core modules, dependency tree, 6 data flow paths, 10 design patterns |
| [B](Appendices/B-Complete-Tool-Inventory.md) | **Complete Tool Inventory** — 50+ tools × 12 categories, readOnly/destructive/concurrencySafe attributes |
| [C](Appendices/C-Feature-Flag-Reference.md) | **Feature Flag Reference** — 89 flags × 13 categories, compile-time/runtime types, dependency graphs |
| [D](Appendices/D-Glossary.md) | **Glossary** — 100 bilingual term definitions with cross-references and chapter locations |

---

## Who Is This For

|  | Reader | What You'll Gain |
|:-:|--------|-----------------|
| | **Architects** | Complete Agent design space map and engineering trade-off analysis |
| | **Senior Engineers** | Underlying mechanisms of tool invocation, streaming, and permission control |
| | **Researchers** | Publishable-quality Agent system implementation analysis |
| | **Claude Code Users** | Understand design intent and maximize capabilities |

---

## Background

On March 31, 2026, security researcher [Chaofan Shou (@Fried_rice)](https://x.com/Fried_rice) discovered that the `@anthropic-ai/claude-code` package on npm contained a build configuration error where source map files referenced an unprotected Cloudflare R2 storage bucket. The disclosure tweet received over 17 million views, sparking unprecedented community discussion about Agent architecture.

This book was born from that discussion — when Agent architecture became a hot topic, we realized the need for a systematic book explaining the design principles of Agent Harness.

---

## Contributing

Issues and PRs welcome — fix technical errors, supplement practical examples, improve chapter structure.

## Acknowledgments

[Linux.Do](https://linux.do/) community

---

## Star History

<a href="https://star-history.com/#lintsinghua/claude-code-book&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="../docs/images/star-history-dark.svg" />
   <source media="(prefers-color-scheme: light)" srcset="../docs/images/star-history-light.svg" />
   <img alt="Star History Chart" src="../docs/images/star-history-light.svg" />
 </picture>
</a>

---

<p align="center">
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">
    <img src="https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-lightgrey" alt="CC BY-NC-SA 4.0" />
  </a>
  <br/><br/>
  Free to share and adapt, with attribution, non-commercial use, and same-license sharing.
</p>
