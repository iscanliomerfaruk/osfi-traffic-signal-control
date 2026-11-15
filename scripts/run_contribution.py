"""CLI script to execute Stage 2 contribution experiments (A, B, C) and LUT benchmarks."""

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
    """Write docs/experiment_log.md with run metadata, timings, seeds, and LUT hashes."""
    exp_cfg = config.get("experiment", {})
    num_seeds = int(exp_cfg.get("num_seeds", 30))
    base_seed = int(exp_cfg.get("base_seed", 202501))
    timings = results["timings"]
    lut_df = results["lut_inventory"]
    err_df = results["lut_errors"]

    lines = [
        "# Experiment Execution Log (`Stage 1` & `Stage 2`)",
        "",
        "## 1. Execution Summary and Wall-Clock Runtimes",
        "",
        f"- **Random seeds:** `{num_seeds}` common-random-number seeds (`{base_seed}` .. `{base_seed + num_seeds - 1}`)",
        "- **Stream separation per seed:**",
        "  - True Poisson vehicle arrivals: `seed`",
        "  - Exponential departure service capacity: `seed + 1_000_003`",
        "  - Additive Gaussian queue sensor noise ($\\sigma_q$): `seed + 2_000_003`",
        "  - Binomial missed-arrival thinning ($p_{\\text{miss}}$) + Poisson false detections ($\\varepsilon = 0.02\\text{ veh/s}$): `seed + 3_000_003`",
        f"- **Stage 2 LUT precomputation & 500-point error verification time:** `{timings['lut_wall_s']:.2f} s`",
        f"- **Experiment A wall-clock time** (`3 scenarios x 6 controllers x {num_seeds} seeds = {3 * 6 * num_seeds} runs`): `{timings['exp_a_wall_s']:.2f} s`",
        f"- **Experiment B wall-clock time** (`2 scenarios x 12 noise cells x 9 controllers x {num_seeds} seeds = {2 * 12 * 9 * num_seeds} runs`): `{timings['exp_b_wall_s']:.2f} s`",
        f"- **Experiment C wall-clock time** (`1 scenario x 6 ablation variants x {num_seeds} seeds = {6 * num_seeds} runs`): `{timings['exp_c_wall_s']:.2f} s`",
        f"- **Total `run_contribution.py` wall-clock time:** `{timings['total_wall_s']:.2f} s`",
        "",
        "## 2. Lookup Table (LUT) 500-Point Off-Grid Interpolation Error Summary",
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
            "## 3. Cached Stage LUT Hashes and Parameters",
            "",
            "| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | $\\sigma_1$ | $\\sigma_2$ | SHA-256 Hash | Build Time (s) | Cache Path |",
            "| :--- | :---: | :--- | :---: | :---: | :---: | :---: | ---: | ---: | :---: | ---: | :--- |",
        ]
    )
    for _, r in lut_df.iterrows():
        lines.append(
            f"| `{r['engine']}` | `{r['stage'].upper()}` | {r['config_label']} "
            f"| `{r['implicator']}` | `{r['tie_break']}` | `{r['defuzz_method']}` "
            f"| `{bool(r['shoulder_edges'])}` | {float(r['sigma1']):.4f} | {float(r['sigma2']):.2f} "
            f"| `{r['config_hash']}` | {float(r['build_time_s']):.3f} | `{r['cache_file']}` |"
        )
    lines.append("")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Parse CLI arguments and run Stage 2 contribution experiments."""
    parser = argparse.ArgumentParser(
        description="Run Stage 2 OSFI-TSC contribution experiments (A, B, C)."
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
        help="Output directory for raw and summary results.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel worker processes.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    results = run_all_contribution_experiments(
        config_path=args.config,
        output_root=args.output,
        n_workers=args.workers,
    )
    repo_root = Path(__file__).resolve().parent.parent
    write_experiment_log(
        log_path=repo_root / "docs" / "experiment_log.md",
        config=config,
        results=results,
    )
    timings = results["timings"]
    print(
        f"Stage 2 experiments completed in {timings['total_wall_s']:.2f} s "
        f"(LUT: {timings['lut_wall_s']:.2f} s, Exp A: {timings['exp_a_wall_s']:.2f} s, "
        f"Exp B: {timings['exp_b_wall_s']:.2f} s, Exp C: {timings['exp_c_wall_s']:.2f} s)."
    )


if __name__ == "__main__":
    main()
