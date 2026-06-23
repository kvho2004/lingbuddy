# LingBuddy — AI French Tutor

> Adaptive French language learning platform combining a rule-based mastery engine with GPT-driven conversational tutoring.

> **Note:** Source code is being cleaned up from a private repository and will be published here. This README documents the system architecture, design decisions, and research outcomes.

---

## Table of Contents

- [LingBuddy — AI French Tutor](#lingbuddy--ai-french-tutor)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [System Architecture](#system-architecture)
  - [Core Components](#core-components)
    - [Mastery Engine](#mastery-engine)
    - [Adaptive Sub-Question Generation](#adaptive-sub-question-generation)
    - [LLM Integration](#llm-integration)
  - [Tech Stack](#tech-stack)
  - [Research Findings](#research-findings)
  - [Project Status](#project-status)

---

## Overview

LingBuddy addresses a fundamental weakness in existing language learning apps. Specifically, static drills tend to cycle through content regardless of what a learner already knows, wasting time on mastered material and underserving genuine gaps.

LingBuddy solves this with a **two-layer tutoring model**:

1. A rule-based mastery engine that tracks per-concept proficiency and builds a dynamically ranked priority queue unique to each user
2. An OpenAI GPT integration that delivers contextual grammar feedback and open-ended conversational practice on top of that structured foundation

A user study conducted as part of this project showed a **27% average improvement in verb conjugation accuracy**, with the adaptive routing being the primary driver.

> Check out Figma Prototype: [UI Design](https://www.figma.com/design/zYIfSm2qHCPLlUAJQEB84m/LingBuddy-Website-UI-Prototype?node-id=0-1&p=f)
---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        Frontend                          │
│              HTML · CSS · Responsive UI                  │
│              (Designed in Figma)                         │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTP / Django REST
┌───────────────────────────▼──────────────────────────────┐
│                    Django Backend                        │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │               Mastery Engine                       │  │
│  │                                                    │  │
│  │  User answers question                             │  │
│  │       │                                            │  │
│  │       ▼                                            │  │
│  │  Score against rule set (tense, pronoun, pattern)  │  │
│  │       │                                            │  │
│  │       ▼                                            │  │
│  │  Update per-concept proficiency score              │  │
│  │       │                                            │  │
│  │       ▼                                            │  │
│  │  Reorder user priority queue                       │  │
│  │       │                                            │  │
│  │       ▼                                            │  │
│  │  Select next question from weakest concept         │  │
│  └───────────────────────┬────────────────────────────┘  │
│                          │ on incorrect / open-ended     │
│  ┌───────────────────────▼────────────────────────────┐  │
│  │              LLM Integration                       │  │
│  │                                                    │  │
│  │  · Grammar feedback: GPT explains the error        │  │
│  │    in natural language with corrected form         │  │
│  │  · Conversation mode: scenario-based dialogue      │  │
│  │    (e.g. ordering food, asking directions)         │  │
│  │    with accuracy tracked against mastery engine    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└───────────────────────────┬──────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────┐
│                       Database                           │
│   SQLite · User sessions · Per-concept progress scores   │
└──────────────────────────────────────────────────────────┘
```

---

## Core Components

### Mastery Engine

Each user has a proficiency score per grammar concept (e.g. present tense -er verbs, irregular subjunctive, reflexive verbs). After each answer, scores are updated using a weighted rule set that factors in:

- Whether the error was a conjugation mistake, a tense selection mistake, or a pronoun agreement mistake
- How recently the concept was last practiced
- The concept's historical error rate for that user

A **min-heap priority queue** keeps concepts ranked by urgency, so the next question always targets the learner's most pressing gap.

### Adaptive Sub-Question Generation

Rather than pulling from a static question bank, LingBuddy generates sub-questions parametrically. Given a target concept (e.g. "passé composé with être verbs"), the engine constructs a question by sampling a subject pronoun, a verb from the target class, and a context sentence. This prevents learners from pattern-matching question format rather than internalizing the grammar rule.

### LLM Integration

GPT is invoked in two modes:

- **Feedback mode:** triggered after an incorrect answer. The prompt includes the original question, the learner's response, the correct answer, and the target concept. GPT returns a plain-language explanation of the error and the rule being tested, not just the correct answer.
- **Conversation mode:** the learner is placed in a scenario (e.g. a café, a train station). GPT maintains the dialogue while the mastery engine silently scores grammar patterns in the learner's responses and updates proficiency scores accordingly.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3, Django, REST APIs |
| AI / LLM | OpenAI GPT API, prompt engineering |
| Frontend | HTML, CSS |
| Design | Figma |
| Database | SQLite |
| Testing | Django test framework, manual user study |


---

## Research Findings

LingBuddy was evaluated in a user study (conducted in-person with classmates, Aug–Nov 2025) measuring verb conjugation accuracy before and after using the platform.

| Metric | Result |
|---|---|
| Study design | Pre/post assessment, in-person |
| Target skill | French verb conjugation accuracy |
| Average improvement | **27%** |
| Primary driver | Adaptive priority queue routing vs. static drill order |

The key finding was that learners improved most on irregular verb patterns — the concepts where static apps tend to underserve users because they surface irregular verbs at the same rate as regular ones regardless of demonstrated weakness.

---

## Project Status

| Component | Status |
|---|---|
| Rule-based mastery engine | Complete |
| Adaptive priority queue | Complete |
| Parametric sub-question generation | Complete |
| OpenAI GPT feedback integration | Complete |
| Scenario-based conversation mode | Complete |
| Responsive frontend | Complete |
| Figma UI design | Complete |
| User study | Complete |
| Source code cleanup | In progress |
| Public source release | Upcoming |

---