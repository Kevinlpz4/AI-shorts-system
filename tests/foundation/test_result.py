"""
Tests del Result Pattern (Sprint 2.3).

Cubre: Result[T], Success[T], Failure[T], Error, ErrorCode.

~60 tests organizados en 11 grupos:

    - TestCreacion        (6) — Construcción
    - TestInspeccion      (8) — Propiedades de inspección
    - TestIgualdad        (6) — Igualdad estructural
    - TestHash            (3) — Hash
    - TestInmutabilidad   (3) — Inmutabilidad (frozen)
    - TestUnwrap          (4) — unwrap()
    - TestError          (11) — ErrorCode + Error
    - TestPatternMatching (3) — Pattern matching
    - TestSerializacion   (4) — deepcopy y pickle
    - TestEdgeCases       (8) — Casos borde
    - TestCrossComponent  (4) — Cross-component
"""

from __future__ import annotations

import copy
import pickle
from dataclasses import FrozenInstanceError

import pytest

from foundation import Error, ErrorCode, Failure, Result, Success


# =============================================================================
# Grupo 1 — Construcción (~6 tests)
# =============================================================================


class TestCreacion:
    """Test de construcción de Result[T]."""

    def test_success_creation(self):
        """Result.success(value) crea un Success."""
        result = Result.success(42)
        assert isinstance(result, Success)
        assert result.value == 42

    def test_failure_creation(self):
        """Result.failure(error) crea un Failure."""
        error = Error(code=ErrorCode.UNKNOWN, message="Not found")
        result: Result[int] = Result.failure(error)
        assert isinstance(result, Failure)
        assert result.error == error

    def test_success_type_retained(self):
        """El tipo genérico T se conserva en Success[T]."""
        result = Result.success("hello")
        assert isinstance(result, Success)

    def test_success_with_none(self):
        """Success con valor None."""
        result = Result.success(None)
        assert isinstance(result, Success)
        assert result.value is None

    def test_success_with_false(self):
        """Success con valor False (falsy pero válido)."""
        result = Result.success(False)
        assert isinstance(result, Success)
        assert result.value is False

    def test_success_with_zero(self):
        """Success con valor 0 (falsy pero válido)."""
        result = Result.success(0)
        assert isinstance(result, Success)
        assert result.value == 0


# =============================================================================
# Grupo 2 — Inspección (~8 tests)
# =============================================================================


class TestInspeccion:
    """Test de propiedades de inspección (is_success, is_failure, value, error)."""

    def test_is_success_on_success(self):
        """is_success es True en Success."""
        result = Result.success(42)
        assert result.is_success is True

    def test_is_success_on_failure(self):
        """is_success es False en Failure."""
        error = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(error)
        assert result.is_success is False

    def test_is_failure_on_success(self):
        """is_failure es False en Success."""
        result = Result.success(42)
        assert result.is_failure is False

    def test_is_failure_on_failure(self):
        """is_failure es True en Failure."""
        error = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(error)
        assert result.is_failure is True

    def test_success_value_access(self):
        """Acceder a .value en Success retorna el valor."""
        result = Result.success(42)
        assert result.value == 42

    def test_failure_error_access(self):
        """Acceder a .error en Failure retorna el error."""
        err = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(err)
        assert result.error == err

    def test_success_error_raises(self):
        """Acceder a .error en Success lanza RuntimeError."""
        result = Result.success(42)
        with pytest.raises(RuntimeError, match="Cannot access error"):
            _ = result.error  # type: ignore[attr-defined]

    def test_failure_value_raises(self):
        """Acceder a .value en Failure lanza RuntimeError."""
        error = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(error)
        with pytest.raises(RuntimeError, match="Cannot access value"):
            _ = result.value  # type: ignore[attr-defined]


# =============================================================================
# Grupo 3 — Igualdad (~6 tests)
# =============================================================================


