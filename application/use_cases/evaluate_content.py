import logging
from typing import Optional

from domain.entities.content_idea import ContentIdea
from domain.entities.script import Script
from domain.services.content_evaluator import ContentEvaluator, EvaluationResult
from domain.ports.content_repository import ContentRepository
from application.dto import EvaluateRequest
from application.dto.responses import ContentResult, EvaluationResponse
from application.error_mapper import ErrorMapper

logger = logging.getLogger(__name__)


class EvaluateContentUseCase:
    """
    Caso de uso: EVALUAR Y OPTIMIZAR CONTENIDO.
    
    Evalúa ideas y scripts según criterios de viralidad.
    Puede optimizar automáticamente si el score es bajo.
    """
    
    def __init__(
        self,
        evaluator: ContentEvaluator,
        repository: ContentRepository,
    ):
        self._evaluator = evaluator
        self._repo = repository

    async def execute(self, request: EvaluateRequest) -> ContentResult:
        """Evalúa contenido."""
        try:
            if request.content_type == "idea":
                return await self._evaluate_idea(request)
            elif request.content_type == "script":
                return await self._evaluate_script(request)
            else:
                return ContentResult.error(
                    f"Tipo de contenido no soportado: {request.content_type}",
                    code="INVALID_CONTENT_TYPE",
                    status=400,
                )
        except Exception as e:
            logger.error(f"Error evaluando contenido: {e}")
            return ContentResult.error(str(e))

    async def _evaluate_idea(self, request: EvaluateRequest) -> ContentResult:
        """Evalúa y opcionalmente optimiza una idea."""
        idea = await self._repo.get_idea(request.content_id)
        if not idea:
            return ContentResult.error("Idea no encontrada", code="NOT_FOUND", status=404)

        result = self._evaluator.evaluate_idea(idea)
        response = EvaluationResponse(
            score=result.score_total,
            classification=result.classification,
            criteria=result.criteria,
            recommendations=result.recommendations,
        )

        if request.optimize and not result.is_acceptable:
            optimized = self._evaluator.optimize_idea(idea, result.recommendations)
            await self._repo.save_idea(optimized)
            response.was_optimized = True
            response.optimized_content = optimized.to_dict()

        return ContentResult.ok(data={
            "evaluation": response.__dict__,
            "original_idea": idea.to_dict(),
        })

    async def _evaluate_script(self, request: EvaluateRequest) -> ContentResult:
        """Evalúa y opcionalmente optimiza un script."""
        script = await self._repo.get_script(request.content_id)
        if not script:
            return ContentResult.error("Script no encontrado", code="NOT_FOUND", status=404)

        result = self._evaluator.evaluate_script(script)
        response = EvaluationResponse(
            score=result.score_total,
            classification=result.classification,
            criteria=result.criteria,
            recommendations=result.recommendations,
        )

        if request.optimize and not result.is_acceptable:
            optimized = self._evaluator.optimize_script(script, result.recommendations)
            await self._repo.save_script(optimized)
            response.was_optimized = True
            response.optimized_content = optimized.to_dict()

        return ContentResult.ok(data={
            "evaluation": response.__dict__,
            "original_script": script.to_dict(),
        })
