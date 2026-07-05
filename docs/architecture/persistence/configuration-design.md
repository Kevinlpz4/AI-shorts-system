# Configuration Design — EPIC 5

> **Diseño completo de configuración de base de datos para el BC Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-05
> Stack: Pydantic Settings 2.x, SQLAlchemy 2.x, Python 3.12, PostgreSQL (prod), SQLite (testing)
>
> **Este documento especifica el esquema de configuración de BD, engine, sesiones y logging.**
> NO implementa código ejecutable. NO modifica Foundation/Domain/Application.

---

## Table of Contents

1. [Settings Management](#1-settings-management)
   - 1.1 [Pydantic Settings vs Dataclass vs YAML](#11-pydantic-settings-vs-dataclass-vs-yaml)
   - 1.2 [Clase DatabaseSettings](#12-clase-databasesettings)
   - 1.3 [Clase AppSettings (composición)](#13-clase-appsettings-composición)
   - 1.4 [Carga de configuración](#14-carga-de-configuración)
2. [Environment Variables](#2-environment-variables)
   - 2.1 [Lista completa](#21-lista-completa)
   - 2.2 [Archivo .env](#22-archivo-env)
3. [Engine Configuration](#3-engine-configuration)
   - 3.1 [Factory Function](#31-factory-function)
   - 3.2 [Configuración por Entorno](#32-configuración-por-entorno)
4. [Session Factory](#4-session-factory)
   - 4.1 [sessionmaker](#41-sessionmaker)
   - 4.2 [Session Lifecycle](#42-session-lifecycle)
   - 4.3 [Inyección en Repositorios](#43-inyección-en-repositorios)
5. [Logging](#5-logging)
   - 5.1 [SQL Logging Condicional](#51-sql-logging-condicional)
   - 5.2 [Query Duration Logging](#52-query-duration-logging)
   - 5.3 [Slow Query Threshold](#53-slow-query-threshold)
6. [Secrets Management](#6-secrets-management)
   - 6.1 [Entornos y estrategia](#61-entornos-y-estrategia)
   - 6.2 [Flujo de resolución](#62-flujo-de-resolución)
7. [Integración con Alembic](#7-integración-con-alembic)
8. [Decisiones Arquitectónicas](#8-decisiones-arquitectónicas)

---

## 1. Settings Management

### 1.1 Pydantic Settings vs Dataclass vs YAML

| Opción | Validación | Tipado | Anidación | Infraestructura | Veredicto |
|--------|-----------|--------|-----------|-----------------|-----------|
| **✅ Pydantic Settings** | ✅ Automática (tipos, rangos, regex) | ✅ Completo | ✅ `model_nested` | ✅ Ya está en `requirements.txt` (pydantic>=2.5.0) | **Elegida** |
| ❌ `dataclass` simple | ❌ Manual | ✅ Parcial | ❌ Manual | ✅ Zero dependencias extra | Descartada |
| ❌ YAML + dataclass | ❌ Manual | ✅ Parcial | ✅ Sí | ❌ Requiere `pyyaml` | Descartada |

**Decisión: Pydantic Settings v2, `BaseSettings`.**

Justificación:

1. **Ya está en el proyecto** — `pydantic>=2.5.0` en `requirements.txt`. No se agregan dependencias.
2. **Validación automática** — Tipos, rangos (`Field(ge=0)`), regex para DATABASE_URL, defaults con lógica condicional.
3. **`.env` support nativo** — `model_config = SettingsConfigDict(env_file=".env")`. Carga automática de variables de entorno.
4. **Inmutabilidad** — `frozen=True` evita modificaciones accidentales en runtime.
5. **Caching** — `@lru_cache` para singleton sin estado global mutable.

### 1.2 Clase `DatabaseSettings`

```python
"""
Configuración de base de datos usando Pydantic Settings v2.

Ubicación: src/ingestion/infrastructure/persistence/settings.py
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Configuración específica de base de datos.

    Atributos:
        url: URL de conexión. PostgreSQL en producción, SQLite en desarrollo/testing.
        pool_size: Tamaño del pool de conexiones.
        max_overflow: Conexiones extra bajo demanda.
        pool_pre_ping: Verificar conexión antes de usar.
        pool_recycle: Reciclar conexiones después de N segundos.
        echo: Log de sentencias SQL.
        connect_timeout: Timeout de conexión en segundos.
        environment: Entorno de ejecución (development, testing, production).
        naming_convention: Convención de nombres de constraints.

    Ejemplos:
        # Desarrollo local con SQLite
        DatabaseSettings(_env_file=".env")

        # Producción
        DatabaseSettings(
            url="postgresql://user:pass@host:5432/dbname",
            environment="production",
        )
    """

    model_config = SettingsConfigDict(
        env_file=".env",           # Cargar desde .env si existe
        env_file_encoding="utf-8",
        extra="ignore",             # Ignorar variables extra en .env
        frozen=True,                # Inmutable en runtime
        case_sensitive=False,       # DATABASE_URL = database_url
    )

    # ── Database URL ────────────────────────────────────────
    url: str = Field(
        default="postgresql+psycopg2://localhost:5432/system_shorts",
        description="Database connection URL",
        json_schema_extra={"env": "DATABASE_URL"},
    )

    # ── Pool Configuration ──────────────────────────────────
    pool_size: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Database connection pool size",
        json_schema_extra={"env": "DATABASE_POOL_SIZE"},
    )

    max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum overflow connections",
        json_schema_extra={"env": "DATABASE_MAX_OVERFLOW"},
    )

    pool_pre_ping: bool = Field(
        default=True,
        description="Verify connection before use",
        json_schema_extra={"env": "DATABASE_POOL_PRE_PING"},
    )

    pool_recycle: int = Field(
        default=3600,
        ge=0,
        description="Recycle connections after N seconds",
        json_schema_extra={"env": "DATABASE_POOL_RECYCLE"},
    )

    pool_use_lifo: bool = Field(
        default=False,
        description="Use LIFO instead of FIFO for pool",
    )

    # ── Connection Configuration ────────────────────────────
    connect_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Connection timeout in seconds",
        json_schema_extra={"env": "DATABASE_CONNECT_TIMEOUT"},
    )

    # ── Logging ─────────────────────────────────────────────
    echo: bool = Field(
        default=False,
        description="Log all SQL statements",
        json_schema_extra={"env": "DATABASE_ECHO"},
    )

    # ── Environment ─────────────────────────────────────────
    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        description="Runtime environment",
        json_schema_extra={"env": "ENVIRONMENT"},
    )

    # ── Testing (solo cuando environment="testing") ─────────
    test_url: str = Field(
        default="sqlite:///:memory:",
        description="Test database URL (SQLite in-memory by default)",
        json_schema_extra={"env": "TEST_DATABASE_URL"},
    )

    test_echo: bool = Field(
        default=False,
        description="SQL logging in tests",
        json_schema_extra={"env": "TEST_DATABASE_ECHO"},
    )

    # ── Validación ──────────────────────────────────────────

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Valida que la URL sea un formato de conexión reconocido.

        Acepta:
        - postgresql://...
        - postgresql+psycopg2://...
        - sqlite:///...
        - sqlite:///:memory:

        No valida que la conexión funcione (eso es runtime).
        """
        if not any(
            v.startswith(prefix)
            for prefix in ["postgresql://", "postgresql+", "sqlite://"]
        ):
            raise ValueError(
                f"Unsupported database URL scheme: {v}. "
                "Expected postgresql://..., postgresql+..., or sqlite://..."
            )
        return v

    @field_validator("test_url")
    @classmethod
    def validate_test_url(cls, v: str) -> str:
        """Valida que la test URL sea sqlite."""
        if not v.startswith("sqlite://"):
            raise ValueError(
                f"Test database URL must be SQLite: {v}"
            )
        return v
```

### 1.3 Clase `AppSettings` (Composición)

```python
"""
Configuración global de la aplicación.

Usa composición para agrupar settings por dominio.
Fácil de extender cuando se agreguen más configuraciones
(ej: RedisSettings, CacheSettings, etc.).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Configuración global de la aplicación.

    Agrupa DatabaseSettings y futuras configuraciones
    (Redis, Cache, Queue, etc.) bajo un mismo objeto.

    Uso:
        settings = AppSettings()
        db_url = settings.database.url
        pool = settings.database.pool_size
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    # ── Database ────────────────────────────────────────────
    database: DatabaseSettings = DatabaseSettings()

    # ── Debug / Dev ─────────────────────────────────────────
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )


# ── Singleton con caching ────────────────────────────────────

@lru_cache
def get_settings() -> AppSettings:
    """Retorna la configuración global (singleton cacheado).

    El resultado se cachea con lru_cache para evitar leer
    .env en cada llamada. La cache se invalida si se modifica
    .env (en desarrollo, reiniciar el proceso).
    """
    return AppSettings()
```

**¿Por qué `@lru_cache` y no un módulo global?**: Evita problemas de orden de inicialización (el clásico "import circular de settings"). `@lru_cache` es thread-safe (en CPython) y garantiza que settings se inicialice solo una vez.

### 1.4 Carga de Configuración

```
Orden de resolución de valores en Pydantic Settings v2:
1. Argumentos del constructor (máxima prioridad)
2. Variables de entorno del sistema (con prefijo configurable)
3. Variables desde .env file
4. Defaults definidos en el modelo (mínima prioridad)

Ejemplo concreto para DATABASE_URL:
1. DatabaseSettings(url="postgresql://custom:pass@host/db")  → constructor
2. os.environ["DATABASE_URL"]                                 → sistema
3. .env file → DATABASE_URL=postgresql://dev:pass@localhost/db
4. default = "postgresql+psycopg2://localhost:5432/system_shorts"
```

### 1.5 Integración con Tests

```python
# En tests/conftest.py — override de settings para testing
@pytest.fixture(autouse=True)
def test_settings():
    """Override de settings para entorno de testing.

    Usa clear_cache() para que cada test file obtenga settings
    con DATABASE_URL overrideado por conftest.py.
    """
    # conftest.py ya setea os.environ["DATABASE_URL"] al inicio
    # Pydantic Settings lo lee automáticamente
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

Esto asegura que los tests usen la BD de testing sin contaminar otros tests.

---

## 2. Environment Variables

### 2.1 Lista Completa

| Variable | Tipo | Default | Entornos | Descripción |
|----------|------|---------|----------|-------------|
| `DATABASE_URL` | `str` | `postgresql+psycopg2://localhost:5432/system_shorts` | all | URL de conexión a BD principal |
| `DATABASE_POOL_SIZE` | `int` | `5` | dev, prod | Tamaño del pool de conexiones |
| `DATABASE_MAX_OVERFLOW` | `int` | `10` | dev, prod | Conexiones extra bajo demanda |
| `DATABASE_POOL_PRE_PING` | `bool` | `True` | all | Verificar conexión antes de usar |
| `DATABASE_POOL_RECYCLE` | `int` | `3600` | prod | Reciclar conexiones después de N segundos |
| `DATABASE_ECHO` | `bool` | `False` | dev | Log de sentencias SQL |
| `DATABASE_CONNECT_TIMEOUT` | `int` | `10` | prod | Timeout de conexión en segundos |
| `ENVIRONMENT` | `str` | `development` | all | Entorno: development, testing, production |
| `TEST_DATABASE_URL` | `str` | `sqlite:///:memory:` | testing | URL de BD para tests |
| `TEST_DATABASE_ECHO` | `bool` | `False` | testing | SQL logging en tests |
| `DEBUG` | `bool` | `False` | dev | Modo debug (logs detallados) |

### 2.2 Archivo `.env` (Desarrollo Local)

```bash
# ═══════════════════════════════════════════════════════════════
# AI Shorts System — Database Configuration
# ═══════════════════════════════════════════════════════════════
# Este archivo es para DESARROLLO LOCAL.
# En producción, las variables se configuran en el entorno del sistema.
# ═══════════════════════════════════════════════════════════════

# ── Database ──────────────────────────────────────────────
DATABASE_URL=postgresql+psycopg2://kevin:1234@localhost:5432/system_shorts
DATABASE_ECHO=True
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# ── Environment ───────────────────────────────────────────
ENVIRONMENT=development
DEBUG=True

# ── Testing ───────────────────────────────────────────────
# TEST_DATABASE_URL=sqlite:///data/test.db
# TEST_DATABASE_ECHO=False
```

Y el `.env.example` actualizado en la raíz del proyecto:

```bash
# ═══════════════════════════════════════════════════════════════
# AI Shorts System — Database Configuration (example)
# ═══════════════════════════════════════════════════════════════
# Copiá este archivo como .env y ajustá los valores.
# ═══════════════════════════════════════════════════════════════

# ── Database (OBLIGATORIO) ────────────────────────────────
# PostgreSQL (producción/desarrollo):
# DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
#
# SQLite (desarrollo local sin PostgreSQL):
# DATABASE_URL=sqlite:///data/system_shorts.db
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/system_shorts

# ── Pool (opcional, ver defaults) ─────────────────────────
# DATABASE_POOL_SIZE=5
# DATABASE_MAX_OVERFLOW=10
# DATABASE_POOL_PRE_PING=True
# DATABASE_POOL_RECYCLE=3600
# DATABASE_CONNECT_TIMEOUT=10

# ── Logging (opcional) ────────────────────────────────────
# DATABASE_ECHO=False
# DEBUG=False

# ── Environment ──────────────────────────────────────────
# ENVIRONMENT=development

# ── Testing (opcional) ────────────────────────────────────
# TEST_DATABASE_URL=sqlite:///:memory:
# TEST_DATABASE_ECHO=False

# ── Existing config (AI, APIs, etc.) ─────────────────────
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
DEFAULT_MODEL=openai/gpt-4o-mini
```

---

## 3. Engine Configuration

### 3.1 Factory Function

```python
"""
Factory de engine SQLAlchemy con configuración por entorno.

Ubicación: src/ingestion/infrastructure/persistence/engine.py
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .settings import DatabaseSettings


def create_db_engine(settings: DatabaseSettings) -> Engine:
    """Crea un engine SQLAlchemy configurado según el entorno.

    Args:
        settings: Configuración de base de datos (DatabaseSettings).

    Returns:
        Engine de SQLAlchemy listo para usar.

    La configuración varía por entorno:
    - Development: echo=True, pool pequeño, pool_pre_ping.
    - Testing: SQLite en memoria, echo=False, sin pool.
    - Production: pool mediano, pool_recycle, connect_timeout.

    Nota:
        SQLite ignora pool_size, max_overflow y pool_recycle
        (no tiene pooling nativo). Se setean a None para evitar
        warnings de SQLAlchemy.
    """
    url = settings.url
    env = settings.environment
    is_sqlite = "sqlite" in url

    # ── Parámetros base ────────────────────────────────────
    kwargs: dict = {
        "echo": settings.echo,
        "pool_pre_ping": settings.pool_pre_ping,
    }

    # ── Configuración específica por entorno ───────────────
    if env == "testing":
        # Testing: SQLite sin pool, sin logging
        kwargs.update({
            "echo": settings.test_echo,
            "poolclass": None if is_sqlite else None,
        })
        # SQLite en memoria requiere connect_args para
        # evitar "Database is locked" en tests concurrentes
        if "sqlite" in url and ":memory:" in url:
            kwargs.setdefault("connect_args", {"check_same_thread": False})

    elif env == "production":
        # Producción: pool robusto, timeout, reciclado
        kwargs.update({
            "pool_size": settings.pool_size,
            "max_overflow": settings.max_overflow,
            "pool_recycle": settings.pool_recycle,
            "pool_use_lifo": True,  # LIFO: conexiones recientes primero
            "connect_args": {
                "connect_timeout": settings.connect_timeout,
            },
        })

    else:  # development
        # Desarrollo: pool pequeño, echo activo por defecto
        kwargs.update({
            "pool_size": settings.pool_size,
            "max_overflow": settings.max_overflow,
            "pool_recycle": settings.pool_recycle,
        })

    # ── SQLite: limpiar parámetros de pool no soportados ──
    if is_sqlite:
        kwargs.pop("pool_size", None)
        kwargs.pop("max_overflow", None)
        kwargs.pop("pool_recycle", None)
        kwargs.pop("pool_use_lifo", None)

    return create_engine(url, **kwargs)
```

### 3.2 Configuración por Entorno (Resumen)

| Parámetro | Development | Testing | Production |
|-----------|-------------|---------|------------|
| **URL** | `.env` → PostgreSQL | `sqlite:///:memory:` | Variable de entorno del sistema |
| **echo** | `True` (default) | `False` | `False` |
| **pool_size** | 5 | — (SQLite) | 10 |
| **max_overflow** | 10 | — (SQLite) | 20 |
| **pool_pre_ping** | `True` | `True` | `True` |
| **pool_recycle** | 3600 | — (SQLite) | 3600 |
| **pool_use_lifo** | `False` | — (SQLite) | `True` |
| **connect_timeout** | — | — | 10s |
| **check_same_thread** | — | `False` (SQLite) | — |

### 3.3 Comportamiento del Pool por Entorno

```
DEVELOPMENT:
  Pool de 5 conexiones, 10 overflow.
  Conexiones se reciclan cada 1 hora.
  SQL logging activo (echo=True).
  Ideal para: desarrollo con recarga rápida.

TESTING:
  SQLite en memoria. Sin pool.
  Sin SQL logging.
  check_same_thread=False para pytest con
  múltiples fixtures en paralelo.

PRODUCTION:
  Pool de 10 conexiones, 20 overflow.
  LIFO: usa la conexión más reciente (reduce
  probabilidad de conexiones stale).
  Timeout de conexión: 10 segundos.
  Sin SQL logging.
```

---

## 4. Session Factory

### 4.1 `sessionmaker`

```python
"""
Factory de sesiones SQLAlchemy + UnitOfWork para el BC Ingestion.

Ubicación: src/ingestion/infrastructure/persistence/session.py
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Crea un sessionmaker configurado para el BC Ingestion.

    Configuración:
        - autocommit=False: El commit es explícito (UoW pattern).
        - autoflush=False: No flush automático antes de queries.
          El repositorio hace flush cuando es necesario (ej: detectar
          IntegrityError en RawArticleRepository.save()).

    Returns:
        sessionmaker listo para producir sesiones.

    Uso:
        SessionLocal = create_session_factory(engine)
        with SessionLocal() as session:
            repo = SQLAlchemyNewsSourceRepository(session)
            repo.save(source)
            session.commit()
    """
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=True,  # Expirar objetos después de commit
                                 # fuerza recarga en la próxima lectura
    )
```

**`autocommit=False`**: Obligatorio para el patrón UoW. El Application Service inicia una transacción (implícitamente al obtener la sesión), ejecuta operaciones, y hace commit/rollback explícitamente.

**`autoflush=False`**: Prevenimos flushes automáticos antes de cada query. El repositorio llama `session.flush()` cuando necesita asegurar que los cambios pendientes estén visibles para la misma transacción (ej: verificar unicidad antes de insertar en RawArticle).

**`expire_on_commit=True`**: Después de `commit()`, todos los objetos cargados se "expiran". La próxima vez que se acceda a un atributo, SQLAlchemy recarga desde la BD. Esto previene usar objetos stale fuera de la transacción.

### 4.2 Session Lifecycle

#### Flujo de vida de una sesión en un Application Service:

```
┌─────────────────────────────────────────────────────────────┐
│  Application Service (ej: DisableSourceUseCase)              │
│                                                              │
│  1. Obtener SessionFactory (inyectada en constructor)        │
│                                                              │
│  2. Iniciar UoW:                                             │
│     ┌─────────────────────────────────────────────────┐     │
│     │  with SQLAlchemyUnitOfWork(session_factory) as uow:  │     │
│     │                                                     │     │
│     │  3. session = uow.session   # sesión activa         │     │
│     │                                                     │     │
│     │  4. Repositorios usan la sesión:                    │     │
│     │     source_repo = SQLAlchemySourceRepo(session)     │     │
│     │     feed_repo = SQLAlchemyFeedRepo(session)         │     │
│     │                                                     │     │
│     │  5. source.disable(reason)   # dominio              │     │
│     │  6. source_repo.save(source) # merge/flush          │     │
│     │  7. uow.commit()             # session.commit()     │     │
│     │                                                     │     │
│     │  # Si algo falla → __exit__ hace session.rollback() │     │
│     └─────────────────────────────────────────────────┘     │
│                                                              │
│  8. publicar eventos (fuera de la transacción)               │
│  9. retornar Result                                          │
└─────────────────────────────────────────────────────────────┘
```

#### ¿scoped_session o sesiones por request?

| Opción | Descripción | Veredicto |
|--------|-------------|-----------|
| **✅ Sesiones por request/use case** | Crear sesión al inicio del use case, cerrar al final. | **Elegida** — Simple, explícito, sin magia. |
| ❌ `scoped_session` | Sesión global por thread/request. | Descartada — Oculta el ciclo de vida. Dificulta el testing. Problemas conocidos con manejo de transacciones anidadas. |
| ❌ Sesión global (singleton) | Una sesión para toda la app. | Descartada — Thread-unsafe. Las sesiones no son thread-safe. |

**Decisión**: Cada Application Service recibe un `sessionmaker` y crea sesiones explícitamente vía `SQLAlchemyUnitOfWork`. No hay sesiones globales, no hay `scoped_session`.

### 4.3 Inyección en Repositorios

Los repositorios SQLAlchemy reciben la sesión en el constructor, NO el sessionmaker:

```python
# ✅ Correcto: repositorio recibe sesión activa
class SQLAlchemyNewsSourceRepository:
    def __init__(self, session: Session):
        self._session = session

    def save(self, source: NewsSource) -> None:
        model = self._domain_to_model(source)
        self._session.merge(model)
        # NO hacer commit aquí — el commit lo maneja el UoW
```

**Principio**: El repositorio no sabe si está dentro de una transacción o no. Solo recibe una sesión y opera contra ella. El commit/rollback es responsabilidad del UoW/Application Service.

**Ciclo de inyección**:

```python
# En el contenedor DI (manual o con library):

def create_source_service(
    session_factory: sessionmaker[Session],
    source_repo_cls: type = SQLAlchemyNewsSourceRepository,
    feed_repo_cls: type = SQLAlchemyFeedRepository,
    uow_cls: type = SQLAlchemyUnitOfWork,
) -> SourceService:
    """Factory para SourceService.

    Los repositorios se crean dentro del UoW, cuando la sesión
    ya está activa. El service no recibe repositorios directamente,
    sino una factory que los crea con la sesión del UoW.
    """
    def repo_factory(session: Session) -> NewsSourceRepository:
        return source_repo_cls(session)

    def feed_repo_factory(session: Session) -> FeedRepository:
        return feed_repo_cls(session)

    uow = uow_cls(session_factory)

    return SourceService(
        source_repo_factory=repo_factory,
        feed_repo_factory=feed_repo_factory,
        uow=uow,
    )


# O más simple: pasar session al repositorio dentro del UoW
class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self):
        self._session = self._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    @property
    def session(self) -> Session:
        assert self._session is not None
        return self._session

    def commit(self):
        self._session.commit()
```

---

## 5. Logging

### 5.1 SQL Logging Condicional

El logging de SQL se controla con `echo` en el engine. Pero `echo` es binario (muestra TODO o nada). Para control más fino:

```python
import logging

# ── Logger específico para SQL ──
sql_logger = logging.getLogger("sqlalchemy.engine")

def configure_sql_logging(settings: DatabaseSettings) -> None:
    """Configura logging de SQL según el entorno.

    - DEVELOPMENT: logging.DEBUG (muestra SQL + parámetros).
    - TESTING: logging.WARN (solo errores).
    - PRODUCTION: logging.WARN (solo errores).

    Para slow queries, ver §5.3.
    """
    level = logging.DEBUG if settings.environment == "development" else logging.WARN
    sql_logger.setLevel(level)

    # En desarrollo, formatear SQL para legibilidad
    if settings.environment == "development":
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "[SQL] %(message)s"
        ))
        sql_logger.addHandler(handler)

    # Prohibir propagación a root logger (evita duplicados)
    sql_logger.propagate = False
```

**¿Por qué no usar `echo` del engine?** Porque `echo` es inflexible — mezcla SQL logging con output de SQLAlchemy. Usando el logger directamente podemos:
- Formatear el output.
- Enrutar a archivos.
- Filtrar queries lentas vs rápidas.
- Desactivar en producción sin modificar código.

### 5.2 Query Duration Logging

Para medir duración de queries, se usa un event listener de SQLAlchemy:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

query_logger = logging.getLogger("sqlalchemy.queries")

def setup_query_logging(engine: Engine, slow_query_threshold: float = 1.0) -> None:
    """Configura logging de duración de queries.

    Args:
        engine: Engine de SQLAlchemy.
        slow_query_threshold: Umbral en segundos para slow query log.

    Uso:
        setup_query_logging(engine, slow_query_threshold=0.5)
    """
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info["query_start_time"] = time.monotonic()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        total = time.monotonic() - conn.info["query_start_time"]
        conn.info["query_start_time"] = None

        if total > slow_query_threshold:
            query_logger.warning(
                "SLOW QUERY (%.2fs): %s",
                total,
                statement,
            )
        else:
            query_logger.debug(
                "Query (%.2fs): %s",
                total,
                statement,
            )
```

### 5.3 Slow Query Threshold

| Entorno | Threshold | Acción |
|---------|-----------|--------|
| Development | 0.5s | Log WARNING con SQL completo |
| Testing | 1.0s | Log WARNING (solo para detectar regresiones) |
| Production | 1.0s | Log WARNING + métrica a sistema de monitoreo (futuro) |

### 5.4 Configuración Completa de Logging

```python
def configure_all_logging(settings: DatabaseSettings, engine: Engine) -> None:
    """Configura TODO el logging de BD de una vez."""
    # 1. SQL logging condicional
    configure_sql_logging(settings)

    # 2. Query duration logging
    slow_threshold = {
        "development": 0.5,
        "testing": 1.0,
        "production": 1.0,
    }.get(settings.environment, 1.0)

    setup_query_logging(engine, slow_threshold)
```

---

## 6. Secrets Management

### 6.1 Entornos y Estrategia

| Entorno | ¿Dónde está DATABASE_URL? | ¿.env file? | Seguridad |
|---------|--------------------------|-------------|-----------|
| **Development** | `.env` file en raíz del proyecto | ✅ Sí | Baja — es local, no expuesto |
| **CI/CD** | Variable de entorno del CI (GitHub Secrets, GitLab CI vars) | ❌ No | Alta — secretos del CI |
| **Production** | Variable de entorno del sistema operativo (systemd env, Docker env, Kubernetes Secret) | ❌ No | Máxima — secrets rotados, acceso restringido |

### 6.2 Flujo de Resolución

```
┌─────────────────────────────────────────────────────────────────┐
│  RESOLUCIÓN DE DATABASE_URL                                     │
│                                                                  │
│  1. ¿os.environ["DATABASE_URL"] existe?                         │
│     ├── Sí → usar ese valor. FIN.                               │
│     └── No → continuar                                          │
│                                                                  │
│  2. ¿Existe .env en PROJECT_ROOT?                               │
│     ├── Sí → cargar .env con python-dotenv                     │
│     │   └── ¿os.environ["DATABASE_URL"] ahora existe?          │
│     │       ├── Sí → usar ese valor. FIN.                      │
│     │       └── No → continuar                                 │
│     └── No → continuar                                          │
│                                                                  │
│  3. Usar default (postgresql://localhost:5432/system_shorts)    │
│     └── Esto fallará a menos que PostgreSQL esté en localhost   │
│                                                                  │
│  En PRODUCCIÓN:                                                 │
│  - La variable de entorno la setea systemd/docker/k8s.          │
│  - No hay .env en producción.                                   │
│  - Si falta DATABASE_URL → la app falla al iniciar (fail fast). │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Reglas de Seguridad

1. **`.env` está en `.gitignore`** — ya está configurado. No se commitca.
2. **`.env.example`** no contiene secrets reales — solo valores placeholder.
3. **En producción**: usar variables de entorno del sistema o Docker secrets. No usar `.env`.
4. **En CI/CD**: usar GitHub Secrets, GitLab CI Variables, o similar.
5. **Rotación de secrets**: DATABASE_URL puede cambiar sin modificar código. Solo cambiar la variable de entorno.

### 6.4 Docker / Systemd

```bash
# ── Docker ──
docker run -e DATABASE_URL=postgresql://user:pass@host:5432/dbname ...

# ── Docker Compose ──
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
    env_file:
      - .env  # Solo en desarrollo

# ── Systemd service ──
[Service]
Environment=DATABASE_URL=postgresql://user:pass@host:5432/dbname

# ── Kubernetes Secret ──
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:pass@host:5432/dbname
```

---

## 7. Integración con Alembic

### 7.1 Comandos de Gestión

```bash
# ── Inicializar Alembic (una vez) ──
alembic init alembic
# Luego personalizar env.py y alembic.ini

# ── Crear migración manual ──
alembic revision -m "add_last_fetched_at_to_feeds"

# ── Auto-generar migración ──
alembic revision --autogenerate -m "detect_changes"

# ── Aplicar migraciones ──
alembic upgrade head

# ── Ver estado ──
alembic current
alembic history --verbose

# ── Rollback ──
alembic downgrade -1        # revertir última
alembic downgrade base       # revertir todo

# ── Generar SQL offline ──
alembic upgrade head --sql  # solo genera SQL, no ejecuta
```

### 7.2 Script de Automatización

```python
# scripts/manage_db.py
"""
Script de gestión de base de datos.

Uso:
    python scripts/manage_db.py upgrade        # aplicar migraciones
    python scripts/manage_db.py downgrade      # revertir última
    python scripts/manage_db.py current        # ver estado
    python scripts/manage_db.py history        # ver historial
    python scripts/manage_db.py revision -m "msg"  # crear migración
"""

import sys
from pathlib import Path

# Asegurar que src/ está en sys.path
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from alembic.config import Config
from alembic import command


def main():
    alembic_cfg = Config("alembic.ini")

    if len(sys.argv) < 2:
        print("Usage: python scripts/manage_db.py <command> [args]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        command.upgrade(alembic_cfg, revision)
    elif cmd == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        command.downgrade(alembic_cfg, revision)
    elif cmd == "current":
        command.current(alembic_cfg)
    elif cmd == "history":
        command.history(alembic_cfg)
    elif cmd == "revision":
        message = sys.argv[3] if len(sys.argv) > 3 else "auto"
        autogenerate = "--autogenerate" in sys.argv
        command.revision(alembic_cfg, message=message, autogenerate=autogenerate)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 7.3 Makefile (opcional)

```makefile
# Makefile — Database management
.PHONY: db-upgrade db-downgrade db-current db-history db-revision

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-current:
	alembic current

db-history:
	alembic history --verbose

db-revision:
	alembic revision --autogenerate -m "$(message)"

db-migrate:
	alembic upgrade head && alembic current
```

---

## 8. Decisiones Arquitectónicas

### Decisión C-01: Pydantic Settings v2 (no dataclass, no YAML)

| Opción | Tradeoff |
|--------|----------|
| **✅ Pydantic Settings v2 `BaseSettings`** | Validación automática. `.env` nativo. Tipado completo. Ya está en requirements.txt. |
| ❌ `dataclass` | Sin validación automática. Sin `.env` nativo. Hay que escribir boilerplate de carga. |
| ❌ YAML + dataclass | Requiere `pyyaml`. Sin validación automática. El schema de configuración queda en dos lugares. |

### Decisión C-02: Sesiones por request/use case (no scoped_session)

| Opción | Tradeoff |
|--------|----------|
| **✅ Sesión explícita por use case** | Simple, testeable, explícita. Sin magia. Fácil de razonar. |
| ❌ `scoped_session` | Oculta el ciclo de vida. Thread-local puede causar leaks. Dificulta el testing. |

### Decisión C-03: `autoflush=False` en sessionmaker

| Opción | Tradeoff |
|--------|----------|
| **✅ `autoflush=False`** | Control explícito de flushes. Previene writes accidentales durante reads. El repositorio hace flush cuando necesita (ej: detectar IntegrityError). |
| ❌ `autoflush=True` | Conveniente pero peligroso. Una query de lectura puede trigger un flush de writes pendientes, causando `IntegrityError` en momentos inesperados. |

### Decisión C-04: SQL logging vía logger (no `echo` del engine)

| Opción | Tradeoff |
|--------|----------|
| **✅ Logger `sqlalchemy.engine`** | Control granular de niveles. Formateo personalizado. Fácil de enrutar a archivos. Medición de duración. |
| ❌ `echo=True` en engine | Binario: muestra todo o nada. Sin control de formato. Mezcla con otros logs de SQLAlchemy. |

### Decisión C-05: DATABASE_URL vía variable de entorno (no hardcodeada)

| Opción | Tradeoff |
|--------|----------|
| **✅ Variable de entorno + .env fallback** | Estándar 12-factor app. Segura (secrets fuera del código). Portable entre entornos. |
| ❌ URL hardcodeada en settings.py | Compromiso de seguridad. Difícil de cambiar por entorno. Violación de 12-factor app. |

---

*Documento diseñado durante EPIC 5 del proyecto AI Shorts System.*
*Basado en: persistence-design.md v1.0, orm-mapping-strategy.md v1.0, transaction-boundaries.md v1.0*
