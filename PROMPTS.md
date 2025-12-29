# PROMPTS.md  
## Prompt Design, Motivation, and Reasoning  
*NCO Classification Engine*\
This document explains **why the Expander and Analyzer prompts are designed the way they are**, what problems they solve, and which failures they intentionally prevent.\
This is a **design document for constrained LLM reasoning inside a graph**.

---
## Design Philosophy
The prompts in this system are written under one assumption:
> **LLMs are pattern recognizers, not decision authorities.**Therefore:
- Prompts **detect and explain signals**
- The graph **enforces decisions and safety**
- No prompt is trusted to “do the right thing” implicitly.Every rule in the prompts exists to prevent a **known failure mode** observed in naive RAG or single-agent systems.
---
## The Expander Prompt
### Purpose
The Expander translates informal job descriptions into a **structured, vector-search-optimized query** aligned with NCO-2015 terminology.
It does **not** classify occupations.

### Motivation: Why an Expander Exists

#### Problem in naive systems
- User inputs are informal, short, and inconsistent
- Direct embedding of raw input underperforms on structured datasets like NCO-2015
- Vector search fails without hierarchy signals (Division, Title)

#### Design decision
Introduce a dedicated agent that:
- normalizes language,
- anchors hierarchy early,
- and exposes its assumptions explicitly.

### Division Anchoring
#### Motivation
NCO-2015 is hierarchical. Division boundaries matter more than surface similarity. Without division anchoring:
- Vector search retrieves cross-division noise
- High similarity ≠ correct occupation
- Also there are only 9 divisions.So, they are easy to classify.
- Notice that we do not do metadata filter with this division but we add this in query.So that if Expander selected wrong division then `query description` and `title` will anchor it towards the right division and Analyzer will notice this mistake.

#### Design Choice
The Expander **must predict a Division first**, based on:
- skill level,
- cognitive vs manual responsibility,
- industry context.

This acts as a **hard semantic constraint** during retrieval.

### Title Guessing (Generic Only)
#### Motivation
Over-specific titles:
- reduce recall,
- bias retrieval,
- and amplify hallucinations.

#### Design Choice
The Expander uses **generic, standard NCO terminology**

### Controlled HyDE (Query Spreading)
#### Motivation
NCO descriptions are verbose and formal.They are spreaded.User inputs are not.
Naive HyDE:
- hallucinates tools, domains, or industries
- silently corrupts retrieval

#### Design Choice
HyDE is allowed **only inside the `query description`**, and:
- must stay within implied task boundaries
- must not introduce new domains or qualifications

HyDE is **intentionally constrained**, not expressive.Also adding title and division help us help us control hyde as they help llm know the real context of the user's job description in relation to NCO-2015.This helps to keep the query grounded.

### Ambiguity Classification (Critical)
The Expander operates in **three explicit modes**:

#### 1. No Clarification
- Input is sufficient
- Query generated and No assumptions required

#### 2. Soft Clarification
- Input mostly sufficient
- Query generated,Assumptions documented and Clarification question included

#### 3. Hard Clarification
- Input insufficient or location-only
- No query generated and clarification required

#### Motivation
Naive systems either:
- guess incorrectly, or
- ask too many questions.

This tri-mode design balances **progress vs safety**.
### `note_for_analyzer`: Forced Assumption Disclosure
#### Motivation
The most dangerous LLM failure is **implicit assumption**.

#### Design Choice
Any assumption affecting:
- Division
- Title
- Skill level

**must** be written explicitly into `note_for_analyzer`.This allows downstream auditing and correction.

### Expander Non-Goals
- Selecting occupation codes
- Resolving fragmentation
- Overriding ambiguity
- Optimizing recall
- Making final decisions

----
## The Analyzer Prompt
### Purpose
The Analyzer is the **final arbitrator** for NCO-2015 classification.It evaluates:
- user input,
- expander reasoning,
- retrieval evidence,
and reports **structured signals** to the graph.

---
## Why a Multi-Phase Analyzer Exists
#### Problem in naive RAG
- Hallucinations propagate unchecked
- Retrieval confidence is mistaken for correctness
- LLMs anchor too early

#### Design Choice
Force the Analyzer to reason in **explicit, ordered phases**, each preventing a specific bias.

---

## Phase Design & Motivation
### Phase 0 — Input Sufficiency Check
#### Motivation
Early bias is the hardest to undo.
If retrieval or expander reasoning is seen too early, the model anchors incorrectly.

