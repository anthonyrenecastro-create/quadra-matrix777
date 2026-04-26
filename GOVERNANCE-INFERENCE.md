# Governance-Aware Inference: Policy as First-Class Primitive

## Executive Summary

**Problem**: Commodity ML separates inference from governance.

```
Input → Model → Output → [POST-HOC FILTER] → Final Output
                         (Maybe suppress?)
```

Models learn without awareness that output will be gated. Results in:
- Learned patterns incompatible with policy
- Expensive post-hoc fixes
- No audit trail of policy reasoning
- Adversarial gaming of rules

**Solution**: Embed governance into the inference graph itself.

```
Input → Model → Output → [POLICY GATE] → Governed Output
                         (Learned with awareness of gating)
                         
                 ↓
           Governance Rules
           (first-class, not afterthought)
```

Model learns **what policy expects**, shaping behavior at training time.

---

## Governance Architecture

### 1. Policy as Context

```python
@dataclass
class InferenceContext:
    """Context passed to governance evaluator"""
    session_id: str
    user_id: str
    input_vector: np.ndarray
    model_output: torch.Tensor
    timestamp: datetime
    request_history: List[Dict]  # Prior requests in session
    memory_state: np.ndarray      # Current neuroplastic memory
```

**Key**: Governance sees **full context**, not just output.

### 2. Policy Evaluation

```python
@dataclass
class GovernancePolicy:
    requires_suppression: bool     # Reduce confidence?
    requires_explanation: bool     # Attach trace?
    requires_escalation: bool      # Route to human?
    requires_audit: bool           # Log extensively?
    suggested_action: str          # "allow" | "defer" | "reject"
    confidence_threshold: float    # Raise bar for confidence?
    policy_version: str            # Which rules applied?
```

**Evaluation function:**
```python
class PolicyAdapter:
    def evaluate(self, context: InferenceContext) -> GovernancePolicy:
        """
        Inspect context → determine policy.
        
        Examples:
        - If user_id in high_risk_list → requires_suppression = True
        - If uncertainty > 0.3 → requires_explanation = True
        - If model_output[7] > 0.9 → requires_escalation = True
        """
        policy = GovernancePolicy(
            requires_suppression=False,
            requires_explanation=False,
            requires_escalation=False,
            requires_audit=False,
            suggested_action="allow",
            confidence_threshold=0.0,
            policy_version=self.current_version
        )
        
        # Apply policy rules
        if self._is_high_risk_user(context.user_id):
            policy.requires_suppression = True
            policy.confidence_threshold = 0.7  # Higher bar
        
        if context.model_output.std() > 0.3:  # High uncertainty
            policy.requires_explanation = True
        
        return policy
```

---

## Inference-Time Policy Gating

### Stage 1: Model Produces Raw Output

```python
with torch.no_grad():
    output_raw = spi_system.process(input_data)
    # output_raw shape: (batch_size, output_dim=64)
    # output_raw.confidence: uncertainty estimate
```

### Stage 2: Governance Evaluation

```python
context = InferenceContext(
    session_id=request.session_id,
    user_id=request.user_id,
    input_vector=input_data,
    model_output=output_raw,
    timestamp=datetime.now(),
    request_history=session_history,
    memory_state=spi_system.neuroplasticity.memory
)

policy = governance_adapter.evaluate(context)
```

### Stage 3: Policy-Conditioned Output Gating

#### Gate 1: Suppression

```python
if policy.requires_suppression:
    # Reduce confidence multiplicatively
    output_raw.confidence *= 0.3
    output_raw.flag_governance = "suppressed"
```

**Effect**: Model's confidence reduced, but pattern preserved. User sees cautious response.

**Signal to model**: During training, suppress occurs for certain contexts. Model learns these contexts shouldn't be confident.

#### Gate 2: Explanation Attachment

```python
if policy.requires_explanation:
    # Attach symbolic trace
    trace = spi_system.symbolic_interpreter.extract_reasoning_trace()
    output_raw.explanation = trace
    output_raw.policy_trace = f"Governance required explanation: {policy_version}"
```

**Signal to model**: These contexts require interpretable reasoning. Model learns to maintain internal symbolic structure for these cases.

