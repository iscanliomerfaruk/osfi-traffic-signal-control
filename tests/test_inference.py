"""Unit tests for Mamdani, Sugeno, and OSFI-literal inference engines."""

from __future__ import annotations

import pytest

from osfi_tsc.inference import (
    MamdaniInference,
    OSFILiteralInference,
    SugenoInference,
)


@pytest.mark.parametrize(
    "engine_cls",
    [MamdaniInference, SugenoInference, OSFILiteralInference],
)
def test_fc1_monotonicity_in_both_inputs(engine_cls: type) -> None:
    """Verify FC1 output is monotonically non-decreasing in both arrival rate and queue length."""
    eng = engine_cls(stage="fc1", shoulder_edges=True)
    lam_points = [0.0, 3.0, 6.0, 9.0, 12.0]
    q_points = [0.0, 15.0, 30.0, 45.0, 60.0]

    grid = [[eng.infer(lam, q) for q in q_points] for lam in lam_points]

    for i in range(len(lam_points)):
        for j in range(len(q_points) - 1):
            assert grid[i][j + 1] >= grid[i][j] - 1e-9, (
                f"{engine_cls.__name__} non-monotonic in queue at lam={lam_points[i]}: "
                f"{grid[i][j]} -> {grid[i][j + 1]}"
            )

    for j in range(len(q_points)):
        for i in range(len(lam_points) - 1):
            assert grid[i + 1][j] >= grid[i][j] - 1e-9, (
                f"{engine_cls.__name__} non-monotonic in arrival rate at q={q_points[j]}: "
                f"{grid[i][j]} -> {grid[i + 1][j]}"
            )


@pytest.mark.parametrize(
    "engine_cls",
    [MamdaniInference, SugenoInference, OSFILiteralInference],
)
def test_fc2_monotonicity_in_both_inputs(engine_cls: type) -> None:
    """Verify FC2 output is non-decreasing in Extension1 and non-increasing in competing queue."""
    eng = engine_cls(stage="fc2", shoulder_edges=True)
    ext1_points = [0.0, 7.5, 12.5, 17.5, 22.5]
    q_other_points = [0.0, 15.0, 30.0, 45.0, 60.0]

    grid = [[eng.infer(e1, qo) for qo in q_other_points] for e1 in ext1_points]

    for j in range(len(q_other_points)):
        for i in range(len(ext1_points) - 1):
            assert grid[i + 1][j] >= grid[i][j] - 1e-9

    for i in range(len(ext1_points)):
        for j in range(len(q_other_points) - 1):
            assert grid[i][j + 1] <= grid[i][j] + 1e-9


def test_osfi_literal_fallback_to_sugeno() -> None:
    """Verify OSFI-literal falls back to Sugeno output and increments fallback counter when sum(alpha)==0."""
    osfi = OSFILiteralInference(stage="fc1", shoulder_edges=True)
    sugeno = SugenoInference(stage="fc1", shoulder_edges=True)

    out_osfi = osfi.infer(1.5, 7.5)
    out_sugeno = sugeno.infer(1.5, 7.5)

    assert osfi.fallback_count == 1
    assert osfi.total_calls == 1
    assert osfi.fallback_rate == pytest.approx(1.0)
    assert out_osfi == pytest.approx(out_sugeno, abs=1e-12)
