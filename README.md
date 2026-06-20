<div align="center">

# 🤖 MemGraph

**A Stateful Agentic AI Assistant**

*Short-term memory · Long-term memory · Multi-thread chat · Tool use · PostgreSQL persistence · LangSmith observability*

---

![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Graph%20Orchestration-1C6B40?style=flat-square&logo=graphql&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Framework-1C6B40?style=flat-square&logo=chainlink&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM%20Inference-F55036?style=flat-square&logo=groq&logoColor=white)
![LangSmith](https://img.shields.io/badge/LangSmith-Observability-F5A623?style=flat-square&logo=langchain&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)

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
- 🧠 **Long-Term Memory** — Extracts durable user facts (name, profession, goals, projects, interests, preferences) and injects them into every system prompt
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

All node logic lives in `backend/nodes.py`.

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

After every turn, `memory_write_node` scans the recent human messages for durable facts using a structured-output chain (`backend/chains.py`):

- Name, Profession, Goals
- Active projects
- Interests and preferences

Facts are stored as key-value pairs in a `PostgresStore`, namespaced per `user_id`. Before each reply, `chat_node` loads them via `load_memories()` and injects them into the system prompt — giving the model persistent knowledge across completely separate sessions.

---

## 🔧 Available Tools

Defined in `backend/tools.py` and bound to the model via `model_with_tools`:

| Tool | Purpose | Required Env Var |
|------|---------|-------------------|
| `fetch_weather` | Current weather for a city/location (WeatherAPI) | `API_KEY` |
| `get_stock_price` | Latest quote for a stock symbol (Alpha Vantage) | `STOCK_API` |
| `python_tool` (`PythonREPLTool`) | Precise/arbitrary Python computation | — |
| `search_tool` (`TavilySearch`) | General web search | `TAVILY_API_KEY` |

---

## 🗂️ Project Structure

```
.
├── backend/
│   ├── __init__.py
│   ├── base_model.py        # Base LLM instance (Groq via LangChain init_chat_model)
│   ├── chains.py             # Structured-output chain for memory fact extraction
│   ├── graph.py               # LangGraph graph definition, compilation, checkpointer & store setup
│   ├── nodes.py                # All graph node implementations + should_summarize router
│   ├── schemas.py               # Pydantic schemas (MemoryFact, MemoryFacts)
│   ├── state.py                  # ChatState TypedDict definition
│   ├── store_helper.py            # Namespace helpers + load_memories()
│   └── tools.py                     # Tool definitions + model_with_tools
├── frontend/
│   ├── __init__.py
│   ├── app.py                # Streamlit entry point
│   ├── chat_history.py        # Renders persisted chat history
│   ├── page_config.py          # Page title / icon / layout config
│   ├── session_state.py         # Bootstraps user_id, thread_id, chat_threads
│   ├── side_bar.py               # Thread list, "New Chat", thread switching
│   ├── stream.py                  # Streams chatbot responses + tool-use status
│   └── utils.py                    # generate_thread_id, reset_chat, add_threads,
│                                    #   load_conversation, display_name, retrieve_all_threads
├── .env                       # Environment variables (not committed)
├── .python-version
├── pyproject.toml             # uv-managed project & dependency definitions
├── uv.lock
├── requirements.txt            # Legacy pip requirements — see note below
└── README.md
```

> **Note:** This project is managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`). `requirements.txt` predates the current Postgres-backed architecture and references packages (e.g. Chroma, sentence-transformers, the SQLite checkpointer) that are no longer used by the code in `backend/`. Prefer `pyproject.toml` / `uv.lock` as the source of truth.

---

## ⚙️ Configuration

Key constants in `backend/nodes.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `MAX_HISTORY_TOKEN` | `6000` | Token threshold that triggers summarization |
| `RECENT_MESSAGE_TOKENS` | `2000` | Token budget for recent messages passed to `chat_node` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- A running **PostgreSQL** instance
- API keys for: [Groq](https://console.groq.com) (chat model), [Tavily](https://tavily.com) (web search), [WeatherAPI](https://www.weatherapi.com) (weather tool), and [Alpha Vantage](https://www.alphavantage.co) (stock tool)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Install dependencies

This project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
uv sync
```

Alternatively, with pip (using `pyproject.toml` directly):

```bash
pip install .
```

> Avoid `pip install -r requirements.txt` — that file is out of date relative to `pyproject.toml`.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URI=postgresql://user:password@localhost:5432/chatbot_db

# Chat model (Groq)
GROQ_API_KEY=your_groq_api_key_here

# Tools
TAVILY_API_KEY=your_tavily_api_key_here
API_KEY=your_weatherapi_key_here        # WeatherAPI.com — used by fetch_weather
STOCK_API=your_alphavantage_key_here    # Alpha Vantage — used by get_stock_price

# LangSmith observability (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=memgraph
```

By default, `backend/base_model.py` uses `init_chat_model` with `model_provider="groq"` and `model="openai/gpt-oss-120b"`. Because `init_chat_model` is provider-agnostic, you can swap in Anthropic, OpenAI, or any other supported provider by changing the `model` / `model_provider` arguments and supplying the corresponding API key.

### 4. Set up the database

`PostgresSaver` and `PostgresStore` both call `.setup()` automatically on first run. Just ensure your PostgreSQL instance is reachable at `DATABASE_URI`.

### 5. Launch the app

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` — your user ID is appended automatically (`?uid=...`) so identity and memory persist across refreshes.

> **Tip:** To export a visual of the compiled graph:
> ```bash
> python -c "from backend.graph import chatbot; open('graph.png','wb').write(chatbot.get_graph().draw_png())"
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

Optionally, name your compiled graph for cleaner trace labels in `backend/graph.py`:

```python
chatbot = graph.compile(
    checkpointer=checkpointer,
    store=store,
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
| ![Groq](https://img.shields.io/badge/-langchain--groq-F55036?style=flat-square&logo=groq&logoColor=white) | Chat model integration (`init_chat_model`, provider `groq`) |
| ![Tavily](https://img.shields.io/badge/-langchain--tavily-1C6B40?style=flat-square) | Web search tool |
| ![Python](https://img.shields.io/badge/-langchain--experimental-3776AB?style=flat-square&logo=python&logoColor=white) | `PythonREPLTool` for precise computation |
| ![PostgreSQL](https://img.shields.io/badge/-langgraph--checkpoint--postgres-4169E1?style=flat-square&logo=postgresql&logoColor=white) | Persistent conversation checkpoints |
| ![PostgreSQL](https://img.shields.io/badge/-langgraph--store--postgres-4169E1?style=flat-square&logo=postgresql&logoColor=white) | Persistent long-term memory store |
| ![Python](https://img.shields.io/badge/-python--dotenv-3776AB?style=flat-square&logo=python&logoColor=white) | Environment variable management |
| ![LangSmith](https://img.shields.io/badge/-LangSmith-F5A623?style=flat-square&logo=langchain&logoColor=white) | Tracing, observability & evals |

---

## 🔧 Extending MemGraph

**Add a new tool** — Define it in `backend/tools.py` and append it to the `TOOLS` list. `ToolNode` and `tools_condition` handle routing automatically.

**Change the LLM** — Swap the model in `backend/base_model.py` (`base_model`, used for summarization and memory extraction). The tool-bound chat model, `model_with_tools`, is defined in `backend/tools.py` via `base_model.bind_tools(...)` and will pick up the change automatically.

**Adjust memory extraction** — Edit the system prompt in `backend/chains.py`, the runtime extraction prompt and fact categories inside `memory_write_node` (`backend/nodes.py`), or update the `MemoryFact` / `MemoryFacts` Pydantic models in `backend/schemas.py` to capture additional fact fields.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.