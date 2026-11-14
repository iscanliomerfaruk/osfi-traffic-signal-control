"""Unit tests for membership functions, fuzzy operators, and FC1/FC2 rule bases."""

from __future__ import annotations

import numpy as np
import pytest

from osfi_tsc.fuzzy.membership import (
    ARRIVAL_CENTERS,
    ARRIVAL_SIGMA,
    EXTENSION_TRIANGLES,
    QUEUE_CENTERS,
    QUEUE_SIGMA,
    arrival_rate_memberships,
    extension_input_memberships,
    extension_output_memberships,
    queue_length_memberships,
    triangular_mf,
)
from osfi_tsc.fuzzy.operators import (
    defuzz_centroid,
    implicator_goguen,
    implicator_kleene_dienes,
    implicator_lukasiewicz,
    implicator_mamdani,
    implicator_zadeh,
    tnorm_lukasiewicz,
    tnorm_min,
    tnorm_product,
)
from osfi_tsc.fuzzy.rules import (
    FC1_RULES,
    FC2_RULES,
    lookup_fc1,
    lookup_fc2,
)


def test_arrival_rate_mf_centers_and_sigma() -> None:
    """Verify Gaussian arrival-rate MFs equal 1.0 at centers and exp(-0.5) at +-sigma."""
    expected_at_sigma = float(np.exp(-0.5))
    for term, center in ARRIVAL_CENTERS.items():
        m_center = arrival_rate_memberships(center, shoulder_edges=False)
        assert m_center[term] == pytest.approx(1.0, abs=1e-12)
        if center + ARRIVAL_SIGMA <= 12.0:
            m_plus = arrival_rate_memberships(center + ARRIVAL_SIGMA, shoulder_edges=False)
            assert m_plus[term] == pytest.approx(expected_at_sigma, abs=1e-9)
        if center - ARRIVAL_SIGMA >= 0.0:
            m_minus = arrival_rate_memberships(center - ARRIVAL_SIGMA, shoulder_edges=False)
            assert m_minus[term] == pytest.approx(expected_at_sigma, abs=1e-9)


def test_queue_length_mf_centers_and_sigma() -> None:
    """Verify Gaussian queue-length MFs equal 1.0 at centers and exp(-0.5) at +-sigma."""
    expected_at_sigma = float(np.exp(-0.5))
    for term, center in QUEUE_CENTERS.items():
        m_center = queue_length_memberships(center, shoulder_edges=False)
        assert m_center[term] == pytest.approx(1.0, abs=1e-12)
        if center + QUEUE_SIGMA <= 60.0:
            m_plus = queue_length_memberships(center + QUEUE_SIGMA, shoulder_edges=False)
            assert m_plus[term] == pytest.approx(expected_at_sigma, abs=1e-9)
        if center - QUEUE_SIGMA >= 0.0:
            m_minus = queue_length_memberships(center - QUEUE_SIGMA, shoulder_edges=False)
            assert m_minus[term] == pytest.approx(expected_at_sigma, abs=1e-9)


def test_extension_triangular_mfs() -> None:
    """Verify triangular MF peaks and feet for Extension1/Extension2."""
    for term, (a, b, c) in EXTENSION_TRIANGLES.items():
        m_peak = extension_output_memberships(b)
        assert m_peak[term] == pytest.approx(1.0, abs=1e-12)
        if a < b:
            m_left = extension_output_memberships(a)
            assert m_left[term] == pytest.approx(0.0, abs=1e-12)
        m_right = extension_output_memberships(c)
        assert m_right[term] == pytest.approx(0.0, abs=1e-12)


def test_shoulder_edges_flag() -> None:
    """Verify shoulder_edges=True saturates extreme sets to 1.0 while False decays."""
    arr_sh = arrival_rate_memberships(11.5, shoulder_edges=True)
    arr_no_sh = arrival_rate_memberships(11.5, shoulder_edges=False)
    assert arr_sh["H"] == pytest.approx(1.0, abs=1e-12)
    assert arr_no_sh["H"] < 0.10

    q_sh = queue_length_memberships(58.0, shoulder_edges=True)
    q_no_sh = queue_length_memberships(58.0, shoulder_edges=False)
    assert q_sh["VL"] == pytest.approx(1.0, abs=1e-12)
    assert q_no_sh["VL"] < 0.05

    ext_sh = extension_input_memberships(24.0, shoulder_edges=True)
    ext_no_sh = extension_input_memberships(24.0, shoulder_edges=False)
    assert ext_sh["L"] == pytest.approx(1.0, abs=1e-12)
    assert ext_no_sh["L"] == pytest.approx(0.0, abs=1e-12)


def test_rule_base_sizes_and_paper_quoted_rules() -> None:
    """Verify FC1 has 16 rules, FC2 has 13 rules, and all 6 quoted rules match paper."""
    assert len(FC1_RULES) == 16
    assert len(FC2_RULES) == 13

    assert lookup_fc1("Z", "Sh") == "Z"
    assert lookup_fc1("Lo", "L") == "Sh"
    assert lookup_fc1("M", "Sh") == "Sh"

    assert lookup_fc2("Z", "Sh") == "Z"
    assert lookup_fc2("Sh", "M") == "Sh"
    assert lookup_fc2("M", "Sh") == "M"

    for q_term in ("Sh", "M", "L", "VL"):
        assert lookup_fc2("Z", q_term) == "Z"


def test_tnorm_boundary_conditions() -> None:
    """Verify t-norm boundary and monotonicity identities on [0, 1]."""
    for tnorm in (tnorm_min, tnorm_product, tnorm_lukasiewicz):
        assert tnorm(0.0, 0.0) == pytest.approx(0.0)
        assert tnorm(1.0, 0.0) == pytest.approx(0.0)
        assert tnorm(0.0, 1.0) == pytest.approx(0.0)
        assert tnorm(1.0, 1.0) == pytest.approx(1.0)
        assert tnorm(0.65, 1.0) == pytest.approx(0.65)
        assert tnorm(1.0, 0.65) == pytest.approx(0.65)


def test_implicator_boundary_conditions_definition3() -> None:
    """Verify Definition 3 boundary conditions for implicators and document Mamdani I(0,b)=0."""
    true_implicators = (
        implicator_lukasiewicz,
        implicator_goguen,
        implicator_kleene_dienes,
        implicator_zadeh,
    )
    for imp in true_implicators:
        assert imp(0.0, 0.0) == pytest.approx(1.0)
        assert imp(1.0, 0.0) == pytest.approx(0.0)
        assert imp(0.0, 1.0) == pytest.approx(1.0)
        assert imp(1.0, 1.0) == pytest.approx(1.0)

    assert implicator_mamdani(1.0, 0.0) == pytest.approx(0.0)
    assert implicator_mamdani(1.0, 1.0) == pytest.approx(1.0)
    assert implicator_mamdani(0.0, 0.0) == pytest.approx(0.0)
    assert implicator_mamdani(0.0, 1.0) == pytest.approx(0.0)


def test_centroid_of_symmetric_triangle() -> None:
    """Verify defuzz_centroid recovers exact center of a symmetric triangle."""
    u = np.arange(0.0, 25.0 + 0.05, 0.05)
    for center in (7.5, 12.5, 17.5):
        mf = triangular_mf(u, center - 5.0, center, center + 5.0)
        c_est = defuzz_centroid(u, mf)
        assert c_est == pytest.approx(center, abs=1e-9)
