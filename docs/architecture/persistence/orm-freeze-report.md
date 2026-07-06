# ORM Freeze Report — Sprint 5.2

> **Certificación oficial del ORM Layer para Ingestion BC**
>
> Fecha: 2026-07-05 | Estado: **FROZEN**
> Basado en: `persistence-design.md` v1.0 (DESIGNED)
> Auditoría: Sprint 5.2.5 — Quality Audit & Freeze

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Estado** | ✅ **APPROVED — FROZEN** |
| **Modelos** | 5 |
| **Association Tables** | 4 |
| **Relaciones ORM** | 12 |
| **Constraints (Unique + Check)** | 6 + 2 = 8 |
| **FKs (con ondelete policy)** | 9 |
| **Índices** | 11 |
| **Composite Objects** | 1 (SyncPolicy) |
| **TypeDecorators** | 8 (1 EntityIdType + 5 VO + 2 Enum) |
| **Tests** | 676 |
| **Regresiones** | 0 |
| **Riesgos Críticos** | 0 |
| **Riesgos Altos** | 0 |
| **Hallazgos** | 1 menor (corregido) |
| **Ready for Sprint 5.3 (Repositories)** | ✅ **YES** |

---

## 2. ORM Compliance Audit

### 2.1 Modelos vs Diseño

| Tabla | Columnas | Tipos | Nullability | PK | FKs | Constraints | Índices | Cumplimiento |
|-------|----------|-------|-------------|----|-----|-------------|---------|--------------|
| `ingestion_news_sources` | 8 | ✅ | ✅ | ✅ | — | 1 UQ | 1 IX | **100%** |
| `ingestion_feeds` | 16 | ✅ | ✅ | ✅ | 1 FK (CASCADE) | 1 UQ | 1 IX | **100%** |
| `ingestion_raw_articles` | 12 | ✅ | ✅ | ✅ | 1 FK (RESTRICT) | 2 UQ + 1 CK | 2 IX | **100%** |
| `ingestion_categories` | 9 | ✅ | ✅ | ✅ | 1 FK (SET NULL) | 1 UQ + 1 CK | 2 IX | **100%** |
| `ingestion_topics` | 7 | ✅ | ✅ | ✅ | — | 1 UQ | 1 IX | **100%** |

**Total columnas: 51** — todas verificadas contra `persistence-design.md` §1.2–§1.6.

### 2.2 Association Tables

| Tabla | Columnas | PK | FKs | Índices | Cumplimiento |
|-------|----------|----|-----|---------|--------------|
| `ingestion_news_source_categories` | 2 | (source_id, category_id) | 2× CASCADE | ix_nsc_category | **100%** |
| `ingestion_news_source_topics` | 2 | (source_id, topic_id) | 2× CASCADE | ix_nst_topic | **100%** |
| `ingestion_feed_categories` | 2 | (feed_id, category_id) | 2× CASCADE | ix_fc_category | **100%** |
| `ingestion_feed_topics` | 2 | (feed_id, topic_id) | 2× CASCADE | ix_ft_topic | **100%** |

### 2.3 TypeDecorator Strategy

| Estrategia | Tipo | Implementación | Cumplimiento |
|------------|------|---------------|--------------|
| T-01 | `EntityIdType[T]` genérico | `types.py` — parametrizado por clase | **100%** |
| T-02 | VO TypeDecorators (String) | 5 decoradores (ArticleTitleType, ArticleUrlType, CategoryNameType, SourceUrlType, LanguageType) | **100%** |
| T-03 | Enum TypeDecorators (VARCHAR) | 2 decoradores (SourceTypeType, SyncModeType) | **100%** |
| T-04 | SyncPolicy composite | `composite(SyncPolicy, ...)` con 7 columnas | **100%** |
| T-05 | JSON para metadata | `JSON(none_as_null=False)` con `"metadata"` column mapping | **100%** |
| T-06 | DateTime(timezone=True) | Todas las columnas datetime | **100%** |

### 2.4 Naming Convention

