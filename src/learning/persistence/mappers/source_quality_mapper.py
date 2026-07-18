"""
SourceQualityMapper — Domain <-> SQLAlchemy model mapping for SourceQualityProfile.

SourceQualityProfile uses object.__setattr__ internally.
Keywords dict is stored as JSON.
"""
from __future__ import annotations

import json
from datetime import datetime

from learning.domain.entities.ids import SourceQualityId
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.value_objects.keyword_stat_vo import KeywordStat
from learning.persistence.models.source_quality import SourceQualityProfileModel


class SourceQualityMapper:
    """Maps SourceQualityProfile domain entity <-> SourceQualityProfileModel."""

    @staticmethod
    def to_domain(model: SourceQualityProfileModel) -> SourceQualityProfile:
        """Convert SQLAlchemy model to domain entity."""
        keywords_data = json.loads(model.keywords_json)
        keywords = {}
        for kw, stat_data in keywords_data.items():
            keywords[kw] = KeywordStat(
                keyword=stat_data["keyword"],
                count=stat_data["count"],
                approved_count=stat_data["approved_count"],
            )

        return SourceQualityProfile(
            id=SourceQualityId.from_string(model.id),
            source_name=model.source_name,
            total_decisions=model.total_decisions,
            approved_count=model.approved_count,
            rejected_count=model.rejected_count,
            auto_approved_count=model.auto_approved_count,
            auto_rejected_count=model.auto_rejected_count,
            overridden_count=model.overridden_count,
            keywords=keywords,
            last_updated=model.last_updated,
        )

    @staticmethod
    def to_model(
        entity: SourceQualityProfile, version: int = 1
    ) -> SourceQualityProfileModel:
        """Convert domain entity to SQLAlchemy model."""
        keywords_json = {}
        for kw, stat in entity.keywords.items():
            keywords_json[kw] = {
                "keyword": stat.keyword,
                "count": stat.count,
                "approved_count": stat.approved_count,
            }

        return SourceQualityProfileModel(
            id=str(entity.id),
            source_name=entity.source_name,
            total_decisions=entity.total_decisions,
            approved_count=entity.approved_count,
            rejected_count=entity.rejected_count,
            auto_approved_count=entity.auto_approved_count,
            auto_rejected_count=entity.auto_rejected_count,
            overridden_count=entity.overridden_count,
            approval_rate=entity.approval_rate,
            keywords_json=json.dumps(keywords_json),
            last_updated=entity.last_updated,
            version=version,
        )
