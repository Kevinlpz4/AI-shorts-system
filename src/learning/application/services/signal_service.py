"""
SignalService — Casos de uso para LearningSignal.

Orquesta las operaciones de registro y recálculo de señales de aprendizaje,
coordinando con SignalRegistry para la creación de señales por dimensión.

Dependencias inyectadas (DIP):
    - signal_repo: LearningSignalRepository
    - signal_registry: SignalRegistry
    - uow: UnitOfWork
    - event_publisher: EventPublisher
    - clock: ClockPort

Siempre retorna ``Result[T]`` — nunca lanza excepciones no manejadas.
"""
from __future__ import annotations

from datetime import timedelta

from foundation.errors import DomainError
from foundation.ports.clock import ClockPort
from foundation.result.result import Error, Result

from learning.application.commands.signal_commands import RegisterSignalCommand
from learning.application.commands.score_commands import RecalculateSignalsCommand
from learning.application.common.query_result import QueryResult
from learning.application.dto.signal_dto import LearningSignalDTO
from learning.application.errors.error_mapper import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.mappers.signal_mapper import LearningSignalMapper
from learning.application.ports.event_publisher import EventPublisher
from learning.application.ports.unit_of_work import UnitOfWork
from learning.application.queries.model_queries import GetLearningSignalsQuery
from learning.domain.entities.ids import LearningSignalId
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.exceptions import LearningDomainError
from learning.domain.ports.repositories import LearningSignalRepository
from learning.domain.signals.registry import SignalRegistry
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.time_window import TimeWindow


class SignalService:
    """Casos de uso para LearningSignal.

    Todos los métodos retornan ``Result[LearningSignalDTO]`` o
    ``Result[QueryResult[LearningSignalDTO]]`` o ``Result[int]``.

    Métodos de escritura usan UnitOfWork + EventPublisher.
    Métodos de solo lectura (queries) NO usan UnitOfWork.
    """

    def __init__(
        self,
        signal_repo: LearningSignalRepository,
        signal_registry: SignalRegistry,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        clock: ClockPort,
    ) -> None:
        self._signal_repo = signal_repo
        self._signal_registry = signal_registry
        self._uow = uow
        self._event_publisher = event_publisher
        self._clock = clock

    # ── Commands ──

    def execute_register_signal(
        self, cmd: RegisterSignalCommand
    ) -> Result[LearningSignalDTO]:
        """Register a new signal from an external source.

        Steps:
            1. Get handler from registry by dimension
            2. Create LearningSignal via handler
            3. Save
            4. Commit
            5. Publish SignalAggregated event
            6. Return LearningSignalDTO
        """
        with self._uow:
            try:
                # 1. Get handler from registry
                signal_type = SignalType(cmd.dimension)
                handler = self._signal_registry.get_handler(signal_type)

                # 2. Compute strength via handler
                strength = handler.compute(
                    {
                        "approval_rate": cmd.value,
                        "sample_size": 1,
                    }
                )

                # 3. Build time window (24h from now)
                now = self._clock.now()
                window = TimeWindow(
                    start=now,
                    end=now + timedelta(hours=24),
                )

                # 4. Create LearningSignal
                signal = LearningSignal(
                    id=LearningSignalId.generate(),
                    signal_type=signal_type,
                    dimension=cmd.source,
                    strength=strength,
                    sample_size=1,
                    approval_rate=cmd.value,
                    window=window,
                    last_updated=now,
                )

                # 5. Save
                self._signal_repo.save(signal)

                # 6. Commit
                self._uow.commit()

                # 7. Publish events (after commit)
                events = signal.pull_events()
                if events:
                    self._event_publisher.publish_many(events)

                # 8. Return DTO
                return Result.success(LearningSignalMapper.to_dto(signal))

            except LearningDomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except KeyError as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.COMMAND_INVALID,
                        message=f"Unknown signal dimension: {e}",
                    )
                )
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    def execute_recalculate_signals(
        self, cmd: RecalculateSignalsCommand
    ) -> Result[int]:
        """Recalculate signals for a dimension or all dimensions.

        Applies time-based decay to signal strengths and persists updates.

        Steps:
            1. Find signals matching filters
            2. Apply decay
            3. Save updated signals
            4. Commit
            5. Return count of recalculated signals
        """
        with self._uow:
            try:
                # 1. Find signals matching filters
                signals: list[LearningSignal] = []

                if cmd.signal_type:
                    # Filter by signal type — use find_all_active and filter
                    all_active = self._signal_repo.find_all_active()
                    target_type = SignalType(cmd.signal_type)
                    signals = [
                        s for s in all_active if s.signal_type == target_type
                    ]
                else:
                    signals = self._signal_repo.find_all_active()

                # 2. Apply decay to each signal
                now = self._clock.now()
                recalculated_count = 0

                for signal in signals:
                    # Calculate elapsed periods (hours since last update)
                    elapsed = (now - signal.last_updated).total_seconds() / 3600.0
                    if elapsed > 0:
                        decayed_strength = signal.strength.apply_decay(elapsed)
                        # Update the signal with decayed strength
                        signal.update(
                            new_sample_size=signal.sample_size,
                            new_approval_rate=signal.approval_rate,
                            new_strength=decayed_strength,
                            new_window=signal.window,
                        )
                        recalculated_count += 1

                # 3. Save updated signals
                if signals:
                    self._signal_repo.save_batch(signals)

                # 4. Commit
                self._uow.commit()

                # 5. Return count
                return Result.success(recalculated_count)

            except LearningDomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except DomainError as e:
                return Result.failure(ErrorMapper.map_domain_error(e))
            except Exception as e:
                return Result.failure(
                    Error(
                        code=ApplicationErrorCode.OPERATION_FAILED,
                        message=str(e),
                    )
                )

    # ── Queries (solo lectura, sin UoW) ──

    def execute_get_learning_signals(
        self, query: GetLearningSignalsQuery
    ) -> Result[QueryResult[LearningSignalDTO]]:
        """List signals with optional filters.

        Solo lectura. Sin UnitOfWork.
        """
        try:
            signals = self._signal_repo.find_all_active()

            # Apply dimension filter
            if query.dimension:
                target_type = SignalType(query.dimension)
                signals = [s for s in signals if s.signal_type == target_type]

            # Apply source filter
            if query.source:
                signals = [s for s in signals if s.dimension == query.source]

            dtos = [LearningSignalMapper.to_dto(s) for s in signals]
            return Result.success(
                QueryResult(
                    data=dtos,
                    total=len(dtos),
                )
            )

        except LearningDomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except DomainError as e:
            return Result.failure(ErrorMapper.map_domain_error(e))
        except Exception as e:
            return Result.failure(
                Error(
                    code=ApplicationErrorCode.OPERATION_FAILED,
                    message=str(e),
                )
            )
