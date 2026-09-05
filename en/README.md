<div align="center">

# Yù Yú: Decoding Agent Harness

A Deep Architectural Analysis of Claude Code

[中文](../README.md) · **English**

<table align="center">
<tr><td><img src="../cover.png" width="420" alt="御舆：解码 Agent Harness — Claude Code 架构深度剖析，LinTsinghua" /></td></tr>
</table>

</div>

Explore how an agent runtime connects the conversation loop, tools, permissions, memory, and orchestration. Fifteen chapters and four appendices connect implementation details to design trade-offs and a hands-on harness project.

> *“Of all artifacts that bring many crafts together, the chariot calls upon the most.”* — *Kǎo Gōng Jì* (Book of Crafts)
>
> Two thousand years ago, building a chariot was already an exercise in systems engineering. The **yú** (舆, carriage body) carries the rider; shafts, spokes, and axle fittings each serve their purpose. Only together can the vehicle move.
>
> Building an AI Agent calls for similar coordination: the conversation loop advances the task, tools perform actions, and permissions set boundaries. The runtime framework that supports and organizes these capabilities—**Agent Harness**—plays the role of the **yú**.
>
> Chariot builders brought many crafts into one working whole. Agent builders, too, must understand how the parts work together. **Yù Yú** (御舆, “driving the chariot”) evokes both control and an understanding of the machinery that makes it possible.
>
> This is the idea behind the title **Yù Yú**, also known as **Yú Shū** (舆书, “The Chariot Book”).

## Start reading

- **First visit:** [Foreword](00-Foreword.md), then chapters 01 → 02 → 04 → 15.
- **Build an agent:** read Parts 1 and 4; use Parts 2 and 3 when adding memory and extensions.
- **Look up a concept:** use the four appendices below.
- **Website:** [Online reading](https://lintsinghua.github.io/). Repository chapters remain directly readable on GitHub.

## Reading notes

Readers should distinguish observed implementation, architectural interpretation, and teaching examples. Feature flags and tool availability depend on build and runtime configuration; counts and timing examples are not promises about current releases.

Claude Code belongs to Anthropic. This independent book is not an official Anthropic publication. The book’s license does not extend to third-party code.

## Contents

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
| 09 | [Sub-Agents and the Fork Pattern](Part-3-Advanced-Patterns/09-Sub-Agents-and-the-Fork-Pattern.md) | Three Agent sources; agent roles and availability gates; byte-level Fork context inheritance; recursive Fork protection |
| 10 | [The Coordinator Pattern — Multi-Agent Orchestration](Part-3-Advanced-Patterns/10-The-Coordinator-Pattern-Multi-Agent-Orchestration.md) | Coordinator-Worker dual gating; "orchestrate-only" constraint; four addressing modes; four-stage workflow |
| 11 | [The Skill System & Plugin Architecture](Part-3-Advanced-Patterns/11-The-Skill-System-and-Plugin-Architecture.md) | 11 core skills; SKILL.md frontmatter; three-level parameter substitution; layered loading; plugin cache |
| 12 | [MCP Integration & External Protocols](Part-3-Advanced-Patterns/12-MCP-Integration-and-External-Protocols.md) | 8 connection configuration variants; five-state connection management; three-part tool naming; Bridge bidirectional comms |

### Part 4. Engineering Practice — From Principles to Construction

> Performance optimization details and a practical roadmap for building a complete Harness from scratch.

| # | Chapter | Core Content |
|:-:|---------|-------------|
| 13 | [Streaming Architecture & Performance Optimization](Part-4-Engineering-Practice/13-Streaming-Architecture-and-Performance-Optimization.md) | QueryEngine lifecycle; concurrency control; parallel prefetching and startup estimates; lazy loading |
| 14 | [Plan Mode & Structured Workflows](Part-4-Engineering-Practice/14-Plan-Mode-and-Structured-Workflows.md) | "Think before you act" philosophy; plan file three-layer recovery; local scheduling & remote triggers |
| 15 | [Building Your Own Agent Harness](Part-4-Engineering-Practice/15-Building-Your-Own-Agent-Harness.md) | Six-step implementation roadmap; circular dependency solutions; four-layer observability; security threat model |

### Appendix — Reference Quick-Lookup

| | Content |
|:-:|---------|
| [A](Appendices/A-Architecture-Navigation-Map.md) | **Architecture Navigation Map** — 16 core modules, dependency tree, 6 data flow paths, 10 design patterns |
| [B](Appendices/B-Complete-Tool-Inventory.md) | **Complete Tool Inventory** — 50+ tools × 12 categories, readOnly/destructive/concurrencySafe attributes |
| [C](Appendices/C-Feature-Flag-Reference.md) | **Feature Flag Reference** — 89 flags × 13 categories, compile-time/runtime types, dependency graphs |
| [D](Appendices/D-Glossary.md) | **Glossary** — 100 bilingual term definitions with cross-references and chapter locations |


## Contributing

Issues and pull requests are welcome. Include the chapter, section, expected correction, and a source link; for rendering problems, include the viewer and reproduction steps. Please keep Chinese and English changes aligned.

Before submitting, run `python3 scripts/check_book.py` and `python3 -m unittest discover -s tests`. To validate Mermaid syntax, install Node.js 22 or later and run `npm ci` followed by `npm run check:diagrams`.

## License and acknowledgements

Book content: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Credit the author, use non-commercially, and share adaptations under the same license. Third-party material retains its own terms. Thanks to the [Linux.Do](https://linux.do/) community.

## Star History

<a href="https://star-history.com/#lintsinghua/claude-code-book&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="../docs/images/star-history-dark.svg" />
   <source media="(prefers-color-scheme: light)" srcset="../docs/images/star-history-light.svg" />
   <img alt="Star History Chart" src="../docs/images/star-history-light.svg" />
 </picture>
</a>
