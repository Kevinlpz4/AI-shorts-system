# Learning BC — Alerting Guide

> **Date**: 2026-07-18
> **BC**: Learning Intelligence
> **Version**: 1.0 (Sprint 7.8)
> **Total Alerts**: 10 (2 CRITICAL, 4 HIGH, 2 MEDIUM, 2 LOW)

---

## 1. Alerting Philosophy

Alerts should be:
- **Actionable**: Every alert requires human action or has a runbook
- **Escalating**: LOW → MEDIUM → HIGH → CRITICAL as severity increases
- **Contextual**: Include enough info to triage without looking at dashboards
- **Non-noisy**: False positives erode trust in alerting

---

## 2. Severity Levels

| Level | Response Time | Notification | Example |
|-------|--------------|--------------|---------|
| **CRITICAL** | Immediate (page) | PagerDuty/Slack #alerts | Database down, config broken |
| **HIGH** | Within 1 hour | Slack #learning-alerts | Error rate spike, high latency |
| **MEDIUM** | Within 4 hours | Slack #learning-alerts | Export failures, integration issues |
| **LOW** | Within 24 hours | Email digest | Staleness, anomalies |

---

## 3. Alert Definitions

### 3.1 CRITICAL Alerts

#### Alert: DatabaseUnavailable

| Property | Value |
|----------|-------|
| **Condition** | `learning_health_status{check="database"} == 0` for 1 minute |
| **Severity** | CRITICAL |
| **For** | 1m |
| **Labels** | `service=learning-intelligence`, `severity=critical` |
| **Annotations** | Summary: "Learning BC database is unreachable" |
| | Description: "Health check for database dependency is failing. All persistence operations will fail." |
| **Escalation** | Page on-call engineer immediately |
| **Runbook** | See §4.1 |
| **Impact** | All write operations fail, read operations return stale data or errors |

```yaml
# Prometheus AlertManager rule
- alert: DatabaseUnavailable
  expr: learning_health_status{check="database"} == 0
  for: 1m
  labels:
    severity: critical
    service: learning-intelligence
  annotations:
    summary: "Learning BC database is unreachable"
    description: "Health check for database dependency has been failing for 1+ minutes."
    runbook_url: "https://wiki/runbook/database-unavailable"
```

#### Alert: ConfigurationErrors

| Property | Value |
|----------|-------|
| **Condition** | `learning_config_load_errors_total > 0` |
| **Severity** | CRITICAL |
| **For** | 0m (immediate) |
| **Labels** | `service=learning-intelligence`, `severity=critical` |
| **Annotations** | Summary: "Learning BC configuration failed to load" |
| | Description: "LearningConfig could not be loaded. Service may be running with incorrect defaults." |
| **Escalation** | Page on-call engineer immediately |
| **Runbook** | See §4.2 |
| **Impact** | Service may use wrong thresholds, wrong TTLs, wrong feature flags |

---

### 3.2 HIGH Alerts

#### Alert: PredictionFailures

| Property | Value |
|----------|-------|
| **Condition** | `rate(learning_errors_total{endpoint="/predict"}[5m]) / rate(learning_api_requests_total{endpoint="/predict"}[5m]) > 0.05` |
| **Severity** | HIGH |
| **For** | 5m |
| **Labels** | `service=learning-intelligence`, `severity=high`, `endpoint=predict` |
| **Annotations** | Summary: "Prediction endpoint error rate > 5%" |
| | Description: "The prediction endpoint has been failing at {{ $value | humanizePercentage }} for 5+ minutes." |
| **Escalation** | Notify team via Slack #learning-alerts |
| **Runbook** | See §4.3 |
| **Impact** | Article approval predictions failing, downstream systems affected |

#### Alert: RecommendationFailures

| Property | Value |
|----------|-------|
| **Condition** | `rate(learning_errors_total{endpoint="/recommend"}[5m]) / rate(learning_api_requests_total{endpoint="/recommend"}[5m]) > 0.05` |
| **Severity** | HIGH |
| **For** | 5m |
| **Labels** | `service=learning-intelligence`, `severity=high`, `endpoint=recommend` |
| **Annotations** | Summary: "Recommendation endpoint error rate > 5%" |
| | Description: "The recommendation endpoint has been failing at {{ $value | humanizePercentage }} for 5+ minutes." |
| **Escalation** | Notify team via Slack #learning-alerts |
| **Runbook** | See §4.4 |
| **Impact** | Content recommendations failing, editorial workflow disrupted |

#### Alert: KnowledgePersistenceFailures

| Property | Value |
|----------|-------|
| **Condition** | `rate(learning_errors_total{error_code=~".*Knowledge.*"}[5m]) > 0` |
| **Severity** | HIGH |
| **For** | 5m |
| **Labels** | `service=learning-intelligence`, `severity=high` |
| **Annotations** | Summary: "Knowledge persistence operations failing" |
| | Description: "Knowledge-related errors detected. Timeline snapshots or artifacts may not be persisting." |
| **Escalation** | Notify team via Slack #learning-alerts |
| **Runbook** | See §4.5 |
| **Impact** | Knowledge timeline gaps, potential data loss |

