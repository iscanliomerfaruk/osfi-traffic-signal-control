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


def test_unified_dead_zone_nearest_rule_fallback() -> None:
    """Verify OSFI-literal, OSFI-DJ-S, and CRI-S use identical nearest-rule fallback in dead zones."""
    from osfi_tsc.fuzzy.rules import nearest_rule_fallback_for_inputs
    from osfi_tsc.inference.cri import CRIInference
    from osfi_tsc.inference.osfi_dj import OSFIDJInference

    osfi_lit = OSFILiteralInference(stage="fc1", shoulder_edges=True)
    osfi_dj = OSFIDJInference(stage="fc1", shoulder_edges=True, use_lut=False)
    cri_s = CRIInference(stage="fc1", shoulder_edges=True, use_lut=False)

    expected_peak = nearest_rule_fallback_for_inputs(
        1.5, 7.5, stage="fc1", shoulder_edges=True
    )
    out_lit = osfi_lit.infer(1.5, 7.5)
    out_dj = osfi_dj.infer(1.5, 7.5)
    out_cri = cri_s.infer(1.5, 7.5)

    assert osfi_lit.fallback_count == 1
    assert osfi_dj.fallback_count == 1
    assert cri_s.fallback_count == 1
    assert out_lit == pytest.approx(expected_peak, abs=1e-12)
    assert out_dj == pytest.approx(expected_peak, abs=1e-12)
    assert out_cri == pytest.approx(expected_peak, abs=1e-12)


def test_dead_zone_eliminated_by_min_and_or_widened_sigma() -> None:
    """Verify min AND and mf_sigma_scale=1.5 eliminate dead-zone fallbacks at crossover (1.5, 7.5)."""
    osfi_min = OSFILiteralInference(
        stage="fc1", shoulder_edges=True, and_operator="min"
    )
    osfi_wide = OSFILiteralInference(
        stage="fc1", shoulder_edges=True, mf_sigma_scale=1.5
    )

    _ = osfi_min.infer(1.5, 7.5)
    _ = osfi_wide.infer(1.5, 7.5)

    assert osfi_min.fallback_count == 0
    assert osfi_wide.fallback_count == 0
