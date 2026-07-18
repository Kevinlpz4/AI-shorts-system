# Learning BC — Metrics Catalog

> **Date**: 2026-07-18
> **BC**: Learning Intelligence
> **Version**: 1.0 (Sprint 7.8)
> **Total Metrics**: 21 (7 counters, 7 gauges, 7 histograms)

---

## 1. Overview

This catalog defines ALL metrics to be emitted by the Learning Intelligence BC. Each metric is designed for a specific operational question and maps to concrete instrumentation points in the codebase.

### Naming Convention

- Prefix: `learning_`
- Format: `learning_<subject>_<qualifier>`
- Units: suffix `_ms` for milliseconds, `_total` for counters
- Labels: snake_case

### Metric Types

| Type | Use When | Example |
|------|----------|---------|
| **Counter** | Monotonically increasing value (count of events) | Total predictions made |
| **Gauge** | Value that can go up and down | Current active signals count |
| **Histogram** | Distribution of values (latency, size) | Request duration |

---

## 2. Counters (7)

### 2.1 `learning_predictions_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `source` (article source), `result` (approved/rejected) |
| **Description** | Total number of predictions made |
| **Instrumentation Point** | `application/services/prediction_service.py` → `predict()` method |
| **When to Increment** | After prediction result is determined |
| **Dashboard Panel** | Prediction Activity — Predictions/min |
| **Alert** | PredictionFailures (if error counter grows faster) |

```python
learning_predictions_total.labels(source="techcrunch", result="approved").inc()
```

### 2.2 `learning_recommendations_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `source` (article source), `action` (type of recommendation) |
| **Description** | Total recommendations generated |
| **Instrumentation Point** | `application/services/recommendation_service.py` → `recommend()` method |
| **When to Increment** | After recommendation is generated |
| **Dashboard Panel** | Recommendation Distribution |

```python
learning_recommendations_total.labels(source="techcrunch", action="approve").inc()
```

### 2.3 `learning_feedback_received_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `decision` (approved/rejected/overridden) |
| **Description** | Total feedback records received |
| **Instrumentation Point** | `application/services/decision_service.py` → `record_feedback()` method |
| **When to Increment** | After feedback is persisted |
| **Dashboard Panel** | Feedback Rate — Feedback/hour |

```python
learning_feedback_received_total.labels(decision="approved").inc()
```

### 2.4 `learning_signals_created_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `signal_type` (keyword/source_quality/temporal/feedback/coherence), `dimension` (signal dimension) |
| **Description** | Total learning signals created |
| **Instrumentation Point** | `application/services/signal_service.py` → signal creation methods |
| **When to Increment** | After signal is created and persisted |
| **Dashboard Panel** | Active Signals — signals by type |

```python
learning_signals_created_total.labels(signal_type="keyword", dimension="technology").inc()
```

### 2.5 `learning_datasets_exported_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `format` (jsonl/csv/parquet) |
| **Description** | Total dataset exports initiated |
| **Instrumentation Point** | `application/services/dataset_service.py` → `export_dataset()` method |
| **When to Increment** | After export completes (success or failure) |
| **Dashboard Panel** | Dataset Growth |

```python
learning_datasets_exported_total.labels(format="jsonl").inc()
```

### 2.6 `learning_errors_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `endpoint` (API endpoint path), `error_code` (DomainException type), `status` (HTTP status code) |
| **Description** | Total errors across all endpoints |
| **Instrumentation Point** | Exception handler in `presentation/app.py` or middleware |
| **When to Increment** | On any unhandled exception or domain error |
| **Dashboard Panel** | Learning Health — Error rate |
| **Alert** | PredictionFailures, RecommendationFailures |

```python
learning_errors_total.labels(endpoint="/api/v1/learning/predict", error_code="InvalidConfidence", status=422).inc()
```

### 2.7 `learning_api_requests_total`

| Property | Value |
|----------|-------|
| **Type** | Counter |
| **Labels** | `method` (GET/POST), `endpoint` (API path), `status` (HTTP status code) |
| **Description** | Total API requests received |
| **Instrumentation Point** | `presentation/middleware/timing.py` or dedicated metrics middleware |
| **When to Increment** | After each request completes |
| **Dashboard Panel** | Learning Health — Requests/min |

```python
learning_api_requests_total.labels(method="POST", endpoint="/predict", status=200).inc()
```

---

## 3. Gauges (7)

