


# Smartovate AI Agent

A conversational AI agent built with **LangChain** and **AWS Bedrock**, combining Retrieval-Augmented Generation (RAG) over a private knowledge base with live web search, persistent multi-turn memory, and automatic conversation summarization. Runs locally via Streamlit for testing and deploys to AWS as a serverless container (Lambda + API Gateway).

## Demo

[![Watch the demo](https://img.youtube.com/vi/4yjqOv8R71o/maxresdefault.jpg)](https://www.youtube.com/watch?v=4yjqOv8R71o)

## Overview

This agent can:
- Answer questions grounded in a custom knowledge base using **RAG** (vector store retrieval)
- Fall back to **live web search** (Tavily) when the knowledge base doesn't have an answer
- Maintain **persistent conversation memory** per user/thread, backed by DynamoDB
- **Summarize** long conversations automatically to stay within context limits
- Run identically in a local Streamlit test UI and as a production Lambda function

Built as part of an internship project at **Smartovate**.

---

## Architecture

```
                 ┌─────────────────┐
   Local dev →   │   Streamlit UI    │   (app.py)
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
   Production →  │  API Gateway →    │
                 │     Lambda        │   (handler.py)
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │    AI Agent       │   (LangChain create_agent)
                 │  + Summarization  │
                 │    Middleware     │
                 └───┬─────┬─────┬──┘
                     │     │     │
           ┌─────────▼┐ ┌──▼───┐ ┌▼──────────────┐
           │ RAG Tool │ │ Web  │ │  Bedrock LLMs  │
           │ (vector  │ │Search│ │ Haiku 4.5 /    │
           │  store)  │ │(Tavily)│ Titan / Nova   │
           └──────────┘ └──────┘ └────────────────┘
                     │
           ┌─────────▼──────────────┐
           │   DynamoDB (memory)     │
           │ - AgentCheckpoints      │
           │ - UserThreads           │
           └─────────────────────────┘
```

**Flow:** A user message comes in through Streamlit (local) or API Gateway → Lambda (production). The LangChain agent, backed by a DynamoDB checkpointer, decides whether to use the RAG tool, the web search tool, or answer directly, then generates a response via Bedrock. A summarization middleware condenses older turns to keep the conversation efficient over long sessions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangChain (`create_agent`) |
| LLM (chat) | AWS Bedrock — `anthropic.claude-haiku-4-5` |
| Embeddings | AWS Bedrock — `amazon.titan-embed-text-v1` |
| Summarization | AWS Bedrock — `amazon.nova-lite-v1` |
| Retrieval | Vector store (RAG) |
| Web search tool | Tavily |
| Memory / checkpointing | Amazon DynamoDB (`AgentCheckpoints`, `UserThreads`) |
| Local testing UI | Streamlit |
| Deployment | Docker + AWS Lambda + API Gateway |
| Dependency management | `uv` (`pyproject.toml` / `uv.lock`) |

---

## Project Structure

```
├── src/
│   ├── agent/
│   │   ├── aiAgent.py              # Agent definition (create_agent, tools, middleware)
│   │   └── get_agent.py            # Agent factory / singleton accessor
│   ├── aws/
│   │   └── bedrock_client.py       # Bedrock client setup
│   ├── memory/
│   │   └── thread_store.py         # DynamoDB-backed thread/session storage
│   ├── models/
│   │   ├── chat_model.py           # Bedrock chat model (Claude Haiku 4.5)
│   │   ├── embedding_model.py      # Bedrock embedding model (Titan)
│   │   └── summarisation_model.py  # Bedrock summarization model (Nova Lite)
│   ├── rag/
│   │   ├── data_loader.py          # Loads/prepares source documents
│   │   ├── get_vector_store_instance.py
│   │   └── vector_store.py         # Vector store creation & querying
│   └── tools/
│       ├── rag_tool.py             # RAG retrieval tool for the agent
│       └── web_search_tool.py      # Tavily web search tool
├── app.py                          # Streamlit app (local testing)
├── handler.py                      # AWS Lambda entry point
├── config.py                       # Configuration & environment loading
├── main.py                         # CLI / local entry point
├── dockerfile                      # Container image for Lambda deployment
├── pyproject.toml / uv.lock        # Dependencies (uv)
├── requirements.txt                # Dependencies (pip fallback)
└── .env                            # Environment variables (not committed)
```

---

## How the Agent Works

The core agent is defined using LangChain's `create_agent`:

```python
self.agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    middleware=[summarization],
    checkpointer=self.checkpointer
)
```

- **`model`** — the Bedrock chat model (Claude Haiku 4.5)
- **`tools`** — `rag_tool` (private knowledge base retrieval) and `web_search_tool` (Tavily)
- **`middleware`** — a summarization step that condenses conversation history using Nova Lite
- **`checkpointer`** — persists agent state per thread to DynamoDB, enabling multi-turn memory across sessions

### Models used (AWS Bedrock)

```python
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"   # chat / reasoning
EMBED_MODEL_ID = "amazon.titan-embed-text-v1"               # embeddings for RAG
SUMM_MODEL_ID = "amazon.nova-lite-v1:0"                      # conversation summarization
```

---

## Memory & Storage (DynamoDB)

The application uses two separate DynamoDB tables, each with a distinct responsibility.

### 1. `AgentCheckpoints`

Managed internally by `DynamoDBSaver` (LangGraph's checkpointer), used by the agent itself to persist conversation state and enable memory across calls.

- **Purpose**: Stores the agent's full internal state — messages, tool calls, checkpoint metadata — required for LangGraph to resume a conversation with real context.
- **Key**: `thread_id`
- **Written/read by**: `Agent` class only (via the checkpointer). Never accessed directly by `handler.py` or the frontend.

### 2. `UserThreads`

A custom table designed to support multi-user thread ownership and a UI-friendly conversation list, decoupled from LangGraph's internal checkpoint format.

- **Purpose**: Tracks which threads belong to which user, and stores a lightweight, UI-friendly copy of the conversation for display (sidebar, history).
- **Partition key**: `user_id` (string)
- **Sort key**: `thread_id` (string)
- **Attributes**:
  | Attribute | Description |
  |---|---|
  | `title` | First ~50 characters of the thread's first query, used as a display label |
  | `created_at` | ISO 8601 timestamp of thread creation |
  | `last_active_at` | ISO 8601 timestamp, updated on every message |
  | `messages` | List of `{role, content, timestamp}` objects, appended via `list_append` |
- **Written/read by**: `handler.py` (Lambda) and the Streamlit frontend, via `src/memory/thread_store.py`:
  - `create_thread(user_id, title)` — creates a new thread, returns its `thread_id`
  - `get_thread(user_id, thread_id)` — returns the thread if it belongs to this user, else `None` (used for ownership checks)
  - `list_threads(user_id)` — returns all threads for a user, most recent first
  - `get_messages(user_id, thread_id)` — returns the stored message history for display
  - `append_message(user_id, thread_id, role, content)` — appends one message and updates `last_active_at`
  - `touch_thread(user_id, thread_id)` — updates `last_active_at` only

### How they relate
The two tables intentionally duplicate message content. This trade-off avoids coupling the frontend/handler to LangGraph's internal checkpoint structure, at the cost of writing each message twice. Given typical message sizes, this has negligible cost impact.

### Access control

Every request that references an existing `thread_id` is checked against `UserThreads` via `get_thread(user_id, thread_id)`. If the thread doesn't exist under that `user_id`, the request is rejected with `403 Forbidden` — this is what prevents one user from accessing another user's conversation.

### IAM scope

Both tables are covered by a single least-privilege policy (`dynamodb-agent-checkpointers-policy-internship`), granting only:
`GetItem`, `PutItem`, `Query`, `UpdateItem`, `DeleteItem`, `BatchGetItem`, `BatchWriteItem`

scoped specifically to:
No broader table access (e.g. `AmazonDynamoDBFullAccess`) is granted.
---

## Getting Started

### Prerequisites

- Python (see `.python-version`)
- [`uv`](https://github.com/astral-sh/uv) for dependency management
- AWS account with Bedrock model access enabled (Claude Haiku 4.5, Titan Embeddings, Nova Lite)
- AWS credentials configured locally (`aws configure` or environment variables)
- A [Tavily](https://tavily.com) API key for web search
- Two DynamoDB tables created: `AgentCheckpoints`, `UserThreads`

### Installation

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=your_tavily_key
```

### Run Locally (Streamlit)

```bash
streamlit run app.py
```

## Deployment (AWS Lambda + API Gateway)

The agent is packaged as a Docker container and deployed to Lambda behind API Gateway.

1. **Build the image**
   ```bash
   docker build -t Smartovate-agent .
   ```

2. **Push to Amazon ECR**
   ```bash
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   docker tag Smartovate-agent:latest <account-id>.dkr.ecr.<region>.amazonaws.com/Smartovate-agent:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/Smartovate-agent:latest
   ```

3. **Create/update the Lambda function** from the ECR image, with `handler.py` as the entry point.

4. **Attach API Gateway** as a trigger to expose the agent over HTTPS.

5. **Set Lambda environment variables** matching your `.env` ( Tavily key) and ensure the Lambda execution role has permissions for:
   - `bedrock:InvokeModel`
   - `dynamodb:GetItem`, `PutItem`, `UpdateItem`, `Query` on `AgentCheckpoints` and `UserThreads`

> Add your actual deploy commands (SAM/CDK/Terraform/manual CLI) here once finalized, so this section reflects exactly how you deploy.

---

## Roadmap / Possible Improvements

- [ ] Add automated tests for tools and agent responses
- [ ] Add CI/CD pipeline for image build + Lambda deploy

---

## Author

Built by **Bouthayna Ajmi** during an internship at **Smartovate**.
