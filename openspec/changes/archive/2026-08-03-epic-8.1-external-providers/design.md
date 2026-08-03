# EPIC 8.1 — External Knowledge Providers Architecture & Official Integration Catalog

**Status**: DESIGN-ONLY — No code implementation
**Date**: 2026-07-21
**Stack**: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, Pydantic v2, httpx, feedparser
**Architecture**: Clean Architecture / DDD / Hexagonal — 4 Frozen BCs + Runtime (NOT a BC)

---

## Part 1 — Technology Taxonomy

### 1.1 RSS / Atom

| Attribute | Detail |
|-----------|--------|
| **Description** | XML-based syndication format for publish/subscribe content delivery. RSS 2.0 and Atom 1.0 are the two standards. Both deliver structured feeds of entries (title, link, summary, date, author). |
| **Advantages** | Universal adoption, zero auth for public feeds, standardized parsing (feedparser), auto-discovery via `<link rel="alternate">`, works without API keys, low latency for new content |
| **Limitations** | No filtering/search (full feed only), no webhooks (must poll), max history varies (10-50 entries), no built-in rate limiting |
| **Authentication** | None for public feeds. HTTP Basic Auth or query-string tokens for private feeds. |
| **Pagination** | Not supported natively. Each poll returns the full feed (last N items). Dedup by `guid` or `link`. |
| **Rate limiting** | Server-side varies. Recommended: poll every 15-30 min. >1/min may get 429 or IP ban. |
| **Polling strategy** | Periodic. Use `If-Modified-Since` / `ETag` headers. feedparser handles conditional GETs. |
| **Stability** | HIGH. RSS stable since 2002, Atom since 2005. Changes extremely rare. |
| **Maintenance effort** | MINIMAL. One adapter handles ALL RSS/Atom feeds. New sources = config only. |
| **Use cases** | Company blogs, news sites, podcasts, release notes, changelogs |

**TechnologyAdapter**: `RSSAdapter`

### 1.2 REST API

| Attribute | Detail |
|-----------|--------|
| **Description** | HTTP APIs using JSON payloads. GET for reads, POST for writes, standard HTTP status codes and headers. |
| **Advantages** | Structured data, rich filtering/pagination, official SDKs, rate limit headers, well-understood errors |
| **Limitations** | Each API has unique schema, requires per-provider logic, rate limits vary wildly (10-10000 req/hr), breaking changes require updates |
| **Authentication** | API key, OAuth 2.0 (Bearer token), Basic Auth, personal access tokens |
| **Pagination** | cursor-based, page-based, offset-based, Link headers — each API different |
| **Rate limiting** | Per-API documented. Use `X-RateLimit-*`, `Retry-After` headers. Respect 429. |
| **Polling strategy** | API-specific. Some support webhooks (preferred). Most require periodic polling. |
| **Stability** | MEDIUM. APIs evolve. Breaking changes possible (v1->v2). Pin versions when available. |
| **Maintenance effort** | MEDIUM. Custom parsing, error handling, and pagination per API. |
| **Use cases** | GitHub, Dev.to, Hacker News, Steam, structured data sources |

**TechnologyAdapter**: `RESTAdapter`

### 1.3 GraphQL

| Attribute | Detail |
|-----------|--------|
| **Description** | Query language where clients specify exact data requirements. Single endpoint, strongly typed schema, introspection. |
| **Advantages** | Exact data fetching, single endpoint, self-documenting schema, efficient for complex nested data |
| **Limitations** | Complex query construction, cost-based rate limiting, rare for news/content APIs, caching harder |
| **Authentication** | Bearer token or API key in header |
| **Pagination** | Cursor-based (Relay spec) or offset-based. Client-controlled page size. |
| **Rate limiting** | Query cost analysis. Each query has a cost; budget per time window. |
| **Polling strategy** | Same as REST — periodic polling. |
| **Stability** | MEDIUM. Schema evolution possible but breaking changes rare. |
| **Maintenance effort** | MEDIUM-HIGH. Query construction, introspection, cost calculation. |
| **Use cases** | GitHub GraphQL API, Contentful, headless CMS. Minimal adoption in news/content APIs currently. |

**TechnologyAdapter**: `GraphQLAdapter` (reserved for future)

### 1.4 Webhook (Push)

| Attribute | Detail |
|-----------|--------|
| **Description** | Server-to-server push. Source sends data TO your endpoint when events occur. Requires public HTTPS endpoint. |
| **Advantages** | Real-time delivery, zero polling, efficient bandwidth, immediate notification |
| **Limitations** | Requires public HTTPS endpoint, security concerns (signature verification), delivery guarantees vary |
| **Authentication** | HMAC signature verification, shared secret, or mutual TLS |
| **Pagination** | N/A — push model |
| **Rate limiting** | N/A — push model |
| **Polling strategy** | No polling — event-driven. Requires fallback polling if webhooks fail. |
| **Stability** | HIGH for concept. LOW for implementations (providers change payloads). |
| **Maintenance effort** | HIGH. Endpoint infrastructure, signature verification, payload parsing, retry handling, DLQ. |
| **Use cases** | GitHub webhooks, Stripe, Twilio. NOT suitable for initial EPIC 8.1. |

**TechnologyAdapter**: `WebhookAdapter` (reserved — Phase 3+)

### 1.5 HTML Scraping (Last Resort)

| Attribute | Detail |
|-----------|--------|
| **Description** | Parsing raw HTML via CSS selectors or XPath. The nuclear option. |
| **Advantages** | Works when no API/RSS exists, universal, can extract data unavailable elsewhere |
| **Limitations** | BRITTLE — breaks on HTML changes, no contract, legal gray area, anti-detection needed, high maintenance, slow |
| **Authentication** | None (but may need cookie consent, CAPTCHA handling) |
| **Pagination** | Manual — discover links from HTML structure |
| **Rate limiting** | Anti-scraping measures (Cloudflare, IP blocking) |
| **Polling strategy** | Infrequent (hourly+). Randomized intervals. |
| **Stability** | LOW. Any HTML change breaks the scraper. |
| **Maintenance effort** | HIGH. Regular monitoring for breakage. |
| **Use cases** | ONLY when no API or RSS exists. NEVER as first choice. |

**TechnologyAdapter**: `HTMLScrapingAdapter` (reserved — last resort only)

### 1.6 Git Feeds (Atom)

