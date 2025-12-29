# NCO 2015 Classification Chatbot

A semantic search and classification system designed to help users identify their `India's` **National Classification of Occupations (NCO) 2015** code.
The application uses a **FastAPI** backend orchestrated by **LangGraph** to process natural language job descriptions. It employs a multi-agent workflow (Expander → Retriever → Analyzer) to map vague user inputs to specific technical occupation codes, maintained with a **PostgreSQL** database for session management and **ChromaDB** for vector search.

---

## 🚀 Features

* **Stateful Conversations**: Remembers context across turns using a Persistent Graph Checkpointer (PostgreSQL).
* **Multi-Stage Reasoning**:
    1.  **Expander**: Translates casual inputs into structured search queries.
    2.  **Retriever**: Fetches relevant NCO documents from ChromaDB.
    3.  **Analyzer**: Acts as a final arbitrator to pick the correct code or ask for clarification.
- **Safe human-in-the-loop flow** (pause & resume)
- **Explicit ambiguity handling** (never guesses silently)
- **Multi-occupation support** for fragmented NCO roles
- **Race-condition safe backend** using DB row locking
- **Persistent graph checkpoints** for fault tolerance

---

## 🛠️ Tech Stack

* **Backend Framework**: FastAPI
* **LLM Orchestration**: LangGraph, LangChain
* **LLM Provider**: Groq (Llama-3.1-8b-instant)
* **Database**: PostgreSQL (Session storage & Graph Checkpoints)
* **Vector Store**: ChromaDB
* **Embeddings**: chromaDB default model `all-MiniLM-L6-v2`
* **Frontend**: HTML5, CSS3, Vanilla JavaScript
* **ORM**: SQLAlchemy

----

## Backend Structure
### 1. Client ↔ Backend (Session Lifecycle)
The client interacts with the backend using **explicit session and thread IDs**.

#### Flow
1. Client calls `/create-new-session`
   - Creates a persistent session
2. Client starts a chat using `/start`
   - A thread is created and marked active
3. Classification proceeds until:
   - `MATCH_FOUND` → thread closes
   - `MORE_INFO` → graph pauses
4. Client resumes using `/resume`
   - Execution continues from last checkpoint

**Only one active thread per session is allowed.**

### 2. Database Structure
#### `ChatSession` table
Stores session and thread metadata:

- `session_id` – User-level container
- `thread_id` – Active classification flow
- `is_active` – Ensures single active thread
- `thread_created_at`
- `thread_last_used_at`
- `thread_closed_at`

This table is the **source of truth** for session state.

### 3. Race Condition Prevention
Race conditions are prevented using:
* **Row-level locking**
  ```Python
  db.query().filter().with_for_update()...
  ```
* Every /start, /resume, and /create-new-chat request:
>>* locks the session row.\
>>* validates thread ownership.\
>>* checks is_active flag.

This guarantees:
* No concurrent classification on the same session
* No stale thread reuse
* No double closure of a thread

------

## 4. Graph Checkpointer Setup
The LangGraph workflow uses a PostgreSQL-backed checkpointer provided by langgraph.What is checkpointed:
* Full graph state after every node execution
* Messages, expander output, retrieval results, analyzer decision

Why this matters:
* Allows safe interruption (MORE_INFO)
* Enables resume without recomputation

Checkpoint data is deleted when a thread completes to avoid stale state reuse.

------
## How It Works (Classification Flow)
### Step 1: Expander
* Normalizes user input and Anchors NCO division
* Generates structured semantic search query
* Explicitly documents assumptions

### Step 2: Retriever
* Performs vector search in ChromaDB
* Supports one controlled query refinement
* Merges results to preserve context

### Step 3: Analyzer
* Audits user input, retrieval, and expander logic
* Detects ambiguity, hallucination, retrieval noise
* Outputs one status:
>* MATCH_FOUND
>* MORE_INFO
>* IMPROVED_SEARCH (internal only)

### Step 4: Graph Control
* Enforces:
>* no infinite loops
>* no guessing under ambiguity
>* no repeated self-correction

* Either:
>* ends the flow, or
>* pauses safely for user clarification

------

## Getting Started
### Backend Local setup
### Prerequisites
* Python 3.10+
* PostgreSQL
* Groq API key
* langsmith api key (optional if you want tracing on langsmith)

### 1. Clone the Repository
```
git clone "https://github.com/abhi-Sharma-Raun/NCO-Classification-Chatbot.git"
cd nco-classification-chatbot
```
### 2. Create Virtual Environment
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
### 3. pip install -r requirements.txt
```
pip install -r requirements.txt
```
### 4.Environment Variables
```
database_username=postgres
database_password=postgres
database_hostname=localhost
database_port=5432
database_name=nco_db
checkpointer_database_name=nco_checkpoints

groq_api_key=YOUR_GROQ_KEY

langsmith_tracing=false
langsmith_endpoint=
langsmith_api_key=
langsmith_project=
```
### 5. Prepare Embeddings
Run the `prepare_embeddings.py` script to prepare embeddings and it will store embeddings in the same directory.To run this, Go in the current project directory in the terminal and then run below command:
```
python "./prepare_embeddings.py"
```

### 6. Start the Backend
```
uvicorn app.main:app --reload
```
Backend will be available at:
```
http://localhost:8000
```
------

## 📂 Project Structure

```text
├── app/
│   ├── main.py            # FastAPI entry point & endpoints
│   ├── database.py        # Database connection logic
│   ├── models.py          # SQLAlchemy models (ChatSession)
│   ├── schemas.py         # Pydantic models for API validation
│   ├── utils.py           # LLM setup, ChromaDB client, Checkpointer
│   ├── config.py          # Configuration & Constants (New)
│   └── src/
│       ├── graph.py       # LangGraph workflow definition
│       └── prompts/       # System prompts for Agents
│           ├── expander_prompt.py
│           └── analyzer_prompt.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── embeddings/            # ChromaDB persistence directory
├── .env                   # Environment variables
├── prepare_embeddings.py
└── requirements.txt       # Python dependencies
```
------

## Notes
* The backend enforces classification safety, not the frontend
* Prompts are advisory, the graph is authoritative
* Ambiguity is handled explicitly, never silently

For deeper details:
* **PROMPTS.md** → Prompt design & motivation
* **GRAPH_FLOW.md** → Graph control logic