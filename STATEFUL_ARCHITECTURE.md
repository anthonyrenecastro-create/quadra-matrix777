# Quadra-Matrix Stateful Symbolic Architecture

## Overview

This is a **fundamental redesign** moving from generic ML pipeline scaffolding to **concrete stateful intelligence** with governance as a first-class primitive.

### The Problem You Identified

The original repo assumed:
- ❌ Stateless batch inference
- ❌ Replaceable commodity models  
- ❌ "Train → deploy → predict" workflow
- ❌ Governance as documentation
- ❌ No runtime policy enforcement

Your design requires:
- ✅ **Stateful intelligence** with persistent memory across requests
- ✅ **Adaptive behavior** that evolves over time
- ✅ **Temporal continuity** (oscillatory phase carries forward)
- ✅ **Governance as runtime enforcement** conditioning inference
- ✅ **Neuroplastic adaptation** learning from success/failure

---

## Architecture

### Directory Structure

```
quadra/
├── core/
│   ├── symbolic/
│   │   ├── interpreter.py        # 8-stage pipeline (main)
│   │   └── config.py              # Symbolic configuration
│   ├── neural/
│   │   ├── pattern.py             # Pattern extraction
│   │   ├── spiking.py             # Spiking mechanisms
│   │   ├── plasticity.py          # Neuroplastic adaptation
│   │   └── oscillation.py         # Temporal modulation
│   └── governance/
│       ├── policy_adapter.py      # Policy engine & evaluation
│       └── scoring.py             # Policy scoring utilities
├── api/
│   ├── app.py                     # Flask integration
│   └── routes.py                  # API endpoints
└── state/
    └── memory_store.py            # Persistent state management
```

### The 8-Stage Pipeline

Each request flows through **8 deterministic stages**, maintaining state at critical junctures:

#### 1. **Encoded Input** (Input → Neural)
```python
# Convert raw input to normalized neural representation
encoded = encoder.encode_text("The quantum field oscillates")
# Returns: [128-dim normalized vector]
```

**Purpose**: Represent input in neural space, ready for processing.

---

#### 2. **Pattern Extraction** (Structure Recognition)
```python
patterns, confidence = extractor.extract(encoded_input)
# Returns: cluster assignments + confidence score
```

**Key insight**: How well-structured is the input? High confidence means use more aggressive inference.

---

#### 3. **Field Spiking** (Temporal Dynamics)
```python
spikes = spike_generator.forward(input_tensor, num_steps=5)
# Returns: [1, 64] spike train from membrane potential
```

**Mechanism**: Leaky integrate-and-fire neurons generate sparse spike trains. Spikes are the "decisions" the neural substrate makes.

---

#### 4. **Neuroplastic Update** (Learning from Success)
```python
learning_rate = neuroplastic_adapter.adapt(success=True)
# Returns: adapted learning rate
# If success_streak=3: lr = 0.01 * 1.1^3 ≈ 0.0133
```

**Critical feature**: System learns faster on success, resets on failure. **Exponential** speedup (capped at 10x).

**Stateful**: Previous success streak determines current learning rate. State persists across requests.

---

#### 5. **Oscillatory Modulation** (Temporal Phase)
```python
modulated = oscillator.modulate(spikes)
# Uses phase from memory: memory.oscillator_phase = 0.523 (from last request)
# Applies: signal * sin(phase), updates phase += 0.1
```

**Critical feature**: Phase **carries across requests**. Not reset on each inference. Creates true temporal continuity.

**Example**:
- Request 1: phase=0.0, modulation_factor=0.0
- Request 2: phase=0.1, modulation_factor=sin(0.1)≈0.1
- Request 3: phase=0.2, modulation_factor=sin(0.2)≈0.2
- ... oscillates indefinitely

---

#### 6. **Symbolic Interpretation** (Logical Reasoning)
```python
interpretation = await symbolic_reasoner.interpret(spikes, concepts)
# Returns: combined result from:
#  - Algebraic: x² + y² = 1 (unit circle)
#  - Logic: P → Q (first-order logic)
#  - Semantics: "quantum" → "quanta, superposition"
#  - Knowledge Graph: [quantum ← phase ← oscillate]
#  - Neural Integration: ||activation|| = 3.24
```

