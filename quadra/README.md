# Quadra Module: Stateful Symbolic Predictive Intelligence

This directory contains the **core stateful architecture** for Quadra-Matrix AI—moving beyond generic ML scaffolding to concrete adaptive intelligence with governance as a first-class primitive.

## What's In Here

### `core/symbolic/interpreter.py`
**The 8-Stage Pipeline**

Complete inference system with:
1. **Encoded Input** - Neural representation of raw input
2. **Pattern Extraction** - Identify structures (clustering, FFT analysis)
3. **Field Spiking** - Generate spike trains
4. **Neuroplastic Update** - Adapt learning rate based on success
5. **Oscillatory Modulation** - Apply phase-based temporal modulation
6. **Symbolic Interpretation** - Derive logical/algebraic insights
7. **Governance Evaluation** - Apply policy constraints
8. **Output Synthesis** - Format final response

Each request flows through all 8 stages. **State persists** across requests via the memory store.

**Key insight**: This is not stateless batch processing. This is a **stateful agent** that maintains coherence across time.

### `core/governance/policy_adapter.py`
**Runtime Policy Enforcement**

Three components:
- **PolicyContext** - Input information for policy evaluation
- **PolicyEngine** - Evaluates rules, returns decisions
- **GovernanceService** - Applies policy decisions to outputs

Built-in rules:
- `HighRiskContentRule` - Suppress dangerous inputs
- `HighConfidenceRule` - Explain high-confidence outputs
- `NovelContextRule` - Disable advanced features for uncertain inputs

**Key insight**: Governance isn't documented. It's **actively enforced** in the inference pipeline.

### `state/memory_store.py`
**Persistent State Across Requests**

Stores:
- **Neural state**: Oscillatory phase, syntropy values, core field
- **Symbolic memory**: Concept history, reasoning traces
- **Learning metrics**: Success streak, learning rate trajectory
- **Context window**: Recent inputs/outputs for coherence

All automatically saved to disk. Loads on startup.

**Key insight**: Phase never resets. System maintains **true temporal continuity**.

## Quick Start

### Basic Usage

```python
from quadra import StatefulSymbolicPredictiveInterpreter
import asyncio

# Create interpreter (loads state from disk)
spi = StatefulSymbolicPredictiveInterpreter()

# Process a request
result = asyncio.run(spi.process({
    'text': 'What is quantum coherence?',
    'concepts': ['quantum', 'coherence', 'phase']
}))

# Inspect output
print(result['symbolic_result'])
print(result['oscillatory_phase'])  # Will be different next request
print(result['neuroplastic_metrics'])
```

### Multi-Request Sequence

```python
# Request 1
r1 = await spi.process({'text': 'First query'})
# phase=0.0 → 0.1, success_streak=1, lr=0.01

# Request 2 (state persists!)
r2 = await spi.process({'text': 'Second query'})
# phase=0.1 → 0.2, success_streak=2, lr=0.011

# Request 3 (phase continues evolving)
r3 = await spi.process({'text': 'Third query'})
# phase=0.2 → 0.3, success_streak=3, lr=0.0121
```

### Check Memory State

```python
snapshot = spi.get_memory_snapshot()
print(snapshot['oscillator_phase'])  # Current phase
print(snapshot['neuroplastic_metrics'])  # Learning progress
print(snapshot['recent_concepts'])  # What has been learned
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from quadra import StatefulSymbolicPredictiveInterpreter

app = Flask(__name__)
spi = StatefulSymbolicPredictiveInterpreter()  # Single instance

@app.route('/api/process', methods=['POST'])
async def process():
    # All requests share THE SAME spi instance
    # Memory persists automatically
    result = await spi.process(request.get_json())
    return jsonify(result)

@app.route('/api/memory', methods=['GET'])
def get_memory():
    # Inspect system state
    return jsonify(spi.get_memory_snapshot())
```

## Architecture Decisions

### Why Stateful?

**Problem**: Stateless systems cannot implement:
- Temporal continuity (oscillatory phase)
- Learning from history (success streaks)
- Coherent multi-turn conversation
- Adaptive behavior

