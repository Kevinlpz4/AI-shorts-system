"""Tests for LearningDomainError and LearningErrorCode."""
import pytest
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.exceptions import LearningDomainError
from foundation.errors import DomainError


class TestLearningErrorCode:
    def test_all_codes_exist(self):
        expected = {
            "FEEDBACK_NOT_FOUND", "SIGNAL_NOT_FOUND", "SOURCE_QUALITY_NOT_FOUND",
            "MODEL_NOT_FOUND", "DUPLICATE_FEEDBACK", "INVALID_DECISION_TYPE",
            "INVALID_CONFIDENCE", "INVALID_WEIGHTS", "WINDOW_INVALID",
            "INSUFFICIENT_DATA", "SIGNAL_ALREADY_FINALIZED",
        }
        assert {c.value for c in LearningErrorCode} == expected

    def test_str_enum(self):
        assert LearningErrorCode.FEEDBACK_NOT_FOUND == "FEEDBACK_NOT_FOUND"


class TestLearningDomainError:
    def test_inherits_domain_error(self):
        assert issubclass(LearningDomainError, DomainError)

    def test_inherits_value_error(self):
        assert issubclass(LearningDomainError, ValueError)

    def test_has_code(self):
        err = LearningDomainError("test")
        assert err.code == "LEARNING_ERROR"

    def test_str_representation(self):
        err = LearningDomainError("something went wrong")
        assert "something went wrong" in str(err)

    def test_raise_and_catch(self):
        with pytest.raises(LearningDomainError):
            raise LearningDomainError("test error")

    def test_catch_as_domain_error(self):
        with pytest.raises(DomainError):
            raise LearningDomainError("test")

    def test_catch_as_value_error(self):
        with pytest.raises(ValueError):
            raise LearningDomainError("test")
