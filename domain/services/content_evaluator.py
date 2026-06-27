from typing import Optional

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.entities.hook import Hook
from domain.value_objects.viral_score import ViralScore


class EvaluationResult:
    """Resultado de evaluación de contenido."""
    def __init__(
        self,
        score_total: float,
        classification: str,
        criteria: dict[str, float],
        recommendations: list[str],
        was_optimized: bool = False,
    ):
        self.score_total = score_total
        self.classification = classification
        self.criteria = criteria
        self.recommendations = recommendations
        self.was_optimized = was_optimized

    @property
    def is_excellent(self) -> bool:
        return self.classification == "excelente"

    @property
    def is_acceptable(self) -> bool:
        return self.classification in ("excelente", "aceptable")

    def to_dict(self) -> dict:
        return {
            "score": round(self.score_total, 1),
            "classification": self.classification,
            "criteria": self.criteria,
            "recommendations": self.recommendations,
            "was_optimized": self.was_optimized,
        }


class ContentEvaluator:
    """
    Servicio de dominio: Evalúa y optimiza contenido.
    
    Totalmente puro — sin llamadas a IA.
    Solo reglas de negocio sobre estructura del texto.
    
    Criterios de evaluación (0-10):
    - curiosidad: ¿El hook genera intriga?
    - emocion: ¿Tiene impacto emocional?
    - claridad: ¿Es fácil de entender?
    - viral: ¿El formato es viral?
    - hook_fuerza: ¿El hook capta atención?
    """
    
    SCORE_EXCELLENT = 8.0
    SCORE_ACCEPTABLE = 6.0

    # Palabras que generan curiosidad
    CURIOSITY_WORDS = {
        "secreto", "descubrir", "nadie", "verdad", "increíble",
        "sorprendente", "no vas a creer", "esto cambió",
        "error", "peligro", "hack", "alerta", "urgente",
    }

    # Palabras con carga emocional
    EMOTIONAL_WORDS = {
        "miedo", "terror", "peligro", "asombroso", "revolucionario",
        "destruye", "cambia todo", "nunca más", "fatal", "importante",
    }

    # Score base por formato
    FORMAT_SCORES = {
        "list": 8.5,
        "fact": 8.0,
        "reaction": 7.5,
        "tutorial": 7.0,
        "story": 6.5,
        "comparison": 7.0,
        "debunk": 7.5,
    }

    def evaluate_idea(self, idea: ContentIdea) -> EvaluationResult:
        """Evalúa una idea según criterios de viralidad."""
        criteria = {
            "curiosidad": self._eval_curiosity(idea.hook),
            "emocion": self._eval_emotion(idea.hook),
            "claridad": self._eval_clarity(idea.hook),
            "viral": self._eval_viral_format(idea.format),
            "hook_fuerza": self._eval_hook_strength(idea.hook),
        }
        return self._build_result(criteria)

    def evaluate_script(self, script: Script) -> EvaluationResult:
        """Evalúa un script según criterios de retención."""
        criteria = {
            "hook_fuerte": self._eval_hook_script(script.hook),
            "ritmo": self._eval_pace(script.body),
            "claridad_narrativa": self._eval_narrative_clarity(script.body),
            "final_impacto": self._eval_cta(script.cta),
            "duracion": self._eval_duration(int(script.duration)),
        }
        return self._build_result(criteria)

    def optimize_idea(self, idea: ContentIdea, recommendations: list[str]) -> ContentIdea:
        """Crea una nueva idea optimizada."""
        hook = idea.hook
        recs = " ".join(recommendations).lower()

        if "curiosidad" in recs:
            hook = f"¿Sabías esto sobre {idea.topic}?"
        if "emocion" in recs:
            hook = f"⚠️ {hook} — Esto cambia todo"
        if "claridad" in recs and len(hook) > 50:
            hook = " ".join(hook.split()[:7]) + "..."

        return ContentIdea(
            hook=hook,
            topic=idea.topic,
            description=idea.description,
            target_audience=idea.target_audience,
            format=idea.format,
            viral_score=idea.viral_score.improve(10),
            keywords=idea.keywords,
            trend_id=idea.trend_id,
        )

    def optimize_script(self, script: Script, recommendations: list[str]) -> Script:
        """Crea un nuevo script optimizado."""
        hook = script.hook
        body = script.body
        cta = script.cta
        recs = " ".join(recommendations).lower()

        if "hook" in recs:
            hook = f"🎯 {hook}"
        if "ritmo" in recs:
            sentences = [s.strip() for s in body.split(".") if len(s.strip()) > 10]
            body = ". ".join(sentences[:4]) + "."
        if "final" in recs:
            cta = f"🔥 {cta} ¡Seguime para más!"

        return Script(
            idea_id=script.idea_id,
            topic=script.topic,
            hook=hook,
            body=body,
            cta=cta,
            duration=script.duration,
            tone=script.tone,
            format=script.format,
        )

    # ── Criterios de evaluación privados ──

    def _eval_curiosity(self, text: str) -> float:
        """Evalúa nivel de curiosidad (0-10)."""
        text_lower = text.lower()
        score = 5.0
        score += sum(1.0 for w in self.CURIOSITY_WORDS if w in text_lower)
        if "?" in text:
            score += 1.5
        if any(c.isdigit() for c in text):
            score += 1.0
        return min(10, score)

    def _eval_emotion(self, text: str) -> float:
        """Evalúa impacto emocional (0-10)."""
        text_lower = text.lower()
        score = 5.0
        score += sum(1.0 for w in self.EMOTIONAL_WORDS if w in text_lower)
        return min(10, score)

    def _eval_clarity(self, text: str) -> float:
        """Evalúa claridad (0-10)."""
        length = len(text)
        if length > 100:
            return 5.0
        if length > 60:
            return 7.0
        if length > 30:
            return 8.5
        return 9.0

    def _eval_viral_format(self, format_type: str) -> float:
        """Evalúa potencial viral del formato."""
        return self.FORMAT_SCORES.get(format_type, 6.0)

    def _eval_hook_strength(self, text: str) -> float:
        """Evalúa fuerza del hook (0-10)."""
        strong_starters = {"¿sabías", "descubre", "atención", "importante",
                          "esto", "nunca", "secret"}
        text_lower = text.lower()
        score = 5.0
        score += sum(1.0 for w in strong_starters if text_lower.startswith(w))
        score += sum(1.0 for w in strong_starters if w in text_lower)
        return min(10, score)

    def _eval_hook_script(self, hook: str) -> float:
        """Evalúa fortaleza del hook en script."""
        length = len(hook)
        if length < 30:
            return 9.0
        if length < 50:
            return 7.5
        if length < 80:
            return 6.0
        return 4.0

    def _eval_pace(self, body: str) -> float:
        """Evalúa ritmo (oraciones cortas = mejor)."""
        sentences = [s for s in body.split(".") if s.strip()]
        if len(sentences) < 3:
            return 5.0
        avg = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg < 10:
            return 9.0
        if avg < 15:
            return 7.5
        if avg < 20:
            return 6.0
        return 4.5

    def _eval_narrative_clarity(self, text: str) -> float:
        """Evalúa claridad narrativa."""
        sentences = [s for s in text.split(".") if s.strip()]
        if not sentences:
            return 5.0
        avg = sum(len(s) for s in sentences) / len(sentences)
        if avg < 50:
            return 9.0
        if avg < 80:
            return 7.5
        if avg < 120:
            return 6.0
        return 4.5

    def _eval_cta(self, cta: str) -> float:
        """Evalúa calidad del CTA."""
        cta_lower = cta.lower()
        if "ahora" in cta_lower or "ya" in cta_lower:
            return 8.5
        if "sígueme" in cta_lower or "like" in cta_lower:
            return 7.5
        return 6.0

    def _eval_duration(self, seconds: int) -> float:
        """Evalúa duración."""
        if 30 <= seconds <= 60:
            return 9.0
        if seconds < 30:
            return 7.0
        if seconds < 90:
            return 6.0
        return 4.0

    def _build_result(self, criteria: dict[str, float]) -> EvaluationResult:
        """Construye resultado de evaluación."""
        score = sum(criteria.values()) / len(criteria)
        if score >= self.SCORE_EXCELLENT:
            classification = "excelente"
        elif score >= self.SCORE_ACCEPTABLE:
            classification = "aceptable"
        else:
            classification = "malo"

        recommendations = self._generate_recommendations(criteria)

        return EvaluationResult(
            score_total=score,
            classification=classification,
            criteria=criteria,
            recommendations=recommendations,
        )

    def _generate_recommendations(self, criteria: dict[str, float]) -> list[str]:
        """Genera recomendaciones para criterios bajos."""
        mapping = {
            "curiosidad": "Mejorá la curiosidad del hook",
            "emocion": "Añadí más impacto emocional",
            "claridad": "Hacé el texto más directo",
            "viral": "Usá un formato más viral (list, fact)",
            "hook_fuerza": "Mejorá el hook inicial",
            "hook_fuerte": "Mejorá el hook del guion",
            "ritmo": "Oraciones más cortas para mejor ritmo",
            "claridad_narrativa": "Simplificá la narrativa",
            "final_impacto": "Mejorá el CTA final",
            "duracion": "Ajustá la duración (30-60s ideal)",
            "hook_implicito": "Mejorá el hook inicial",
        }
        return [
            mapping[k] for k, v in criteria.items()
            if v < self.SCORE_ACCEPTABLE and k in mapping
        ]
