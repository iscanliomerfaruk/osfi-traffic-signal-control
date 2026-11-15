"""Unit tests for Deng & Jiang (2014) OSFI-DJ, sup-T CRI, Proposition 1, and d1 similarity."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from osfi_tsc.fuzzy.operators import implicator_mamdani
from osfi_tsc.inference.cri import CRIStageEngine, d1_similarity
from osfi_tsc.inference.osfi_dj import OSFIDJInference, OSFIDJStageEngine


@pytest.mark.parametrize("implicator", ["lukasiewicz", "goguen", "kleene_dienes"])
def test_proposition_singleton_osfi_dj_equals_closed_form_and_cri(implicator: str) -> None:
    """Verify Proposition 1: singleton OSFI-DJ equals I(A(x0), B(y)) and CRI (< 1e-9 on grid points)."""
    osfi_eng = OSFIDJStageEngine(
        stage="fc1",
        implicator=implicator,
        tie_break="smallest",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sigma1=0.0,
        sigma2=0.0,
    )
    cri_eng = CRIStageEngine(
        stage="fc1",
        implicator=implicator,
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sigma1=0.0,
        sigma2=0.0,
    )

    sample_x1_indices = [0, 10, 20, 30, 45, 60]
    sample_x2_indices = [0, 12, 25, 37, 50, 60]

    max_err_closed = 0.0
    max_err_cri_set = 0.0
    max_err_cri_crisp = 0.0

    for i1 in sample_x1_indices:
        for i2 in sample_x2_indices:
            x1_0 = float(osfi_eng.x1_grid[i1])
            x2_0 = float(osfi_eng.x2_grid[i2])
            flat_idx = i1 * osfi_eng.x2_pts + i2

            a_star = osfi_eng.build_input_fuzzy_set(x1_0, x2_0)
            assert float(a_star[flat_idx]) == 1.0
            assert float(np.sum(a_star)) == 1.0

            b_all_osfi = osfi_eng.infer_all_rule_conclusions(a_star)
            for r_idx in range(len(osfi_eng.rules)):
                closed_form = np.asarray(
                    osfi_eng.implicator_fn(
                        osfi_eng.a_rules[r_idx, flat_idx],
                        osfi_eng.b_rules[r_idx],
                    ),
                    dtype=float,
                )
                b_cri_rule = cri_eng.infer_rule_conclusion(r_idx, a_star)

                err_c = float(np.max(np.abs(b_all_osfi[r_idx] - closed_form)))
                err_r = float(np.max(np.abs(b_all_osfi[r_idx] - b_cri_rule)))
                max_err_closed = max(max_err_closed, err_c)
                max_err_cri_set = max(max_err_cri_set, err_r)

            crisp_osfi = osfi_eng.infer_direct(x1_0, x2_0)
            crisp_cri = cri_eng.infer_direct(x1_0, x2_0)
            max_err_cri_crisp = max(max_err_cri_crisp, abs(crisp_osfi - crisp_cri))

    assert max_err_closed < 1e-9
    assert max_err_cri_set < 1e-9
    assert max_err_cri_crisp < 1e-9


def test_proposition_singleton_mamdani_equals_clipping() -> None:
    """Verify Mamdani-min singleton OSFI-DJ equals Mamdani clipping min(A(x0), B(y)) and CRI."""
    osfi_eng = OSFIDJStageEngine(
        stage="fc1",
        implicator="mamdani",
        tie_break="smallest",
        defuzz_method="centroid",
        shoulder_edges=True,
        sigma1=0.0,
        sigma2=0.0,
    )
    cri_eng = CRIStageEngine(
        stage="fc1",
        implicator="mamdani",
        defuzz_method="centroid",
        shoulder_edges=True,
        sigma1=0.0,
        sigma2=0.0,
    )

    sample_x1_indices = [0, 15, 30, 45]
    sample_x2_indices = [0, 15, 30, 45]

    max_err_clipping = 0.0
    max_err_cri = 0.0

    for i1 in sample_x1_indices:
        for i2 in sample_x2_indices:
            x1_0 = float(osfi_eng.x1_grid[i1])
            x2_0 = float(osfi_eng.x2_grid[i2])
            flat_idx = i1 * osfi_eng.x2_pts + i2

            a_star = osfi_eng.build_input_fuzzy_set(x1_0, x2_0)
            b_all_osfi = osfi_eng.infer_all_rule_conclusions(a_star)
            for r_idx in range(len(osfi_eng.rules)):
                clipped = np.asarray(
                    implicator_mamdani(
                        osfi_eng.a_rules[r_idx, flat_idx],
                        osfi_eng.b_rules[r_idx],
                    ),
                    dtype=float,
                )
                b_cri = cri_eng.infer_rule_conclusion(r_idx, a_star)
                max_err_clipping = max(
                    max_err_clipping,
                    float(np.max(np.abs(b_all_osfi[r_idx] - clipped))),
                )
                max_err_cri = max(
                    max_err_cri,
                    float(np.max(np.abs(b_all_osfi[r_idx] - b_cri))),
                )

    assert max_err_clipping < 1e-9
    assert max_err_cri < 1e-9


def test_non_singleton_osfi_dj_and_cri_differ() -> None:
    """Verify that under non-singleton inputs OSFI-DJ and sup-T CRI produce distinct outputs."""
    osfi_eng = OSFIDJStageEngine(
        stage="fc1",
        implicator="lukasiewicz",
        tie_break="smallest",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sigma1=1.0,
        sigma2=10.0,
    )
    cri_eng = CRIStageEngine(
        stage="fc1",
        implicator="lukasiewicz",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sigma1=1.0,
        sigma2=10.0,
    )

    test_points = [(0.5, 17.5), (4.0, 20.0), (8.5, 7.5), (9.5, 2.5)]
    max_set_diff = 0.0
    max_crisp_diff = 0.0
    report_lines: list[str] = []

    for x1_val, x2_val in test_points:
        b_osfi = osfi_eng.infer_aggregated_set(x1_val, x2_val)
        b_cri = cri_eng.infer_aggregated_set(x1_val, x2_val)
        y_osfi = osfi_eng.infer_direct(x1_val, x2_val)
        y_cri = cri_eng.infer_direct(x1_val, x2_val)

        set_diff = float(np.max(np.abs(b_osfi - b_cri)))
        crisp_diff = abs(y_osfi - y_cri)
        max_set_diff = max(max_set_diff, set_diff)
        max_crisp_diff = max(max_crisp_diff, crisp_diff)
        report_lines.append(
            f"input=({x1_val:.1f}, {x2_val:.1f}): OSFI-DJ={y_osfi:.4f}s, "
            f"CRI={y_cri:.4f}s, |d_crisp|={crisp_diff:.4f}s, max|dB*|={set_diff:.4f}"
        )

    summary_msg = " | ".join(report_lines)
    print(f"\nNon-singleton OSFI-DJ vs CRI comparison: {summary_msg}")

    assert max_set_diff > 0.3, (
        f"Expected non-singleton OSFI-DJ and CRI output sets to differ, got max_set_diff={max_set_diff}"
    )
    assert max_crisp_diff > 0.5, (
        f"Expected non-singleton OSFI-DJ and CRI crisp outputs to differ, got max_crisp_diff={max_crisp_diff}"
    )


def test_d1_similarity_measure_properties() -> None:
    """Verify Definition 4 axioms for d1 similarity: bounds, symmetry, identity, and inclusion."""
    rng = np.random.default_rng(12345)
    for _ in range(25):
        a = rng.uniform(0.0, 1.0, size=(30, 20))
        b = rng.uniform(0.0, 1.0, size=(30, 20))

        sim_ab = d1_similarity(a, b)
        sim_ba = d1_similarity(b, a)
        sim_aa = d1_similarity(a, a)

        assert 0.0 <= sim_ab <= 1.0
        assert abs(sim_ab - sim_ba) < 1e-15
        assert abs(sim_aa - 1.0) < 1e-15
        if np.max(np.abs(a - b)) > 1e-6:
            assert sim_ab < 1.0

    zeros = np.zeros((10, 10), dtype=float)
    ones = np.ones((10, 10), dtype=float)
    assert abs(d1_similarity(zeros, ones) - 0.0) < 1e-15

    e1 = rng.uniform(0.0, 0.3, size=(25, 25))
    e2 = e1 + rng.uniform(0.0, 0.3, size=(25, 25))
    e3 = e2 + rng.uniform(0.0, 0.3, size=(25, 25))
    assert d1_similarity(e1, e3) <= d1_similarity(e1, e2) + 1e-15
    assert d1_similarity(e1, e3) <= d1_similarity(e2, e3) + 1e-15


def test_osfi_dj_singleton_control_surface_monotonicity() -> None:
    """Verify monotonicity of the OSFI-DJ singleton FC1 control surface in both inputs."""
    osfi_eng = OSFIDJStageEngine(
        stage="fc1",
        implicator="lukasiewicz",
        tie_break="smallest",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sigma1=0.0,
        sigma2=0.0,
    )

    lam_grid = [0.0, 3.0, 6.0, 9.0, 12.0]
    q_grid = [0.0, 15.0, 30.0, 45.0, 60.0]
    surface = np.zeros((len(lam_grid), len(q_grid)), dtype=float)

    for i, lam in enumerate(lam_grid):
        for j, q in enumerate(q_grid):
            surface[i, j] = osfi_eng.infer_direct(float(lam), float(q))

    diffs_lam = np.diff(surface, axis=0)
    diffs_q = np.diff(surface, axis=1)

    assert float(np.min(diffs_lam)) >= -1e-9
    assert float(np.min(diffs_q)) >= -1e-9
    assert float(surface[-1, -1] - surface[0, 0]) > 10.0


def test_osfi_dj_lut_build_and_interpolation_accuracy(tmp_path: Path) -> None:
    """Verify LUT building, caching, and bilinear interpolation accuracy on random off-grid points."""
    inf = OSFIDJInference(
        stage="fc1",
        implicator="lukasiewicz",
        tie_break="smallest",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sigma_lambda=0.0,
        sigma_queue=0.0,
        sigma_ext1=0.0,
        use_lut=True,
        cache_dir=tmp_path,
        n_workers=2,
    )
    assert inf.fc1_lut is not None
    assert inf.fc2_lut is not None
    assert Path(inf.fc1_lut["cache_file"]).exists()
    assert Path(inf.fc2_lut["cache_file"]).exists()

    errors = inf.measure_lut_errors(n_samples=40, seed=99)
    assert errors["fc1"]["mean_abs_error"] < 0.8
    assert errors["fc2"]["mean_abs_error"] < 0.5
