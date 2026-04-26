import asyncio
import logging
import random
import re
import time
import json
import math
import numpy as np
import sympy as sp
from sympy.logic.boolalg import And, Or, Not, Implies
from sympy import symbols
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import snntorch as snn
from snntorch import surrogate
import networkx as nx
from scipy.fft import fft, fftfreq
from scipy.integrate import solve_ivp
from scipy.stats import variation
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from collections import Counter, deque
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet

try:
    from utils.atlantean_runtime import Runtime as AtlanteanRuntime, CoordinationTask
    ATLANTEAN_AVAILABLE = True
except Exception:
    ATLANTEAN_AVAILABLE = False

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('wordnet')

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pattern Recognition Module ---
class PatternModule:
    def __init__(self, n_clusters=3):
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    
    def extract_patterns(self, data: np.ndarray) -> np.ndarray:
        data = data.reshape(-1, 1) if data.ndim == 1 else data
        if len(data) < self.kmeans.n_clusters:
            return np.zeros(self.kmeans.n_clusters)
        return self.kmeans.fit_predict(data)

# --- Neuroplasticity Manager ---
class NeuroplasticityManager:
    def __init__(self, oscillator, core_field, syntropy_engine):
        self.oscillator = oscillator
        self.core_field = core_field
        self.syntropy_engine = syntropy_engine
        self.pattern_module = None
        self.symbolic_interpreter = None
        self.train_controls: Dict[str, bool] = {
            'plasticity_enabled': True,
            'field_feedback_enabled': True,
            'pattern_coupling_enabled': True,
            'symbolic_coupling_enabled': True,
            'component_logging_enabled': True,
        }
        self.data_queue = deque(maxlen=100)
        self.stability_threshold = 0.05

    async def learn_async(self, streamed_text: str):
        feature_vector = self.oscillator.process_streamed_data(streamed_text)
        self.data_queue.append(feature_vector)
        synthetic_data = self.oscillator.generate_synthetic_data(num_samples=10)

        symbolic_score = 0.0
        if self.symbolic_interpreter is not None:
            try:
                concepts = streamed_text.split()[:10]
                symbolic_result = await self.symbolic_interpreter.predict(concepts, self.core_field.get_state())
                symbolic_score = min(1.0, len(concepts) / 10.0)
                if 'failed' in symbolic_result.lower() or 'error' in symbolic_result.lower():
                    symbolic_score *= 0.5
            except Exception:
                symbolic_score = 0.0

        train_out = self.oscillator.train(
            synthetic_data,
            streamed_text,
            epochs=5,
            controls=self.train_controls,
            pattern_module=self.pattern_module,
            symbolic_score=symbolic_score,
            return_details=True,
        )
        reward = train_out['avg_reward']
        field_update = np.mean([v.cpu().numpy() for v in self.data_queue], axis=0)
        self.core_field.update_with_vibrational_mode(field_update)
        field_var = torch.var(self.core_field.get_state()).item()
        if field_var > self.stability_threshold:
            logger.info(f"High variance ({field_var:.4f}) detected. Reducing input rate.")
            await asyncio.sleep(2)
        logger.info(f"Neuroplasticity update completed. Reward: {reward:.4f}")
        self.oscillator.update_q_table(reward)

    def regulate_syntropy(self):
        for i in range(self.syntropy_engine.num_fields):
            field_mean = np.mean(self.syntropy_engine.field_data[i])
            if abs(field_mean - 0.5) > 0.1:
                self.syntropy_engine.field_data[i] += (0.5 - field_mean) * 0.1
                self.syntropy_engine.field_data[i] = np.clip(self.syntropy_engine.field_data[i], -1, 1)
        logger.info("Syntropy regulation applied.")

# --- Symbolic Interpreter Module ---
@dataclass
class SymbolicConfig:
    population_size: int = 12
    generations: int = 6
    alpha: float = 1.0
    beta: float = 0.1
    gamma: float = 0.2

class SymbolicPredictiveInterpreter:
    def __init__(self, pattern_module, core_field, config: SymbolicConfig):
        self.pattern_module = pattern_module
        self.core_field = core_field
        self.config = config
        self.x, self.y = sp.symbols('x y')
        self.P, self.Q = sp.symbols('P Q', cls=sp.Function)
        self.z = sp.Symbol('z')
        self.knowledge_graph = nx.DiGraph()
        logger.info("Symbolic Predictive Interpreter initialized with knowledge graph.")

    def build_knowledge_graph(self, concepts: List[str], neural_output: torch.Tensor):
        """Build a knowledge graph from concepts and neural output."""
        self.knowledge_graph.clear()
        for concept in concepts:
            tokens = word_tokenize(concept.lower())
            for token in tokens:
                self.knowledge_graph.add_node(token)
                synsets = wordnet.synsets(token)
                for syn in synsets[:2]:
                    synonym = syn.lemmas()[0].name()
                    self.knowledge_graph.add_node(synonym)
                    self.knowledge_graph.add_edge(token, synonym, relation="synonym")
        neural_mean = torch.mean(neural_output).item()
        self.knowledge_graph.add_node("neural_state")
        self.knowledge_graph.add_edge("neural_state", concepts[0] if concepts else "default", relation="influences", weight=neural_mean)

    def query_knowledge_graph(self):
        """Query the knowledge graph for related concepts."""
        if not self.knowledge_graph.nodes:
            return "Empty knowledge graph."
        try:
            central_node = max(self.knowledge_graph.nodes, key=lambda n: self.knowledge_graph.degree(n))
            related = list(self.knowledge_graph.neighbors(central_node))
            return f"Central concept: {central_node}, related: {related}"
        except Exception as e:
            return f"Graph query failed: {e}"

    async def predict(self, concepts: List[str], neural_output: torch.Tensor) -> str:
        logger.info(f"Symbolic interpreter processing concepts: {concepts}")
        try:
            expr = self.x**2 - self.y**2
            factored = sp.factor(expr)
            proof_result = f"Proved: {expr} = {factored}"
            # Simplified logic representation without ForAll
            P_val = sp.Symbol('P_true')
            Q_val = sp.Symbol('Q_true')
            premise = Implies(P_val, Q_val)
            logic_result = f"Evaluated: P(True) => Q(True) = {premise}"
            semantic_result = []
            for concept in concepts:
                tokens = word_tokenize(concept.lower())
                synonyms = []
                for token in tokens:
                    synsets = wordnet.synsets(token)
                    if synsets:
                        synonyms.append(synsets[0].lemmas()[0].name())
                semantic_result.append(f"Concept '{concept}' mapped to synonyms: {synonyms[:3]}")
            self.build_knowledge_graph(concepts, neural_output)
            graph_result = self.query_knowledge_graph()
            neural_mean = torch.mean(neural_output).item()
            cluster_result = self.pattern_module.extract_patterns(neural_output.cpu().numpy().flatten())
            neural_integration = f"Neural input (mean={neural_mean:.4f}) clustered into {len(set(cluster_result))} groups."
            result = (f"Algebraic proof: {proof_result}. "
                     f"First-order logic: {logic_result}. "
                     f"Semantic reasoning: {'; '.join(semantic_result)}. "
                     f"Knowledge graph: {graph_result}. "
                     f"Neural integration: {neural_integration}")
        except Exception as e:
            result = f"Symbolic reasoning failed: {e}. Using {len(concepts)} concepts."
        await asyncio.sleep(0.1)
        return result

