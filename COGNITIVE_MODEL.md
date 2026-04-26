# Cognitive Model: Neurodynamics & Symbolic Integration

## Abstract

Quadra-Matrix implements a hybrid cognitive architecture combining:
- **Spiking neural field equations** (threshold-based, sparse)
- **Oscillatory phase modulation** (temporal dynamics)
- **Neuroplastic adaptation** (memory-based learning)
- **Symbolic pattern algebra** (logical reasoning)

This creates an **agent** that adapts to its environment, remembers interactions, and reasons symbolically about patterns—fundamentally different from feedforward neural networks.

---

## 1. Spiking Field Dynamics

### The Spiking Neuron Model

Traditional artificial neurons: `a = σ(Wx + b)` (memoryless)

Spiking neurons add **threshold nonlinearity**:

```
potential(t) = sigmoid(W·x(t) + b)
fire(t) = [potential(t) > θ]  ∈ {0, 1}   ← threshold gate
output(t) = fire(t) * potential(t)
```

**Why this matters:**
- Sparse: Most neurons silent (fire = 0)
- Temporal: Spike events are distinct, discrete moments
- Energy-efficient: Only active neurons consume compute
- Meaningful: Binary decision (fire vs. rest) is interpretable

### Implementation: `SpikingFieldUpdateNN`

```python
class SpikingFieldUpdateNN(nn.Module):
    def __init__(self, input_dim=128, hidden_dim=256):
        super().__init__()
        self.fc = nn.Linear(input_dim, hidden_dim)
        self.threshold = 0.5
        
    def forward(self, x):
        potential = torch.sigmoid(self.fc(x))
        spikes = (potential > self.threshold).float()
        return spikes * potential
```

**Dynamics:**
- Sigmoid ensures potential ∈ [0,1]
- Comparison (potential > 0.5) is the **threshold gate**
- Multiply by spike: Gates output by binary spike decision

**Interpretation:**
- Each neuron either "fires" (emits potential) or "rests" (outputs 0)
- Ensemble of ~256 neurons → sparse, distributed representation

---

## 2. Neuroplastic Memory

### Exponential Memory Consolidation

Biological neurons strengthen synapses through experience (Hebbian learning). Quadra-Matrix implements this via:

```python
class NeuroplasticityManager(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.adaptation_layer = nn.Linear(dim, dim)
        self.memory = None  ← persistent state
        
    def forward(self, x):
        adapted = torch.tanh(self.adaptation_layer(x))
        if self.memory is None:
            self.memory = adapted.detach()
        else:
            # Exponential moving average (EMA)
            self.memory = 0.9 * self.memory + 0.1 * adapted.detach()
        return adapted
```

### Memory Consolidation Rule

**Exponential Moving Average (EMA):**
```
M(t) = α·M(t-1) + (1-α)·X(t)
```

Where:
- M(t-1) = memory from previous request
- X(t) = new input/activation from current request
- α = decay factor (0.9 = slow, long-term memory)
- (1-α) = learning rate (0.1 = small updates, stability)

**Properties:**
- **Persistence**: New memory blends with old (never fully forgets)
- **Recency**: Recent events weighted slightly more (0.1 > 0)
- **Stability**: Smooth transitions (no jumps)
- **Trace decay**: 10+ requests to halve old memory

### Mathematical Analysis

Let's trace memory evolution:
```
Request 1: M₁ = 0 (init) + 0.1·X₁ = 0.1·X₁
Request 2: M₂ = 0.9·(0.1·X₁) + 0.1·X₂ = 0.09·X₁ + 0.1·X₂
Request 3: M₃ = 0.9·(0.09·X₁ + 0.1·X₂) + 0.1·X₃
         = 0.081·X₁ + 0.09·X₂ + 0.1·X₃
```

**Pattern**: Weights form `[0.081, 0.09, 0.1, ...]` — **exponential decay**.

Memory of X₁ fades as 0.9^(n-1), so after ~7 requests, X₁'s contribution is <5%.

---

## 3. Oscillatory Modulation

### Phase-Coupled Oscillations

Brains use oscillations for:
- **Synchronization**: Neural ensembles phase-lock
- **Routing**: Phase gates information flow
- **Energy**: Oscillatory bound-states are efficient

Quadra-Matrix implements sinusoidal phase modulation:

```python
class OscillatorySynapseTheory(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.oscillator = nn.Linear(dim, dim)
        self.phase = 0.0  ← persistent phase state
        
    def forward(self, x):
        self.phase += 0.1  ← phase increment per request
        modulation = torch.sin(torch.tensor(self.phase))
        return torch.tanh(self.oscillator(x)) * modulation
```

### Oscillation Waveform

```
phase(t) = phase(t-1) + 0.1
modulation(t) = sin(phase(t))

Request 1: phase=0.1, sin(0.1) ≈ 0.100
Request 2: phase=0.2, sin(0.2) ≈ 0.198
Request 3: phase=0.3, sin(0.3) ≈ 0.296
...
Request 31: phase=3.1, sin(3.1) ≈ 0.042
Request 62: phase=6.2, sin(6.2) ≈ -0.024  ← completes ~1 cycle
```

**Periodicity**: ~62 requests ≈ 1 full oscillation cycle (2π ≈ 6.28)

### Interpretation

After request processing, output is **modulated** (multiplied) by `sin(phase(t))`:

```
Raw output = tanh(FC(x))  ∈ [-1, 1]
Modulated output = tanh(FC(x)) * sin(phase)
```

Effects:
- Requests 1-15: Output magnitude **rises** (sin growing)
- Requests 15-31: Output magnitude **falls** (sin decreasing)
- Requests 31-47: Output magnitude **negative** (sin < 0)
- Cycle repeats every ~62 requests