#### Design Choice
Evaluate **user input alone**, ignoring all other signals.Purpose:
- Detect location-only input
- Detect industry-only input
- Allow explicitly fragmented occupations

### Phase 1 — Retrieval Audit
#### Motivation
Vector similarity ≠ semantic correctness.Retrieval introduces two common failures:
##### Zombie Swarm
- Multiple strong matches from different occupational families or divisions
##### Noise
- Generic results, Distant roles and Dominance of `not elsewhere classified(n.e.c)` entries

#### Design Choice
The Analyzer **detects these faults**, but does not decide resolution and try to find the reason of these faults.Resolution is enforced by the graph.

### Phase 2 — Independent Anchoring
#### Motivation
Without independent anchoring:
- retrieval overrides user intent
- hallucinations appear justified

#### Design Choice
The Analyzer forms a hypothesis using **only user input**.
Retrieved results are trusted **only if aligned**.
Retrieval confidence is treated as advisory, not authoritative.

### Phase 3 — Expander Audit
#### Motivation
The Expander is allowed limited hallucination.Someone must audit it.

#### Design Choice
The Analyzer checks for:
- hallucinated constraints,
- incorrect division anchoring,
- unjustified specificity.

Detected faults are reported, not silently corrected.

---

## Multi-Occupation Detection (Signal Only)
#### Motivation
NCO-2015 fragments many stable real-world jobs into multiple codes.Forcing a single code:
- reduces correctness,
- increases false clarification.

#### Design Choice
The Analyzer detects **convergent fragmentation**:
- same division,
- same occupational family,
- differences only in specialization or task scope.

The Analyzer **reports convergence**.
The graph decides whether multi-occupation output is allowed.

---
## User Intent Interpretation
### Motivation
In real-world usage — especially in the Indian context — users describe
their occupation based on **habitual activity**, not formal job classification.
Example:
> “I drive a tractor.”

This statement means the user drives tractor most of the time.It does not describe a single narrowly scoped occupation.In practice, a tractor driver in India typically:
- operates the tractor across multiple seasons,
- performs agricultural work during farming seasons,
- performs construction, transport, or earth-moving work during off-seasons.

Asking a clarification question in such cases would reduce usability and does
not reflect real occupational identity and lead to bad user experience.

### Design Principle
The prompts are designed to interpret **behavioral identity**, not contractual
or seasonal specialization.The system assumes:
- The stated role represents **dominant, recurring behavior**
- Seasonal variation does not invalidate occupational identity
- Multi-context usage is normal, not ambiguous

### Design Choice
When a user states a stable, equipment-driven or role-driven occupation
(e.g., tractor driver, driver, mechanic, guard):
- The Analyzer does **not** ask follow-up questions about seasonal usage
- It evaluates whether the role maps to:
  - one dominant occupation, or
  - multiple closely related occupations

If multiple mappings are valid and converge:
- The system returns **multiple occupation codes** and is not treated as ambiguity.

### Why Clarification Is Avoided Here
Clarification is avoided because:
- The user intent is already clear
- The variation is contextual, not semantic
- NCO-2015 itself separates roles more finely than real-world practice

Asking questions such as:
> “Do you drive the tractor for farming or construction?”

would:
- add friction,
- misrepresent real labor behavior,
- and reduce classification usefulness.

### Constraints
This behavior applies **only when**:
- The occupation is stable and equipment- or role-centric
- Retrieved occupations belong to the same division
- Differences reflect task context, not skill level

If these conditions fail, normal ambiguity handling applies.

-----

## Status Signals
The Analyzer outputs **one** of:
- `MATCH_FOUND`
- `MORE_INFO`
- `IMPROVED_SEARCH`

---

## Hard Constraints (Why They Exist)
- `IMPROVED_SEARCH` allowed once → prevents infinite self-correction loops
- No mixed-division outputs → preserves NCO hierarchy integrity
- No `n.e.c.` selection → avoids semantic dumping ground
- No guessing under ambiguity → correctness over coverage

---

## Analyzer Non-Goals
- Maximizing recall
- Guessing user intent
- Acting as control logic
- Enforcing graph flow

---

## Summary
These prompts are intentionally:
- conservative,
- explicit,
- constrained.

They exist to **surface uncertainty, bias, and failure modes** — not to hide them behind fluent language.All final authority lives in the graph.
