"""
SignalType Value Object — Classifies the dimension of a learning signal.

Signals are categorized by the dimension they measure, enabling
the Open/Closed signal handler hierarchy.
"""
from __future__ import annotations

from enum import Enum


class SignalType(str, Enum):
    """Classification of a learning signal by its measurement dimension.

    Attributes:
        KEYWORD: Signal based on keyword effectiveness (per-keyword approval rates).
        SOURCE: Signal based on source reliability (per-source approval rates).
        CATEGORY: Signal based on category performance (per-category approval rates).
        TOPIC: Signal based on topic engagement (per-topic approval rates).
        TIME: Signal based on temporal patterns (time-of-day, day-of-week).
    """

    KEYWORD = "KEYWORD"
    SOURCE = "SOURCE"
    CATEGORY = "CATEGORY"
    TOPIC = "TOPIC"
    TIME = "TIME"
