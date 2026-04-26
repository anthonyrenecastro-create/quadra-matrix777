import copy
import math
import random
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn.functional as F


# ============================================================
# TRACE / CAUSAL DATA STRUCTURES
# ============================================================


@dataclass
class TraceEvent:
    tick: int
    opcode: str
    payload: Any
    channel: Optional[int] = None
    domain: Optional[int] = None
    source: Optional[Tuple[int, int]] = None
    target: Optional[Tuple[int, int]] = None
    cause_state_ids: List[str] = field(default_factory=list)
    cause_memory_keys: List[str] = field(default_factory=list)
    task_score_before: float = 0.0
    task_score_after: float = 0.0
    changed_downstream: bool = False
    influenced_branch: bool = False
    influenced_output: bool = False
    influenced_state: bool = False


@dataclass
class ActiveState:
    id: str
    value: float
    channel: int
    domain: int
    coherence: float = 0.0
    energy: float = 1.0
    age: int = 0
    tags: List[str] = field(default_factory=list)
    influenced_other_state: bool = False
    influenced_output: bool = False


@dataclass
class MemoryReadRecord:
    tick: int
    key: str
    value: Any
    consumed_by_branch: bool = False
    consumed_by_output: bool = False
    consumed_by_emit: bool = False
    consumed_by_field: bool = False
    consumed_by_couple: bool = False
    changed_downstream: bool = False


@dataclass
class CoordinationTask:
    min_distinct_domains_emitted: int = 2
    min_distinct_domains_coupled: int = 2
    require_memory_use: bool = True
    require_output: bool = True
    require_cross_domain_sequence: bool = True


# ============================================================
# MORPHOFIELD RUNTIME (PDE-ENHANCED)
# ============================================================


