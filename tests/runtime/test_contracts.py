"""
Tests for ProviderResult, PipelineContext, PipelineResult, StepResult,
JobResult, JobContext, ValidationReport.

Covers:
- ProviderResult construction and defaults
- PipelineContext mutable operations (set/get step results)
- PipelineResult and StepResult construction
- JobResult and JobContext construction
- ValidationReport construction
- Immutability (frozen) where applicable
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from runtime.contracts.job_result import JobContext, JobResult
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import PipelineResult, StepResult
from runtime.contracts.provider_result import ProviderResult
from runtime.contracts.validation_report import ValidationReport


class TestProviderResult:
    """Tests for ProviderResult frozen dataclass."""

    def test_default_construction(self) -> None:
        """ProviderResult has sensible defaults."""
        result = ProviderResult(source_id="src-1", provider="rss")

        assert result.source_id == "src-1"
        assert result.provider == "rss"
        assert result.items == []
        assert result.fetched_at is None
        assert result.metadata == {}
        assert result.errors == []

    def test_full_construction(self) -> None:
        """ProviderResult accepts all fields."""
        now = datetime.now(timezone.utc)
        result = ProviderResult(
            source_id="src-2",
            provider="newsapi",
            items=[{"title": "Test", "url": "http://example.com"}],
            fetched_at=now,
            metadata={"count": "1"},
            errors=["timeout"],
        )

        assert result.source_id == "src-2"
        assert result.provider == "newsapi"
        assert len(result.items) == 1
        assert result.fetched_at == now
        assert result.metadata == {"count": "1"}
        assert result.errors == ["timeout"]

    def test_frozen_immutability(self) -> None:
        """ProviderResult is frozen."""
        result = ProviderResult(source_id="src-1", provider="rss")

        with pytest.raises(AttributeError):
            result.source_id = "src-2"  # type: ignore[misc]


class TestPipelineContext:
    """Tests for PipelineContext mutable dataclass."""

    def test_default_construction(self) -> None:
        """PipelineContext has sensible defaults."""
        ctx = PipelineContext()

        assert isinstance(ctx.correlation_id, UUID)
        assert ctx.step_data == {}
        assert ctx.errors == []

    def test_set_and_get_step_result(self) -> None:
        """PipelineContext stores and retrieves step results by name."""
        ctx = PipelineContext()

        ctx.set_step_result("fetch", {"items": 10})
        result = ctx.get_step_result("fetch")

        assert result == {"items": 10}

    def test_get_missing_step_returns_none(self) -> None:
        """PipelineContext returns None for missing step names."""
        ctx = PipelineContext()

        assert ctx.get_step_result("nonexistent") is None

    def test_custom_correlation_id(self) -> None:
        """PipelineContext accepts a custom correlation_id."""
        cid = uuid4()
        ctx = PipelineContext(correlation_id=cid)

        assert ctx.correlation_id == cid

    def test_step_data_overwrites(self) -> None:
        """Setting the same step name twice overwrites the previous value."""
        ctx = PipelineContext()

        ctx.set_step_result("step1", {"v": 1})
        ctx.set_step_result("step1", {"v": 2})

        assert ctx.get_step_result("step1") == {"v": 2}

    def test_multiple_steps(self) -> None:
        """PipelineContext holds multiple independent step results."""
        ctx = PipelineContext()

        ctx.set_step_result("step_a", "result_a")
        ctx.set_step_result("step_b", "result_b")

        assert ctx.get_step_result("step_a") == "result_a"
        assert ctx.get_step_result("step_b") == "result_b"

    def test_errors_list(self) -> None:
        """PipelineContext errors list is mutable."""
        ctx = PipelineContext()
        ctx.errors.append("something went wrong")

        assert ctx.errors == ["something went wrong"]


class TestStepResult:
    """Tests for StepResult frozen dataclass."""

    def test_minimal_construction(self) -> None:
        """StepResult requires step_name and success."""
        result = StepResult(step_name="fetch", success=True)

        assert result.step_name == "fetch"
        assert result.success is True
        assert result.items_processed == 0
        assert result.items_output == 0
        assert result.errors == []
        assert result.metadata == {}

    def test_full_construction(self) -> None:
        """StepResult accepts all fields."""
        result = StepResult(
            step_name="transform",
            success=False,
            items_processed=100,
            items_output=95,
            errors=["5 items malformed"],
            metadata={"duration_ms": "1234"},
        )

        assert result.step_name == "transform"
        assert result.success is False
        assert result.items_processed == 100
        assert result.items_output == 95
        assert result.errors == ["5 items malformed"]
        assert result.metadata == {"duration_ms": "1234"}

    def test_frozen_immutability(self) -> None:
        """StepResult is frozen."""
        result = StepResult(step_name="fetch", success=True)

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


class TestPipelineResult:
    """Tests for PipelineResult frozen dataclass."""

    def test_default_construction(self) -> None:
        """PipelineResult has sensible defaults."""
        cid = uuid4()
        result = PipelineResult(correlation_id=cid)

        assert result.correlation_id == cid
        assert result.steps == []
        assert result.success is True
        assert result.total_items_processed == 0
        assert result.total_items_output == 0
        assert result.errors == []

    def test_with_steps(self) -> None:
        """PipelineResult holds StepResult list."""
        cid = uuid4()
        steps = [
            StepResult(step_name="fetch", success=True, items_processed=10),
            StepResult(step_name="transform", success=True, items_output=10),
        ]
        result = PipelineResult(
            correlation_id=cid,
            steps=steps,
            total_items_processed=10,
            total_items_output=10,
        )

        assert len(result.steps) == 2
        assert result.steps[0].step_name == "fetch"
        assert result.total_items_processed == 10

    def test_frozen_immutability(self) -> None:
        """PipelineResult is frozen."""
        result = PipelineResult(correlation_id=uuid4())

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


class TestJobContext:
    """Tests for JobContext frozen dataclass."""

    def test_default_construction(self) -> None:
        """JobContext has sensible defaults."""
        ctx = JobContext()

        assert isinstance(ctx.correlation_id, UUID)
        assert ctx.triggered_at is None
        assert ctx.metadata == {}

    def test_custom_construction(self) -> None:
        """JobContext accepts custom values."""
        now = datetime.now(timezone.utc)
        cid = uuid4()
        ctx = JobContext(
            correlation_id=cid,
            triggered_at=now,
            metadata={"source": "scheduler"},
        )

        assert ctx.correlation_id == cid
        assert ctx.triggered_at == now
        assert ctx.metadata == {"source": "scheduler"}

    def test_frozen_immutability(self) -> None:
        """JobContext is frozen."""
        ctx = JobContext()

        with pytest.raises(AttributeError):
            ctx.correlation_id = uuid4()  # type: ignore[misc]


class TestJobResult:
    """Tests for JobResult frozen dataclass."""

    def test_minimal_construction(self) -> None:
        """JobResult requires job_name, success, and correlation_id."""
        cid = uuid4()
        result = JobResult(job_name="ingestion", success=True, correlation_id=cid)

        assert result.job_name == "ingestion"
        assert result.success is True
        assert result.correlation_id == cid
        assert result.pipeline_result is None
        assert result.duration_seconds == 0.0
        assert result.errors == []

    def test_full_construction(self) -> None:
        """JobResult accepts all fields."""
        cid = uuid4()
        pipeline_result = PipelineResult(correlation_id=cid)
        result = JobResult(
            job_name="learning",
            success=False,
            correlation_id=cid,
            pipeline_result=pipeline_result,
            duration_seconds=12.5,
            errors=["step failed"],
        )

        assert result.job_name == "learning"
        assert result.success is False
        assert result.pipeline_result is pipeline_result
        assert result.duration_seconds == 12.5
        assert result.errors == ["step failed"]

    def test_frozen_immutability(self) -> None:
        """JobResult is frozen."""
        result = JobResult(job_name="j", success=True, correlation_id=uuid4())

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]


class TestValidationReport:
    """Tests for ValidationReport frozen dataclass."""

    def test_construction(self) -> None:
        """ValidationReport accepts all fields."""
        now = datetime.now(timezone.utc)
        report = ValidationReport(
            generated_at=now,
            accuracy=0.95,
            precision=0.92,
            recall=0.88,
            f1_score=0.90,
            total_predictions=1000,
            total_feedback=500,
            improvement_pct=5.2,
            metadata={"version": "v1"},
        )

        assert report.generated_at == now
        assert report.accuracy == 0.95
        assert report.precision == 0.92
        assert report.recall == 0.88
        assert report.f1_score == 0.90
        assert report.total_predictions == 1000
        assert report.total_feedback == 500
        assert report.improvement_pct == 5.2
        assert report.metadata == {"version": "v1"}

    def test_minimal_construction(self) -> None:
        """ValidationReport has sensible defaults for metrics."""
        now = datetime.now(timezone.utc)
        report = ValidationReport(generated_at=now)

        assert report.accuracy == 0.0
        assert report.precision == 0.0
        assert report.recall == 0.0
        assert report.f1_score == 0.0
        assert report.total_predictions == 0
        assert report.total_feedback == 0
        assert report.improvement_pct == 0.0
        assert report.metadata == {}

    def test_frozen_immutability(self) -> None:
        """ValidationReport is frozen."""
        report = ValidationReport(generated_at=datetime.now(timezone.utc))

        with pytest.raises(AttributeError):
            report.accuracy = 1.0  # type: ignore[misc]