| Attribute | Detail |
|-----------|--------|
| **Description** | GitHub/GitLab provide standard Atom feeds for repository events (commits, releases, issues, PRs). |
| **Advantages** | Standard RSS format (reuse RSSAdapter), real-time tracking, no auth for public repos |
| **Limitations** | Limited to git-specific events, feed history short, some events require auth |
| **Authentication** | None for public repos. Personal access token for private. |
| **Pagination** | Standard RSS (full feed per poll) |
| **Rate limiting** | GitHub rate limits (60 req/hr unauthenticated, 5000 authenticated) |
| **Polling strategy** | Every 15-30 minutes |
| **Stability** | HIGH. GitHub Atom feeds stable. |
| **Maintenance effort** | MINIMAL. Uses RSSAdapter with minor metadata extraction. |
| **Use cases** | Tracking releases, watching trending repos, org activity |

**TechnologyAdapter**: `RSSAdapter` (reused — Git feeds are standard Atom)

### 1.7 Static JSON

| Attribute | Detail |
|-----------|--------|
| **Description** | Pre-built JSON files at a stable URL. No auth, no pagination, no dynamic behavior. |
| **Advantages** | Zero parsing complexity, no auth, no rate limits, instant loading |
| **Limitations** | Must be maintained by host, no real-time updates, freshness depends on host |
| **Authentication** | None |
| **Pagination** | N/A — entire dataset in one file |
| **Rate limiting** | None (CDN caching may apply) |
| **Polling strategy** | Daily or on-demand |
| **Stability** | HIGH. Static files rarely change. |
| **Maintenance effort** | ZERO on our side. |
| **Use cases** | Curated lists, dataset registries, awesome-lists |

**TechnologyAdapter**: `StaticJSONAdapter` (reserved for future)

### 1.8 XML Feed (Non-RSS)

| Attribute | Detail |
|-----------|--------|
| **Description** | Generic XML feeds that don't conform to RSS/Atom. Custom schemas. |
| **Advantages** | Structured data, complex relationships |
| **Limitations** | Custom parsing per feed, no standard tooling |
| **Authentication** | Varies |
| **Pagination** | Varies |
| **Rate limiting** | Varies |
| **Polling strategy** | Periodic polling |
| **Stability** | LOW-MEDIUM. Custom schemas unpredictable. |
| **Maintenance effort** | MEDIUM. Custom parser per schema. |
| **Use cases** | Scientific papers (arXiv), government data, legacy systems |

**TechnologyAdapter**: `XMLFeedAdapter` (reserved for future)

---

## Part 2 — Provider Catalog

### 2.1 AI Category

#### OpenAI Blog

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://openai.com/blog/rss.xml` |
| **Authentication** | None |
| **Format** | RSS 2.0 / Atom |
| **Unique identifier** | `openai-blog` |
| **Pagination** | Full feed (last ~20 entries) |
| **Limits** | None (public feed) |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH — standard RSS |
| **Risks** | Low — openai.com stable infrastructure |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~2-4 posts/month |

#### Anthropic

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://www.anthropic.com/feed.xml` |
| **Authentication** | None |
| **Format** | RSS 2.0 / Atom |
| **Unique identifier** | `anthropic` |
| **Pagination** | Full feed (last ~15 entries) |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~1-3 posts/month |

#### Google AI Blog

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://blog.google/technology/ai/rss/` |
| **Authentication** | None |
| **Format** | RSS 2.0 |
| **Unique identifier** | `google-ai` |
| **Pagination** | Full feed |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~3-6 posts/month |

#### HuggingFace Blog

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://huggingface.co/blog/feed.xml` |
| **Authentication** | None |
| **Format** | Atom |
| **Unique identifier** | `huggingface` |
| **Pagination** | Full feed |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~4-8 posts/month |

#### Reddit AI (r/artificial)

| Attribute | Detail |
|-----------|--------|
| **Technology** | Reddit RSS |
| **Official endpoint** | `https://www.reddit.com/r/artificial/.rss` |
| **Authentication** | None |
| **Format** | Atom (Reddit-flavored) |
| **Unique identifier** | `reddit-r-artificial` |
| **Pagination** | Last 25 posts per feed |
| **Limits** | Reddit rate limits (100 req/min authenticated, lower unauthenticated) |
| **Recommended polling** | Every 15 minutes |
| **Stability** | MEDIUM — Reddit changes feed format occasionally |
| **Risks** | Medium — Reddit may require OAuth in future |
| **Integration effort** | LOW-MEDIUM — RedditProvider config preset |
| **Publication frequency** | ~20-50 posts/day |

#### Reddit AI (r/OpenAI)

| Attribute | Detail |
|-----------|--------|
| **Technology** | Reddit RSS |
| **Official endpoint** | `https://www.reddit.com/r/OpenAI/.rss` |
| **Authentication** | None |
| **Format** | Atom (Reddit-flavored) |
| **Unique identifier** | `reddit-r-openai` |
| **Pagination** | Last 25 posts |
| **Limits** | Same as Reddit |
| **Recommended polling** | Every 15 minutes |
| **Stability** | MEDIUM |
| **Risks** | Same as Reddit |
| **Integration effort** | LOW — same RedditProvider |
| **Publication frequency** | ~15-40 posts/day |

### 2.2 Programming Category

#### Hacker News

| Attribute | Detail |
|-----------|--------|
| **Technology** | REST API |
| **Official endpoint** | `https://hacker-news.firebaseio.com/v0/` |
| **Authentication** | None |
| **Format** | JSON |
| **Unique identifier** | `hackernews` |
| **Pagination** | ID-based: `/topstories.json` -> array of IDs -> `/item/{id}.json` each |
| **Limits** | ~100 req/min (community policy) |
| **Recommended polling** | Every 15 minutes |
| **Stability** | HIGH — official Firebase API, stable for years |
| **Risks** | Low — maintained by Y Combinator |
| **Integration effort** | MEDIUM — custom RESTAdapter (ID-based pagination) |
| **Publication frequency** | ~30 stories/hour on front page |

#### GitHub (Trending)

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS + REST API |
| **Official endpoint** | RSS: `https://github.com/trending.atom` — API: `https://api.github.com/search/repositories` |
| **Authentication** | None for public. Token for higher rate limits. |
| **Format** | Atom (RSS) or JSON (API) |
| **Unique identifier** | `github-trending` |
| **Pagination** | RSS: full feed. API: `Link` header pagination |
| **Limits** | 60 req/hr unauthenticated, 5000 authenticated |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter for trending, RESTAdapter for search |
| **Publication frequency** | Daily trending repos |