class TestIgualdad:
    """Test de igualdad estructural."""

    def test_equal_success(self):
        """Dos Success con mismo valor son iguales."""
        a = Success(value=42)
        b = Success(value=42)
        assert a == b

    def test_unequal_success(self):
        """Dos Success con diferente valor NO son iguales."""
        a = Success(value=42)
        b = Success(value=99)
        assert a != b

    def test_equal_failure(self):
        """Dos Failure con mismo error son iguales."""
        err = Error(code=ErrorCode.UNKNOWN, message="x")
        a = Failure(error=err)
        b = Failure(error=err)
        assert a == b

    def test_unequal_failure(self):
        """Dos Failure con diferente error NO son iguales."""
        a = Failure(error=Error(code=ErrorCode.UNKNOWN, message="x"))
        b = Failure(error=Error(code=ErrorCode.UNKNOWN, message="y"))
        assert a != b

    def test_success_not_equal_failure(self):
        """Success y Failure nunca son iguales."""
        s = Result.success(42)
        f: Result[int] = Result.failure(Error(code=ErrorCode.UNKNOWN, message="err"))
        assert s != f

    def test_success_same_hash(self):
        """Success con mismo valor tienen mismo hash."""
        a = Success(value=42)
        b = Success(value=42)
        assert hash(a) == hash(b)


# =============================================================================
# Grupo 4 — Hash (~3 tests)
# =============================================================================


class TestHash:
    """Test de hash."""

    def test_hash_equal_success(self):
        """Dos Success iguales tienen el mismo hash."""
        a = Success(value=42)
        b = Success(value=42)
        assert hash(a) == hash(b)

    def test_hash_different_success(self):
        """Dos Success con distinto valor tienen distinto hash."""
        a = Success(value=42)
        b = Success(value=99)
        assert hash(a) != hash(b)

    def test_hash_success_and_failure(self):
        """Success y Failure tienen distinto hash."""
        s = Success(value=42)
        f = Failure(error=Error(code=ErrorCode.UNKNOWN, message="x"))
        assert hash(s) != hash(f)


# =============================================================================
# Grupo 5 — Inmutabilidad (~3 tests)
# =============================================================================


class TestInmutabilidad:
    """Test de inmutabilidad (frozen=True)."""

    def test_success_frozen(self):
        """No se puede mutar un Success."""
        s = Success(value=42)
        with pytest.raises(FrozenInstanceError):
            s.value = 99  # type: ignore[misc]

    def test_failure_frozen(self):
        """No se puede mutar un Failure."""
        err = Error(code=ErrorCode.UNKNOWN, message="x")
        f = Failure(error=err)
        with pytest.raises(FrozenInstanceError):
            f.error = Error(code=ErrorCode.UNKNOWN, message="y")  # type: ignore[misc]

    def test_success_and_failure_are_types(self):
        """Success y Failure son clases distintas."""
        s = Success(value=42)
        f = Failure(error=Error(code=ErrorCode.UNKNOWN, message="x"))
        assert type(s) is not type(f)


# =============================================================================
# Grupo 6 — unwrap (~4 tests)
# =============================================================================


class TestUnwrap:
    """Test del método unwrap()."""

    def test_unwrap_success(self):
        """unwrap() retorna el valor en Success."""
        result = Result.success(42)
        assert result.unwrap() == 42

    def test_unwrap_failure_raises(self):
        """unwrap() lanza RuntimeError en Failure."""
        error = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(error)
        with pytest.raises(RuntimeError, match="Cannot unwrap"):
            result.unwrap()

    def test_unwrap_with_none(self):
        """unwrap() en Success con None retorna None."""
        result = Result.success(None)
        assert result.unwrap() is None

    def test_unwrap_error_message(self):
        """El RuntimeError de unwrap() incluye str(error)."""
        error = Error(code=ErrorCode.UNKNOWN, message="Something failed")
        result: Result[int] = Result.failure(error)
        with pytest.raises(RuntimeError) as exc:
            result.unwrap()
        assert "Cannot unwrap Failure:" in str(exc.value)
        assert "[UNKNOWN] Something failed" in str(exc.value)


# =============================================================================
# Grupo 7 — ErrorCode + Error (~11 tests)
# =============================================================================


