"""Family 276: numerical one-use GAD Holevo optimization, in bits.

The scalar objective predates the 2026 OpenAI manuscript. Its interpretation
as unrestricted classical capacity depends on that manuscript's additivity
claim. This module performs floating-point calculations, not proof checking.
nu is the stationary EXCITED-state population, not the ground-state weight.
"""

from dataclasses import asdict, dataclass
import math


def _unit(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number in [0, 1]") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def binary_entropy(p: float) -> float:
    """Binary entropy in bits, with stable endpoint handling."""
    p = _unit(p, "p")
    if p == 0.0 or p == 1.0:
        return 0.0
    return -(p * math.log(p) + (1.0 - p) * math.log1p(-p)) / math.log(2.0)


def output_entropy(p: float, gamma: float, nu: float) -> float:
    """Entropy of a pure signal's output, in bits (source eq. 1.8)."""
    p, gamma, nu = _unit(p, "p"), _unit(gamma, "gamma"), _unit(nu, "nu")
    determinant = math.fsum((gamma * nu * (1.0 - nu),
                             gamma * (1.0 - gamma) * (p - nu) ** 2))
    # For valid parameters the determinant lies in [0, 1/4]. The clamp
    # removes roundoff at a maximally mixed state, not invalid user input.
    determinant = min(0.25, max(0.0, determinant))
    root = math.sqrt(max(0.0, 1.0 - 4.0 * determinant))
    # Avoid subtractive cancellation in (1-root)/2 near pure outputs.
    small_eigenvalue = 2.0 * determinant / (1.0 + root)
    return binary_entropy(small_eigenvalue)


def objective(p: float, gamma: float, nu: float) -> float:
    """Holevo information of the equiprobable opposite-phase signal pair."""
    p, gamma, nu = _unit(p, "p"), _unit(gamma, "gamma"), _unit(nu, "nu")
    if gamma == 1.0 or p == 0.0 or p == 1.0:
        return 0.0
    population = (1.0 - gamma) * p + gamma * nu
    value = binary_entropy(population) - output_entropy(p, gamma, nu)
    return max(0.0, value)  # Holevo information is nonnegative.


@dataclass(frozen=True)
class Result:
    gamma: float
    nu: float
    p: float
    capacity_bits: float
    bracket_low: float
    bracket_high: float
    evaluations: int

    def as_dict(self) -> dict:
        result = asdict(self)
        result["quantity"] = "one_use_holevo_bits; classical_capacity_if_source_theorem_holds"
        result["method"] = "floating_point_concave_scalar_optimization"
        result["signal_plus"] = [math.sqrt(1.0 - self.p), math.sqrt(self.p)]
        result["signal_minus"] = [math.sqrt(1.0 - self.p), -math.sqrt(self.p)]
        result["signal_probabilities"] = [0.5, 0.5]
        result["bracket_note"] = "Numerical search interval; not a certified error bound."
        return result


def optimize(gamma: float, nu: float, tolerance: float = 1e-10) -> Result:
    """Maximize source eq. 1.7 using concavity and golden-section search.

    tolerance controls the search interval in p, not a certified bit error.
    Endpoints and the unital midpoint have explicit formulas. Thermal
    reflection makes the p <-> 1-p convention exact at the API level.
    """
    gamma, nu = _unit(gamma, "gamma"), _unit(nu, "nu")
    try:
        tolerance = float(tolerance)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("tolerance must be finite and in [1e-14, 0.1]") from exc
    if not math.isfinite(tolerance) or not 1e-14 <= tolerance <= 0.1:
        raise ValueError("tolerance must be finite and in [1e-14, 0.1]")
    if gamma == 0.0 or gamma == 1.0 or nu == 0.5:
        value = 1.0 if gamma == 0.0 else (0.0 if gamma == 1.0 else objective(0.5, gamma, nu))
        return Result(gamma, nu, 0.5, value, 0.5, 0.5, 1)
    if nu > 0.5:
        reflected = optimize(gamma, 1.0 - nu, tolerance)
        return Result(gamma, nu, 1.0 - reflected.p, reflected.capacity_bits,
                      1.0 - reflected.bracket_high, 1.0 - reflected.bracket_low,
                      reflected.evaluations)

    low, high = 0.0, 1.0
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    left, right = high - ratio * (high - low), low + ratio * (high - low)
    left_value, right_value = objective(left, gamma, nu), objective(right, gamma, nu)
    evaluations = 2
    while high - low > tolerance:
        if left_value < right_value:
            low, left, left_value = left, right, right_value
            right = low + ratio * (high - low)
            right_value = objective(right, gamma, nu)
        else:
            high, right, right_value = right, left, left_value
            left = high - ratio * (high - low)
            left_value = objective(left, gamma, nu)
        evaluations += 1
    p = (low + high) / 2.0
    return Result(gamma, nu, p, objective(p, gamma, nu), low, high, evaluations + 1)