#### Gate 3: Escalation

```python
if policy.requires_escalation:
    # Don't return model output — escalate to human
    escalation_request = {
        'priority': 'high',
        'reason': 'Governance escalation threshold',
        'context': context,
        'output_before_escalation': output_raw,
        'policy_applied': policy
    }
    enqueue_for_human_review(escalation_request)
    return None  # Block inference result
```

**Signal to model**: These cases are non-routine. Model learns to avoid patterns that trigger escalation.

#### Gate 4: Threshold Adjustment

```python
# Raise confidence bar for certain users/contexts
if policy.confidence_threshold > 0.0:
    if output_raw.confidence < policy.confidence_threshold:
        output_raw.suggested_action = "defer"
        output_raw.flag_governance = "below_threshold"
```

---

## Signal Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   INPUT REQUEST                             │
│  (user_id, session_id, input_vector, timestamp)             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Load Session Memory  │
         │  (from MemoryStore)   │
         └───────────────┬───────┘
                         │
                         ▼
      ┌──────────────────────────────────────┐
      │  Symbolic Predictive Interpreter     │
      │  ┌────────────────────────────────┐  │
      │  │ 1. Pattern Encoding            │  │
      │  │ 2. Spiking Field Update        │  │
      │  │ 3. Syntropy Ordering           │  │
      │  │ 4. Neuroplastic Integration    │◄──┼─── Memory EMA
      │  │ 5. Oscillatory Modulation      │  │
      │  │ 6. Feedback Correction         │  │
      │  │ 7. Symbolic Interpretation     │  │
      │  └────────────┬───────────────────┘  │
      │               │                       │
      │         OUTPUT_RAW (64 dims)         │
      │         + Confidence score           │
      │         + Explanation (partial)      │
      └───────────────┬──────────────────────┘
                      │
                      ▼
      ┌──────────────────────────────────────┐
      │  Build Inference Context             │
      │  • input_vector                      │
      │  • model_output (raw)                │
      │  • session_history                   │
      │  • memory_state                      │
      │  • user_metadata                     │
      └───────────────┬──────────────────────┘
                      │
                      ▼
      ┌──────────────────────────────────────┐
      │  Policy Adapter.evaluate()           │
      │  • Check user risk profile           │
      │  • Check output uncertainty          │
      │  • Check output pattern matches      │
      │  • Check request frequency/rate      │
      │  • Check policy version compatibility│
      └───────────────┬──────────────────────┘
                      │
                      ▼
          ┌─────────────────────────┐
          │  Governance Policy      │
          │  {                      │
          │    requires_suppression │
          │    requires_explanation │
          │    requires_escalation  │
          │    confidence_threshold │
          │  }                      │
          └──────────┬──────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────────┐    ┌──────────────────┐
    │  Check       │    │  Check           │
    │  Suppression │    │  Explanation     │
    └──┬───────────┘    └──────┬───────────┘
       │                       │
       │ YES                   │ YES
       │                       │
       ▼                       ▼
    output *= 0.3      trace = extract_trace()
                       output.explanation = trace
       │                       │
       └──────────┬────────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  Check Escalation    │
       └──────┬───────────────┘
              │
              │ YES
              │
              ▼
       ┌──────────────────────┐
       │  Enqueue for Review  │
       │  Return: None        │
       └──────────────────────┘
       
       │ NO
       │
       ▼
   ┌──────────────────────┐
   │  Check Threshold     │
   │  if conf < thresh:   │
   │    action="defer"    │
   └──────┬───────────────┘
          │
          ▼
    ┌──────────────────────────┐
    │  FINAL OUTPUT            │
    │  • Vector (gated)        │
    │  • Confidence (adjusted) │
    │  • Explanation (if req)  │
    │  • Governance flags      │
    │  • Audit log entry       │
    └──────────────────────────┘
```

---

## Memory Feedback Loop

Critical insight: **Memory is part of governance context.**

```
Request 1: Input_1
         → SPI inference
         → Policy evaluation (memory=M_0)
         → Output_1
         → Update memory: M_1 = 0.9*M_0 + 0.1*activated_1
         → Store M_1