@dataclass
class Runtime:
    num_channels: int = 4
    num_domains: int = 6
    task_spec: CoordinationTask = field(default_factory=CoordinationTask)
    device: str = "cpu"

    # PDE parameters (recommended ranges)
    alpha: float = 1.5
    beta: float = 0.08
    gamma1: float = 0.35
    zeta: float = 0.15
    omega: float = 0.15
    gamma5: float = 0.10
    theta: float = 0.30
    dt: float = 0.01
    relaxation: float = 0.2
    eps: float = 1e-8

    fields: Dict[str, List[List[float]]] = field(default_factory=dict)
    active_states: List[ActiveState] = field(default_factory=list)
    retired_states: Dict[str, ActiveState] = field(default_factory=dict)
    memory_bank: Dict[str, Any] = field(default_factory=dict)
    memory_writes: List[Tuple[int, str, Any]] = field(default_factory=list)
    memory_reads: List[MemoryReadRecord] = field(default_factory=list)
    attractor_table: Dict[Tuple[int, int], Dict[str, int]] = field(default_factory=dict)
    output_buffer: List[str] = field(default_factory=list)

    interactions: int = 0
    transitions: int = 0
    steps: int = 0
    failures: int = 0
    task_score: float = 0.0

    trace: List[TraceEvent] = field(default_factory=list)
    emitted_effects: List[Tuple[int, float, int, int]] = field(default_factory=list)
    coupling_effects: List[Tuple[int, int]] = field(default_factory=list)
    field_updates: List[Tuple[int, str, int, int, float]] = field(default_factory=list)

    state_effects: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    current_state_causes: List[str] = field(default_factory=list)
    current_memory_causes: List[str] = field(default_factory=list)
    last_memory_event_by_key: Dict[str, int] = field(default_factory=dict)
    last_state_event_by_id: Dict[str, int] = field(default_factory=dict)
    task_score_history: List[Tuple[int, float]] = field(default_factory=list)

    # PDE internal tensors, one 1D field per channel/domain lattice
    phi1: Optional[torch.Tensor] = None  # shape (C, D)
    phi5: Optional[torch.Tensor] = None  # shape (C, D)
    Phi: Optional[torch.Tensor] = None   # shape (C, D)
    pde_last_stats: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.fields:
            self.fields = {
                "excitability": [[0.5 for _ in range(self.num_domains)] for _ in range(self.num_channels)],
                "persistence": [[0.2 for _ in range(self.num_domains)] for _ in range(self.num_channels)],
                "global_phi": [[0.0 for _ in range(self.num_domains)] for _ in range(self.num_channels)],
                "coherence": [[0.0 for _ in range(self.num_domains)] for _ in range(self.num_channels)],
            }
        dev = torch.device(self.device)
        self.phi1 = (torch.randn(self.num_channels, self.num_domains, device=dev) * 0.15).float()
        self.phi5 = (0.05 + 0.15 * torch.rand(self.num_channels, self.num_domains, device=dev)).float()
        self.Phi = torch.zeros(self.num_channels, self.num_domains, device=dev).float()
        self.task_score_history.append((self.steps, self.task_score))

    def clamp_coords(self, channel: int, domain: int) -> Tuple[int, int]:
        return channel % self.num_channels, domain % self.num_domains

    # -------- PDE solver (1D circular finite differences per channel) --------
    def _lap1d(self, x: torch.Tensor) -> torch.Tensor:
        # x shape (C, D)
        xp = torch.roll(x, shifts=1, dims=1)
        xn = torch.roll(x, shifts=-1, dims=1)
        return xp - 2.0 * x + xn

    def pde_step(self, spike_feedback: Optional[torch.Tensor] = None):
        lap_phi1 = self._lap1d(self.phi1)
        bi_lap_phi1 = self._lap1d(lap_phi1)
        lap_phi5 = self._lap1d(self.phi5)
        lap_Phi = self._lap1d(self.Phi)

        reaction = -self.alpha * (self.phi1 ** 3) + self.zeta * lap_Phi
        diffusion = -self.gamma1 * lap_phi1 + self.beta * bi_lap_phi1
        d_phi1 = diffusion + reaction

        log_term = self.omega * self.phi5 * torch.log(torch.abs(self.phi5) + self.eps)
        advection = self.theta * (lap_phi5 * self.Phi + self.phi5 * lap_Phi)
        d_phi5 = -self.gamma5 * lap_phi5 + log_term + advection

        max_abs = max(float(torch.max(torch.abs(d_phi1)).item()), float(torch.max(torch.abs(d_phi5)).item()))
        local_dt = self.dt
        if max_abs > 1.0:
            local_dt = local_dt * max(0.1, 1.0 / max_abs)

        phi1_candidate = self.phi1 + d_phi1 * local_dt
        phi5_candidate = self.phi5 + d_phi5 * local_dt

        self.phi1 = (1.0 - self.relaxation) * self.phi1 + self.relaxation * phi1_candidate
        self.phi5 = (1.0 - self.relaxation) * self.phi5 + self.relaxation * phi5_candidate

        self.phi1 = torch.clamp(self.phi1, -3.0, 3.0)
        self.phi5 = torch.clamp(self.phi5, 1e-6, 5.0)

        if spike_feedback is not None:
            # spike_feedback expected shape (C, D) or broadcastable
            self.Phi = 0.85 * self.Phi + 0.15 * spike_feedback.to(self.Phi.device)
        else:
            self.Phi = 0.995 * self.Phi
        self.Phi = torch.clamp(self.Phi, -3.0, 3.0)

        self.pde_last_stats = {
            "adaptive_dt": float(local_dt),
            "max_abs_dphi1": float(torch.max(torch.abs(d_phi1)).item()),
            "max_abs_dphi5": float(torch.max(torch.abs(d_phi5)).item()),
            "phi1_mean": float(torch.mean(self.phi1).item()),
            "phi5_mean": float(torch.mean(self.phi5).item()),
            "phi1_var": float(torch.var(self.phi1).item()),
            "phi5_var": float(torch.var(self.phi5).item()),
        }

        # Mirror PDE fields into scalar runtime fields
        for c in range(self.num_channels):
            for d in range(self.num_domains):
                self.fields["excitability"][c][d] = float(torch.sigmoid(self.phi1[c, d]).item())
                self.fields["persistence"][c][d] = float(torch.sigmoid(self.phi5[c, d]).item())
                self.fields["global_phi"][c][d] = float(torch.sigmoid(self.Phi[c, d]).item())

    # ---------------------- provenance helpers ----------------------
    def set_current_state_causes(self, state_ids: List[str]):
        self.current_state_causes = list(dict.fromkeys(state_ids))

    def set_current_memory_causes(self, keys: List[str]):
        self.current_memory_causes = list(dict.fromkeys(keys))

    def clear_current_causes(self):
        self.current_state_causes = []
        self.current_memory_causes = []

    def all_states(self) -> List[ActiveState]:
        return list(self.retired_states.values()) + list(self.active_states)

    def count_useful_states(self) -> int:
        return sum(1 for st in self.all_states() if st.influenced_other_state and st.influenced_output)

    # --------------------------- task checks ---------------------------
    def distinct_emitted_domains(self) -> set:
        return {dm for _, _, _, dm in self.emitted_effects}

    def distinct_coupled_domains(self) -> set:
        ds = set()
        for s, t in self.coupling_effects:
            ds.add(s)
            ds.add(t)
        return ds

    def has_true_interdomain_dependency(self) -> bool:
        for ev in self.trace:
            if ev.opcode in {"COUPLE", "STATE_COUPLE"} and isinstance(ev.payload, dict):
                src = ev.payload.get("src_domain")
                dst = ev.payload.get("dst_domain")
                if src is not None and dst is not None and src != dst:
                    return True
        return False

    def has_useful_memory(self) -> bool:
        for rec in self.memory_reads:
            if rec.changed_downstream and (rec.consumed_by_branch or rec.consumed_by_output):
                return True
        return False

    def recompute_task_score(self):
        repeated_attractors = 0
        for _, bucket in self.attractor_table.items():
            for _, count in bucket.items():
                if count >= 2:
                    repeated_attractors += 1

        inter_domain_ok = self.has_true_interdomain_dependency()
        if not inter_domain_ok:
            self.task_score = 0.0
            self.task_score_history.append((self.steps, self.task_score))
            return

        score = 0.0
        if len(self.output_buffer) > 0:
            score += 0.15
        if repeated_attractors > 0:
            score += 0.10
        if self.has_useful_memory():
            score += 0.25
        if self.count_useful_states() > 0:
            score += 0.25
        if len(self.distinct_emitted_domains()) >= self.task_spec.min_distinct_domains_emitted:
            score += 0.15
        if len(self.distinct_coupled_domains()) >= self.task_spec.min_distinct_domains_coupled:
            score += 0.10

        self.task_score = min(1.0, score)
        self.task_score_history.append((self.steps, self.task_score))

    def log(self, opcode: str, payload: Any, channel=None, domain=None, source=None, target=None):
        before = self.task_score
        self.recompute_task_score()
        after = self.task_score
        self.trace.append(
            TraceEvent(
                tick=self.steps,
                opcode=opcode,
                payload=payload,
                channel=channel,
                domain=domain,
                source=source,
                target=target,
                cause_state_ids=list(self.current_state_causes),
                cause_memory_keys=list(self.current_memory_causes),
                task_score_before=before,
                task_score_after=after,
            )
        )

    # --------------------------- runtime ops ---------------------------
    def emit_state(self, value: float, channel: int, domain: int, tag: Optional[str] = None):
        channel, domain = self.clamp_coords(channel, domain)
        st = ActiveState(
            id=str(uuid.uuid4()),
            value=float(value),
            channel=channel,
            domain=domain,
            coherence=self.fields["coherence"][channel][domain],
            energy=1.0 + self.fields["persistence"][channel][domain],
            age=0,
            tags=[tag] if tag else [],
        )
        self.active_states.append(st)
        self.transitions += 1
        self.emitted_effects.append((self.steps, round(float(value), 6), channel, domain))
        self.log("EMIT", round(float(value), 6), channel=channel, domain=domain, target=(channel, domain))
        return st

    def record_attractor(self, channel: int, domain: int, label: str):
        key = (channel, domain)
        if key not in self.attractor_table:
            self.attractor_table[key] = {}
        self.attractor_table[key][label] = self.attractor_table[key].get(label, 0) + 1

    def update_memory(self, key: str, value: Any):
        self.memory_bank[key] = value
        self.memory_writes.append((self.steps, key, value))
        self.log("UPDATE_MEMORY", {"key": key, "value": value})

    def read_memory(self, key: str) -> Any:
        val = self.memory_bank.get(key, None)
        self.memory_reads.append(MemoryReadRecord(tick=self.steps, key=key, value=val))
        self.log("READ_MEMORY", {"key": key, "value": val})
        return val

    def couple(self, src_domain: int, dst_domain: int):
        src_domain %= self.num_domains
        dst_domain %= self.num_domains
        self.interactions += 1
        self.coupling_effects.append((src_domain, dst_domain))
        self.log("COUPLE", {"src_domain": src_domain, "dst_domain": dst_domain}, source=(None, src_domain), target=(None, dst_domain))
        for ch in range(self.num_channels):
            src_coh = self.fields["coherence"][ch][src_domain]
            self.fields["coherence"][ch][dst_domain] = min(1.0, 0.8 * self.fields["coherence"][ch][dst_domain] + 0.2 * src_coh + 0.05)
            self.fields["global_phi"][ch][dst_domain] = min(1.0, 0.9 * self.fields["global_phi"][ch][dst_domain] + 0.1 * self.fields["global_phi"][ch][src_domain] + 0.03)

    def tick_states(self):
        # Use active states as spike-like feedback map for PDE fields.
        spike_like = torch.zeros(self.num_channels, self.num_domains, device=self.phi1.device)
        for st in self.active_states:
            spike_like[st.channel, st.domain] += float(max(0.0, st.value))
        if torch.max(spike_like) > 0:
            spike_like = spike_like / (torch.max(spike_like) + 1e-6)
        self.pde_step(spike_feedback=spike_like)

        new_states = []
        produced_effects = 0
        for st in self.active_states:
            st.age += 1
            ex = self.fields["excitability"][st.channel][st.domain]
            pe = self.fields["persistence"][st.channel][st.domain]
            co = self.fields["coherence"][st.channel][st.domain]
            gp = self.fields["global_phi"][st.channel][st.domain]

            st.energy = st.energy * (0.82 + 0.12 * pe)
            st.coherence = 0.65 * st.coherence + 0.35 * co
            st.value = st.value * (0.88 + 0.08 * ex)

            label = f"{round(st.value, 2)}|c{st.channel}d{st.domain}"
            self.record_attractor(st.channel, st.domain, label)
            self.set_current_state_causes([st.id])

            if st.energy > 0.6:
                self.fields["coherence"][st.channel][st.domain] = min(1.0, self.fields["coherence"][st.channel][st.domain] + 0.05)
                self.field_updates.append((self.steps, "coherence", st.channel, st.domain, self.fields["coherence"][st.channel][st.domain]))
                self.log("STATE_FIELD_UPDATE", {"state": st.id, "field": "coherence", "delta": 0.05}, channel=st.channel, domain=st.domain)
                produced_effects += 1

            if st.coherence > 0.45 and st.energy > 0.4:
                target_domain = (st.domain + 1) % self.num_domains
                child_value = st.value * 0.5
                self.emit_state(child_value, st.channel, target_domain, tag="state_child")
                self.log("STATE_EMIT", {"state": st.id, "child_value": round(child_value, 6)}, channel=st.channel, domain=target_domain, source=(st.channel, st.domain), target=(st.channel, target_domain))
                st.influenced_other_state = True
                produced_effects += 1

            if st.energy > 0.75 and gp > 0.2:
                target_domain = (st.domain + 2) % self.num_domains
                if target_domain != st.domain:
                    self.couple(st.domain, target_domain)
                    self.log("STATE_COUPLE", {"state": st.id, "src_domain": st.domain, "dst_domain": target_domain}, channel=st.channel, domain=st.domain, source=(st.channel, st.domain), target=(st.channel, target_domain))
                    produced_effects += 1

            if st.age >= 2 and st.coherence > 0.35:
                mem_key = f"state_{st.channel}_{st.domain}"
                mem_val = round(st.value, 4)
                self.update_memory(mem_key, mem_val)
                self.log("STATE_MEMORY_WRITE", {"state": st.id, "key": mem_key, "value": mem_val}, channel=st.channel, domain=st.domain)
                produced_effects += 1

            self.clear_current_causes()

            if st.energy > 0.14 and st.age < 12:
                new_states.append(st)
            else:
                self.retired_states[st.id] = copy.deepcopy(st)

        self.active_states = new_states
        self.steps += 1
        self.log("TICK", {"tick": self.steps, "state_effects": produced_effects, "pde": self.pde_last_stats})


