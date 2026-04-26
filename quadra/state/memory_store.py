"""
Stateful Memory Store - Persistent neural and symbolic state across requests.

Enables the critical "stateful intelligence" requirement:
- Persistent memory of patterns (neuroplastic)
- Oscillatory phase continuity
- Syntropy trajectory history
- Context accumulation for reasoning

This breaks the stateless commodity model and enables true adaptive intelligence.
"""

import logging
import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import numpy as np
import torch

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Persistent memory for stateful inference.
    
    Maintains:
    - Neural field state (oscillator phase, syntropy levels, core field values)
    - Symbolic memory (concepts, reasoning traces)
    - Neuroplastic adaptation history
    - Context window for inference
    """
    
    def __init__(self, storage_path: str = "./memory_store"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory state (synced to disk)
        self.oscillator_phase: float = 0.0
        self.syntropy_values: List[float] = [0.5, 0.5, 0.5]  # Three fields
        self.core_field: Optional[np.ndarray] = None
        
        # Symbolic memory
        self.concept_history: List[str] = []
        self.reasoning_traces: List[Dict[str, Any]] = []
        
        # Neuroplastic history
        self.learning_rate_trajectory: List[float] = []
        self.success_streak: int = 0
        self.total_inferences: int = 0
        
        # Context window (recent inputs/outputs for coherence)
        self.context_window: List[Dict[str, Any]] = []
        self.max_context_size = 20
        
        self._load_from_disk()
        logger.info(f"MemoryStore initialized at {self.storage_path}")
    
    def _load_from_disk(self):
        """Load state from persistent storage."""
        try:
            # Load neural state
            neural_file = self.storage_path / "neural_state.pkl"
            if neural_file.exists():
                with open(neural_file, 'rb') as f:
                    state = pickle.load(f)
                    self.oscillator_phase = state.get('oscillator_phase', 0.0)
                    self.syntropy_values = state.get('syntropy_values', [0.5, 0.5, 0.5])
                    if 'core_field' in state and state['core_field'] is not None:
                        self.core_field = state['core_field']
                logger.info("Loaded neural state from disk")
            
            # Load symbolic memory
            symbolic_file = self.storage_path / "symbolic_memory.json"
            if symbolic_file.exists():
                with open(symbolic_file, 'r') as f:
                    symbolic = json.load(f)
                    self.concept_history = symbolic.get('concept_history', [])
                    self.reasoning_traces = symbolic.get('reasoning_traces', [])
                logger.info(f"Loaded {len(self.concept_history)} concepts from memory")
            
            # Load neuroplasticity history
            neuro_file = self.storage_path / "neuroplasticity.json"
            if neuro_file.exists():
                with open(neuro_file, 'r') as f:
                    neuro = json.load(f)
                    self.learning_rate_trajectory = neuro.get('learning_rate_trajectory', [])
                    self.success_streak = neuro.get('success_streak', 0)
                    self.total_inferences = neuro.get('total_inferences', 0)
                logger.info(f"Loaded neuroplasticity trajectory ({len(self.learning_rate_trajectory)} entries)")
        
        except Exception as e:
            logger.warning(f"Failed to load memory from disk: {e}. Starting fresh.")
    
    def _save_to_disk(self):
        """Persist state to disk."""
        try:
            # Save neural state
            neural_state = {
                'oscillator_phase': self.oscillator_phase,
                'syntropy_values': self.syntropy_values,
                'core_field': self.core_field,
                'timestamp': datetime.utcnow().isoformat(),
            }
            with open(self.storage_path / "neural_state.pkl", 'wb') as f:
                pickle.dump(neural_state, f)
            
            # Save symbolic memory
            symbolic = {
                'concept_history': self.concept_history[-500:],  # Keep last 500
                'reasoning_traces': self.reasoning_traces[-100:],  # Keep last 100
                'timestamp': datetime.utcnow().isoformat(),
            }
            with open(self.storage_path / "symbolic_memory.json", 'w') as f:
                json.dump(symbolic, f, indent=2)
            
            # Save neuroplasticity
            neuro = {
                'learning_rate_trajectory': self.learning_rate_trajectory[-1000:],
                'success_streak': self.success_streak,
                'total_inferences': self.total_inferences,
                'timestamp': datetime.utcnow().isoformat(),
            }
            with open(self.storage_path / "neuroplasticity.json", 'w') as f:
                json.dump(neuro, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save memory to disk: {e}")
    
    def update_neural_state(self, oscillator_phase: float, syntropy_values: List[float], 
                           core_field: Optional[np.ndarray] = None):
        """Update neural state after inference."""
        self.oscillator_phase = oscillator_phase
        self.syntropy_values = syntropy_values
        if core_field is not None:
            self.core_field = core_field
        self._save_to_disk()
    
    def add_concept(self, concept: str):
        """Record a concept encountered during inference."""
        if concept not in self.concept_history[-10:]:  # Avoid duplicates in recent history
            self.concept_history.append(concept)
            self._save_to_disk()
    
    def add_reasoning_trace(self, trace: Dict[str, Any]):
        """Record a symbolic reasoning trace."""
        trace['timestamp'] = datetime.utcnow().isoformat()
        self.reasoning_traces.append(trace)
        if len(self.reasoning_traces) > 200:
            self.reasoning_traces.pop(0)
        self._save_to_disk()
    
    def record_inference(self, success: bool, learning_rate: float):
        """Record inference outcome for neuroplastic tracking."""
        self.total_inferences += 1
        self.learning_rate_trajectory.append(learning_rate)
        
        if success:
            self.success_streak += 1
        else:
            self.success_streak = 0
        
        # Keep trajectory bounded
        if len(self.learning_rate_trajectory) > 2000:
            self.learning_rate_trajectory.pop(0)
        
        self._save_to_disk()
    
    def add_to_context(self, item: Dict[str, Any]):
        """Add item to context window for coherence."""
        item['timestamp'] = datetime.utcnow().isoformat()
        self.context_window.append(item)
        
        if len(self.context_window) > self.max_context_size:
            self.context_window.pop(0)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of recent context for coherence."""
        if not self.context_window:
            return {}
        
        return {
            'recent_concepts': [c.get('concept') for c in self.context_window if 'concept' in c][-5:],
            'recent_outputs': [c.get('output') for c in self.context_window if 'output' in c][-3:],
            'context_size': len(self.context_window),
        }
    
    def get_neuroplastic_metrics(self) -> Dict[str, Any]:
        """Get current neuroplastic adaptation metrics."""
        if not self.learning_rate_trajectory:
            return {'learning_rate': 0.01, 'success_streak': 0, 'total_inferences': 0}
        
        return {
            'current_learning_rate': float(self.learning_rate_trajectory[-1]),
            'avg_learning_rate': float(np.mean(self.learning_rate_trajectory[-100:])) if len(self.learning_rate_trajectory) > 0 else 0.01,
            'learning_rate_trend': self._compute_trend(self.learning_rate_trajectory[-20:]),
            'success_streak': self.success_streak,
            'total_inferences': self.total_inferences,
            'success_rate': self.success_streak / max(10, self.total_inferences),  # Approximate
        }
    
    def _compute_trend(self, values: List[float]) -> str:
        """Compute trend (increasing/decreasing) in recent values."""
        if len(values) < 2:
            return "stable"
        
        change = values[-1] - values[0]
        if abs(change) < 0.001:
            return "stable"
        return "increasing" if change > 0 else "decreasing"
    
    def clear(self):
        """Clear all memory (for reset/testing)."""
        self.oscillator_phase = 0.0
        self.syntropy_values = [0.5, 0.5, 0.5]
        self.core_field = None
        self.concept_history.clear()
        self.reasoning_traces.clear()
        self.learning_rate_trajectory.clear()
        self.success_streak = 0
        self.total_inferences = 0
        self.context_window.clear()
        logger.info("Memory cleared")