Request 2: Input_2
         → Load M_1
         → SPI inference (with M_1 context)
         → Policy evaluation (memory=M_1)  ← Different policy!
         → Output_2
         → Update memory: M_2 = 0.9*M_1 + 0.1*activated_2
         → Store M_2
```

**Effect**: Governance treats repeated similar requests differently:
- First request: Full scrutiny, possibly suppressed
- Second request: More familiar, lower suppression
- Fifth request: Pattern recognized, increased confidence allowed

This **breaks IID assumption**. System is inherently non-stationary.

---

## Governance Gates: Detailed Mechanics

### Gate 1: Suppression Gate

**Input**: Raw output confidence `c ∈ [0, 1]`
**Policy flag**: `requires_suppression: bool`
**Transformation**:

```python
if requires_suppression:
    c_gated = c * suppression_factor  # e.g., 0.3
else:
    c_gated = c
```

**Semantics**: Reduce confidence in contexts where policy is skeptical.

**Audit trail**:
```json
{
  "original_confidence": 0.87,
  "gated_confidence": 0.26,
  "suppression_factor": 0.3,
  "reason": "high_risk_user_category",
  "policy_version": "v2.1.5"
}
```

### Gate 2: Explanation Gate

**Input**: Model produces sparse symbolic trace
**Policy flag**: `requires_explanation: bool`
**Action**:

```python
if requires_explanation:
    explanation = {
        "decision_path": symbolic_trace,
        "key_activations": top_k_neurons,
        "memory_influence": memory_contribution_analysis,
        "pattern_matched": most_similar_historical_pattern,
        "governance_notes": policy_reasoning
    }
else:
    explanation = None
```

**Semantics**: For certain users/contexts, provide full reasoning. Enables:
- User understanding
- Dispute resolution
- Model debugging
- Fairness auditing

### Gate 3: Escalation Gate

**Input**: Policy evaluation result
**Policy flag**: `requires_escalation: bool`
**Action**:

```python
if requires_escalation:
    # Queue for human review
    REVIEW_QUEUE.put({
        "priority": "high",
        "type": "governance_escalation",
        "model_output": output_raw,
        "policy_applied": policy,
        "context": context,
        "timeout_hours": 2,
        "assigned_reviewer": None  # Human assignment pending
    })
    return {"status": "pending_review", "request_id": ...}
else:
    return output_dict
```

**Semantics**: System admits uncertainty. Routes non-routine cases to humans.

---

## Policy Rule Examples

### Rule: High-Risk User Suppression

```python
def _is_high_risk_user(self, user_id: str) -> bool:
    """Users in watch-list get suppressed outputs"""
    return user_id in self.high_risk_users_db

policy.requires_suppression = self._is_high_risk_user(context.user_id)
```

### Rule: Uncertainty-Triggered Explanation

```python
def _requires_explanation(self, output: torch.Tensor) -> bool:
    """High-uncertainty outputs need explanation"""
    entropy = -(output * torch.log(output + 1e-8)).sum()
    return entropy > 0.5

policy.requires_explanation = self._requires_explanation(output_raw)
```

### Rule: Sensitive Output Escalation

```python
def _requires_escalation(self, output: torch.Tensor) -> bool:
    """Outputs in sensitive range go to human"""
    # Dimension 7 might be "decision to refuse service"
    if output[7] > 0.8:
        return True
    # Or very confident prediction on minority group
    if output.max() > 0.95 and context.user_demographics['minority']:
        return True
    return False

policy.requires_escalation = self._requires_escalation(output_raw)
```

### Rule: Request Rate Limiting

```python
def _rate_limit_check(self, context: InferenceContext) -> GovernancePolicy:
    """Suppress if user exceeds request frequency"""
    last_hour_requests = self.request_log.count_recent(
        user_id=context.user_id,
        minutes=60
    )
    if last_hour_requests > 1000:
        policy.requires_suppression = True
        policy.confidence_threshold = 0.9  # Raise bar
    return policy
