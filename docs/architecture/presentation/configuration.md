# Design: Configuration

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0

---

## 1. Configuration Strategy

Pydantic Settings for type-safe configuration. Environment-based profiles (dev/test/prod). All secrets via environment variables — never hardcoded.

## 2. Settings Class

```python
# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "AI_SHORTS_",
        "case_sensitive": False,
    }

    # ── Application ──
    app_name: str = "AI Shorts System"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", pattern="^(development|testing|production)$")
    debug: bool = False

    # ── Database ──
    database_url: str = "sqlite:///./data.db"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # ── CORS ──
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]

    # ── Trusted Hosts ──
    trusted_hosts: list[str] = ["localhost", "127.0.0.1"]

    # ── Logging ──
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"

    # ── OpenAPI ──
    openapi_title: str = "AI Shorts System — Ingestion API"
    openapi_description: str = "News ingestion bounded context API"
    openapi_version: str = "1.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
```

## 3. Environment Profiles

| Variable | Development | Testing | Production |
|----------|------------|---------|------------|
| `AI_SHORTS_ENVIRONMENT` | `development` | `testing` | `production` |
| `AI_SHORTS_DATABASE_URL` | `sqlite:///./data.db` | `sqlite:///:memory:` | `postgresql+psycopg://...` |
| `AI_SHORTS_DB_ECHO` | `true` | `false` | `false` |
| `AI_SHORTS_DEBUG` | `true` | `true` | `false` |
| `AI_SHORTS_LOG_LEVEL` | `DEBUG` | `WARNING` | `INFO` |
| `AI_SHORTS_LOG_FORMAT` | `text` | `text` | `json` |
| `AI_SHORTS_WORKERS` | `1` | `1` | `4` |
| `AI_SHORTS_CORS_ORIGINS` | `["*"]` | `["*"]` | `["https://app.ai-shorts.com"]` |
| `AI_SHORTS_TRUSTED_HOSTS` | `["*"]` | `["*"]` | `["api.ai-shorts.com"]` |

## 4. .env File Structure

```bash
# .env (development)
AI_SHORTS_ENVIRONMENT=development
AI_SHORTS_DATABASE_URL=sqlite:///./data.db
AI_SHORTS_DB_ECHO=true
AI_SHORTS_DEBUG=true
AI_SHORTS_LOG_LEVEL=DEBUG
AI_SHORTS_LOG_FORMAT=text
AI_SHORTS_CORS_ORIGINS=["http://localhost:3000"]
AI_SHORTS_TRUSTED_HOSTS=["localhost","127.0.0.1"]
```

## 5. Factory Function

```python
# config/settings.py
_settings: Settings | None = None

def get_settings() -> Settings:
    """Get or create Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

## 6. Validation

Settings validates at import time. Invalid values raise `ValidationError` immediately — fail fast.

---

*See also: `composition-root.md`, `lifespan.py` design in `dependency-injection.md`*