class TestError:
    """Test de ErrorCode y Error."""

    def test_errorcode_unknown_default(self):
        """ErrorCode.UNKNOWN existe y vale 'UNKNOWN'."""
        assert ErrorCode.UNKNOWN == "UNKNOWN"

    def test_error_creation(self):
        """Se puede crear un Error con code y message."""
        err = Error(code=ErrorCode.UNKNOWN, message="Topic not found")
        assert err.code is ErrorCode.UNKNOWN
        assert err.message == "Topic not found"

    def test_error_default_code(self):
        """Si no se pasa code, se usa ErrorCode.UNKNOWN."""
        err = Error(message="something")
        assert err.code is ErrorCode.UNKNOWN

    def test_error_with_detail(self):
        """Error admite detail opcional."""
        err = Error(
            code=ErrorCode.UNKNOWN,
            message="Invalid data",
            detail="Field 'name' is required",
        )
        assert err.detail == "Field 'name' is required"

    def test_error_detail_defaults_none(self):
        """detail default es None."""
        err = Error(code=ErrorCode.UNKNOWN, message="y")
        assert err.detail is None

    def test_error_str_no_detail(self):
        """__str__ sin detail retorna '[CODE] message'."""
        err = Error(code=ErrorCode.UNKNOWN, message="Something went wrong")
        assert str(err) == "[UNKNOWN] Something went wrong"

    def test_error_str_with_detail(self):
        """__str__ con detail retorna '[CODE] message: detail'."""
        err = Error(
            code=ErrorCode.UNKNOWN,
            message="Invalid data",
            detail="Field 'name' is required",
        )
        assert str(err) == "[UNKNOWN] Invalid data: Field 'name' is required"

    def test_error_not_exception(self):
        """Error NO es una excepción."""
        err = Error(code=ErrorCode.UNKNOWN, message="")
        assert not isinstance(err, Exception)
        assert not isinstance(err, BaseException)

    def test_error_str_empty_message(self):
        """__str__ con message vacío."""
        err = Error(code=ErrorCode.UNKNOWN)
        assert str(err) == "[UNKNOWN] "

    def test_error_structural_equality(self):
        """Dos Error con mismos atributos son iguales."""
        a = Error(code=ErrorCode.UNKNOWN, message="test", detail="info")
        b = Error(code=ErrorCode.UNKNOWN, message="test", detail="info")
        assert a == b
        assert hash(a) == hash(b)

    def test_error_frozen(self):
        """Error es frozen (inmutable)."""
        err = Error(code=ErrorCode.UNKNOWN, message="Y")
        with pytest.raises(FrozenInstanceError):
            err.code = ErrorCode.UNKNOWN  # type: ignore[misc]


# =============================================================================
# Grupo 8 — Pattern Matching (~3 tests)
# =============================================================================


class TestPatternMatching:
    """Test de pattern matching con Result[T]."""

    def test_match_success(self):
        """match reconoce Success(value=v)."""
        result = Result.success(42)
        matched = False
        match result:
            case Success(value=v):
                assert v == 42
                matched = True
            case Failure():
                pytest.fail("Should not match Failure")
        assert matched, "Success pattern did not match"

    def test_match_failure(self):
        """match reconoce Failure(error=e)."""
        err = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(err)
        matched = False
        match result:
            case Success():
                pytest.fail("Should not match Success")
            case Failure(error=e):
                assert e == err
                matched = True
        assert matched, "Failure pattern did not match"

    def test_match_exhaustive(self):
        """Ambos casos (Success y Failure) se pueden cubrir exhaustivamente."""
        results: list[Result[int]] = [
            Result.success(1),
            Result.failure(Error(code=ErrorCode.UNKNOWN, message="e")),
        ]
        values: list[int | str] = []
        for r in results:
            match r:
                case Success(value=v):
                    values.append(v)
                case Failure():
                    values.append("error")
        assert values == [1, "error"]


# =============================================================================
# Grupo 9 — Serialización (~4 tests)
# =============================================================================