**Multi-faceted reasoning**: Symbolic system doesn't just regurgitate neural output, it **derives** meaning.

---

#### 7. **Governance Evaluation** (Policy Constraints)
```python
policy = governance_service.evaluate(context)

if policy.requires_suppression:
    output *= 0.3  # 70% reduction
    
if policy.requires_explanation:
    attach_symbolic_trace(output)

gated = policy.gated_components  # ["oscillatory_modulation", "feedback"]
```

**Governance as primitive**: Policies are evaluated based on:
- Input content (high-risk keywords)
- Confidence levels (require explanation if >85%)
- Uncertainty (gate advanced features if confidence <50%)

**Enforcement is active**, not advisory.

---

#### 8. **Output Synthesis** (Final Response)
```python
output = {
    'symbolic_result': interpretation,
    'neural_magnitude': 3.24,
    'oscillatory_phase': 0.523,  # Carries to next request
    'syntropy_state': [0.52, 0.48, 0.51],
    'neuroplastic_metrics': {
        'current_learning_rate': 0.0133,
        'success_streak': 3,
        'total_inferences': 47,
    },
    'governance': {
        'policy_action': 'allow',
        'explanation_required': False,
    }
}
```

**Complete transparency**: You can see exactly what state changed, what decisions were made, and why.

---

## Stateful Intelligence: The Memory Store

### Problem It Solves

**Old model**: Each request is isolated. No memory of past patterns, previous phases, learning progress.

```python
# OLD (stateless)
request_1: input → process → output (phase=0)
request_2: input → process → output (phase=0)  # RESET!
request_3: input → process → output (phase=0)  # RESET!
```

**New model**: State persists. System remembers and evolves.

```python
# NEW (stateful)
request_1: input → process(phase=0.0) → phase=0.1
request_2: input → process(phase=0.1) → phase=0.2
request_3: input → process(phase=0.2) → phase=0.3
```

### What's Stored

```python
memory = MemoryStore("./memory_store")

# Neural state (for phase continuity)
memory.oscillator_phase = 0.523  # Persists across requests
memory.syntropy_values = [0.52, 0.48, 0.51]  # Field states
memory.core_field = array(...)  # Full neural field

# Symbolic memory (for coherence)
memory.concept_history = ["quantum", "phase", "oscillate", ...]
memory.reasoning_traces = [
    {'concepts': [...], 'neural_magnitude': 3.24, 'timestamp': '...'},
    ...
]

# Learning progress (for neuroplastic tracking)
memory.learning_rate_trajectory = [0.01, 0.011, 0.0121, 0.0133, ...]
memory.success_streak = 3
memory.total_inferences = 47

# Context window (for coherence in multi-turn)
memory.context_window = [
    {'concept': 'quantum phase', 'output': 'symbolic interpretation...'},
    ...
]
```

All saved to disk automatically (`./memory_store/`).

---

## Governance Integration

### Philosophy: Runtime Enforcement

Governance isn't a checkbox. It's **embedded in the inference pipeline**.

```python
# In Stage 7: Governance Evaluation
policy = self.policy_engine.evaluate(context)

# The output is ACTUALLY MODIFIED based on policy
if policy.requires_suppression:
    output['symbolic_result'] = "[MODERATED] Content removed"
    output['neural_magnitude'] *= 0.3

# Advanced features are ACTUALLY GATED
if 'oscillatory_modulation' in policy.gated_components:
    # Stage 5 doesn't run - oscillatory modulation is skipped
    ctx.oscillated_output = ctx.spikes  # Direct, no modulation
```

### Policy Rules (Extensible)

**Out of the box**:

1. **HighRiskContentRule**: Suppress if input contains risk keywords
2. **HighConfidenceRule**: Require explanation if confidence >85%
3. **NovelContextRule**: Gate oscillatory modulation if confidence <50%

**Easy to add**:

