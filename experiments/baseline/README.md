# Baseline Reproduction Experiments (`experiments/baseline/`)

This directory contains the configuration and exact execution instructions for reproducing the baseline controllers from Esmaeili et al. (2025) alongside standard traffic engineering baselines (`Webster` fixed-time and `Actuated` stop-line presence).

## Controllers Evaluated
- `Mamdani` (`min` AND, `min` implication, `max` aggregation, centroid defuzzification on $0.05\text{ s}$ grid)
- `Sugeno` (`min` AND, zero-order weighted average of consequent peaks $\{0, 7.5, 12.5, 17.5\}\text{ s}$)
- `OSFI-literal` (Sec. 4.1.2 formula: Łukasiewicz t-norm $\alpha_i = \max(0, f_1+f_2-1)$ + zero-order weighted average with unified nearest-rule dead-zone fallback)
- `Webster` (fixed-time cycle $C_0 = \text{clip}((1.5L+5)/(1-Y), 40, 180)\text{ s}$, greens proportional to $y_i/Y$)
- `Actuated` (round-robin vehicle-actuated control with stop-line queue presence and $3\text{ s}$ unit extension)

## Scenarios
- `moderate`: $1100\text{ veh/h}$ constant ($Y = 0.3056$)
- `heavy`: $1500\text{ veh/h}$ constant ($Y = 0.4167$)
- `peak`: $1100 \to 1800 \to 1100\text{ veh/h}$ trapezoid, mean $1625\text{ veh/h}$ ($Y = 0.4514$)
- `stress`: $1800\text{ veh/h}$ constant ($Y = 0.5000$)

## Exact Command to Run

From the repository root (`osfi-tsc/`):

```bash
python scripts/run_reproduction.py --config experiments/baseline/config.yaml --output results
```

## Generated Outputs
- Raw per-seed run metrics: `results/raw/reproduction_runs.csv`, `results/raw/input_coverage_runs.csv`
- Summary tables:
  - `results/tables/metrics_summary_ci.csv`
  - `results/tables/paper_style_table_moderate.{csv,md}`
  - `results/tables/paper_style_table_heavy.{csv,md}`
  - `results/tables/paper_vs_ours.md`
  - `results/tables/wilcoxon_tests.{csv,md}`
  - `results/tables/input_coverage_summary.{csv,md}`
