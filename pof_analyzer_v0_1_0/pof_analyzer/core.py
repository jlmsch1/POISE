from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional
import re
import sympy as sp

@dataclass(frozen=True)
class Term:
    coeff: sp.Expr
    op: str

def _compactify_trig_text(text: str) -> str:
    text = re.sub(r'cos\(([^()]*)\)', r'c(\1)', text)
    text = re.sub(r'sin\(([^()]*)\)', r's(\1)', text)
    return text

def _compactify_trig_latex(text: str) -> str:
    text = text.replace(r"\cos", "c").replace(r"\sin", "s")
    return text

class Expression:
    def __init__(self, terms: Optional[List[Term]] = None, history: Optional[List[str]] = None):
        self.terms = terms or []
        self.history = history or []

    def copy(self):
        return Expression(list(self.terms), list(self.history))

    def simplify(self):
        combined: Dict[str, sp.Expr] = {}
        order: List[str] = []
        for term in self.terms:
            if term.op not in combined:
                combined[term.op] = 0
                order.append(term.op)
            combined[term.op] += sp.sympify(term.coeff)
        new_terms = []
        for op in order:
            coeff = sp.trigsimp(sp.simplify(combined[op]))
            if coeff != 0:
                new_terms.append(Term(coeff, op))
        self.terms = new_terms
        return self

    def add_history(self, line: str):
        self.history.append(line)
        return self

    def subs(self, *args, **kwargs):
        return Expression(
            [Term(sp.trigsimp(sp.simplify(term.coeff.subs(*args, **kwargs))), term.op) for term in self.terms],
            list(self.history),
        ).simplify()

    def keep_only(self, allowed_ops: Iterable[str]):
        allowed = set(allowed_ops)
        return Expression([term for term in self.terms if term.op in allowed], list(self.history)).simplify()

    def scaled(self, factor):
        factor = sp.sympify(factor)
        return Expression([Term(sp.simplify(factor * term.coeff), term.op) for term in self.terms], list(self.history)).simplify()

    def __add__(self, other):
        return Expression(list(self.terms) + list(other.terms), list(self.history)).simplify()

    def __sub__(self, other):
        return Expression(list(self.terms) + [Term(-t.coeff, t.op) for t in other.terms], list(self.history)).simplify()

    def coeff_map(self):
        tmp = self.copy().simplify()
        return {term.op: sp.simplify(term.coeff) for term in tmp.terms}

    def _display_parts(self, term, style="canonical"):
        coeff = sp.simplify(term.coeff)
        op = term.op
        display_op = op
        display_multiplier = 1
        if style == "expanded":
            m = re.match(r"^(\d+)([A-Z].*)$", op)
            if m:
                display_multiplier = int(m.group(1))
                display_op = m.group(2)
        return coeff, display_op, display_multiplier

    def _term_to_string(self, term, style="canonical", compact_trig=False):
        coeff, display_op, display_multiplier = self._display_parts(term, style=style)
        coeff = sp.simplify(coeff * display_multiplier)

        if coeff == 1:
            out = f"{display_op}"
        elif coeff == -1:
            out = f"-{display_op}"
        else:
            sign = "-" if coeff.could_extract_minus_sign() else ""
            mag = -coeff if sign else coeff
            out = f"{sign}{display_op}*{mag}"

        return _compactify_trig_text(out) if compact_trig else out

    def to_string(self, style="canonical", compact_trig=False):
        simplified = self.copy().simplify()
        if not simplified.terms:
            return "0"
        s = " + ".join(self._term_to_string(term, style=style, compact_trig=compact_trig) for term in simplified.terms)
        s = s.replace("+ -", "- ")
        return _compactify_trig_text(s) if compact_trig else s

    def _op_to_latex(self, op, style="canonical"):
        multiplier = ""
        body = op
        m = re.match(r"^(\d+)([A-Z].*)$", op)
        if m:
            leading = m.group(1)
            body = m.group(2)
            if style == "canonical":
                multiplier = leading
        factors = []
        i = 0
        while i < len(body):
            spin = body[i]
            axis = body[i + 1]
            factors.append(f"{spin}_{{{axis}}}")
            i += 2
        return f"{multiplier}{''.join(factors)}"

    def _term_to_latex(self, term, style="canonical", compact_trig=False):
        coeff, _, display_multiplier = self._display_parts(term, style=style)
        coeff = sp.simplify(coeff * display_multiplier)
        op_ltx = self._op_to_latex(term.op, style=style)
        if coeff == 1:
            out = op_ltx
        elif coeff == -1:
            out = "-" + op_ltx
        else:
            sign = "-" if coeff.could_extract_minus_sign() else ""
            mag = -coeff if sign else coeff
            out = sign + op_ltx + r"\," + sp.latex(mag)
        return _compactify_trig_latex(out) if compact_trig else out

    def to_latex(self, style="canonical", compact_trig=False):
        simplified = self.copy().simplify()
        if not simplified.terms:
            return "0"
        parts = []
        for term in simplified.terms:
            piece = self._term_to_latex(term, style=style, compact_trig=compact_trig)
            if piece.startswith("-"):
                parts.append(piece)
            else:
                if parts:
                    parts.append("+ " + piece)
                else:
                    parts.append(piece)
        out = " ".join(parts)
        return _compactify_trig_latex(out) if compact_trig else out

    def __str__(self):
        return self.to_string(style="canonical")

def Op(label: str):
    return Expression([Term(1, label)], history=[f"Start: {label}"])

def Ix(): return Op("Ix")
def Iy(): return Op("Iy")
def Iz(): return Op("Iz")
def Sx(): return Op("Sx")
def Sy(): return Op("Sy")
def Sz(): return Op("Sz")
def Hx(): return Op("Hx")
def Hy(): return Op("Hy")
def Hz(): return Op("Hz")
