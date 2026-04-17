from dataclasses import dataclass
from typing import Dict, List, Optional
import sympy as sp
from .core import Expression, Term
from .diff import difference
from .pulses import pulse, pulse_exact
from .evolution import evolve_J, evolve_cs

_RECEIVER_FACTORS = {"x": 1, "+x": 1, "-x": -1, "y": 1, "+y": 1, "-y": -1}

@dataclass
class ScanResult:
    name: str
    expr: Expression
    def summary(self, style: str = "canonical", compact_trig: bool = False) -> str:
        return f"{self.name}: {self.expr.to_string(style=style, compact_trig=compact_trig)}"

@dataclass
class PhaseCycleResult:
    scans: List[ScanResult]
    summed: Expression
    surviving_terms: Expression
    canceled_terms: Expression
    flipped_terms: Expression
    def summary(self, style: str = "canonical", compact_trig: bool = False) -> str:
        lines = ["Scan outputs:"]
        for scan in self.scans:
            lines.append(f"  {scan.summary(style=style, compact_trig=compact_trig)}")
        lines += [
            f"Sum: {self.summed.to_string(style=style, compact_trig=compact_trig)}",
            f"Surviving terms: {self.surviving_terms.to_string(style=style, compact_trig=compact_trig)}",
            f"Canceled terms: {self.canceled_terms.to_string(style=style, compact_trig=compact_trig)}",
            f"Sign-flipped terms: {self.flipped_terms.to_string(style=style, compact_trig=compact_trig)}",
        ]
        return "\n".join(lines)

def apply_receiver(expr: Expression, receiver: Optional[str]) -> Expression:
    out = expr.copy()
    if receiver is None:
        return out.simplify()
    out = out.scaled(_RECEIVER_FACTORS[receiver])
    out.add_history(f"After receiver {receiver}: {out}")
    return out.simplify()

def run_sequence(start: Expression, steps: List[Dict]) -> Expression:
    out = start.copy()
    for step in steps:
        kind = step["type"]
        if kind == "pulse":
            mode = step.get("mode", "ideal")
            if mode == "ideal":
                out = pulse(out, angle=step["angle"], phase=step["phase"], spins=step["spins"])
            elif mode == "exact":
                out = pulse_exact(out, angle=step["angle"], phase=step["phase"], spins=step["spins"])
            else:
                raise ValueError(f"Unsupported pulse mode: {mode}")
        elif kind == "J":
            out = evolve_J(out, time=step["time"], coupling=step.get("coupling"))
        elif kind in ("CS", "shift", "chemical_shift"):
            out = evolve_cs(out, spin=step["spin"], time=step["time"], omega=step.get("omega"))
        else:
            raise ValueError(f"Unsupported step type: {kind}")
    return out.simplify()

def run_scan(start: Expression, steps: List[Dict], receiver: Optional[str] = None, name: Optional[str] = None) -> ScanResult:
    expr = apply_receiver(run_sequence(start, steps), receiver)
    return ScanResult(name=name or "scan", expr=expr)

def _collect_features(scan_exprs: List[Expression]):
    coeff_maps = [expr.coeff_map() for expr in scan_exprs]
    all_ops = sorted(set().union(*[set(m.keys()) for m in coeff_maps])) if coeff_maps else []
    surviving = {}; canceled = {}; flipped = {}
    for op in all_ops:
        coeffs = [sp.simplify(m.get(op, 0)) for m in coeff_maps]
        total = sp.simplify(sum(coeffs))
        present_all = all(sp.simplify(c) != 0 for c in coeffs)
        same_all = present_all and all(sp.simplify(c - coeffs[0]) == 0 for c in coeffs[1:])
        if same_all and total != 0:
            surviving[op] = total
        if total == 0 and any(sp.simplify(c) != 0 for c in coeffs):
            canceled[op] = next(c for c in coeffs if sp.simplify(c) != 0)
        if present_all and len(coeffs) >= 2:
            ref = coeffs[0]
            if sp.simplify(ref) != 0:
                signs = []
                ok = True
                for c in coeffs:
                    if sp.simplify(c - ref) == 0:
                        signs.append(1)
                    elif sp.simplify(c + ref) == 0:
                        signs.append(-1)
                    else:
                        ok = False; break
                if ok and any(s == -1 for s in signs):
                    flipped[op] = ref
    return surviving, canceled, flipped

def phase_cycle(scans: List[ScanResult]) -> PhaseCycleResult:
    total = Expression([])
    for scan in scans:
        total = (total + scan.expr).simplify()
    total.add_history(f"Phase-cycle sum: {total}")
    surviving, canceled, flipped = _collect_features([scan.expr for scan in scans])
    return PhaseCycleResult(
        scans=scans,
        summed=total,
        surviving_terms=Expression([Term(c, op) for op, c in surviving.items()]).simplify(),
        canceled_terms=Expression([Term(c, op) for op, c in canceled.items()]).simplify(),
        flipped_terms=Expression([Term(c, op) for op, c in flipped.items()]).simplify(),
    )

def phase_cycle_difference(a_scans: List[ScanResult], b_scans: List[ScanResult]):
    return difference(phase_cycle(a_scans).summed, phase_cycle(b_scans).summed)
