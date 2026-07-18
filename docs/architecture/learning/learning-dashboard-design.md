# Learning BC — Dashboard Design

> **Date**: 2026-07-18
> **BC**: Learning Intelligence
> **Version**: 1.0 (Sprint 7.8)
> **Target**: Grafana (text-based layout, not JSON)

---

## 1. Dashboard Overview

**Dashboard Name**: Learning Intelligence — Operational Overview
**Refresh Rate**: 15s
**Time Range**: Last 24h (default), configurable
**Panels**: 14 panels across 4 rows

---

## 2. Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEARNING INTELLIGENCE — OPERATIONAL OVERVIEW              │
│                    ┌──────────────────────────────────────┐                 │
│                    │  Time Range: [Last 24h ▼]  Auto-refresh: [15s]       │
│                    └──────────────────────────────────────┘                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ ROW 1: HEALTH                                                               │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│ │ PANEL 1:        │ │ PANEL 2:        │ │ PANEL 3:        │               │
│ │ Service Status  │ │ Uptime          │ │ Error Rate      │               │
│ │                 │ │                 │ │                 │               │
│ │   ● HEALTHY     │ │  99.97%         │ │    0.12%        │               │
│ │                 │ │  (7d average)   │ │  (last 5min)    │               │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘               │
├─────────────────────────────────────────────────────────────────────────────┤
│ ROW 2: ACTIVITY                                                             │
│ ┌─────────────────────────────┐ ┌─────────────────────────────┐           │
│ │ PANEL 4:                    │ │ PANEL 5:                    │           │
│ │ Prediction Activity         │ │ Recommendation Distribution │           │
│ │                             │ │                             │           │
│ │  Predictions/min: 12.3      │ │  ┌──────────────────────┐  │           │
│ │  Approval rate: 67.2%       │ │  │ approve    ████████  │  │           │
│ │  ┌──────────────────────┐   │ │  │ review     ████      │  │           │
│ │  │ ░░░░░░░░░░░░░░░░░░░░ │   │ │  │ reject     ██        │  │           │
│ │  │ approved  ████████   │   │ │  └──────────────────────┘  │           │
│ │  │ rejected  ███        │   │ │                             │           │
│ │  └──────────────────────┘   │ │  Total: 847 recommendations │           │
│ │  Confidence distribution:   │ │                             │           │
│ │  [histogram visualization]  │ │                             │           │
│ └─────────────────────────────┘ └─────────────────────────────┘           │
├─────────────────────────────────────────────────────────────────────────────┤
│ ROW 3: LEARNING GROWTH                                                      │
│ ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐  │
│ │ PANEL 6:              │ │ PANEL 7:          │ │ PANEL 8:              │  │
│ │ Feedback Rate         │ │ Approval Rate     │ │ Top Sources           │  │
│ │                       │ │                   │ │                       │  │
│ │  Feedback/hour: 45    │ │  Overall: 67.2%   │ │  1. techcrunch  [89%] │  │
│ │  ┌────────────────┐   │ │  ┌──────────────┐ │ │  2. arstechnica [76%] │  │
│ │  │ approved ████  │   │ │  │ ╱╲    ╱╲    │ │ │  3. theverge    [71%] │  │
│ │  │ rejected ██    │   │ │  │╱  ╲╱  ╲╱  │ │ │  4. hackernews  [65%] │  │
│ │  │ overridden █  │   │ │  └──────────────┘ │ │  5. wired        [58%] │  │
│ │  └────────────────┘   │ │  Per-source:      │ │                       │  │
│ │  Approve/reject: 3:1  │ │  techcrunch: 89%  │ │  Total profiles: 12   │  │
│ │                       │ │  arstechnica: 76%  │ │                       │  │
│ └───────────────────────┘ └───────────────────┘ └───────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ROW 4: KNOWLEDGE & DATA                                                     │
│ ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐  │
│ │ PANEL 9:              │ │ PANEL 10:         │ │ PANEL 11:             │  │
│ │ Timeline Growth       │ │ Dataset Growth    │ │ Knowledge Growth      │  │
│ │                       │ │                   │ │                       │  │
│ │  Snapshots: 342       │ │  Datasets: 8      │ │  Artifacts: 156       │  │
│ │  ┌────────────────┐   │ │  ┌──────────────┐ │ │  ┌────────────────┐  │  │
│ │  │      ╱──────   │   │ │  │    ╱──       │ │ │  │    ╱───────   │  │  │
│ │  │   ╱──          │   │ │  │ ╱──          │ │ │  │ ╱──           │  │  │
│ │  │ ╱──            │   │ │  │╱──           │ │ │  │╱──            │  │  │
│ │  └────────────────┘   │ │  └──────────────┘ │ │  └────────────────┘  │  │
│ └───────────────────────┘ └───────────────────┘ └───────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│ ROW 5: FEATURES & TRAINING                                                  │
│ ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐  │
│ │ PANEL 12:             │ │ PANEL 13:         │ │ PANEL 14:             │  │
│ │ Feature Store Growth  │ │ Training History  │ │ Latency               │  │
│ │                       │ │                   │ │                       │  │
│ │  Entries: 2,847       │ │  Versions: 12     │ │  p50: 12ms            │  │
│ │  ┌────────────────┐   │ │  ┌──────────────┐ │ │  p95: 45ms            │  │
│ │  │      ╱──────   │   │ │  │ v12  ●       │ │ │  p99: 120ms           │  │
│ │  │   ╱──          │   │ │  │ v11  ●       │ │ │  ┌────────────────┐  │  │
│ │  │ ╱──            │   │ │  │ v10  ●       │ │ │  │   ╱╲  ╱╲      │  │  │
│ │  └────────────────┘   │ │  │ ...          │ │ │  │  ╱  ╲╱  ╲     │  │  │
│ │  Hit rate: 87.3%      │ │  └──────────────┘ │ │  │ ╱          ╲   │  │  │
│ │  Evictions: 23        │ │  Weight evolution: │ │  └────────────────┘  │  │
│ └───────────────────────┘ │  [line chart]     │ │  By endpoint:         │  │
│                           └───────────────────┘ │  /predict: p95=35ms  │  │
│                                                 │  /feedback: p95=15ms │  │
│                                                 └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Panel Specifications

