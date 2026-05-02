---
title: "Don't Build Multi-Agents"
excerpt: "Why multi-agent architectures are fragile in 2025, and the two core principles of context engineering that should guide how you build reliable AI agents."
date: "2025-06-12"
author: "walden-yan"
tags: ["AI", "Agents", "Context Engineering", "LLM", "Architecture"]
status: "published"
source: "https://cognition.ai/blog/dont-build-multi-agents"
---

# Don't Build Multi-Agents

*by Walden Yan — Cognition AI*

---

## Principles of Context Engineering

We'll work our way up to the following principles:

1. **Share context** — share full agent traces, not just individual messages
2. **Actions carry implicit decisions** — conflicting decisions carry bad results

---

## Why Think About Principles?

HTML was introduced in 1993. In 2013, Facebook released React — not just a scaffold for writing code, but a philosophy: building applications with reactivity and modularity. In the age of LLMs and AI Agents, we're still playing with the equivalent of raw HTML and CSS, figuring out how to fit things together to make a good experience.

> Libraries like [openai/swarm](https://github.com/openai/swarm) and [microsoft/autogen](https://github.com/microsoft/autogen) actively push concepts I believe to be the wrong way of building agents — namely, multi-agent architectures.

---

## A Theory of Building Long-Running Agents

At the core of reliability is **Context Engineering**.

Models in 2025 are extremely intelligent. But even the smartest human can't do their job effectively without context. *Prompt engineering* was coined for writing tasks in the ideal format for an LLM chatbot. *Context engineering* is the next level — doing this automatically in a dynamic system. It is effectively the **#1 job** of engineers building AI agents.

---

## The Fragile Multi-Agent Pattern

A tempting architecture:

1. Break work down into multiple parts
2. Spin up subagents to work on those parts in parallel
3. Combine the results at the end

**Why it fails:** Suppose your task is "build a Flappy Bird clone." Subtask 1 is "build a moving game background with green pipes and hit boxes," and Subtask 2 is "build a bird that you can move up and down."

- Subagent 1 mistakes the subtask and builds a Super Mario Bros background.
- Subagent 2 builds a bird that doesn't look like a game asset and moves wrong.
- The final agent is left combining two miscommunications.

Most real-world tasks have layers of nuance that all have the potential to be miscommunicated.

---

## Principle 1: Share Context

> **Share context, and share full agent traces — not just individual messages.**

Copying only the original task description to subagents is not enough. In a real production system, the conversation is multi-turn, the agent has made tool calls, and any number of details could affect interpretation.

---

## Principle 2: Actions Carry Implicit Decisions

Even when each subagent has the original context, parallel subagents **cannot see what the other is doing**. Their work ends up inconsistent because they operate on conflicting unstated assumptions.

> **Actions carry implicit decisions, and conflicting decisions carry bad results.**

Principles 1 and 2 are so critical, and so rarely worth violating, that you should **by default rule out any agent architecture that doesn't abide by them**.

---

## Compliant Architectures

### Single-Threaded Linear Agent *(recommended default)*

The simplest way to follow both principles. Context is continuous. This will get you very far for the vast majority of production tasks.

**Limitation:** For very large tasks, context windows start to overflow.

### Context Compression Agent *(for truly long-duration tasks)*

Introduce a dedicated LLM whose key purpose is to compress a history of actions and conversation into key details, events, and decisions. This is hard to get right — it requires investment in figuring out what information is truly key. Depending on the domain, consider fine-tuning a smaller model (something Cognition has done internally).

---

## Real-World Examples

### Claude Code Subagents
As of June 2025, Claude Code spawns subtasks but **never does work in parallel with the subtask agent**. The subtask agent is usually only tasked with answering a question, not writing code — because it lacks the main agent's context needed to do anything more. Running parallel subagents would produce conflicting responses. The designers of Claude Code took a purposefully simple approach.

### Edit Apply Models
In 2024, a common practice was using an "edit apply model" — a small model that rewrites an entire file given a markdown explanation of desired changes, rather than having a large model output a properly formatted diff. These systems were still faulty: the small model would misinterpret instructions due to slight ambiguities. Today, edit decision-making and applying are more often done by a single model in one action.

---

## The Problem with Multi-Agent Collaboration

For true parallelism, you might let decision-making agents "talk" to each other. This is what humans do when we disagree — Engineer A and Engineer B talk out a merge conflict and reach consensus. However, **agents today are not able to engage in this style of long-context proactive discourse with the reliability of a single agent**. Humans are efficient at communicating the most important knowledge to one another, but this efficiency requires nontrivial intelligence.

While the long-term possibilities of agent collaboration are exciting, in 2025 running multiple agents in collaboration only results in **fragile systems**. Decision-making becomes too dispersed and context can't be shared thoroughly enough between agents.

> I personally think true multi-agent collaboration will come for free as single-threaded agents get better at communicating with humans.

---

## Applying the Principles

Ensure your agent's every action is informed by the context of **all relevant decisions** made by other parts of the system. Ideally, every action would see everything else. When context windows and practical tradeoffs make this impossible, decide what level of complexity you're willing to take on for the level of reliability you're targeting.

---

## Toward a More General Theory

These observations on context engineering are just the start of what may someday be the standard principles of building agents. At Cognition, agent building is a key frontier — internal tools and frameworks are built around these principles as a way to enforce ideas learned and relearned in production. The theories are not perfect, and flexibility and humility are required as the field advances.