class StatefulInferenceContext:
    """
    Context object passed through the inference pipeline.
    
    Carries memory state and governance decisions through all stages.
    """
    
    def __init__(self, memory_store: MemoryStore, request_id: str = ""):
        self.memory = memory_store
        self.request_id = request_id or str(datetime.utcnow().timestamp())
        
        # Pipeline state
        self.encoded_input: Optional[np.ndarray] = None
        self.patterns: Optional[np.ndarray] = None
        self.spikes: Optional[torch.Tensor] = None
        self.neuroplastic_update: Optional[np.ndarray] = None
        self.oscillated_output: Optional[torch.Tensor] = None
        self.symbolic_interpretation: Optional[str] = None
        self.governance_decision: Optional[Dict[str, Any]] = None
        self.final_output: Optional[Dict[str, Any]] = None
        
        # Metrics
        self.stage_times: Dict[str, float] = {}
        self.stage_start_time: Optional[datetime] = None
    
    def start_stage(self, stage_name: str):
        """Mark start of a pipeline stage."""
        self.stage_start_time = datetime.utcnow()
    
    def end_stage(self, stage_name: str):
        """Record stage completion time."""
        if self.stage_start_time:
            elapsed = (datetime.utcnow() - self.stage_start_time).total_seconds()
            self.stage_times[stage_name] = elapsed
    
    def to_dict(self) -> Dict[str, Any]:
        """Export context for logging/debugging."""
        return {
            'request_id': self.request_id,
            'stage_times': self.stage_times,
            'memory_metrics': self.memory.get_neuroplastic_metrics(),
        }
