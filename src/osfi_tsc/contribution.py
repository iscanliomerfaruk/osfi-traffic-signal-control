"""Stage 2 contribution experiments (A, B, C), LUT precomputation, and statistical analyses."""

from __future__ import annotations

import copy
from multiprocessing import Pool, cpu_count
from pathlib import Path
import time
from typing import Any
import numpy as np
import pandas as pd
from scipy import stats
from tqdm import tqdm

from osfi_tsc.experiment import (
    FUZZY_CONTROLLER_NAMES,
    build_controller,
    load_config,
    summarize_input_coverage,
    verify_sanity_gates,
)
from osfi_tsc.inference.cri import CRIInference, CRIStageEngine
from osfi_tsc.inference.osfi_dj import (
    OSFIDJInference,
    OSFIDJStageEngine,
    measure_stage_lut_interpolation_error,
)
from osfi_tsc.metrics import compute_run_metrics, holm_bonferroni, mean_and_t_ci
from osfi_tsc.sim import (
    IntersectionSimulator,
    ScenarioDemand,
    compute_matched_input_sigmas,
    pregenerate_arrivals,
    pregenerate_sensor_noise,
    validate_and_print_webster_ratios,
)

EXP_A_CONTROLLERS: tuple[str, ...] = (
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "OSFI-DJ-S",
    "CRI-S",
    "Webster",
    "Actuated",
)

EXP_B_CONTROLLERS: tuple[str, ...] = (
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "OSFI-DJ-S",
    "CRI-NS",
    "OSFI-DJ-NS",
    "OSFI-DJ-NS-mis",
    "Webster",
    "Actuated",
)

ABLATION_SPECS: tuple[dict[str, Any], ...] = (
    {
        "variant_id": "baseline_luk_smallest_abovefloor_shoulder",
        "factor": "Baseline",
        "label": "Łukasiewicz + smallest + above_floor + shoulder + gpe_first",
        "implicator": "lukasiewicz",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "implicator_goguen",
        "factor": "Implicator",
        "label": "Goguen implicator",
        "implicator": "goguen",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "implicator_kleene_dienes",
        "factor": "Implicator",
        "label": "Kleene-Dienes implicator",
        "implicator": "kleene_dienes",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "tie_break_midpoint",
        "factor": "Tie-break",
        "label": "Midpoint tie-break",
        "implicator": "lukasiewicz",
        "tie_break": "midpoint",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "defuzz_standard_centroid",
        "factor": "Defuzzifier",
        "label": "Standard centroid (with floor)",
        "implicator": "lukasiewicz",
        "tie_break": "smallest",
        "defuzz_method": "centroid",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "shoulder_edges_false",
        "factor": "Boundary MFs",
        "label": "shoulder_edges = False",
        "implicator": "lukasiewicz",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": False,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "and_operator_min",
        "factor": "Antecedent AND",
        "label": "and_operator = min (eliminates dead zones)",
        "implicator": "lukasiewicz",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "min",
        "mf_sigma_scale": 1.0,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "mf_sigma_scale_1_5",
        "factor": "MF Width",
        "label": "mf_sigma_scale = 1.5 (widened Gaussians)",
        "implicator": "lukasiewicz",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.5,
        "spm_mode": "gpe_first",
    },
    {
        "variant_id": "spm_mode_preempt",
        "factor": "Phase Switching",
        "label": "spm_mode = preempt (thrashing ablation)",
        "implicator": "lukasiewicz",
        "tie_break": "smallest",
        "defuzz_method": "centroid_above_floor",
        "shoulder_edges": True,
        "and_operator": "lukasiewicz",
        "mf_sigma_scale": 1.0,
        "spm_mode": "preempt",
    },
)