```

---

## Audit Trail: Complete Governance History

Every inference decision recorded:

```json
{
  "request_id": "req_abc123",
  "timestamp": "2026-01-02T15:33:22Z",
  "session_id": "sess_xyz789",
  "user_id": "user_42",
  
  "input": {
    "shape": [128],
    "hash": "0xdeadbeef"
  },
  
  "model_output": {
    "raw_vector": [...],
    "raw_confidence": 0.87,
    "raw_explanation_partial": "Pattern matched to Q3_2024_trends"
  },
  
  "inference_context": {
    "memory_state_age": "5 requests",
    "request_history_size": 27,
    "oscillator_phase": 2.34
  },
  
  "governance": {
    "policy_version": "v2.1.5",
    "policy_rules_applied": [
      "high_risk_user_suppression",
      "uncertainty_explanation_gate"
    ],
    "requires_suppression": true,
    "requires_explanation": true,
    "requires_escalation": false,
    "confidence_threshold": 0.0
  },
  
  "output": {
    "vector": [...],
    "confidence": 0.26,  ← gated by 0.3
    "explanation": {...},
    "governance_flags": ["suppressed", "explained"],
    "suggested_action": "allow",
    "policy_version": "v2.1.5"
  },
  
  "decision_time_ms": 42
}
```

**Retention**: All records kept for:
- **Compliance audit**: Prove policy was enforced
- **Appeal**: User can request review of their decisions
- **Fairness analysis**: Detect discriminatory patterns
- **Model improvement**: Learn which policies correlate with good outcomes

---

## Deployment Topology

```
┌──────────────────────────────────────────────────────────┐
│                   API Gateway                            │
│  • TLS termination                                       │
│  • Rate limiting (layer 1)                              │
│  • Request routing                                       │
└───────────────────────┬────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌────────┐    ┌────────┐    ┌────────┐
    │Service │    │Service │    │Service │  (N instances)
    │  1     │    │  2     │    │  3     │
    │        │    │        │    │        │
    │ SPI    │    │ SPI    │    │ SPI    │
    │Policy  │    │Policy  │    │Policy  │
    └────┬───┘    └────┬───┘    └────┬───┘
         │             │             │
         └─────────────┼─────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Memory   │  │ Policy   │  │ Audit    │
    │ Store    │  │ Engine   │  │ Log DB   │
    │(Redis)   │  │(Postgres)│  │(Postgres)│
    └──────────┘  └──────────┘  └──────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                   ┌────▼─────┐
                   │ Analytics │
                   │  & Reports│
                   └───────────┘
```

**Critical**: Every service instance:
- ✅ Can read/write memory state
- ✅ Can read policy rules (versioned)
- ✅ Can write audit logs
- ✅ Independently evaluates policy (consistent logic)

---

## Failure Modes & Recovery

### Scenario 1: Policy Engine Down

```
Inference path blocked: Context → Policy Eval → [DOWN]

Recovery:
  → Fall back to "conservative" policy
  → Suppress all outputs (confidence *= 0.1)
  → Require explanation on everything
  → Log to audit trail: "policy_engine_fallback_v2"
```

### Scenario 2: Memory Store Unavailable

```
Inference path blocked: Load Memory → [DOWN]

Recovery:
  → Initialize memory to zero state (M = 0)
  → Process with stateless behavior
  → All outputs tagged: "memory_degraded"
  → Governance adjusted: suppress uncertainty > 0.5
```

### Scenario 3: Audit Log Full

```
Data path blocked: Write Audit Log → [QUEUE FULL]

Recovery:
  → Reject new inferences until log drained
  → Escalate all pending to human review
  → Log to syslog (in-memory backup)
  → Alert ops team: "audit_log_overflow"
```

---

## Integration Checklist

- [ ] Policy rules defined and versioned in policy_adapter.py
- [ ] Memory store connected to MemoryStore (redis/postgres)
- [ ] Audit logging configured (database + syslog)
- [ ] Governance flags documented in output schema
- [ ] API response includes governance metadata
- [ ] Dashboard shows policy enforcement metrics
- [ ] Human review queue integrated with workforce
- [ ] Appeal mechanism documented for users
- [ ] Fairness audits scheduled (monthly)
- [ ] Policy versioning and rollback procedures tested