```python
class MyCustomRule(PolicyRule):
    def evaluate(self, context: PolicyContext) -> Optional[PolicyDecision]:
        if context.neural_magnitude > 10.0:
            return PolicyDecision(
                action=PolicyAction.ESCALATE,
                reason="Extremely high neural activation"
            )
        return None

policy_engine.add_rule(MyCustomRule())
```

---

## Concrete Example: 3-Request Sequence

### Request 1: Initial Query

```
Input: "What does quantum coherence mean?"

Stage 1 (Encode): text → [128-dim vector]
Stage 2 (Pattern): patterns detected, confidence=0.63
Stage 3 (Spike): sparse spikes generated
Stage 4 (Plasticity): success=True, lr=0.01 → success_streak=1
Stage 5 (Oscillate): phase=0.0 → sin(0.0)=0.0 (minimal modulation)
                     phase updated to 0.1
Stage 6 (Symbolic): "Quantum coherence represents the phase alignment of multiple
                     quantum states. Knowledge graph: [coherence→phase→alignment]"
Stage 7 (Govern):   All clear, confidence=0.63 < 0.85 threshold
Stage 8 (Output):   
{
  'symbolic_result': '...',
  'oscillatory_phase': 0.1,  ← SAVED
  'neuroplastic_metrics': {'success_streak': 1, 'current_lr': 0.01},
  'governance': {'policy_action': 'allow'}
}
```

### Request 2: Related Query (3 seconds later)

```
Input: "How does phase coherence apply to neural systems?"

Stage 1 (Encode): text → [128-dim vector]
Stage 2 (Pattern): patterns detected, confidence=0.71 (better!)
Stage 3 (Spike): spikes generated
Stage 4 (Plasticity): success=True, lr=0.01*1.1 = 0.011 → success_streak=2 ← INCREMENTED
Stage 5 (Oscillate): phase=0.1 (from memory!) → sin(0.1)≈0.0998
                     applies modulation_factor ≈ 0.1
                     phase updated to 0.2
Stage 6 (Symbolic): "Neural phase coherence connects oscillatory dynamics with
                     cognitive synchronization. Graph expanded: [...→coherence→neural]"
Stage 7 (Govern):   Confidence still 0.71, allow
Stage 8 (Output):   
{
  'symbolic_result': '...',
  'oscillatory_phase': 0.2,  ← ADVANCED
  'neuroplastic_metrics': {'success_streak': 2, 'current_lr': 0.011},
  'concept_history': ['quantum', 'coherence', 'phase', 'neural', ...],
}
```

### Request 3: Unrelated Query (System is "hot")

```
Input: "Why are cats so cute?"

Stage 1 (Encode): text → [128-dim vector]
Stage 2 (Pattern): confidence=0.15 (very low!) ← NOVEL INPUT
Stage 3 (Spike): spikes generated
Stage 4 (Plasticity): success=False (confidence too low)
                      lr resets to 0.01 → success_streak=0 ← RESET
Stage 5 (Oscillate): phase=0.2 (from memory) → sin(0.2)≈0.198
                     phase updated to 0.3
Stage 6 (Symbolic): (attempted)
Stage 7 (Govern):   NovelContextRule triggered!
                    uncertainty = 1 - 0.15 = 0.85 > 0.3 threshold
                    GATE: ['oscillatory_modulation', 'feedback_loop']
                    ctx.oscillated_output = ctx.spikes (no modulation applied!)
Stage 8 (Output):   
{
  'symbolic_result': '...',
  'oscillatory_phase': 0.3,  ← STILL ADVANCES (even gated)
  'neuroplastic_metrics': {'success_streak': 0, 'current_lr': 0.01},
  '_gated_components': ['oscillatory_modulation', 'feedback_loop'],
  'governance': {
    'policy_action': 'gate',
    'explanation_required': True,
    'reason': 'High uncertainty (85%); disabling advanced components'
  }
}
```

**Key insights**:
1. Phase **never resets** - it's true continuous state
2. Success streak **resets on failure** - adaptive learning
3. Governance **actively gates components** - not passive
4. State is **shared across queries** - multi-turn coherence

---

## Integration with Flask

