<div align="center">

# 🤖 MemGraph

**A production-ready, Stateful Agentic AI Assistant**

*Short-term memory · Long-term memory · Multi-thread chat · Tool use · PostgreSQL persistence · LangSmith observability*

---

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Graph%20Orchestration-1C6B40?style=flat-square&logo=graphql&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Framework-1C6B40?style=flat-square&logo=chainlink&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97757?style=flat-square&logo=anthropic&logoColor=white)
![LangSmith](https://img.shields.io/badge/LangSmith-Observability-F5A623?style=flat-square&logo=langchain&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)
![Status](https://img.shields.io/badge/Status-Production%20Ready-22C55E?style=flat-square)

</div>

---

## 🎯 Why MemGraph?

Most LLM chatbots are **stateless by default** — every conversation starts from scratch. MemGraph solves three compounding production problems:

| # | Problem | Naive Approach | MemGraph's Solution |
|---|---------|---------------|-------------------|
| 1 | **Context window overflow** | Silently truncate old messages, losing context | Compress trimmed history into a rolling summary — the model always has the gist |
| 2 | **No cross-session identity** | User re-introduces themselves every session | `memory_write_node` extracts durable facts and injects them on every turn |
| 3 | **Stateless tool use** | Brittle custom loops outside the conversation | `ToolNode` and `tools_condition` are first-class graph nodes with full context |

---

## ✨ Features

- 🔄 **Stateful Conversations** — Full history persisted via `PostgresSaver` checkpointer across sessions, refreshes, and restarts
- 📝 **Automatic Summarization** — When history exceeds 6,000 tokens, old messages are compressed into a rolling summary
- 🧠 **Long-Term Memory** — Extracts durable user facts (name, profession, goals, interests) and injects them into every system prompt
- 🔧 **Tool Use** — The model calls external tools mid-conversation and loops back with full context intact
- 🖥️ **Streamlit UI** — Clean chat interface with sidebar thread management, streaming responses, and live tool-use indicators
- 💬 **Multi-Thread Support** — Create, switch, and resume unlimited parallel conversation threads per user
- 🔗 **URL-Persistent Identity** — `?uid=` query param embeds user identity in the URL — shareable and survives browser clears
- 🔭 **LangSmith Observability** — Full trace of every graph run: node-level spans, token usage, latency, injected prompts, and tool I/O

---

## 🏗️ Architecture

### Backend Graph

The chatbot is structured as a directed graph with conditional routing:

```
START
  │
  ▼
[should_summarize?]
  ├─ yes → [summary] → [cleanup] → [chat]
  └─ no  ──────────────────────────▶ [chat]
                                        │
                                [tools_condition?]
                                  ├─ tools → [tools] → [chat]
                                  └─ end  → [memory_write] → END
```

### Graph Nodes

| Node | Responsibility |
|------|---------------|
| `should_summarize` | Conditional router — checks if message history exceeds `MAX_HISTORY_TOKEN` (6,000 tokens) |
| `summary_node` | Generates or extends a running summary of trimmed messages using the base LLM |
| `cleanup_node` | Removes summarized messages from state using `RemoveMessage` |
| `chat_node` | Assembles the full prompt (system + memory + summary + recent messages) and invokes the tool-enabled model |
| `tool_node` | Executes any tool calls the model requests |
| `memory_write_node` | Extracts durable user facts from the conversation and upserts them into the long-term store |

### Frontend (Streamlit)

- **User identity** bootstrapped from `?uid=` query param — persists across refreshes
- **Thread management** — sidebar lists all past threads; switch or start a new chat via "New Chat"
- **Streaming** — responses streamed token-by-token via `chatbot.stream()` in `messages` mode
- **Tool status** — `st.status()` indicator shows which tool is running, collapses to ✅ on completion

---

## 🧠 Memory System

### Short-Term Memory (Summarization)

When the rolling conversation exceeds **6,000 tokens**, `summary_node` compresses the oldest messages into a plain-text summary. `cleanup_node` removes those messages from state. On subsequent turns, `chat_node` injects this summary as a `SystemMessage` — the model retains full context without holding raw history.

> Only the most recent **2,000 tokens** of raw messages are ever sent to the model.

### Long-Term Memory (Cross-Session Facts)

After every turn, `memory_write_node` scans the exchange for durable facts:

- Name, Profession, Goals
- Active projects
- Interests and preferences

Facts are stored as key-value pairs in a `PostgresStore`, namespaced per `user_id`. Before each reply, `chat_node` loads them via `load_memories()` and injects them into the system prompt — giving the model persistent knowledge across completely separate sessions.

---

## 🗂️ Project Structure

```
.
├── backend/
│   ├── ltm_graph.py        # LangGraph graph definition and compilation
│   ├── base_model.py       # Base LLM instance
│   ├── state.py            # ChatState TypedDict definition
│   ├── tools.py            # Tool definitions + model_with_tools
│   ├── schemas.py          # Pydantic schemas (MemoryExtractor, etc.)
│   ├── db_helper.py        # Namespace helpers, load_memories(), retrieve_all_threads()
│   └── utils.py            # generate_thread_id, reset_chat, add_thread,
│                           #   load_conversation, display_name
├── app.py                  # Streamlit frontend
├── .env                    # Environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration

Key constants in `backend/ltm_graph.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `MAX_HISTORY_TOKEN` | `6000` | Token threshold that triggers summarization |
| `RECENT_MESSAGE_TOKENS` | `2000` | Token budget for recent messages passed to `chat_node` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A running **PostgreSQL** instance
- API key for your LLM provider (Anthropic, OpenAI, etc.)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URI=postgresql://user:password@localhost:5432/chatbot_db
ANTHROPIC_API_KEY=your_api_key_here

# LangSmith observability (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=memgraph
```

### 4. Set up the database

`PostgresSaver` and `PostgresStore` both call `.setup()` automatically on first run. Just ensure your PostgreSQL instance is reachable at `DATABASE_URI`.

### 5. Launch the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` — your user ID is appended automatically (`?uid=...`) so identity and memory persist across refreshes.

> **Tip:** To export a visual of the compiled graph:
> ```bash
> python -c "from backend.ltm_graph import chatbot; open('graph.png','wb').write(chatbot.get_graph().draw_png())"
> ```

---

## 🔭 Observability with LangSmith

MemGraph integrates with [LangSmith](https://smith.langchain.com) for full tracing of every graph run — zero code changes required. LangGraph auto-detects the env vars and instruments everything automatically.

### Setup

Add the following to your `.env`:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=memgraph
```

Optionally, name your compiled graph for cleaner trace labels in `backend/ltm_graph.py`:

```python
graph = builder.compile(
    checkpointer=checkpointer,
    name="MemGraph"          # appears as the run name in LangSmith
)
```

### What you get

| Signal | Details |
|--------|---------|
| **Graph traces** | Every run as a tree — each node (`summary_node`, `chat_node`, `tool_node`, `memory_write_node`) is a labelled span |
| **LLM call inspection** | Exact prompt sent to the model at `chat_node` — see what memory + summary was injected |
| **Token usage & latency** | Per-node breakdown of input/output tokens and wall-clock time |
| **Tool call I/O** | Inputs and outputs for every tool invocation |
| **Error traces** | Full stack trace when any node fails, with the state that caused it |
| **Feedback & evals** | Tag runs, leave human feedback, and run automated evaluations from the LangSmith UI |

---

## 📦 Tech Stack

| Package | Purpose |
|---------|---------|
| ![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) | Frontend chat UI |
| ![LangGraph](https://img.shields.io/badge/-LangGraph-1C6B40?style=flat-square) | Graph-based agent orchestration |
| ![LangChain](https://img.shields.io/badge/-LangChain%20Core-1C6B40?style=flat-square) | Messages, runnables, trimming utilities |
| ![PostgreSQL](https://img.shields.io/badge/-langgraph--checkpoint--postgres-4169E1?style=flat-square&logo=postgresql&logoColor=white) | Persistent conversation checkpoints |
| ![PostgreSQL](https://img.shields.io/badge/-langgraph--store--postgres-4169E1?style=flat-square&logo=postgresql&logoColor=white) | Persistent long-term memory store |
| ![Python](https://img.shields.io/badge/-python--dotenv-3776AB?style=flat-square&logo=python&logoColor=white) | Environment variable management |
| ![LangSmith](https://img.shields.io/badge/-LangSmith-F5A623?style=flat-square&logo=langchain&logoColor=white) | Tracing, observability & evals |

---

## 🔧 Extending MemGraph

**Add a new tool** — Define it in `backend/tools.py` and append it to the `tools` list. `ToolNode` and `tools_condition` handle routing automatically.

**Change the LLM** — Swap the model in `backend/base_model.py`. Both `model` (summarization) and `model_with_tools` (chat) are defined there.

**Adjust memory extraction** — Edit the extraction prompt in `memory_write_node` or update the `MemoryExtractor` schema in `backend/schemas.py` to capture additional fact categories.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
