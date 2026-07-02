"""
Tests del Error System (Sprint 2.5).

Cubre: FoundationError, DomainError, ApplicationError, InfrastructureError,
Error.from_exception(), FoundationError.to_error().

~25 tests organizados en 8 grupos:

    - TestFoundationError      (5) — FoundationError base
    - TestDomainError          (3) — DomainError
    - TestApplicationError     (3) — ApplicationError
    - TestInfrastructureError  (3) — InfrastructureError
    - TestJerarquia            (3) — Jerarquía y isinstance
    - TestToError              (4) — FoundationError.to_error()
    - TestFromException        (4) — Error.from_exception()
    - TestRegresion            (3) — No rompe Result existente
"""

from __future__ import annotations

import pytest

from foundation import (
    ApplicationError,
    DomainError,
    Error,
    ErrorCode,
    Failure,
    FoundationError,
    InfrastructureError,
    Result,
    Success,
)


# ══════════════════════════════════════════════
# 1. FoundationError — Creación y propiedades
# ══════════════════════════════════════════════


class TestFoundationError:
    """Test de FoundationError base."""

    def test_is_exception(self):
        """FoundationError hereda de Exception."""
        err = FoundationError("test")
        assert isinstance(err, Exception)
        assert isinstance(err, BaseException)

    def test_default_code(self):
        """code default es FOUNDATION_ERROR."""
        err = FoundationError()
        assert err.code == "FOUNDATION_ERROR"

    def test_message_and_detail(self):
        """message y detail se setean en constructor."""
        err = FoundationError("public message", detail="debug info")
        assert err.message == "public message"
        assert err.detail == "debug info"

    def test_message_default_empty(self):
        """message default es string vacío."""
        err = FoundationError()
        assert err.message == ""

    def test_to_dict(self):
        """to_dict() serializa correctamente."""
        err = FoundationError("fail", detail="because")
        d = err.to_dict()
        assert d == {
            "error": "FOUNDATION_ERROR",
            "message": "fail",
            "detail": "because",
        }


# ══════════════════════════════════════════════
# 2. DomainError
# ══════════════════════════════════════════════


class TestDomainError:
    """Test de DomainError."""

    def test_domain_error_code(self):
        """DomainError.code es DOMAIN_ERROR."""
        err = DomainError("violated business rule")
        assert err.code == "DOMAIN_ERROR"

    def test_is_foundation_error(self):
        """DomainError es FoundationError."""
        err = DomainError()
        assert isinstance(err, FoundationError)

    def test_is_exception(self):
        """DomainError es Exception."""
        err = DomainError()
        assert isinstance(err, Exception)


# ══════════════════════════════════════════════
# 3. ApplicationError
# ══════════════════════════════════════════════


class TestApplicationError:
    """Test de ApplicationError."""

    def test_application_error_code(self):
        """ApplicationError.code es APPLICATION_ERROR."""
        err = ApplicationError("invalid command")
        assert err.code == "APPLICATION_ERROR"

    def test_is_foundation_error(self):
        """ApplicationError es FoundationError."""
        err = ApplicationError()
        assert isinstance(err, FoundationError)

    def test_is_exception(self):
        """ApplicationError es Exception."""
        err = ApplicationError()
        assert isinstance(err, Exception)


# ══════════════════════════════════════════════
# 4. InfrastructureError
# ══════════════════════════════════════════════


class TestInfrastructureError:
    """Test de InfrastructureError."""

    def test_infrastructure_error_code(self):
        """InfrastructureError.code es INFRASTRUCTURE_ERROR."""
        err = InfrastructureError("db connection failed")
        assert err.code == "INFRASTRUCTURE_ERROR"

    def test_is_foundation_error(self):
        """InfrastructureError es FoundationError."""
        err = InfrastructureError()
        assert isinstance(err, FoundationError)

    def test_is_exception(self):
        """InfrastructureError es Exception."""
        err = InfrastructureError()
        assert isinstance(err, Exception)


# ══════════════════════════════════════════════
# 5. Jerarquía — isinstance checks
# ══════════════════════════════════════════════


