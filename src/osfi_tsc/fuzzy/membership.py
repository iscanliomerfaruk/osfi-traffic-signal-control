"""Membership functions for arrival rate, queue length, and green extension."""

from __future__ import annotations

from typing import Union
import numpy as np

ArrayOrFloat = Union[float, np.ndarray]

ARRIVAL_UNIVERSE: tuple[float, float] = (0.0, 12.0)
ARRIVAL_SIGMA: float = 1.0
ARRIVAL_CENTERS: dict[str, float] = {
    "Z": 0.0,
    "Lo": 3.0,
    "M": 6.0,
    "H": 9.0,
}

QUEUE_UNIVERSE: tuple[float, float] = (0.0, 60.0)
QUEUE_SIGMA: float = 5.0
QUEUE_CENTERS: dict[str, float] = {
    "Sh": 0.0,
    "M": 15.0,
    "L": 30.0,
    "VL": 45.0,
}

EXTENSION_UNIVERSE: tuple[float, float] = (0.0, 25.0)
EXTENSION_TRIANGLES: dict[str, tuple[float, float, float]] = {
    "Z": (0.0, 0.0, 7.5),
    "Sh": (0.0, 7.5, 12.5),
    "M": (7.5, 12.5, 17.5),
    "L": (12.5, 17.5, 22.5),
}
EXTENSION_PEAKS: dict[str, float] = {
    "Z": 0.0,
    "Sh": 7.5,
    "M": 12.5,
    "L": 17.5,
}


def clip_to_universe(x: ArrayOrFloat, bounds: tuple[float, float]) -> ArrayOrFloat:
    """Clip scalar or array input to the closed interval bounds."""
    if isinstance(x, np.ndarray):
        return np.clip(x, bounds[0], bounds[1])
    return float(np.clip(float(x), bounds[0], bounds[1]))


def gaussian_mf(
    x: ArrayOrFloat,
    center: float,
    sigma: float,
    left_shoulder: bool = False,
    right_shoulder: bool = False,
) -> ArrayOrFloat:
    """Evaluate Gaussian membership function with optional flat shoulders."""
    arr = np.asarray(x, dtype=float)
    val = np.exp(-0.5 * ((arr - center) / sigma) ** 2)
    if left_shoulder:
        val = np.where(arr <= center, 1.0, val)
    if right_shoulder:
        val = np.where(arr >= center, 1.0, val)
    if isinstance(x, np.ndarray):
        return val
    return float(val)


def triangular_mf(
    x: ArrayOrFloat,
    a: float,
    b: float,
    c: float,
    left_shoulder: bool = False,
    right_shoulder: bool = False,
) -> ArrayOrFloat:
    """Evaluate triangular membership function with vertices (a, b, c)."""
    arr = np.asarray(x, dtype=float)
    val = np.zeros_like(arr, dtype=float)

    if b > a:
        left_mask = (arr > a) & (arr < b)
        val = np.where(left_mask, (arr - a) / (b - a), val)

    val = np.where(arr == b, 1.0, val)

    if c > b:
        right_mask = (arr > b) & (arr < c)
        val = np.where(right_mask, (c - arr) / (c - b), val)

    if left_shoulder:
        val = np.where(arr <= b, 1.0, val)
    if right_shoulder:
        val = np.where(arr >= b, 1.0, val)

    val = np.clip(val, 0.0, 1.0)
    if isinstance(x, np.ndarray):
        return val
    return float(val)


def arrival_rate_memberships(
    x: ArrayOrFloat,
    shoulder_edges: bool = True,
) -> dict[str, ArrayOrFloat]:
    """Compute memberships for Arrival Rate lambda in {Z, Lo, M, H}."""
    clipped = clip_to_universe(x, ARRIVAL_UNIVERSE)
    terms = list(ARRIVAL_CENTERS.keys())
    out: dict[str, ArrayOrFloat] = {}
    for idx, term in enumerate(terms):
        left = shoulder_edges and (idx == 0)
        right = shoulder_edges and (idx == len(terms) - 1)
        out[term] = gaussian_mf(
            clipped,
            center=ARRIVAL_CENTERS[term],
            sigma=ARRIVAL_SIGMA,
            left_shoulder=left,
            right_shoulder=right,
        )
    return out


def queue_length_memberships(
    x: ArrayOrFloat,
    shoulder_edges: bool = True,
) -> dict[str, ArrayOrFloat]:
    """Compute memberships for Queue Length q in {Sh, M, L, VL}."""
    clipped = clip_to_universe(x, QUEUE_UNIVERSE)
    terms = list(QUEUE_CENTERS.keys())
    out: dict[str, ArrayOrFloat] = {}
    for idx, term in enumerate(terms):
        left = shoulder_edges and (idx == 0)
        right = shoulder_edges and (idx == len(terms) - 1)
        out[term] = gaussian_mf(
            clipped,
            center=QUEUE_CENTERS[term],
            sigma=QUEUE_SIGMA,
            left_shoulder=left,
            right_shoulder=right,
        )
    return out


def extension_input_memberships(
    x: ArrayOrFloat,
    shoulder_edges: bool = True,
) -> dict[str, ArrayOrFloat]:
    """Compute memberships for Extension1 input in {Z, Sh, M, L}."""
    clipped = clip_to_universe(x, EXTENSION_UNIVERSE)
    terms = list(EXTENSION_TRIANGLES.keys())
    out: dict[str, ArrayOrFloat] = {}
    for idx, term in enumerate(terms):
        a, b, c = EXTENSION_TRIANGLES[term]
        left = shoulder_edges and (idx == 0)
        right = shoulder_edges and (idx == len(terms) - 1)
        out[term] = triangular_mf(
            clipped,
            a=a,
            b=b,
            c=c,
            left_shoulder=left,
            right_shoulder=right,
        )
    return out


def extension_output_memberships(
    x: ArrayOrFloat,
) -> dict[str, ArrayOrFloat]:
    """Compute output triangular memberships for Extension1/Extension2."""
    clipped = clip_to_universe(x, EXTENSION_UNIVERSE)
    out: dict[str, ArrayOrFloat] = {}
    for term, (a, b, c) in EXTENSION_TRIANGLES.items():
        out[term] = triangular_mf(clipped, a=a, b=b, c=c)
    return out


def dominant_linguistic_term(memberships: dict[str, float]) -> str:
    """Return the linguistic term with the largest membership degree."""
    best_term = ""
    best_val = -1.0
    for term, val in memberships.items():
        fval = float(val)
        if fval > best_val:
            best_val = fval
            best_term = term
    return best_term