# ============================================================
# PROGRAM DSL (MINIMAL BUT RUNNABLE)
# ============================================================


VAR_NAMES = ["x", "y", "z", "ch", "dm", "val"]


class Expr:
    def eval(self, rt: Runtime, env: Dict[str, Any]):
        raise NotImplementedError


class ConstExpr(Expr):
    def __init__(self, value):
        self.value = value

    def eval(self, rt: Runtime, env: Dict[str, Any]):
        return self.value


class VarExpr(Expr):
    def __init__(self, name):
        self.name = name

    def eval(self, rt: Runtime, env: Dict[str, Any]):
        return env.get(self.name, 0)


class BinExpr(Expr):
    def __init__(self, a: Expr, op: str, b: Expr):
        self.a, self.op, self.b = a, op, b

    def eval(self, rt: Runtime, env: Dict[str, Any]):
        av = self.a.eval(rt, env)
        bv = self.b.eval(rt, env)
        if self.op == "+":
            return av + bv
        if self.op == "-":
            return av - bv
        if self.op == "*":
            return av * bv
        if self.op == "/":
            return av / (bv + 1e-6)
        if self.op == ">":
            return float(av > bv)
        return 0


class Stmt:
    def execute(self, rt: Runtime, env: Dict[str, Any]):
        raise NotImplementedError


