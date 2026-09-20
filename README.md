# AI-Powered Customer Support Knowledge Assistant

A local-first RAG (Retrieval-Augmented Generation) chatbot that answers customer support questions strictly from a company's own uploaded documents — with zero-hallucination safeguards built into both the retrieval and prompt layers.

> If the answer isn't in the knowledge base, the bot says so instead of guessing. This is designed for support workflows, where a wrong answer is worse than no answer.

---

## Why this project

Generic LLM chatbots can make things up. For customer support — such as refund policies, warranty terms, return procedures, and service rules — a confidently wrong answer is worse than an honest "I don't know." This system enforces a safer pattern with two layers of protection:

1. Retrieval guard — the app only answers when a retrieved document chunk is similar enough to the user's question. If nothing is close enough, it does not fabricate an answer.
2. Prompt guard — the model is explicitly instructed to answer only from the retrieved context and to say exactly: "I don't have information on this." when the context does not support an answer.

## Features

- PDF, DOCX, and TXT document ingestion
- Chunked text splitting with overlap for better retrieval quality
- Local vector search using ChromaDB + ONNXMiniLM_L6_V2 embeddings
- Strict, grounded answers generated from the uploaded knowledge base only
- Per-session chat memory for short conversation continuity
- Response sanitization to remove markdown bullets and noisy punctuation
- API-key protection for administrative routes
- Rate limiting on the chat endpoint
- Analytics logging for query success and fallback behavior
- Lightweight browser dashboard for live testing
- Regression coverage for answer cleanup behavior

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Web framework | FastAPI 0.115 | REST API, routing, and dashboard hosting |
| ASGI server | Uvicorn | Service runner |
| Vector store | ChromaDB 0.5.5 | Local persistent similarity search |
| Embeddings | ONNXMiniLM_L6_V2 | Converts text into vectors |
| LLM | Groq SDK 1.7.0 | Generates final answers from retrieved context |
| PDF parsing | pypdf | Extracts text from uploaded PDFs |
| DOCX parsing | python-docx | Extracts text from uploaded Word files |
| Metadata / analytics | SQLite | Tracks uploaded documents and query logs |
| Validation | Pydantic | Request and response schemas |
| Rate limiting | SlowAPI | Limits abusive request volume |
| Config | python-dotenv | Loads `.env` settings |

## Architecture

```text
POST /api/documents/upload
          │
          ▼
  loaders.py → raw text
          │
          ▼
  chunker.py → overlapping chunks
          │
          ▼
  vectorstore.py → ChromaDB vectors
          │
          ▼
  db.py → SQLite metadata + analytics

POST /api/chat {session_id, message}
          │
          ▼
  vectorstore.query() → retrieved chunks
          │
          ▼
  chat_service.py → strict context prompt
          │
          ▼
  Groq LLM → answer + sources + resolved
          │
          ▼
  sanitize_answer() → cleaned user-facing output
```

## Project structure

```text
app/
├── main.py                 # FastAPI app entry point and routes
├── config.py               # Environment-driven settings
├── security.py             # API key auth and rate limiting
├── schemas.py              # Pydantic request/response models
├── static/index.html       # Minimal browser dashboard
├── test_chat_service.py    # Regression test for answer sanitization
└── services/
    ├── loaders.py          # PDF/DOCX/TXT text extraction
    ├── chunker.py          # Overlapping paragraph-aware chunking
    ├── vectorstore.py      # ChromaDB retrieval wrapper
    ├── chat_service.py     # Retrieval guard + LLM orchestration + sanitization
    ├── memory.py           # Per-session conversation history
    └── db.py               # SQLite metadata and analytics

data/                       # Runtime: uploads, SQLite database, Chroma vectors
requirements.txt
.env.example
README.md
```

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# then set GROQ_API_KEY and APP_API_KEY in .env

uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000 to test the dashboard.

## API usage

```bash
# Ask a question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user-123", "message": "What is your return policy?"}'

# Upload a document
curl -X POST http://localhost:8000/api/documents/upload \
  -H "X-API-Key: YOUR_APP_API_KEY" \
  -F "file=@/path/to/faq.pdf"
```

Interactive API docs: http://localhost:8000/docs

## Configuration

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | LLM provider key |
| `GROQ_MODEL` | Which Groq model to use |
| `APP_API_KEY` | Must be passed via `X-API-Key` for admin routes |
| `MAX_DISTANCE_THRESHOLD` | How strict the retrieval check is before calling the LLM |
| `MAX_HISTORY_TURNS` | How many conversation turns are kept per session |
| `TOP_K` | How many chunks are retrieved per question |

## Design decisions

- CPU-only embeddings are used to avoid unstable CoreML execution paths on some Macs.
- The app is intentionally conservative: it prefers "I don't have information on this." over making up facts.
- Conversation history is in-process and resets on server restart.
- Ingestion is lightweight and incremental; adding a new document does not require reprocessing the existing ones.
- Chroma stores the vectors while SQLite tracks metadata and analytics for cleaner separation of concerns.

## Roadmap and known limitations

- Redis-backed session memory for multi-worker deployments
- Docker packaging for reproducible deployment
- OCR support for scanned image-based PDFs
- Richer admin dashboard and document delete controls
- Re-ranking and hybrid search improvements

## License

MIT