class TestSerializacion:
    """Test de serialización: deepcopy y pickle."""

    def test_deepcopy_success(self):
        """deepcopy de Success produce copia independiente."""
        original = Result.success([1, 2, 3])
        copied = copy.deepcopy(original)
        assert copied == original
        assert copied.value is not original.value  # different object

    def test_deepcopy_failure(self):
        """deepcopy de Failure produce copia independiente."""
        err = Error(code=ErrorCode.UNKNOWN, message="test")
        original: Result[int] = Result.failure(err)
        copied = copy.deepcopy(original)
        assert copied == original
        assert copied.error is not original.error  # different object

    def test_pickle_success(self):
        """Success es pickeable."""
        original = Result.success(42)
        data = pickle.dumps(original)
        restored = pickle.loads(data)
        assert restored == original
        assert restored.unwrap() == 42

    def test_pickle_failure(self):
        """Failure es pickeable."""
        err = Error(code=ErrorCode.UNKNOWN, message="test error")
        original: Result[int] = Result.failure(err)
        data = pickle.dumps(original)
        restored = pickle.loads(data)
        assert restored == original
        assert restored.is_failure is True
        assert restored.error == err


# =============================================================================
# Grupo 10 — Edge Cases (~8 tests)
# =============================================================================


class TestEdgeCases:
    """Test de casos borde con tipos y estructuras de datos."""

    def test_success_with_list_value(self):
        """Success con lista como valor."""
        result = Result.success([1, 2, 3])
        assert result.is_success is True
        assert result.value == [1, 2, 3]

    def test_success_with_empty_list(self):
        """Success con lista vacía como valor."""
        result = Result.success([])
        assert result.is_success is True
        assert result.value == []

    def test_success_with_dict_value(self):
        """Success con dict como valor."""
        result = Result.success({"a": 1})
        assert result.is_success is True
        assert result.value == {"a": 1}

    def test_success_with_empty_dict(self):
        """Success con dict vacío como valor."""
        result = Result.success({})
        assert result.is_success is True
        assert result.value == {}

    def test_failure_generic_type_int(self):
        """Failure tipado como Result[int]."""
        err = Error(code=ErrorCode.UNKNOWN, message="err")
        result: Result[int] = Result.failure(err)
        assert isinstance(result, Failure)

    def test_failure_generic_type_str(self):
        """Failure tipado como Result[str]."""
        err = Error(code=ErrorCode.UNKNOWN, message="err")
        result: Result[str] = Result.failure(err)
        assert isinstance(result, Failure)

    def test_result_in_set(self):
        """Result se puede usar en sets (hashable)."""
        s1 = Success(value=1)
        s2 = Success(value=1)
        s3 = Success(value=2)
        result_set = {s1, s2, s3}
        assert len(result_set) == 2  # s1 y s2 son iguales

    def test_result_in_dict(self):
        """Result se puede usar como key de dict."""
        key = Success(value="k")
        d = {key: "value"}
        assert d[Success(value="k")] == "value"


# =============================================================================
# Grupo 11 — Cross-component (~4 tests)
# =============================================================================


class TestCrossComponent:
    """Test cross-component: interacción entre tipos."""

    def test_success_vs_failure_never_equal(self):
        """Success y Failure nunca son iguales, incluso con mismo contenido."""
        s = Result.success(42)
        f: Result[int] = Result.failure(Error(code=ErrorCode.UNKNOWN, message="42"))
        assert s != f

    def test_result_with_complex_types(self):
        """Result con tipos complejos (dict anidado)."""
        result = Result.success({"key": [1, 2, 3]})
        assert result.is_success is True
        assert result.value == {"key": [1, 2, 3]}

    def test_result_of_result_nested(self):
        """Result anidado (Result de Result)."""
        inner = Result.success(42)
        outer = Result.success(inner)
        assert outer.is_success is True
        assert outer.value == inner
        assert outer.value.is_success is True

    def test_result_is_not_exception(self):
        """Result no es una excepción."""
        s = Result.success(42)
        err = Error(code=ErrorCode.UNKNOWN, message="")
        f: Result[int] = Result.failure(err)
        assert not isinstance(s, BaseException)
        assert not isinstance(f, BaseException)