class AssignStmt(Stmt):
    def __init__(self, target: str, expr: Expr):
        self.target = target
        self.expr = expr

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        env[self.target] = self.expr.eval(rt, env)


class EmitStmt(Stmt):
    def __init__(self, val_expr: Expr, ch_expr: Expr, dm_expr: Expr):
        self.val_expr, self.ch_expr, self.dm_expr = val_expr, ch_expr, dm_expr

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        v = float(self.val_expr.eval(rt, env))
        ch = int(self.ch_expr.eval(rt, env))
        dm = int(self.dm_expr.eval(rt, env))
        rt.emit_state(v, ch, dm, tag="prog_emit")


class CoupleStmt(Stmt):
    def __init__(self, src_expr: Expr, dst_expr: Expr):
        self.src_expr, self.dst_expr = src_expr, dst_expr

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        rt.couple(int(self.src_expr.eval(rt, env)), int(self.dst_expr.eval(rt, env)))


class OutputStmt(Stmt):
    def __init__(self, expr: Expr):
        self.expr = expr

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        msg = str(self.expr.eval(rt, env))
        rt.output_buffer.append(msg)
        rt.log("OUTPUT", msg)


class TickStmt(Stmt):
    def __init__(self, count_expr: Expr):
        self.count_expr = count_expr

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        n = int(max(0, self.count_expr.eval(rt, env)))
        for _ in range(n):
            rt.tick_states()


