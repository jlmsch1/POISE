import sympy as sp
from .core import Expression, Term
from .ops import parse_op, build_op

t, J = sp.symbols("t J", real=True)

def evolve_J(expr: Expression, time=t, coupling=J):
    if coupling is None:
        coupling = J
    phi = sp.pi * coupling * time
    c = sp.cos(phi); s = sp.sin(phi)
    rules = {
        "Ix": [Term(c, "Ix"), Term(s, "2IySz")],
        "Iy": [Term(c, "Iy"), Term(-s, "2IxSz")],
        "Sx": [Term(c, "Sx"), Term(s, "2IzSy")],
        "Sy": [Term(c, "Sy"), Term(-s, "2IzSx")],
        "2IxSz": [Term(c, "2IxSz"), Term(s, "Iy")],
        "2IySz": [Term(c, "2IySz"), Term(-s, "Ix")],
        "2IzSx": [Term(c, "2IzSx"), Term(s, "Sy")],
        "2IzSy": [Term(c, "2IzSy"), Term(-s, "Sx")],
        "Iz": [Term(1, "Iz")],
        "Sz": [Term(1, "Sz")],
        "2IzSz": [Term(1, "2IzSz")],
        "2IxSx": [Term(1, "2IxSx")],
        "2IxSy": [Term(1, "2IxSy")],
        "2IySx": [Term(1, "2IySx")],
        "2IySy": [Term(1, "2IySy")],
    }
    new_terms = []
    for term in expr.terms:
        if term.op not in rules:
            raise ValueError(f"No J-evolution rule implemented yet for {term.op}")
        for mapped in rules[term.op]:
            new_terms.append(Term(term.coeff * mapped.coeff, mapped.op))
    out = Expression(new_terms, list(expr.history)).simplify()
    out.add_history(f"After J evolution for {time}: {out}")
    return out

def evolve_cs(expr: Expression, spin: str, time=t, omega=None):
    if omega is None:
        omega = sp.symbols(f"omega_{spin}", real=True)
    phi = omega * time
    c = sp.cos(phi); s = sp.sin(phi)
    new_terms = []
    for term in expr.terms:
        prefactor_label, factors = parse_op(term.op)
        found = False
        for idx, (spn, axis) in enumerate(factors):
            if spn == spin:
                found = True
                if axis == "x":
                    fac1 = list(factors); fac1[idx] = (spn, "x")
                    fac2 = list(factors); fac2[idx] = (spn, "y")
                    new_terms.append(Term(term.coeff * c, build_op(prefactor_label, fac1)))
                    new_terms.append(Term(term.coeff * s, build_op(prefactor_label, fac2)))
                elif axis == "y":
                    fac1 = list(factors); fac1[idx] = (spn, "y")
                    fac2 = list(factors); fac2[idx] = (spn, "x")
                    new_terms.append(Term(term.coeff * c, build_op(prefactor_label, fac1)))
                    new_terms.append(Term(term.coeff * (-s), build_op(prefactor_label, fac2)))
                elif axis == "z":
                    new_terms.append(term)
                else:
                    raise ValueError(f"Unsupported axis: {axis}")
                break
        if not found:
            new_terms.append(term)
    out = Expression(new_terms, list(expr.history)).simplify()
    out.add_history(f"After CS evolution on {spin} for {time}: {out}")
    return out
