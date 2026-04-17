from .core import Expression
OBSERVABLE_I = {"Ix", "Iy", "2IxSz", "2IySz"}
OBSERVABLE_S = {"Sx", "Sy", "2IzSx", "2IzSy"}
def observable(expr: Expression, detect_on="I") -> Expression:
    if detect_on == "I":
        return expr.keep_only(OBSERVABLE_I)
    if detect_on == "S":
        return expr.keep_only(OBSERVABLE_S)
    raise ValueError("detect_on must be 'I' or 'S'")