# --- Spiking Neural Network Components ---
class SpikingFieldUpdateNN(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, beta: float = 0.95):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.lif1 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())
        self.fc3 = nn.Linear(hidden_size, input_size)
        self.lif3 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())

    def forward(self, x: torch.Tensor, num_steps: int = 10) -> torch.Tensor:
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()
        mem3 = self.lif3.init_leaky()
        spk3_rec = []
        for _ in range(num_steps):
            cur1 = self.fc1(x)
            spk1, mem1 = self.lif1(cur1, mem1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            cur3 = self.fc3(spk2)
            spk3, mem3 = self.lif3(cur3, mem3)
            spk3_rec.append(spk3)
        return torch.stack(spk3_rec).mean(dim=0)

    def update_field(self, field: torch.Tensor, chaos_threshold: float = 0.1) -> torch.Tensor:
        update = self.forward(field)
        if torch.var(field) > chaos_threshold:
            update *= 0.5
        return field + update

class SpikingSyntropyNN(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 32, beta: float = 0.95):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.lif1 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())
        self.fc3 = nn.Linear(hidden_size, input_size)
        self.lif3 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())

    def forward(self, x: torch.Tensor, num_steps: int = 10) -> torch.Tensor:
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()
        mem3 = self.lif3.init_leaky()
        spk3_rec = []
        for _ in range(num_steps):
            cur1 = self.fc1(x)
            spk1, mem1 = self.lif1(cur1, mem1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            cur3 = self.fc3(spk2)
            spk3, mem3 = self.lif3(cur3, mem3)
            spk3_rec.append(spk3)
        return torch.stack(spk3_rec).mean(dim=0)

    def adjust_syntropy(self, field: torch.Tensor, target_mean: float = 0.5, speed_factor: float = 0.5) -> torch.Tensor:
        adjustment = (target_mean - torch.mean(field)) * speed_factor
        delta = self.forward(torch.full_like(field, torch.mean(field)))
        return field + delta * adjustment * 0.5

class SpikingFeedbackNN(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 48, beta: float = 0.95):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.lif1 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.lif2 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())
        self.fc3 = nn.Linear(hidden_size, 1)
        self.lif3 = snn.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid())

    def forward(self, x: torch.Tensor, num_steps: int = 10) -> torch.Tensor:
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()
        mem3 = self.lif3.init_leaky()
        spk3_rec = []
        for _ in range(num_steps):
            cur1 = self.fc1(x)
            spk1, mem1 = self.lif1(cur1, mem1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            cur3 = self.fc3(spk2)
            spk3, mem3 = self.lif3(cur3, mem3)
            spk3_rec.append(spk3)
        return torch.stack(spk3_rec).mean(dim=0)

    def penalize_variance(self, field: torch.Tensor) -> torch.Tensor:
        variance = torch.var(field)
        penalty = self.forward(torch.full((1, field.size(0)), variance.item())).item()
        return field - penalty * variance


class FieldPDE:
    """Convolution-based PDE field solver for excitability (phi1) and resource (phi5)."""

    def __init__(
        self,
        field_size: int,
        device: torch.device,
        alpha: float = 1.5,
        beta: float = 0.08,
        gamma1: float = 0.35,
        zeta: float = 0.15,
        omega: float = 0.15,
        gamma5: float = 0.10,
        theta: float = 0.30,
        dt: float = 0.01,
        relaxation: float = 0.2,
        eps: float = 1e-8,
    ):
        self.field_size = field_size
        self.device = device
        self.alpha = alpha
        self.beta = beta
        self.gamma1 = gamma1
        self.zeta = zeta
        self.omega = omega
        self.gamma5 = gamma5
        self.theta = theta
        self.dt = dt
        self.relaxation = relaxation
        self.eps = eps

        self.height, self.width = self._grid_shape(field_size)
        self.lap_kernel = torch.tensor(
            [[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]],
            dtype=torch.float32,
            device=self.device,
        ).view(1, 1, 3, 3)

        self.phi1 = (torch.randn(1, 1, self.height, self.width, device=self.device) * 0.15).float()
        self.phi5 = (0.05 + 0.15 * torch.rand(1, 1, self.height, self.width, device=self.device)).float()
        self.Phi = torch.zeros(1, 1, self.height, self.width, device=self.device).float()
        self.last_stats: Dict[str, float] = {
            'max_abs_dphi1': 0.0,
            'max_abs_dphi5': 0.0,
            'adaptive_dt': self.dt,
        }

    def _grid_shape(self, n: int) -> (int, int):
        side = int(math.sqrt(n))
        for h in range(side, 0, -1):
            if n % h == 0:
                return h, n // h
        return 1, n

    def _to_grid(self, vec: torch.Tensor) -> torch.Tensor:
        return vec.reshape(1, 1, self.height, self.width)

    def _to_vec(self, grid: torch.Tensor) -> torch.Tensor:
        return grid.reshape(-1)

    def laplacian(self, grid: torch.Tensor) -> torch.Tensor:
        padded = F.pad(grid, (1, 1, 1, 1), mode='circular')
        return F.conv2d(padded, self.lap_kernel)

    def bi_laplacian(self, grid: torch.Tensor) -> torch.Tensor:
        return self.laplacian(self.laplacian(grid))

    def update_global_potential(self, spike_like: torch.Tensor):
        with torch.no_grad():
            spike_grid = self._to_grid(spike_like.detach().to(self.device))
            self.Phi = 0.85 * self.Phi + 0.15 * spike_grid
            self.Phi = torch.clamp(self.Phi, -3.0, 3.0)

    def pde_step(self, dt: Optional[float] = None, spike_feedback: Optional[torch.Tensor] = None):
        with torch.no_grad():
            local_dt = self.dt if dt is None else dt

            lap_phi1 = self.laplacian(self.phi1)
            bi_lap_phi1 = self.bi_laplacian(self.phi1)
            lap_phi5 = self.laplacian(self.phi5)
            lap_Phi = self.laplacian(self.Phi)

            reaction = -self.alpha * (self.phi1 ** 3) + self.zeta * lap_Phi
            diffusion = -self.gamma1 * lap_phi1 + self.beta * bi_lap_phi1
            d_phi1 = diffusion + reaction

            log_term = self.omega * self.phi5 * torch.log(torch.abs(self.phi5) + self.eps)
            advection = self.theta * (lap_phi5 * self.Phi + self.phi5 * lap_Phi)
            d_phi5 = -self.gamma5 * lap_phi5 + log_term + advection

            max_abs_dphi1 = float(torch.max(torch.abs(d_phi1)).item())
            max_abs_dphi5 = float(torch.max(torch.abs(d_phi5)).item())
            max_abs = max(max_abs_dphi1, max_abs_dphi5)
            if max_abs > 1.0:
                local_dt = local_dt * max(0.1, 1.0 / max_abs)

            phi1_candidate = self.phi1 + d_phi1 * local_dt
            phi5_candidate = self.phi5 + d_phi5 * local_dt

            self.phi1 = (1.0 - self.relaxation) * self.phi1 + self.relaxation * phi1_candidate
            self.phi5 = (1.0 - self.relaxation) * self.phi5 + self.relaxation * phi5_candidate

            self.phi1 = torch.clamp(self.phi1, -3.0, 3.0)
            self.phi5 = torch.clamp(self.phi5, 1e-6, 5.0)

            if spike_feedback is not None:
                self.update_global_potential(spike_feedback)
            else:
                self.Phi = 0.995 * self.Phi

            self.last_stats = {
                'max_abs_dphi1': max_abs_dphi1,
                'max_abs_dphi5': max_abs_dphi5,
                'adaptive_dt': float(local_dt),
            }

    def get_modulators(self) -> Dict[str, torch.Tensor]:
        phi1_vec = self._to_vec(self.phi1)
        phi5_vec = self._to_vec(self.phi5)
        threshold_shift = torch.clamp(0.5 * phi1_vec, -1.0, 1.0)
        leak_scale = torch.clamp(1.0 / (1.0 + phi5_vec), 0.2, 2.0)
        input_gain = torch.clamp(1.0 + 0.5 * phi5_vec, 0.5, 2.5)
        return {
            'threshold_shift': threshold_shift,
            'leak_scale': leak_scale,
            'input_gain': input_gain,
        }

    def get_state_summary(self) -> Dict[str, float]:
        return {
            'phi1_mean': float(torch.mean(self.phi1).item()),
            'phi1_var': float(torch.var(self.phi1).item()),
            'phi5_mean': float(torch.mean(self.phi5).item()),
            'phi5_var': float(torch.var(self.phi5).item()),
            'Phi_mean': float(torch.mean(self.Phi).item()),
            'Phi_var': float(torch.var(self.Phi).item()),
            'max_abs_dphi1': self.last_stats.get('max_abs_dphi1', 0.0),
            'max_abs_dphi5': self.last_stats.get('max_abs_dphi5', 0.0),
            'adaptive_dt': self.last_stats.get('adaptive_dt', self.dt),
            'grid_h': float(self.height),
            'grid_w': float(self.width),
        }

    def export_state(self) -> Dict[str, Any]:
        return {
            'phi1': self.phi1.detach().cpu(),
            'phi5': self.phi5.detach().cpu(),
            'Phi': self.Phi.detach().cpu(),
            'height': self.height,
            'width': self.width,
            'params': {
                'alpha': self.alpha,
                'beta': self.beta,
                'gamma1': self.gamma1,
                'zeta': self.zeta,
                'omega': self.omega,
                'gamma5': self.gamma5,
                'theta': self.theta,
                'dt': self.dt,
                'relaxation': self.relaxation,
            },
        }

    def load_state(self, state: Dict[str, Any]):
        if not state:
            return
        self.phi1 = state.get('phi1', self.phi1.cpu()).to(self.device)
        self.phi5 = state.get('phi5', self.phi5.cpu()).to(self.device)
        self.Phi = state.get('Phi', self.Phi.cpu()).to(self.device)
        params = state.get('params', {})
        for key in ['alpha', 'beta', 'gamma1', 'zeta', 'omega', 'gamma5', 'theta', 'dt', 'relaxation']:
            if key in params:
                setattr(self, key, float(params[key]))

# --- Core Theoretical Engines ---
class OscillatorySynapseTheory:
    def __init__(self, field_size: int = 100, device: str = 'cpu'):
        self.device = torch.device(device)
        self.field = torch.randn(field_size, device=self.device) * 0.1
        self.nn1 = SpikingFieldUpdateNN(field_size).to(self.device)
        self.nn2 = SpikingSyntropyNN(field_size).to(self.device)
        self.nn3 = SpikingFeedbackNN(field_size).to(self.device)
        self.optimizer1 = optim.Adam(self.nn1.parameters(), lr=0.001)
        self.optimizer2 = optim.Adam(self.nn2.parameters(), lr=0.001)
        self.optimizer3 = optim.Adam(self.nn3.parameters(), lr=0.001)
        self.base_lrs = {
            'optimizer1': 0.001,
            'optimizer2': 0.001,
            'optimizer3': 0.001,
        }
        self.balanced = False
        self.message_queue = deque(maxlen=10)
        # Q-learning setup
        self.q_table = {}  # State-action value table
        self.actions = ['update_field', 'adjust_syntropy', 'penalize_variance']
        self.alpha = 0.1  # Learning rate
        self.gamma = 0.9  # Discount factor
        self.epsilon = 0.1  # Exploration rate
        self.component_update_log = deque(maxlen=200)
        self.last_train_details: Dict[str, Any] = {}
        self.field_pde = FieldPDE(field_size=field_size, device=self.device)
        self.atlantean_runtime = AtlanteanRuntime(num_channels=4, num_domains=6, task_spec=CoordinationTask()) if ATLANTEAN_AVAILABLE else None

    def _runtime_trace_slice(self, field: torch.Tensor, action: str, enabled: bool) -> List[int]:
        if not enabled or self.atlantean_runtime is None:
            return []
        rt = self.atlantean_runtime
        start = len(rt.trace)
        ch = self.actions.index(action) % rt.num_channels
        dm = self.field_pde.field_size % rt.num_domains
        val = float(torch.mean(field.detach()).item())
        rt.emit_state(val, ch, dm, tag="snn_update")
        rt.tick_states()
        return list(range(start, len(rt.trace)))

    def _component_attribution(
        self,
        *,
        plasticity_enabled: bool,
        field_feedback_enabled: bool,
        pattern_coupling_enabled: bool,
        symbolic_coupling_enabled: bool,
        plasticity_scale: float,
        pattern_loss: torch.Tensor,
        symbolic_loss: torch.Tensor,
        feedback_loss: torch.Tensor,
    ) -> Dict[str, bool]:
        pde_stats = self.field_pde.last_stats
        return {
            'plasticity': bool(plasticity_enabled and abs(plasticity_scale - 1.0) > 1e-3),
            'feedback': bool(field_feedback_enabled and float(feedback_loss.item()) > 1e-8),
            'pattern': bool(pattern_coupling_enabled and float(pattern_loss.item()) > 1e-8),
            'symbolic': bool(symbolic_coupling_enabled and float(symbolic_loss.item()) > 1e-8),
            'pde': bool(
                pde_stats.get('max_abs_dphi1', 0.0) > 1e-8
                or pde_stats.get('max_abs_dphi5', 0.0) > 1e-8
            ),
        }

    def generate_synthetic_data(self, num_samples: int = 100) -> torch.Tensor:
        return torch.randn(num_samples, self.field.size(0), device=self.device) * 0.1

    def process_streamed_data(self, text: str) -> torch.Tensor:
        """Convert text to a dense feature vector using hashing trick + bigrams."""
        n = self.field.size(0)
        words = text.lower().split()
        total = len(words) + 1
        feature_vector = np.zeros(n, dtype=np.float32)
        for i, word in enumerate(words):
            tf_weight = 1.0 / total
            feature_vector[hash(word) % n] += tf_weight
            if i < len(words) - 1:
                bigram = word + '_' + words[i + 1]
                feature_vector[hash(bigram) % n] += 0.5 * tf_weight
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector /= norm
        return torch.tensor(feature_vector, dtype=torch.float32, device=self.device)

    def get_state_key(self, field: torch.Tensor, pattern_module=None) -> str:
        """Discretize state using mean/variance/energy/zero-crossings + KMeans pattern bins."""
        arr = field.detach().cpu().numpy()
        n = max(arr.shape[0], 1)
        mean_bin = int(np.clip((arr.mean() + 1.0) * 5.0, 0, 9))
        var_bin = int(np.clip(arr.var() * 20.0, 0, 9))
        energy_bin = int(np.clip(np.mean(np.abs(arr)) * 10.0, 0, 9))
        zero_crossings = np.sum(np.diff(np.signbit(arr)).astype(np.int32))
        zc_bin = int(np.clip((zero_crossings / n) * 10.0, 0, 9))

        pattern_bin = 0
        pattern_entropy_bin = 0
        if pattern_module is not None:
            try:
                labels = pattern_module.extract_patterns(arr)
                labels = np.array(labels).astype(int)
                if labels.size > 0:
                    counts = np.bincount(labels, minlength=pattern_module.kmeans.n_clusters)
                    probs = counts / max(np.sum(counts), 1)
                    entropy = -np.sum(probs * np.log(probs + 1e-8))
                    pattern_bin = int(np.argmax(counts))
                    pattern_entropy_bin = int(np.clip(entropy * 3.0, 0, 9))
            except Exception:
                pass

        top_idx = np.argsort(np.abs(arr))[-5:]
        seg_size = max(n // 5, 1)
        top_segs = tuple(sorted((top_idx // seg_size).tolist()))

        # PDE-aware state enrichment to reduce action collapse.
        pde_summary = self.field_pde.get_state_summary()
        phi1_bin = int(np.clip((pde_summary['phi1_mean'] + 1.0) * 5.0, 0, 9))
        phi5_bin = int(np.clip(pde_summary['phi5_mean'] * 5.0, 0, 9))
        phi1_var_bin = int(np.clip(pde_summary['phi1_var'] * 20.0, 0, 9))
        phi5_var_bin = int(np.clip(pde_summary['phi5_var'] * 20.0, 0, 9))

        phi1_vec = self.field_pde.phi1.detach().cpu().numpy().reshape(-1)
        phi5_vec = self.field_pde.phi5.detach().cpu().numpy().reshape(-1)

        # Active region features for phase-separated patterns/memory packets.
        phi1_active_ratio = float(np.mean(np.abs(phi1_vec) > 0.35))
        phi5_active_ratio = float(np.mean(phi5_vec > 0.20))
        phi1_active_bin = int(np.clip(phi1_active_ratio * 10.0, 0, 9))
        phi5_active_bin = int(np.clip(phi5_active_ratio * 10.0, 0, 9))

        phi1_cluster_bin = 0
        phi5_cluster_bin = 0
        if pattern_module is not None:
            try:
                phi1_labels = np.array(pattern_module.extract_patterns(phi1_vec)).astype(int)
                phi5_labels = np.array(pattern_module.extract_patterns(phi5_vec)).astype(int)
                phi1_cluster_bin = int(np.clip(len(np.unique(phi1_labels)), 0, 9))
                phi5_cluster_bin = int(np.clip(len(np.unique(phi5_labels)), 0, 9))
            except Exception:
                pass

        return (
            f"{mean_bin}_{var_bin}_{energy_bin}_{zc_bin}_{pattern_bin}_{pattern_entropy_bin}_"
            f"{phi1_bin}_{phi1_var_bin}_{phi1_active_bin}_{phi1_cluster_bin}_"
            f"{phi5_bin}_{phi5_var_bin}_{phi5_active_bin}_{phi5_cluster_bin}_{top_segs}"
        )

    def choose_action(self, state: str) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        q_vals = self.q_table.get(state, {a: 0.0 for a in self.actions})
        max_q = max(q_vals.values())
        best_actions = [a for a, q in q_vals.items() if q == max_q]
        return random.choice(best_actions)

    def update_q_table(self, reward: float, old_state: str = None, action: str = None, new_state: str = None):
        if old_state and action:
            if old_state not in self.q_table:
                self.q_table[old_state] = {a: 0 for a in self.actions}
            if new_state is None:
                new_state = self.get_state_key(self.field)
            if new_state not in self.q_table:
                self.q_table[new_state] = {a: 0 for a in self.actions}
            self.q_table[old_state][action] += self.alpha * (
                reward + self.gamma * max(self.q_table[new_state].values()) - self.q_table[old_state][action]
            )

    def train(
        self,
        synthetic_data: torch.Tensor,
        streamed_text: Optional[str] = None,
        epochs: int = 10,
        controls: Optional[Dict[str, bool]] = None,
        pattern_module=None,
        symbolic_score: float = 0.0,
        return_details: bool = False,
    ) -> Any:
        controls = controls or {}
        plasticity_enabled = controls.get('plasticity_enabled', True)
        field_feedback_enabled = controls.get('field_feedback_enabled', True)
        pattern_coupling_enabled = controls.get('pattern_coupling_enabled', True)
        symbolic_coupling_enabled = controls.get('symbolic_coupling_enabled', True)
        component_logging_enabled = controls.get('component_logging_enabled', True)
        atlantean_enabled = controls.get('atlantean_enabled', True)

        logger.info("Starting spiking neural network training...")
        total_reward = 0
        component_sums = {
            'base_loss': 0.0,
            'pattern_loss': 0.0,
            'symbolic_loss': 0.0,
            'feedback_loss': 0.0,
        }
        update_count = 0

        for p in self.nn1.parameters():
            p.requires_grad = plasticity_enabled
        for p in self.nn2.parameters():
            p.requires_grad = plasticity_enabled
        for p in self.nn3.parameters():
            p.requires_grad = plasticity_enabled

        if plasticity_enabled:
            for pg in self.optimizer1.param_groups:
                if pg['lr'] == 0.0:
                    pg['lr'] = self.base_lrs['optimizer1']
            for pg in self.optimizer2.param_groups:
                if pg['lr'] == 0.0:
                    pg['lr'] = self.base_lrs['optimizer2']
            for pg in self.optimizer3.param_groups:
                if pg['lr'] == 0.0:
                    pg['lr'] = self.base_lrs['optimizer3']
        else:
            for pg in self.optimizer1.param_groups:
                pg['lr'] = 0.0
            for pg in self.optimizer2.param_groups:
                pg['lr'] = 0.0
            for pg in self.optimizer3.param_groups:
                pg['lr'] = 0.0

        for epoch in range(epochs):
            self.optimizer1.zero_grad()
            self.optimizer2.zero_grad()
            self.optimizer3.zero_grad()
            total_loss = 0

            pde_summary = self.field_pde.get_state_summary()
            plasticity_scale = float(np.clip(1.0 + 0.3 * (pde_summary['phi5_mean'] - 0.1), 0.5, 2.0))
            if plasticity_enabled:
                for pg in self.optimizer1.param_groups:
                    pg['lr'] = self.base_lrs['optimizer1'] * plasticity_scale
                for pg in self.optimizer2.param_groups:
                    pg['lr'] = self.base_lrs['optimizer2'] * plasticity_scale
                for pg in self.optimizer3.param_groups:
                    pg['lr'] = self.base_lrs['optimizer3'] * plasticity_scale

            state = self.get_state_key(self.field, pattern_module=pattern_module)
            for data in synthetic_data:
                self.field_pde.pde_step()
                modulators = self.field_pde.get_modulators()
                mod_data = data * modulators['input_gain']
                action = self.choose_action(state)
                if not field_feedback_enabled and action == 'penalize_variance':
                    action = 'update_field'

                if action == 'update_field':
                    field = self.nn1.update_field(mod_data)
                elif action == 'adjust_syntropy':
                    field = self.nn2.adjust_syntropy(mod_data)
                else:
                    field = self.nn3.penalize_variance(mod_data)
                self.field_pde.update_global_potential(torch.sigmoid(field.detach()))

                if action == 'update_field':
                    threshold_penalty = torch.mean(torch.relu(torch.abs(field) - (1.0 + torch.abs(modulators['threshold_shift']))))
                    base_loss = torch.mean((field - mod_data[:field.shape[0]]) ** 2) + 0.1 * threshold_penalty
                elif action == 'adjust_syntropy':
                    probs = torch.softmax(field, dim=0) + 1e-8
                    leak_reg = torch.mean(torch.abs(field * modulators['leak_scale'] - field))
                    base_loss = torch.sum(probs * torch.log(probs)) + 0.1 * leak_reg
                else:
                    var_weight = torch.mean(modulators['leak_scale'])
                    base_loss = var_weight * torch.var(field) + torch.abs(torch.mean(field))

                pattern_loss = torch.tensor(0.0, device=self.device)
                if pattern_coupling_enabled and pattern_module is not None:
                    try:
                        labels = pattern_module.extract_patterns(field.detach().cpu().numpy())
                        labels = np.array(labels).astype(int)
                        k = max(pattern_module.kmeans.n_clusters, 1)
                        counts = np.bincount(labels, minlength=k).astype(np.float32)
                        probs = counts / max(np.sum(counts), 1.0)
                        uniform = np.full(k, 1.0 / k, dtype=np.float32)
                        pattern_loss = torch.tensor(np.mean(np.abs(probs - uniform)), dtype=torch.float32, device=self.device)
                    except Exception:
                        pattern_loss = torch.tensor(0.0, device=self.device)

                symbolic_loss = torch.tensor(0.0, device=self.device)
                if symbolic_coupling_enabled:
                    symbolic_target = torch.tensor(float(symbolic_score) * 0.5, dtype=torch.float32, device=self.device)
                    symbolic_loss = torch.abs(torch.mean(field) - symbolic_target)

                feedback_loss = torch.tensor(0.0, device=self.device)
                if field_feedback_enabled:
                    feedback_state = self.nn3.penalize_variance(self.field)
                    feedback_loss = torch.mean((field - feedback_state.detach()) ** 2)
                    self.field = 0.7 * self.field + 0.2 * field.detach() + 0.1 * feedback_state.detach()
                else:
                    self.field = field.detach().clone()

                loss = base_loss + 0.2 * pattern_loss + 0.2 * symbolic_loss + 0.1 * feedback_loss
                total_loss += loss
                scalar_loss = max(float(loss.item()), 0.0)
                reward = 1.0 / (1.0 + scalar_loss)
                total_reward += reward
                new_state = self.get_state_key(self.field, pattern_module=pattern_module)
                self.update_q_table(reward, state, action, new_state=new_state)
                state = new_state
                component_sums['base_loss'] += float(base_loss.item())
                component_sums['pattern_loss'] += float(pattern_loss.item())
                component_sums['symbolic_loss'] += float(symbolic_loss.item())
                component_sums['feedback_loss'] += float(feedback_loss.item())
                update_count += 1

                if component_logging_enabled:
                    trace_ids = self._runtime_trace_slice(field, action, atlantean_enabled)
                    influence = self._component_attribution(
                        plasticity_enabled=plasticity_enabled,
                        field_feedback_enabled=field_feedback_enabled,
                        pattern_coupling_enabled=pattern_coupling_enabled,
                        symbolic_coupling_enabled=symbolic_coupling_enabled,
                        plasticity_scale=plasticity_scale,
                        pattern_loss=pattern_loss,
                        symbolic_loss=symbolic_loss,
                        feedback_loss=feedback_loss,
                    )
                    self.component_update_log.append({
                        'action': action,
                        'reward': reward,
                        'state': state,
                        'base_loss': float(base_loss.item()),
                        'pattern_loss': float(pattern_loss.item()),
                        'symbolic_loss': float(symbolic_loss.item()),
                        'feedback_loss': float(feedback_loss.item()),
                        'controls': {
                            'plasticity_enabled': plasticity_enabled,
                            'field_feedback_enabled': field_feedback_enabled,
                            'pattern_coupling_enabled': pattern_coupling_enabled,
                            'symbolic_coupling_enabled': symbolic_coupling_enabled,
                            'atlantean_enabled': atlantean_enabled,
                        },
                        'trace_event_ids': trace_ids,
                        'trace_influence': {
                            'plasticity_trace_events': trace_ids if influence['plasticity'] else [],
                            'feedback_trace_events': trace_ids if influence['feedback'] else [],
                            'symbolic_trace_events': trace_ids if influence['symbolic'] else [],
                            'pattern_trace_events': trace_ids if influence['pattern'] else [],
                            'pde_trace_events': trace_ids if influence['pde'] else [],
                        },
                        'influence_flags': influence,
                    })

            if streamed_text:
                streamed_data = self.process_streamed_data(streamed_text)
                self.field_pde.pde_step()
                modulators = self.field_pde.get_modulators()
                streamed_data = streamed_data * modulators['input_gain']
                action = self.choose_action(state)
                if not field_feedback_enabled and action == 'penalize_variance':
                    action = 'update_field'
                if action == 'update_field':
                    field = self.nn1.update_field(streamed_data)
                elif action == 'adjust_syntropy':
                    field = self.nn2.adjust_syntropy(streamed_data)
                else:
                    field = self.nn3.penalize_variance(streamed_data)
                self.field_pde.update_global_potential(torch.sigmoid(field.detach()))

                if action == 'update_field':
                    threshold_penalty = torch.mean(torch.relu(torch.abs(field) - (1.0 + torch.abs(modulators['threshold_shift']))))
                    base_loss = torch.mean((field - streamed_data[:field.shape[0]]) ** 2) + 0.1 * threshold_penalty
                elif action == 'adjust_syntropy':
                    probs = torch.softmax(field, dim=0) + 1e-8
                    leak_reg = torch.mean(torch.abs(field * modulators['leak_scale'] - field))
                    base_loss = torch.sum(probs * torch.log(probs)) + 0.1 * leak_reg
                else:
                    var_weight = torch.mean(modulators['leak_scale'])
                    base_loss = var_weight * torch.var(field) + torch.abs(torch.mean(field))

                pattern_loss = torch.tensor(0.0, device=self.device)
                if pattern_coupling_enabled and pattern_module is not None:
                    try:
                        labels = pattern_module.extract_patterns(field.detach().cpu().numpy())
                        labels = np.array(labels).astype(int)
                        k = max(pattern_module.kmeans.n_clusters, 1)
                        counts = np.bincount(labels, minlength=k).astype(np.float32)
                        probs = counts / max(np.sum(counts), 1.0)
                        uniform = np.full(k, 1.0 / k, dtype=np.float32)
                        pattern_loss = torch.tensor(np.mean(np.abs(probs - uniform)), dtype=torch.float32, device=self.device)
                    except Exception:
                        pattern_loss = torch.tensor(0.0, device=self.device)

                symbolic_loss = torch.tensor(0.0, device=self.device)
                if symbolic_coupling_enabled:
                    symbolic_target = torch.tensor(float(symbolic_score) * 0.5, dtype=torch.float32, device=self.device)
                    symbolic_loss = torch.abs(torch.mean(field) - symbolic_target)

                feedback_loss = torch.tensor(0.0, device=self.device)
                if field_feedback_enabled:
                    feedback_state = self.nn3.penalize_variance(self.field)
                    feedback_loss = torch.mean((field - feedback_state.detach()) ** 2)
                    self.field = 0.7 * self.field + 0.2 * field.detach() + 0.1 * feedback_state.detach()
                else:
                    self.field = field.detach().clone()

                loss = base_loss + 0.2 * pattern_loss + 0.2 * symbolic_loss + 0.1 * feedback_loss
                total_loss += loss
                scalar_loss = max(float(loss.item()), 0.0)
                reward = 1.0 / (1.0 + scalar_loss)
                total_reward += reward
                new_state = self.get_state_key(self.field, pattern_module=pattern_module)
                self.update_q_table(reward, state, action, new_state=new_state)
                state = new_state
                component_sums['base_loss'] += float(base_loss.item())
                component_sums['pattern_loss'] += float(pattern_loss.item())
                component_sums['symbolic_loss'] += float(symbolic_loss.item())
                component_sums['feedback_loss'] += float(feedback_loss.item())
                update_count += 1

                if component_logging_enabled:
                    trace_ids = self._runtime_trace_slice(field, action, atlantean_enabled)
                    influence = self._component_attribution(
                        plasticity_enabled=plasticity_enabled,
                        field_feedback_enabled=field_feedback_enabled,
                        pattern_coupling_enabled=pattern_coupling_enabled,
                        symbolic_coupling_enabled=symbolic_coupling_enabled,
                        plasticity_scale=plasticity_scale,
                        pattern_loss=pattern_loss,
                        symbolic_loss=symbolic_loss,
                        feedback_loss=feedback_loss,
                    )
                    self.component_update_log.append({
                        'action': action,
                        'reward': reward,
                        'state': state,
                        'base_loss': float(base_loss.item()),
                        'pattern_loss': float(pattern_loss.item()),
                        'symbolic_loss': float(symbolic_loss.item()),
                        'feedback_loss': float(feedback_loss.item()),
                        'controls': {
                            'plasticity_enabled': plasticity_enabled,
                            'field_feedback_enabled': field_feedback_enabled,
                            'pattern_coupling_enabled': pattern_coupling_enabled,
                            'symbolic_coupling_enabled': symbolic_coupling_enabled,
                            'atlantean_enabled': atlantean_enabled,
                        },
                        'trace_event_ids': trace_ids,
                        'trace_influence': {
                            'plasticity_trace_events': trace_ids if influence['plasticity'] else [],
                            'feedback_trace_events': trace_ids if influence['feedback'] else [],
                            'symbolic_trace_events': trace_ids if influence['symbolic'] else [],
                            'pattern_trace_events': trace_ids if influence['pattern'] else [],
                            'pde_trace_events': trace_ids if influence['pde'] else [],
                        },
                        'influence_flags': influence,
                    })

            received_state = self.receive_state()
            if received_state is not None:
                self.field_pde.pde_step()
                modulators = self.field_pde.get_modulators()
                received_state = received_state * modulators['input_gain']
                action = self.choose_action(state)
                if not field_feedback_enabled and action == 'penalize_variance':
                    action = 'update_field'
                if action == 'update_field':
                    field = self.nn1.update_field(received_state)
                elif action == 'adjust_syntropy':
                    field = self.nn2.adjust_syntropy(received_state)
                else:
                    field = self.nn3.penalize_variance(received_state)
                self.field_pde.update_global_potential(torch.sigmoid(field.detach()))
                if action == 'update_field':
                    threshold_penalty = torch.mean(torch.relu(torch.abs(field) - (1.0 + torch.abs(modulators['threshold_shift']))))
                    base_loss = torch.mean((field - received_state[:field.shape[0]]) ** 2) + 0.1 * threshold_penalty
                elif action == 'adjust_syntropy':
                    probs = torch.softmax(field, dim=0) + 1e-8
                    leak_reg = torch.mean(torch.abs(field * modulators['leak_scale'] - field))
                    base_loss = torch.sum(probs * torch.log(probs)) + 0.1 * leak_reg
                else:
                    var_weight = torch.mean(modulators['leak_scale'])
                    base_loss = var_weight * torch.var(field) + torch.abs(torch.mean(field))

                pattern_loss = torch.tensor(0.0, device=self.device)
                if pattern_coupling_enabled and pattern_module is not None:
                    try:
                        labels = pattern_module.extract_patterns(field.detach().cpu().numpy())
                        labels = np.array(labels).astype(int)
                        k = max(pattern_module.kmeans.n_clusters, 1)
                        counts = np.bincount(labels, minlength=k).astype(np.float32)
                        probs = counts / max(np.sum(counts), 1.0)
                        uniform = np.full(k, 1.0 / k, dtype=np.float32)
                        pattern_loss = torch.tensor(np.mean(np.abs(probs - uniform)), dtype=torch.float32, device=self.device)
                    except Exception:
                        pattern_loss = torch.tensor(0.0, device=self.device)

                symbolic_loss = torch.tensor(0.0, device=self.device)
                if symbolic_coupling_enabled:
                    symbolic_target = torch.tensor(float(symbolic_score) * 0.5, dtype=torch.float32, device=self.device)
                    symbolic_loss = torch.abs(torch.mean(field) - symbolic_target)

                feedback_loss = torch.tensor(0.0, device=self.device)
                if field_feedback_enabled:
                    feedback_state = self.nn3.penalize_variance(self.field)
                    feedback_loss = torch.mean((field - feedback_state.detach()) ** 2)
                    self.field = 0.7 * self.field + 0.2 * field.detach() + 0.1 * feedback_state.detach()
                else:
                    self.field = field.detach().clone()

                loss = base_loss + 0.2 * pattern_loss + 0.2 * symbolic_loss + 0.1 * feedback_loss
                total_loss += loss
                scalar_loss = max(float(loss.item()), 0.0)
                reward = 1.0 / (1.0 + scalar_loss)
                total_reward += reward
                new_state = self.get_state_key(self.field, pattern_module=pattern_module)
                self.update_q_table(reward, state, action, new_state=new_state)
                state = new_state
                component_sums['base_loss'] += float(base_loss.item())
                component_sums['pattern_loss'] += float(pattern_loss.item())
                component_sums['symbolic_loss'] += float(symbolic_loss.item())
                component_sums['feedback_loss'] += float(feedback_loss.item())
                update_count += 1

            total_loss /= (len(synthetic_data) + (1 if streamed_text else 0) + (1 if received_state is not None else 0))
            if plasticity_enabled:
                total_loss.backward()
                self.optimizer1.step()
                self.optimizer2.step()
                self.optimizer3.step()
            logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss.item():.4f}, Avg Reward: {total_reward/max(update_count, 1):.4f}")

        avg_components = {
            k: (v / max(update_count, 1)) for k, v in component_sums.items()
        }
        self.last_train_details = {
            'avg_reward': total_reward / max(update_count, 1),
            'updates': update_count,
            'q_table_size': len(self.q_table),
            'component_contributions': avg_components,
            'field_pde': self.field_pde.get_state_summary(),
            'controls': {
                'plasticity_enabled': plasticity_enabled,
                'field_feedback_enabled': field_feedback_enabled,
                'pattern_coupling_enabled': pattern_coupling_enabled,
                'symbolic_coupling_enabled': symbolic_coupling_enabled,
                'component_logging_enabled': component_logging_enabled,
                'atlantean_enabled': atlantean_enabled,
            },
        }
        if component_logging_enabled:
            logger.info(f"Train contribution summary: {self.last_train_details['component_contributions']}")

        return self.last_train_details if return_details else self.last_train_details['avg_reward']

    def share_state(self):
        self.message_queue.append(self.field.clone())
        logger.info("Shared spiking neural network field state.")

    def receive_state(self) -> Optional[torch.Tensor]:
        if self.message_queue:
            return self.message_queue.popleft()
        return None

    def save_weights(self, path: str = "nn_weights.pth"):
        torch.save({
            'nn1': self.nn1.state_dict(),
            'nn2': self.nn2.state_dict(),
            'nn3': self.nn3.state_dict(),
            'field': self.field,
            'q_table': self.q_table,
            'field_pde': self.field_pde.export_state(),
        }, path)
        logger.info(f"Saved neural network weights to {path}")
    
    def load_weights(self, path: str = "nn_weights.pth"):
        checkpoint = torch.load(path)
        self.nn1.load_state_dict(checkpoint['nn1'])
        self.nn2.load_state_dict(checkpoint['nn2'])
        self.nn3.load_state_dict(checkpoint['nn3'])
        self.field = checkpoint['field']
        self.q_table = checkpoint.get('q_table', {})
        self.field_pde.load_state(checkpoint.get('field_pde', {}))
        logger.info(f"Loaded neural network weights from {path}")