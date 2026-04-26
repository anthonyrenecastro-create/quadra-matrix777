"""
Governance Policy Adapter - Runtime policy enforcement for conditioned inference.

Enables governance as a first-class primitive in the inference pipeline:
- Policy evaluation based on input/output context
- Output suppression and modification
- Feature gating (what components can execute)
- Symbolic trace generation for explainability
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions that can be triggered by governance policies."""
    ALLOW = "allow"
    SUPPRESS = "suppress"
    REDUCE = "reduce"
    EXPLAIN = "explain"
    ESCALATE = "escalate"
    GATE = "gate"  # Prevent component execution


@dataclass
class PolicyContext:
    """Context information for policy evaluation."""
    input_text: Optional[str] = None
    input_vector: Optional[Any] = None
    neural_magnitude: float = 0.0
    pattern_confidence: float = 0.0
    symbolic_concepts: List[str] = field(default_factory=list)
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    request_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dict for logging/tracing."""
        return {
            'input_text': self.input_text[:100] if self.input_text else None,
            'neural_magnitude': self.neural_magnitude,
            'pattern_confidence': self.pattern_confidence,
            'symbolic_concepts': self.symbolic_concepts,
            'source_ip': self.source_ip,
            'user_id': self.user_id,
            'request_id': self.request_id,
        }


@dataclass
class PolicyDecision:
    """Decision output from policy evaluation."""
    action: PolicyAction = PolicyAction.ALLOW
    confidence: float = 1.0
    suppression_factor: float = 1.0  # 1.0 = no change, 0.3 = 70% reduction
    requires_explanation: bool = False
    gated_components: List[str] = field(default_factory=list)  # Components to skip
    reason: str = ""
    audit_entry: Dict[str, Any] = field(default_factory=dict)


class PolicyRule:
    """Base class for policy rules."""
    
    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
    
    def evaluate(self, context: PolicyContext) -> Optional[PolicyDecision]:
        """
        Evaluate if this rule applies.
        Return None if rule doesn't apply, PolicyDecision if it does.
        """
        raise NotImplementedError


class HighRiskContentRule(PolicyRule):
    """Suppress high-risk patterns in output."""
    
    RISK_KEYWORDS = {
        'violence', 'harm', 'illegal', 'exploit', 'unsafe',
        'manipulate', 'deceive', 'attack'
    }
    
    def __init__(self):
        super().__init__("high_risk_content", priority=100)
    
    def evaluate(self, context: PolicyContext) -> Optional[PolicyDecision]:
        """Check if input/concepts contain risk keywords."""
        text_to_check = (context.input_text or "").lower()
        concepts_text = " ".join(context.symbolic_concepts).lower()
        combined = text_to_check + " " + concepts_text
        
        risk_matches = [kw for kw in self.RISK_KEYWORDS if kw in combined]
        
        if risk_matches:
            return PolicyDecision(
                action=PolicyAction.REDUCE,
                confidence=min(len(risk_matches) * 0.3, 0.95),
                suppression_factor=0.3,
                requires_explanation=True,
                reason=f"High-risk content detected: {', '.join(risk_matches)}"
            )
        return None


class HighConfidenceRule(PolicyRule):
    """Require explanation for high-confidence outputs."""
    
    def __init__(self, threshold: float = 0.85):
        super().__init__("high_confidence", priority=50)
        self.threshold = threshold
    
    def evaluate(self, context: PolicyContext) -> Optional[PolicyDecision]:
        """Require explanation if confidence exceeds threshold."""
        if context.pattern_confidence > self.threshold:
            return PolicyDecision(
                action=PolicyAction.EXPLAIN,
                requires_explanation=True,
                reason=f"High confidence decision ({context.pattern_confidence:.2%})"
            )
        return None


class NovelContextRule(PolicyRule):
    """Gate advanced components for novel/uncertain inputs."""
    
    def __init__(self, uncertainty_threshold: float = 0.3):
        super().__init__("novel_context", priority=30)
        self.uncertainty_threshold = uncertainty_threshold
    
    def evaluate(self, context: PolicyContext) -> Optional[PolicyDecision]:
        """Gate oscillatory modulation for uncertain contexts."""
        # High uncertainty = low confidence
        uncertainty = 1.0 - context.pattern_confidence
        
        if uncertainty > self.uncertainty_threshold:
            return PolicyDecision(
                action=PolicyAction.GATE,
                gated_components=['oscillatory_modulation', 'feedback_loop'],
                requires_explanation=True,
                reason=f"High uncertainty ({uncertainty:.2%}); disabling advanced components"
            )
        return None


class PolicyEngine:
    """
    Central policy evaluation engine for runtime governance.
    
    Evaluates policies in priority order and returns combined decision.
    Enables governance as first-class primitive in inference.
    """
    
    def __init__(self):
        self.rules: List[PolicyRule] = [
            HighRiskContentRule(),
            HighConfidenceRule(threshold=0.85),
            NovelContextRule(uncertainty_threshold=0.3),
        ]
        self.audit_log: List[Dict[str, Any]] = []
        logger.info(f"PolicyEngine initialized with {len(self.rules)} rules")
    
    def add_rule(self, rule: PolicyRule):
        """Register a new policy rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Policy rule added: {rule.name} (priority={rule.priority})")
    
    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """
        Evaluate all rules in priority order.
        
        Returns combined decision with strongest enforcement action.
        """
        decisions = []
        
        for rule in self.rules:
            decision = rule.evaluate(context)
            if decision:
                decisions.append(decision)
        
        if not decisions:
            decision = PolicyDecision(
                action=PolicyAction.ALLOW,
                reason="All rules passed"
            )
        else:
            # Combine decisions: use strongest suppression, gate all components, etc.
            decision = self._combine_decisions(decisions)
        
        # Audit
        decision.audit_entry = {
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'context': context.to_dict(),
            'decision': {
                'action': decision.action.value,
                'confidence': decision.confidence,
                'suppression_factor': decision.suppression_factor,
                'gated_components': decision.gated_components,
                'reason': decision.reason,
            },
            'rules_evaluated': len(self.rules),
            'rules_triggered': len(decisions),
        }
        self.audit_log.append(decision.audit_entry)
        
        return decision
    
    def _combine_decisions(self, decisions: List[PolicyDecision]) -> PolicyDecision:
        """Combine multiple decisions into one."""
        # Use strongest action
        action_priority = {
            PolicyAction.SUPPRESS: 4,
            PolicyAction.ESCALATE: 3,
            PolicyAction.GATE: 2,
            PolicyAction.REDUCE: 1,
            PolicyAction.EXPLAIN: 1,
            PolicyAction.ALLOW: 0,
        }
        
        action = max(decisions, key=lambda d: action_priority.get(d.action, -1)).action
        
        combined = PolicyDecision(
            action=action,
            confidence=max(d.confidence for d in decisions),
            suppression_factor=min(d.suppression_factor for d in decisions),
            requires_explanation=any(d.requires_explanation for d in decisions),
            gated_components=list(set().union(*(d.gated_components for d in decisions))),
            reason=" | ".join(d.reason for d in decisions if d.reason),
        )
        
        return combined
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit entries."""
        return self.audit_log[-limit:]


class GovernanceService:
    """
    High-level governance service integrating policy engine with symbolic interpretation.
    
    Provides:
    - Policy evaluation
    - Output modification (suppression/reduction)
    - Symbolic trace attachment
    - Audit and compliance tracking
    """
    
    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        self.policy_engine = policy_engine or PolicyEngine()
        self.model_version = "spi-symbolic-0.2.0"
        logger.info("GovernanceService initialized")
    
    def evaluate_and_condition_output(
        self,
        output: Dict[str, Any],
        context: PolicyContext
    ) -> Dict[str, Any]:
        """
        Evaluate policy and condition output accordingly.
        
        Returns modified output dict with governance applied.
        """
        decision = self.policy_engine.evaluate(context)
        
        output['governance'] = {
            'policy_action': decision.action.value,
            'confidence': decision.confidence,
            'explanation_required': decision.requires_explanation,
            'gated_components': decision.gated_components,
            'audit_id': decision.audit_entry.get('timestamp', ''),
        }
        
        # Apply suppression
        if decision.action in [PolicyAction.SUPPRESS, PolicyAction.REDUCE]:
            # Reduce output magnitudes
            if 'symbolic_result' in output:
                output['symbolic_result'] = f"[MODERATED] {output['symbolic_result'][:50]}..."
            if 'neural_output' in output and isinstance(output['neural_output'], (int, float)):
                output['neural_output'] *= decision.suppression_factor
            if 'score' in output and isinstance(output['score'], (int, float)):
                output['score'] *= decision.suppression_factor
        
        # Add explanation if required
        if decision.requires_explanation:
            output['explanation'] = {
                'reason': decision.reason,
                'policy_action': decision.action.value,
                'symbolic_trace': self._generate_symbolic_trace(context),
            }
        
        # Mark gated components
        if decision.gated_components:
            output['_gated_components'] = decision.gated_components
        
        return output
    
    def _generate_symbolic_trace(self, context: PolicyContext) -> str:
        """Generate symbolic reasoning trace for explainability."""
        trace = f"Policy Evaluation Trace\n"
        trace += f"  Input concepts: {context.symbolic_concepts}\n"
        trace += f"  Pattern confidence: {context.pattern_confidence:.2%}\n"
        trace += f"  Neural magnitude: {context.neural_magnitude:.4f}\n"
        return trace
