"""Independent spectra and high-precision references for the thermal lemma.

The factor path uses the two Gram factors in source eq. (thermal-factors),
then singular values of their weighted concatenation. The high-precision
path builds the block state directly and uses mpmath's Hermitian eigensolver.
All entropies are in nats. These numerical references do not prove a theorem.

Matrices may be arrays/nested lists or dictionaries with ``real`` and ``imag``
arrays. Decimal strings in such dictionaries are preserved by mpmath. X and Y
are explicitly normalized in the precision of each calculation. Coefficients
must already sum to one within 1e-12; a reported common normalization removes
only their decimal reconstruction error and preserves the determinant's sign.
"""

from __future__ import annotations

from fractions import Fraction
import math
from collections.abc import Mapping

import numpy as np


def _exact_coefficients(coeff):
    """Interpret saved decimal/rational tokens exactly before testing feasibility."""
    try:
        values = [Fraction(str(value)) for value in coeff]
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValueError("four finite nonnegative coefficients are required") from exc
    if len(values) != 4 or min(values) < 0:
        raise ValueError("four finite nonnegative coefficients are required")
    total = sum(values)
    if abs(total - 1) > Fraction("1e-12"):
        raise ValueError("coefficient sum differs materially from one")
    normalized = [value / total for value in values]
    a, b, eta, d = normalized
    determinant = a * d - b * eta
    if determinant < 0:
        raise ValueError("negative exact coefficient determinant; no feasibility repair performed")
    return normalized, total, determinant


def _parts(value):
    if isinstance(value, Mapping):
        if "real" not in value or "imag" not in value:
            raise ValueError("serialized matrices require real and imag arrays")
        real = np.asarray(value["real"], dtype=object)
        imag = np.asarray(value["imag"], dtype=object)
    else:
        array = np.asarray(value)
        if np.iscomplexobj(array):
            real, imag = array.real.astype(object), array.imag.astype(object)
        else:
            real = array.astype(object)
            imag = np.zeros(array.shape, dtype=object)
    if real.ndim != 2 or real.shape != imag.shape or min(real.shape, default=0) == 0:
        raise ValueError("X and Y must be nonempty rectangular matrices")
    return real, imag


def _float_inputs(x, y, coeff):
    arrays, original_norms = [], []
    for value in (x, y):
        real, imag = _parts(value)
        convert = np.vectorize(lambda entry: float(Fraction(str(entry))), otypes=[float])
        array = convert(real) + 1j * convert(imag)
        if not np.isfinite(array).all():
            raise ValueError("matrix entries must be finite")
        norm = float(np.linalg.norm(array))
        if not math.isfinite(norm) or norm == 0.0:
            raise ValueError("each matrix must have finite nonzero Hilbert-Schmidt norm")
        original_norms.append(norm)
        arrays.append(array / norm)
    if arrays[0].shape != arrays[1].shape:
        raise ValueError("X and Y must have the same rectangular shape")
    exact_coefficients, exact_sum, exact_determinant = _exact_coefficients(coeff)
    coefficients = np.asarray([float(value) for value in exact_coefficients])
    original_sum = exact_sum
    determinant = float(exact_determinant)
    return arrays[0], arrays[1], coefficients, determinant, original_norms, original_sum


def _block_state(x, y, coeff, k):
    a, b, eta, d = coeff
    xx, yy, xy = x @ x.conj().T, y @ y.conj().T, x @ y.conj().T
    return np.block([[a * xx + b * yy, k * xy], [k * xy.conj().T, eta * xx + d * yy]])


def _thermal_factor(x, y, coeff, determinant):
    """Return F with T=FF*, using the source's endpoint mixture."""
    a, b, eta, d = coeff
    u0, u1 = a + b, eta + d
    u = b * u1 + eta * u0
    zero = np.zeros_like(x)
    if u > 0.0:
        # A positive u implies both row sums are positive.
        w1, w2 = b * u1 / u, eta * u0 / u
        m1 = np.block([[math.sqrt(determinant / u1) * x, math.sqrt(u / u1) * y], [math.sqrt(u1) * y, zero]])
        m2 = np.block([[math.sqrt(u0) * x, zero], [math.sqrt(determinant / u0) * y, math.sqrt(u / u0) * x]])
        factor = np.hstack((math.sqrt(w1) * m1, math.sqrt(w2) * m2))
        return factor, "weighted_source_endpoint_factors", [float(w1), float(w2)]
    if u0 > 0.0 and u1 > 0.0:
        # Here beta=eta=0 and the shared column index retains XY*.
        return np.vstack((math.sqrt(a) * x, math.sqrt(d) * y)), "u_zero_shared_column_factor", [1.0]
    factor = np.block([[math.sqrt(a) * x, math.sqrt(b) * y, zero, zero], [zero, zero, math.sqrt(eta) * x, math.sqrt(d) * y]])
    return factor, "vanishing_row_diagonal_factors", [1.0]


