"""
TypeDecorators for SQLAlchemy — convert between domain Value Objects and DB columns.

Each decorator handles serialization (domain -> DB) and deserialization (DB -> domain)
for a specific Value Object type. VOs are stored as JSON text or simple strings.

Decorator list:
  - EntityIdDecorator: Generic for all EntityId subclasses
  - ConfidenceDecorator: Confidence VO
  - FeatureVectorDecorator: FeatureVector VO
  - AlgorithmVersionDecorator: AlgorithmVersion VO
  - ScoreWeightsDecorator: ScoreWeights VO
  - SignalStrengthDecorator: SignalStrength VO
  - TimeWindowDecorator: TimeWindow VO
  - KeywordStatDecorator: KeywordStat VO
  - FeatureSnapshotDecorator: FeatureSnapshot VO
  - EnumDecorator: Generic for all str, Enum subclasses
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import String, Text, TypeDecorator


class EntityIdDecorator(TypeDecorator):
    """Generic TypeDecorator for all EntityId subclasses.

    Stores as String(36) in DB, reconstructs the specific EntityId subclass.
    """

    impl = String(36)
    cache_ok = True

    def __init__(self, entity_id_class: type) -> None:
        super().__init__()
        self._entity_id_class = entity_id_class

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return self._entity_id_class.from_string(value)


class ConfidenceDecorator(TypeDecorator):
    """TypeDecorator for Confidence VO.

    Stored as JSON: {"value": float, "sample_size": int}
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps({"value": value.value, "sample_size": value.sample_size})

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.confidence import Confidence

        data = json.loads(value)
        return Confidence(value=data["value"], sample_size=data["sample_size"])


class FeatureVectorDecorator(TypeDecorator):
    """TypeDecorator for FeatureVector VO.

    Stored as JSON: {"features": {"key": float, ...}}
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps({"features": dict(value.features)})

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.feature_vector import FeatureVector

        data = json.loads(value)
        return FeatureVector(features=data["features"])


class AlgorithmVersionDecorator(TypeDecorator):
    """TypeDecorator for AlgorithmVersion VO.

    Stored as string: "major.minor.patch"
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.algorithm_version import AlgorithmVersion

        return AlgorithmVersion.parse(value)


class ScoreWeightsDecorator(TypeDecorator):
    """TypeDecorator for ScoreWeights VO.

    Stored as JSON: {"relevance": float, "popularity": float, "recency": float, "source_reliability": float}
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(
            {
                "relevance": value.relevance,
                "popularity": value.popularity,
                "recency": value.recency,
                "source_reliability": value.source_reliability,
            }
        )

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.score_weights import ScoreWeights

        data = json.loads(value)
        return ScoreWeights(**data)


class SignalStrengthDecorator(TypeDecorator):
    """TypeDecorator for SignalStrength VO.

    Stored as JSON: {"value": float, "decay_factor": float}
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps({"value": value.value, "decay_factor": value.decay_factor})

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.signal_strength import SignalStrength

        data = json.loads(value)
        return SignalStrength(value=data["value"], decay_factor=data["decay_factor"])


class TimeWindowDecorator(TypeDecorator):
    """TypeDecorator for TimeWindow VO.

    Stored as JSON: {"start": iso_str, "end": iso_str}
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(
            {"start": value.start.isoformat(), "end": value.end.isoformat()}
        )

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.time_window import TimeWindow

        data = json.loads(value)
        return TimeWindow(
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
        )


class KeywordStatDecorator(TypeDecorator):
    """TypeDecorator for KeywordStat VO.

    Stored as JSON: {"keyword": str, "count": int, "approved_count": int}
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(
            {
                "keyword": value.keyword,
                "count": value.count,
                "approved_count": value.approved_count,
            }
        )

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.keyword_stat_vo import KeywordStat

        data = json.loads(value)
        return KeywordStat(**data)


class FeatureSnapshotDecorator(TypeDecorator):
    """TypeDecorator for FeatureSnapshot VO.

    Stored as JSON dict of all fields including timestamp as ISO string.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value.as_dict(), default=str)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        from learning.domain.value_objects.feature_snapshot import FeatureSnapshot

        data = json.loads(value)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return FeatureSnapshot(**data)


class EnumDecorator(TypeDecorator):
    """Generic TypeDecorator for all str, Enum subclasses.

    Stores the string value, reconstructs the enum.
    """

    impl = Text
    cache_ok = True

    def __init__(self, enum_class: type) -> None:
        super().__init__()
        self._enum_class = enum_class

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return value.value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        return self._enum_class(value)
