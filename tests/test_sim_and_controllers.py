"""Unit tests for simulator conservation, common random numbers, determinism, and code style."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from osfi_tsc.control import ActuatedController, FuzzyController, WebsterController
from osfi_tsc.inference import (
    MamdaniInference,
    OSFILiteralInference,
    SugenoInference,
)
from osfi_tsc.metrics import compute_run_metrics
from osfi_tsc.sim import (
    APPROACHES,
    IntersectionSimulator,
    ScenarioDemand,
    compute_matched_input_sigmas,
    compute_webster_flow_ratios,
    pregenerate_arrival_timestamps,
    pregenerate_arrivals,
    pregenerate_sensor_noise,
)


def test_webster_flow_ratio_under_095() -> None:
    """Verify calibrated YAML scenarios load properly and Webster flow ratio Y < 0.95."""
    expected_means = {
        "moderate": 1100.0,
        "heavy": 1500.0,
        "peak": 1625.0,
        "stress": 1800.0,
    }
    for name, exp_vph in expected_means.items():
        scen = ScenarioDemand.from_name(name)
        assert scen.mean_total_demand_vph() == pytest.approx(exp_vph, abs=1e-9)
        y_map, y_tot = compute_webster_flow_ratios(scen)
        assert y_tot < 0.95
        assert sum(y_map.values()) == pytest.approx(y_tot, abs=1e-12)


def test_simulator_conservation_every_step() -> None:
    """Verify arrivals == departures + queued at every simulation step and at horizon end."""
    sim = IntersectionSimulator(warmup_s=100, measurement_s=300)
    ctrl = FuzzyController(OSFILiteralInference())
    res = sim.run(
        controller=ctrl,
        scenario=ScenarioDemand.from_name("heavy"),
        seed=42,
        controller_name="OSFI-literal",
        verify_conservation=True,
    )
    for app in APPROACHES:
        total_arr = int(np.sum(res.arrival_counts[app]))
        total_dep = len(res.departed_vehicles[app])
        total_rem = len(res.remaining_queues[app])
        assert total_arr == total_dep + total_rem


def test_common_random_numbers_identical_arrival_streams() -> None:
    """Verify all controllers receive bit-for-bit identical arrival streams for a given seed."""
    sim = IntersectionSimulator(warmup_s=60, measurement_s=180)
    seed = 202599
    scen = ScenarioDemand.from_name("moderate")

    controllers = [
        ("Mamdani", FuzzyController(MamdaniInference())),
        ("Sugeno", FuzzyController(SugenoInference())),
        ("OSFI-literal", FuzzyController(OSFILiteralInference())),
        ("Webster", WebsterController(scen)),
        ("Actuated", ActuatedController()),
    ]

    results = [
        sim.run(ctrl, scen, seed=seed, controller_name=name)
        for name, ctrl in controllers
    ]

    ref_arrivals = results[0].arrival_counts
    for res in results[1:]:
        for app in APPROACHES:
            assert np.array_equal(ref_arrivals[app], res.arrival_counts[app])

    ts1 = pregenerate_arrival_timestamps(scen, seed=seed, warmup_s=60, measurement_s=180)
    ts2 = pregenerate_arrival_timestamps(scen, seed=seed, warmup_s=60, measurement_s=180)
    for app in APPROACHES:
        assert np.array_equal(ts1[app], ts2[app])
        assert len(ts1[app]) == int(np.sum(ref_arrivals[app]))


def test_simulator_determinism_same_seed_same_results() -> None:
    """Verify running the simulator twice with the same seed produces identical metrics."""
    sim = IntersectionSimulator(warmup_s=120, measurement_s=300)
    scen = ScenarioDemand.from_name("peak")
    seed = 777

    c1 = FuzzyController(OSFILiteralInference())
    c2 = FuzzyController(OSFILiteralInference())

    r1 = sim.run(c1, scen, seed=seed, controller_name="OSFI-literal")
    r2 = sim.run(c2, scen, seed=seed, controller_name="OSFI-literal")

    m1, cov1 = compute_run_metrics(r1, c1)
    m2, cov2 = compute_run_metrics(r2, c2)

    assert m1 == m2
    assert cov1 == cov2
    for app in APPROACHES:
        assert np.array_equal(r1.queue_veh_history[app], r2.queue_veh_history[app])


def test_no_comment_lines_in_python_source_files() -> None:
    """Enforce repository style rule: no '#' comment lines inside Python source files."""
    repo_root = Path(__file__).resolve().parent.parent
    for folder in ("src", "scripts", "tests"):
        for py_file in (repo_root / folder).rglob("*.py"):
            for lineno, line in enumerate(
                py_file.read_text(encoding="utf-8").splitlines(), start=1
            ):
                stripped = line.lstrip()
                assert not stripped.startswith("#"), (
                    f"Comment line found in {py_file}:{lineno}: {line}"
                )


def test_noisy_sensor_common_random_numbers_and_bounds() -> None:
    """Verify noisy queue and arrival sensor streams are reproducible and non-negative."""
    scen = ScenarioDemand.from_name("heavy")
    arr = pregenerate_arrivals(scen, seed=101, warmup_s=60, measurement_s=180)
    q_n1, d_a1 = pregenerate_sensor_noise(
        arr, seed=101, horizon_steps=240, queue_noise_std_m=10.0, arrival_p_miss=0.2
    )
    q_n2, d_a2 = pregenerate_sensor_noise(
        arr, seed=101, horizon_steps=240, queue_noise_std_m=10.0, arrival_p_miss=0.2
    )
    for app in APPROACHES:
        assert np.array_equal(q_n1[app], q_n2[app])
        assert np.array_equal(d_a1[app], d_a2[app])
        assert int(np.min(d_a1[app])) >= 0

    s1_0, s2_0 = compute_matched_input_sigmas(sigma_q=0.0, p_miss=0.0)
    s1_2, s2_2 = compute_matched_input_sigmas(sigma_q=10.0, p_miss=0.2)
    assert s2_0 == 1.0
    assert s2_2 == 10.0
    assert s1_2 > s1_0


def test_gpe_first_never_switches_when_ext2_at_least_1_and_under_gmax() -> None:
    """Verify gpe_first never switches while Extension2 >= 1, q_cur > 0, and green < G_max."""
    from osfi_tsc.sim.intersection import SensorReading

    ctrl = FuzzyController(MamdaniInference(), g_min=7, g_max=60, spm_mode="gpe_first")
    reading = SensorReading(
        t=7.0,
        queues_m={"E": 15.0, "S": 55.0, "W": 40.0, "N": 30.0},
        queues_veh={"E": 4, "S": 16, "W": 11, "N": 9},
        arrival_rates={"E": 4.0, "S": 6.0, "W": 3.0, "N": 3.0},
        arrivals_this_step={"E": 0, "S": 1, "W": 0, "N": 0},
        active_phase="E",
        green_elapsed=7,
        in_intergreen=False,
    )
    cmd = ctrl.step(7.0, reading)
    assert cmd == "E"
    assert ctrl.decision_log[-1]["extension2"] >= 1.0
    assert ctrl.decision_log[-1]["action"].startswith("extend_")

    ctrl_preempt = FuzzyController(
        MamdaniInference(), g_min=7, g_max=60, spm_mode="preempt"
    )
    cmd_preempt = ctrl_preempt.step(7.0, reading)
    assert cmd_preempt == "S"
    assert ctrl_preempt.decision_log[-1]["action"] == "switch_longer_queue"


def test_mamdani_thrashing_guard_mean_green_above_gmin_plus_2() -> None:
    """Verify Mamdani mean green duration in heavy scenario is strictly above G_min + 2 s."""
    sim = IntersectionSimulator(warmup_s=300, measurement_s=1800)
    ctrl = FuzzyController(MamdaniInference(), g_min=7, g_max=60, spm_mode="gpe_first")
    scen = ScenarioDemand.from_name("heavy")
    res = sim.run(ctrl, scen, seed=202501, controller_name="Mamdani")
    assert len(res.green_durations_measurement) > 0
    mean_green = float(np.mean(res.green_durations_measurement))
    assert mean_green > float(ctrl.g_min + 2), f"Expected mean_green > 9.0s, got {mean_green:.2f}s"


def test_actuated_does_not_gap_out_while_queue_positive() -> None:
    """Verify ActuatedController does not gap out while its current queue > 0 and green < G_max."""
    from osfi_tsc.sim.intersection import SensorReading

    ctrl = ActuatedController(g_min=7, unit_extension=3, g_max=60, initial_phase="E")
    for t in range(1, 25):
        reading = SensorReading(
            t=float(t),
            queues_m={"E": 21.0, "S": 35.0, "W": 14.0, "N": 14.0},
            queues_veh={"E": 6, "S": 10, "W": 4, "N": 4},
            arrival_rates={"E": 0.0, "S": 3.0, "W": 1.0, "N": 1.0},
            arrivals_this_step={"E": 0, "S": 1, "W": 0, "N": 0},
            active_phase="E",
            green_elapsed=t,
            in_intergreen=False,
        )
        cmd = ctrl.step(float(t), reading)
        assert cmd == "E", f"Actuated gapped out at t={t} despite q_E=21.0 m > 0"