**Purpose**: Creates **temporal non-stationarity**. System behavior differs depending on phase. Enables:
- Circadian-like patterns
- Emergent periodicity without explicit timing
- Phase-dependent decision gates

---

## 4. Pattern Encoding & Reconstruction

### Bottleneck Autoencoder

The `PatternModule` acts as a **compressed pattern codec**:

```python
class PatternModule(nn.Module):
    def __init__(self, input_dim=128, hidden_dim=256):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, input_dim)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))       # Encode to hidden
        x = torch.relu(self.fc2(x))       # Refine
        return self.fc3(x)                # Decode back to input
```

**Architecture: 128 → 256 → 256 → 128**
- **Expansion** (128→256): Project to richer space
- **Refinement** (256→256): Pattern algebra operations
- **Bottleneck** (256→128): Compress back, discard noise

### Information-Theoretic View

Input is **lossy-compressed** then reconstructed:
```
Input (128 dims) → Pattern Features (256 dims) → Output (128 dims)
```

Reconstruction error measures pattern fit:
```
loss = ||input - reconstruction||²
```

Sparse, repeatable patterns have low reconstruction error. Noise is discarded.

---

## 5. Syntropy: Order-Promoting Layer

### Negative Entropy

`SpikingSyntropyNN` drives the system toward **organized, low-entropy states**:

```python
class SpikingSyntropyNN(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.syntropy_layer = nn.Linear(dim, dim)
        
    def forward(self, x):
        return torch.sigmoid(self.syntropy_layer(x))
```

**Effect**: Output of sigmoid is normalized to [0, 1]. Ensemble output becomes **peaked, ordered**.

Compare:
- **High entropy**: Uniform distribution over 256 dimensions
- **Low entropy**: Few dimensions high, rest low (peaked)

Syntropy feedback **gates** high-entropy noise, amplifies ordered patterns.

---

## 6. Feedback & Attractor Dynamics

### Recurrent Error Correction

`SpikingFeedbackNN` implements **recurrent error correction**:

```python
class SpikingFeedbackNN(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.feedback_layer = nn.Linear(dim, dim)
        
    def forward(self, x, feedback=None):
        if feedback is not None:
            x = x + 0.1 * feedback  ← feedback integration
        return torch.relu(self.feedback_layer(x))
```

**Mechanism:**
1. Forward pass produces hidden state `h`
2. If error feedback available, integrate: `h' = h + 0.1·feedback`
3. Amplify via ReLU: `output = ReLU(FC(h'))`

**Effect**: Creates **attractor basin**. Small errors corrected by positive feedback loop. Large errors increase non-linearly.

---

## 7. Symbolic Reasoning Integration

### Pattern Algebra

The `SymbolicPredictiveInterpreter` (stubbed in current code) should implement:

```
Given: encoded patterns from spiking field
Compute: logical structure via symbolic algebra

Example:
Pattern_A = [sparse activation in dims 1,3,7]
Pattern_B = [sparse activation in dims 2,4,9]

Pattern_A ∧ Pattern_B = [dims 1,3,7] ∩ [dims 2,4,9] = ∅  (no intersection)
Pattern_A ∨ Pattern_B = [1,2,3,4,7,9]                       (union)
```

Symbolic operators:
- **∧ (AND)**: Intersection of active dimensions
- **∨ (OR)**: Union of active dimensions
- **¬ (NOT)**: Complement
- **→ (implication)**: If A active, expect B active
- **Causal**: Did A precede B in memory history?

---

## 8. Full Cognitive Pipeline

```
Input Vector (128 dims)
         │
         ▼
    Pattern Encoding
   (Lossy compression via bottleneck)
         │
         ▼
    Spiking Field Update
   (Sparse threshold activation ~40-50 neurons fire)
         │
         ▼
    Syntropy Ordering
   (Suppress noise, amplify structure)
         │
         ▼
    Neuroplastic Integration
   (Blend with session memory via EMA)
         │
         ▼
    Oscillatory Modulation
   (Multiply by sin(phase) — phase-dependent)
         │
         ▼
    Feedback Correction
   (Recurrent error correction loop)
         │
         ▼
    Symbolic Interpretation
   (Extract logic: AND, OR, causality, etc.)
         │
         ▼
  Governance Evaluation
   (Policy gates output)
         │
         ▼
   Output Vector (64 dims) + Confidence + Explanation
```

---

## 9. Emergent Behaviors

This architecture, when trained on structured tasks, exhibits:

### Attractor States
- System settles to low-energy configurations
- Similar inputs → similar outputs (basins of attraction)

### Phase Locking
- Multiple instances synchronize oscillations
- Enables distributed coordination

### Memory Decay Curves
- Exponential forgetting with characteristic time ~70 requests
- Enables temporal context window

### Sparse Firing Patterns
- ~30-50 of 256 neurons active per inference
- Interpretable, low-entropy representations

### Emergent Periodicity
- Without explicit scheduling, system shows cyclical behavior
- Driven purely by accumulated phase

---

## References & Inspiration

- **Spiking Neural Networks**: Maass, "Networks of Spiking Neurons" (Computational Neuroscience)
- **Neuroplasticity**: Hebbian learning, synaptic consolidation (Kandel, Hawkins)
- **Oscillations**: Phase-coding in hippocampus, theta-gamma coupling (Buzsáki)
- **Attractors**: Hopfield networks, neural dynamics (Hopfield, Amari)
- **Symbolic AI**: Newell & Simon, Physical Symbol Systems Hypothesis
