"""Quadra-Matrix AI: Stateful Symbolic Predictive Intelligence System"""

__version__ = "0.2.0"
__author__ = "Quadra-Matrix Team"

from .core.symbolic.interpreter import StatefulSymbolicPredictiveInterpreter
from .state.memory_store import MemoryStore, StatefulInferenceContext
from .core.governance.policy_adapter import PolicyEngine, GovernanceService, PolicyContext

__all__ = [
    'StatefulSymbolicPredictiveInterpreter',
    'MemoryStore',
    'StatefulInferenceContext',
    'PolicyEngine',
    'GovernanceService',
    'PolicyContext',
]