| Tipo | Diseño | Implementación | Cumplimiento |
|------|--------|---------------|--------------|
| Unique | `uq_{table}_{fields}` | 6 constraints con nombres explícitos | **100%** |
| Check | `ck_{table}_{rule}` | 2 constraints con nombres explícitos | **100%** |
| Index | `ix_{table}_{fields}` | 11 indexes con nombres explícitos | **100%** |
| FK (DB) | `fk_{child}_{parent}` | Auto-generado por naming convention | ✅ **Consistente** |

### 2.5 Hallazgos

| # | Severidad | Hallazgo | Estado |
|---|-----------|----------|--------|
| H-01 | **Menor** | `sync_mode` en FeedModel sin `default=SyncMode.PULL`. El diseño especifica `DEFAULT 'PULL'`. No bloqueante porque la aplicación siempre provee el valor desde el dominio, pero inconsistente con el diseño. | ✅ **Corregido** |

---

## 3. Performance Audit

### 3.1 Análisis N+1

| Relación | Estrategia | Riesgo N+1 | Veredicto |
|----------|-----------|------------|-----------|
| NewsSource → Feeds (1:N) | `lazy="select"` | Bajo — Feeds son ARs separados, se cargan bajo demanda | ✅ Correcto |
| Feed → Source (N:1 inversa) | `lazy="joined"` | Ninguno — JOIN único | ✅ Correcto |
| Category → parent (self-ref) | `lazy="joined"` | Ninguno — JOIN único | ✅ Correcto |
| Category → children (self-ref) | NO MAPEADA | Ninguno — acceso vía repositorio | ✅ Correcto |
| NewsSource → Categories (M:N) | `lazy="selectin"` | Ninguno — 1 query extra con IN clause | ✅ Correcto |
| NewsSource → Topics (M:N) | `lazy="selectin"` | Ninguno — 1 query extra con IN clause | ✅ Correcto |
| Feed → Categories (M:N) | `lazy="selectin"` | Ninguno — 1 query extra con IN clause | ✅ Correcto |
| Feed → Topics (M:N) | `lazy="selectin"` | Ninguno — 1 query extra con IN clause | ✅ Correcto |
| Feed → RawArticles (1:N) | NO MAPEADA | Ninguno — acceso siempre paginado vía repositorio | ✅ Correcto |

### 3.2 Análisis de Índices

| Índice | Diseño §1.8 | Implementado | Queries que soporta |
|--------|------------|--------------|---------------------|
| `ix_raw_articles_feed_fetched` | ✅ | ✅ (feed_id, fetched_at DESC) | find_by_feed() ORDER BY fetched_at |
| `ix_raw_articles_feed_url` | ✅ | ✅ (feed_id, url) | exists_by_url() |
| `ix_feeds_source_active` | ✅ | ✅ (source_id, is_active) | find_by_source(), find_active_by_source() |
| `ix_news_sources_active` | ✅ | ✅ (is_active) | find_active() |
| `ix_categories_parent` | ✅ | ✅ (parent_id) | find_by_parent() |
| `ix_categories_active` | ✅ | ✅ (is_active) | find_active() |
| `ix_topics_active` | ✅ | ✅ (is_active) | find_active() |
| `ix_nsc_category` | ✅ | ✅ (category_id) | Queries inversas category → source |
| `ix_nst_topic` | ✅ | ✅ (topic_id) | Queries inversas topic → source |
| `ix_fc_category` | ✅ | ✅ (category_id) | Queries inversas category → feed |
| `ix_ft_topic` | ✅ | ✅ (topic_id) | Queries inversas topic → feed |

**Total: 11/11 índices implementados.** Cobertura completa de queries esperadas en repositorios.

### 3.3 Riesgos de Performance

| Riesgo | Severidad | Notas |
|--------|-----------|-------|
| `lazy="joined"` en Feed → Source | **Informativo** | Un JOIN por feed cargado. Aceptable porque Source es padre directo. Si en el futuro hay queries que carguen 100+ feeds, puede requerir `selectinload` explícito desde Application Layer. |
| SQLite en testing ignora `desc()` en índices | **Informativo** | PostgresSQL respeta DESC indexes correctamente. No afecta producción. |