#### Alert: HighLatency

| Property | Value |
|----------|-------|
| **Condition** | `histogram_quantile(0.95, rate(learning_api_request_duration_ms_bucket[5m])) > 200` |
| **Severity** | HIGH |
| **For** | 5m |
| **Labels** | `service=learning-intelligence`, `severity=high` |
| **Annotations** | Summary: "API p95 latency > 200ms" |
| | Description: "The 95th percentile request latency has been above 200ms for 5+ minutes. Current: {{ $value }}ms" |
| **Escalation** | Notify team via Slack #learning-alerts |
| **Runbook** | See §4.6 |
| **Impact** | Slow responses, potential timeout cascades |

---

### 3.3 MEDIUM Alerts

#### Alert: DatasetExportFailures

| Property | Value |
|----------|-------|
| **Condition** | `increase(learning_errors_total{endpoint="/datasets/export"}[1h]) > 0` |
| **Severity** | MEDIUM |
| **For** | 0m |
| **Labels** | `service=learning-intelligence`, `severity=medium` |
| **Annotations** | Summary: "Dataset export failed" |
| | Description: "A dataset export operation failed. Check logs for details." |
| **Escalation** | Log + notify via Slack #learning-alerts |
| **Runbook** | See §4.7 |
| **Impact** | ML training pipeline affected, no datasets produced |

#### Alert: SignalAggregationFailures

| Property | Value |
|----------|-------|
| **Condition** | `increase(learning_errors_total{error_code=~".*Signal.*"}[1h]) > 0` |
| **Severity** | MEDIUM |
| **For** | 0m |
| **Labels** | `service=learning-intelligence`, `severity=medium` |
| **Annotations** | Summary: "Signal aggregation operation failed" |
| | Description: "A signal-related error occurred. Signal processing may be degraded." |
| **Escalation** | Log + notify via Slack #learning-alerts |
| **Runbook** | See §4.8 |
| **Impact** | Learning signals may be stale or missing |

---

### 3.4 LOW Alerts

#### Alert: FeedbackAnomaly

| Property | Value |
|----------|-------|
| **Condition** | `increase(learning_feedback_received_total[24h]) == 0` |
| **Severity** | LOW |
| **For** | 24h |
| **Labels** | `service=learning-intelligence`, `severity=low` |
| **Annotations** | Summary: "No feedback received in 24 hours" |
| | Description: "The learning system has received zero feedback records in the last 24 hours. This may indicate an upstream issue." |
| **Escalation** | Email digest |
| **Runbook** | See §4.9 |
| **Impact** | Learning system not improving, stale predictions |

#### Alert: ModelStaleness

| Property | Value |
|----------|-------|
| **Condition** | `(time() - learning_model_last_update_timestamp) > 30 * 24 * 3600` |
| **Severity** | LOW |
| **For** | 0m |
| **Labels** | `service=learning-intelligence`, `severity=low` |
| **Annotations** | Summary: "Learning model not updated in 30 days" |
| | Description: "The learning model has not been updated in 30+ days. Consider retraining with recent data." |
| **Escalation** | Email digest |
| **Runbook** | See §4.10 |
| **Impact** | Model predictions may be outdated |

---

## 4. Runbooks

### 4.1 DatabaseUnavailable

```
1. Check if the database process is running:
   - systemctl status postgresql (or docker ps for containerized DB)

2. Check database connectivity:
   - psql -h <host> -U <user> -d <database> -c "SELECT 1"

3. Check database disk space:
   - df -h /var/lib/postgresql

4. Check database connection pool:
   - Look at connection count: SELECT count(*) FROM pg_stat_activity

5. If DB is down, restart it:
   - systemctl restart postgresql

6. If disk is full, clean up:
   - VACUUM FULL on large tables
   - Archive old data

7. If connection pool is exhausted:
   - Restart the Learning BC service
   - Consider increasing pool size in config
```

### 4.2 ConfigurationErrors

```
1. Check LearningConfig values:
   - Verify .env file or environment variables
   - Check for typos in config keys

2. Validate config schema:
   - Run: python -c "from src.learning.infrastructure.configuration import LearningConfig; LearningConfig()"

3. Check for recent config changes:
   - git log --oneline -5 -- .env config/

4. If config is invalid, revert to last known good:
   - git checkout HEAD~1 -- .env

5. Restart the service after fixing config
```

### 4.3 PredictionFailures