def _spectrum_entropy(values, tolerance=2e-12):
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all() or float(values.min()) < -tolerance:
        raise ValueError("material negative or nonfinite spectrum; no PSD repair performed")
    positive = values[values > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def _padded_singular_spectrum(matrix, rows):
    values = np.linalg.svd(matrix, compute_uv=False) ** 2
    if values.size < rows:
        values = np.pad(values, (0, rows - values.size))
    return np.sort(values)


def singular_residual(x, y, coeff) -> dict:
    """Compare direct eigenvalues with source-factor singular-value spectra.

    Nonzero input matrices are explicitly HS-normalized. An infeasible
    coefficient determinant is rejected, rather than clipped to zero.
    """
    x, y, coefficients, determinant, norms, coefficient_sum = _float_inputs(x, y, coeff)
    a, b, eta, d = coefficients
    k = math.sqrt(determinant)
    full = _block_state(x, y, coefficients, k)
    factor, branch, weights = _thermal_factor(x, y, coefficients, determinant)
    scalar_x = np.ones((1, 1), dtype=complex)
    scalar = _block_state(scalar_x, scalar_x, coefficients, k)
    scalar_factor, _, _ = _thermal_factor(scalar_x, scalar_x, coefficients, determinant)
    direct_spectra = [np.linalg.eigvalsh(matrix) for matrix in (full, x @ x.conj().T, y @ y.conj().T, scalar)]
    singular_spectra = [_padded_singular_spectrum(matrix, rows) for matrix, rows in ((factor, 2 * x.shape[0]), (x, x.shape[0]), (y, y.shape[0]), (scalar_factor, 2))]
    direct_entropies = [_spectrum_entropy(values) for values in direct_spectra]
    singular_entropies = [_spectrum_entropy(values) for values in singular_spectra]
    def residual(entropies):
        return entropies[0] - (a + eta) * entropies[1] - (b + d) * entropies[2] - entropies[3]
    direct, singular = residual(direct_entropies), residual(singular_entropies)
    reconstructed = factor @ factor.conj().T
    return {
        "entropy_units": "nats",
        "direct_residual_nats": float(direct),
        "singular_residual_nats": float(singular),
        "residual_nats": float(singular),
        "residual_difference_nats": float(singular - direct),
        "reconstruction_max_abs_error": float(np.max(np.abs(reconstructed - full))),
        "maximum_spectrum_abs_difference": float(max(np.max(np.abs(left - right)) for left, right in zip(direct_spectra, singular_spectra))),
        "direct_full_spectrum": direct_spectra[0].tolist(),
        "factor_full_spectrum": singular_spectra[0].tolist(),
        "minimum_direct_eigenvalue": float(min(values.min() for values in direct_spectra)),
        "maximum_trace_error": float(max(abs(np.sum(values) - 1.0) for values in direct_spectra)),
        "factor_branch": branch,
        "mixture_weights": weights,
        "original_hilbert_schmidt_norms": norms,
        "original_coefficient_sum": float(coefficient_sum),
        "original_coefficient_sum_exact_rational": str(coefficient_sum),
        "coefficient_common_normalization_applied": coefficient_sum != 1.0,
        "coefficients_alpha_beta_eta_delta": coefficients.tolist(),
        "feasibility": {"accepted": True, "determinant": determinant, "K": k, "negative_determinant_repair": False},
        "limitation": "Double precision numerical consistency only; no certified enclosure or proof.",
    }


def reference_residual(x, y, coeff, dps=80) -> dict:
    """Compute direct thermal residual with independently normalized mpmath data.

    Exact decimal strings and integers are read without a binary64 round trip.
    Float inputs are interpreted as their Python decimal repr, not as unknown
    pre-rounding values. Tiny negative eigensolver roundoff is reported and
    excluded from entropy only after an explicit precision-scaled PSD check.
    """
    import mpmath as mp

    if isinstance(dps, bool) or not isinstance(dps, int) or not 30 <= dps <= 1000:
        raise ValueError("dps must be an integer between 30 and 1000")
    with mp.workdps(dps):
        def number(value):
            # str avoids silently constructing an mpf from a binary64 value.
            if isinstance(value, np.generic):
                value = value.item()
            token = str(value)
            if "/" in token:
                rational = Fraction(token)
                result = mp.mpf(rational.numerator) / rational.denominator
            else:
                result = mp.mpf(token)
            if not mp.isfinite(result):
                raise ValueError("all entries and coefficients must be finite")
            return result
        def decimal(value):
            return mp.nstr(value, n=dps)
        matrices, norms = [], []
        for value in (x, y):
            real, imag = _parts(value)
            matrix = mp.matrix([[mp.mpc(number(real[i, j]), number(imag[i, j])) for j in range(real.shape[1])] for i in range(real.shape[0])])
            norm = mp.sqrt(mp.fsum(abs(value) ** 2 for value in matrix))
            if norm == 0:
                raise ValueError("each input matrix must have nonzero Hilbert-Schmidt norm")
            matrices.append(matrix / norm)
            norms.append(norm)
        x, y = matrices
        if x.rows != y.rows or x.cols != y.cols:
            raise ValueError("X and Y must have the same rectangular shape")
        exact_coefficients, exact_sum, exact_determinant = _exact_coefficients(coeff)
        original_sum = number(exact_sum)
        coefficients = [number(value) for value in exact_coefficients]
        a, b, eta, d = coefficients
        # Evaluate the exact rational determinant rather than subtracting
        # nearly equal mp products. This preserves exact feasible K=0 cases
        # without clipping a negative number or changing the hypothesis.
        determinant = number(exact_determinant)
        k = mp.sqrt(determinant)
        xx, yy, xy = x * x.H, y * y.H, x * y.H
        top, bottom = a * xx + b * yy, eta * xx + d * yy
        full = mp.matrix(2 * x.rows)
        for i in range(x.rows):
            for j in range(x.rows):
                full[i, j] = top[i, j]
                full[i, j + x.rows] = k * xy[i, j]
                full[i + x.rows, j] = k * mp.conj(xy[j, i])
                full[i + x.rows, j + x.rows] = bottom[i, j]
        scalar = mp.matrix([[a + b, k], [k, eta + d]])
        # eigensolver backward errors scale with dimension; this threshold is
        # tied to current precision and far below any requested decimal claim.
        psd_tolerance = 1000 * mp.eps * max(1, full.rows)
        spectra = [list(mp.eighe(matrix, eigvals_only=True)) for matrix in (full, xx, yy, scalar)]
        minimum = min(min(values) for values in spectra)
        if minimum < -psd_tolerance:
            raise ValueError("material negative high-precision eigenvalue; no PSD repair performed")
        entropies = [-mp.fsum(value * mp.log(value) for value in values if value > 0) for values in spectra]
        rhs = (a + eta) * entropies[1] + (b + d) * entropies[2] + entropies[3]
        residual = entropies[0] - rhs
        gram_difference_spectrum = list(mp.eighe(xx - yy, eigvals_only=True))
        gram_trace_norm = mp.fsum(abs(value) for value in gram_difference_spectrum)
        u0, u1 = a + b, eta + d
        pinsker_bound = b * eta * gram_trace_norm**2 / (2 * u0 * u1) if u0 > 0 and u1 > 0 else mp.mpf(0)
        trace_error = max(abs(mp.fsum(values) - 1) for values in spectra)
        hermitian_error = max(abs(full[i, j] - mp.conj(full[j, i])) for i in range(full.rows) for j in range(full.cols))
        if trace_error > psd_tolerance or hermitian_error > psd_tolerance:
            raise ValueError("high-precision state violates trace or Hermiticity tolerance")
        return {
            "entropy_units": "nats",
            "dps": dps,
            "residual_nats": decimal(residual),
            "lhs_entropy_nats": decimal(entropies[0]),
            "rhs_entropy_nats": decimal(rhs),
            "gram_difference_trace_norm": decimal(gram_trace_norm),
            "pinsker_lower_bound_nats": decimal(pinsker_bound),
            "pinsker_margin_nats": decimal(residual - pinsker_bound),
            "minimum_eigenvalue": decimal(minimum),
            "full_spectrum": [decimal(value) for value in spectra[0]],
            "maximum_trace_error": decimal(trace_error),
            "maximum_hermitian_error": decimal(hermitian_error),
            "psd_roundoff_tolerance": decimal(psd_tolerance),
            "negative_roundoff_eigenvalues_excluded_from_entropy": sum(value < 0 for values in spectra for value in values),
            "original_hilbert_schmidt_norms": [decimal(value) for value in norms],
            "input_matrix_normalization": "Each matrix divided by its nonzero Hilbert-Schmidt norm at requested precision; direction preserved.",
            "input_number_interpretation": "Integers/decimal strings preserved; float values interpreted as decimal repr, not unobserved exact inputs.",
            "original_coefficient_sum": decimal(original_sum),
            "original_coefficient_sum_exact_rational": str(exact_sum),
            "coefficient_common_normalization_applied": exact_sum != 1,
            "coefficients_alpha_beta_eta_delta": [decimal(value) for value in coefficients],
            "feasibility": {"accepted": True, "determinant": decimal(determinant), "exact_rational_determinant": str(exact_determinant), "K": decimal(k), "u": decimal(b * (eta + d) + eta * (a + b)), "negative_determinant_repair": False},
            "method": "mpmath.eighe on directly constructed Hermitian thermal state, normalized in arbitrary precision",
            "limitation": "High-precision numerics only; no interval certificate or theorem proof.",
        }