class TestJerarquia:
    """Test de relaciones de herencia entre los tipos de error."""

    def test_domain_not_application(self):
        """DomainError NO es ApplicationError."""
        err = DomainError()
        assert not isinstance(err, ApplicationError)

    def test_application_not_infrastructure(self):
        """ApplicationError NO es InfrastructureError."""
        err = ApplicationError()
        assert not isinstance(err, InfrastructureError)

    def test_infrastructure_not_domain(self):
        """InfrastructureError NO es DomainError."""
        err = InfrastructureError()
        assert not isinstance(err, DomainError)


# ══════════════════════════════════════════════
# 6. FoundationError.to_error()
# ══════════════════════════════════════════════


class TestToError:
    """Test de FoundationError.to_error() → Error dataclass."""

    def test_foundation_error_to_error(self):
        """to_error() retorna un Error dataclass."""
        exc = FoundationError("fail")
        err = exc.to_error()
        assert isinstance(err, Error)

    def test_preserves_code_in_message(self):
        """to_error() preserva código de excepción en mensaje."""
        exc = DomainError("rule violation")
        err = exc.to_error()
        assert "[DOMAIN_ERROR]" in err.message

    def test_preserves_detail(self):
        """to_error() preserva detail."""
        exc = FoundationError("fail", detail="debug info")
        err = exc.to_error()
        assert err.detail == "debug info"

    def test_empty_message_strips_brackets(self):
        """to_error() con message vacío no deja colgando [CODE]."""
        exc = FoundationError()
        err = exc.to_error()
        # message debería ser "[FOUNDATION_ERROR] " → .strip() → "[FOUNDATION_ERROR]"
        assert err.message == "[FOUNDATION_ERROR]"


# ══════════════════════════════════════════════
# 7. Error.from_exception()
# ══════════════════════════════════════════════


class TestFromException:
    """Test de Error.from_exception()."""

    def test_from_domain_error(self):
        """Error.from_exception(DomainError) retorna Error."""
        exc = DomainError("rule violation", detail="entity id 123")
        err = Error.from_exception(exc)
        assert isinstance(err, Error)
        assert "[DOMAIN_ERROR]" in err.message
        assert err.detail == "entity id 123"

    def test_from_application_error(self):
        """Error.from_exception(ApplicationError) retorna Error."""
        exc = ApplicationError("invalid")
        err = Error.from_exception(exc)
        assert isinstance(err, Error)
        assert "[APPLICATION_ERROR]" in err.message

    def test_from_infrastructure_error(self):
        """Error.from_exception(InfrastructureError) retorna Error."""
        exc = InfrastructureError("timeout")
        err = Error.from_exception(exc)
        assert isinstance(err, Error)
        assert "[INFRASTRUCTURE_ERROR]" in err.message

    def test_from_non_foundation_exception(self):
        """Error.from_exception con Exception genérica usa str()."""
        exc = ValueError("something bad")
        err = Error.from_exception(exc)
        assert isinstance(err, Error)
        assert err.code == ErrorCode.UNKNOWN
        assert err.message == "something bad"


# ══════════════════════════════════════════════
# 8. No regresión — Result existente no se rompe
# ══════════════════════════════════════════════


class TestRegresion:
    """Test que verifican que Result existente NO se modificó."""

    def test_success_still_works(self):
        """Result.success() funciona como antes."""
        r = Result.success(42)
        assert r.is_success is True
        assert r.is_failure is False
        assert r.unwrap() == 42

    def test_failure_still_works(self):
        """Result.failure() funciona como antes."""
        r: Result[int] = Result.failure(Error(code=ErrorCode.UNKNOWN, message="fail"))
        assert r.is_success is False
        assert r.is_failure is True
        with pytest.raises(RuntimeError):
            r.unwrap()

    def test_from_exception_does_not_affect_pattern_matching(self):
        """Error.from_exception no altera el pattern matching de Result."""
        exc = DomainError("test")
        err = Error.from_exception(exc)
        f: Result[str] = Result.failure(err)
        matched = False
        match f:
            case Failure(error=e):
                assert isinstance(e, Error)
                matched = True
            case Success():
                pytest.fail("Should not match Success")
        assert matched
