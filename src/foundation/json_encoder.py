"""
FoundationEncoder — JSONEncoder genérico para tipos Foundation.

Responsabilidades:
  - Serializar EntityId a string UUID en JSON
  - Ser extensible para futuros tipos Foundation
    (ValueObject, DomainEvent, Result, etc.)

Uso:
    import json
    from foundation import EntityId, FoundationEncoder

    eid = EntityId.new()
    data = json.dumps({"id": eid}, cls=FoundationEncoder)

    # Sin encoder, lanza TypeError
    # json.dumps({"id": eid})  # ❌ TypeError
"""

import json

from foundation.entity_id import EntityId


class FoundationEncoder(json.JSONEncoder):
    """
    JSONEncoder genérico para tipos Foundation.

    Actualmente maneja:
      - EntityId → serializa como string UUID

    Cuando se agreguen nuevos tipos Foundation (ValueObject, DomainEvent,
    Result, etc.), agregar su serialización AQUí, no crear encoders
    separados. Esto mantiene un solo punto de extensión.

    Uso:
        json.dumps({"id": some_entity_id}, cls=FoundationEncoder)

    Nota: Si un tipo Foundation no tiene serialización registrada,
    FoundationEncoder delega al default de JSONEncoder, que lanza
    TypeError para tipos no serializables.
    """

    def default(self, obj: object) -> str:
        if isinstance(obj, EntityId):
            return str(obj)
        return super().default(obj)
