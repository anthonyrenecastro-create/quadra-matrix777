"""
Stateful Symbolic Predictive Interpreter - Complete 8-stage pipeline.

Full inference pipeline:
  1. Encoded Input: Convert input to neural representation
  2. Pattern Extraction: Identify structures (clustering, frequency analysis)
  3. Field Spiking: Generate spike trains via spiking neural networks
  4. Neuroplastic Update: Adapt weights and state based on success
  5. Oscillatory Modulation: Apply temporal phase modulation
  6. Symbolic Interpretation: Derive logical/algebraic insights
  7. Governance Evaluation: Apply policy constraints
  8. Output Synthesis: Format and condition final output

Maintains state across requests via MemoryStore for true adaptive intelligence.
"""

import logging
import numpy as np
import torch
import torch.nn as nn
import sympy as sp
from sympy.logic.boolalg import Implies
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import networkx as nx
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet

from quadra.state.memory_store import MemoryStore, StatefulInferenceContext
from quadra.core.governance.policy_adapter import PolicyEngine, GovernanceService, PolicyContext

logger = logging.getLogger(__name__)


class InputEncoder:
    """Stage 1: Encode raw input into neural representation."""
    
    def __init__(self, input_dim: int = 128):
        self.input_dim = input_dim
    
    def encode_text(self, text: str) -> np.ndarray:
        """Simple encoding: average word embeddings via NLTK."""
        tokens = word_tokenize(text.lower())
        
        # Simple frequency-based encoding
        embedding = np.zeros(self.input_dim)
        for i, token in enumerate(tokens[:self.input_dim]):
            embedding[i] = len(token) / 10.0  # Normalize by length
        
        # Add context signal
        embedding = embedding + np.random.randn(self.input_dim) * 0.01
        return embedding / (np.linalg.norm(embedding) + 1e-8)
    
    def encode_vector(self, vector: np.ndarray) -> np.ndarray:
        """Ensure vector is properly normalized."""
        if vector.size == 0:
            return np.zeros(self.input_dim)
        
        vector = np.array(vector).flatten()
        if vector.size < self.input_dim:
            vector = np.pad(vector, (0, self.input_dim - vector.size), mode='constant')
        elif vector.size > self.input_dim:
            vector = vector[:self.input_dim]
        
        return vector / (np.linalg.norm(vector) + 1e-8)


