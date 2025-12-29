# Graph Flow & Control Logic

This document describes the **runtime behavior** of the LangGraph workflow
used in the NCO Classification Engine.

---

## 1. High-Level Flow
<figure>
    <img src="image.png" alt="graph_structure">
    <figcaption>This diagram shows the design and data flow in the graph</figcaption>
</figure>

### Graph State Guarantees
The graph enforces the following invariants:
- Never loops indefinitely
- Never returns MATCH_FOUND under user ambiguity
- Never trusts retrieval blindly
- Never allows repeated self-correction
- Always checkpoints before human interruption

---

### 2. Graph State Management
The Data-Flow in the entire graph happens through a common State. This State is persisted to PostgreSQL after every step using PostgresSaver.

### State Definition
<table>
  <tr>
    <th>Field</th>
    <th>Type</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>messages</td>
    <td>List[BaseMessage]</td>
    <td>Append-only log of user inputs and AI responses.</td>
  </tr>
  <tr>
    <td>expander_analysis</td>
    <td>dict</td>
    <td>Output from the Expander node.</td>
  </tr>
  <tr>
    <td>retrieved_results</td>
    <td>dict</td>
    <td>Raw results from ChromaDB (distances, metadata, documents).</td>
  </tr>
  <tr>
    <td>analyzer_response</td>
    <td>dict</td>
    <td>Structured decision output from the Analyzer node.</td>
  </tr>
  <tr>
    <td>improved_search</td>
    <td>bool</td>
    <td>Flag indicating if the Analyzer triggered a query refinement loop.</td>
  </tr>
  <tr>
    <td>improved_search_count</td>
    <td>int</td>
    <td>Circuit Breaker: Counts retrieval loops (Max: 1) to prevent infinite cycles.</td>
  </tr>
</table>

---

## 3. Node Responsibilities
### Expander Node
- Normalizes user input
- Detects ambiguity
- Generates structured search query
- Externalizes assumptions

Does **not**:
- Choose occupation codes
- Decide final status

### Retrieval Node
- Executes semantic search (ChromaDB)
- Uses:
  - Expander query (default)
  - Analyzer refined query (improved search)
- Merges results on retry to preserve context

Retrieval is treated as **untrusted evidence**.

### Analyzer Node
- Performs final arbitration
- Executes multi-phase reasoning
- Chooses exactly one status:
  - MATCH_FOUND
  - MORE_INFO
  - IMPROVED_SEARCH

### User Info Node
- if Analyzer demands clarification, then interrupt occurs on this node and
- graph waits for user input then after getting user input, graph resumes from this same node.

---

## 4. Conditional Routing Logic
### Improved Search Router
- Allows **only one** correction loop
- Enforced via `improved_search_count`

If exceeded:
- Analyzer must choose between MORE_INFO or MATCH_FOUND

### User Info Router
- Routes to END when MATCH_FOUND
- Routes back to Expander after clarification input

---

## 5. Human-in-the-Loop Handling
When Analyzer returns `MORE_INFO`:
1. Graph raises `interrupt()`
2. State is checkpointed on user_info_node
3. Execution halts
4. User response is injected via: `Command(resume=user_message)`
5. Graph restarts cleanly from Expander

No partial state reuse.
No mid-node resumption.

---

## 6. Failure Mode Resolution Matrix

| Failure Source            | Resolution       |
|---------------------------|------------------|
| User ambiguity            | MORE_INFO        |
| Retrieval noise           | IMPROVED_SEARCH |
| Expander hallucination    | IMPROVED_SEARCH |
| Fragmented convergence    | MATCH_FOUND     |
| Repeated uncertainty      | MORE_INFO        |

---

## 7. Non-Goals of the Graph
- Guessing occupations from location alone
- Forcing a single code under fragmentation
- Maximizing recall at the cost of correctness
- Treating LLM outputs as ground truth