**Riesgos críticos: 0 | Riesgos altos: 0 | Riesgos medios: 0**

---

## 4. Roundtrip Audit

### 4.1 Cobertura de Tests

| Agregado/Entidad | Test | Fields verificados |
|-----------------|------|--------------------|
| **NewsSource** | `test_create_and_load` | id (EntityId), name, source_type (enum VO), source_url (VO), is_active, version |
| | `test_load_inactive_source` | is_active=False |
| | `test_unique_name_constraint` | UNIQUE constraint enforcement |
| | `test_version_increments_on_update` | Optimistic locking |
| | `test_news_source_full_roundtrip` | All domain fields via **kwargs |
| **Feed** | `test_create_and_load` | id, source_id, url (VO), label (VO), language (VO), retry_count, SyncPolicy (7 fields) |
| | `test_sync_policy_default_values` | SyncPolicy with defaults (PULL+interval) |
| | `test_feed_source_relationship` | N:1 joined load |
| | `test_source_feeds_relationship` | 1:N lazy select |
| | `test_interval_minutes_nullable_for_push` | nullable interval, PUSH mode |
| | `test_feed_full_roundtrip` | All fields + SyncPolicy equality |
| **RawArticle** | `test_create_and_load` | All 12 fields, VO types, dict metadata, datetimes |
| | `test_nullable_fields` | All nullable → None, default metadata {} |
| | `test_no_version_column` | Immutability verified |
| | `test_no_updated_at_column` | Immutability verified |
| | `test_raw_article_full_roundtrip` | All fields via domain-like flow |
| **Category** | `test_create_and_load` | id, name (VO), slug, description, is_active |
| | `test_self_referencing_parent` | parent joined load, parent fields |
| | `test_parent_can_be_null` | parent_id=None → parent=None |
| **Topic** | `test_create_and_load` | id, name, description, is_active |
| | `test_unique_name_constraint` | UNIQUE constraint enforcement |
| **M:N** | `test_source_categories_m2m` | selectinload, collection size, VO values |
| | `test_source_topics_m2m` | selectinload, collection size |
| | `test_feed_categories_m2m` | selectinload, collection size |
| | `test_feed_topics_m2m` | selectinload, collection size |
| **FKs** | `test_feed_requires_existing_source` | FK violation → IntegrityError |
| | `test_raw_article_requires_existing_feed` | FK violation → IntegrityError |
| | `test_category_parent_must_exist` | FK violation → IntegrityError |

### 4.2 Verificaciones de Fidelidad

| Concepto | Verificado | Detalle |
|----------|-----------|---------|
| Identidad (EntityId) | ✅ | `type(loaded.id) is SourceId`, equality checks |
| Value Objects (str-based) | ✅ | `.value` attribute preserved (ArticleTitle, ArticleUrl, CategoryName, SourceUrl) |
| Value Objects (code-based) | ✅ | `.code` attribute preserved (Language) |
| Value Objects (enum) | ✅ | Enum member identity preserved (SourceType, SyncMode) |
| SyncPolicy composite | ✅ | All 7 fields, equality check `loaded.sync_policy == policy` |
| Colecciones M:N | ✅ | selectinload, len(), value access |
| metadata dict | ✅ | Roundtrip of complex dict, default `{}` |
| Timestamps | ✅ | SQLite tzinfo workaround applied |
| Optimistic Locking | ✅ | version 1→2 after update |
| FK enforcement | ✅ | 3 FK violation tests (with PRAGMA foreign_keys=ON) |

### 4.3 Resumen

**Total tests: 28 | Passing: 28 (100%)**

---

## 5. SQLAlchemy Best Practices

### 5.1 Análisis de Calidad

