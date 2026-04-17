from typing import Dict, List, Tuple
import sympy as sp
from .core import Expression, Term
from .ops import parse_op, build_op

ROTATIONS: Dict[str, Dict[str, List[Tuple[int, str]]]] = {
    "90x":   {"x": [(1, "x")],  "y": [(1, "z")],   "z": [(-1, "y")]},
    "90-x":  {"x": [(1, "x")],  "y": [(-1, "z")],  "z": [(1, "y")]},
    "90y":   {"x": [(-1, "z")], "y": [(1, "y")],   "z": [(1, "x")]},
    "90-y":  {"x": [(1, "z")],  "y": [(1, "y")],   "z": [(-1, "x")]},
    "180x":  {"x": [(1, "x")],  "y": [(-1, "y")],  "z": [(-1, "z")]},
    "180-x": {"x": [(1, "x")],  "y": [(-1, "y")],  "z": [(-1, "z")]},
    "180y":  {"x": [(-1, "x")], "y": [(1, "y")],   "z": [(-1, "z")]},
    "180-y": {"x": [(-1, "x")], "y": [(1, "y")],   "z": [(-1, "z")]},
}

def _normalize_phase(phase: str) -> str:
    if phase in ("+x", "+y"):
        return phase[1:]
    return phase

def pulse(expr: Expression, angle: int, phase: str, spins):
    target_spins = {spins} if isinstance(spins, str) else set(spins)
    key = f"{angle}{_normalize_phase(phase)}"
    if key not in ROTATIONS:
        raise ValueError(f"Unsupported pulse: {key}")
    mapping = ROTATIONS[key]
    new_terms = []
    for term in expr.terms:
        coeff = term.coeff
        prefactor_label, factors = parse_op(term.op)
        current = [(coeff, [])]
        for spin, axis in factors:
            rotated = mapping[axis] if spin in target_spins else [(1, axis)]
            nxt = []
            for coeff_old, fac_old in current:
                for coeff_rot, axis_rot in rotated:
                    nxt.append((coeff_old * coeff_rot, fac_old + [(spin, axis_rot)]))
            current = nxt
        for coeff_new, fac_new in current:
            new_terms.append(Term(coeff_new, build_op(prefactor_label, fac_new)))
    out = Expression(new_terms, list(expr.history)).simplify()
    out.add_history(f"After {angle}{phase} on {','.join(sorted(target_spins))}: {out}")
    return out

def _rotation_formula(axis: str, angle, component: str):
    a = sp.sympify(angle)
    c = sp.cos(a); s = sp.sin(a)
    if axis == "x":
        if component == "x": return [(1, "x")]
        if component == "y": return [(c, "y"), (s, "z")]
        if component == "z": return [(c, "z"), (-s, "y")]
    if axis == "-x":
        if component == "x": return [(1, "x")]
        if component == "y": return [(c, "y"), (-s, "z")]
        if component == "z": return [(c, "z"), (s, "y")]
    if axis == "y":
        if component == "x": return [(c, "x"), (-s, "z")]
        if component == "y": return [(1, "y")]
        if component == "z": return [(c, "z"), (s, "x")]
    if axis == "-y":
        if component == "x": return [(c, "x"), (s, "z")]
        if component == "y": return [(1, "y")]
        if component == "z": return [(c, "z"), (-s, "x")]
    raise ValueError(f"Unsupported exact pulse axis: {axis}")

def pulse_exact(expr: Expression, angle, phase: str, spins):
    axis = _normalize_phase(phase)
    target_spins = {spins} if isinstance(spins, str) else set(spins)
    new_terms = []
    for term in expr.terms:
        coeff = term.coeff
        prefactor_label, factors = parse_op(term.op)
        current = [(coeff, [])]
        for spin, comp in factors:
            rotated = _rotation_formula(axis, angle, comp) if spin in target_spins else [(1, comp)]
            nxt = []
            for coeff_old, fac_old in current:
                for coeff_rot, comp_rot in rotated:
                    nxt.append((coeff_old * coeff_rot, fac_old + [(spin, comp_rot)]))
            current = nxt
        for coeff_new, fac_new in current:
            new_terms.append(Term(coeff_new, build_op(prefactor_label, fac_new)))
    out = Expression(new_terms, list(expr.history)).simplify()
    out.add_history(f"After exact {angle} about {phase} on {','.join(sorted(target_spins))}: {out}")
    return out