class IfStmt(Stmt):
    def __init__(self, cond_expr: Expr, then_stmt: Stmt, else_stmt: Optional[Stmt] = None):
        self.cond_expr = cond_expr
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        cond = self.cond_expr.eval(rt, env)
        rt.log("IF", {"cond": cond})
        if cond:
            self.then_stmt.execute(rt, env)
        elif self.else_stmt is not None:
            self.else_stmt.execute(rt, env)


class BlockStmt(Stmt):
    def __init__(self, statements: List[Stmt]):
        self.statements = statements

    def execute(self, rt: Runtime, env: Dict[str, Any]):
        for s in self.statements:
            s.execute(rt, env)


class Program:
    def __init__(self, body: BlockStmt, pid: Optional[str] = None, lineage: Optional[List[str]] = None):
        self.body = body
        self.id = pid or str(uuid.uuid4())
        self.lineage = lineage or []

    def run(self, rt: Runtime) -> Dict[str, Any]:
        env = {}
        try:
            self.body.execute(rt, env)
            success = True
        except Exception as e:
            rt.failures += 1
            env["runtime_error"] = str(e)
            success = False
        return {"success": success, "env": env}


# ============================================================
# FITNESS / EVOLUTION (COMPACT)
# ============================================================


def stmt_to_str(s: Stmt) -> str:
    return s.__class__.__name__


