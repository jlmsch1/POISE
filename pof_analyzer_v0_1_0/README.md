# POISE v1.6

**POISE** = **Product Operator and Integrated Sequence Engine**

## New in v1.6
- compact trig formatting:
  - `compact_trig=True` gives `Iy*c(pi*J*tau)` style output
- stable operator-first formatting preserved
- simple COSY-fragment helpers:
  - `classify_cosy_precursors(...)`
  - `diagonal_precursors(...)`
  - `cross_precursors(...)`
  - `other_precursors(...)`

## Scope note
The COSY helpers are intentionally heuristic and teaching-first.
They classify common precursor operator families rather than attempting a full coherence-pathway engine.
