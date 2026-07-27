"""
Simulation Engine — adaptive learning & one-month runtime simulation.

Provides virtual clock, feedback policies, learning evolution tracking,
and reproducible simulation runs using seeded randomness.

Usage::

    from runtime.simulation import SimulationEngine, SimulationConfig

    config = SimulationConfig(days=30, seed=42)
    engine = SimulationEngine(config)
    report = engine.run()
"""
from runtime.simulation.config import SimulationConfig
from runtime.simulation.engine import SimulationEngine

__all__ = ["SimulationConfig", "SimulationEngine"]