```
1. Check prediction endpoint logs:
   - grep "predict" logs/learning.log | tail -50

2. Identify error type:
   - Domain errors (InvalidConfidence, etc.) → check input validation
   - Infrastructure errors → check dependencies

3. Check if feedback data is available:
   - GET /api/v1/learning/feedback?limit=5

4. Check signal freshness:
   - GET /api/v1/learning/signals

5. If input validation errors, check client payload format
6. If infrastructure errors, check §4.1 (DatabaseUnavailable)
```

### 4.4 RecommendationFailures

```
1. Check recommendation endpoint logs:
   - grep "recommend" logs/learning.log | tail -50

2. Identify error type:
   - Domain errors → check recommendation service logic
   - Infrastructure errors → check dependencies

3. Check if enough data exists for recommendations:
   - GET /api/v1/learning/knowledge

4. Verify scoring service health:
   - Check source quality profiles: GET /api/v1/learning/source-quality/all

5. If data insufficient, wait for more feedback to accumulate
```

### 4.5 KnowledgePersistenceFailures

```
1. Check knowledge-related errors in logs:
   - grep "Knowledge" logs/learning.log | tail -50

2. Check timeline connectivity:
   - GET /api/v1/learning/timeline

3. Check knowledge storage:
   - GET /api/v1/learning/artifacts

4. If timeline is disconnected, check KnowledgeTimeline wiring
5. If storage is full, archive old artifacts
```

### 4.6 HighLatency

```
1. Check which endpoint is slow:
   - Review Grafana latency panel breakdown

2. Check database query performance:
   - Enable slow query logging
   - EXPLAIN ANALYZE on frequent queries

3. Check feature store cache hit rate:
   - Low hit rate → increase cache TTL
   - Cache eviction → increase cache size

4. Check for resource contention:
   - CPU/memory usage on the service host
   - Database connection pool saturation

5. If persistent, consider:
   - Adding database indexes
   - Increasing cache size
   - Scaling horizontally
```

### 4.7 DatasetExportFailures

```
1. Check export endpoint logs:
   - grep "export" logs/learning.log | tail -20

2. Check disk space for export output:
   - df -h /data/exports

3. Check source data availability:
   - GET /api/v1/learning/datasets

4. If placeholder data issue, implement real export logic
5. If disk full, clean old exports
```

### 4.8 SignalAggregationFailures

```
1. Check signal-related errors:
   - grep "Signal" logs/learning.log | tail -20

2. Check signal handlers:
   - Verify all 5 handlers are registered
   - Check handler execution logs

3. Check signal decay:
   - Old signals may have decayed to zero
   - Verify signal_decay_factor config

4. If handler error, check domain event emission
```

### 4.9 FeedbackAnomaly

```
1. Verify feedback endpoint is reachable:
   - curl -X POST /api/v1/learning/feedback -d '...'

2. Check upstream systems:
   - Is the editorial team using the feedback mechanism?
   - Are there integration issues with the feedback source?

3. Check if feedback pipeline is working:
   - GET /api/v1/learning/feedback?limit=5

4. If no feedback is expected (e.g., new deployment), this alert is expected
5. If feedback should exist, investigate upstream integration
```

### 4.10 ModelStaleness

```
1. Check model version history:
   - GET /api/v1/learning/analytics

2. Verify training pipeline:
   - Is the ML training pipeline running?
   - Are datasets being exported?

3. Check if new data is available:
   - GET /api/v1/learning/datasets

4. If training pipeline is broken, fix it
5. If no new data, this is expected (model is current for available data)
```

---

## 5. SLA Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | 99.9% (8.76h downtime/year) | Health check success rate |
| Prediction Latency (p95) | <200ms | `learning_prediction_latency_ms` |
| Recommendation Latency (p95) | <200ms | `learning_recommendation_latency_ms` |
| Feedback Latency (p95) | <100ms | `learning_feedback_latency_ms` |
| Error Rate | <1% | `learning_errors_total / learning_api_requests_total` |
| Data Freshness | <1h | Time since last signal update |
| Model Update Frequency | Monthly | Time since last model snapshot |

---

## 6. Escalation Path

```
Alert fires
    │
    ▼
Slack #learning-alerts (all alerts)
    │
    ├── CRITICAL → PagerDuty on-call (immediate page)
    │               └── If no response in 15min → secondary on-call
    │
    ├── HIGH → Team lead notified (within 1h)
    │           └── If unresolved in 4h → escalate to CRITICAL
    │
    ├── MEDIUM → Team notified (within 4h)
    │             └── If unresolved in 24h → escalate to HIGH
    │
    └── LOW → Email digest (daily)
               └── Reviewed in weekly sprint
```

---

## 7. Alert Suppression Rules

| Scenario | Action |
|----------|--------|
| During maintenance window | Suppress all alerts except CRITICAL |
| During deployment | Suppress HIGH/MEDIUM for 10 minutes |
| Database migration | Suppress DatabaseUnavailable during migration window |
| Known issue | Add `silence` annotation with ticket reference |

---

*Generated: 2026-07-18 | Sprint 7.8 | Learning BC v1.0*