### 3.1 `learning_active_signals`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of active (non-decayed) learning signals |
| **Instrumentation Point** | `application/services/signal_service.py` → `get_active_signals()` |
| **When to Update** | After signal creation, decay, or removal |
| **Dashboard Panel** | Active Signals — current count |

```python
learning_active_signals.set(count)
```

### 3.2 `learning_source_profiles`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of source quality profiles tracked |
| **Instrumentation Point** | `application/services/scoring_service.py` or signal handlers |
| **When to Update** | After profile creation or removal |
| **Dashboard Panel** | Top Sources — profile count |

```python
learning_source_profiles.set(count)
```

### 3.3 `learning_knowledge_snapshots`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of knowledge snapshots in timeline |
| **Instrumentation Point** | `integration/observability/knowledge_timeline.py` |
| **When to Update** | After snapshot creation |
| **Dashboard Panel** | Timeline Growth — snapshot count |

```python
learning_knowledge_snapshots.set(count)
```

### 3.4 `learning_datasets_count`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of datasets available |
| **Instrumentation Point** | `application/services/dataset_service.py` |
| **When to Update** | After dataset creation or deletion |
| **Dashboard Panel** | Dataset Growth — dataset count |

```python
learning_datasets_count.set(count)
```

### 3.5 `learning_artifacts_count`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of knowledge artifacts |
| **Instrumentation Point** | `application/services/` (artifact-related operations) |
| **When to Update** | After artifact creation or removal |
| **Dashboard Panel** | Knowledge Growth — artifact count |

```python
learning_artifacts_count.set(count)
```

### 3.6 `learning_training_snapshots`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of training snapshots (model versions) |
| **Instrumentation Point** | `application/services/` (model update operations) |
| **When to Update** | After model snapshot creation |
| **Dashboard Panel** | Training History — snapshot count |

```python
learning_training_snapshots.set(count)
```

### 3.7 `learning_feature_store_size`

| Property | Value |
|----------|-------|
| **Type** | Gauge |
| **Labels** | None |
| **Description** | Current number of entries in the feature store |
| **Instrumentation Point** | `infrastructure/feature_store.py` |
| **When to Update** | After feature entry creation or eviction |
| **Dashboard Panel** | Feature Store Growth — entry count |

```python
learning_feature_store_size.set(count)
```

---

## 4. Histograms (7)

### 4.1 `learning_prediction_latency_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | `source` (optional, for per-source analysis) |
| **Description** | Latency of prediction requests in milliseconds |
| **Buckets** | [10, 25, 50, 100, 200, 500, 1000] |
| **Instrumentation Point** | `presentation/routers/prediction.py` → `predict()` |
| **When to Observe** | After prediction completes |
| **Dashboard Panel** | Latency — p50/p95/p99 |

```python
learning_prediction_latency_ms.labels(source="techcrunch").observe(elapsed_ms)
```

### 4.2 `learning_recommendation_latency_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | None |
| **Description** | Latency of recommendation requests in milliseconds |
| **Buckets** | [10, 25, 50, 100, 200, 500, 1000] |
| **Instrumentation Point** | `presentation/routers/recommendation.py` → `recommend()` |
| **When to Observe** | After recommendation completes |
| **Dashboard Panel** | Latency — p50/p95/p99 |

### 4.3 `learning_feedback_latency_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | None |
| **Description** | Latency of feedback recording in milliseconds |
| **Buckets** | [5, 10, 25, 50, 100, 200, 500] |
| **Instrumentation Point** | `presentation/routers/feedback.py` → `record_feedback()` |
| **When to Observe** | After feedback recording completes |
| **Dashboard Panel** | Latency — p50/p95/p99 |

### 4.4 `learning_dataset_export_latency_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | `format` (jsonl/csv/parquet) |
| **Description** | Latency of dataset export operations in milliseconds |
| **Buckets** | [100, 500, 1000, 5000, 10000, 30000, 60000] |
| **Instrumentation Point** | `presentation/routers/datasets.py` → `export_dataset()` |
| **When to Observe** | After export completes |
| **Dashboard Panel** | Latency — p50/p95/p99 |

### 4.5 `learning_timeline_query_latency_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | None |
| **Description** | Latency of timeline queries in milliseconds |
| **Buckets** | [10, 25, 50, 100, 200, 500, 1000] |
| **Instrumentation Point** | `presentation/routers/timeline.py` → timeline query endpoint |
| **When to Observe** | After query completes |
| **Dashboard Panel** | Latency — p50/p95/p99 |

