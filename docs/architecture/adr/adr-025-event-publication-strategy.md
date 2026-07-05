---
adr: "ADR-025"
title: "Event Publication Strategy — Post-Commit Hooks with Outbox Evolution Path"
status: "APPROVED"
date: "2026-07-05"
---

# ADR-025: Event Publication Strategy

## Contexto

El BC Ingestion define 3 Domain Events que se emiten durante operaciones de escritura:

| Evento | Emitido por | Frecuencia estimada |
|--------|-------------|---------------------|
| `SourceEnabled` | `NewsSource.enable()` | ~1-10/día |
| `SourceDisabled` | `NewsSource.disable()` | ~1-10/día |
| `RawArticleCollected` | `Feed.record_collection()` | ~100-1,000/día |

Cuando un Application Service ejecuta una operación que modifica un Aggregate Root y emite eventos,
necesitamos decidir **cuándo y cómo** se publican esos eventos en relación con la transacción de BD.

Tenemos 3 opciones principales:

### Opción A: Post-Commit Hooks
Los eventos se recolectan del aggregate en el Service, se pasan al UnitOfWork, y se publican
**después** de `session.commit()` exitoso.

```
Service: uow.__enter__()
           ↓ operaciones de dominio + repositorios
Service: uow.commit()
           ↓ session.commit()  ← PERSISTIDO
           ↓ publish_events()  ← Si falla, evento PERDIDO
Service: uow.__exit__()
```

### Opción B: Outbox Pattern
Los eventos se insertan en una tabla `event_outbox` **dentro** de la misma transacción de BD.
Un worker separado lee la outbox y publica los eventos de forma asíncrona.

```
Service: uow.__enter__()
           ↓ operaciones + repositorios
           ↓ INSERT INTO event_outbox  ← MISMA transacción
Service: uow.commit()
           ↓ session.commit()  ← PERSISTIDO (datos + outbox)
           ...
Worker:   SELECT FROM event_outbox WHERE NOT published
           ↓ publish_events()
           ↓ UPDATE event_outbox SET published = true
```

### Opción C: Two-Phase (híbrido)
Los eventos se guardan en outbox dentro de la transacción (como Opción B) Y se publican
inmediatamente después de commit (como Opción A). Si publish falla, el worker lo retoma.

```
Service: uow.__enter__()
           ↓ operaciones + repositorios
           ↓ INSERT INTO event_outbox
Service: uow.commit()
           ↓ session.commit()
           ↓ publish_events()     ← Intento inmediato
           ↓ (si falla → queda en outbox para worker)
Worker:   SELECT FROM event_outbox WHERE NOT published (safety net)
```

## Decisión

### Opción A: Post-Commit Hooks — SELECCIONADA para EPIC 5

```python
class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory, event_publisher):
        self._session_factory = session_factory
        self._event_publisher = event_publisher
        self._pending_events: list[DomainEvent] = []
        self.session: Session | None = None
    
    def collect_events(self, aggregate: AggregateRoot) -> None:
        """Recolecta eventos de un aggregate antes de commit."""
        self._pending_events.extend(aggregate.pull_events())
    
    def commit(self) -> None:
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            self._pending_events.clear()
            raise
        
        # Post-commit: publicar eventos
        events = self._pending_events[:]
        self._pending_events.clear()
        if events:
            self._event_publisher.publish_batch(events)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            self._pending_events.clear()
        self.session.close()
```

### Justificación

| Factor | Opción A | Opción B | Opción C |
|--------|----------|----------|----------|
| **Complejidad de implementación** | 🔵 BAJA (~50 líneas) | 🔴 ALTA (~300 líneas + worker) | 🟡 MEDIA (~400 líneas) |
| **Pérdida de eventos si publish falla** | ✅ Sí (se pierde) | ❌ No (retry vía worker) | ❌ No (retry vía worker) |
| **Latencia de publicación** | ⚡ Inmediata | ⏳ Eventual (hasta 1s) | ⚡ Inmediata + eventual |
| **Consistencia** | Eventual (pérdida posible) | Fuerte (outbox en misma tx) | Fuerte + eventual backup |
| **Costo operativo** | CERO | Worker separado + monitoreo | Worker separado + monitoreo |
| **Volumen soportado** | ~1,000 eventos/día | Ilimitado | Ilimitado |
| **Rollback safety** | ✅ Sí (eventos se limpian) | ✅ Sí (outbox se revierte) | ✅ Sí (outbox se revierte) |

