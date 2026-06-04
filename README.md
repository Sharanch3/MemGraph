# 🤖 MemGraph

A production-ready, Stateful Agentic AI Assistant built with **LangGraph**, **LangChain**, and **Streamlit**, featuring short-term memory, long-term memory, automatic conversation summarization, multi-thread chat history, tool use, and persistent storage via PostgreSQL.

---

## ✨ Features

- **Stateful Conversations** — Full conversation history persisted across sessions using a PostgreSQL checkpointer
- **Automatic Summarization** — Detects when conversation history exceeds a token threshold and compresses old messages into a rolling summary, keeping costs low and context focused
- **Long-Term Memory** — Extracts and stores durable user facts (name, profession, goals, interests, etc.) across conversations using a PostgreSQL store
- **Tool Use** — The model can call external tools mid-conversation and loop back to continue the response
- **Modular Graph Architecture** — Each concern (summarization, memory, chat, cleanup) is a discrete, testable node in a LangGraph `StateGraph`
- **Streamlit UI** — A clean chat interface with a sidebar for thread management, real-time streaming responses, and live tool-use status indicators
- **Multi-Thread Support** — Users can create new chats, switch between past conversations, and have their identity persisted via URL query params (`?uid=...`)

---

## 🏗️ Architecture

![Core Architecture](architecture/architecture_chatbot.png)



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

#### Nodes

| Node | Responsibility |
|---|---|
| `should_summarize` | Conditional router — checks if message history exceeds `MAX_HISTORY_TOKEN` (6,000 tokens) |
| `summary_node` | Generates or extends a running summary of trimmed messages using the base LLM |
| `cleanup_node` | Removes summarized messages from state using `RemoveMessage` |
| `chat_node` | Assembles the full prompt (system + memory + summary + recent messages) and invokes the tool-enabled model |
| `tool_node` | Executes any tool calls the model requests |
| `memory_write_node` | Extracts durable user facts from the conversation and upserts them into the long-term store |

### Frontend (Streamlit)

The UI is built in `app.py` and communicates directly with the compiled LangGraph chatbot:

- **User identity** is bootstrapped from the `?uid=` query param on first load and stored in `st.session_state`, so the same user is recognized across browser refreshes
- **Thread management** — the sidebar lists all past conversation threads (loaded from `retrieve_all_threads()`), lets users switch between them, and start a new chat via a "New Chat" button
- **Streaming** — responses are streamed token-by-token using `chatbot.stream()` in `messages` mode and piped to `st.write_stream()`
- **Tool status** — when the model triggers a tool call, a `st.status()` indicator shows which tool is running and collapses to ✅ when complete

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

Key constants in `backend/ltm_graph.py` that control memory behaviour:

| Constant | Default | Description |
|---|---|---|
| `MAX_HISTORY_TOKEN` | `6000` | Token threshold that triggers summarization |
| `RECENT_MESSAGE_TOKENS` | `2000` | Token budget for recent messages passed to the LLM in `chat_node` |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A running **PostgreSQL** instance
- API keys for your LLM provider

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
ANTHROPIC_API_KEY=your_api_key_here   # or OPENAI_API_KEY, etc.
```

### 4. Set up the database

The `PostgresSaver` checkpointer and `PostgresStore` both call `.setup()` automatically on first run. Just ensure your PostgreSQL instance is reachable at `DATABASE_URI`.

### 5. Launch the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`. Your user ID is appended to the URL automatically (`?uid=...`) so your identity and memory persist across refreshes.

To save a visual of the compiled graph instead:

```bash
python -c "from backend.ltm_graph import chatbot; open('graph.png','wb').write(chatbot.get_graph().draw_png())"
```

---

## 🧠 Memory System

### Short-Term Memory (Summarization)

When the rolling conversation exceeds **6,000 tokens**, `summary_node` compresses the oldest messages into a plain-text summary. `cleanup_node` then removes those messages from state. On subsequent turns, `chat_node` injects this summary as a `SystemMessage` so the model retains context without holding the full history.

### Long-Term Memory (Cross-Session Facts)

After every conversation turn, `memory_write_node` scans the recent exchange for durable facts about the user:

- Name, Profession, Goals
- Active projects
- Interests and preferences

Facts are stored as key-value pairs in a `PostgresStore`, namespaced per `user_id`. Before each reply, `chat_node` loads these facts via `load_memories()` and injects them into the system prompt — giving the model persistent knowledge about the user across completely separate sessions.

---

## 🔧 Extending the Chatbot

### Adding a new tool

Define your tool in `backend/tools.py` and add it to the `tools` list. LangGraph's `ToolNode` and `tools_condition` handle the rest automatically.

### Changing the LLM

Swap the model in `backend/base_model.py`. Both `model` (used for summarization) and `model_with_tools` (used for chat) are defined there.

### Adjusting memory extraction

Edit the extraction prompt in `memory_write_node` or update the `MemoryExtractor` schema in `backend/schemas.py` to capture additional fact categories.

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Frontend chat UI |
| `langgraph` | Graph-based agent orchestration |
| `langchain-core` | Messages, runnables, trimming utilities |
| `langgraph-checkpoint-postgres` | Persistent conversation checkpoints |
| `langgraph-store-postgres` | Persistent long-term memory store |
| `python-dotenv` | Environment variable management |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🎯 Problem Statement

Most LLM-powered chatbots are **stateless by default** — every conversation starts from scratch. The model has no memory of who the user is, what they've discussed before, or what they care about. This creates three compounding problems in production applications:

**1. Context loss within long conversations**
Language models have a fixed context window. As a conversation grows, naively feeding the entire history into every prompt becomes expensive and eventually hits the token limit entirely — either crashing the session or forcing the developer to silently truncate old messages, which causes the model to "forget" earlier parts of the same conversation.

**2. No identity continuity across sessions**
When a user returns the next day, the model treats them as a complete stranger. Any preferences, background, goals, or prior decisions mentioned in past sessions are gone. This forces users to re-explain themselves repeatedly, which degrades experience and trust.

**3. No awareness of tool execution state**
Vanilla chatbots can't call external tools mid-conversation and resume gracefully. Either tool use is bolted on as a post-processing step (losing conversational context), or developers wire up brittle custom loops that are hard to maintain.

---

## 🔩 What Bottlenecks This Solves

| Bottleneck | Naive Approach | This Project |
|---|---|---|
| **Context window overflow** | Truncate old messages silently, losing context | Summarize trimmed history into a rolling summary; the model always has the gist even if not the raw messages |
| **No memory across sessions** | User must re-introduce themselves every session | `memory_write_node` extracts durable facts and upserts them into a `PostgresStore`; `chat_node` injects them on every turn |
| **Expensive full-history prompts** | Send all N messages on every turn | Only the most recent 2,000 tokens of messages are sent; older context lives in the summary |
| **Stateless tool use** | Custom ad-hoc loops outside the conversation graph | `ToolNode` and `tools_condition` are first-class graph nodes; tool calls loop back into `chat_node` with full context intact |
| **No persistent conversation threads** | Session resets on page refresh | `PostgresSaver` checkpoints every graph state; threads survive refreshes, server restarts, and re-deployments |
| **Single-session UX** | One conversation per app instance | `thread_id` + `user_id` namespacing supports unlimited parallel threads per user, all switchable from the sidebar |
| **No user identity between tabs/devices** | `sessionStorage` or cookies, lost on clear | `?uid=` query param embeds the identity in the URL itself — shareable and persistent |
