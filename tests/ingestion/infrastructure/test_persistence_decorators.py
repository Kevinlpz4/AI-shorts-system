"""
Tests for Value Object TypeDecorators (Sprint 5.2).

Validates for each TypeDecorator:
  - process_bind_param: VO → underlying type
  - process_result_value: underlying type → VO
  - None propagation in both directions
  - ORM roundtrip (insert + select)

Tested decorators
-----------------
* ``ArticleTitleType``
* ``ArticleUrlType``
* ``CategoryNameType``
* ``SourceUrlType``
* ``LanguageType``
* ``SourceTypeType``
* ``SyncModeType``
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import Mapped, mapped_column

from ingestion.infrastructure.persistence import PersistenceBase
from ingestion.infrastructure.persistence.decorators import (
    ArticleTitleType,
    ArticleUrlType,
    CategoryNameType,
    LanguageType,
    SourceTypeType,
    SourceUrlType,
    SyncModeType,
)
from ingestion.infrastructure.persistence.types import EntityIdType

from ingestion.domain.entities.ids import SourceId
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode

# ══════════════════════════════════════════════════════════════════════════════
# Shared test values
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_TITLE = "Breaking News: AI Learns to Write Tests"
SAMPLE_URL = "https://example.com/article/123"
SAMPLE_CATEGORY = "Technology"
SAMPLE_SOURCE_URL = "https://example.com"
SAMPLE_LANG = "en"

SAMPLE_UUID = uuid4()


# ══════════════════════════════════════════════════════════════════════════════
# ArticleTitleType
# ══════════════════════════════════════════════════════════════════════════════

class TestArticleTitleType:
    """Tests for ArticleTitleType."""

    @pytest.fixture
    def decorator(self):
        return ArticleTitleType()

    def test_construction(self, decorator):
        """ArticleTitleType debe construirse sin argumentos."""
        assert decorator is not None
        assert decorator.cache_ok is True

    def test_bind_param_title_to_str(self, decorator):
        """ArticleTitle debe convertirse a str para la BD."""
        vo = ArticleTitle(SAMPLE_TITLE)
        result = decorator.process_bind_param(vo, None)
        assert result == SAMPLE_TITLE
        assert isinstance(result, str)

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_title(self, decorator):
        """str debe convertirse a ArticleTitle al leer de BD."""
        result = decorator.process_result_value(SAMPLE_TITLE, None)
        assert isinstance(result, ArticleTitle)
        assert result.value == SAMPLE_TITLE

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None


# ══════════════════════════════════════════════════════════════════════════════
# ArticleUrlType
# ══════════════════════════════════════════════════════════════════════════════

class TestArticleUrlType:
    """Tests for ArticleUrlType."""

    @pytest.fixture
    def decorator(self):
        return ArticleUrlType()

    def test_bind_param_url_to_str(self, decorator):
        """ArticleUrl debe convertirse a str para la BD."""
        vo = ArticleUrl(SAMPLE_URL)
        result = decorator.process_bind_param(vo, None)
        assert result == SAMPLE_URL
        assert isinstance(result, str)

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_url(self, decorator):
        """str debe convertirse a ArticleUrl al leer de BD."""
        result = decorator.process_result_value(SAMPLE_URL, None)
        assert isinstance(result, ArticleUrl)
        assert result.value == SAMPLE_URL

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None


# ══════════════════════════════════════════════════════════════════════════════
# CategoryNameType
# ══════════════════════════════════════════════════════════════════════════════

class TestCategoryNameType:
    """Tests for CategoryNameType."""

    @pytest.fixture
    def decorator(self):
        return CategoryNameType()

    def test_bind_param_name_to_str(self, decorator):
        """CategoryName debe convertirse a str para la BD."""
        vo = CategoryName(SAMPLE_CATEGORY)
        result = decorator.process_bind_param(vo, None)
        assert result == SAMPLE_CATEGORY
        assert isinstance(result, str)

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_name(self, decorator):
        """str debe convertirse a CategoryName al leer de BD."""
        result = decorator.process_result_value(SAMPLE_CATEGORY, None)
        assert isinstance(result, CategoryName)
        assert result.value == SAMPLE_CATEGORY

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None


# ══════════════════════════════════════════════════════════════════════════════
# SourceUrlType
# ══════════════════════════════════════════════════════════════════════════════

class TestSourceUrlType:
    """Tests for SourceUrlType."""

    @pytest.fixture
    def decorator(self):
        return SourceUrlType()

    def test_bind_param_url_to_str(self, decorator):
        """SourceUrl debe convertirse a str para la BD."""
        vo = SourceUrl(SAMPLE_SOURCE_URL)
        result = decorator.process_bind_param(vo, None)
        assert result == SAMPLE_SOURCE_URL
        assert isinstance(result, str)

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_url(self, decorator):
        """str debe convertirse a SourceUrl al leer de BD."""
        result = decorator.process_result_value(SAMPLE_SOURCE_URL, None)
        assert isinstance(result, SourceUrl)
        assert result.value == SAMPLE_SOURCE_URL

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None


# ══════════════════════════════════════════════════════════════════════════════
# LanguageType
# ══════════════════════════════════════════════════════════════════════════════

class TestLanguageType:
    """Tests for LanguageType.

    NOTE: LanguageType is SPECIAL — it uses ``.code`` (not ``.value``)
    as the internal attribute.
    """

    @pytest.fixture
    def decorator(self):
        return LanguageType()

    def test_bind_param_lang_to_str(self, decorator):
        """Language debe convertirse a str via .code para la BD."""
        vo = Language(SAMPLE_LANG)
        result = decorator.process_bind_param(vo, None)
        assert result == SAMPLE_LANG
        assert isinstance(result, str)

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_lang(self, decorator):
        """str debe convertirse a Language al leer de BD."""
        result = decorator.process_result_value(SAMPLE_LANG, None)
        assert isinstance(result, Language)
        assert result.code == SAMPLE_LANG

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None


# ══════════════════════════════════════════════════════════════════════════════
# SourceTypeType (Enum)
# ══════════════════════════════════════════════════════════════════════════════

class TestSourceTypeType:
    """Tests for SourceTypeType (enum → VARCHAR)."""

    @pytest.fixture
    def decorator(self):
        return SourceTypeType()

    def test_bind_param_enum_to_str(self, decorator):
        """SourceType enum debe convertirse a str para la BD."""
        result = decorator.process_bind_param(SourceType.RSS, None)
        assert result == "RSS"

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_enum(self, decorator):
        """str debe convertirse a SourceType al leer de BD."""
        result = decorator.process_result_value("API", None)
        assert result is SourceType.API

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None

    def test_result_value_invalid_raises_value_error(self, decorator):
        """str inválido debe lanzar ValueError (defensa en profundidad)."""
        with pytest.raises(ValueError):
            decorator.process_result_value("INVALID_TYPE", None)


# ══════════════════════════════════════════════════════════════════════════════
# SyncModeType (Enum)
# ══════════════════════════════════════════════════════════════════════════════

class TestSyncModeType:
    """Tests for SyncModeType (enum → VARCHAR)."""

    @pytest.fixture
    def decorator(self):
        return SyncModeType()

    def test_bind_param_enum_to_str(self, decorator):
        """SyncMode enum debe convertirse a str para la BD."""
        result = decorator.process_bind_param(SyncMode.PULL, None)
        assert result == "PULL"

    def test_bind_param_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_bind_param(None, None) is None

    def test_result_value_str_to_enum(self, decorator):
        """str debe convertirse a SyncMode al leer de BD."""
        result = decorator.process_result_value("STREAM", None)
        assert result is SyncMode.STREAM

    def test_result_value_none(self, decorator):
        """None debe retornar None."""
        assert decorator.process_result_value(None, None) is None


# ══════════════════════════════════════════════════════════════════════════════
# ORM Roundtrip — All TypeDecorators
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.usefixtures("tables")
class TestAllDecoratorsRoundtrip:
    """ORM roundtrip: insert with VOs → DB → read back VOs."""

    def test_article_title_type_roundtrip(self, engine, engine_session):
        """ArticleTitleType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = TitleModel(
            id=eid,
            title=ArticleTitle("Test Title"),
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(TitleModel, eid)
        assert loaded is not None
        assert isinstance(loaded.title, ArticleTitle)
        assert loaded.title.value == "Test Title"

    def test_article_url_type_roundtrip(self, engine, engine_session):
        """ArticleUrlType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = UrlModel(
            id=eid,
            url=ArticleUrl("https://example.com/article"),
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(UrlModel, eid)
        assert loaded is not None
        assert isinstance(loaded.url, ArticleUrl)
        assert loaded.url.value == "https://example.com/article"

    def test_category_name_type_roundtrip(self, engine, engine_session):
        """CategoryNameType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = CatNameModel(
            id=eid,
            name=CategoryName("Technology"),
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(CatNameModel, eid)
        assert loaded is not None
        assert isinstance(loaded.name, CategoryName)
        assert loaded.name.value == "Technology"

    def test_source_url_type_roundtrip(self, engine, engine_session):
        """SourceUrlType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = SrcUrlModel(
            id=eid,
            source_url=SourceUrl("https://example.com"),
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(SrcUrlModel, eid)
        assert loaded is not None
        assert isinstance(loaded.source_url, SourceUrl)
        assert loaded.source_url.value == "https://example.com"

    def test_language_type_roundtrip(self, engine, engine_session):
        """LanguageType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = LangModel(
            id=eid,
            language=Language("en"),
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(LangModel, eid)
        assert loaded is not None
        assert isinstance(loaded.language, Language)
        assert loaded.language.code == "en"

    def test_source_type_type_roundtrip(self, engine, engine_session):
        """SourceTypeType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = EnumModel(
            id=eid,
            source_type=SourceType.API,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(EnumModel, eid)
        assert loaded is not None
        assert isinstance(loaded.source_type, SourceType)
        assert loaded.source_type is SourceType.API

    def test_sync_mode_type_roundtrip(self, engine, engine_session):
        """SyncModeType en columna ORM debe sobrevivir un ciclo completo."""
        eid = SourceId(value=SAMPLE_UUID)
        model = SyncModeModel(
            id=eid,
            sync_mode=SyncMode.STREAM,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(SyncModeModel, eid)
        assert loaded is not None
        assert isinstance(loaded.sync_mode, SyncMode)
        assert loaded.sync_mode is SyncMode.STREAM

    def test_none_roundtrip(self, engine, engine_session):
        """Columnas nullable con None deben persistir y cargar como None."""
        eid = SourceId(value=SAMPLE_UUID)
        model = NullableModel(
            id=eid,
            title=None,
            url=None,
        )
        engine_session.add(model)
        engine_session.commit()

        loaded = engine_session.get(NullableModel, eid)
        assert loaded is not None
        assert loaded.title is None
        assert loaded.url is None


# ══════════════════════════════════════════════════════════════════════════════
# Test Models
# ══════════════════════════════════════════════════════════════════════════════


class TitleModel(PersistenceBase):
    """Minimal model with ArticleTitleType column."""
    __tablename__ = "test_title"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    title: Mapped[ArticleTitle] = mapped_column(ArticleTitleType)


class UrlModel(PersistenceBase):
    """Minimal model with ArticleUrlType column."""
    __tablename__ = "test_url"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    url: Mapped[ArticleUrl] = mapped_column(ArticleUrlType)


class CatNameModel(PersistenceBase):
    """Minimal model with CategoryNameType column."""
    __tablename__ = "test_catname"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    name: Mapped[CategoryName] = mapped_column(CategoryNameType)


class SrcUrlModel(PersistenceBase):
    """Minimal model with SourceUrlType column."""
    __tablename__ = "test_src_url"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    source_url: Mapped[SourceUrl] = mapped_column(SourceUrlType)


class LangModel(PersistenceBase):
    """Minimal model with LanguageType column."""
    __tablename__ = "test_lang"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    language: Mapped[Language] = mapped_column(LanguageType)


class EnumModel(PersistenceBase):
    """Minimal model with SourceTypeType column."""
    __tablename__ = "test_enum"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    source_type: Mapped[SourceType] = mapped_column(SourceTypeType)


class SyncModeModel(PersistenceBase):
    """Minimal model with SyncModeType column."""
    __tablename__ = "test_sync_mode"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    sync_mode: Mapped[SyncMode] = mapped_column(SyncModeType)


class NullableModel(PersistenceBase):
    """Model with nullable VO columns to test None roundtrip."""
    __tablename__ = "test_nullable"
    id: Mapped[SourceId] = mapped_column(EntityIdType(SourceId), primary_key=True)
    title: Mapped[ArticleTitle | None] = mapped_column(ArticleTitleType, nullable=True)
    url: Mapped[ArticleUrl | None] = mapped_column(ArticleUrlType, nullable=True)