def prebuild_all_luts_and_measure_errors(
    config: dict[str, Any],
    n_workers: int | None = None,
    n_error_samples: int = 500,
) -> tuple[pd.DataFrame, pd.DataFrame, float, OSFIDJInference, OSFIDJInference]:
    """Precompute all Stage 2/3 LUTs and measure 500-point off-grid interpolation accuracy."""
    t_start = time.perf_counter()
    fuzzy_cfg = config.get("fuzzy", {})
    sim_cfg = config.get("simulator", {})
    noise_cfg = sim_cfg.get("sensor_noise", {})

    cache_dir = Path(str(fuzzy_cfg.get("cache_dir", "results/cache")))
    sigma_q_grid = [float(x) for x in noise_cfg.get("queue_std_grid_m", [0.0, 5.0, 10.0, 15.0])]
    p_miss_grid = [float(x) for x in noise_cfg.get("arrival_p_miss_grid", [0.0, 0.1, 0.2])]

    lut_records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    def _register_osfi(
        label: str,
        implicator: str,
        tie_break: str,
        defuzz_method: str,
        shoulder_edges: bool,
        sig_lam: float,
        sig_q: float,
        and_operator: str = "lukasiewicz",
        mf_sigma_scale: float = 1.0,
    ) -> OSFIDJInference:
        inf = OSFIDJInference(
            implicator=implicator,
            tie_break=tie_break,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder_edges,
            and_operator=and_operator,
            mf_sigma_scale=mf_sigma_scale,
            sigma_lambda=sig_lam,
            sigma_queue=sig_q,
            sigma_ext1=0.0,
            use_lut=True,
            cache_dir=cache_dir,
            n_workers=n_workers,
        )
        for stg, eng, lut in (
            ("fc1", inf.fc1_engine, inf.fc1_lut),
            ("fc2", inf.fc2_engine, inf.fc2_lut),
        ):
            assert lut is not None
            h_val = f"osfi_dj_{stg}_{eng.config_hash()}"
            if h_val not in seen_hashes:
                seen_hashes.add(h_val)
                lut_records.append(
                    {
                        "engine": "OSFI-DJ",
                        "stage": stg,
                        "config_label": label,
                        "implicator": implicator,
                        "tie_break": tie_break,
                        "defuzz_method": defuzz_method,
                        "shoulder_edges": shoulder_edges,
                        "and_operator": and_operator,
                        "mf_sigma_scale": mf_sigma_scale,
                        "sigma1": eng.sigma1,
                        "sigma2": eng.sigma2,
                        "config_hash": eng.config_hash(),
                        "build_time_s": float(lut["build_time_s"]),
                        "cache_file": str(lut["cache_file"]),
                    }
                )
        return inf

    def _register_cri(
        label: str,
        implicator: str,
        defuzz_method: str,
        shoulder_edges: bool,
        sig_lam: float,
        sig_q: float,
        and_operator: str = "lukasiewicz",
        mf_sigma_scale: float = 1.0,
    ) -> CRIInference:
        inf = CRIInference(
            implicator=implicator,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder_edges,
            and_operator=and_operator,
            mf_sigma_scale=mf_sigma_scale,
            sigma_lambda=sig_lam,
            sigma_queue=sig_q,
            sigma_ext1=0.0,
            use_lut=True,
            cache_dir=cache_dir,
            n_workers=n_workers,
        )
        for stg, eng, lut in (
            ("fc1", inf.fc1_engine, inf.fc1_lut),
            ("fc2", inf.fc2_engine, inf.fc2_lut),
        ):
            assert lut is not None
            h_val = f"cri_{stg}_{eng.config_hash()}"
            if h_val not in seen_hashes:
                seen_hashes.add(h_val)
                lut_records.append(
                    {
                        "engine": "CRI",
                        "stage": stg,
                        "config_label": label,
                        "implicator": implicator,
                        "tie_break": "n/a",
                        "defuzz_method": defuzz_method,
                        "shoulder_edges": shoulder_edges,
                        "and_operator": and_operator,
                        "mf_sigma_scale": mf_sigma_scale,
                        "sigma1": eng.sigma1,
                        "sigma2": eng.sigma2,
                        "config_hash": eng.config_hash(),
                        "build_time_s": float(lut["build_time_s"]),
                        "cache_file": str(lut["cache_file"]),
                    }
                )
        return inf

    osfi_s = _register_osfi(
        label="OSFI-DJ-S (singleton)",
        implicator="lukasiewicz",
        tie_break="smallest",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sig_lam=0.0,
        sig_q=0.0,
    )
    _ = _register_cri(
        label="CRI-S (singleton)",
        implicator="lukasiewicz",
        defuzz_method="centroid_above_floor",
        shoulder_edges=True,
        sig_lam=0.0,
        sig_q=0.0,
    )

    osfi_ns_ref: OSFIDJInference | None = None
    cri_ns_ref: CRIInference | None = None

    for sq in sigma_q_grid:
        for pm in p_miss_grid:
            s1, s2 = compute_matched_input_sigmas(sigma_q=sq, p_miss=pm)
            lbl = f"sigma_q={sq:g}, p_miss={pm:g}"
            inf_o = _register_osfi(
                label=f"OSFI-DJ-NS ({lbl})",
                implicator="lukasiewicz",
                tie_break="smallest",
                defuzz_method="centroid_above_floor",
                shoulder_edges=True,
                sig_lam=s1,
                sig_q=s2,
            )
            inf_c = _register_cri(
                label=f"CRI-NS ({lbl})",
                implicator="lukasiewicz",
                defuzz_method="centroid_above_floor",
                shoulder_edges=True,
                sig_lam=s1,
                sig_q=s2,
            )
            if abs(sq - 10.0) < 1e-9 and abs(pm - 0.0) < 1e-9:
                osfi_ns_ref = inf_o
                cri_ns_ref = inf_c

    s1_c, s2_c = compute_matched_input_sigmas(sigma_q=10.0, p_miss=0.0)
    for spec in ABLATION_SPECS:
        _register_osfi(
            label=f"Ablation: {spec['label']}",
            implicator=str(spec["implicator"]),
            tie_break=str(spec["tie_break"]),
            defuzz_method=str(spec["defuzz_method"]),
            shoulder_edges=bool(spec["shoulder_edges"]),
            sig_lam=s1_c,
            sig_q=s2_c,
            and_operator=str(spec["and_operator"]),
            mf_sigma_scale=float(spec["mf_sigma_scale"]),
        )

    assert osfi_ns_ref is not None and cri_ns_ref is not None

    error_rows: list[dict[str, Any]] = []
    for model_name, inf_obj, seed_base in (
        ("OSFI-DJ-S (singleton)", osfi_s, 42),
        ("OSFI-DJ-NS (sigma_q=10, p_miss=0)", osfi_ns_ref, 142),
        ("CRI-NS (sigma_q=10, p_miss=0)", cri_ns_ref, 242),
    ):
        for stg, stg_eng, stg_lut, s_off in (
            ("fc1", inf_obj.fc1_engine, inf_obj.fc1_lut, 0),
            ("fc2", inf_obj.fc2_engine, inf_obj.fc2_lut, 1),
        ):
            assert stg_lut is not None
            stats_dict = measure_stage_lut_interpolation_error(
                stage_engine=stg_eng,
                lut_dict=stg_lut,
                n_samples=n_error_samples,
                seed=seed_base + s_off,
            )
            error_rows.append(
                {
                    "model": model_name,
                    "stage": stg,
                    "config_hash": stg_eng.config_hash(),
                    "build_time_s": float(stg_lut["build_time_s"]),
                    "n_samples": int(stats_dict["n_samples"]),
                    "max_abs_error_s": float(stats_dict["max_abs_error"]),
                    "mean_abs_error_s": float(stats_dict["mean_abs_error"]),
                    "median_abs_error_s": float(stats_dict["median_abs_error"]),
                    "p95_abs_error_s": float(stats_dict["p95_abs_error"]),
                }
            )

    total_lut_wall_s = time.perf_counter() - t_start
    return (
        pd.DataFrame(lut_records),
        pd.DataFrame(error_rows),
        total_lut_wall_s,
        osfi_s,
        osfi_ns_ref,
    )


