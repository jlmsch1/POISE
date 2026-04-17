from .core import Expression, Term

# Teaching-first, heuristic COSY precursor classification.
# Diagonal-like precursors: single-spin transverse terms.
# Cross-peak-like precursors: antiphase terms with one longitudinal and one transverse factor.
DIAGONAL_OPS = {"Ix", "Iy", "Sx", "Sy"}
CROSS_OPS = {"2IxSz", "2IySz", "2IzSx", "2IzSy"}

def diagonal_precursors(expr: Expression) -> Expression:
    return expr.keep_only(DIAGONAL_OPS)

def cross_precursors(expr: Expression) -> Expression:
    return expr.keep_only(CROSS_OPS)

def other_precursors(expr: Expression) -> Expression:
    keep = DIAGONAL_OPS | CROSS_OPS
    return Expression([term for term in expr.terms if term.op not in keep], list(expr.history)).simplify()

def classify_cosy_precursors(expr: Expression):
    return {
        "diagonal": diagonal_precursors(expr),
        "cross": cross_precursors(expr),
        "other": other_precursors(expr),
    }