**Solution**: `MemoryStore` maintains state across requests. Everything persists to disk.

### Why Governance as Primitive?

**Problem**: If governance is just documentation, it's not enforced.

**Solution**: `PolicyEngine` actually:
- Modifies outputs (`output *= suppression_factor`)
- Gates components (skips execution)
- Requires explanations
- Audits all decisions

### Why 8 Explicit Stages?

**Problem**: What exactly runs? What state changes?

**Solution**: Clear, sequential pipeline:
- Each stage has defined input/output
- Stateful stages update memory
- All are timed and logged
- Failures are caught and traced

## Testing

Comprehensive test suite in `tests/test_stateful_architecture.py`:

```bash
pytest tests/test_stateful_architecture.py -v -s
```

Verifies:
- ✅ Phase continuity across requests
- ✅ Success streak accumulation/reset
- ✅ Learning rate adaptation (exponential growth)
- ✅ Governance enforcement
- ✅ Memory persistence to disk
- ✅ All 8 pipeline stages
- ✅ Policy rule evaluation

## Configuration

Default configuration is reasonable but adjustable:

```python
from quadra import StatefulSymbolicPredictiveInterpreter

spi = StatefulSymbolicPredictiveInterpreter(
    model_version="spi-symbolic-0.2.0"
)

# Memory location
spi.memory = MemoryStore("./custom_memory_path")

# Add custom policy rules
from quadra.core.governance.policy_adapter import PolicyRule

class MyRule(PolicyRule):
    def evaluate(self, context):
        if condition:
            return PolicyDecision(action=PolicyAction.ESCALATE)
        return None

spi.policy_engine.add_rule(MyRule())
```

## Output Format

Every inference returns complete information:

```json
{
  "request_id": "123456",
  "model_version": "spi-symbolic-0.2.0",
  "symbolic_result": "Algebraic proof: ... | Logic: ... | Semantics: ... | Knowledge graph: ...",
  "neural_magnitude": 3.24,
  "spike_rate": 0.45,
  "oscillatory_phase": 0.523,
  "syntropy_state": [0.52, 0.48, 0.51],
  "neuroplastic_metrics": {
    "current_learning_rate": 0.0133,
    "success_streak": 3,
    "total_inferences": 47,
    "success_rate": 0.85
  },
  "stage_times": {
    "encode": 0.001,
    "pattern_extraction": 0.002,
    "spike_generation": 0.003,
    ...
  },
  "governance": {
    "policy_action": "allow",
    "explanation_required": false,
    "audit_id": "2024-01-02T14:30:45.123"
  },
  "memory_state": {
    "total_concepts": 47,
    "reasoning_traces": 23,
    "success_streak": 3
  }
}
```

## Philosophy

This architecture embodies three principles:

### 1. Stateful Intelligence
Systems that learn must remember. Phase doesn't reset. Concepts accumulate. Success builds on itself.

### 2. Governance as Enforcement
Policies aren't recommendations. They gate features, suppress outputs, require explanations. Enforced at runtime.

### 3. Concrete Over Abstract
No "enterprise features" without implementation. Every component is testable, observable, and measurable.

## Documentation

- **[STATEFUL_ARCHITECTURE.md](../STATEFUL_ARCHITECTURE.md)** - Deep dive into design philosophy
- **[IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)** - What was built and why
- **[tests/test_stateful_architecture.py](../tests/test_stateful_architecture.py)** - Executable specifications

## Contributing

New policy rules:
```python
class MyNewRule(PolicyRule):
    def evaluate(self, context: PolicyContext) -> Optional[PolicyDecision]:
        # Implement your logic
        pass
```

New neural components:
```python
# In quadra/core/neural/
class MyComponent(nn.Module):
    def forward(self, x):
        pass
```

Custom governance service:
```python
class MyGovernanceService(GovernanceService):
    def evaluate_and_condition_output(self, output, context):
        # Custom conditioning logic
        pass
```

---

**Status**: ✅ Production-ready foundation for stateful adaptive AI with runtime governance.

**Next**: Extend with domain-specific policies, monitoring, and multi-agent coordination.