#### Dev.to

| Attribute | Detail |
|-----------|--------|
| **Technology** | REST API |
| **Official endpoint** | `https://dev.to/api/articles` |
| **Authentication** | None (public). API key for private. |
| **Format** | JSON |
| **Unique identifier** | `devto` |
| **Pagination** | Page-based: `?page=1&per_page=30` |
| **Limits** | 30 req/30s (with key), 10 req/30s (without) |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH — well-documented stable API |
| **Risks** | Low |
| **Integration effort** | LOW — standard RESTAdapter |
| **Publication frequency** | ~50-100 articles/day |

#### Hashnode

| Attribute | Detail |
|-----------|--------|
| **Technology** | GraphQL / RSS |
| **Official endpoint** | GraphQL: `https://api.hashnode.com` — RSS: per-publication feeds |
| **Authentication** | None for public |
| **Format** | GraphQL JSON or RSS |
| **Unique identifier** | `hashnode` |
| **Pagination** | GraphQL: cursor-based. RSS: full feed. |
| **Limits** | Varies |
| **Recommended polling** | Every 30 minutes (RSS) |
| **Stability** | MEDIUM — GraphQL schema may evolve |
| **Risks** | Medium — startup, API may change |
| **Integration effort** | MEDIUM — GraphQLAdapter or RSSAdapter |
| **Publication frequency** | ~30-80 posts/day across platform |

### 2.3 Gaming Category

#### Steam (New Releases)

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://store.steampowered.com/feeds/newreleases.xml` |
| **Authentication** | None |
| **Format** | XML (RSS-like) |
| **Unique identifier** | `steam-newreleases` |
| **Pagination** | Full feed |
| **Limits** | ~200,000 calls/day (with API key) |
| **Recommended polling** | Every 1 hour |
| **Stability** | MEDIUM — Steam API has known quirks |
| **Risks** | Medium — not officially documented, community-maintained |
| **Integration effort** | LOW-MEDIUM — RSSAdapter |
| **Publication frequency** | ~5-15 new releases/day |

#### IGN

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://feeds.feedburner.com/ign/all` |
| **Authentication** | None |
| **Format** | RSS 2.0 |
| **Unique identifier** | `ign` |
| **Pagination** | Full feed (~20 items) |
| **Limits** | None (via FeedBurner) |
| **Recommended polling** | Every 30 minutes |
| **Stability** | MEDIUM — FeedBurner sunset risk |
| **Risks** | Low-Medium — Google may deprecate FeedBurner |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~20-40 articles/day |

#### GameSpot

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://www.gamespot.com/rss/reviews/` |
| **Authentication** | None |
| **Format** | RSS 2.0 |
| **Unique identifier** | `gamespot` |
| **Pagination** | Full feed |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | MEDIUM |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~10-20 articles/day |

#### Reddit Gaming (r/gaming)

| Attribute | Detail |
|-----------|--------|
| **Technology** | Reddit RSS |
| **Official endpoint** | `https://www.reddit.com/r/gaming/.rss` |
| **Authentication** | None |
| **Format** | Atom (Reddit-flavored) |
| **Unique identifier** | `reddit-r-gaming` |
| **Pagination** | Last 25 posts |
| **Limits** | Reddit rate limits |
| **Recommended polling** | Every 15 minutes |
| **Stability** | MEDIUM |
| **Risks** | Same as Reddit |
| **Integration effort** | LOW — same RedditProvider |
| **Publication frequency** | ~50-200 posts/day |

### 2.4 Technology Category

#### TechCrunch

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://techcrunch.com/feed/` |
| **Authentication** | None |
| **Format** | RSS 2.0 |
| **Unique identifier** | `techcrunch` |
| **Pagination** | Full feed (~20 items) |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~10-20 articles/day |

#### The Verge

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://www.theverge.com/rss/index.xml` |
| **Authentication** | None |
| **Format** | Atom |
| **Unique identifier** | `theverge` |
| **Pagination** | Full feed |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~15-30 articles/day |

#### Wired

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://www.wired.com/feed/rss` |
| **Authentication** | None |
| **Format** | RSS 2.0 |
| **Unique identifier** | `wired` |
| **Pagination** | Full feed |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~10-20 articles/day |

#### Ars Technica

| Attribute | Detail |
|-----------|--------|
| **Technology** | RSS |
| **Official endpoint** | `https://feeds.arstechnica.com/arstechnica/index` |
| **Authentication** | None |
| **Format** | RSS 2.0 |
| **Unique identifier** | `ars-technica` |
| **Pagination** | Full feed |
| **Limits** | None |
| **Recommended polling** | Every 30 minutes |
| **Stability** | HIGH |
| **Risks** | Low |
| **Integration effort** | LOW — RSSAdapter config preset |
| **Publication frequency** | ~10-15 articles/day |

---

## Part 3 — TechnologyAdapter vs ProviderAdapter Separation

### 3.1 The Principle

**ONE technology handles MANY providers.** A single `RSSAdapter` processes feeds from OpenAI, Anthropic, Google AI, HuggingFace, IGN, TechCrunch, The Verge, Wired, Ars Technica, and Steam — all with ZERO code differences.

A `ProviderAdapter` adds provider-specific intelligence on TOP of the technology.

### 3.2 TechnologyAdapter Responsibilities

```
TechnologyAdapter (Transport Layer)
├── HTTP transport (httpx for REST, feedparser for RSS)
├── Authentication injection (API keys, tokens)
├── Rate limiting (respect Retry-After, X-RateLimit-* headers)
├── Retries (exponential backoff)
├── Timeout management
├── Generic parsing (XML->dict, JSON->dict)
├── Conditional GET (ETag, If-Modified-Since)
├── Error classification (transient vs permanent)
└── Connection pooling
```

**Examples**:
- `RSSAdapter` — parses ANY RSS/Atom feed, handles ETag, manages polling interval
- `RESTAdapter` — handles ANY REST API, pagination, auth headers, rate limits
- `GraphQLAdapter` — handles GraphQL queries, cost calculation, introspection

### 3.3 ProviderAdapter Responsibilities

