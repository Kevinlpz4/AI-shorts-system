"""
ValueObject — Marker class for Domain Value Objects.

ValueObject is a **marker base class** (not a dataclass). It does NOT impose
@dataclass(frozen=True) or any other implementation. Each concrete Value Object
chooses how to implement itself, but MUST be immutable.

Typical usage:

    @dataclass(frozen=True)
    class Address(ValueObject):
        street: str
        city: str

The @dataclass(frozen=True) decorator provides:
    - Immutability (FrozenInstanceError on attribute reassignment)
    - Structural equality (__eq__ based on all fields)
    - Automatic __hash__ based on all fields
    - Automatic __init__ and __repr__

However, a Value Object could also use namedtuple, attrs, or manual
implementation. The marker class ensures isinstance checks and type hints
work polymorphically across all Value Objects in the system.

NOTE: Foundation does NOT enforce immutability — that is the responsibility
of each concrete Value Object and must be verified in code review.
"""


class ValueObject:
    """
    Marker base class for all Value Objects in the system.

    Responsibilities:
        - Common type for isinstance checks and polymorphic type hints
        - Documents intent: "this class is a Domain Value Object"

    Does NOT do:
        - Does NOT impose @dataclass(frozen=True) or any implementation
        - Does NOT provide __eq__, __hash__, __init__, __repr__
        - Does NOT have identity
        - Does NOT have lifecycle events
        - Does NOT validate or persist itself

    Concrete subclasses MUST be immutable. The typical implementation uses
    @dataclass(frozen=True), but other mechanisms are allowed as long as
    immutability is guaranteed.
    """
    pass
