"""
Tests for EventDispatcher — decoupled, Open/Closed event dispatch.

Validates: handler registration, dispatch, exception isolation,
unregistration, handler counting, and dispatch semantics.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from learning.integration.dispatcher.event_dispatcher import EventDispatcher
from learning.integration.events.ingestion_events import (
    ArticleCreated,
    RawArticleCollected,
    RawArticleRejected,
)
from learning.integration.events.learning_outbound_events import (
    RecommendationGenerated,
)


class TestEventDispatcherRegistration:
    """Handler registration and has_handlers / handler_count."""

    def test_register_single_handler(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock()
        dispatcher.register(RawArticleCollected, handler)
        assert dispatcher.has_handlers(RawArticleCollected)

    def test_register_multiple_handlers_same_event(self) -> None:
        dispatcher = EventDispatcher()
        handler_a = MagicMock(name="handler_a")
        handler_b = MagicMock(name="handler_b")
        dispatcher.register(RawArticleCollected, handler_a)
        dispatcher.register(RawArticleCollected, handler_b)
        assert dispatcher.handler_count(RawArticleCollected) == 2

    def test_register_does_not_duplicate(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock()
        dispatcher.register(RawArticleCollected, handler)
        dispatcher.register(RawArticleCollected, handler)
        assert dispatcher.handler_count(RawArticleCollected) == 1

    def test_has_handlers_true(self) -> None:
        dispatcher = EventDispatcher()
        dispatcher.register(RawArticleCollected, MagicMock())
        assert dispatcher.has_handlers(RawArticleCollected) is True

    def test_has_handlers_false(self) -> None:
        dispatcher = EventDispatcher()
        assert dispatcher.has_handlers(RawArticleCollected) is False

    def test_handler_count(self) -> None:
        dispatcher = EventDispatcher()
        assert dispatcher.handler_count(RawArticleCollected) == 0
        dispatcher.register(RawArticleCollected, MagicMock())
        assert dispatcher.handler_count(RawArticleCollected) == 1
        dispatcher.register(RawArticleCollected, MagicMock())
        assert dispatcher.handler_count(RawArticleCollected) == 2


class TestEventDispatcherUnregistration:
    """Unregistration of handlers."""

    def test_unregister_handler(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock()
        dispatcher.register(RawArticleCollected, handler)
        dispatcher.unregister(RawArticleCollected, handler)
        assert dispatcher.has_handlers(RawArticleCollected) is False

    def test_unregister_only_removes_specified_handler(self) -> None:
        dispatcher = EventDispatcher()
        handler_a = MagicMock(name="a")
        handler_b = MagicMock(name="b")
        dispatcher.register(RawArticleCollected, handler_a)
        dispatcher.register(RawArticleCollected, handler_b)
        dispatcher.unregister(RawArticleCollected, handler_a)
        assert dispatcher.handler_count(RawArticleCollected) == 1

    def test_unregister_raises_key_error_no_event_type(self) -> None:
        dispatcher = EventDispatcher()
        with pytest.raises(KeyError):
            dispatcher.unregister(RawArticleCollected, MagicMock())

    def test_unregister_raises_value_error_handler_not_found(self) -> None:
        dispatcher = EventDispatcher()
        dispatcher.register(RawArticleCollected, MagicMock())
        with pytest.raises(ValueError):
            dispatcher.unregister(RawArticleCollected, MagicMock())


class TestEventDispatcherDispatch:
    """Event dispatching and exception isolation."""

    def test_dispatch_calls_handler(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock()
        dispatcher.register(RawArticleCollected, handler)
        event = RawArticleCollected(article_id="art-001", source_name="Reuters")
        dispatcher.dispatch(event)
        handler.assert_called_once_with(event)

    def test_dispatch_returns_empty_on_success(self) -> None:
        dispatcher = EventDispatcher()
        dispatcher.register(RawArticleCollected, MagicMock())
        event = RawArticleCollected()
        errors = dispatcher.dispatch(event)
        assert errors == []

    def test_dispatch_catches_handler_exception(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock(side_effect=RuntimeError("boom"))
        dispatcher.register(RawArticleCollected, handler)
        event = RawArticleCollected()
        errors = dispatcher.dispatch(event)
        assert len(errors) == 1
        assert isinstance(errors[0], RuntimeError)
        assert str(errors[0]) == "boom"

    def test_dispatch_does_not_stop_on_first_error(self) -> None:
        dispatcher = EventDispatcher()
        failing_handler = MagicMock(side_effect=RuntimeError("fail"))
        success_handler = MagicMock()
        dispatcher.register(RawArticleCollected, failing_handler)
        dispatcher.register(RawArticleCollected, success_handler)
        event = RawArticleCollected()
        errors = dispatcher.dispatch(event)
        assert len(errors) == 1
        success_handler.assert_called_once_with(event)

    def test_dispatch_no_handlers_returns_empty(self) -> None:
        dispatcher = EventDispatcher()
        event = RawArticleCollected()
        errors = dispatcher.dispatch(event)
        assert errors == []

    def test_dispatch_preserves_event_immutability(self) -> None:
        dispatcher = EventDispatcher()
        original_article_id = "art-immutable"
        event = RawArticleCollected(article_id=original_article_id)
        dispatcher.register(RawArticleCollected, MagicMock())
        dispatcher.dispatch(event)
        assert event.article_id == original_article_id

    def test_dispatch_multiple_handler_errors(self) -> None:
        dispatcher = EventDispatcher()
        handler_a = MagicMock(side_effect=ValueError("err_a"))
        handler_b = MagicMock(side_effect=TypeError("err_b"))
        dispatcher.register(RawArticleCollected, handler_a)
        dispatcher.register(RawArticleCollected, handler_b)
        errors = dispatcher.dispatch(RawArticleCollected())
        assert len(errors) == 2
        assert isinstance(errors[0], ValueError)
        assert isinstance(errors[1], TypeError)


class TestEventDispatcherMultipleEventTypes:
    """Dispatch with different event types — Open/Closed principle."""

    def test_multiple_event_types(self) -> None:
        dispatcher = EventDispatcher()
        ingestion_handler = MagicMock(name="ingestion_handler")
        outbound_handler = MagicMock(name="outbound_handler")
        dispatcher.register(RawArticleCollected, ingestion_handler)
        dispatcher.register(RecommendationGenerated, outbound_handler)

        event_ingestion = RawArticleCollected(article_id="art-001")
        event_outbound = RecommendationGenerated(recommendation="APPROVE")

        dispatcher.dispatch(event_ingestion)
        dispatcher.dispatch(event_outbound)

        ingestion_handler.assert_called_once_with(event_ingestion)
        outbound_handler.assert_called_once_with(event_outbound)

    def test_dispatch_correlation_id_event(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock()
        dispatcher.register(RawArticleCollected, handler)
        event = RawArticleCollected(
            correlation_id="corr-123",
            article_id="art-001",
        )
        dispatcher.dispatch(event)
        handler.assert_called_once_with(event)
        assert handler.call_args[0][0].correlation_id == "corr-123"

    def test_dispatch_multiple_events_same_type(self) -> None:
        dispatcher = EventDispatcher()
        handler = MagicMock()
        dispatcher.register(RawArticleCollected, handler)

        event1 = RawArticleCollected(article_id="art-001")
        event2 = RawArticleCollected(article_id="art-002")
        dispatcher.dispatch(event1)
        dispatcher.dispatch(event2)

        assert handler.call_count == 2
        handler.assert_any_call(event1)
        handler.assert_any_call(event2)

    def test_register_different_event_types_independent(self) -> None:
        dispatcher = EventDispatcher()
        assert dispatcher.handler_count(RawArticleCollected) == 0
        assert dispatcher.handler_count(ArticleCreated) == 0

        dispatcher.register(RawArticleCollected, MagicMock())
        assert dispatcher.handler_count(RawArticleCollected) == 1
        assert dispatcher.handler_count(ArticleCreated) == 0