def flatten_statement_strings(program: Program) -> List[str]:
    return [stmt_to_str(s) for s in program.body.statements]


def score_runtime(program: Program, rt: Runtime, run_result: Dict[str, Any]) -> Dict[str, float]:
    valid_execution = 1.0 if run_result["success"] else 0.0
    transitions = min(1.0, rt.transitions / 8.0)
    memory_usage = min(1.0, len(rt.memory_bank) / 8.0)
    inter_domain = 1.0 if rt.has_true_interdomain_dependency() else 0.0
    repeated_attractors = sum(1 for _, bucket in rt.attractor_table.items() for _, c in bucket.items() if c >= 2)
    attractor_stability = min(1.0, repeated_attractors / 8.0)
    task_completion = rt.task_score

    instr_count = max(1, len(flatten_statement_strings(program)))
    rep_pen = max(0.0, (len(flatten_statement_strings(program)) - len(set(flatten_statement_strings(program)))) / instr_count)

    distinct_emit = len(rt.distinct_emitted_domains())
    distinct_couple = len(rt.distinct_coupled_domains())
    useful_states = rt.count_useful_states()

    pde_stability = 1.0 / (1.0 + rt.pde_last_stats.get("max_abs_dphi1", 0.0) + rt.pde_last_stats.get("max_abs_dphi5", 0.0))

    fitness = (
        2.5 * valid_execution
        + 1.0 * transitions
        + 0.4 * memory_usage
        + 2.0 * inter_domain
        + 0.6 * attractor_stability
        + 2.5 * task_completion
        + 0.4 * min(1.0, distinct_emit / 3.0)
        + 0.4 * min(1.0, distinct_couple / 3.0)
        + 0.6 * min(1.0, useful_states / 3.0)
        + 0.6 * pde_stability
        - 1.2 * rep_pen
    )

    return {
        "valid_execution": valid_execution,
        "transitions": transitions,
        "memory_usage": memory_usage,
        "inter_domain": inter_domain,
        "attractor_stability": attractor_stability,
        "task_completion": task_completion,
        "distinct_emit_domains": distinct_emit,
        "distinct_coupled_domains": distinct_couple,
        "useful_state_count": useful_states,
        "pde_stability": pde_stability,
        "instr_count": instr_count,
        "fitness": fitness,
    }


class ProgramRecord:
    def __init__(self, program: Program, metrics: Dict[str, float], runtime_snapshot: Runtime):
        self.program = program
        self.metrics = metrics
        self.runtime_snapshot = runtime_snapshot


OPS = ["emit", "couple", "tick", "output", "assign", "if"]


def rand_expr() -> Expr:
    if random.random() < 0.5:
        return ConstExpr(random.randint(0, 5))
    return VarExpr(random.choice(VAR_NAMES))


def rand_stmt() -> Stmt:
    op = random.choice(OPS)
    if op == "emit":
        return EmitStmt(rand_expr(), rand_expr(), rand_expr())
    if op == "couple":
        return CoupleStmt(rand_expr(), rand_expr())
    if op == "tick":
        return TickStmt(ConstExpr(random.randint(0, 2)))
    if op == "output":
        return OutputStmt(rand_expr())
    if op == "assign":
        return AssignStmt(random.choice(VAR_NAMES), rand_expr())
    then_stmt = EmitStmt(rand_expr(), rand_expr(), rand_expr())
    else_stmt = CoupleStmt(rand_expr(), rand_expr())
    return IfStmt(rand_expr(), then_stmt, else_stmt)


