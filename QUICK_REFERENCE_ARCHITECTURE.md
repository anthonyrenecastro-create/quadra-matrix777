# Quick Reference: Core Architecture

## The Three Papers at a Glance

| Paper | Focus | Length | Key Insight |
|-------|-------|--------|-------------|
| **ARCHITECTURE.md** | System design | 320 lines | SPI is stateful agent, not commodity ML |
| **COGNITIVE_MODEL.md** | Neuroscience math | 377 lines | Spiking + memory + oscillation = emergent cognition |
| **GOVERNANCE-INFERENCE.md** | Policy enforcement | 625 lines | Governance gates at inference time, shapes behavior |

---

## 8-Stage Pipeline (Memorize This)

```
1. Input → 2. Pattern Encoding → 3. Spiking Field
4. Syntropy → 5. Neuroplasticity → 6. Oscillation
7. Feedback → 8. Symbolic Reason → Governance Gate → Output
```

**Each stage has purpose:**
- **1-3**: Feature extraction (sparse)
- **4-6**: Adaptation (memory + phase)
- **7-8**: Reasoning + governance

---

## 4 Governance Gates (Memorize This)

```
1. SUPPRESSION: output *= 0.3
2. EXPLANATION: attach symbolic trace
3. ESCALATION: defer to human review
4. THRESHOLD: raise confidence bar
```

Applied **in sequence** after model output, before returning.

---

## Key Equations

### Exponential Moving Average (Memory)
```
M(t) = 0.9 * M(t-1) + 0.1 * X(t)
```
- α=0.9 (decay), (1-α)=0.1 (learning)
- Forgets old after ~7 requests
- Never resets, always blends

### Spiking Field
```
potential = sigmoid(W·x + b)
spike = (potential > 0.5)
output = spike * potential
```
- Binary gate (spike: 0 or 1)
- Sparse activation
- Temporal events

### Oscillation
```
phase(t) = phase(t-1) + 0.1
modulation = sin(phase(t))
```
- Period ~62 requests
- Output *= sin(phase)
- Creates temporal non-stationarity

---

## Core Concepts

### Stateful vs Stateless
- **Stateless** (commodity ML): Same input → same output always
- **Stateful** (SPI): Same input → different output depending on session history

### Memory as Context
- Policy evaluator sees memory state
- Same user treated differently based on history
- "Learning" happens implicitly via EMA

### Governance as First-Class
- Not: Inference → Output → [Filter output]
- Yes: Inference → [Policy evaluator] → Gated output
- Model learns policies exist, shapes itself

### Sparse & Interpretable
- Spiking: ~40-50 of 256 neurons active
- Can see which neurons fired
- Not black box like dense ReLU

---

## Deployment Pieces

| Component | Purpose | Technology |
|-----------|---------|-----------|
| API Gateway | Auth, rate limit, TLS | Flask/Gunicorn |
| SPI Service | Inference | PyTorch |
| Memory Store | Persistent state | Redis/Postgres |
| Policy Engine | Rule evaluation | Custom |
| Audit Log | Decision history | Postgres |

All services stateless. State in persistent store.

---

## Common Gotchas

### ❌ "But this is just a neural network"
✅ Not true. It has memory, governance, and temporal dynamics. It's an **agent**.

### ❌ "Why not just filter output after?"
✅ Model doesn't learn policy exists. Learns to output whatever, then gets filtered. Incompatible.

### ❌ "Can we make memory bigger?"
✅ No. If α=0.99 instead of 0.9, memory never updates (gets stuck). If α=0.1, only recent requests matter. 0.9 is sweet spot.

### ❌ "Can we turn off oscillation?"
✅ You can set phase increment to 0. Then output is deterministic. But you lose phase-coupling between instances.

### ❌ "Does governance reduce accuracy?"
✅ It reduces confidence, not accuracy. But it increases **reliability** (user trust + audit trail).

---

## File Locations