### 4.6 `learning_analytics_latency_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | None |
| **Description** | Latency of analytics queries in milliseconds |
| **Buckets** | [10, 25, 50, 100, 200, 500, 1000] |
| **Instrumentation Point** | `presentation/routers/analytics.py` → analytics endpoint |
| **When to Observe** | After analytics query completes |
| **Dashboard Panel** | Latency — p50/p95/p99 |

### 4.7 `learning_api_request_duration_ms`

| Property | Value |
|----------|-------|
| **Type** | Histogram |
| **Labels** | `method` (GET/POST), `endpoint` (API path) |
| **Description** | Overall API request duration in milliseconds |
| **Buckets** | [5, 10, 25, 50, 100, 200, 500, 1000, 2000] |
| **Instrumentation Point** | `presentation/middleware/timing.py` (existing TimingMiddleware) |
| **When to Observe** | After request completes (where X-Response-Time is calculated) |
| **Dashboard Panel** | Latency — p50/p95/p99 |

```python
learning_api_request_duration_ms.labels(method="POST", endpoint="/predict").observe(elapsed_ms)
```

---

## 5. Instrumentation Summary

### 5.1 Files to Modify

| File | Add | Metrics Affected |
|------|-----|-----------------|
| `presentation/middleware/timing.py` | Prometheus histogram observation | `learning_api_request_duration_ms`, `learning_api_requests_total` |
| `presentation/middleware/request_id.py` | structlog context binding | All metrics (context) |
| `presentation/routers/prediction.py` | Counter + histogram | `learning_predictions_total`, `learning_prediction_latency_ms` |
| `presentation/routers/recommendation.py` | Counter + histogram | `learning_recommendations_total`, `learning_recommendation_latency_ms` |
| `presentation/routers/feedback.py` | Counter + histogram | `learning_feedback_received_total`, `learning_feedback_latency_ms` |
| `presentation/routers/datasets.py` | Counter + histogram + gauge | `learning_datasets_exported_total`, `learning_dataset_export_latency_ms`, `learning_datasets_count` |
| `presentation/routers/signals.py` | Gauge | `learning_active_signals` |
| `presentation/routers/knowledge.py` | Gauge | `learning_artifacts_count` |
| `presentation/routers/timeline.py` | Gauge + histogram | `learning_knowledge_snapshots`, `learning_timeline_query_latency_ms` |
| `presentation/routers/analytics.py` | Histogram | `learning_analytics_latency_ms` |
| `application/services/signal_service.py` | Counter + gauge | `learning_signals_created_total`, `learning_active_signals` |
| `application/services/scoring_service.py` | Gauge | `learning_source_profiles` |
| `infrastructure/feature_store.py` | Gauge | `learning_feature_store_size` |
| `infrastructure/knowledge_storage.py` | Gauge | `learning_knowledge_snapshots`, `learning_training_snapshots` |
| Exception handler (new or existing) | Counter | `learning_errors_total` |

### 5.2 New Files to Create

| File | Purpose |
|------|---------|
| `infrastructure/metrics.py` | All metric definitions (Counter, Gauge, Histogram) |
| `infrastructure/logging.py` | structlog configuration |
| `infrastructure/tracing.py` | OpenTelemetry setup |
| `presentation/middleware/metrics.py` | Prometheus metrics middleware |
| `presentation/middleware/logging.py` | Request/response logging middleware |
| `presentation/routers/metrics.py` | `/metrics` endpoint for Prometheus |

---

## 6. Grafana Dashboard Integration

All metrics in this catalog are designed to be consumed by Grafana dashboards. See `learning-dashboard-design.md` for the complete dashboard layout.

### Key PromQL Queries

```promql
# Predictions per minute
rate(learning_predictions_total[1m]) * 60

# Error rate
rate(learning_errors_total[1m]) / rate(learning_api_requests_total[1m]) * 100

# p95 latency
histogram_quantile(0.95, rate(learning_api_request_duration_ms_bucket[5m]))

# Active signals
learning_active_signals

# Feedback ratio
learning_feedback_received_total{decision="approved"} / learning_feedback_received_total{decision="rejected"}
```

---

## 7. Prometheus Scrape Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'learning-intelligence'
    scrape_interval: 15s
    static_configs:
      - targets: ['learning-api:8000']
    metrics_path: '/metrics'
```

---

*Generated: 2026-07-18 | Sprint 7.8 | Learning BC v1.0*