def rand_program(program_len: int) -> Program:
    return Program(BlockStmt([rand_stmt() for _ in range(program_len)]))


def clone_program(p: Program) -> Program:
    return Program(copy.deepcopy(p.body), lineage=p.lineage + [p.id])


def mutate_program(p: Program) -> Program:
    q = clone_program(p)
    if not q.body.statements:
        q.body.statements.append(rand_stmt())
        return q
    idx = random.randrange(len(q.body.statements))
    q.body.statements[idx] = rand_stmt()
    return q


def crossover_program(a: Program, b: Program) -> Program:
    sa = a.body.statements
    sb = b.body.statements
    if not sa:
        return clone_program(b)
    if not sb:
        return clone_program(a)
    ca = random.randrange(len(sa))
    cb = random.randrange(len(sb))
    child = sa[:ca] + sb[cb:]
    return Program(BlockStmt(copy.deepcopy(child)), lineage=[a.id, b.id])


def program_to_str(program: Program) -> str:
    return "\n".join(f"{i:02d}: {stmt_to_str(s)}" for i, s in enumerate(program.body.statements))


class MorphoFieldEvolutionEngine:
    def __init__(self, pop_size: int = 12, program_len: int = 8):
        self.pop_size = pop_size
        self.program_len = program_len
        self.population = [rand_program(program_len) for _ in range(pop_size)]
        self.generation = 0
        self.best_history: List[ProgramRecord] = []

    def evaluate_program(self, program: Program) -> ProgramRecord:
        rt = Runtime(num_channels=4, num_domains=6, task_spec=CoordinationTask())
        result = program.run(rt)
        rt.tick_states()
        metrics = score_runtime(program, rt, result)
        return ProgramRecord(program, metrics, rt)

    def select(self, records: List[ProgramRecord]) -> List[ProgramRecord]:
        records = sorted(records, key=lambda r: r.metrics["fitness"], reverse=True)
        return records[: max(2, self.pop_size // 3)]

    def reproduce(self, elites: List[ProgramRecord]) -> List[Program]:
        new_population: List[Program] = []
        for e in elites[:2]:
            new_population.append(clone_program(e.program))
        while len(new_population) < self.pop_size:
            mode = random.choice(["mutate", "crossover", "fresh"])
            if mode == "mutate":
                parent = random.choice(elites).program
                new_population.append(mutate_program(parent))
            elif mode == "crossover" and len(elites) >= 2:
                a = random.choice(elites).program
                b = random.choice(elites).program
                new_population.append(crossover_program(a, b))
            else:
                new_population.append(rand_program(self.program_len))
        return new_population[: self.pop_size]

    def step(self):
        t0 = time.perf_counter()
        records = [self.evaluate_program(p) for p in self.population]
        elites = self.select(records)
        best = elites[0]
        self.best_history.append(best)
        self.population = self.reproduce(elites)
        self.generation += 1
        batch_ms = (time.perf_counter() - t0) * 1000.0
        return best, records, batch_ms


if __name__ == "__main__":
    random.seed(42)
    engine = MorphoFieldEvolutionEngine(pop_size=12, program_len=8)
    for gen in range(10):
        best, records, batch_ms = engine.step()
        valid_rate = sum(r.metrics["valid_execution"] for r in records) / len(records)
        print(f"\n=== Generation {gen} ===")
        print("Batch runtime ms:", round(batch_ms, 3))
        print("Best fitness:", round(best.metrics["fitness"], 4))
        print("Core:", {k: round(best.metrics[k], 4) for k in ["valid_execution", "transitions", "memory_usage", "inter_domain", "attractor_stability", "task_completion"]})
        print("Coordination:", {
            "distinct_emit_domains": best.metrics["distinct_emit_domains"],
            "distinct_coupled_domains": best.metrics["distinct_coupled_domains"],
            "useful_state_count": best.metrics["useful_state_count"],
        })
        print("PDE:", {"pde_stability": round(best.metrics["pde_stability"], 4)})
        print("Instr count:", best.metrics["instr_count"])
        print("Valid execution rate:", round(valid_rate, 4))
        print("Program:")
        print(program_to_str(best.program))
