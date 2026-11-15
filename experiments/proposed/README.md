# Proposed Contribution Experiments (`experiments/proposed/`)

This directory contains the configuration and exact execution instructions for the original contribution: the faithful Deng & Jiang (2014) truth-table similarity optimization engine (`OSFI-DJ`), singleton equivalence verification (`OSFI-DJ-S == CRI-S`), and sensor-noise-robust non-singleton inference (`OSFI-DJ-NS` vs `CRI-NS` and baselines).

## Experiments Included
- **Experiment A (Noiseless Extended Reproduction):** `Mamdani`, `Sugeno`, `OSFI-literal`, `OSFI-DJ-S`, `CRI-S`, `Webster`, and `Actuated` across `moderate`, `heavy`, `peak`, and `stress` (`n = 30` seeds).
- **Experiment B (Sensor Noise Robustness Grid):** $\sigma_q \in \{0, 5, 10, 15\}\text{ m/lane}$ and $p_{\text{miss}} \in \{0, 0.1, 0.2\}$ on `heavy` and `peak` across all 9 controllers (`Mamdani`, `Sugeno`, `OSFI-literal`, `OSFI-DJ-S`, `CRI-NS`, `OSFI-DJ-NS`, `OSFI-DJ-NS-mis`, `Webster`, `Actuated`, `n = 30` seeds per cell).
- **Experiment C (Ablation Study):** 9 variants on `heavy` ($\sigma_q = 10\text{ m}, p_{\text{miss}} = 0$): implicator (`lukasiewicz`, `goguen`, `kleene_dienes`), tie-break (`smallest`, `midpoint`), defuzzifier (`centroid_above_floor`, `centroid`), boundary MFs (`shoulder_edges = True/False`), antecedent AND (`lukasiewicz`, `min`), MF width (`mf_sigma_scale = 1.0/1.5`), and phase switching (`spm_mode = gpe_first/preempt`).

## Exact Command to Run

From the repository root (`osfi-tsc/`):

```bash
python scripts/run_contribution.py --config experiments/proposed/config.yaml --output results
```

## Generated Outputs
- Raw per-seed run metrics: `results/raw/contribution_exp_{a,b,c}_runs.csv`
- Summary & statistical tables:
  - `results/tables/contribution_exp_a_summary.{csv,md}`
  - `results/tables/contribution_exp_b_summary.{csv,md}`
  - `results/tables/contribution_exp_c_summary.{csv,md}`
  - `results/tables/contribution_wilcoxon.{csv,md}`
  - `results/tables/contribution_comparison.{csv,md}` (Guideline §6.2 comparison table)
  - `results/tables/contribution_lut_stats.{csv,md}` & `results/tables/contribution_lut_inventory.csv`