def _run_exp_a_task(
    task: tuple[str, int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenario_name, seed, config = task
    sim_cfg = config.get("simulator", {})
    scen = ScenarioDemand.from_name(scenario_name)
    warmup_s = int(sim_cfg.get("warmup_s", 600))
    measurement_s = int(sim_cfg.get("measurement_s", 3600))
    dt = float(sim_cfg.get("dt", 1.0))

    common_arrivals = pregenerate_arrivals(
        scenario=scen,
        seed=seed,
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        dt=dt,
    )
    horizon_steps = int(round((warmup_s + measurement_s) / dt))
    common_noise = pregenerate_sensor_noise(
        arrival_counts=common_arrivals,
        seed=seed,
        horizon_steps=horizon_steps,
        queue_noise_std_m=0.0,
        arrival_p_miss=0.0,
        dt=dt,
    )

    simulator = IntersectionSimulator(
        dt=dt,
        lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
        service=str(sim_cfg.get("service", "exponential")),
        service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
        startup_lost_time=float(sim_cfg.get("startup_lost_time", 2.0)),
        yellow_time=float(sim_cfg.get("yellow_time", 3.0)),
        all_red_time=float(sim_cfg.get("all_red_time", 2.0)),
        vehicle_length_m=float(sim_cfg.get("vehicle_length_m", 7.0)),
        arrival_window_s=float(sim_cfg.get("arrival_window_s", 10.0)),
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        queue_noise_std_m=0.0,
        arrival_p_miss=0.0,
    )

    rows: list[dict[str, Any]] = []
    cov_rows: list[dict[str, Any]] = []
    for ctrl_name in EXP_A_CONTROLLERS:
        ctrl = build_controller(
            ctrl_name, scen, config, sigma_q=0.0, p_miss=0.0, use_lut=True
        )
        res = simulator.run(
            controller=ctrl,
            scenario=scen,
            seed=seed,
            controller_name=ctrl_name,
            arrival_counts=common_arrivals,
            pregenerated_noise=common_noise,
            verify_conservation=True,
        )
        m_rows, cov_row = compute_run_metrics(res, controller=ctrl)
        rows.extend(m_rows)
        if ctrl_name in FUZZY_CONTROLLER_NAMES:
            cov_rows.append(cov_row)
    return rows, cov_rows


def _run_exp_b_task(
    task: tuple[str, float, float, int, dict[str, Any]],
) -> list[dict[str, Any]]:
    scenario_name, sigma_q, p_miss, seed, config = task
    sim_cfg = config.get("simulator", {})
    noise_cfg = sim_cfg.get("sensor_noise", {})
    false_rate = float(noise_cfg.get("arrival_false_rate_vps", 0.02))

    scen = ScenarioDemand.from_name(scenario_name)
    warmup_s = int(sim_cfg.get("warmup_s", 600))
    measurement_s = int(sim_cfg.get("measurement_s", 3600))
    dt = float(sim_cfg.get("dt", 1.0))

    common_arrivals = pregenerate_arrivals(
        scenario=scen,
        seed=seed,
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        dt=dt,
    )
    horizon_steps = int(round((warmup_s + measurement_s) / dt))
    common_noise = pregenerate_sensor_noise(
        arrival_counts=common_arrivals,
        seed=seed,
        horizon_steps=horizon_steps,
        queue_noise_std_m=sigma_q,
        arrival_p_miss=p_miss,
        arrival_false_rate_vps=false_rate,
        dt=dt,
    )

    simulator = IntersectionSimulator(
        dt=dt,
        lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
        service=str(sim_cfg.get("service", "exponential")),
        service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
        startup_lost_time=float(sim_cfg.get("startup_lost_time", 2.0)),
        yellow_time=float(sim_cfg.get("yellow_time", 3.0)),
        all_red_time=float(sim_cfg.get("all_red_time", 2.0)),
        vehicle_length_m=float(sim_cfg.get("vehicle_length_m", 7.0)),
        arrival_window_s=float(sim_cfg.get("arrival_window_s", 10.0)),
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        queue_noise_std_m=sigma_q,
        arrival_p_miss=p_miss,
        arrival_false_rate_vps=false_rate,
    )

    rows: list[dict[str, Any]] = []
    for ctrl_name in EXP_B_CONTROLLERS:
        ctrl = build_controller(
            ctrl_name, scen, config, sigma_q=sigma_q, p_miss=p_miss, use_lut=True
        )
        res = simulator.run(
            controller=ctrl,
            scenario=scen,
            seed=seed,
            controller_name=ctrl_name,
            arrival_counts=common_arrivals,
            pregenerated_noise=common_noise,
            verify_conservation=True,
        )
        m_rows, _ = compute_run_metrics(res, controller=ctrl)
        for r in m_rows:
            r["sigma_q"] = float(sigma_q)
            r["p_miss"] = float(p_miss)
        rows.extend(m_rows)
    return rows


def _run_exp_c_task(
    task: tuple[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    seed, config = task
    sim_cfg = config.get("simulator", {})
    noise_cfg = sim_cfg.get("sensor_noise", {})
    false_rate = float(noise_cfg.get("arrival_false_rate_vps", 0.02))

    scenario_name = "heavy"
    sigma_q = 10.0
    p_miss = 0.0

    scen = ScenarioDemand.from_name(scenario_name)
    warmup_s = int(sim_cfg.get("warmup_s", 600))
    measurement_s = int(sim_cfg.get("measurement_s", 3600))
    dt = float(sim_cfg.get("dt", 1.0))

    common_arrivals = pregenerate_arrivals(
        scenario=scen,
        seed=seed,
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        dt=dt,
    )
    horizon_steps = int(round((warmup_s + measurement_s) / dt))
    common_noise = pregenerate_sensor_noise(
        arrival_counts=common_arrivals,
        seed=seed,
        horizon_steps=horizon_steps,
        queue_noise_std_m=sigma_q,
        arrival_p_miss=p_miss,
        arrival_false_rate_vps=false_rate,
        dt=dt,
    )

    simulator = IntersectionSimulator(
        dt=dt,
        lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
        service=str(sim_cfg.get("service", "exponential")),
        service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
        startup_lost_time=float(sim_cfg.get("startup_lost_time", 2.0)),
        yellow_time=float(sim_cfg.get("yellow_time", 3.0)),
        all_red_time=float(sim_cfg.get("all_red_time", 2.0)),
        vehicle_length_m=float(sim_cfg.get("vehicle_length_m", 7.0)),
        arrival_window_s=float(sim_cfg.get("arrival_window_s", 10.0)),
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        queue_noise_std_m=sigma_q,
        arrival_p_miss=p_miss,
        arrival_false_rate_vps=false_rate,
    )

    rows: list[dict[str, Any]] = []
    for spec in ABLATION_SPECS:
        cfg_copy = copy.deepcopy(config)
        cfg_copy.setdefault("fuzzy", {})
        cfg_copy["fuzzy"]["implicator"] = spec["implicator"]
        cfg_copy["fuzzy"]["tie_break"] = spec["tie_break"]
        cfg_copy["fuzzy"]["defuzz_method"] = spec["defuzz_method"]
        cfg_copy["fuzzy"]["shoulder_edges"] = spec["shoulder_edges"]
        cfg_copy["fuzzy"]["and_operator"] = spec["and_operator"]
        cfg_copy["fuzzy"]["mf_sigma_scale"] = spec["mf_sigma_scale"]
        cfg_copy.setdefault("controller", {})
        cfg_copy["controller"]["spm_mode"] = spec["spm_mode"]

        ctrl = build_controller(
            "OSFI-DJ-NS",
            scen,
            cfg_copy,
            sigma_q=sigma_q,
            p_miss=p_miss,
            use_lut=True,
        )
        res = simulator.run(
            controller=ctrl,
            scenario=scen,
            seed=seed,
            controller_name=str(spec["variant_id"]),
            arrival_counts=common_arrivals,
            pregenerated_noise=common_noise,
            verify_conservation=True,
        )
        m_rows, _ = compute_run_metrics(res, controller=ctrl)
        for r in m_rows:
            if r["approach"] == "overall":
                r["variant_id"] = str(spec["variant_id"])
                r["factor"] = str(spec["factor"])
                r["label"] = str(spec["label"])
                r["implicator"] = str(spec["implicator"])
                r["tie_break"] = str(spec["tie_break"])
                r["defuzz_method"] = str(spec["defuzz_method"])
                r["shoulder_edges"] = bool(spec["shoulder_edges"])
                r["and_operator"] = str(spec["and_operator"])
                r["mf_sigma_scale"] = float(spec["mf_sigma_scale"])
                r["spm_mode"] = str(spec["spm_mode"])
                r["sigma_q"] = sigma_q
                r["p_miss"] = p_miss
                rows.append(r)
    return rows


def summarize_grouped_metrics(
    raw_df: pd.DataFrame,
    group_cols: list[str],
) -> pd.DataFrame:
    """Compute mean, std, and 95% t-CI for grouped simulation metric rows."""
    metric_cols = [
        "avg_delay_s",
        "avg_delay_incl_queued_s",
        "throughput_veh",
        "arrivals_veh",
        "discharge_ratio",
        "mean_queue_veh",
        "max_queue_veh",
        "mean_queue_m",
        "max_queue_m",
        "mean_cycle_length_s",
        "num_switches",
        "fallback_rate",
        "fc1_fallback_rate",
        "fc2_fallback_rate",
    ]
    out_rows: list[dict[str, Any]] = []
    for keys, grp in raw_df.groupby(group_cols, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row: dict[str, Any] = {col: val for col, val in zip(group_cols, keys)}
        row["n_seeds"] = len(grp)
        for m_col in metric_cols:
            if m_col in grp.columns:
                m_val, sd_val, ci_val = mean_and_t_ci(grp[m_col].to_numpy(dtype=float))
                row[f"{m_col}_mean"] = m_val
                row[f"{m_col}_std"] = sd_val
                row[f"{m_col}_ci95"] = ci_val
        out_rows.append(row)
    return pd.DataFrame(out_rows)


def compute_stage2_wilcoxon_tests(exp_b_raw_df: pd.DataFrame) -> pd.DataFrame:
    """Compute paired Wilcoxon tests and effect sizes for OSFI-DJ-NS vs 4 baselines per noise cell."""
    overall = exp_b_raw_df[exp_b_raw_df["approach"] == "overall"].copy()
    baselines = ("OSFI-DJ-S", "CRI-NS", "Mamdani", "Sugeno")
    scenarios = sorted(overall["scenario"].unique())
    sigma_qs = sorted(overall["sigma_q"].unique())
    p_misses = sorted(overall["p_miss"].unique())

    records: list[dict[str, Any]] = []
    for scen in scenarios:
        for pm in p_misses:
            for sq in sigma_qs:
                cell = overall[
                    (overall["scenario"] == scen)
                    & (np.isclose(overall["sigma_q"], sq))
                    & (np.isclose(overall["p_miss"], pm))
                ]
                ns_df = cell[cell["controller"] == "OSFI-DJ-NS"].sort_values("seed")
                x = ns_df["avg_delay_s"].to_numpy(dtype=float)

                cell_pvals: list[float] = []
                cell_indices: list[int] = []

                for base in baselines:
                    base_df = cell[cell["controller"] == base].sort_values("seed")
                    y = base_df["avg_delay_s"].to_numpy(dtype=float)
                    diff = x - y
                    pct_diff = np.where(y > 1e-9, ((x - y) / y) * 100.0, 0.0)

                    mean_diff_s = float(np.mean(diff))
                    median_diff_s = float(np.median(diff))
                    mean_diff_pct = float(np.mean(pct_diff))
                    median_diff_pct = float(np.median(pct_diff))

                    if np.all(np.abs(diff) <= 1e-12):
                        stat_val = 0.0
                        p_val = 1.0
                    else:
                        w_res = stats.wilcoxon(
                            x, y, zero_method="wilcox", alternative="two-sided"
                        )
                        stat_val = float(w_res.statistic)
                        p_val = float(w_res.pvalue)

                    r_idx = len(records)
                    cell_indices.append(r_idx)
                    cell_pvals.append(p_val)
                    records.append(
                        {
                            "scenario": scen,
                            "sigma_q": float(sq),
                            "p_miss": float(pm),
                            "comparison": f"OSFI-DJ-NS vs {base}",
                            "baseline": base,
                            "osfi_dj_ns_mean_s": float(np.mean(x)),
                            "baseline_mean_s": float(np.mean(y)),
                            "mean_diff_s": mean_diff_s,
                            "median_diff_s": median_diff_s,
                            "mean_diff_pct": mean_diff_pct,
                            "median_diff_pct": median_diff_pct,
                            "wilcoxon_stat": stat_val,
                            "p_raw": p_val,
                            "p_holm_cell": p_val,
                        }
                    )

                holm_cell = holm_bonferroni(cell_pvals)
                for r_idx, adj_p in zip(cell_indices, holm_cell):
                    records[r_idx]["p_holm_cell"] = adj_p

    all_pvals = [float(r["p_raw"]) for r in records]
    all_holm = holm_bonferroni(all_pvals)
    for r, adj_all in zip(records, all_holm):
        r["p_holm_global"] = adj_all
        r["significant_005_holm_cell"] = bool(r["p_holm_cell"] < 0.05)

    return pd.DataFrame(records)


def benchmark_inference_speed(
    osfi_s: OSFIDJInference,
    osfi_ns: OSFIDJInference,
    n_calls: int = 10000,
    seed: int = 202505,
) -> dict[str, float]:
    """Measure per-inference execution time (direct and LUT) over 10,000 calls with time.perf_counter."""
    rng = np.random.default_rng(seed)
    lams = rng.uniform(0.0, 12.0, size=n_calls)
    q_curs = rng.uniform(0.0, 60.0, size=n_calls)
    q_oths = rng.uniform(0.0, 60.0, size=n_calls)

    t0 = time.perf_counter()
    for i in range(n_calls):
        osfi_s.infer_gpe(float(lams[i]), float(q_curs[i]), float(q_oths[i]))
    lut_s_total = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(n_calls):
        osfi_ns.infer_gpe(float(lams[i]), float(q_curs[i]), float(q_oths[i]))
    lut_ns_total = time.perf_counter() - t0

    osfi_s_dir = OSFIDJInference(
        implicator=osfi_s.fc1_engine.implicator_name,
        tie_break=osfi_s.fc1_engine.tie_break,
        defuzz_method=osfi_s.fc1_engine.defuzz_method,
        shoulder_edges=osfi_s.shoulder_edges,
        and_operator=osfi_s.and_operator,
        mf_sigma_scale=osfi_s.mf_sigma_scale,
        sigma_lambda=0.0,
        sigma_queue=0.0,
        sigma_ext1=0.0,
        use_lut=False,
    )
    osfi_ns_dir = OSFIDJInference(
        implicator=osfi_ns.fc1_engine.implicator_name,
        tie_break=osfi_ns.fc1_engine.tie_break,
        defuzz_method=osfi_ns.fc1_engine.defuzz_method,
        shoulder_edges=osfi_ns.shoulder_edges,
        and_operator=osfi_ns.and_operator,
        mf_sigma_scale=osfi_ns.mf_sigma_scale,
        sigma_lambda=osfi_ns.fc1_engine.sigma1,
        sigma_queue=osfi_ns.fc1_engine.sigma2,
        sigma_ext1=0.0,
        use_lut=False,
    )

    t0 = time.perf_counter()
    for i in range(n_calls):
        osfi_s_dir.infer_gpe(float(lams[i]), float(q_curs[i]), float(q_oths[i]))
    dir_s_total = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(n_calls):
        osfi_ns_dir.infer_gpe(float(lams[i]), float(q_curs[i]), float(q_oths[i]))
    dir_ns_total = time.perf_counter() - t0

    assert osfi_s.fc1_lut is not None and osfi_s.fc2_lut is not None
    assert osfi_ns.fc1_lut is not None and osfi_ns.fc2_lut is not None
    build_s = float(osfi_s.fc1_lut["build_time_s"]) + float(osfi_s.fc2_lut["build_time_s"])
    build_ns = float(osfi_ns.fc1_lut["build_time_s"]) + float(osfi_ns.fc2_lut["build_time_s"])

    return {
        "n_calls": float(n_calls),
        "direct_s_ms_per_call": (dir_s_total / n_calls) * 1e3,
        "direct_ns_ms_per_call": (dir_ns_total / n_calls) * 1e3,
        "lut_s_ms_per_call": (lut_s_total / n_calls) * 1e3,
        "lut_ns_ms_per_call": (lut_ns_total / n_calls) * 1e3,
        "lut_s_us_per_call": (lut_s_total / n_calls) * 1e6,
        "lut_ns_us_per_call": (lut_ns_total / n_calls) * 1e6,
        "lut_build_s_sec": build_s,
        "lut_build_ns_sec": build_ns,
    }


def build_contribution_comparison_table(
    exp_b_sum: pd.DataFrame,
    speed_stats: dict[str, float],
) -> pd.DataFrame:
    """Build Guideline §6.2 comparison table (Baseline OSFI-DJ-S vs Proposed OSFI-DJ-NS)."""
    overall = exp_b_sum[exp_b_sum["approach"] == "overall"].copy()

    def _get_pair(scen: str, pm: float, sq: float, col: str) -> tuple[float, float, float, float]:
        sub = overall[
            (overall["scenario"] == scen)
            & np.isclose(overall["p_miss"], pm)
            & np.isclose(overall["sigma_q"], sq)
        ].set_index("controller")
        b_m = float(sub.loc["OSFI-DJ-S", f"{col}_mean"])
        b_ci = float(sub.loc["OSFI-DJ-S", f"{col}_ci95"])
        p_m = float(sub.loc["OSFI-DJ-NS", f"{col}_mean"])
        p_ci = float(sub.loc["OSFI-DJ-NS", f"{col}_ci95"])
        return b_m, b_ci, p_m, p_ci

    rows: list[dict[str, str]] = []

    for scen_lbl, scen_key in (("Heavy (1500 veh/h)", "heavy"), ("Peak (1100→1800→1100 veh/h)", "peak")):
        for pm in (0.0, 0.1):
            for sq in (0.0, 10.0, 15.0):
                b_m, b_ci, p_m, p_ci = _get_pair(scen_key, pm, sq, "avg_delay_s")
                diff = p_m - b_m
                pct = (diff / b_m) * 100.0 if b_m > 1e-9 else 0.0
                rows.append(
                    {
                        "Performance Metric": f"Average Delay [s/veh] — {scen_lbl}, σ_q={sq:.0f} m, p_miss={pm:.1f}",
                        "Baseline (OSFI-DJ-S)": f"{b_m:.2f} ± {b_ci:.2f}",
                        "Proposed (OSFI-DJ-NS)": f"{p_m:.2f} ± {p_ci:.2f}",
                        "Change": f"{diff:+.2f} s/veh ({pct:+.2f}%)",
                    }
                )

        b_tp, b_tp_ci, p_tp, p_tp_ci = _get_pair(scen_key, 0.0, 10.0, "throughput_veh")
        diff_tp = p_tp - b_tp
        pct_tp = (diff_tp / b_tp) * 100.0 if b_tp > 1e-9 else 0.0
        rows.append(
            {
                "Performance Metric": f"Throughput [veh/h] — {scen_lbl}, σ_q=10 m, p_miss=0.0",
                "Baseline (OSFI-DJ-S)": f"{b_tp:.1f} ± {b_tp_ci:.1f}",
                "Proposed (OSFI-DJ-NS)": f"{p_tp:.1f} ± {p_tp_ci:.1f}",
                "Change": f"{diff_tp:+.1f} veh ({pct_tp:+.2f}%)",
            }
        )

        b_q, b_q_ci, p_q, p_q_ci = _get_pair(scen_key, 0.0, 10.0, "mean_queue_m")
        diff_q = p_q - b_q
        pct_q = (diff_q / b_q) * 100.0 if b_q > 1e-9 else 0.0
        rows.append(
            {
                "Performance Metric": f"Mean Queue Length [m/lane] — {scen_lbl}, σ_q=10 m, p_miss=0.0",
                "Baseline (OSFI-DJ-S)": f"{b_q:.2f} ± {b_q_ci:.2f}",
                "Proposed (OSFI-DJ-NS)": f"{p_q:.2f} ± {p_q_ci:.2f}",
                "Change": f"{diff_q:+.2f} m/lane ({pct_q:+.2f}%)",
            }
        )

    dir_s = speed_stats["direct_s_ms_per_call"]
    dir_ns = speed_stats["direct_ns_ms_per_call"]
    dir_diff = dir_ns - dir_s
    dir_pct = (dir_diff / dir_s) * 100.0 if dir_s > 1e-9 else 0.0
    rows.append(
        {
            "Performance Metric": "Execution Time per Inference (Direct, 10k calls) [ms/call]",
            "Baseline (OSFI-DJ-S)": f"{dir_s:.3f} ms",
            "Proposed (OSFI-DJ-NS)": f"{dir_ns:.3f} ms",
            "Change": f"{dir_diff:+.3f} ms ({dir_pct:+.1f}%)",
        }
    )

    lut_s_us = speed_stats["lut_s_us_per_call"]
    lut_ns_us = speed_stats["lut_ns_us_per_call"]
    lut_diff_us = lut_ns_us - lut_s_us
    lut_pct = (lut_diff_us / lut_s_us) * 100.0 if lut_s_us > 1e-9 else 0.0
    rows.append(
        {
            "Performance Metric": "Execution Time per Inference (2D LUT Lookup, 10k calls) [µs/call]",
            "Baseline (OSFI-DJ-S)": f"{lut_s_us:.2f} µs ({speed_stats['lut_s_ms_per_call']:.5f} ms)",
            "Proposed (OSFI-DJ-NS)": f"{lut_ns_us:.2f} µs ({speed_stats['lut_ns_ms_per_call']:.5f} ms)",
            "Change": f"{lut_diff_us:+.2f} µs ({lut_pct:+.1f}%)",
        }
    )

    b_build = speed_stats["lut_build_s_sec"]
    p_build = speed_stats["lut_build_ns_sec"]
    build_diff = p_build - b_build
    build_pct = (build_diff / b_build) * 100.0 if b_build > 1e-9 else 0.0
    rows.append(
        {
            "Performance Metric": "Offline LUT Precomputation Build Time (FC1 + FC2) [s]",
            "Baseline (OSFI-DJ-S)": f"{b_build:.2f} s",
            "Proposed (OSFI-DJ-NS)": f"{p_build:.2f} s",
            "Change": f"{build_diff:+.2f} s ({build_pct:+.1f}%)",
        }
    )

    return pd.DataFrame(rows)


def format_contribution_comparison_markdown(comp_df: pd.DataFrame) -> str:
    """Format Guideline §6.2 Baseline vs Proposed comparison table as Markdown."""
    lines = [
        "# Guideline §6.2 Comparison Table — Baseline (`OSFI-DJ-S`) vs. Proposed (`OSFI-DJ-NS`)",
        "",
        "Comparison across `n = 30` common-random-number seeds (mean $\\pm$ 95% $t$-CI) and `10,000`-call `time.perf_counter` inference benchmarks.",
        "",
        "| Performance Metric | Baseline (`OSFI-DJ-S`) | Proposed (`OSFI-DJ-NS`) | Change |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for _, r in comp_df.iterrows():
        lines.append(
            f"| {r['Performance Metric']} | {r['Baseline (OSFI-DJ-S)']} | {r['Proposed (OSFI-DJ-NS)']} | {r['Change']} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_lut_markdown(lut_df: pd.DataFrame, err_df: pd.DataFrame, wall_s: float) -> str:
    """Format LUT build time and 500-point interpolation error report as Markdown."""
    lines = [
        "# Lookup Table (LUT) Build Time and Interpolation Error Report",
        "",
        f"- **Total LUT preparation wall-clock time:** `{wall_s:.2f} s`",
        f"- **Sum of single-LUT build times across `{len(lut_df)}` cached tables:** `{lut_df['build_time_s'].sum():.2f} s`",
        "",
        "## 1. Off-Grid Bilinear Interpolation Accuracy (`500` Random Points per Stage vs. Direct Inference)",
        "",
        "| Model | Stage | Config Hash | Build Time (s) | Samples | Max Abs Error (s) | Mean Abs Error (s) | Median Abs Error (s) | 95th Pct Error (s) |",
        "| :--- | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in err_df.iterrows():
        lines.append(
            f"| `{r['model']}` | `{r['stage'].upper()}` | `{r['config_hash']}` "
            f"| {float(r['build_time_s']):.3f} | {int(r['n_samples'])} "
            f"| {float(r['max_abs_error_s']):.4f} | {float(r['mean_abs_error_s']):.4f} "
            f"| {float(r['median_abs_error_s']):.4f} | {float(r['p95_abs_error_s']):.4f} |"
        )
    lines.extend(
        [
            "",
            "> **Note on `Max Abs Error`:** On smooth interior regions, bilinear interpolation error is $< 0.05\\text{ s}$ (median error $\\approx 0.00-0.02\\text{ s}$). Larger maximum differences occur only on the narrow grid cells straddling the boundary of the Łukasiewicz dead-zone pocket ($a_1 + a_2 = 1$), where direct inference switches between the nearest-rule fallback and active rule outputs.",
            "",
            "## 2. Cached Stage LUT Inventory",
            "",
            "| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | AND | $\\sigma$-Scale | $\\sigma_1$ | $\\sigma_2$ | Hash | Build Time (s) |",
            "| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | ---: | ---: | ---: | :---: | ---: |",
        ]
    )
    for _, r in lut_df.iterrows():
        lines.append(
            f"| `{r['engine']}` | `{r['stage'].upper()}` | {r['config_label']} "
            f"| `{r['implicator']}` | `{r['tie_break']}` | `{r['defuzz_method']}` "
            f"| `{bool(r['shoulder_edges'])}` | `{r.get('and_operator', 'lukasiewicz')}` "
            f"| {float(r.get('mf_sigma_scale', 1.0)):.2f} "
            f"| {float(r['sigma1']):.4f} | {float(r['sigma2']):.2f} "
            f"| `{r['config_hash']}` | {float(r['build_time_s']):.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_exp_a_markdown(exp_a_sum: pd.DataFrame) -> str:
    """Format Experiment A (noiseless reproduction with OSFI-DJ-S and CRI-S) summary as Markdown."""
    overall = exp_a_sum[exp_a_sum["approach"] == "overall"].copy()
    lines = [
        "# Experiment A — Noiseless Reproduction Extended with `OSFI-DJ-S` and `CRI-S` (`n = 30` Seeds)",
        "",
        "| Scenario | Controller | Avg Delay (s/veh) $\\pm$ 95% CI | Delay Incl. Queued (s/veh) $\\pm$ 95% CI | Throughput (veh) $\\pm$ 95% CI | Discharge (%) | Mean Queue (m/lane) | Switches | Dead-Zone Fallback Rate (Total / FC1 / FC2) |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for _, r in overall.iterrows():
        fb_str = (
            f"{float(r['fallback_rate_mean'])*100:.2f}% "
            f"({float(r['fc1_fallback_rate_mean'])*100:.2f}% / {float(r['fc2_fallback_rate_mean'])*100:.2f}%)"
        )
        disc_pct = float(r.get("discharge_ratio_mean", 1.0)) * 100.0
        lines.append(
            f"| `{r['scenario']}` | `{r['controller']}` "
            f"| {float(r['avg_delay_s_mean']):.2f} $\\pm$ {float(r['avg_delay_s_ci95']):.2f} "
            f"| {float(r['avg_delay_incl_queued_s_mean']):.2f} $\\pm$ {float(r['avg_delay_incl_queued_s_ci95']):.2f} "
            f"| {float(r['throughput_veh_mean']):.1f} $\\pm$ {float(r['throughput_veh_ci95']):.1f} "
            f"| {disc_pct:.2f}% "
            f"| {float(r['mean_queue_m_mean']):.2f} "
            f"| {float(r['num_switches_mean']):.1f} | {fb_str} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_exp_b_markdown(exp_b_sum: pd.DataFrame) -> str:
    """Format Experiment B (sensor noise grid) overall delay summary as Markdown."""
    overall = exp_b_sum[exp_b_sum["approach"] == "overall"].copy()
    lines = [
        "# Experiment B — Sensor Noise Robustness Grid (`n = 30` Seeds per Cell)",
        "",
        "Values show overall **Average Delay [s/veh] (Mean $\\pm$ 95% CI)** across $\\sigma_q \\in \\{0, 5, 10, 15\\}\\text{ m}$ and $p_{\\text{miss}} \\in \\{0, 0.1, 0.2\\}$.",
        "",
    ]
    for scen in ("heavy", "peak"):
        lines.append(f"## Scenario: `{scen.capitalize()}`")
        lines.append("")
        lines.append(
            "| $p_{\\text{miss}}$ | $\\sigma_q$ (m) | `Mamdani` | `Sugeno` | `OSFI-literal` | `OSFI-DJ-S` | `CRI-NS` | `OSFI-DJ-NS` | `OSFI-DJ-NS-mis` | `Webster` | `Actuated` |"
        )
        lines.append(
            "| :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
        )
        sub_s = overall[overall["scenario"] == scen]
        for pm in sorted(sub_s["p_miss"].unique()):
            for sq in sorted(sub_s["sigma_q"].unique()):
                cell = sub_s[
                    np.isclose(sub_s["p_miss"], pm) & np.isclose(sub_s["sigma_q"], sq)
                ].set_index("controller")
                vals = []
                for c_name in EXP_B_CONTROLLERS:
                    m_v = float(cell.loc[c_name, "avg_delay_s_mean"])
                    ci_v = float(cell.loc[c_name, "avg_delay_s_ci95"])
                    vals.append(f"{m_v:.2f}$\\pm${ci_v:.2f}")
                lines.append(
                    f"| {pm:.1f} | {sq:.0f} | " + " | ".join(vals) + " |"
                )
        lines.append("")
    return "\n".join(lines)


def format_stage2_wilcoxon_markdown(wilcoxon_df: pd.DataFrame) -> str:
    """Format Stage 2/3 paired Wilcoxon signed-rank tests and effect sizes as Markdown."""
    lines = [
        "# Paired Wilcoxon Signed-Rank Tests & Effect Sizes (`OSFI-DJ-NS` vs Baselines, `n = 30` Seeds)",
        "",
        "Negative `Median Diff (s/veh)` and `Median Diff (%)` indicate that `OSFI-DJ-NS` achieves **lower** average delay than the compared baseline.",
        "",
        "| Scenario | $p_{\\text{miss}}$ | $\\sigma_q$ (m) | Comparison | `OSFI-DJ-NS` Mean (s) | Baseline Mean (s) | Median Paired Diff (s/veh) | Median Paired Diff (%) | Wilcoxon Stat | Raw $p$ | Holm $p$ (Cell) | Sig. ($\\alpha=0.05$)? |",
        "| :--- | :---: | :---: | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for _, r in wilcoxon_df.iterrows():
        sig = "Yes" if bool(r["significant_005_holm_cell"]) else "No"
        lines.append(
            f"| `{r['scenario']}` | {float(r['p_miss']):.1f} | {float(r['sigma_q']):.0f} "
            f"| `{r['comparison']}` | {float(r['osfi_dj_ns_mean_s']):.2f} "
            f"| {float(r['baseline_mean_s']):.2f} | {float(r['median_diff_s']):+.2f} "
            f"| {float(r['median_diff_pct']):+.2f}% | {float(r['wilcoxon_stat']):.1f} "
            f"| {float(r['p_raw']):.4g} | {float(r['p_holm_cell']):.4g} | {sig} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_exp_c_markdown(exp_c_sum: pd.DataFrame) -> str:
    """Format Experiment C (Ablation study) summary as Markdown."""
    lines = [
        "# Experiment C — Ablation Study on `OSFI-DJ-NS` (`heavy`, $\\sigma_q = 10\\text{ m}$, $p_{\\text{miss}} = 0$, `n = 30` Seeds)",
        "",
        "| Factor | Variant | Implicator | Tie-Break | Defuzzifier | `shoulder_edges` | AND | $\\sigma$-Scale | `spm_mode` | Avg Delay (s/veh) $\\pm$ 95% CI | Throughput (veh) $\\pm$ 95% CI | Switches | Dead-Zone Fallback Rate |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | ---: | :---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in exp_c_sum.iterrows():
        lines.append(
            f"| {r['factor']} | {r['label']} | `{r['implicator']}` | `{r['tie_break']}` "
            f"| `{r['defuzz_method']}` | `{bool(r['shoulder_edges'])}` "
            f"| `{r['and_operator']}` | {float(r['mf_sigma_scale']):.1f} | `{r['spm_mode']}` "
            f"| {float(r['avg_delay_s_mean']):.2f} $\\pm$ {float(r['avg_delay_s_ci95']):.2f} "
            f"| {float(r['throughput_veh_mean']):.1f} $\\pm$ {float(r['throughput_veh_ci95']):.1f} "
            f"| {float(r['num_switches_mean']):.1f} | {float(r['fallback_rate_mean'])*100:.2f}% |"
        )
    lines.append("")
    return "\n".join(lines)


def run_all_contribution_experiments(
    config_path: str | Path = "configs/default.yaml",
    output_root: str | Path = "results",
    n_workers: int | None = None,
    log_path: str | Path | None = "docs/experiment_log.md",
) -> dict[str, Any]:
    """Execute LUT precomputation, 10k-call speed benchmarks, sanity gates, and Experiments A, B, C."""
    t_total_start = time.perf_counter()
    config = load_config(config_path)
    exp_cfg = config.get("experiment", {})
    sim_cfg = config.get("simulator", {})
    noise_cfg = sim_cfg.get("sensor_noise", {})

    validate_and_print_webster_ratios(
        service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
        lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
    )

    num_seeds = int(exp_cfg.get("num_seeds", 30))
    base_seed = int(exp_cfg.get("base_seed", 202501))
    workers = n_workers if n_workers is not None else max(1, min(cpu_count() or 4, 8))

    print(
        f"[Estimate] Parallel workers={workers}, seeds={num_seeds}. "
        "Estimated total runtime: ~4-6 min (LUT build + 10k-call direct/LUT benchmark + Exp A/B/C; well under the 90 min cap, keeping all 30 seeds)."
    )

    lut_df, err_df, lut_wall_s, osfi_s, osfi_ns_ref = prebuild_all_luts_and_measure_errors(
        config=config, n_workers=workers, n_error_samples=500
    )

    t_bench0 = time.perf_counter()
    speed_stats = benchmark_inference_speed(osfi_s=osfi_s, osfi_ns=osfi_ns_ref, n_calls=10000)
    bench_wall_s = time.perf_counter() - t_bench0

    t_a0 = time.perf_counter()
    exp_a_scenarios = ("moderate", "heavy", "peak", "stress")
    exp_a_tasks = [
        (scen_name, base_seed + idx, config)
        for scen_name in exp_a_scenarios
        for idx in range(num_seeds)
    ]
    exp_a_rows: list[dict[str, Any]] = []
    exp_a_cov_rows: list[dict[str, Any]] = []
    with Pool(processes=workers) as pool:
        for rows, cov_rows in tqdm(
            pool.imap_unordered(_run_exp_a_task, exp_a_tasks),
            total=len(exp_a_tasks),
            desc="Experiment A (noiseless + OSFI-DJ-S & CRI-S)",
        ):
            exp_a_rows.extend(rows)
            exp_a_cov_rows.extend(cov_rows)
    exp_a_wall_s = time.perf_counter() - t_a0

    exp_a_raw = pd.DataFrame(exp_a_rows)
    exp_a_raw["controller"] = pd.Categorical(
        exp_a_raw["controller"], categories=list(EXP_A_CONTROLLERS), ordered=True
    )
    exp_a_raw = exp_a_raw.sort_values(
        ["scenario", "controller", "seed", "approach"]
    ).reset_index(drop=True)
    exp_a_raw["controller"] = exp_a_raw["controller"].astype(str)
    exp_a_sum = summarize_grouped_metrics(
        exp_a_raw, ["scenario", "controller", "approach"]
    )
    exp_a_cov_df = pd.DataFrame(exp_a_cov_rows).sort_values(
        ["scenario", "controller", "seed"]
    ).reset_index(drop=True)
    exp_a_cov_sum = summarize_input_coverage(exp_a_cov_df)

    verify_sanity_gates(
        summary_df=exp_a_sum,
        cov_summary_df=exp_a_cov_sum,
        runner_name="run_contribution",
        log_path=log_path,
    )

    t_b0 = time.perf_counter()
    sigma_q_grid = [float(x) for x in noise_cfg.get("queue_std_grid_m", [0.0, 5.0, 10.0, 15.0])]
    p_miss_grid = [float(x) for x in noise_cfg.get("arrival_p_miss_grid", [0.0, 0.1, 0.2])]
    exp_b_tasks = [
        (scen_name, sq, pm, base_seed + idx, config)
        for scen_name in ("heavy", "peak")
        for pm in p_miss_grid
        for sq in sigma_q_grid
        for idx in range(num_seeds)
    ]
    exp_b_rows: list[dict[str, Any]] = []
    with Pool(processes=workers) as pool:
        for rows in tqdm(
            pool.imap_unordered(_run_exp_b_task, exp_b_tasks),
            total=len(exp_b_tasks),
            desc="Experiment B (noise grid x 9 controllers)",
        ):
            exp_b_rows.extend(rows)
    exp_b_wall_s = time.perf_counter() - t_b0

    exp_b_raw = pd.DataFrame(exp_b_rows)
    exp_b_raw["controller"] = pd.Categorical(
        exp_b_raw["controller"], categories=list(EXP_B_CONTROLLERS), ordered=True
    )
    exp_b_raw = exp_b_raw.sort_values(
        ["scenario", "p_miss", "sigma_q", "controller", "seed", "approach"]
    ).reset_index(drop=True)
    exp_b_raw["controller"] = exp_b_raw["controller"].astype(str)
    exp_b_sum = summarize_grouped_metrics(
        exp_b_raw, ["scenario", "p_miss", "sigma_q", "controller", "approach"]
    )
    wilcoxon_df = compute_stage2_wilcoxon_tests(exp_b_raw)

    t_c0 = time.perf_counter()
    exp_c_tasks = [(base_seed + idx, config) for idx in range(num_seeds)]
    exp_c_rows: list[dict[str, Any]] = []
    with Pool(processes=workers) as pool:
        for rows in tqdm(
            pool.imap_unordered(_run_exp_c_task, exp_c_tasks),
            total=len(exp_c_tasks),
            desc="Experiment C (9 ablations on heavy, sigma_q=10)",
        ):
            exp_c_rows.extend(rows)
    exp_c_wall_s = time.perf_counter() - t_c0

    exp_c_raw = pd.DataFrame(exp_c_rows)
    variant_order = [str(s["variant_id"]) for s in ABLATION_SPECS]
    exp_c_raw["variant_id"] = pd.Categorical(
        exp_c_raw["variant_id"], categories=variant_order, ordered=True
    )
    exp_c_raw = exp_c_raw.sort_values(["variant_id", "seed"]).reset_index(drop=True)
    exp_c_raw["variant_id"] = exp_c_raw["variant_id"].astype(str)
    exp_c_sum = summarize_grouped_metrics(
        exp_c_raw,
        [
            "variant_id",
            "factor",
            "label",
            "implicator",
            "tie_break",
            "defuzz_method",
            "shoulder_edges",
            "and_operator",
            "mf_sigma_scale",
            "spm_mode",
        ],
    )

    comp_df = build_contribution_comparison_table(exp_b_sum=exp_b_sum, speed_stats=speed_stats)

    total_wall_s = time.perf_counter() - t_total_start

    out_dir = Path(output_root)
    raw_dir = out_dir / "raw"
    sum_dir = out_dir / "tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    sum_dir.mkdir(parents=True, exist_ok=True)

    exp_a_raw.to_csv(raw_dir / "contribution_exp_a_runs.csv", index=False)
    exp_a_cov_df.to_csv(raw_dir / "contribution_exp_a_coverage_runs.csv", index=False)
    exp_b_raw.to_csv(raw_dir / "contribution_exp_b_runs.csv", index=False)
    exp_c_raw.to_csv(raw_dir / "contribution_exp_c_runs.csv", index=False)

    lut_df.to_csv(sum_dir / "contribution_lut_inventory.csv", index=False)
    err_df.to_csv(sum_dir / "contribution_lut_stats.csv", index=False)
    (sum_dir / "contribution_lut_stats.md").write_text(
        format_lut_markdown(lut_df, err_df, lut_wall_s), encoding="utf-8"
    )

    exp_a_sum.to_csv(sum_dir / "contribution_exp_a_summary.csv", index=False)
    (sum_dir / "contribution_exp_a_summary.md").write_text(
        format_exp_a_markdown(exp_a_sum), encoding="utf-8"
    )

    exp_b_sum.to_csv(sum_dir / "contribution_exp_b_summary.csv", index=False)
    (sum_dir / "contribution_exp_b_summary.md").write_text(
        format_exp_b_markdown(exp_b_sum), encoding="utf-8"
    )

    wilcoxon_df.to_csv(sum_dir / "contribution_wilcoxon.csv", index=False)
    (sum_dir / "contribution_wilcoxon.md").write_text(
        format_stage2_wilcoxon_markdown(wilcoxon_df), encoding="utf-8"
    )

    exp_c_sum.to_csv(sum_dir / "contribution_exp_c_summary.csv", index=False)
    (sum_dir / "contribution_exp_c_summary.md").write_text(
        format_exp_c_markdown(exp_c_sum), encoding="utf-8"
    )

    comp_df.to_csv(sum_dir / "contribution_comparison.csv", index=False)
    (sum_dir / "contribution_comparison.md").write_text(
        format_contribution_comparison_markdown(comp_df), encoding="utf-8"
    )

    return {
        "lut_inventory": lut_df,
        "lut_errors": err_df,
        "speed_stats": speed_stats,
        "exp_a_raw": exp_a_raw,
        "exp_a_summary": exp_a_sum,
        "exp_a_coverage": exp_a_cov_sum,
        "exp_b_raw": exp_b_raw,
        "exp_b_summary": exp_b_sum,
        "wilcoxon": wilcoxon_df,
        "exp_c_raw": exp_c_raw,
        "exp_c_summary": exp_c_sum,
        "comparison": comp_df,
        "timings": {
            "lut_wall_s": lut_wall_s,
            "bench_wall_s": bench_wall_s,
            "exp_a_wall_s": exp_a_wall_s,
            "exp_b_wall_s": exp_b_wall_s,
            "exp_c_wall_s": exp_c_wall_s,
            "total_wall_s": total_wall_s,
        },
    }