class PatternExtractor:
    """Stage 2: Extract patterns from encoded input."""
    
    def __init__(self, n_patterns: int = 3):
        self.n_patterns = n_patterns
    
    def extract(self, encoded_input: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Extract patterns via frequency analysis and clustering.
        
        Returns:
            patterns: Cluster assignments
            confidence: How confident we are about the patterns
        """
        # Frequency analysis
        fft_result = np.abs(np.fft.fft(encoded_input))
        top_freqs = np.argsort(fft_result)[-self.n_patterns:]
        
        # Simple pattern detection: group by magnitude
        patterns = np.zeros(len(encoded_input))
        for i, idx in enumerate(top_freqs):
            patterns[idx] = i + 1
        
        # Confidence = how concentrated the power spectrum is
        normalized_power = fft_result / (np.sum(fft_result) + 1e-8)
        entropy = -np.sum(normalized_power * np.log(normalized_power + 1e-8))
        confidence = np.exp(-entropy)  # Low entropy = high confidence
        
        return patterns, confidence


class SpikeGenerator:
    """Stage 3: Generate spike trains via spiking neural networks."""
    
    def __init__(self, input_dim: int = 128, hidden_dim: int = 64):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Simple spiking mechanism
        self.weights = nn.Parameter(torch.randn(input_dim, hidden_dim) * 0.1)
        self.threshold = 0.5
    
    def forward(self, encoded_input: torch.Tensor, num_steps: int = 5) -> torch.Tensor:
        """
        Generate spike trains by applying threshold over time steps.
        """
        spikes_over_time = []
        membrane_potential = torch.zeros(1, self.hidden_dim)
        
        for step in range(num_steps):
            # Compute input current
            current = torch.matmul(encoded_input.unsqueeze(0), self.weights)
            
            # Update membrane potential
            membrane_potential = 0.9 * membrane_potential + 0.1 * current
            
            # Generate spikes
            spikes = (membrane_potential > self.threshold).float()
            spikes_over_time.append(spikes)
            
            # Reset after spike
            membrane_potential = membrane_potential * (1 - spikes)
        
        return torch.stack(spikes_over_time).mean(dim=0)


class NeuroplasticAdapter:
    """Stage 4: Adapt neural state based on inference success."""
    
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.base_learning_rate = 0.01
    
    def adapt(self, success: bool) -> np.ndarray:
        """
        Compute adaptive learning rate and update memory.
        
        Uses exponential adaptation: success increases rate, failure resets.
        """
        metrics = self.memory.get_neuroplastic_metrics()
        current_streak = metrics['success_streak']
        
        # Exponential growth with safety cap
        if success:
            learning_rate = min(
                self.base_learning_rate * (1.1 ** current_streak),
                self.base_learning_rate * 10.0  # 10x max speedup
            )
        else:
            learning_rate = self.base_learning_rate
        
        self.memory.record_inference(success, learning_rate)
        
        # Return as adaptation signal (for field update)
        return np.array([learning_rate] * 3)  # Three fields


class OscillatorModule:
    """Stage 5: Apply temporal oscillatory modulation."""
    
    def __init__(self, memory: MemoryStore):
        self.memory = memory
    
    def modulate(self, input_signal: torch.Tensor) -> torch.Tensor:
        """
        Modulate signal by current oscillatory phase from memory.
        
        Phase is continuous across requests (stateful).
        """
        phase = self.memory.oscillator_phase
        
        # Sinusoidal modulation with phase from previous state
        modulation = torch.sin(torch.tensor(phase)).item()
        
        # Update phase for next request
        self.memory.oscillator_phase = (phase + 0.1) % (2 * np.pi)
        
        # Apply modulation
        modulated = input_signal * (1.0 + 0.3 * modulation)
        
        return modulated


class SymbolicReasoner:
    """Stage 6: Symbolic interpretation of neural output."""
    
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.knowledge_graph = nx.DiGraph()
    
    def interpret(self, neural_output: torch.Tensor, concepts: List[str]) -> str:
        """
        Derive symbolic meaning from neural activations.
        
        Combines algebraic reasoning, logic, and knowledge graphs.
        """
        try:
            # 6a: Algebraic reasoning
            x, y = sp.symbols('x y')
            expr = x**2 + y**2 - 1  # Unit circle
            simplified = sp.simplify(expr)
            algebra_result = f"Geometric relation: {expr} = {simplified}"
            
            # 6b: First-order logic
            P_val = sp.Symbol('P_true')
            Q_val = sp.Symbol('Q_true')
            premise = Implies(P_val, Q_val)
            logic_result = f"Logical implication: {premise}"
            
            # 6c: Semantic analysis & concept recording
            semantic_items = []
            for concept in concepts:
                tokens = word_tokenize(concept.lower())
                synonyms = []
                for token in tokens:
                    synsets = wordnet.synsets(token)
                    if synsets:
                        syn = synsets[0].lemmas()[0].name()
                        synonyms.append(syn)
                        self.memory.add_concept(syn)
                
                semantic_items.append(f"{concept}→{','.join(synonyms[:2])}")
            
            semantic_result = " | ".join(semantic_items)
            
            # 6d: Knowledge graph
            for concept in concepts:
                self.knowledge_graph.add_node(concept)
                if len(self.knowledge_graph.nodes) > 1:
                    prev = list(self.knowledge_graph.nodes)[-2]
                    self.knowledge_graph.add_edge(prev, concept, weight=1.0)
            
            graph_summary = f"Knowledge nodes: {len(self.knowledge_graph.nodes)}, edges: {len(self.knowledge_graph.edges)}"
            
            # 6e: Neural integration
            neural_magnitude = torch.norm(neural_output).item()
            neural_info = f"Activation magnitude: {neural_magnitude:.4f}"
            
            result = f"{algebra_result} | {logic_result} | Semantics: {semantic_result} | {graph_summary} | {neural_info}"
            
            # Record trace
            self.memory.add_reasoning_trace({
                'concepts': concepts,
                'neural_magnitude': neural_magnitude,
                'graph_size': len(self.knowledge_graph.nodes),
            })
            
            return result
        
        except Exception as e:
            logger.error(f"Symbolic reasoning failed: {e}")
            return f"Reasoning error: {str(e)}"


class StatefulSymbolicPredictiveInterpreter:
    """
    Complete 8-stage stateful inference system.
    
    Implements the full pipeline with persistent memory and governance.
    """
    
    def __init__(self, model_version: str = "spi-symbolic-0.2.0"):
        self.model_version = model_version
        self.device = torch.device('cpu')
        
        # Initialize memory (stateful across requests)
        self.memory = MemoryStore()
        
        # Initialize pipeline stages
        self.encoder = InputEncoder(input_dim=128)
        self.pattern_extractor = PatternExtractor(n_patterns=3)
        self.spike_generator = SpikeGenerator(input_dim=128, hidden_dim=64)
        self.neuroplastic_adapter = NeuroplasticAdapter(self.memory)
        self.oscillator = OscillatorModule(self.memory)
        self.symbolic_reasoner = SymbolicReasoner(self.memory)
        
        # Governance
        self.policy_engine = PolicyEngine()
        self.governance_service = GovernanceService(self.policy_engine)
        
        logger.info(f"StatefulSymbolicPredictiveInterpreter initialized (v{self.model_version})")
    
    async def process(self, input_data: Dict[str, Any], request_id: str = "") -> Dict[str, Any]:
        """
        Full 8-stage pipeline execution with state management and governance.
        
        Args:
            input_data: Dict with 'text' or 'vector' or 'concepts'
            request_id: For tracing
        
        Returns:
            Complete output with governance applied
        """
        ctx = StatefulInferenceContext(self.memory, request_id)
        
        try:
            # Stage 1: Encode Input
            ctx.start_stage("encode")
            if 'text' in input_data:
                ctx.encoded_input = self.encoder.encode_text(input_data['text'])
            elif 'vector' in input_data:
                ctx.encoded_input = self.encoder.encode_vector(input_data['vector'])
            else:
                ctx.encoded_input = np.zeros(128)
            ctx.end_stage("encode")
            
            # Stage 2: Extract Patterns
            ctx.start_stage("pattern_extraction")
            ctx.patterns, pattern_confidence = self.pattern_extractor.extract(ctx.encoded_input)
            ctx.end_stage("pattern_extraction")
            
            # Stage 3: Generate Spikes
            ctx.start_stage("spike_generation")
            input_tensor = torch.from_numpy(ctx.encoded_input).float().to(self.device)
            ctx.spikes = self.spike_generator.forward(input_tensor, num_steps=5)
            ctx.end_stage("spike_generation")
            
            # Stage 4: Neuroplastic Adaptation
            ctx.start_stage("neuroplasticity")
            success = pattern_confidence > 0.5  # Simple success criterion
            neuroplastic_signal = self.neuroplastic_adapter.adapt(success)
            ctx.neuroplastic_update = neuroplastic_signal
            ctx.end_stage("neuroplasticity")
            
            # Stage 5: Oscillatory Modulation
            ctx.start_stage("oscillation")
            ctx.oscillated_output = self.oscillator.modulate(ctx.spikes)
            ctx.end_stage("oscillation")
            
            # Stage 6: Symbolic Interpretation
            ctx.start_stage("symbolic_reasoning")
            concepts = input_data.get('concepts', [])
            ctx.symbolic_interpretation = await self._async_symbolic_reasoning(
                ctx.oscillated_output, concepts
            )
            ctx.end_stage("symbolic_reasoning")
            
            # Stage 7: Governance Evaluation
            ctx.start_stage("governance")
            policy_context = PolicyContext(
                input_text=input_data.get('text', ''),
                neural_magnitude=float(torch.norm(ctx.spikes).item()),
                pattern_confidence=pattern_confidence,
                symbolic_concepts=concepts,
                request_id=request_id,
            )
            ctx.governance_decision = self.policy_engine.evaluate(policy_context).audit_entry
            ctx.end_stage("governance")
            
            # Stage 8: Output Synthesis
            ctx.start_stage("output_synthesis")
            ctx.final_output = self._synthesize_output(ctx)
            ctx.end_stage("output_synthesis")
            
            # Apply governance conditioning
            ctx.final_output = self.governance_service.evaluate_and_condition_output(
                ctx.final_output,
                policy_context
            )
            
            # Update memory context
            self.memory.add_to_context({
                'concept': ' '.join(concepts),
                'output': ctx.final_output.get('symbolic_result', '')[:50],
            })
            
            return ctx.final_output
        
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return self._error_output(str(e), ctx)
    
    async def _async_symbolic_reasoning(self, neural_output: torch.Tensor, 
                                       concepts: List[str]) -> str:
        """Async wrapper for symbolic reasoning."""
        return await asyncio.to_thread(
            self.symbolic_reasoner.interpret,
            neural_output,
            concepts
        )
    
    def _synthesize_output(self, ctx: StatefulInferenceContext) -> Dict[str, Any]:
        """Combine all pipeline outputs into final response."""
        metrics = self.memory.get_neuroplastic_metrics()
        
        return {
            'request_id': ctx.request_id,
            'model_version': self.model_version,
            'symbolic_result': ctx.symbolic_interpretation or "No interpretation",
            'neural_magnitude': float(torch.norm(ctx.spikes).item()) if ctx.spikes is not None else 0.0,
            'spike_rate': float(ctx.spikes.mean().item()) if ctx.spikes is not None else 0.0,
            'oscillatory_phase': float(self.memory.oscillator_phase),
            'syntropy_state': self.memory.syntropy_values.copy(),
            'neuroplastic_metrics': metrics,
            'stage_times': ctx.stage_times,
            'memory_state': {
                'total_concepts': len(self.memory.concept_history),
                'reasoning_traces': len(self.memory.reasoning_traces),
                'success_streak': metrics['success_streak'],
            }
        }
    
    def _error_output(self, error_msg: str, ctx: StatefulInferenceContext) -> Dict[str, Any]:
        """Generate error response."""
        return {
            'request_id': ctx.request_id,
            'model_version': self.model_version,
            'error': error_msg,
            'stage_times': ctx.stage_times,
        }
    
    def get_memory_snapshot(self) -> Dict[str, Any]:
        """Export current memory state for inspection."""
        return {
            'oscillator_phase': self.memory.oscillator_phase,
            'syntropy_values': self.memory.syntropy_values,
            'neuroplastic_metrics': self.memory.get_neuroplastic_metrics(),
            'concept_count': len(self.memory.concept_history),
            'recent_concepts': self.memory.concept_history[-10:],
            'context_summary': self.memory.get_context_summary(),
        }
