from dataclasses import dataclass
from typing import Dict
import sympy as sp
from .core import Expression, Term

@dataclass
class DifferenceResult:
    a: Expression
    b: Expression
    only_in_a: Expression
    only_in_b: Expression
    changed_in_a: Expression
    changed_in_b: Expression
    difference: Expression

    def summary(self, style: str = "canonical", compact_trig: bool = False) -> str:
        parts = [
            f"A: {self.a.to_string(style=style, compact_trig=compact_trig)}",
            f"B: {self.b.to_string(style=style, compact_trig=compact_trig)}",
            f"Only in A: {self.only_in_a.to_string(style=style, compact_trig=compact_trig)}",
            f"Only in B: {self.only_in_b.to_string(style=style, compact_trig=compact_trig)}",
            f"Changed terms in A: {self.changed_in_a.to_string(style=style, compact_trig=compact_trig)}",
            f"Changed terms in B: {self.changed_in_b.to_string(style=style, compact_trig=compact_trig)}",
            f"A - B: {self.difference.to_string(style=style, compact_trig=compact_trig)}",
        ]
        return "\n".join(parts)

def _expr_from_map(coeff_map: Dict[str, sp.Expr]) -> Expression:
    return Expression([Term(coeff, op) for op, coeff in coeff_map.items() if sp.simplify(coeff) != 0]).simplify()

def difference(a: Expression, b: Expression) -> DifferenceResult:
    a_map = a.coeff_map(); b_map = b.coeff_map()
    only_a = {}; only_b = {}; changed_a = {}; changed_b = {}
    for op in sorted(set(a_map) | set(b_map)):
        if op in a_map and op not in b_map:
            only_a[op] = a_map[op]
        elif op in b_map and op not in a_map:
            only_b[op] = b_map[op]
        elif sp.simplify(a_map[op] - b_map[op]) != 0:
            changed_a[op] = a_map[op]; changed_b[op] = b_map[op]
    return DifferenceResult(
        a=a.copy().simplify(), b=b.copy().simplify(),
        only_in_a=_expr_from_map(only_a),
        only_in_b=_expr_from_map(only_b),
        changed_in_a=_expr_from_map(changed_a),
        changed_in_b=_expr_from_map(changed_b),
        difference=(a - b).simplify(),
    )