### Panel 1: Service Status

| Property | Value |
|----------|-------|
| **Type** | Stat Panel |
| **Metric** | Health check response |
| **Query** | `learning_health_status` (derived from /health endpoint) |
| **States** | healthy (green), degraded (yellow), unhealthy (red) |
| **Position** | Row 1, Column 1 |

### Panel 2: Uptime

| Property | Value |
|----------|-------|
| **Type** | Stat Panel |
| **Metric** | Availability percentage |
| **Query** | `1 - (rate(learning_errors_total[7d]) / rate(learning_api_requests_total[7d]))` |
| **Thresholds** | >99.9% green, 99-99.9% yellow, <99% red |
| **Position** | Row 1, Column 2 |

### Panel 3: Error Rate

| Property | Value |
|----------|-------|
| **Type** | Time Series |
| **Metric** | Error percentage over time |
| **Query** | `rate(learning_errors_total[1m]) / rate(learning_api_requests_total[1m]) * 100` |
| **Thresholds** | <1% green, 1-5% yellow, >5% red |
| **Position** | Row 1, Column 3 |

### Panel 4: Prediction Activity

| Property | Value |
|----------|-------|
| **Type** | Mixed (Stat + Bar + Histogram) |
| **Metrics** | Predictions/min, approval rate, confidence distribution |
| **Queries** | `rate(learning_predictions_total[1m]) * 60`, `learning_predictions_total{result="approved"} / learning_predictions_total`, histogram of confidence values |
| **Position** | Row 2, Column 1 (wider) |

### Panel 5: Recommendation Distribution

| Property | Value |
|----------|-------|
| **Type** | Bar Chart |
| **Metric** | Recommendations by action type |
| **Query** | `sum by (action) (learning_recommendations_total)` |
| **Position** | Row 2, Column 2 (wider) |

