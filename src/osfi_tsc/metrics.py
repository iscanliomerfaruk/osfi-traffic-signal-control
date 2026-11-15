"""Metrics computation, confidence intervals, and paired Wilcoxon tests."""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd
from scipy import stats

from osfi_tsc.sim.demand import APPROACHES
from osfi_tsc.sim.intersection import SimulationResult


def compute_run_metrics(
    result: SimulationResult,
    controller: Any | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compute per-approach and overall metrics for a single simulation run."""
    warmup_s = float(result.warmup_s)
    horizon_s = float(result.warmup_s + result.measurement_s)
    warmup_steps = int(round(result.warmup_s / result.dt))
    intergreen_s = 5.0

    if result.green_durations_measurement:
        mean_green_s = float(np.mean(result.green_durations_measurement))
        mean_cycle_s = 4.0 * (mean_green_s + intergreen_s)
    else:
        mean_green_s = float(result.measurement_s)
        mean_cycle_s = 4.0 * (mean_green_s + intergreen_s)

    fallback_rate = 0.0
    fc1_fallback_rate = 0.0
    fc2_fallback_rate = 0.0
    if controller is not None and hasattr(controller, "engine"):
        eng = controller.engine
        fallback_rate = float(getattr(eng, "fallback_rate", 0.0))
        fc1_fallback_rate = float(getattr(eng, "fc1_fallback_rate", 0.0))
        fc2_fallback_rate = float(getattr(eng, "fc2_fallback_rate", 0.0))

    rows: list[dict[str, Any]] = []
    all_departed_delays: list[float] = []
    all_incl_queued_delays: list[float] = []
    total_throughput = 0
    total_arrivals = 0
    approach_mean_q_veh: list[float] = []
    approach_max_q_veh: list[float] = []
    approach_mean_q_m: list[float] = []
    approach_max_q_m: list[float] = []

    for app in APPROACHES:
        dep_post_warmup = [
            v
            for v in result.departed_vehicles[app]
            if v.arrival_time >= warmup_s and v.departure_time is not None
        ]
        dep_delays = [
            float(v.departure_time - v.arrival_time)
            for v in dep_post_warmup
            if v.departure_time is not None
        ]
        rem_post_warmup = [
            v for v in result.remaining_queues[app] if v.arrival_time >= warmup_s
        ]
        rem_delays = [float(horizon_s - v.arrival_time) for v in rem_post_warmup]
        comb_delays = dep_delays + rem_delays

        all_departed_delays.extend(dep_delays)
        all_incl_queued_delays.extend(comb_delays)

        arrivals_in_window = len(dep_post_warmup) + len(rem_post_warmup)
        exits_in_window = sum(
            1
            for v in result.departed_vehicles[app]
            if v.departure_time is not None and v.departure_time >= warmup_s
        )
        total_arrivals += arrivals_in_window
        total_throughput += exits_in_window
        app_discharge = (
            float(exits_in_window) / float(arrivals_in_window)
            if arrivals_in_window > 0
            else 1.0
        )

        q_veh_slice = result.queue_veh_history[app][warmup_steps:]
        q_m_slice = result.queue_m_history[app][warmup_steps:]

        m_q_veh = float(np.mean(q_veh_slice)) if len(q_veh_slice) > 0 else 0.0
        x_q_veh = float(np.max(q_veh_slice)) if len(q_veh_slice) > 0 else 0.0
        m_q_m = float(np.mean(q_m_slice)) if len(q_m_slice) > 0 else 0.0
        x_q_m = float(np.max(q_m_slice)) if len(q_m_slice) > 0 else 0.0

        approach_mean_q_veh.append(m_q_veh)
        approach_max_q_veh.append(x_q_veh)
        approach_mean_q_m.append(m_q_m)
        approach_max_q_m.append(x_q_m)

        rows.append(
            {
                "scenario": result.scenario_name,
                "controller": result.controller_name,
                "seed": result.seed,
                "approach": app,
                "avg_delay_s": float(np.mean(dep_delays)) if dep_delays else 0.0,
                "avg_delay_incl_queued_s": (
                    float(np.mean(comb_delays)) if comb_delays else 0.0
                ),
                "arrivals_veh": int(arrivals_in_window),
                "throughput_veh": int(exits_in_window),
                "discharge_ratio": app_discharge,
                "mean_queue_veh": m_q_veh,
                "max_queue_veh": x_q_veh,
                "mean_queue_m": m_q_m,
                "max_queue_m": x_q_m,
                "mean_cycle_length_s": mean_cycle_s,
                "num_switches": int(result.num_switches_measurement),
                "fallback_rate": fallback_rate,
                "fc1_fallback_rate": fc1_fallback_rate,
                "fc2_fallback_rate": fc2_fallback_rate,
            }
        )

    total_discharge = (
        float(total_throughput) / float(total_arrivals)
        if total_arrivals > 0
        else 1.0
    )
    rows.append(
        {
            "scenario": result.scenario_name,
            "controller": result.controller_name,
            "seed": result.seed,
            "approach": "overall",
            "avg_delay_s": (
                float(np.mean(all_departed_delays)) if all_departed_delays else 0.0
            ),
            "avg_delay_incl_queued_s": (
                float(np.mean(all_incl_queued_delays))
                if all_incl_queued_delays
                else 0.0
            ),
            "arrivals_veh": int(total_arrivals),
            "throughput_veh": int(total_throughput),
            "discharge_ratio": total_discharge,
            "mean_queue_veh": float(np.mean(approach_mean_q_veh)),
            "max_queue_veh": float(np.max(approach_max_q_veh)),
            "mean_queue_m": float(np.mean(approach_mean_q_m)),
            "max_queue_m": float(np.max(approach_max_q_m)),
            "mean_cycle_length_s": mean_cycle_s,
            "num_switches": int(result.num_switches_measurement),
            "fallback_rate": fallback_rate,
            "fc1_fallback_rate": fc1_fallback_rate,
            "fc2_fallback_rate": fc2_fallback_rate,
        }
    )

    coverage_record: dict[str, Any] = {
        "scenario": result.scenario_name,
        "controller": result.controller_name,
        "seed": result.seed,
        "fallback_rate": fallback_rate,
        "fc1_fallback_rate": fc1_fallback_rate,
        "fc2_fallback_rate": fc2_fallback_rate,
    }
    if controller is not None and hasattr(controller, "get_input_coverage_shares"):
        shares = controller.get_input_coverage_shares()
        coverage_record["gpe_evaluations"] = int(getattr(controller, "gpe_evaluations", 0))
        for var_name, term_dict in shares.items():
            for term_name, share_val in term_dict.items():
                coverage_record[f"{var_name}_{term_name}"] = float(share_val)
    else:
        coverage_record["gpe_evaluations"] = 0

    return rows, coverage_record


def mean_and_t_ci(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float, float]:
    """Compute sample mean, standard deviation, and half-width of t-confidence interval."""
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    if n == 0:
        return 0.0, 0.0, 0.0
    mean_val = float(np.mean(arr))
    if n == 1:
        return mean_val, 0.0, 0.0
    sd_val = float(np.std(arr, ddof=1))
    t_crit = float(stats.t.ppf(0.5 + 0.5 * confidence, df=n - 1))
    ci_half = t_crit * sd_val / float(np.sqrt(n))
    return mean_val, sd_val, ci_half


def summarize_metrics_with_ci(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean, std, and 95% t-CI per scenario, controller, approach, and metric."""
    metric_cols = [
        "avg_delay_s",
        "avg_delay_incl_queued_s",
        "arrivals_veh",
        "throughput_veh",
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
    summary_rows: list[dict[str, Any]] = []
    grouped = raw_df.groupby(["scenario", "controller", "approach"], sort=False)
    for (scen, ctrl, app), grp in grouped:
        row: dict[str, Any] = {
            "scenario": scen,
            "controller": ctrl,
            "approach": app,
            "n_seeds": len(grp),
        }
        for col in metric_cols:
            m_val, sd_val, ci_val = mean_and_t_ci(grp[col].to_numpy(dtype=float))
            row[f"{col}_mean"] = m_val
            row[f"{col}_std"] = sd_val
            row[f"{col}_ci95"] = ci_val
        summary_rows.append(row)
    return pd.DataFrame(summary_rows)


def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Apply Holm-Bonferroni step-down correction to a list of p-values."""
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p_val) in enumerate(indexed):
        adj = min(1.0, float(p_val) * float(m - rank))
        running_max = max(running_max, adj)
        corrected[orig_idx] = running_max
    return corrected


def run_paired_wilcoxon_tests(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Run paired Wilcoxon signed-rank tests (OSFI-literal vs Mamdani & Sugeno) with Holm correction."""
    overall_df = raw_df[raw_df["approach"] == "overall"].copy()
    scenarios = list(overall_df["scenario"].unique())
    metrics = ["avg_delay_s", "avg_delay_incl_queued_s", "throughput_veh"]
    baselines = ["Mamdani", "Sugeno"]

    records: list[dict[str, Any]] = []
    for scen in scenarios:
        scen_df = overall_df[overall_df["scenario"] == scen]
        osfi_df = scen_df[scen_df["controller"] == "OSFI-literal"].sort_values("seed")
        for metric in metrics:
            pair_pvals: list[float] = []
            pair_indices: list[int] = []
            for base in baselines:
                base_df = scen_df[scen_df["controller"] == base].sort_values("seed")
                x = osfi_df[metric].to_numpy(dtype=float)
                y = base_df[metric].to_numpy(dtype=float)
                diff = x - y
                mean_diff = float(np.mean(diff))
                median_diff = float(np.median(diff))
                if np.all(np.abs(diff) <= 1e-12):
                    stat_val = 0.0
                    p_val = 1.0
                else:
                    res = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
                    stat_val = float(res.statistic)
                    p_val = float(res.pvalue)
                idx = len(records)
                pair_indices.append(idx)
                pair_pvals.append(p_val)
                records.append(
                    {
                        "scenario": scen,
                        "metric": metric,
                        "comparison": f"OSFI-literal vs {base}",
                        "osfi_mean": float(np.mean(x)),
                        "baseline_mean": float(np.mean(y)),
                        "mean_diff_osfi_minus_base": mean_diff,
                        "median_diff_osfi_minus_base": median_diff,
                        "wilcoxon_stat": stat_val,
                        "p_raw": p_val,
                        "p_holm_pair": p_val,
                    }
                )
            holm_pair = holm_bonferroni(pair_pvals)
            for idx, adj_p in zip(pair_indices, holm_pair):
                records[idx]["p_holm_pair"] = adj_p

    all_pvals = [float(r["p_raw"]) for r in records]
    all_holm = holm_bonferroni(all_pvals)
    for r, adj_all in zip(records, all_holm):
        r["p_holm_all"] = adj_all
        r["significant_005_holm_pair"] = bool(r["p_holm_pair"] < 0.05)

    return pd.DataFrame(records)
