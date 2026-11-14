"""Fuzzy t-norms, s-norms, implicators, and centroid defuzzification."""

from __future__ import annotations

from typing import Union
import numpy as np

ArrayOrFloat = Union[float, np.ndarray]


def _format_return(val: np.ndarray, a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return val
    return float(val)


def tnorm_min(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Minimum (Godel) t-norm: min(a, b)."""
    res = np.minimum(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    return _format_return(res, a, b)


def tnorm_product(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Algebraic product t-norm: a * b."""
    res = np.asarray(a, dtype=float) * np.asarray(b, dtype=float)
    return _format_return(res, a, b)


def tnorm_lukasiewicz(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Lukasiewicz t-norm: max(0, a + b - 1)."""
    res = np.maximum(0.0, np.asarray(a, dtype=float) + np.asarray(b, dtype=float) - 1.0)
    return _format_return(res, a, b)


def snorm_max(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Maximum t-conorm (s-norm): max(a, b)."""
    res = np.maximum(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    return _format_return(res, a, b)


def implicator_mamdani(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Mamdani implicator (Definition 3, Example 1): min(a, b)."""
    res = np.minimum(np.asarray(a, dtype=float), np.asarray(b, dtype=float))
    return _format_return(res, a, b)


def implicator_lukasiewicz(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Lukasiewicz implicator (Definition 3, Example 2): min(1, 1 - a + b)."""
    res = np.minimum(1.0, 1.0 - np.asarray(a, dtype=float) + np.asarray(b, dtype=float))
    return _format_return(res, a, b)


def implicator_goguen(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Goguen implicator (Definition 3, Example 3): 1 if a <= b else b / a."""
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    safe_a = np.where(arr_a > arr_b, arr_a, 1.0)
    res = np.where(arr_a <= arr_b, 1.0, arr_b / safe_a)
    return _format_return(res, a, b)


def implicator_kleene_dienes(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Kleene-Dienes implicator: max(1 - a, b)."""
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    res = np.maximum(1.0 - arr_a, arr_b)
    return _format_return(res, a, b)


def implicator_zadeh(a: ArrayOrFloat, b: ArrayOrFloat) -> ArrayOrFloat:
    """Zadeh implicator (Definition 3, Example 4): max(1 - a, min(a, b))."""
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    res = np.maximum(1.0 - arr_a, np.minimum(arr_a, arr_b))
    return _format_return(res, a, b)


def defuzz_centroid(universe: np.ndarray, membership: np.ndarray) -> float:
    """Compute centroid (center of gravity) over a discretized universe."""
    u = np.asarray(universe, dtype=float)
    m = np.asarray(membership, dtype=float)
    denom = float(np.sum(m))
    if denom <= 1e-12:
        return 0.0
    return float(np.sum(u * m) / denom)