```
ProviderAdapter (Provider Logic Layer)
├── Provider-specific URL construction
├── Provider-specific field normalization
├── Provider-specific data transformation
├── Provider-specific metadata extraction
├── Provider-specific rate limit rules
├── Provider-specific error handling
├── Provider-specific deduplication strategy
├── Mapping to RawResearchData (domain contract)
└── Source quality hints (reliability, freshness)
```

**Examples**:
- `OpenAIBlogProvider` — knows OpenAI's RSS feed URL, maps fields, extracts dates
- `GitHubProvider` — knows GitHub API endpoints, handles OAuth, maps repo data
- `RedditProvider` — knows Reddit's RSS format quirks, handles subreddit parsing

### 3.4 The Rule

```
TechnologyAdapter = WHAT protocol to use
ProviderAdapter   = HOW to use it for THIS specific provider

TechnologyAdapter NEVER knows about providers.
ProviderAdapter NEVER knows about HTTP/RSS parsing.

They connect via composition, NOT inheritance.
```

### 3.5 File Structure

```
src/runtime/
├── adapters/
│   ├── technology/                    # Technology adapters (transport)
│   │   ├── base.py                   # TechnologyAdapter Protocol
│   │   ├── rss_adapter.py            # RSS/Atom implementation
│   │   ├── rest_adapter.py           # REST API implementation
│   │   └── graphql_adapter.py        # (reserved)
│   ├── providers/                     # Provider adapters (logic)
│   │   ├── base.py                   # ProviderAdapter Protocol
│   │   ├── rss/
│   │   │   ├── openai_blog.py
│   │   │   ├── anthropic.py
│   │   │   ├── google_ai.py
│   │   │   ├── huggingface.py
│   │   │   ├── ign.py
│   │   │   ├── gamespot.py
│   │   │   ├── techcrunch.py
│   │   │   ├── theverge.py
│   │   │   ├── wired.py
│   │   │   ├── ars_technica.py
│   │   │   ├── steam.py
│   │   │   └── git_feed.py
│   │   ├── rest/
│   │   │   ├── hackernews.py
│   │   │   ├── devto.py
│   │   │   ├── github_api.py
│   │   │   └── steam_api.py
│   │   └── reddit/
│   │       ├── reddit_provider.py
│   │       └── presets.py
│   └── mapping/
│       └── topic_to_feature.py       # RawResearchData -> FeatureSnapshot
```

---

## Part 4 — Source Definition

### 4.1 SourceDefinition Dataclass

```python
@dataclass(frozen=True)
class SourceDefinition:
    """Declarative definition of a knowledge source.

    Runtime discovers ALL sources automatically via SourceRegistry.
    NO hardcoded source lists. Adding a source = adding a config entry.

    Constraints:
        - All fields immutable (frozen=True)
        - id is globally unique
        - provider references a registered ProviderAdapter name
        - technology references a registered TechnologyAdapter name
        - categories are used for filtering, NOT for adapter selection
    """

    # Identity
    id: str                          # "openai-blog", "reddit-r-artificial"
    provider: str                    # ProviderAdapter name: "openai", "reddit"
    technology: str                  # TechnologyAdapter name: "rss", "rest"

    # Classification
    categories: list[str]            # ["ai", "research", "company_blog"]
    enabled: bool = True

    # Scheduling
    priority: int = 5                # 1=highest, 10=lowest
    poll_interval: timedelta = timedelta(minutes=30)

    # Authentication
    authentication: AuthConfig | None = None

    # Resilience
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    # Domain mapping
    default_tags: list[str] = field(default_factory=list)

    # Extensibility
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 4.2 Supporting Types

```python
@dataclass(frozen=True)
class AuthConfig:
    """Authentication configuration for a source."""
    method: str                          # "api_key", "bearer", "basic", "none"
    key_env_var: str | None = None       # "HN_API_KEY"
    header_name: str = "Authorization"
    token_prefix: str = "Bearer"

@dataclass(frozen=True)
class RetryPolicy:
    """Exponential backoff retry configuration."""
    max_retries: int = 3
    base_delay: timedelta = timedelta(seconds=1)
    max_delay: timedelta = timedelta(seconds=60)
    backoff_factor: float = 2.0
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    retryable_exceptions: tuple[type[Exception], ...] = (
        httpx.TimeoutException,
        httpx.ConnectError,
    )

@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int = 60
    per_window: timedelta = timedelta(minutes=1)
    respect_retry_after: bool = True
```

### 4.3 How Runtime Discovers Sources

```
SourceRegistry discovers via:
1. Config files (YAML/JSON) in src/runtime/config/sources/
2. Each file = one SourceDefinition
3. SourceRegistry.load_from_directory() scans at startup
4. NO hardcoded source lists anywhere
5. Adding a source = adding ONE config file
6. Removing a source = deleting ONE config file (or setting enabled=false)
```

---

## Part 5 — Reuse Matrix

### 5.1 The Matrix

```
TechnologyAdapter    -> ProviderAdapter          -> Sources (SourceDefinition.id)
================================================================================

RSSAdapter        -> OpenAIBlogProvider          -> openai-blog
                  -> AnthropicProvider           -> anthropic
                  -> GoogleAIProvider            -> google-ai
                  -> HuggingFaceProvider         -> huggingface
                  -> IGNProvider                 -> ign
                  -> GameSpotProvider            -> gamespot
                  -> TechCrunchProvider          -> techcrunch
                  -> TheVergeProvider            -> theverge
                  -> WiredProvider               -> wired
                  -> ArsTechnicaProvider         -> ars-technica
                  -> SteamRSSProvider            -> steam-newreleases
                  -> GitFeedProvider             -> github-trending

RESTAdapter       -> HackerNewsProvider          -> hackernews
                  -> DevtoProvider               -> devto
                  -> GitHubAPIProvider           -> github-search
                  -> SteamAPIProvider            -> steam-api

RedditProvider    -> RedditProvider (single)     -> reddit-r-artificial
  (own adapter)                                   -> reddit-r-openai
                                                  -> reddit-r-gaming
                                                  -> reddit-r-machinelearning
