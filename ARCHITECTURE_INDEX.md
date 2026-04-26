# Core Architecture Papers Index

This directory now contains **substantive architecture documentation** replacing buzzword summaries.

## The Three Core Papers

### 1. 📐 [ARCHITECTURE.md](ARCHITECTURE.md)
**System Design & Component Overview**

- Quadra-Matrix as a **Stateful Symbolic Predictive Interpreter (SPI)**
- Core components (Symbolic, Neural Dynamics, Governance, State Management)
- **8-stage data flow pipeline** (visual diagram)
- State persistence model for neuroplastic memory
- Session-scoped adaptation mechanism
- **Commodity ML vs. SPI comparison**
- Deployment topology (replicated inference + memory store)
- Critical design decisions (multiplicative gating, EMA, spiking > ReLU)

**Read this first** to understand what the system is and how it works.

---

### 2. 🧠 [COGNITIVE_MODEL.md](COGNITIVE_MODEL.md)
**Neuroscientific Foundations & Dynamics**

- **Spiking neural field equations** with threshold nonlinearity
- Why spikes matter (sparse, temporal, interpretable)
- **Neuroplasticity via Exponential Moving Average (EMA)**
  - Memory consolidation mathematics
  - Trace decay analysis
- **Oscillatory phase modulation** (sinusoidal gating)
  - Periodicity (~62 requests per cycle)
  - Emergent circadian-like patterns
- **Pattern encoding** via bottleneck autoencoder
- **Syntropy layer** (negative entropy, order-promoting)
- **Feedback & attractor dynamics** (error correction)
- **Symbolic reasoning integration** (pattern algebra)
- Full cognitive pipeline (7 stages → output)
- **Emergent behaviors** (attractors, phase-locking, sparse firing)

**Read this** to understand the cognitive science and math behind each component.

---

### 3. ⚖️ [GOVERNANCE-INFERENCE.md](GOVERNANCE-INFERENCE.md)
**Policy-Aware Inference & Runtime Enforcement**

- **Problem statement**: Commodity ML separates inference from governance (breaks compatibility)
- **Solution**: Embed governance as first-class primitive in inference graph
- **InferenceContext** (full state passed to evaluator)
- **GovernancePolicy** (structured decision from evaluator)
- **4 Independent Governance Gates**:
  1. **Suppression Gate** - reduce confidence multiplicatively
  2. **Explanation Gate** - attach symbolic trace
  3. **Escalation Gate** - route to human review
  4. **Threshold Gate** - raise confidence bar
- **Memory-Governance Integration** - memory is part of policy context
- **Complete signal flow diagram** (13-step inference path)
- **Memory feedback loop** (how memory updates shape policy over time)
- **Audit trail schema** (complete decision logging)
- **Policy rule examples** (risk profiling, uncertainty, escalation, rate limits)
- **Deployment topology** (services → memory store → policy engine → audit log)
- **Failure modes & recovery** (policy down, memory down, audit queue full)
- **Integration checklist** (13 items for production deployment)

**Read this** to understand how governance works at runtime and why policy should shape learning.

---

## Visual Maps

### Signal Flow (from ARCHITECTURE.md)
```
Input (128) 
  ↓
[Pattern Encoding] - PatternModule bottleneck
  ↓
[Field Spiking] - SpikingFieldUpdateNN threshold
  ↓
[Syntropy] - Order-promoting layer
  ↓
[Neuroplasticity] - EMA memory update
  ↓
[Oscillation] - Phase-modulated gating
  ↓
[Feedback Loop] - Recurrent error correction
  ↓
[Symbolic Reason] - Pattern algebra
  ↓
[Governance Gate] - Policy-conditioned
  ↓
Output (64) + Confidence + Explanation + Flags
```

### Memory-Governed Inference (from GOVERNANCE-INFERENCE.md)
```
Request N:
  • Load Memory[N-1] from MemoryStore
  • Pass into SPI pipeline (memory-aware)
  • Evaluate policy WITH memory context
  • Gate output based on policy
  • Update Memory: M[N] = 0.9*M[N-1] + 0.1*new
  • Audit decision
  • Return governed output

→ System "remembers" prior requests
→ Policy treats similar users differently over time
→ Governance & memory are coupled
```

### Governance Gate Pipeline (from GOVERNANCE-INFERENCE.md)
```
Model Output (raw)
  ↓
Governance Evaluator
  ├─ User risk profile?
  ├─ Output uncertainty?
  ├─ Output pattern match?
  ├─ Request frequency?
  └─ Policy version compatible?
  ↓
GovernancePolicy (4 flags + metadata)
  ↓
Apply 4 Gates in sequence:
  ├─ Suppression: output *= 0.3?
  ├─ Explanation: attach trace?
  ├─ Escalation: defer to human?
  └─ Threshold: raise confidence bar?
  ↓
Governed Output (same shape, maybe modified)
+ Confidence (maybe reduced)
+ Explanation (maybe attached)
+ Governance Flags (audit metadata)
+ Audit Log Entry
```

---

## Key Concepts

### Stateful vs. Stateless

| Aspect | Commodity ML | SPI |
|--------|-------------|-----|
| Memory | None | Persistent (per-session) |
| Requests | IID | Temporally dependent |
| Adaptation | Retraining required | Online learning via EMA |
| Governance | Post-hoc filter | First-class (shapes inference) |

### The 8 Inference Stages

1. **Pattern Encoding** - Lossy compression via bottleneck
2. **Field Spiking** - Sparse threshold activation
3. **Syntropy** - Order-promoting, low-entropy
4. **Neuroplasticity** - Blend with session memory
5. **Oscillation** - Phase-dependent modulation
6. **Feedback** - Recurrent error correction
7. **Symbolic Reasoning** - Extract logical structure
8. **Governance Gate** - Policy-conditioned output

### The 4 Governance Gates

1. **Suppression** - Reduce confidence
2. **Explanation** - Provide trace
3. **Escalation** - Route to human
4. **Threshold** - Raise confidence bar

---

## Design Philosophy

**Core insight**: Model is an **agent**, not an **artifact**.

- **Agents adapt** (SPI has memory, responds to environment)
- **Artifacts are replaceable** (commodity ML models)
- **Governance shapes behavior** (not just filters output)
- **Memory is capital** (state accumulates value over time)

This breaks commodity ML assumptions. It's intentional.

---

## Production Checklist

- [ ] Understand the 8-stage pipeline (from ARCHITECTURE.md)
- [ ] Understand spiking dynamics & EMA math (from COGNITIVE_MODEL.md)
- [ ] Implement the 4 governance gates (from GOVERNANCE-INFERENCE.md)
- [ ] Set up memory store (Redis/Postgres)
- [ ] Implement audit logging (complete schema)
- [ ] Define policy rules (user profiles, patterns, thresholds)
- [ ] Set up human review queue
- [ ] Test failure recovery (policy down, memory down)
- [ ] Build fairness audit reports
- [ ] Document appeal mechanism for users

---

## Navigation

- **Quick start** → Read ARCHITECTURE.md (overview)
- **Deep dive (neuroscience)** → Read COGNITIVE_MODEL.md
- **Deep dive (governance)** → Read GOVERNANCE-INFERENCE.md
- **Implementation** → See production checklist above
- **Questions about buzzword docs?** → See [DOCS_CONVERSION_SUMMARY.md](DOCS_CONVERSION_SUMMARY.md)