| Aspecto | Estado | Notas |
|---------|--------|-------|
| Imports necesarios | ✅ | Sin imports huérfanos |
| `from __future__ import annotations` | ✅ | En todos los módulos |
| `mapped_column()` sin redundancia | ✅ | Cada columna declarada una vez |
| `__table_args__` completo | ✅ | 5/5 modelos con table args |
| `__mapper_args__` correcto | ✅ | 4/5 con version_id_col |
| Relaciones sin duplicación | ✅ | Cada relación declarada una vez |
| `viewonly=True` en todas las relaciones | ✅ | 8/8 relaciones |
| `secondary` vs `Table` correcto | ✅ | `secondary=` en relaciones, `Table` objects |
| `ForeignKey` con `ondelete` explícito | ✅ | 9/9 FKs |
| `server_default` vs `default` coherente | ✅ | server_default para timestamps, default para el resto |
| Naming convention activa | ✅ | `PersistenceBase.metadata` con naming_convention |

### 5.2 Oportunidades de Mejora (No Bloqueantes)

| # | Sugerencia | Impacto | Cuándo abordar |
|---|-----------|---------|---------------|
| S-01 | Extraer `_TimestampMixin` (created_at + updated_at) repetido en 4 modelos | Bajo — mejora DRY pero añade complejidad con `mapped_column()` en mixins | Sprint 5.3 o cuando un 2do BC use el mismo patrón |
| S-02 | Extraer `_VersionMixin` (version + __mapper_args__) repetido en 4 modelos | Bajo — mismo análisis que S-01 | Sprint 5.3+ |
| S-03 | Extraer `_ActiveMixin` (is_active + default) repetido en 3 modelos | Muy bajo — solo 3 columnas idénticas | Si se agrega un 4to modelo con is_active |

**Decisión**: No implementar mixins ahora. YAGNI aplicado. Los modelos son explícitos y legibles. La extracción a mixins tiene sentido solo cuando un 2do Bounded Context comparta el mismo `PersistenceBase`.

---

## 6. Freeze Declaration

```
╔══════════════════════════════════════════════════════════════╗
║              ORM LAYER — FREEZE CERTIFICATE                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Bounded Context:    Ingestion                               ║
║  Sprint:             5.2 — SQLAlchemy ORM Mapping            ║
║  Estado:             ✅ APPROVED — FROZEN                     ║
║  Fecha:              2026-07-05                              ║
║                                                              ║
║  Modelos ORM:        5                                      ║
║  Association Tables: 4                                      ║
║  Relaciones:         12 (8 viewonly, 4 association tables)  ║
║  Constraints:        6 UNIQUE + 2 CHECK + 9 FK              ║
║  Índices:            11                                      ║
║  Composite Objects:  1 (SyncPolicy, 7-column)               ║
║  TypeDecorators:     8 (1 generic + 5 VO + 2 enum)          ║
║                                                              ║
║  Tests:              676 total                              ║
║  Regresiones:        0                                       ║
║  Riesgos Críticos:   0                                       ║
║  Hallazgos:          1 menor (CORREGIDO)                     ║
║                                                              ║
║  Ready for Sprint 5.3:  ✅ YES                              ║
║  (Repository Layer)                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 6.1 Cambios Permitidos Post-Freeze

| Tipo | Permitido | Razón |
|------|-----------|-------|
| ❌ Nuevas columnas | NO | Requiere nuevo sprint de diseño |
| ❌ Nuevas relaciones | NO | Requiere nuevo sprint de diseño |
| ❌ Nuevos modelos | NO | Requiere nuevo sprint de diseño |
| ❌ Cambios en constraints | NO | Requiere nuevo sprint de diseño |
| ✅ Mixins de refactor (S-01, S-02, S-03) | SÍ, con tests | No alteran schema ni semántica |
| ✅ Corrección de bugs | SÍ, con tests | Siempre que no alteren contratos |
| ✅ Repositorios (Sprint 5.3) | SÍ | Usan el ORM, no lo modifican |
| ✅ Nuevos índices (si repositorios los requieren) | SÍ, con justificación | Performance — evaluar caso por caso |

### 6.2 Riesgos Remanentes

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| SQLite no soporta DESC index | Baja | Bajo | PostgreSQL en producción respeta DESC. Índice seguirá funcionando (sin orden reverso en SQLite). |
| SQLite no preserva tzinfo | Baja | Bajo | Tests usan `.replace(tzinfo=None)`. PostgreSQL preserva timezone. |

---

*— Fin del ORM Freeze Report —*