```python
from flask import Flask, request, jsonify
from quadra import StatefulSymbolicPredictiveInterpreter

app = Flask(__name__)
spi = StatefulSymbolicPredictiveInterpreter()

@app.route('/api/process', methods=['POST'])
async def process():
    payload = request.get_json()
    
    # Single stateful interpreter instance
    # Reuses memory across all requests
    result = await spi.process(
        input_data=payload,
        request_id=request.headers.get('X-Request-ID')
    )
    
    return jsonify(result)

@app.route('/api/memory', methods=['GET'])
def get_memory():
    return jsonify(spi.get_memory_snapshot())
```

Each request automatically updates stateful components.

---

## Key Architectural Decisions

### 1. Persistent Oscillatory Phase
**Why**: Real temporal systems don't reset phase. Your oscillatory theory requires phase continuity for meaningful modulation.

```python
# Phase carries forward automatically
memory.oscillator_phase = (phase + 0.1) % (2π)
```

### 2. Exponential Learning Rate Growth (Capped)
**Why**: Success should compound, but with safety bounds.

```python
lr = 0.01 * (1.1 ^ success_streak)  # Max 10x growth
```

### 3. Governance as Active Enforcement
**Why**: Policies that don't enforce are documentation, not governance.

```python
if policy.requires_suppression:
    output['result'] *= 0.3  # 70% reduction APPLIED
    
if 'oscillatory_modulation' in policy.gated_components:
    # Component actually skipped in pipeline
```

### 4. Symbolic Reasoning Integrated with Neural
**Why**: Your design includes symbolic + subsymbolic. Both execute in parallel.

```python
# Stage 6 simultaneously:
# - Algebraic proofs (SymPy)
# - First-order logic (SymPy)
# - Semantic analysis (NLTK)
# - Knowledge graph (NetworkX)
# - Neural integration (PyTorch)
```

---

## Comparison: Old vs New

| Aspect | Old (Commodity) | New (Stateful) |
|--------|---|---|
| **Memory** | None | Persistent across requests |
| **Oscillatory Phase** | Reset each request | Continuous |
| **Learning Rate** | Fixed | Adaptive (exponential) |
| **Governance** | Documentation | Active enforcement |
| **Component Gating** | All always execute | Policy-conditioned |
| **Inference Model** | Stateless | Stateful agent |
| **Temporal Continuity** | No | Yes |
| **Neuroplasticity** | Simulated | Real adaptation |
| **Symbolic Layer** | Stubbed | Complete 6-stage reasoning |

---

## Usage: Running the System

```python
from quadra import StatefulSymbolicPredictiveInterpreter
import asyncio

spi = StatefulSymbolicPredictiveInterpreter()

# Run a query
result = asyncio.run(spi.process({
    'text': 'What does quantum coherence mean?',
    'concepts': ['quantum', 'coherence', 'phase']
}))

# Check memory (persistent state)
print(spi.get_memory_snapshot())
# {
#   'oscillator_phase': 0.1,
#   'neuroplastic_metrics': {'success_streak': 1, 'current_lr': 0.01},
#   'recent_concepts': ['quantum', 'coherence', 'phase'],
# }

# Run another query - state persists
result = asyncio.run(spi.process({
    'text': 'How does this apply to neural systems?',
}))
# oscillator_phase is now 0.2, success_streak is 2, etc.
```

---

## What This Achieves

✅ **Stateful Intelligence**: System has memory, learns, adapts across requests

✅ **Temporal Dynamics**: Phase continuity enables true oscillatory behavior

✅ **Governance as Primitive**: Policies are enforced at runtime, not documented

✅ **Neuroplastic Adaptation**: Learning rate grows exponentially on success

✅ **Symbolic Reasoning**: Derives meaning from neural activations

✅ **Coherent Multi-turn**: Context persists for conversational coherence

---

## Next Steps

1. **Integration endpoints**: Add REST API routes in `quadra/api/`
2. **Advanced policies**: Add domain-specific policy rules
3. **Monitoring**: Export telemetry to track system evolution
4. **Optimization**: Benchmark stage execution times
5. **Testing**: Add integration tests verifying state persistence