```
Quadra-Matrix-A.I.-main/
├─ ARCHITECTURE.md                 ← Start here
├─ COGNITIVE_MODEL.md              ← Then here
├─ GOVERNANCE-INFERENCE.md         ← Then here
├─ ARCHITECTURE_INDEX.md           ← Navigation guide
├─ ARCHITECTURE_SUMMARY.md         ← Full diagram tour
├─ QUICK_REFERENCE.md              ← You are here
│
├─ quadra/                         ← Implementation (TBD)
│  ├─ core/
│  │  ├─ symbolic/
│  │  ├─ neural/
│  │  └─ governance/
│  ├─ api/
│  ├─ state/
│  └─ tests/
│
└─ [other project files]
```

---

## Implementation Checklist

**Phase 1: Core Pipeline**
- [ ] Implement PatternModule
- [ ] Implement SpikingFieldUpdateNN, SpikingSyntropyNN, SpikingFeedbackNN
- [ ] Implement NeuroplasticityManager with EMA
- [ ] Implement OscillatorySynapseTheory with phase
- [ ] Wire 8 stages together in SymbolicPredictiveInterpreter

**Phase 2: State Management**
- [ ] Build MemoryStore (Redis backend)
- [ ] Add session_id to requests
- [ ] Load/save memory on each request

**Phase 3: Governance**
- [ ] Define GovernancePolicy dataclass
- [ ] Implement PolicyAdapter.evaluate()
- [ ] Implement 4 gates (suppression, explanation, escalation, threshold)
- [ ] Add audit logging

**Phase 4: Production**
- [ ] Multi-instance deployment
- [ ] Failure recovery (policy engine down, memory down)
- [ ] Fairness audits
- [ ] Human review queue integration
- [ ] Appeal mechanism for users

---

## Testing Strategy

### Unit Tests
```python
# Test EMA memory
M0 = [0, 0, ...]
X1 = [1, 0, ...]
M1 = 0.9*M0 + 0.1*X1 = [0.1, 0, ...]
assert M1[0] ≈ 0.1

# Test spiking
potential = 0.7 (> 0.5 threshold)
spike = 1
output = 1 * 0.7 = 0.7
assert output == 0.7
```

### Integration Tests
```python
# Test full pipeline
for i in range(10):
    output = spi.process(input_i)
    assert output.shape == (64,)
    assert 0 <= output.confidence <= 1

# Test memory persistence
store.save(session_id, memory)
loaded = store.load(session_id)
assert loaded ≈ memory
```

### Governance Tests
```python
# Test suppression gate
policy.requires_suppression = True
gated = output * 0.3
assert gated < output

# Test escalation gate
policy.requires_escalation = True
result = apply_gates(output, policy)
assert result is None  # Blocked
assert escalation_queue.size() == 1
```

---

## Key Papers/References (from COGNITIVE_MODEL.md)

- **Spiking neurons**: Maass, "Networks of Spiking Neurons"
- **Neuroplasticity**: Kandel et al., "Neuroscience" (synaptic consolidation)
- **Oscillations**: Buzsáki, "Rhythms of the Brain" (phase-coding)
- **Attractors**: Hopfield, "Neural networks and physical systems"
- **Symbolic AI**: Newell & Simon, "Physical Symbol Systems Hypothesis"

---

## Quick Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Memory never updates | α too high (0.99) | Use α=0.9 |
| Memory forgets too fast | α too low (0.5) | Use α=0.9 |
| Outputs non-deterministic | Oscillation phase random | Initialize phase=0 consistently |
| Governance always suppresses | Policy threshold wrong | Tune suppression_factor |
| Audit log explosion | Log everything at INFO | Use audit_sample_rate=0.1 |

---

## One-Minute Elevator Pitch

**Quadra-Matrix is a Stateful Symbolic Predictive Interpreter.**

It combines:
1. **Spiking neural field** (sparse, interpretable)
2. **Exponential memory** (learns from session history)
3. **Phase-modulated oscillations** (emergent temporal dynamics)
4. **Symbolic reasoning** (extracts patterns logically)
5. **Governance gates** (policy-aware, auditable)

**Unlike commodity ML**: It's an **agent** that adapts and remembers, not a stateless predictor. Governance is embedded in inference, not added after. Memory is capital that increases value over time.

---

**Start reading**: [ARCHITECTURE.md](ARCHITECTURE.md)
