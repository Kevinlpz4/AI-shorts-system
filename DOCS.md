# AI Shorts System — Documentation

> Full-stack pipeline for AI-generated short-form video content.
> Research topics → AI scripts → Production.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Quick Start](#2-quick-start)
3. [Backend Architecture](#3-backend-architecture)
4. [API Reference](#4-api-reference)
5. [Database Schema](#5-database-schema)
6. [CLI Reference](#6-cli-reference)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Terminal Reference](#8-terminal-reference)
9. [Script Generation Flow](#9-script-generation-flow)
10. [Development Guide](#10-development-guide)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐   │
│  │Dashboard │  │  Topic   │  │ Terminal │  │  Settings  │   │
│  │   /      │  │ /create  │  │ /terminal│  │ /settings │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────────┘   │
│       │              │             │                         │
│  ┌────▼──────────────▼─────────────▼─────────────────────┐  │
│  │              Zustand Store (topicStore)                │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │              Application Use Cases                     │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │  Container (DI) — switch: Mock │ API via HTTP         │  │
│  └────────────────────────┬──────────────────────────────┘  │
└───────────────────────────┼──────────────────────────────────┘
                            │ HTTP (localhost:8000)
┌───────────────────────────┼──────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                 │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │              FastAPI /api/v1/*                         │  │
│  │  topics  scripts  discover  status  manual             │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │        Application Layer (Use Cases)                   │  │
│  │  Research: Discover │ Approve │ Reject │ List │ Manual │  │
│  │  Script:  Generate │ Get │ Regenerate                  │  │
│  └────┬──────────────────────┬───────────────────────────┘  │
│       │                      │                               │
│  ┌────▼──────────────┐ ┌─────▼──────────────────────────┐  │
│  │  Research Module  │ │  Core Domain                   │  │
│  │  (DDD sub-domain) │ │  Script, ContentIdea, Ports    │  │
│  │  ResearchTopic    │ │  ScriptGeneratorPort, AIProvider│  │
│  │  ResearchStatus   │ │  ContentEvaluator, Publisher    │  │
│  └────┬──────────────┘ └─────┬──────────────────────────┘  │
│       │                      │                               │
│  ┌────▼──────────────────────▼──────────────────────────┐  │
│  │           Infrastructure Layer                        │  │
│  │  SQLiteRepos │ OpenRouter AI │ Mock Providers        │  │
│  │  GoogleNews RSS │ File Persistence │ TTS │ Video     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python | 3.12.3 |
| API Framework | FastAPI | 0.136.3 |
| AI Provider | OpenRouter (multi-model) | — |
| Database | SQLite (WAL mode) | — |
| Frontend | Next.js (App Router) | 14.2.35 |
| State | Zustand | — |
| Styling | TailwindCSS | 3.4 |
| Fonts | JetBrains Mono + Orbitron | — |
| Testing (Backend) | pytest + pytest-asyncio | 9.0.3 |
| Testing (Frontend) | TypeScript (type-check) | 5.4 |

### Design Principles

- **Domain-Driven Design** — Business logic in domain entities, not in frameworks
- **Hexagonal Architecture** — Ports (interfaces) in domain, adapters in infrastructure
- **SOLID** — Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- **Strict TDD Mode** — Tests before implementation

---

## 2. Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (recommended: 20.x via nvm)
- OpenRouter API key (in `.env`)

### Backend Setup

```bash
# Clone and enter
cd AI_Shorts_System

# Python virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY

# Run the API server
python app/main.py api --reload
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

### Frontend Setup

```bash
# From project root
cd frontend

# Load Node.js (if using nvm)
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
nvm use

# Install dependencies
npm install

# Run dev server with API backend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
# → http://localhost:3000

# Or run with mock data (no backend needed)
npm run dev
# → Mock mode: all data is in-memory with 8 seeded topics
```

### Verify Everything Works

```bash
# Backend (in another terminal)
curl http://localhost:8000/api/v1/status
# → {"version":"1.0.0","uptime":"...","topics":{...}}

# Frontend: open http://localhost:3000
# You should see the cyberpunk dashboard with topic data
```

---

## 3. Backend Architecture

### Directory Structure

```
app/
├── main.py                  # Entry point (argparse: CLI commands + API)
├── config.py                # Settings (DB path, API keys, ports)

domain/                      # Core Domain (no external deps)
├── entities/
│   ├── script.py            # Script: hook, body, cta, duration, topic, tone, format
│   ├── idea.py              # ContentIdea
│   ├── video.py             # VideoAsset
│   ├── voice.py             # VoiceAudio
│   └── trend.py             # Trend
├── value_objects/
│   ├── duration.py          # Duration (seconds, optimal 30-60)
│   └── hook_type.py         # Hook type enum
├── services/
│   └── content_evaluator.py # Script evaluation + optimization
├── ports/
│   ├── ai_provider.py       # AIProvider, ScriptGeneratorPort, IdeaGeneratorPort
│   ├── script_repository.py # ScriptRepository Protocol
│   ├── content_repository.py
│   ├── publisher.py         # PublisherPort
│   ├── trend_source.py
│   ├── tts_provider.py
│   └── video_renderer.py
└── exceptions/
    ├── base.py              # DomainError base class
    ├── content.py           # ScriptValidationError, ScriptGenerationError, etc.
    └── script.py            # ScriptNotFoundError (404), ScriptAlreadyExistsError (409)

application/                 # Application Layer (orchestrates domain)
├── use_cases/
│   ├── generate_content.py  # Full pipeline: trends → idea → script → tts → video → publish
│   └── script/
│       ├── generate_script.py    # GenerateScriptUseCase
│       ├── get_script.py         # GetScriptUseCase
│       ├── regenerate_script.py  # RegenerateScriptUseCase
│       └── mappers.py            # ResearchTopic → ContentIdea bridge
├── dtos/
│   └── script.py            # ScriptDTO, GenerateScriptRequest
├── error_mapper.py          # DomainError → (log_level, message, http_status)
└── exceptions/
    └── script.py            # Application-level script exceptions

infrastructure/              # Infrastructure Layer (adapters)
├── ai/
│   ├── openrouter_provider.py  # OpenRouter (real AI calls)
│   └── mock_provider.py        # Mock AI for testing
├── persistence/
│   ├── sqlite_script_repository.py  # SQLite ScriptRepository
│   ├── sqlite_repository.py         # SQLite ResearchRepository
│   └── file_repository.py           # File-based persistence
├── publishing/
│   └── mock_publisher.py    # Mock YouTube/TikTok publisher
└── tts/
    └── mock_tts_provider.py # Mock TTS

research/                    # Research Module (DDD sub-domain)
├── domain/
│   ├── entities/research_topic.py     # ResearchTopic aggregate root
│   ├── value_objects/                 # ResearchStatus, ResearchSource, ResearchScore
│   ├── ports/research_repository.py   # ResearchRepository Protocol
│   ├── services/                      # ResearchScorer, DuplicateDetector
│   └── events/                        # TopicDiscovered, TopicApproved, TopicRejected
├── application/
│   ├── use_cases/                     # AutoDiscoverTopics, ApproveTopic, RejectTopic, etc.
│   └── dtos.py                        # Research DTOs
└── infrastructure/
    ├── persistence/sqlite_repository.py  # SQLite ResearchRepository
    └── sources/                          # GoogleNewsRSS, MockSource

presentation/                # Presentation Layer
├── cli/
│   ├── container.py         # DI Container (CLI)
│   └── commands.py          # CLI command handlers
└── api/
    ├── container.py         # ApiContainer (extends CLI container, adds script deps)
    ├── main.py              # FastAPI app factory
    ├── error_handlers.py    # DomainError → JSON responses
    └── routes/
        ├── topics.py        # Topic CRUD endpoints
        ├── scripts.py       # Script generation endpoints
        └── discover.py      # Discovery + status endpoints
```

### Key Domain Entities

**Script** (`domain/entities/script.py`):
```
- hook: str        — Hook del guion (≥ 10 chars)
- body: str        — Desarrollo (≥ 50 chars)
- cta: str          — Call to action (≥ 5 chars)
- duration: int    — Segundos (30-60 óptimo)
- topic: str       — Tema general
- tone: str        — educational | entertaining | controversial | inspirational
- format: str      — story | list | tutorial | fact | reaction
- is_valid()       — hook ≥ 10 AND body ≥ 50 AND cta ≥ 5
```

**ResearchTopic** (`research/domain/entities/research_topic.py`):
```
- id, title, description, content
- source (ResearchSource with name, type, url)
- status: FOUND → PENDING_REVIEW → APPROVED | REJECTED
- score (ResearchScore with relevance, popularity, recency, source_reliability)
- url, author, published_at, created_at, reviewed_at, duplicate_hash
- approve() / reject() / markAsPendingReview() — immutable transitions
```

---

## 4. API Reference

Base URL: `http://localhost:8000/api/v1`

### System

#### `GET /api/v1/`

Root endpoint. Returns API info.

```bash
curl http://localhost:8000/api/v1/
```

Response:
```json
{
  "name": "AI Shorts System API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### `GET /api/v1/status`

System status with topic counts.

```bash
curl http://localhost:8000/api/v1/status
```

Response:
```json
{
  "version": "1.0.0",
  "uptime": "0:05:23.123456",
  "topics": {
    "total": 10,
    "found": 2,
    "pending_review": 3,
    "approved": 3,
    "rejected": 2
  },
  "started_at": "2026-06-29T10:00:00"
}
```

### Topics

#### `GET /api/v1/topics`

List topics with optional filters.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status (`found`, `pending_review`, `approved`, `rejected`) |
| `source` | string | Filter by source name |
| `q` | string | Search query (searches title + description) |
| `min_score` | int | Minimum total score (0-100) |
| `limit` | int | Max results (default: 50) |

```bash
curl "http://localhost:8000/api/v1/topics?status=approved&limit=5"
```

Response:
```json
{
  "topics": [
    {
      "id": "abc-123",
      "title": "La IA está transformando la educación",
      "description": "5 casos reales...",
      "status": "approved",
      "score": { "total": 78, "relevance": 80, "popularity": 70, "recency": 90, "source_reliability": 75 },
      "source": { "name": "google-news", "type": "automatic" },
      "url": "https://...",
      "created_at": "2026-06-28T10:00:00",
      "reviewed_at": "2026-06-29T08:00:00"
    }
  ],
  "total": 1
}
```

#### `GET /api/v1/topics/{topic_id}`

Get a single topic by ID.

```bash
curl http://localhost:8000/api/v1/topics/abc-123
```

Response: Single topic object (same shape as above).  
**Status 404**: `{"detail": "Research topic not found: abc-123"}`

#### `POST /api/v1/topics/{topic_id}/approve`

Approve a topic (changes status to `approved`).

```bash
curl -X POST http://localhost:8000/api/v1/topics/abc-123/approve
```

Response: Updated topic object.  
**Status 409**: Topic already in terminal state (approved/rejected).

#### `POST /api/v1/topics/{topic_id}/reject`

Reject a topic (changes status to `rejected`).

```bash
curl -X POST http://localhost:8000/api/v1/topics/abc-123/reject
```

Response: Updated topic object.  
**Status 409**: Topic already in terminal state.

#### `POST /api/v1/topics/manual`

Create a topic manually.

```bash
curl -X POST http://localhost:8000/api/v1/topics/manual \
  -H "Content-Type: application/json" \
  -d '{"title": "Mi topic manual", "description": "Descripción", "url": "https://..."}'
```

Request body:
```json
{
  "title": "string (required)",
  "description": "string (required)",
  "url": "string | null",
  "source_name": "string (default: 'manual')"
}
```

Response: Created topic object. **Status 201.**

### Discovery

#### `POST /api/v1/discover`

Trigger automatic topic discovery from external sources.

```bash
curl -X POST http://localhost:8000/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"query": "inteligencia artificial", "limit": 10}'
```

Request body:
```json
{
  "query": "string (optional, trending if empty)",
  "limit": "int (default: 10)",
  "source_names": "string[] (optional, specific sources)"
}
```

Response:
```json
{
  "discovered": [/* Topic[] */],
  "duplicates": [/* Topic[] */],
  "errors": [{"source": "google-news", "error": "..."}]
}
```

### Scripts

#### `GET /api/v1/topics/{topic_id}/script`

Get the generated script for an approved topic.

```bash
curl http://localhost:8000/api/v1/topics/abc-123/script
```

Response:
```json
{
  "id": "script-001",
  "topic_id": "abc-123",
  "hook": "¿Sabías que la IA ya está transformando las aulas?",
  "body": "5 casos reales muestran cómo instituciones educativas están implementando inteligencia artificial para personalizar el aprendizaje...",
  "cta": "Seguinos para más contenido sobre IA en educación.",
  "duration": 45,
  "tone": "educational",
  "format": "story",
  "word_count": 132,
  "is_valid": true,
  "created_at": "2026-06-29T08:00:00",
  "updated_at": "2026-06-29T08:00:00"
}
```

**Status 404**: No script found for this topic.

#### `POST /api/v1/topics/{topic_id}/script/generate`

Generate a new script for an approved topic. **Idempotent**: if script exists, returns it.

```bash
curl -X POST http://localhost:8000/api/v1/topics/abc-123/script/generate \
  -H "Content-Type: application/json" \
  -d '{"duration": 45, "tone": "educational"}'
```

Request body:
```json
{
  "duration": "int (default: 45, range: 30-60)",
  "tone": "string (default: 'educational')"
}
```

Response: `ScriptDTO` (same shape as GET). **Status 201** if new, **200** if already existed.  
**Status 400**: Topic is not approved.  
**Status 404**: Topic not found.

#### `POST /api/v1/topics/{topic_id}/script/regenerate`

Regenerate an existing script (deletes old, generates new).

```bash
curl -X POST http://localhost:8000/api/v1/topics/abc-123/script/regenerate \
  -H "Content-Type: application/json" \
  -d '{"duration": 45, "tone": "entertaining"}'
```

Request body: Same as generate.  
Response: New `ScriptDTO`. **Status 200.**

### Error Responses

All errors follow this format:

```json
{
  "error": "SCRIPT_NOT_FOUND",
  "message": "Script not found for topic abc-123",
  "detail": null
}
```

HTTP Status Codes:
| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (validation error, topic not approved) |
| 404 | Not found (topic, script) |
| 409 | Conflict (already exists, terminal state) |
| 500 | Internal server error |

---

## 5. Database Schema

Both tables live in the same SQLite database file (default: `data/research.db`).

### `research_topics`

```sql
CREATE TABLE IF NOT EXISTS research_topics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    content TEXT DEFAULT '',
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending_review',
    score_total REAL DEFAULT 0,
    score_relevance REAL DEFAULT 0,
    score_popularity REAL DEFAULT 0,
    score_recency REAL DEFAULT 0,
    score_source_reliability REAL DEFAULT 0,
    url TEXT,
    author TEXT,
    published_at TEXT,
    created_at TEXT NOT NULL,
    reviewed_at TEXT,
    duplicate_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_research_topics_status ON research_topics(status);
CREATE INDEX IF NOT EXISTS idx_research_topics_created ON research_topics(created_at);
CREATE INDEX IF NOT EXISTS idx_research_topics_duplicate_hash ON research_topics(duplicate_hash);
```

### `scripts`

```sql
CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL UNIQUE,
    hook TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    cta TEXT NOT NULL DEFAULT '',
    duration INTEGER NOT NULL DEFAULT 45,
    tone TEXT NOT NULL DEFAULT 'educational',
    format TEXT NOT NULL DEFAULT 'story',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (topic_id) REFERENCES research_topics(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scripts_topic_id ON scripts(topic_id);
```

### Migration Pattern

Both repositories use `_ensure_table()` called on every instantiation:

```python
def _ensure_table(self):
    self._cursor.execute("""CREATE TABLE IF NOT EXISTS ...""")
    self._connection.commit()
```

This is not a migration system — it's a "create if not exists" pattern. For schema changes, a proper migration tool should be added in production.

---

## 6. CLI Reference

```bash
python app/main.py <command> [args]
```

### Research Commands

| Command | Description |
|---------|-------------|
| `research discover [--query] [--limit] [--sources]` | Discover topics from external sources |
| `research list [--status]` | List all research topics |
| `research approve <id>` | Approve a topic |
| `research reject <id>` | Reject a topic |
| `research manual` | Interactive manual topic creation |
| `research script generate <id>` | Generate script for approved topic |
| `research script view <id>` | View script for topic |
| `research schedule status` | Show scheduler status |
| `research schedule start` | Start the discovery scheduler |
| `research schedule stop` | Stop the discovery scheduler |
| `research schedule interval <minutes>` | Set scheduler interval |
| `research schedule queries [query ...]` | Set scheduler search queries |
| `research schedule run-now` | Run discovery immediately |

### API Command

| Command | Description |
|---------|-------------|
| `api [--port PORT] [--host HOST] [--reload]` | Start FastAPI server |

### Other Commands

| Command | Description |
|---------|-------------|
| `run` | Run full content pipeline |
| `trends` | Fetch current trends |
| `evaluate` | Evaluate content |
| `test` | Run test suite |

---

## 7. Frontend Architecture

### Directory Structure

```
frontend/src/
├── types/
│   ├── index.ts            # TopicData, ScriptData, KPIStats, TopicFilters, etc.
│   └── terminal.ts         # TerminalOutput, TerminalCommand, CommandHistory
├── domain/
│   ├── value-objects/      # Score, TopicStatus, Source
│   ├── entities/Topic.ts   # Topic aggregate root entity
│   ├── services/           # ScoringService, TopicModerationService
│   └── ports/              # ITopicRepository, ITopicSource
├── application/
│   └── use-cases/          # DiscoverTopics, ListTopics, ApproveTopic, RejectTopic, CreateManualTopic
├── infrastructure/
│   ├── Container.ts        # DI Composition Root (mock/API switch)
│   ├── api/
│   │   ├── MockTopicSource.ts    # Mock source (8 seeded topics)
│   │   ├── ApiTopicSource.ts     # API source (POST /api/v1/discover)
│   │   ├── ApiTopicRepository.ts # API repository (REST CRUD)
│   │   └── SourceRegistry.ts     # Source registry pattern
│   └── repos/
│       └── TopicRepositoryImpl.ts # In-memory repository
├── store/
│   └── topicStore.ts       # Zustand: topics, filters, KPI, scripts, all actions
├── hooks/
│   └── useTopics.ts        # useTopicList, useTopicDetail, useTopicModeration, useTopicDiscovery
├── components/
│   ├── layout/             # Sidebar, Header, DashboardLayout
│   ├── dashboard/          # KPIGrid, TopicList, TopicCard
│   ├── topic/              # TopicDetailPanel, ScoreRadar, ScoreGauge
│   ├── forms/              # ManualTopicForm
│   ├── terminal/           # Terminal (command parser, history, 11 commands)
│   └── ui/                 # Button, Card, Input, Select, StatusBadge
└── app/                    # Next.js App Router pages
    ├── layout.tsx          # Root layout (DashboardLayout wrapper)
    ├── globals.css         # Cyberpunk theme (colors, animations, glassmorphism)
    ├── page.tsx            # Dashboard (KPIs + topic list + detail panel)
    ├── create/page.tsx     # Manual topic creation form
    ├── discover/page.tsx   # Discovery page with search
    ├── topics/page.tsx     # All topics with detail panel
    ├── topics/[id]/page.tsx # Single topic detail
    ├── terminal/page.tsx   # Developer terminal with 11 commands
    ├── analytics/page.tsx  # Analytics (placeholder)
    └── settings/page.tsx   # Settings (placeholder)
```

### Routes

| Route | Type | Description |
|-------|------|-------------|
| `/` | Static | Dashboard with KPIs, topic list, detail panel |
| `/create` | Static | Create manual topic |
| `/discover` | Static | Discover topics with search query |
| `/topics` | Static | All topics with detail panel |
| `/topics/[id]` | **Dynamic** | Single topic detail |
| `/terminal` | Static | Developer terminal |
| `/analytics` | Static | Analytics (placeholder) |
| `/settings` | Static | Settings (placeholder) |

### Mock vs API Mode

The frontend automatically switches between mock data and real API via `NEXT_PUBLIC_API_URL`:

```typescript
// frontend/src/infrastructure/Container.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (API_URL) {
  this.repository = new ApiTopicRepository(API_URL);
  this.sourceRegistry.register(new ApiTopicSource(API_URL));
} else {
  this.repository = new TopicRepositoryImpl(createSeedTopics());
  this.sourceRegistry.register(new MockTopicSource("google-news"));
}
```

- **No env var** → Mock mode with 8 seeded topics, fully functional client-side
- `NEXT_PUBLIC_API_URL=http://localhost:8000` → API mode, reads/writes to FastAPI backend

### Design System

- **Colors**: `#0B0F1A` (background), cyan `#00f0ff`, magenta `#ff00e4`, green `#00ff41`, purple `#8257e5`, red `#ff004d`
- **Glassmorphism**: `bg-glass`, `backdrop-blur-xl`, `border-glass-border`
- **Typography**: JetBrains Mono (code), Orbitron (display/headings)
- **Animations**: `glow-pulse`, `fade-in`, `slide-in`, scan lines (CSS pseudo-elements)
- **Icons**: lucide-react

---

## 8. Terminal Reference

The terminal is a full command-line interface embedded in the web UI at `/terminal`.

### Features

- Black background with green/cyan monospace text
- Blinking `>_` prompt
- Command history (up/down arrow keys)
- Scrollable output with ANSI-style coloring
- ALL commands execute REAL actions via the API

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show all commands with descriptions | `>_ help` |
| `topics list [status]` | List topics (optional status filter) | `>_ topics list pending_review` |
| `topics approve <id>` | Approve a topic | `>_ topics approve abc-123` |
| `topics reject <id>` | Reject a topic | `>_ topics reject abc-123` |
| `topics discover [query]` | Run auto-discovery | `>_ topics discover inteligencia artificial` |
| `script generate <topicId>` | Generate script for approved topic | `>_ script generate abc-123` |
| `script view <topicId>` | View generated script | `>_ script view abc-123` |
| `script regenerate <topicId>` | Regenerate script | `>_ script regenerate abc-123` |
| `status` | Show system status | `>_ status` |
| `clear` | Clear terminal screen | `>_ clear` |
| `echo <text>` | Echo text back | `>_ echo hello world` |

### Output Example

```
>_ topics list
┌─────────────────────────────────────────────────────────────┐
│ ID        │ Title                    │ Status    │ Score    │
├───────────┼──────────────────────────┼───────────┼──────────┤
│ abc-123   │ La IA transforma...      │ approved  │ 78       │
│ def-456   │ Batería estado sólido    │ pending   │ 85       │
│ ghi-789   │ Ciberseguridad 2026      │ approved  │ 62       │
└───────────┴──────────────────────────┴───────────┴──────────┘

>_ status
✓ Backend connected: http://localhost:8000
  Topics: 10 total | 3 pending | 3 approved | 2 rejected | 2 found
  Version: 1.0.0
```

### Offline Mode

If `NEXT_PUBLIC_API_URL` is not set, the terminal shows:
```
[ERROR] Backend not connected. Set NEXT_PUBLIC_API_URL to enable real commands.
```

Only `help`, `echo`, and `clear` work in offline mode.

---

## 9. Script Generation Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Discovery  │    │   Approve    │    │   Generate  │
│ (Research)  │───→│ (Research)   │───→│   Script    │
└─────────────┘    └──────────────┘    └─────────────┘
                                               │
                    ┌──────────────────────────┤
                    ▼                          ▼
           ┌─────────────────┐       ┌─────────────────┐
           │  OpenRouter AI  │       │  Script exists?  │
           │  (generate_json)│       │  → Return cached │
           └────────┬────────┘       └─────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  Script entity   │
           │  is_valid()?     │
           │  hook ≥ 10       │
           │  body ≥ 50       │
           │  cta ≥ 5         │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  SQLite save     │
           │  (upsert)        │
           └─────────────────┘
```

### Bridge: ResearchTopic → ContentIdea

The `ScriptGeneratorPort` expects a `ContentIdea`, but scripts are generated from `ResearchTopic`. The bridge lives in `application/use_cases/script/mappers.py`:

```python
def research_topic_to_content_idea(topic, tone="educational", format="story"):
    return ContentIdea(
        hook=topic.title[:100],
        topic=topic.title,
        description=topic.description,
        keywords=[topic.title.split()[0]] if topic.title else [],
        format=format,
        trend_id=str(topic.id),
    )
```

### Idempotency

`GenerateScriptUseCase` is **idempotent** — calling it twice returns the existing script. To force regeneration, use the `/regenerate` endpoint.

### Validation

`Script.is_valid()` requires:
- `hook` ≥ 10 characters
- `body` ≥ 50 characters
- `cta` ≥ 5 characters

If validation fails, the use case raises `ScriptValidationError` (400 Bad Request).

---

## 10. Development Guide

### Environment Variables

Create `.env` in the project root:

```env
OPENROUTER_API_KEY=sk-or-v1-...
# Optional:
DATABASE_PATH=data/research.db
API_HOST=127.0.0.1
API_PORT=8000
API_CORS_ORIGINS=["http://localhost:3000"]
```

For the frontend, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running Tests

```bash
# Backend — all tests
python -m pytest

# Backend — unit only
python -m pytest tests/ -m unit

# Backend — specific module
python -m pytest tests/research/

# Backend — with coverage
python -m pytest --cov=.

# Frontend — type check
cd frontend && npx tsc --noEmit

# Frontend — build check
cd frontend && npx next build
```

### Adding a New API Endpoint

1. Add the use case logic in `application/use_cases/`
2. Add the route in `presentation/api/routes/`
3. Register the use case in `presentation/api/container.py`
4. Add the router in `presentation/api/main.py`
5. Add tests in `tests/`

### Adding a New Frontend Page

1. Create page file in `frontend/src/app/<name>/page.tsx`
2. Add nav item in `frontend/src/components/layout/Sidebar.tsx`
3. Add any new components in `frontend/src/components/`
4. Add types in `frontend/src/types/`
5. Verify with `npx tsc --noEmit && npx next build`

### Coding Conventions

- **Python**: Type hints everywhere, async/await for I/O, domain entities are immutable (Object.freeze pattern in frontend, dataclass(frozen=True) in Python)
- **TypeScript**: Strict mode, no `any`, interfaces for contracts, enums for finite states
- **Imports**: Domain never imports from infrastructure. Application imports from domain. Infrastructure implements ports.
- **Error handling**: Always use DomainError subclasses in domain layer. ErrorMapper converts to HTTP responses at the edge.

---

## 11. Troubleshooting

### Backend won't start

```
Error: Address already in use
```
→ Port 8000 is taken. Use `python app/main.py api --port 8001`.

```
ModuleNotFoundError: No module named 'fastapi'
```
→ Run `pip install -r requirements.txt` in your virtual environment.

### OpenRouter API errors

```
Error 401: Unauthorized
```
→ Check your `OPENROUTER_API_KEY` in `.env`. Make sure it's valid.

```
Error 429: Rate limited
```
→ OpenRouter has rate limits. Wait and retry, or use a different model.

### Frontend shows empty data

- Mock mode: Make sure you're NOT setting `NEXT_PUBLIC_API_URL`
- API mode: Make sure the backend is running on port 8000
- Check browser console for network errors (F12 → Console/Network)

### Script generation fails

```
ScriptValidationError: Generated script is invalid (hook: 5 chars, needs ≥10)
```
→ The AI generated a poor script. Use `/regenerate` with a different tone.

```
ScriptGenerationError: AI provider failed
```
→ OpenRouter might be down. Check status.openrouter.ai. Try again later.

### Build errors (frontend)

```
Error: Definition for rule '@typescript-eslint/no-unused-vars' was not found
```
→ Run `npm install --save-dev @typescript-eslint/eslint-plugin` in the frontend directory.

```
TypeScript errors in build
```
→ Run `npx tsc --noEmit` to see all errors. Fix them one by one.

### Port already in use

```bash
# Find what's using the port
lsof -i :8000
# Or on Windows/WSL
netstat -ano | grep :8000
```

---

> **Last updated**: 2026-06-29
> **Generated from**: `sdd/script-generation-api-integration`
