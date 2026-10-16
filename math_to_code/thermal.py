"""Quantitative thermal entropy-gap bound from the source mixture proof.

Entropy and the returned bound are in nats. The trace norm of XX*-YY* is
supplied by the caller; no matrix library is needed for this scalar API.
See docs/thermal-stability-derivation.md for the derivation.
"""

import math
from collections.abc import Sequence
from fractions import Fraction


def gap_lower_bound(coefficients: Sequence[float], gram_trace_norm: float) -> float:
    """Return beta*eta*||XX*-YY*||_1²/(2*U0*U1), in nats.

    coefficients are (alpha,beta,eta,delta), nonnegative and summing to one,
    with alpha*delta >= beta*eta. X and Y each have Hilbert-Schmidt norm 1,
    so their Gram trace distance lies in [0,2]. A zero row gives bound 0.
    Coefficient feasibility is checked exactly on the accepted numbers'
    decimal representations, including very small row weights.
    """
    try:
        values = tuple(float(value) for value in coefficients)
        distance = float(gram_trace_norm)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("finite coefficients and trace norm are required") from exc
    if len(values) != 4 or not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("four finite nonnegative coefficients are required")
    if abs(math.fsum(values) - 1.0) > 1e-12:
        raise ValueError("coefficients must sum to one")
    if not math.isfinite(distance) or not 0 <= distance <= 2.0 + 1e-12:
        raise ValueError("Gram trace norm must be finite and in [0,2]")
    a, beta, eta, delta = values
    if Fraction(str(a)) * Fraction(str(delta)) < Fraction(str(beta)) * Fraction(str(eta)):
        raise ValueError("alpha*delta must be at least beta*eta")
    u0, u1 = a + beta, eta + delta
    if beta == 0 or eta == 0 or u0 == 0 or u1 == 0:
        return 0.0
    # Ratios stay in [0,1], avoiding products of subnormal row weights.
    return 0.5 * (beta / u0) * (eta / u1) * distance * distance
