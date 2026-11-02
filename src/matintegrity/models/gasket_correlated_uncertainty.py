"""Registry exposure for the correlation-preserving gasket scenario calculator."""

from ..gasket_correlated_uncertainty import (
    GasketLeakageCorrelatedScenario,
    GasketLeakageCorrelatedScenarioEnvelope,
    evaluate_gasket_leakage_correlated_scenarios,
    specifications,
)

__all__ = [
    "GasketLeakageCorrelatedScenario",
    "GasketLeakageCorrelatedScenarioEnvelope",
    "evaluate_gasket_leakage_correlated_scenarios",
    "specifications",
]
