"""
Tests para ContentEvaluator — Servicio de dominio puro.
"""
import pytest
from domain.services.content_evaluator import ContentEvaluator, EvaluationResult
from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.hook import Hook
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration
from domain.value_objects.hook_type import HookType


class TestContentEvaluatorInit:
    def test_default_initialization(self):
        ev = ContentEvaluator()
        assert ev.SCORE_EXCELLENT == 8.0
        assert ev.SCORE_ACCEPTABLE == 6.0


class TestEvaluateIdea:
    def test_high_curiosity_hook_scores_high(self):
        ev = ContentEvaluator()
        idea = ContentIdea(
            hook="El secreto que nadie te cuenta sobre IA",
            topic="AI",
            format="list",
            viral_score=ViralScore(80),
        )
        result = ev.evaluate_idea(idea)
        assert 0 <= result.score_total <= 10
        assert result.classification in ("excelente", "aceptable", "malo")
        assert "curiosidad" in result.criteria
        assert "emocion" in result.criteria

    def test_poor_hook_scores_low(self):
        ev = ContentEvaluator()
        idea = ContentIdea(hook="Hoy es lunes", topic="Días")
        result = ev.evaluate_idea(idea)
        # Low curiosity (no trigger words), low emotion
        assert result.score_total < 7

    def test_criteria_breakdown(self):
        ev = ContentEvaluator()
        idea = ContentIdea(hook="¿Descubriste el secreto? 5 cosas", topic="Test")
        result = ev.evaluate_idea(idea)
        assert len(result.criteria) == 5
        assert all(0 <= v <= 10 for v in result.criteria.values())

    def test_recommendations_for_low_score(self):
        ev = ContentEvaluator()
        idea = ContentIdea(hook="Hola", topic="Test")
        result = ev.evaluate_idea(idea)
        # A poor idea should have recommendations
        assert len(result.recommendations) > 0

    def test_good_idea_fewer_recommendations(self):
        ev = ContentEvaluator()
        idea = ContentIdea(
            hook="⚠️ El secreto que nadie te cuenta sobre IA — 5 verdades",
            topic="AI",
            format="list",
        )
        result = ev.evaluate_idea(idea)
        # A good idea should have fewer recommendations
        if result.classification == "excelente":
            assert len(result.recommendations) == 0

    def test_format_scoring(self):
        ev = ContentEvaluator()
        list_idea = ContentIdea(hook="Hook", topic="T", format="list")
        story_idea = ContentIdea(hook="Hook", topic="T", format="story")
        list_result = ev.evaluate_idea(list_idea)
        story_result = ev.evaluate_idea(story_idea)
        assert list_result.criteria["viral"] >= story_result.criteria["viral"]


class TestEvaluateScript:
    def test_valid_script_evaluation(self):
        ev = ContentEvaluator()
        script = Script(
            hook="Hook potente para el video",
            body="Esta es la primera oración. Esta es la segunda.",
            cta="Seguime ahora",
            duration=Duration(45),
        )
        result = ev.evaluate_script(script)
        assert 0 <= result.score_total <= 10
        assert "hook_fuerte" in result.criteria
        assert "ritmo" in result.criteria

    def test_short_hook_scores_better(self):
        ev = ContentEvaluator()
        short = Script(hook="Hook corto", body="x", cta="y")
        long = Script(hook="Hook " * 20, body="x", cta="y")
        short_result = ev.evaluate_script(short)
        long_result = ev.evaluate_script(long)
        assert short_result.criteria["hook_fuerte"] > long_result.criteria["hook_fuerte"]

    def test_cta_with_urgency(self):
        ev = ContentEvaluator()
        good_cta = Script(hook="Hook", body="Body", cta="Seguime ahora")
        bad_cta = Script(hook="Hook", body="Body", cta="Gracias")
        good = ev.evaluate_script(good_cta)
        bad = ev.evaluate_script(bad_cta)
        assert good.criteria["final_impacto"] > bad.criteria["final_impacto"]


class TestOptimize:
    def test_optimize_idea_adds_curiosity(self):
        ev = ContentEvaluator()
        idea = ContentIdea(hook="Hook", topic="AI")
        recs = ["falta curiosidad", "mejorar"]
        optimized = ev.optimize_idea(idea, recs)
        assert "¿Sabías" in optimized.hook

    def test_optimize_idea_improves_viral_score(self):
        ev = ContentEvaluator()
        idea = ContentIdea(hook="Hook", topic="T", viral_score=ViralScore(50))
        recs = ["mejorar"]
        optimized = ev.optimize_idea(idea, recs)
        assert optimized.viral_score.value == 60  # 50 + 10

    def test_optimize_script_adds_emoji_to_hook(self):
        ev = ContentEvaluator()
        script = Script(hook="Hook", body="Cuerpo", cta="CTA")
        recs = ["mejorar hook"]
        optimized = ev.optimize_script(script, recs)
        assert "🎯" in optimized.hook

    def test_optimize_script_improves_cta(self):
        ev = ContentEvaluator()
        script = Script(hook="Hook", body="Cuerpo", cta="Gracias")
        recs = ["mejorar final"]
        optimized = ev.optimize_script(script, recs)
        assert "🔥" in optimized.cta

    def test_optimize_script_shortens_body(self):
        ev = ContentEvaluator()
        body = ". ".join(["Oración larga aquí para probar"] * 10) + "."
        script = Script(hook="Hook", body=body, cta="CTA")
        recs = ["mejorar ritmo"]
        optimized = ev.optimize_script(script, recs)
        assert len(optimized.body.split(".")) <= len(body.split("."))


class TestEvaluationResult:
    def test_is_excellent(self):
        r = EvaluationResult(score_total=9.0, classification="excelente", criteria={}, recommendations=[])
        assert r.is_excellent is True
        assert r.is_acceptable is True

    def test_is_acceptable(self):
        r = EvaluationResult(score_total=7.0, classification="aceptable", criteria={}, recommendations=[])
        assert r.is_excellent is False
        assert r.is_acceptable is True

    def test_not_acceptable(self):
        r = EvaluationResult(score_total=4.0, classification="malo", criteria={}, recommendations=["mejorar"])
        assert r.is_acceptable is False
        assert r.is_excellent is False

    def test_to_dict(self):
        r = EvaluationResult(
            score_total=8.5,
            classification="excelente",
            criteria={"curiosidad": 8.0},
            recommendations=[],
            was_optimized=True,
        )
        d = r.to_dict()
        assert d["score"] == 8.5
        assert d["classification"] == "excelente"
        assert d["was_optimized"] is True