**Se selecciona Opción A porque:**

1. **Volumen bajo**: ~100-1,000 eventos/día. La pérdida de un evento es aceptable y recuperable
   manualmente (re-intentar la operación).

2. **Complejidad cero**: Sin worker, sin outbox table, sin monitoreo adicional. ~50 líneas de código.

3. **La pérdida de un evento no es crítica**:
   - `SourceEnabled`/`SourceDisabled`: son notificaciones. Si se pierde una, el sistema sigue funcionando.
     El estado actual está en la BD.
   - `RawArticleCollected`: es una métrica. Si se pierde, no afecta la integridad de los datos.

4. **YAGNI**: Outbox Pattern sería premature optimization para el volumen actual. Cuando se necesite
   at-least-once, la migración a Opción C es directa (agregar outbox table + worker).

### Cuándo migrar a Opción C (Two-Phase)

Si en el futuro ocurre ALGUNA de estas condiciones:
- Se agregan eventos cuyo consumo es crítico (ej: notificaciones a usuarios, webhooks externos)
- El volumen supera 10,000 eventos/día
- Se reporta pérdida de eventos en producción más de 1 vez

La migración es directa:
1. Agregar tabla `event_outbox`
2. Modificar `UnitOfWork` para insertar eventos en outbox (antes de commit)
3. Publicar inmediatamente después de commit (como ahora)
4. Agregar worker opcional como safety net
5. Sin cambios en los servicios de aplicación

## Consecuencias

### Positivas ✅

- **Implementación trivial**: ~50 líneas, sin dependencias nuevas
- **Sin worker**: Cero infraestructura adicional
- **Rollback safety**: eventos se limpian automáticamente en rollback
- **Order FIFO**: Los eventos se publican en el orden en que fueron recolectados
- **Migración directa**: Opción C agrega outbox + worker sin refactor

### Negativas ⚠️

- **Pérdida posible**: Si el publisher falla post-commit, el evento se pierde
- **Sin retry**: Solo se intenta una vez
- **Sin monitoreo de fallos**: No hay alerta automática si publish falla

## Alternativas Descartadas

### Alternativa B: Outbox Pattern (descartada para EPIC 5)

- **Ventaja**: Garantía de entrega at-least-once.
- **Desventaja**: Complejidad alta para el volumen actual. Worker, tabla outbox, dead letter queue.
- **Descartada por**: YAGNI. ~100-1,000 eventos/día no justifican la complejidad de un sistema
  de mensajería. La pérdida ocasional de un evento de baja criticidad es aceptable.

### Alternativa: Publicar eventos en el Service (no en UoW)

- **Descripción**: El service publica eventos directamente después de llamar a `uow.commit()`.
- **Descartada por**: Viola SRP. El service no debería manejar publicación de eventos.
  Además, duplica la lógica de post-commit en cada service.

## Compliance

- **Principios**: P2 (Clean Architecture), P5 (YAGNI)
- **Baseline**: v1.0 (no rompe)
- **Foundation**: No se modifica. `DomainEvent` se usa como type hint.
- **Domain**: No se modifica. Los eventos se recolectan vía `pull_events()`.
- **Application**: No se modifica. Los services ya recolectan eventos de aggregates.
- **ADR relacionados**: ADR-021 (Foundation FROZEN)

## Compliance Futuro

- Migrar a Opción C cuando el volumen o criticidad lo ameriten.
- La migración no requiere cambios en Domain (los eventos siguen siendo los mismos).
- No requiere cambios en Application (los services siguen usando `uow.commit()`).