### Panel 6: Feedback Rate

| Property | Value |
|----------|-------|
| **Type** | Mixed (Stat + Stacked Bar) |
| **Metrics** | Feedback/hour, approve vs reject ratio |
| **Queries** | `rate(learning_feedback_received_total[1h]) * 3600`, `sum by (decision) (learning_feedback_received_total)` |
| **Position** | Row 3, Column 1 |

### Panel 7: Approval Rate

| Property | Value |
|----------|-------|
| **Type** | Time Series + Table |
| **Metrics** | Overall approval rate, per-source approval rate |
| **Queries** | `learning_feedback_received_total{decision="approved"} / learning_feedback_received_total`, grouped by source |
| **Position** | Row 3, Column 2 |

### Panel 8: Top Sources

| Property | Value |
|----------|-------|
| **Type** | Table (sorted by volume) |
| **Metrics** | Source name, volume, quality score |
| **Queries** | `learning_source_profiles`, `learning_predictions_total` grouped by source |
| **Position** | Row 3, Column 3 |

### Panel 9: Timeline Growth

| Property | Value |
|----------|-------|
| **Type** | Time Series |
| **Metric** | Knowledge snapshots over time |
| **Query** | `learning_knowledge_snapshots` |
| **Position** | Row 4, Column 1 |

### Panel 10: Dataset Growth

| Property | Value |
|----------|-------|
| **Type** | Time Series |
| **Metric** | Datasets created over time |
| **Query** | `learning_datasets_count` |
| **Position** | Row 4, Column 2 |

### Panel 11: Knowledge Growth

| Property | Value |
|----------|-------|
| **Type** | Time Series |
| **Metric** | Knowledge artifacts over time |
| **Query** | `learning_artifacts_count` |
| **Position** | Row 4, Column 3 |

### Panel 12: Feature Store Growth

| Property | Value |
|----------|-------|
| **Type** | Time Series + Stat |
| **Metrics** | Feature entries over time, hit rate |
| **Queries** | `learning_feature_store_size`, cache hit rate (derived) |
| **Position** | Row 5, Column 1 |

### Panel 13: Training History

| Property | Value |
|----------|-------|
| **Type** | Table + Line Chart |
| **Metrics** | Model versions, weight evolution |
| **Queries** | `learning_training_snapshots`, weight values from model snapshots |
| **Position** | Row 5, Column 2 |

### Panel 14: Latency

| Property | Value |
|----------|-------|
| **Type** | Heatmap + Stat |
| **Metrics** | p50/p95/p99 latency by endpoint |
| **Queries** | `histogram_quantile(0.50, rate(learning_api_request_duration_ms_bucket[5m]))`, same for p95, p99 |
| **Position** | Row 5, Column 3 |

---

## 4. Row Summary

| Row | Theme | Panels | Purpose |
|-----|-------|--------|---------|
| 1 | Health | Service Status, Uptime, Error Rate | Is the system healthy? |
| 2 | Activity | Predictions, Recommendations | What's the system doing? |
| 3 | Learning | Feedback, Approval Rate, Sources | Is the system learning? |
| 4 | Knowledge | Timeline, Datasets, Artifacts | What has the system learned? |
| 5 | Infrastructure | Features, Training, Latency | How is the system performing? |

---

## 5. Variables & Filters

| Variable | Type | Values | Used In |
|----------|------|--------|---------|
| `source` | Custom | All article sources | Panels 4, 5, 7, 8 |
| `endpoint` | Custom | All API endpoints | Panel 14 |
| `decision` | Custom | approved/rejected/overridden | Panel 6 |
| `signal_type` | Custom | keyword/source_quality/temporal/feedback/coherence | Panel 4 |

---

## 6. Alert Overlay

When an alert fires, the corresponding panel should show a red border and the alert annotation should appear on the time series panels. See `learning-alerting-guide.md` for alert definitions.

---

*Generated: 2026-07-18 | Sprint 7.8 | Learning BC v1.0*
