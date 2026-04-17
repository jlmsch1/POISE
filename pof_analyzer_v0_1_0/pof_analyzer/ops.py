SPIN_ORDER = {"I": 0, "S": 1, "H": 2, "C": 3, "N": 4}

def parse_op(op: str):
    prefactor_label = 1
    body = op
    if body and body[0].isdigit():
        i = 0
        while i < len(body) and body[i].isdigit():
            i += 1
        prefactor_label = int(body[:i]); body = body[i:]
    factors = []
    i = 0
    while i < len(body):
        factors.append((body[i], body[i+1]))
        i += 2
    return prefactor_label, factors

def build_op(prefactor_label: int, factors):
    factors = sorted(factors, key=lambda x: SPIN_ORDER.get(x[0], 999))
    body = "".join(f"{spin}{axis}" for spin, axis in factors)
    return f"{prefactor_label}{body}" if prefactor_label != 1 else body
