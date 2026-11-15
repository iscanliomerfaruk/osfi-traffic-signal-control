"""CLI script to execute Stage 2/3 contribution experiments (A, B, C) and LUT benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from osfi_tsc.contribution import run_all_contribution_experiments
from osfi_tsc.experiment import load_config


def write_experiment_log(
    log_path: Path,
    config: dict[str, Any],
    results: dict[str, Any],
) -> None:
    """Append or update the dated Stage 3 rerun entry in docs/experiment_log.md while preserving earlier logs."""
    exp_cfg = config.get("experiment", {})
    num_seeds = int(exp_cfg.get("num_seeds", 30))
    base_seed = int(exp_cfg.get("base_seed", 202501))
    timings = results["timings"]
    lut_df = results["lut_inventory"]
    err_df = results["lut_errors"]
    speed_stats = results["speed_stats"]

    lines = [
        "# Stage 3 Rerun (`2026-11-15`) — Control-Logic, Calibration, and Dead-Zone Fixes",
        "",
        "## 1. Factual Summary of Stage 3 Changes (Sections 1–3) and Rationale",
        "",
        "1. **Section 1 — Controller Fixes (`spm_mode = gpe_first` & Actuated Stop-Line Presence):**",
        "   - *Diagnosis:* In Stage 1–2, `FuzzyController.step` preempted the active green phase whenever any competing approach had a strictly longer queue *before* consulting the two-stage Green Phase Extension (GPE), causing signal thrashing after almost every $G_{\\min} = 7\\text{ s}$ ($\\approx 280\\text{--}300$ switches/h, $>50\\%$ lost time). Simultaneously, `ActuatedController` extended only on upstream arrivals within $3\\text{ s}$ and gapped out with standing queues when mean arrival headways exceeded $3\\text{ s}$.",
        "   - *Fix:* Added `controller.spm_mode \\in \\{\\text{gpe\\_first}, \\text{preempt}\\}$ (default `gpe_first`, keeping `preempt` for Experiment C ablation). Under `gpe_first` (Esmaeili et al. 2025, Sec. 4.1.3), GPE is evaluated at the end of $G_{\\min}$ and each extension window; if $\\text{Extension2} \\ge 1\\text{ s}$, $q_{\\text{cur}} > 0$, and $g_{\\text{elapsed}} < G_{\\max}$, the active phase extends by $\\text{round}(\\text{Extension2})$, otherwise NPS selects the longest competing queue. Updated `ActuatedController` to include stop-line queue presence detection ($q_{\\text{cur}} > 0$ or arrival within `unit_extension`).",
        "2. **Section 2 — Demand Calibration (`configs/scenarios/*.yaml`) & Sanity Gates:**",
        "   - *Diagnosis:* Stage 1–2 demands ($1800\\text{--}2700\\text{ veh/h}$) exceeded the paper's Table 1 total Mamdani exit volume ($328+398+165+173 = 1064\\text{ veh}$) and saturated the $[0, 60]\\text{ m/lane}$ queue universe ($\\approx 8.6\\text{ veh/lane}$) at `VL` $90\\text{--}100\\%$ of the time, clipping $\\sigma_q \\le 15\\text{ m}$ sensor noise.",
        "   - *Fix:* Removed hardcoded demands and calibrated YAML scenarios to the paper's exit sum and $[0, 60]\\text{ m/lane}$ universe: `moderate` ($1100\\text{ veh/h}$, $Y=0.3056$), `heavy` ($1500\\text{ veh/h}$, $Y=0.4167$), `peak` ($1100 \\to 1800 \\to 1100\\text{ veh/h}$ trapezoid, mean $1625\\text{ veh/h}$, $Y=0.4514$), and `stress` ($1800\\text{ veh/h}$, $Y=0.5000$). Added automated sanity gates verifying $\\ge 97\\%$ discharge in non-stress scenarios and $\\ge 3$ queue linguistic sets with $\\ge 5\\%$ coverage for Mamdani in `moderate` and `heavy`.",
        "3. **Section 3 — Unified Dead-Zone Nearest-Rule Fallback & Antecedent/Width Ablations:**",
        "   - *Diagnosis:* Adjacent Gaussian MFs ($\\sigma_\\lambda = 1.0, \\sigma_q = 5.0$) cross at $\\approx 0.3247$, creating diamond-shaped dead zones around $\\lambda \\in \\{1.5, 4.5, 7.5\\}, q \\in \\{7.5, 22.5, 37.5\\}$ where $\\max_i \\alpha_i = \\max_i(a_{i1}+a_{i2}-1, 0) = 0$. Previously `OSFI-literal` fell back to Sugeno while `OSFI-DJ`/`CRI` fell back to $0\\text{ s}$.",
        "   - *Fix:* Unified dead-zone fallback ($\\max_i \\alpha_i < 10^{-6}$ or zero above-floor area) across `OSFI-literal`, `OSFI-DJ`, and `CRI` using the **nearest-rule fallback** (peak of the consequent of the rule with highest `min`-firing strength), and added `fuzzy.and_operator \\in \\{\\text{lukasiewicz}, \\text{min}\\}$ and `fuzzy.mf_sigma_scale` ($1.0$ default, $1.5$ ablation).",
        "",
        "## 2. Stage 3 Execution Summary and Wall-Clock Runtimes",
        "",
        f"- **Random seeds:** `{num_seeds}` common-random-number seeds (`{base_seed}` .. `{base_seed + num_seeds - 1}`)",
        f"- **LUT precomputation & 500-point error verification time:** `{timings['lut_wall_s']:.2f} s`",
        f"- **10,000-call `time.perf_counter` direct & LUT inference benchmark time:** `{timings['bench_wall_s']:.2f} s`",
        f"  - `OSFI-DJ-S` Direct: `{speed_stats['direct_s_ms_per_call']:.3f} ms/call` | 2D LUT: `{speed_stats['lut_s_us_per_call']:.2f} µs/call` | LUT build (FC1+FC2): `{speed_stats['lut_build_s_sec']:.2f} s`",
        f"  - `OSFI-DJ-NS` Direct: `{speed_stats['direct_ns_ms_per_call']:.3f} ms/call` | 2D LUT: `{speed_stats['lut_ns_us_per_call']:.2f} µs/call` | LUT build (FC1+FC2): `{speed_stats['lut_build_ns_sec']:.2f} s`",
        f"- **Experiment A wall-clock time** (`4 scenarios x 7 controllers x {num_seeds} seeds = {4 * 7 * num_seeds} runs`): `{timings['exp_a_wall_s']:.2f} s`",
        f"- **Experiment B wall-clock time** (`2 scenarios x 12 noise cells x 9 controllers x {num_seeds} seeds = {2 * 12 * 9 * num_seeds} runs`): `{timings['exp_b_wall_s']:.2f} s`",
        f"- **Experiment C wall-clock time** (`1 scenario x 9 ablation variants x {num_seeds} seeds = {9 * num_seeds} runs`): `{timings['exp_c_wall_s']:.2f} s`",
        f"- **Total `run_contribution.py` wall-clock time:** `{timings['total_wall_s']:.2f} s`",
        "",
        "## 3. Stage 3 Lookup Table (LUT) 500-Point Off-Grid Interpolation Error Summary",
        "",
        "| Model | Stage | Config Hash | Build Time (s) | Max Abs Error (s) | Mean Abs Error (s) | Median Abs Error (s) | 95th Pct Error (s) |",
        "| :--- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in err_df.iterrows():
        lines.append(
            f"| `{r['model']}` | `{r['stage'].upper()}` | `{r['config_hash']}` "
            f"| {float(r['build_time_s']):.3f} | {float(r['max_abs_error_s']):.4f} "
            f"| {float(r['mean_abs_error_s']):.4f} | {float(r['median_abs_error_s']):.4f} "
            f"| {float(r['p95_abs_error_s']):.4f} |"
        )

    lines.extend(
        [
            "",
            "## 4. Stage 3 Cached Stage LUT Hashes and Parameters",
            "",
            "| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | AND | $\\sigma$-Scale | $\\sigma_1$ | $\\sigma_2$ | SHA-256 Hash | Build Time (s) | Cache Path |",
            "| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | ---: | ---: | ---: | :---: | ---: | :--- |",
        ]
    )
    for _, r in lut_df.iterrows():
        lines.append(
            f"| `{r['engine']}` | `{r['stage'].upper()}` | {r['config_label']} "
            f"| `{r['implicator']}` | `{r['tie_break']}` | `{r['defuzz_method']}` "
            f"| `{bool(r['shoulder_edges'])}` | `{r.get('and_operator', 'lukasiewicz')}` "
            f"| {float(r.get('mf_sigma_scale', 1.0)):.2f} "
            f"| {float(r['sigma1']):.4f} | {float(r['sigma2']):.2f} "
            f"| `{r['config_hash']}` | {float(r['build_time_s']):.3f} | `{r['cache_file']}` |"
        )
    lines.append("")

    report_text = "\n".join(lines)
    marker_start = "<!-- STAGE3_CONTRIBUTION_LOG_START -->"
    marker_end = "<!-- STAGE3_CONTRIBUTION_LOG_END -->"
    block = f"{marker_start}\n{report_text}\n{marker_end}"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.is_file():
        existing = log_path.read_text(encoding="utf-8")
        if marker_start in existing and marker_end in existing:
            pre = existing.split(marker_start)[0]
            post = existing.split(marker_end)[1]
            log_path.write_text(f"{pre}{block}{post}", encoding="utf-8")
        else:
            log_path.write_text(existing.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
    else:
        log_path.write_text(block + "\n", encoding="utf-8")


def main() -> None:
    """Parse CLI arguments and run Stage 2/3 contribution experiments."""
    parser = argparse.ArgumentParser(
        description="Run OSFI-TSC contribution experiments (A, B, C)."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default.yaml",
        help="Path to default YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for raw and tables results.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel worker processes.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    log_path = repo_root / "docs" / "experiment_log.md"
    config = load_config(args.config)
    results = run_all_contribution_experiments(
        config_path=args.config,
        output_root=args.output,
        n_workers=args.workers,
        log_path=log_path,
    )
    write_experiment_log(
        log_path=log_path,
        config=config,
        results=results,
    )
    timings = results["timings"]
    print(
        f"Contribution experiments completed in {timings['total_wall_s']:.2f} s "
        f"(LUT: {timings['lut_wall_s']:.2f} s, SpeedBench: {timings['bench_wall_s']:.2f} s, "
        f"Exp A: {timings['exp_a_wall_s']:.2f} s, Exp B: {timings['exp_b_wall_s']:.2f} s, "
        f"Exp C: {timings['exp_c_wall_s']:.2f} s)."
    )


if __name__ == "__main__":
    main()
