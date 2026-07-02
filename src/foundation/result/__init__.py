"""
Result Pattern — API pública del paquete ``foundation/result``.

Exporta las clases principales del Result Pattern para toda la aplicación.
"""

from foundation.result.result import Error, ErrorCode, Failure, Result, Success

__all__ = [
    "Error",
    "ErrorCode",
    "Failure",
    "Result",
    "Success",
]