```

### 5.2 Summary Statistics

| Metric | Count |
|--------|-------|
| **TechnologyAdapters implemented** | 2 (RSS, REST) + 1 specialized (Reddit) |
| **ProviderAdapters implemented** | 15 (12 RSS + 3 REST) + 1 multi-source (Reddit) |
| **Total SourceDefinitions** | 19 |
| **Total adapter classes** | 18 (2 tech + 15 provider + 1 mapping) |
| **Config-only sources** | 12 (RSS pure config presets) |
| **Custom code providers** | 6 (HN, Dev.to, GitHub API, Reddit, Steam, Hashnode) |

### 5.3 The Insight

**12 out of 19 sources (63%) require ZERO custom code** — they are pure RSSAdapter config presets. The RSSAdapter does ALL the work. This is the power of the TechnologyAdapter/ProviderAdapter separation.

The remaining 7 sources need custom code because:
- HackerNews: ID-based pagination (non-standard REST)
- Dev.to: Page-based REST with specific field mapping
- GitHub API: Link-header pagination, optional OAuth
- Reddit: Custom Atom format with subreddit-specific quirks
- Steam: Undocumented API with quirks
- Hashnode: GraphQL (or RSS fallback)

---

## Part 6 — Complexity Classification

### Level 1 — Configuration Only (no custom code)

| Provider | Justification |
|----------|---------------|
| OpenAI Blog | Pure RSS. RSSAdapter handles everything. ProviderAdapter = URL constant. |
| Anthropic | Pure RSS. Same as above. |
| Google AI | Pure RSS. Same. |
| HuggingFace | Pure RSS/Atom. Same. |
| IGN | Pure RSS via FeedBurner. Same. |
| GameSpot | Pure RSS. Same. |
| TechCrunch | Pure RSS. Same. |
| The Verge | Pure Atom. Same. |
| Wired | Pure RSS. Same. |
| Ars Technica | Pure RSS. Same. |
| GitHub Trending (RSS) | Pure Atom. Same. |
| Steam (RSS) | Pure XML/RSS. Same. |

**Total**: 12 providers — just a SourceDefinition config entry.

### Level 2 — Small Specific Logic

| Provider | Justification |
|----------|---------------|
| Dev.to | RESTAdapter + small field mapping (title, body_markdown, url, tags, published_at). Page-based pagination. ~50 lines of provider logic. |
| GitHub API | RESTAdapter + Link header pagination, search query construction, repository->RawResearchData mapping. ~80 lines. |
| Steam API | RESTAdapter + undocumented endpoints, app details mapping. ~60 lines. |
| Hashnode | RSSAdapter fallback or GraphQLAdapter. Per-publication feed discovery. ~70 lines. |

**Total**: 4 providers — minimal custom logic.

### Level 3 — Complex Integration

| Provider | Justification |
|----------|---------------|
| Hacker News | RESTAdapter + unique ID-based pagination (fetch /topstories, then individual items N+1), score-based filtering, no standard page/cursor. ~120 lines. |
| Reddit (all subreddits) | Custom adapter handling Reddit's non-standard Atom format, subreddit-specific parsing, future OAuth requirement, anti-bot measures. ~150 lines shared across all subreddits. |

**Total**: 2 providers — significant custom logic, but shared across multiple sources.

### Complexity Summary

```
Level 1 (Config):        12 providers  (63%)  — 0 custom lines
Level 2 (Small Logic):    4 providers  (21%)  — ~260 custom lines total
Level 3 (Complex):         2 providers  (11%)  — ~270 custom lines total
Mapping (shared):          1 module            — ~80 lines (topic_to_feature.py)
────────────────────────────────────────────────
TOTAL:                    19 providers         — ~610 lines of custom adapter code
```

---

## Part 7 — Prioritization

### 7.1 Prioritization Criteria

| Priority | Criteria |
|----------|----------|
| **HIGH** | Free, RSS or simple API, public, high stability, high volume, zero auth, Level 1 complexity |
| **MEDIUM** | Moderate effort, limited API, some auth, Level 2 complexity |
| **LOW** | Complex auth, scraping, heavy rate limits, unstable, Level 3 complexity, future technology |

### 7.2 HIGH Priority (Phase 1 — RSS Foundation)

| # | Provider | Justification |
|---|----------|---------------|
| 1 | **Hacker News** | Free, high volume (~30 stories/hr), public API, stable for years, high community signal. Priority 1 because it's the BEST source for trending tech content. |
| 2 | **Reddit (r/artificial)** | Free, high volume (~30 posts/day), public RSS, no auth. AI-specific community with strong signal. |
| 3 | **Reddit (r/OpenAI)** | Same as above, OpenAI-specific community. |
| 4 | **Dev.to** | Free, high volume (~75 articles/day), stable REST API, developer community. Excellent for programming content. |
| 5 | **OpenAI Blog** | Free, RSS, no auth, high authority source. Low volume but extremely high quality signals. |
| 6 | **Anthropic** | Same as OpenAI Blog — high authority, RSS, zero effort. |
| 7 | **Google AI Blog** | Same — high authority, RSS, zero effort. |
| 8 | **HuggingFace** | Free, RSS, active ML community blog. High relevance for AI content. |
| 9 | **TechCrunch** | Free, RSS, no auth, high volume (~15 articles/day). Premier tech news. |
| 10 | **The Verge** | Free, RSS, no auth, high volume. General tech news. |

**Justification**: These 10 sources give us ~200+ articles/day from zero-effort RSS plus 2 high-volume REST APIs. This is the 80/20 of content acquisition.

### 7.3 MEDIUM Priority (Phase 2 — Expansion)

| # | Provider | Justification |
|---|----------|---------------|
| 11 | **Wired** | Free, RSS, no auth. Similar to Verge/TechCrunch. Easy add. |
| 12 | **Ars Technica** | Free, RSS, no auth. Deep technical analysis. |
| 13 | **GitHub Trending** | Free, RSS+API, no auth for public data. High signal for trending repos. |
| 14 | **IGN** | Free, RSS, gaming content. Medium stability (FeedBurner risk). |
| 15 | **GameSpot** | Free, RSS, gaming content. |
| 16 | **Reddit (r/gaming)** | Free, RSS, gaming community. |
| 17 | **Steam** | Free, RSS or undocumented API. Medium stability. Gaming release tracking. |
| 18 | **Hashnode** | GraphQL or RSS, developer platform. Medium complexity. |

**Justification**: These add breadth (gaming, more tech) but are lower signal-to-noise or slightly more complex.

### 7.4 LOW Priority (Phase 3 — Future)

| # | Provider | Justification |
|---|----------|---------------|
| 19 | **YouTube** (future) | Requires API key, quota limits (10,000 units/day), OAuth. High complexity. |
| 20 | **X / Twitter** (future) | API is now paid ($100/mo basic), rate-limited, unstable. |
| 21 | **Discord** (future) | Bot infrastructure required, ToS restrictions on scraping. |
| 22 | **Telegram** (future) | Bot API, channel monitoring. Infrastructure overhead. |
| 23 | **Medium** (future) | RSS exists but limited. Partner Program restrictions. |

**Justification**: These require new TechnologyAdapters (Webhook, API with OAuth), infrastructure, or are paywalled. Architecturally compatible but NOT for initial implementation.

---

## Part 8 — Future Scalability Validation

### 8.1 Validation Criteria

For each future provider, verify: Can it be integrated WITHOUT modifying any existing TechnologyAdapter, ProviderAdapter, or SourceDefinition infrastructure?

### 8.2 Future Provider Validation

| Future Provider | Technology | Adapter Needed | Modify Existing? | Validated |
|-----------------|------------|----------------|-------------------|-----------|
| **YouTube** | REST API | RESTAdapter (reuse) + YouTubeProvider (new) | No — new ProviderAdapter only | ✅ |
| **X / Twitter** | REST API | RESTAdapter (reuse) + TwitterProvider (new) | No | ✅ |
| **Discord** | Webhook/Polling | WebhookAdapter (new Tech) + DiscordProvider (new) | No — new TechnologyAdapter | ✅ |
| **Telegram** | Bot API | RESTAdapter (reuse) + TelegramProvider (new) | No | ✅ |
| **Medium** | RSS | RSSAdapter (reuse) + MediumProvider (new config) | No | ✅ |
| **Custom RSS** | RSS | RSSAdapter (reuse) + new SourceDefinition | No | ✅ |
| **Scientific papers** | XML Feed | XMLFeedAdapter (new Tech) + ArxivProvider (new) | No — new TechnologyAdapter | ✅ |
| **Own blogs** | RSS | RSSAdapter (reuse) + new SourceDefinition | No | ✅ |
| **Technical docs** | REST/Scrape | RESTAdapter or HTMLScrapingAdapter + new Provider | No | ✅ |
| **Podcasts** | RSS | RSSAdapter (reuse) + new SourceDefinition | No | ✅ |

### 8.3 Scalability Guarantees

1. **Adding a new RSS source**: Create ONE SourceDefinition config file. Zero code.
2. **Adding a new REST source**: Create ONE ProviderAdapter class (~50-120 lines) + ONE SourceDefinition.
3. **Adding a new technology**: Create ONE TechnologyAdapter class + ONE ProviderAdapter + ONE SourceDefinition.
4. **No existing code modified**: Open/Closed Principle enforced.
5. **SourceRegistry auto-discovers**: New sources appear automatically at startup.

### 8.4 Architecture Capacity

| Metric | Current | Capacity |
|--------|---------|----------|
| TechnologyAdapters | 2 implemented | Unlimited (plugin model) |
| ProviderAdapters | 16 | Unlimited |
| SourceDefinitions | 19 | Unlimited (config-driven) |
| Total daily articles | ~200+ | Scales linearly with sources |

---

## Part 9 — Risks & Mitigations

### 9.1 Risk Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **RSS feed URL changes** | Medium | Medium | SourceDefinition.metadata holds fallback URLs. Health checks detect 404s. ProviderAdapter can be updated independently. |
| **API breaking changes (v1->v2)** | High | Low | Pin API versions in SourceDefinition.metadata. ProviderAdapter isolates change. Only ONE adapter affected. |
| **Authentication changes (free->paid)** | High | Medium (Reddit, X) | SourceDefinition.enabled = false disables instantly. RSSAdapter fallback where available. No code changes needed. |
| **Rate limiting / IP blocking** | Medium | Medium | Exponential backoff (RetryPolicy). Configurable poll intervals. Respect Retry-After headers. Circuit breaker pattern. |
| **HTML structure changes (scraping)** | High | High (if scraping) | ADR-002: APIs before scraping. ADR-003: HTML only as last resort. Avoid scraping entirely for Phase 1-2. |
| **Provider downtime** | Low | Medium | SourceAdapter.available property. Graceful degradation — other sources continue. Health monitoring. |
| **Feed format changes (Reddit Atom)** | Medium | Medium | RedditProviderAdapter encapsulates parsing. Change only affects ONE adapter class. |
| **FeedBurner sunset (IGN)** | Medium | Low | IGN has direct RSS fallback. SourceDefinition updated to point to direct feed. |
| **Maintenance burden (N adapters)** | Medium | Low | 63% of sources are config-only. Only 2 complex adapters. TechnologyAdapter reuse minimizes code. |
| **Legal/scraping risks** | High | Low (if no scraping) | ADR-002: No scraping. All sources are public APIs/RSS. Terms of service respected. |

### 9.2 Circuit Breaker Design

```python
@dataclass
class CircuitBreakerState:
    """Per-source circuit breaker for graceful degradation."""
    failure_count: int = 0
    last_failure: datetime | None = None
    state: str = "closed"  # "closed" | "open" | "half_open"
    
    # Config
    failure_threshold: int = 5
    recovery_timeout: timedelta = timedelta(minutes=30)
    
    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure = datetime.now(timezone.utc)
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "closed"
    
    def should_attempt(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open" and self.last_failure:
            if datetime.now(timezone.utc) - self.last_failure > self.recovery_timeout:
                self.state = "half_open"
                return True
            return False
        return True  # half_open: allow one attempt
```

### 9.3 Health Check Design

```python
class SourceHealthCheck:
    """Periodic health check for all registered sources."""
    
    async def check_all(self) -> dict[str, SourceHealth]:
        """Check health of all sources. Returns status map."""
        ...
    
    async def check_source(self, source_id: str) -> SourceHealth:
        """Single source health check — lightweight GET."""
        ...
    
    def get_unhealthy_sources(self) -> list[str]:
        """Sources that have been failing for > 1 hour."""
        ...
```

---

## Part 10 — ADRs

### ADR-001: RSS as Preferred Technology

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | RSS/Atom is the PREFERRED technology for content acquisition. All providers that offer RSS feeds will use RSSAdapter as primary. |
| **Rationale** | RSS is the lowest-effort, highest-stability technology. 12 of 19 providers (63%) are pure RSS config presets. Zero authentication. Standardized parsing. Universal adoption. The RSSAdapter handles ALL RSS feeds with a single class. |
| **Alternatives considered** | REST APIs for all providers — REJECTED: more complex, requires per-API auth/pagination logic. GraphQL — REJECTED: overkill for content feeds, rare adoption. |
| **Tradeoffs** | RSS gives less filtering/pagination control than REST APIs. Acceptable: we get ALL content and filter client-side. |

### ADR-002: APIs Before Scraping

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | Always prefer official APIs (REST, GraphQL) over HTML scraping. Scraping is ONLY allowed when no API or RSS exists. |
| **Rationale** | APIs provide structured data, contracts, rate limit headers, and legal clarity. Scraping is brittle, legally risky, and high-maintenance. |
| **Alternatives considered** | Scraping as primary — REJECTED: maintenance nightmare, no contracts, legal risk. |
| **Tradeoffs** | Some data may be unavailable via API. Acceptable: we prioritize data quality and system stability over completeness. |

### ADR-003: HTML Only as Last Resort

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | HTML scraping (`HTMLScrapingAdapter`) is reserved exclusively for providers where NO API, RSS, or other structured access method exists. |
| **Rationale** | HTML scraping has the highest maintenance cost, lowest stability, and highest legal risk. It violates the principle of stable contracts. |
| **Alternatives considered** | None — this is a constraint, not a choice. |
| **Tradeoffs** | Some valuable sources may be excluded if they only offer HTML. Acceptable: system stability > data completeness. |

### ADR-004: Configurable Polling

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | Each SourceDefinition specifies its own `poll_interval`. Runtime respects these intervals. No global default overrides provider-specific needs. |
| **Rationale** | Different sources have different update frequencies. HN changes every minute; company blogs change weekly. Polling interval should match source velocity. |
| **Alternatives considered** | Fixed global interval (e.g., 30 min for all) — REJECTED: wastes bandwidth on slow sources, misses fast sources. Adaptive polling — DEFERRED: adds complexity, YAGNI for Phase 1. |
| **Tradeoffs** | More complex scheduler (per-source intervals). Acceptable: APScheduler handles this natively. |

### ADR-005: Exponential Retries

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | All TechnologyAdapters implement exponential backoff retries. Default: 3 retries, base delay 1s, backoff factor 2x, max delay 60s. |
| **Rationale** | Network failures are transient. Exponential backoff prevents thundering herd on recovery. Configurable per-source via RetryPolicy. |
| **Alternatives considered** | Fixed delay retries — REJECTED: can cause cascading failures. No retries — REJECTED: too fragile. Immediate retries — REJECTED: can overwhelm recovering servers. |
| **Tradeoffs** | Slower recovery on transient failures. Acceptable: correctness > speed for background polling. |

### ADR-006: Adapter Versioning

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | ProviderAdapters are versioned via `provider_version` in their class. SourceDefinition includes `adapter_version` field. Breaking provider changes require a new adapter version, not modification of existing. |
| **Rationale** | APIs evolve. A ProviderAdapter for Dev.to API v1 should coexist with v2 until migration is complete. |
| **Alternatives considered** | Modify existing adapter — REJECTED: breaks running sources during migration. |
| **Tradeoffs** | Temporary code duplication during migration windows. Acceptable: safety > elegance. |

### ADR-007: TechnologyAdapter vs ProviderAdapter Separation

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | Strict two-layer architecture: TechnologyAdapters handle transport (HTTP, RSS parsing, auth, retries). ProviderAdapters handle provider-specific logic (field mapping, URL construction, metadata). NEVER mix responsibilities. |
| **Rationale** | Single Responsibility Principle. A change in HTTP transport (httpx version upgrade) must NOT affect provider logic. A change in provider API schema must NOT affect transport code. 63% of sources are pure config presets BECAUSE of this separation. |
| **Alternatives considered** | Single adapter per provider — REJECTED: massive code duplication, violates DRY. Inheritance hierarchy — REJECTED: fragile base class problem, tight coupling. |
| **Tradeoffs** | Slightly more indirection (two classes instead of one). Acceptable: the reuse payoff is enormous (1 RSSAdapter handles 12 providers). |

### ADR-008: Declarative Source Registry

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | Sources are defined declaratively via SourceDefinition dataclasses. SourceRegistry auto-discovers and registers all enabled sources at startup. NO hardcoded source lists in code. |
| **Rationale** | Adding a source should be a config change, NOT a code change. This follows the Open/Closed Principle and makes the system extensible without code deployments. |
| **Alternatives considered** | Hardcoded source lists — REJECTED: violates OCP, requires code changes for new sources. Plugin system — DEFERRED: too complex for Phase 1, config files are sufficient. |
| **Tradeoffs** | Less runtime flexibility (sources defined at startup). Acceptable: runtime source addition is YAGNI. |

### ADR-009: Provider Grouping by Technology (Not Category)

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Decision** | ProviderAdapters are organized by TECHNOLOGY (rss/, rest/, reddit/) NOT by content category (ai/, programming/, gaming/). A provider's technology determines its adapter class; its category is metadata only. |
| **Rationale** | Technology determines CODE (how to fetch). Category determines FILTERING (what to show). Mixing them creates artificial dependencies (why should an AI blog's adapter know about gaming?). |
| **Alternatives considered** | Group by category — REJECTED: OpenAI Blog and TechCrunch would be in different groups despite using identical RSS technology. Creates duplication. |
| **Tradeoffs** | Category filtering is done at the SourceDefinition level, not adapter level. Acceptable: categories are metadata, not behavior. |

---

## Part 11 — Implementation Roadmap

### Phase 1: RSS Technology Foundation (Week 1-2)

**Goal**: 1 RSSAdapter + 10 RSS providers + 1 Reddit adapter + 4 Reddit sources

```
Files to create:
src/runtime/adapters/technology/base.py          # TechnologyAdapter Protocol
src/runtime/adapters/technology/rss_adapter.py   # RSSAdapter (THE reusable class)
src/runtime/adapters/providers/base.py           # ProviderAdapter Protocol
src/runtime/adapters/providers/rss/              # 10 config preset files
    openai_blog.py
    anthropic.py
    google_ai.py
    huggingface.py
    ign.py
    gamespot.py
    techcrunch.py
    theverge.py
    wired.py
    ars_technica.py
src/runtime/adapters/providers/reddit/
    reddit_provider.py                           # Shared Reddit logic
    presets.py                                   # Subreddit configurations
src/runtime/adapters/mapping/topic_to_feature.py # RawResearchData -> FeatureSnapshot
src/runtime/adapters/source_registry.py          # SourceRegistry
src/runtime/contracts/source_definition.py       # SourceDefinition + supporting types
src/runtime/config/sources/                      # 14 YAML/JSON config files
    openai-blog.yaml
    anthropic.yaml
    google-ai.yaml
    huggingface.yaml
    ign.yaml
    gamespot.yaml
    techcrunch.yaml
    theverge.yaml
    wired.yaml
    ars-technica.yaml
    reddit-r-artificial.yaml
    reddit-r-openai.yaml
    reddit-r-gaming.yaml
    github-trending.yaml
```

**Total**: ~25 files. 1 TechnologyAdapter + 12 ProviderAdapters (10 RSS presets + 2 complex) + 1 mapping + 1 registry + 14 configs.

### Phase 2: REST API Technology (Week 3-4)

**Goal**: 1 RESTAdapter + 3 REST providers

```
Additional files:
src/runtime/adapters/technology/rest_adapter.py  # RESTAdapter
src/runtime/adapters/providers/rest/
    hackernews.py                                # Level 3 — ID-based pagination
    devto.py                                     # Level 2 — page-based
    github_api.py                                # Level 2 — Link header pagination
src/runtime/config/sources/
    hackernews.yaml
    devto.yaml
    github-search.yaml
```

**Total**: ~5 files. 1 TechnologyAdapter + 3 ProviderAdapters + 3 configs.

### Phase 3: Gaming Expansion (Week 5)

**Goal**: Add remaining gaming sources (Steam, Hashnode)

```
Additional files:
src/runtime/adapters/providers/rss/steam.py     # Steam RSS preset
src/runtime/adapters/providers/rest/steam_api.py # Steam API (optional)
src/runtime/adapters/providers/rest/hashnode.py  # or RSS fallback
src/runtime/config/sources/
    steam-newreleases.yaml
    hashnode.yaml
```

**Total**: ~4 files.

### Phase 4: Polish & Monitoring (Week 6)

**Goal**: Health checks, circuit breaker, metrics

```
Additional files:
src/runtime/adapters/health.py                   # SourceHealthCheck
src/runtime/adapters/circuit_breaker.py          # CircuitBreakerState
src/runtime/api/sources.py                       # Source status API endpoints
```

### Roadmap Summary

| Phase | TechnologyAdapter | ProviderAdapters | SourceDefinitions | Total Files |
|-------|-------------------|------------------|-------------------|-------------|
| Phase 1 | 1 (RSS) + Reddit | 12 | 14 | ~25 |
| Phase 2 | 1 (REST) | 3 | 3 | ~5 |
| Phase 3 | — | 2 | 2 | ~4 |
| Phase 4 | — | — | — | ~3 |
| **Total** | **2+Reddit** | **17** | **19** | **~37** |

### Key Insight

**Phase 1 alone delivers 74% of all sources (14/19) with ONE TechnologyAdapter.** This is the ROI of the RSS-first approach. The remaining 25% require one additional TechnologyAdapter (REST) in Phase 2.

The architecture is designed so that Phase 1 and Phase 2 can be developed IN PARALLEL by different developers, as they share NO code between TechnologyAdapters. The ProviderAdapters and SourceRegistry are the ONLY shared components.

---

## Appendix A — Integration with Existing Architecture

### How This Fits EPIC 8.0 Design

```
EPIC 8.0 Design (frozen):
├── src/runtime/adapters/source_adapter.py    # SourceAdapter Protocol (existing)
├── src/runtime/adapters/source_registry.py   # SourceRegistry (existing)
├── src/runtime/adapters/topic_to_feature.py  # Mapping (existing)
└── src/runtime/adapters/hackernews.py        # Example adapter (existing)

EPIC 8.1 Enhancement (this design):
├── src/runtime/adapters/technology/          # NEW: Technology layer
│   ├── base.py                              # TechnologyAdapter Protocol
│   ├── rss_adapter.py                       # RSS/Atom implementation
│   └── rest_adapter.py                      # REST API implementation
├── src/runtime/adapters/providers/           # NEW: Provider layer
│   ├── base.py                              # ProviderAdapter Protocol
│   ├── rss/                                 # 12 RSS provider presets
│   ├── rest/                                # 3 REST provider adapters
│   └── reddit/                              # Reddit multi-source adapter
├── src/runtime/contracts/                    # NEW: Typed contracts
│   └── source_definition.py                 # SourceDefinition + types
└── src/runtime/config/sources/               # NEW: Declarative configs
    └── 14 YAML files                         # One per source
```

**Key**: EPIC 8.1 ADDS the Technology/Provider separation ON TOP of EPIC 8.0's SourceAdapter Protocol. The existing `SourceAdapter` Protocol becomes the output of the ProviderAdapter chain. No modification to existing files.

### Data Flow (Updated)

```
SourceDefinition (config)
    |
    v
ProviderAdapter.resolve() -> constructs URL, sets params
    |
    v
TechnologyAdapter.fetch() -> HTTP transport, RSS parsing, auth, retries
    |
    v
RawResearchData (normalized output)
    |
    v
TopicToFeatureAdapter -> FeatureSnapshot (Learning BC compatible)
    |
    v
PipelineOrchestrator -> IngestStep -> RecommendStep -> ...
```

---

## Appendix B — Glossary

| Term | Definition |
|------|------------|
| **TechnologyAdapter** | Handles a specific protocol (RSS, REST, GraphQL). Transport layer. |
| **ProviderAdapter** | Handles a specific provider (OpenAI, GitHub, Reddit). Logic layer. |
| **SourceDefinition** | Declarative config for a knowledge source. Identity + scheduling + auth. |
| **SourceRegistry** | Auto-discovers and manages all SourceDefinitions and their adapters. |
| **RawResearchData** | Normalized DTO returned by any adapter. Domain-agnostic. |
| **FeatureSnapshot** | Learning BC value object. Mapping target from RawResearchData. |

---

*This document is the OFFICIAL REFERENCE for all present and future external knowledge provider integrations in AI_Shorts_System.*
