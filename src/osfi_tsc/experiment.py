"""Experiment runner and summary table generators for Stage 1 reproduction."""

from __future__ import annotations

from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any
import pandas as pd
import yaml
from tqdm import tqdm

from osfi_tsc.control import ActuatedController, FuzzyController, WebsterController
from osfi_tsc.inference import (
    CRIInference,
    MamdaniInference,
    OSFIDJInference,
    OSFILiteralInference,
    SugenoInference,
)
from osfi_tsc.metrics import (
    compute_run_metrics,
    run_paired_wilcoxon_tests,
    summarize_metrics_with_ci,
)
from osfi_tsc.sim import (
    APPROACHES,
    IntersectionSimulator,
    ScenarioDemand,
    compute_matched_input_sigmas,
    pregenerate_arrivals,
    pregenerate_sensor_noise,
    validate_and_print_webster_ratios,
)

CONTROLLER_ORDER: tuple[str, ...] = (
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "Webster",
    "Actuated",
)

STAGE2_CONTROLLER_ORDER: tuple[str, ...] = (
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

FUZZY_CONTROLLER_NAMES: tuple[str, ...] = (
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "OSFI-DJ-S",
    "CRI-NS",
    "OSFI-DJ-NS",
    "OSFI-DJ-NS-mis",
)

PAPER_TABLE_1: dict[str, dict[str, dict[str, float]]] = {
    "Average Delay (s)": {
        "E": {"Mamdani": 1.048, "Sugeno": 1.018, "OSFI": 1.011, "imp_M": 3.55, "imp_S": 0.69},
        "S": {"Mamdani": 1.210, "Sugeno": 1.199, "OSFI": 1.182, "imp_M": 2.31, "imp_S": 1.42},
        "W": {"Mamdani": 1.172, "Sugeno": 1.183, "OSFI": 1.153, "imp_M": 1.62, "imp_S": 2.54},
        "N": {"Mamdani": 1.062, "Sugeno": 1.074, "OSFI": 1.022, "imp_M": 3.78, "imp_S": 4.84},
    },
    "Average Exit (veh)": {
        "E": {"Mamdani": 328.0, "Sugeno": 320.0, "OSFI": 310.0, "imp_M": 5.49, "imp_S": 3.13},
        "S": {"Mamdani": 398.0, "Sugeno": 397.0, "OSFI": 387.0, "imp_M": 2.76, "imp_S": 2.52},
        "W": {"Mamdani": 165.0, "Sugeno": 145.0, "OSFI": 138.0, "imp_M": 16.36, "imp_S": 4.83},
        "N": {"Mamdani": 173.0, "Sugeno": 175.0, "OSFI": 173.0, "imp_M": 0.58, "imp_S": 1.14},
    },
}

PAPER_TABLE_2: dict[str, dict[str, dict[str, float]]] = {
    "Average Delay (s)": {
        "E": {"Mamdani": 1.137, "Sugeno": 1.126, "OSFI": 1.098, "imp_M": 3.64, "imp_S": 2.55},
        "S": {"Mamdani": 1.178, "Sugeno": 1.201, "OSFI": 1.165, "imp_M": 1.11, "imp_S": 3.09},
        "W": {"Mamdani": 1.172, "Sugeno": 1.154, "OSFI": 1.132, "imp_M": 3.53, "imp_S": 1.94},
        "N": {"Mamdani": 1.144, "Sugeno": 1.131, "OSFI": 1.082, "imp_M": 5.73, "imp_S": 4.52},
    },
    "Average Exit (veh)": {
        "E": {"Mamdani": 347.0, "Sugeno": 321.0, "OSFI": 298.0, "imp_M": 16.44, "imp_S": 7.71},
        "S": {"Mamdani": 381.0, "Sugeno": 385.0, "OSFI": 362.0, "imp_M": 5.20, "imp_S": 6.35},
        "W": {"Mamdani": 152.0, "Sugeno": 137.0, "OSFI": 128.0, "imp_M": 18.75, "imp_S": 2.34},
        "N": {"Mamdani": 186.0, "Sugeno": 185.0, "OSFI": 178.0, "imp_M": 4.49, "imp_S": 3.93},
    },
}


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load YAML configuration file."""
    with Path(config_path).open("r", encoding="utf-8") as fh:
        return dict(yaml.safe_load(fh))


def build_controller(
    name: str,
    scenario: ScenarioDemand,
    config: dict[str, Any],
    sigma_q: float | None = None,
    p_miss: float | None = None,
    use_lut: bool = True,
) -> Any:
    """Instantiate a traffic signal controller by name."""
    fuzzy_cfg = config.get("fuzzy", {})
    ctrl_cfg = config.get("controller", {})
    sim_cfg = config.get("simulator", {})
    noise_cfg = sim_cfg.get("sensor_noise", {})

    shoulder = bool(fuzzy_cfg.get("shoulder_edges", True))
    grid_step = float(fuzzy_cfg.get("mamdani_grid_step", 0.05))
    implicator = str(fuzzy_cfg.get("implicator", "lukasiewicz"))
    tie_break = str(fuzzy_cfg.get("tie_break", "smallest"))
    defuzz_method = str(fuzzy_cfg.get("defuzz_method", "centroid_above_floor"))
    cache_dir = str(fuzzy_cfg.get("cache_dir", "results/cache"))

    sq = float(sigma_q if sigma_q is not None else noise_cfg.get("queue_std_m", 0.0))
    pm = float(p_miss if p_miss is not None else noise_cfg.get("arrival_p_miss", 0.0))

    g_min = int(ctrl_cfg.get("g_min", 7))
    g_max = int(ctrl_cfg.get("g_max", 60))
    spm_mode = str(ctrl_cfg.get("spm_mode", "gpe_first"))

    if name == "Mamdani":
        engine: Any = MamdaniInference(shoulder_edges=shoulder, grid_step=grid_step)
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "Sugeno":
        engine = SugenoInference(shoulder_edges=shoulder)
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "OSFI-literal":
        engine = OSFILiteralInference(shoulder_edges=shoulder)
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "OSFI-DJ-S":
        engine = OSFIDJInference(
            implicator=implicator,
            tie_break=tie_break,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder,
            sigma_lambda=0.0,
            sigma_queue=0.0,
            sigma_ext1=0.0,
            use_lut=use_lut,
            cache_dir=cache_dir,
        )
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "CRI-NS":
        sig1, sig2 = compute_matched_input_sigmas(sigma_q=sq, p_miss=pm)
        engine = CRIInference(
            implicator=implicator,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder,
            sigma_lambda=sig1,
            sigma_queue=sig2,
            sigma_ext1=0.0,
            use_lut=use_lut,
            cache_dir=cache_dir,
        )
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "OSFI-DJ-NS":
        sig1, sig2 = compute_matched_input_sigmas(sigma_q=sq, p_miss=pm)
        engine = OSFIDJInference(
            implicator=implicator,
            tie_break=tie_break,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder,
            sigma_lambda=sig1,
            sigma_queue=sig2,
            sigma_ext1=0.0,
            use_lut=use_lut,
            cache_dir=cache_dir,
        )
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "OSFI-DJ-NS-mis":
        sig1_mis, sig2_mis = compute_matched_input_sigmas(sigma_q=5.0, p_miss=0.0)
        engine = OSFIDJInference(
            implicator=implicator,
            tie_break=tie_break,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder,
            sigma_lambda=sig1_mis,
            sigma_queue=sig2_mis,
            sigma_ext1=0.0,
            use_lut=use_lut,
            cache_dir=cache_dir,
        )
        return FuzzyController(engine=engine, g_min=g_min, g_max=g_max, spm_mode=spm_mode)
    if name == "Webster":
        bounds = tuple(ctrl_cfg.get("webster_cycle_bounds", [40.0, 180.0]))
        return WebsterController(
            scenario=scenario,
            service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
            lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
            yellow_time=float(sim_cfg.get("yellow_time", 3.0)),
            all_red_time=float(sim_cfg.get("all_red_time", 2.0)),
            startup_lost_time=float(sim_cfg.get("startup_lost_time", 2.0)),
            cycle_bounds=(float(bounds[0]), float(bounds[1])),
            g_min=g_min,
        )
    if name == "Actuated":
        unit_ext = int(ctrl_cfg.get("actuated_unit_extension", 3))
        return ActuatedController(
            g_min=g_min,
            unit_extension=unit_ext,
            g_max=g_max,
        )
    raise ValueError(f"Unknown controller: {name}")


def _run_single_scenario_seed(
    task: tuple[str, int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenario_name, seed, config = task
    sim_cfg = config.get("simulator", {})
    exp_cfg = config.get("experiment", {})
    controllers = list(exp_cfg.get("controllers", CONTROLLER_ORDER))

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
        queue_noise_std_m=float(
            sim_cfg.get("sensor_noise", {}).get("queue_std_m", 0.0)
        ),
        arrival_noise_std=float(
            sim_cfg.get("sensor_noise", {}).get("arrival_std", 0.0)
        ),
    )

    metric_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []

    for ctrl_name in controllers:
        ctrl = build_controller(ctrl_name, scen, config)
        res = simulator.run(
            controller=ctrl,
            scenario=scen,
            seed=seed,
            controller_name=ctrl_name,
            arrival_counts=common_arrivals,
            verify_conservation=True,
        )
        m_rows, cov_row = compute_run_metrics(res, controller=ctrl)
        metric_rows.extend(m_rows)
        if ctrl_name in ("Mamdani", "Sugeno", "OSFI-literal"):
            coverage_rows.append(cov_row)

    return metric_rows, coverage_rows


def build_paper_style_table(
    summary_df: pd.DataFrame,
    scenario_name: str,
) -> pd.DataFrame:
    """Construct Table 1/2 layout with correct improvement sign conventions."""
    sub = summary_df[summary_df["scenario"] == scenario_name]
    rows: list[dict[str, Any]] = []

    for indicator, col_prefix, lower_is_better in (
        ("Average Delay (s)", "avg_delay_s", True),
        ("Average Exit (veh)", "throughput_veh", False),
    ):
        for app in APPROACHES:
            app_sub = sub[sub["approach"] == app].set_index("controller")
            val_m = float(app_sub.loc["Mamdani", f"{col_prefix}_mean"])
            val_s = float(app_sub.loc["Sugeno", f"{col_prefix}_mean"])
            val_o = float(app_sub.loc["OSFI-literal", f"{col_prefix}_mean"])

            if lower_is_better:
                imp_m = ((val_m - val_o) / val_m) * 100.0 if val_m > 0 else 0.0
                imp_s = ((val_s - val_o) / val_s) * 100.0 if val_s > 0 else 0.0
            else:
                imp_m = ((val_o - val_m) / val_m) * 100.0 if val_m > 0 else 0.0
                imp_s = ((val_o - val_s) / val_s) * 100.0 if val_s > 0 else 0.0

            if imp_m > 0.0 and imp_s > 0.0:
                reproduced = "Yes (both > 0%)"
            elif imp_m > 0.0:
                reproduced = "Partial (vs Mamdani only)"
            elif imp_s > 0.0:
                reproduced = "Partial (vs Sugeno only)"
            else:
                reproduced = "No"

            rows.append(
                {
                    "Indicator": indicator,
                    "Phase": app,
                    "Mamdani": val_m,
                    "Sugeno": val_s,
                    "OSFI-literal": val_o,
                    "Improvement_vs_Mamdani_pct": imp_m,
                    "Improvement_vs_Sugeno_pct": imp_s,
                    "Paper_Direction_Reproduced": reproduced,
                }
            )
    return pd.DataFrame(rows)


def format_paper_style_markdown(df: pd.DataFrame, scenario_name: str) -> str:
    """Format a paper-style comparison DataFrame as a Markdown table."""
    title = (
        f"# Paper-Style Comparison Table — `{scenario_name.capitalize()}` Scenario\n\n"
        "Sign convention: positive `% Improvement` always indicates better performance by `OSFI-literal` "
        "(lower Average Delay, higher Average Exit).\n\n"
    )
    lines = [
        title,
        "| Indicator | Phase | Mamdani | Sugeno | OSFI-literal | % Imp. vs Mamdani | % Imp. vs Sugeno | Paper Claimed Direction Reproduced? |",
        "| :--- | :---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for _, r in df.iterrows():
        ind = str(r["Indicator"])
        fmt_val = "{:.2f}" if "Delay" in ind else "{:.1f}"
        m_str = fmt_val.format(float(r["Mamdani"]))
        s_str = fmt_val.format(float(r["Sugeno"]))
        o_str = fmt_val.format(float(r["OSFI-literal"]))
        im_str = f"{float(r['Improvement_vs_Mamdani_pct']):+.2f}%"
        is_str = f"{float(r['Improvement_vs_Sugeno_pct']):+.2f}%"
        lines.append(
            f"| {ind} | {r['Phase']} | {m_str} | {s_str} | {o_str} | {im_str} | {is_str} | {r['Paper_Direction_Reproduced']} |"
        )
    lines.append("")
    return "\n".join(lines)


def format_paper_vs_ours_markdown(
    mod_df: pd.DataFrame,
    hvy_df: pd.DataFrame,
) -> str:
    """Build side-by-side comparison of paper Tables 1-2 vs our simulation results."""
    lines = [
        "# Reference Paper (Tables 1–2) vs. Our Reproduction (`n = 30` Seeds)",
        "",
        "> **Note on physical comparability:** In Esmaeili et al. (2025), Tables 1 and 2 report average delays of "
        "`1.011–1.210 s/veh` across a 4-phase intersection where only one approach receives green at a time. "
        "Under any physically realizable 4-phase signal cycle ($G_{\\min} = 7\\text{ s}$, intergreen $= 5\\text{ s}$, "
        "minimum cycle $\\ge 48\\text{ s}$), vehicles arriving on the three red approaches wait tens of seconds on average. "
        "Hence absolute delay magnitudes in our queueing simulation are on the physically expected scale ($\\sim 50–180\\text{ s/veh}$), "
        "and comparison focuses on **relative rankings, directional changes, and structural behavior**.",
        "> Furthermore, in the paper's Tables 1 and 2, the `Average Exit (veh)` percentage columns report lower OSFI throughput "
        "(e.g., `310` vs `328` in Table 1 Phase E) as a positive `+5.49%` improvement; in our columns we use the physically "
        "correct sign convention where higher throughput is positive.",
        "",
    ]

    for scen_title, paper_tbl, our_df in (
        ("Moderate Traffic (Paper Table 1 vs. Ours)", PAPER_TABLE_1, mod_df),
        ("Heavy Traffic (Paper Table 2 vs. Ours)", PAPER_TABLE_2, hvy_df),
    ):
        lines.extend(
            [
                f"## {scen_title}",
                "",
                "| Indicator | Phase | Paper Mamdani | Paper Sugeno | Paper OSFI | Paper % vs M | Paper % vs S | Our Mamdani | Our Sugeno | Our OSFI-literal | Our % vs M | Our % vs S |",
                "| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for _, r in our_df.iterrows():
            ind = str(r["Indicator"])
            app = str(r["Phase"])
            p_row = paper_tbl[ind][app]
            if "Delay" in ind:
                p_m = f"{p_row['Mamdani']:.3f}"
                p_s = f"{p_row['Sugeno']:.3f}"
                p_o = f"{p_row['OSFI']:.3f}"
                o_m = f"{float(r['Mamdani']):.2f}"
                o_s = f"{float(r['Sugeno']):.2f}"
                o_o = f"{float(r['OSFI-literal']):.2f}"
            else:
                p_m = f"{int(p_row['Mamdani'])}"
                p_s = f"{int(p_row['Sugeno'])}"
                p_o = f"{int(p_row['OSFI'])}"
                o_m = f"{float(r['Mamdani']):.1f}"
                o_s = f"{float(r['Sugeno']):.1f}"
                o_o = f"{float(r['OSFI-literal']):.1f}"

            lines.append(
                f"| {ind} | {app} | {p_m} | {p_s} | {p_o} | {p_row['imp_M']:.2f}% | {p_row['imp_S']:.2f}% "
                f"| {o_m} | {o_s} | {o_o} | {float(r['Improvement_vs_Mamdani_pct']):+.2f}% | {float(r['Improvement_vs_Sugeno_pct']):+.2f}% |"
            )
        lines.append("")

    return "\n".join(lines)


def format_wilcoxon_markdown(wilcoxon_df: pd.DataFrame) -> str:
    """Format paired Wilcoxon signed-rank test table as Markdown."""
    lines = [
        "# Paired Wilcoxon Signed-Rank Tests (`n = 30` Common-Random-Number Seeds)",
        "",
        "| Scenario | Metric | Comparison | OSFI-literal Mean | Baseline Mean | Mean Diff (OSFI - Base) | Wilcoxon Stat | Raw $p$-value | Holm $p$ (Pair) | Holm $p$ (All) | Sig. ($\\alpha=0.05$)? |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for _, r in wilcoxon_df.iterrows():
        sig = "Yes" if bool(r["significant_005_holm_pair"]) else "No"
        lines.append(
            f"| `{r['scenario']}` | `{r['metric']}` | {r['comparison']} "
            f"| {float(r['osfi_mean']):.3f} | {float(r['baseline_mean']):.3f} "
            f"| {float(r['mean_diff_osfi_minus_base']):+.3f} | {float(r['wilcoxon_stat']):.1f} "
            f"| {float(r['p_raw']):.4g} | {float(r['p_holm_pair']):.4g} | {float(r['p_holm_all']):.4g} | {sig} |"
        )
    lines.append("")
    return "\n".join(lines)


def summarize_input_coverage(cov_df: pd.DataFrame) -> pd.DataFrame:
    """Average input coverage shares and fallback rates across seeds per scenario and controller."""
    value_cols = [
        c
        for c in cov_df.columns
        if c not in ("scenario", "controller", "seed")
    ]
    return (
        cov_df.groupby(["scenario", "controller"], sort=False)[value_cols]
        .mean()
        .reset_index()
    )


def format_input_coverage_markdown(cov_summary_df: pd.DataFrame) -> str:
    """Format input coverage and fallback rate summary as Markdown."""
    lines = [
        "# Fuzzy Input Coverage Diagnostics and OSFI-Literal Fallback Rate",
        "",
        "Share of GPE decision evaluations during the 3600 s measurement window in which each linguistic term achieved the highest membership degree.",
        "",
        "| Scenario | Controller | GPE Evals | Fallback Rate (Total / FC1 / FC2) | $\\lambda$: `Z / Lo / M / H` | $q_{\\text{cur}}$: `Sh / M / L / VL` | `Ext1`: `Z / Sh / M / L` | $q_{\\text{other}}$: `Sh / M / L / VL` |",
        "| :--- | :--- | ---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for _, r in cov_summary_df.iterrows():
        fb_str = (
            f"{float(r['fallback_rate'])*100:.2f}% "
            f"({float(r['fc1_fallback_rate'])*100:.2f}% / {float(r['fc2_fallback_rate'])*100:.2f}%)"
        )
        lam_str = (
            f"{float(r['arrival_rate_Z'])*100:.1f}% / "
            f"{float(r['arrival_rate_Lo'])*100:.1f}% / "
            f"{float(r['arrival_rate_M'])*100:.1f}% / "
            f"{float(r['arrival_rate_H'])*100:.1f}%"
        )
        qcur_str = (
            f"{float(r['queue_current_Sh'])*100:.1f}% / "
            f"{float(r['queue_current_M'])*100:.1f}% / "
            f"{float(r['queue_current_L'])*100:.1f}% / "
            f"{float(r['queue_current_VL'])*100:.1f}%"
        )
        ext1_str = (
            f"{float(r['extension1_Z'])*100:.1f}% / "
            f"{float(r['extension1_Sh'])*100:.1f}% / "
            f"{float(r['extension1_M'])*100:.1f}% / "
            f"{float(r['extension1_L'])*100:.1f}%"
        )
        qoth_str = (
            f"{float(r['queue_others_max_Sh'])*100:.1f}% / "
            f"{float(r['queue_others_max_M'])*100:.1f}% / "
            f"{float(r['queue_others_max_L'])*100:.1f}% / "
            f"{float(r['queue_others_max_VL'])*100:.1f}%"
        )
        lines.append(
            f"| `{r['scenario']}` | `{r['controller']}` | {float(r['gpe_evaluations']):.1f} "
            f"| {fb_str} | {lam_str} | {qcur_str} | {ext1_str} | {qoth_str} |"
        )
    lines.append("")
    return "\n".join(lines)


def verify_sanity_gates(
    summary_df: pd.DataFrame,
    cov_summary_df: pd.DataFrame | None = None,
    runner_name: str = "reproduction",
    log_path: str | Path | None = "docs/experiment_log.md",
) -> str:
    """Verify discharge ratio (>=97%) and Mamdani queue-input coverage sanity gates."""
    overall = summary_df[summary_df["approach"] == "overall"].copy()
    failures: list[str] = []
    lines: list[str] = [
        f"## Sanity Gate Check (`{runner_name}`)",
        "",
        "### Gate 1 — Measurement-Window Discharge Ratio ($\\ge 97\\%$ in non-stress scenarios)",
        "",
        "| Scenario | `Webster` Discharge (%) | Best Fuzzy Controller | Best Fuzzy Discharge (%) | Status |",
        "| :--- | ---: | :--- | ---: | :---: |",
    ]

    for scen in ("moderate", "heavy", "peak"):
        sub = overall[overall["scenario"] == scen]
        if sub.empty:
            continue
        web_rows = sub[sub["controller"] == "Webster"]
        if web_rows.empty:
            failures.append(f"[{runner_name}] Missing Webster row for scenario '{scen}'")
            continue
        if "discharge_ratio_mean" in web_rows.columns:
            web_ratio = float(web_rows.iloc[0]["discharge_ratio_mean"])
        else:
            web_ratio = float(web_rows.iloc[0]["throughput_veh_mean"]) / max(
                1.0, float(web_rows.iloc[0]["arrivals_veh_mean"])
            )

        fuzzy_sub = sub[~sub["controller"].isin(["Webster", "Actuated"])]
        if fuzzy_sub.empty:
            failures.append(f"[{runner_name}] Missing fuzzy rows for scenario '{scen}'")
            continue
        if "discharge_ratio_mean" in fuzzy_sub.columns:
            best_idx = fuzzy_sub["discharge_ratio_mean"].astype(float).idxmax()
            best_row = fuzzy_sub.loc[best_idx]
            best_fuzzy_name = str(best_row["controller"])
            best_fuzzy_ratio = float(best_row["discharge_ratio_mean"])
        else:
            ratios = fuzzy_sub["throughput_veh_mean"].astype(float) / fuzzy_sub[
                "arrivals_veh_mean"
            ].astype(float).clip(lower=1.0)
            best_idx = ratios.idxmax()
            best_fuzzy_name = str(fuzzy_sub.loc[best_idx, "controller"])
            best_fuzzy_ratio = float(ratios.loc[best_idx])

        ok = (web_ratio >= 0.97) and (best_fuzzy_ratio >= 0.97)
        status = "PASS" if ok else "FAIL"
        lines.append(
            f"| `{scen}` | {web_ratio*100:.2f}% | `{best_fuzzy_name}` | {best_fuzzy_ratio*100:.2f}% | **{status}** |"
        )
        if not ok:
            failures.append(
                f"[{runner_name}] Discharge gate failed in '{scen}': "
                f"Webster={web_ratio*100:.2f}%, best_fuzzy({best_fuzzy_name})={best_fuzzy_ratio*100:.2f}% (< 97%)"
            )

    if cov_summary_df is not None and not cov_summary_df.empty:
        lines.extend(
            [
                "",
                "### Gate 2 — `Mamdani` Queue-Input Coverage ($\\ge 3$ linguistic sets with $\\ge 5\\%$ share in `moderate` and `heavy`)",
                "",
                "| Scenario | $q_{\\text{cur}}$ (`Sh / M / L / VL`) | Sets $\\ge 5\\%$ ($q_{\\text{cur}}$) | $q_{\\text{other}}$ (`Sh / M / L / VL`) | Sets $\\ge 5\\%$ ($q_{\\text{other}}$) | Status |",
                "| :--- | :---: | :---: | :---: | :---: | :---: |",
            ]
        )
        for scen in ("moderate", "heavy"):
            c_sub = cov_summary_df[
                (cov_summary_df["scenario"] == scen)
                & (cov_summary_df["controller"] == "Mamdani")
            ]
            if c_sub.empty:
                failures.append(
                    f"[{runner_name}] Missing Mamdani coverage row for scenario '{scen}'"
                )
                continue
            r = c_sub.iloc[0]
            qcur_vals = [
                float(r[f"queue_current_{t}"]) for t in ("Sh", "M", "L", "VL")
            ]
            qoth_vals = [
                float(r[f"queue_others_max_{t}"]) for t in ("Sh", "M", "L", "VL")
            ]
            n_qcur = sum(1 for v in qcur_vals if v >= 0.05)
            n_qoth = sum(1 for v in qoth_vals if v >= 0.05)
            ok_cov = max(n_qcur, n_qoth) >= 3
            status = "PASS" if ok_cov else "FAIL"
            qcur_s = " / ".join(f"{v*100:.1f}%" for v in qcur_vals)
            qoth_s = " / ".join(f"{v*100:.1f}%" for v in qoth_vals)
            lines.append(
                f"| `{scen}` | {qcur_s} | {n_qcur} | {qoth_s} | {n_qoth} | **{status}** |"
            )
            if not ok_cov:
                failures.append(
                    f"[{runner_name}] Coverage gate failed in '{scen}': "
                    f"Mamdani has {n_qcur} sets >=5% in q_cur and {n_qoth} in q_other (need >=3)"
                )

    lines.append("")
    report_text = "\n".join(lines)
    print("\n" + report_text)

    if log_path is not None:
        lp = Path(log_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        marker_start = f"<!-- SANITY_GATE_START:{runner_name} -->"
        marker_end = f"<!-- SANITY_GATE_END:{runner_name} -->"
        block = f"{marker_start}\n{report_text}\n{marker_end}"
        if lp.is_file():
            existing = lp.read_text(encoding="utf-8")
            if marker_start in existing and marker_end in existing:
                pre = existing.split(marker_start)[0]
                post = existing.split(marker_end)[1]
                lp.write_text(f"{pre}{block}{post}", encoding="utf-8")
            else:
                lp.write_text(existing.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
        else:
            lp.write_text("# Experiment Log & Sanity Gate Verification\n\n" + block + "\n", encoding="utf-8")

    if failures:
        raise RuntimeError("Sanity gate check failed:\n" + "\n".join(failures))

    return report_text


def run_all_experiments(
    config_path: str | Path = "configs/default.yaml",
    output_root: str | Path = "results",
    n_workers: int | None = None,
    log_path: str | Path | None = "docs/experiment_log.md",
) -> dict[str, pd.DataFrame]:
    """Execute full 5 controllers x 4 scenarios x 30 seeds experiment suite."""
    config = load_config(config_path)
    sim_cfg = config.get("simulator", {})
    exp_cfg = config.get("experiment", {})

    validate_and_print_webster_ratios(
        service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
        lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
    )

    scenarios = list(exp_cfg.get("scenarios", ["moderate", "heavy", "peak", "stress"]))
    num_seeds = int(exp_cfg.get("num_seeds", 30))
    base_seed = int(exp_cfg.get("base_seed", 202501))

    tasks: list[tuple[str, int, dict[str, Any]]] = []
    for scen_name in scenarios:
        for idx in range(num_seeds):
            tasks.append((scen_name, base_seed + idx, config))

    workers = n_workers if n_workers is not None else max(1, min(cpu_count() or 4, 8))
    all_metric_rows: list[dict[str, Any]] = []
    all_coverage_rows: list[dict[str, Any]] = []

    with Pool(processes=workers) as pool:
        for m_rows, c_rows in tqdm(
            pool.imap_unordered(_run_single_scenario_seed, tasks),
            total=len(tasks),
            desc="Simulating (scenario, seed) pairs",
        ):
            all_metric_rows.extend(m_rows)
            all_coverage_rows.extend(c_rows)

    raw_df = pd.DataFrame(all_metric_rows)
    raw_df["controller"] = pd.Categorical(
        raw_df["controller"], categories=list(CONTROLLER_ORDER), ordered=True
    )
    raw_df = raw_df.sort_values(["scenario", "controller", "seed", "approach"]).reset_index(
        drop=True
    )
    raw_df["controller"] = raw_df["controller"].astype(str)

    cov_df = pd.DataFrame(all_coverage_rows).sort_values(
        ["scenario", "controller", "seed"]
    ).reset_index(drop=True)

    summary_df = summarize_metrics_with_ci(raw_df)
    cov_summary_df = summarize_input_coverage(cov_df)

    verify_sanity_gates(
        summary_df=summary_df,
        cov_summary_df=cov_summary_df,
        runner_name="run_reproduction",
        log_path=log_path,
    )

    out_dir = Path(output_root)
    raw_dir = out_dir / "raw"
    sum_dir = out_dir / "tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    sum_dir.mkdir(parents=True, exist_ok=True)

    raw_df.to_csv(raw_dir / "reproduction_runs.csv", index=False)
    cov_df.to_csv(raw_dir / "input_coverage_runs.csv", index=False)

    summary_df.to_csv(sum_dir / "metrics_summary_ci.csv", index=False)

    wilcoxon_df = run_paired_wilcoxon_tests(raw_df)
    wilcoxon_df.to_csv(sum_dir / "wilcoxon_tests.csv", index=False)
    (sum_dir / "wilcoxon_tests.md").write_text(
        format_wilcoxon_markdown(wilcoxon_df), encoding="utf-8"
    )

    cov_summary_df.to_csv(sum_dir / "input_coverage_summary.csv", index=False)
    (sum_dir / "input_coverage_summary.md").write_text(
        format_input_coverage_markdown(cov_summary_df), encoding="utf-8"
    )

    mod_table = build_paper_style_table(summary_df, "moderate")
    hvy_table = build_paper_style_table(summary_df, "heavy")
    mod_table.to_csv(sum_dir / "paper_style_table_moderate.csv", index=False)
    hvy_table.to_csv(sum_dir / "paper_style_table_heavy.csv", index=False)
    (sum_dir / "paper_style_table_moderate.md").write_text(
        format_paper_style_markdown(mod_table, "moderate"), encoding="utf-8"
    )
    (sum_dir / "paper_style_table_heavy.md").write_text(
        format_paper_style_markdown(hvy_table, "heavy"), encoding="utf-8"
    )
    (sum_dir / "paper_vs_ours.md").write_text(
        format_paper_vs_ours_markdown(mod_table, hvy_table), encoding="utf-8"
    )

    return {
        "raw": raw_df,
        "summary": summary_df,
        "wilcoxon": wilcoxon_df,
        "coverage": cov_summary_df,
        "paper_moderate": mod_table,
        "paper_heavy": hvy_table,
    }
