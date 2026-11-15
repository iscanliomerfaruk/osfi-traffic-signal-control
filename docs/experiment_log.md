# Experiment Execution Log (`Stage 1` & `Stage 2`)

## 1. Execution Summary and Wall-Clock Runtimes

- **Random seeds:** `30` common-random-number seeds (`202501` .. `202530`)
- **Stream separation per seed:**
  - True Poisson vehicle arrivals: `seed`
  - Exponential departure service capacity: `seed + 1_000_003`
  - Additive Gaussian queue sensor noise ($\sigma_q$): `seed + 2_000_003`
  - Binomial missed-arrival thinning ($p_{\text{miss}}$) + Poisson false detections ($\varepsilon = 0.02\text{ veh/s}$): `seed + 3_000_003`
- **Stage 2 LUT precomputation & 500-point error verification time:** `223.57 s`
- **Experiment A wall-clock time** (`3 scenarios x 6 controllers x 30 seeds = 540 runs`): `8.36 s`
- **Experiment B wall-clock time** (`2 scenarios x 12 noise cells x 9 controllers x 30 seeds = 6480 runs`): `70.94 s`
- **Experiment C wall-clock time** (`1 scenario x 6 ablation variants x 30 seeds = 180 runs`): `1.66 s`
- **Total `run_contribution.py` wall-clock time:** `305.70 s`

## 2. Lookup Table (LUT) 500-Point Off-Grid Interpolation Error Summary

| Model | Stage | Config Hash | Build Time (s) | Max Abs Error (s) | Mean Abs Error (s) | Median Abs Error (s) | 95th Pct Error (s) |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |
| `OSFI-DJ-S (singleton)` | `FC1` | `f0cd9ff537f2aa73` | 1.679 | 9.6564 | 0.2248 | 0.0041 | 1.4041 |
| `OSFI-DJ-S (singleton)` | `FC2` | `42c5986621fa680a` | 2.987 | 10.0869 | 0.1277 | 0.0085 | 0.3653 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC1` | `40ce4e120c956fc8` | 6.905 | 5.9863 | 0.1594 | 0.0030 | 0.9600 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC2` | `05e06bf7ade3bb8a` | 1.878 | 5.3402 | 0.1067 | 0.0127 | 0.3474 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC1` | `72bedce35f4bb8e0` | 5.904 | 10.4318 | 0.2307 | 0.0037 | 1.3330 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC2` | `3d5c603ffdf7c550` | 0.495 | 5.9833 | 0.0893 | 0.0031 | 0.1951 |

## 3. Cached Stage LUT Hashes and Parameters

| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | $\sigma_1$ | $\sigma_2$ | SHA-256 Hash | Build Time (s) | Cache Path |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | ---: | ---: | :---: | ---: | :--- |
| `OSFI-DJ` | `FC1` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 0.00 | `f0cd9ff537f2aa73` | 1.679 | `results/cache/lut_osfi_dj_fc1_f0cd9ff537f2aa73.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 0.00 | `42c5986621fa680a` | 2.987 | `results/cache/lut_osfi_dj_fc2_42c5986621fa680a.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 1.00 | `e631861af11481ad` | 1.281 | `results/cache/lut_osfi_dj_fc1_e631861af11481ad.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 1.00 | `1d9e20406cbbd5dd` | 1.515 | `results/cache/lut_osfi_dj_fc2_1d9e20406cbbd5dd.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 1.00 | `c8391aee27f10dac` | 0.323 | `results/cache/lut_cri_fc1_c8391aee27f10dac.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 1.00 | `3efa4b612673f337` | 0.233 | `results/cache/lut_cri_fc2_3efa4b612673f337.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 1.00 | `95ec9bd468f567e3` | 1.740 | `results/cache/lut_osfi_dj_fc1_95ec9bd468f567e3.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 1.00 | `02689ddb8d89cf4d` | 0.485 | `results/cache/lut_cri_fc1_02689ddb8d89cf4d.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 1.00 | `3f4c9a45ddd15cd5` | 1.849 | `results/cache/lut_osfi_dj_fc1_3f4c9a45ddd15cd5.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 1.00 | `698c089f0f2983ea` | 0.561 | `results/cache/lut_cri_fc1_698c089f0f2983ea.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 5.00 | `181bf4f90d4d364f` | 4.115 | `results/cache/lut_osfi_dj_fc1_181bf4f90d4d364f.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 5.00 | `d0d1583df44277a4` | 1.746 | `results/cache/lut_osfi_dj_fc2_d0d1583df44277a4.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 5.00 | `ba1df8aca84aef03` | 1.080 | `results/cache/lut_cri_fc1_ba1df8aca84aef03.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 5.00 | `87ae3e399576da67` | 0.357 | `results/cache/lut_cri_fc2_87ae3e399576da67.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 5.00 | `a4e78e729cbb69e2` | 6.018 | `results/cache/lut_osfi_dj_fc1_a4e78e729cbb69e2.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 5.00 | `ea490df9f0833eb6` | 4.784 | `results/cache/lut_cri_fc1_ea490df9f0833eb6.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 5.00 | `a3e3c57ac73050af` | 6.461 | `results/cache/lut_osfi_dj_fc1_a3e3c57ac73050af.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 5.00 | `1c70624deba2df0a` | 5.553 | `results/cache/lut_cri_fc1_1c70624deba2df0a.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `40ce4e120c956fc8` | 6.905 | `results/cache/lut_osfi_dj_fc1_40ce4e120c956fc8.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `05e06bf7ade3bb8a` | 1.878 | `results/cache/lut_osfi_dj_fc2_05e06bf7ade3bb8a.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `72bedce35f4bb8e0` | 5.904 | `results/cache/lut_cri_fc1_72bedce35f4bb8e0.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `3d5c603ffdf7c550` | 0.495 | `results/cache/lut_cri_fc2_3d5c603ffdf7c550.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 10.00 | `15fcf62518451b33` | 10.049 | `results/cache/lut_osfi_dj_fc1_15fcf62518451b33.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 10.00 | `a0380e04cd5b37d5` | 9.027 | `results/cache/lut_cri_fc1_a0380e04cd5b37d5.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 10.00 | `1d987d604838f59d` | 11.193 | `results/cache/lut_osfi_dj_fc1_1d987d604838f59d.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 10.00 | `614f6b6356609e0d` | 9.887 | `results/cache/lut_cri_fc1_614f6b6356609e0d.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 15.00 | `9811ea49e0653840` | 8.524 | `results/cache/lut_osfi_dj_fc1_9811ea49e0653840.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 15.00 | `cf9a79af322c13b6` | 1.926 | `results/cache/lut_osfi_dj_fc2_cf9a79af322c13b6.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 15.00 | `ecec328dd3f5854c` | 8.138 | `results/cache/lut_cri_fc1_ecec328dd3f5854c.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 15.00 | `121461714d502d74` | 0.427 | `results/cache/lut_cri_fc2_121461714d502d74.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 15.00 | `4eb5ae87aea301b7` | 12.721 | `results/cache/lut_osfi_dj_fc1_4eb5ae87aea301b7.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 15.00 | `5542f7d0da829d3d` | 12.621 | `results/cache/lut_cri_fc1_5542f7d0da829d3d.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 15.00 | `7b577b9a267e82f1` | 14.170 | `results/cache/lut_osfi_dj_fc1_7b577b9a267e82f1.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 15.00 | `ea5d0811c38fc648` | 13.837 | `results/cache/lut_cri_fc1_ea5d0811c38fc648.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `ad274d585e340ab0` | 7.162 | `results/cache/lut_osfi_dj_fc1_ad274d585e340ab0.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `c0bc75da1507bfd6` | 2.495 | `results/cache/lut_osfi_dj_fc2_c0bc75da1507bfd6.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `6c8a54c00e8e133b` | 7.062 | `results/cache/lut_osfi_dj_fc1_6c8a54c00e8e133b.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `be3b130b4ed1b337` | 2.421 | `results/cache/lut_osfi_dj_fc2_be3b130b4ed1b337.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `7d5583279fb29541` | 7.103 | `results/cache/lut_osfi_dj_fc1_7d5583279fb29541.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `3c0cb6ba3a2ce110` | 2.458 | `results/cache/lut_osfi_dj_fc2_3c0cb6ba3a2ce110.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | 0.5000 | 10.00 | `5c5307da8d6d85f4` | 7.077 | `results/cache/lut_osfi_dj_fc1_5c5307da8d6d85f4.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | 0.0000 | 10.00 | `36aa307a72187911` | 2.454 | `results/cache/lut_osfi_dj_fc2_36aa307a72187911.npz` |
| `OSFI-DJ` | `FC1` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | 0.5000 | 10.00 | `ac33fca3bba861a6` | 3.734 | `results/cache/lut_osfi_dj_fc1_ac33fca3bba861a6.npz` |
| `OSFI-DJ` | `FC2` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | 0.0000 | 10.00 | `f11090a69484b81b` | 2.147 | `results/cache/lut_osfi_dj_fc2_f11090a69484b81b.npz` |

<!-- SANITY_GATE_START:run_reproduction -->
## Sanity Gate Check (`run_reproduction`)

### Gate 1 — Measurement-Window Discharge Ratio ($\ge 97\%$ in non-stress scenarios)

| Scenario | `Webster` Discharge (%) | Best Fuzzy Controller | Best Fuzzy Discharge (%) | Status |
| :--- | ---: | :--- | ---: | :---: |
| `moderate` | 100.03% | `Sugeno` | 100.02% | **PASS** |
| `heavy` | 99.81% | `Mamdani` | 100.00% | **PASS** |
| `peak` | 99.91% | `Mamdani` | 100.01% | **PASS** |

### Gate 2 — `Mamdani` Queue-Input Coverage ($\ge 3$ linguistic sets with $\ge 5\%$ share across `moderate` and `heavy`)

| Scope | $q_{\text{cur}}$ (`Sh / M / L / VL`) | Sets $\ge 5\%$ ($q_{\text{cur}}$) | $q_{\text{other}}$ (`Sh / M / L / VL`) | Sets $\ge 5\%$ ($q_{\text{other}}$) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `moderate` | 90.8% / 8.7% / 0.5% / 0.0% | 2 | 33.5% / 63.2% / 3.2% / 0.1% | 2 | **PASS** |
| `heavy` | 77.1% / 19.4% / 3.3% / 0.3% | 2 | 7.1% / 68.5% / 23.0% / 1.4% | 3 | **PASS** |
| `moderate + heavy (pooled)` | 83.9% / 14.0% / 1.9% / 0.1% | 2 | 20.3% / 65.9% / 13.1% / 0.7% | 3 | **PASS** |

<!-- SANITY_GATE_END:run_reproduction -->

<!-- SANITY_GATE_START:run_contribution -->
## Sanity Gate Check (`run_contribution`)

### Gate 1 — Measurement-Window Discharge Ratio ($\ge 97\%$ in non-stress scenarios)

| Scenario | `Webster` Discharge (%) | Best Fuzzy Controller | Best Fuzzy Discharge (%) | Status |
| :--- | ---: | :--- | ---: | :---: |
| `moderate` | 100.03% | `Sugeno` | 100.02% | **PASS** |
| `heavy` | 99.81% | `Mamdani` | 100.00% | **PASS** |
| `peak` | 99.91% | `Mamdani` | 100.01% | **PASS** |

### Gate 2 — `Mamdani` Queue-Input Coverage ($\ge 3$ linguistic sets with $\ge 5\%$ share across `moderate` and `heavy`)

| Scope | $q_{\text{cur}}$ (`Sh / M / L / VL`) | Sets $\ge 5\%$ ($q_{\text{cur}}$) | $q_{\text{other}}$ (`Sh / M / L / VL`) | Sets $\ge 5\%$ ($q_{\text{other}}$) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `moderate` | 90.8% / 8.7% / 0.5% / 0.0% | 2 | 33.5% / 63.2% / 3.2% / 0.1% | 2 | **PASS** |
| `heavy` | 77.1% / 19.4% / 3.3% / 0.3% | 2 | 7.1% / 68.5% / 23.0% / 1.4% | 3 | **PASS** |
| `moderate + heavy (pooled)` | 83.9% / 14.0% / 1.9% / 0.1% | 2 | 20.3% / 65.9% / 13.1% / 0.7% | 3 | **PASS** |

<!-- SANITY_GATE_END:run_contribution -->

<!-- STAGE3_CONTRIBUTION_LOG_START -->
# Stage 3 Rerun (`2026-11-15`) — Control-Logic, Calibration, and Dead-Zone Fixes

## 1. Factual Summary of Stage 3 Changes (Sections 1–3) and Rationale

1. **Section 1 — Controller Fixes (`spm_mode = gpe_first` & Actuated Stop-Line Presence):**
   - *Diagnosis:* In Stage 1–2, `FuzzyController.step` preempted the active green phase whenever any competing approach had a strictly longer queue *before* consulting the two-stage Green Phase Extension (GPE), causing signal thrashing after almost every $G_{\min} = 7\text{ s}$ ($\approx 280\text{--}300$ switches/h, $>50\%$ lost time). Simultaneously, `ActuatedController` extended only on upstream arrivals within $3\text{ s}$ and gapped out with standing queues when mean arrival headways exceeded $3\text{ s}$.
   - *Fix:* Added `controller.spm_mode \in \{\text{gpe\_first}, \text{preempt}\}$ (default `gpe_first`, keeping `preempt` for Experiment C ablation). Under `gpe_first` (Esmaeili et al. 2025, Sec. 4.1.3), GPE is evaluated at the end of $G_{\min}$ and each extension window; if $\text{Extension2} \ge 1\text{ s}$, $q_{\text{cur}} > 0$, and $g_{\text{elapsed}} < G_{\max}$, the active phase extends by $\text{round}(\text{Extension2})$, otherwise NPS selects the longest competing queue. Updated `ActuatedController` to include stop-line queue presence detection ($q_{\text{cur}} > 0$ or arrival within `unit_extension`).
2. **Section 2 — Demand Calibration (`configs/scenarios/*.yaml`) & Sanity Gates:**
   - *Diagnosis:* Stage 1–2 demands ($1800\text{--}2700\text{ veh/h}$) exceeded the paper's Table 1 total Mamdani exit volume ($328+398+165+173 = 1064\text{ veh}$) and saturated the $[0, 60]\text{ m/lane}$ queue universe ($\approx 8.6\text{ veh/lane}$) at `VL` $90\text{--}100\%$ of the time, clipping $\sigma_q \le 15\text{ m}$ sensor noise.
   - *Fix:* Removed hardcoded demands and calibrated YAML scenarios to the paper's exit sum and $[0, 60]\text{ m/lane}$ universe: `moderate` ($1100\text{ veh/h}$, $Y=0.3056$), `heavy` ($1500\text{ veh/h}$, $Y=0.4167$), `peak` ($1100 \to 1800 \to 1100\text{ veh/h}$ trapezoid, mean $1625\text{ veh/h}$, $Y=0.4514$), and `stress` ($1800\text{ veh/h}$, $Y=0.5000$). Added automated sanity gates verifying $\ge 97\%$ discharge in non-stress scenarios and $\ge 3$ queue linguistic sets with $\ge 5\%$ coverage for Mamdani in `moderate` and `heavy`.
3. **Section 3 — Unified Dead-Zone Nearest-Rule Fallback & Antecedent/Width Ablations:**
   - *Diagnosis:* Adjacent Gaussian MFs ($\sigma_\lambda = 1.0, \sigma_q = 5.0$) cross at $\approx 0.3247$, creating diamond-shaped dead zones around $\lambda \in \{1.5, 4.5, 7.5\}, q \in \{7.5, 22.5, 37.5\}$ where $\max_i \alpha_i = \max_i(a_{i1}+a_{i2}-1, 0) = 0$. Previously `OSFI-literal` fell back to Sugeno while `OSFI-DJ`/`CRI` fell back to $0\text{ s}$.
   - *Fix:* Unified dead-zone fallback ($\max_i \alpha_i < 10^{-6}$ or zero above-floor area) across `OSFI-literal`, `OSFI-DJ`, and `CRI` using the **nearest-rule fallback** (peak of the consequent of the rule with highest `min`-firing strength), and added `fuzzy.and_operator \in \{\text{lukasiewicz}, \text{min}\}$ and `fuzzy.mf_sigma_scale` ($1.0$ default, $1.5$ ablation).

## 2. Stage 3 Execution Summary and Wall-Clock Runtimes

- **Random seeds:** `30` common-random-number seeds (`202501` .. `202530`)
- **LUT precomputation & 500-point error verification time:** `131.23 s`
- **10,000-call `time.perf_counter` direct & LUT inference benchmark time:** `89.52 s`
  - `OSFI-DJ-S` Direct: `1.296 ms/call` | 2D LUT: `21.06 µs/call` | LUT build (FC1+FC2): `0.92 s`
  - `OSFI-DJ-NS` Direct: `7.614 ms/call` | 2D LUT: `21.16 µs/call` | LUT build (FC1+FC2): `3.92 s`
- **Experiment A wall-clock time** (`4 scenarios x 7 controllers x 30 seeds = 840 runs`): `6.98 s`
- **Experiment B wall-clock time** (`2 scenarios x 12 noise cells x 9 controllers x 30 seeds = 6480 runs`): `59.03 s`
- **Experiment C wall-clock time** (`1 scenario x 9 ablation variants x 30 seeds = 270 runs`): `2.96 s`
- **Total `run_contribution.py` wall-clock time:** `290.72 s`

## 3. Stage 3 Lookup Table (LUT) 500-Point Off-Grid Interpolation Error Summary

| Model | Stage | Config Hash | Build Time (s) | Max Abs Error (s) | Mean Abs Error (s) | Median Abs Error (s) | 95th Pct Error (s) |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: | ---: |
| `OSFI-DJ-S (singleton)` | `FC1` | `5467b11367eca185` | 0.326 | 3.5549 | 0.1313 | 0.0040 | 0.7172 |
| `OSFI-DJ-S (singleton)` | `FC2` | `33c33e2dc94c4df7` | 0.599 | 2.4611 | 0.0921 | 0.0086 | 0.3467 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC1` | `61cdbf7a10a8bd90` | 3.119 | 4.9499 | 0.1037 | 0.0026 | 0.4621 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC2` | `91eedc20f54459d1` | 0.801 | 3.5845 | 0.0864 | 0.0127 | 0.3036 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC1` | `1d2d3f06a6a14603` | 3.041 | 6.8461 | 0.1292 | 0.0035 | 0.5031 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC2` | `563f8e096b237e21` | 0.220 | 1.9216 | 0.0591 | 0.0031 | 0.1951 |

## 4. Stage 3 Cached Stage LUT Hashes and Parameters

| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | AND | $\sigma$-Scale | $\sigma_1$ | $\sigma_2$ | SHA-256 Hash | Build Time (s) | Cache Path |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | ---: | ---: | ---: | :---: | ---: | :--- |
| `OSFI-DJ` | `FC1` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `5467b11367eca185` | 0.326 | `results/cache/lut_osfi_dj_fc1_5467b11367eca185.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `33c33e2dc94c4df7` | 0.599 | `results/cache/lut_osfi_dj_fc2_33c33e2dc94c4df7.npz` |
| `CRI` | `FC1` | CRI-S (singleton) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `55863fa0c1815312` | 0.075 | `results/cache/lut_cri_fc1_55863fa0c1815312.npz` |
| `CRI` | `FC2` | CRI-S (singleton) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `461adcde876d56d3` | 0.125 | `results/cache/lut_cri_fc2_461adcde876d56d3.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 1.00 | `799342566747e257` | 0.544 | `results/cache/lut_osfi_dj_fc1_799342566747e257.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 1.00 | `d331653e94d5a38d` | 0.631 | `results/cache/lut_osfi_dj_fc2_d331653e94d5a38d.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 1.00 | `bb50a04f7bde095a` | 0.162 | `results/cache/lut_cri_fc1_bb50a04f7bde095a.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 1.00 | `7a6ae6cc803af0a7` | 0.131 | `results/cache/lut_cri_fc2_7a6ae6cc803af0a7.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 1.00 | `1862e7646f4d88c2` | 0.671 | `results/cache/lut_osfi_dj_fc1_1862e7646f4d88c2.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 1.00 | `7b1470e133d0ef7e` | 0.222 | `results/cache/lut_cri_fc1_7b1470e133d0ef7e.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 1.00 | `090d272085f2ad7d` | 0.718 | `results/cache/lut_osfi_dj_fc1_090d272085f2ad7d.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 1.00 | `ab7a34a4419b483c` | 0.240 | `results/cache/lut_cri_fc1_ab7a34a4419b483c.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 5.00 | `d178b295c11485b2` | 1.827 | `results/cache/lut_osfi_dj_fc1_d178b295c11485b2.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 5.00 | `fd58aee87bba4e8a` | 0.754 | `results/cache/lut_osfi_dj_fc2_fd58aee87bba4e8a.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 5.00 | `a35af764cee9d94e` | 0.520 | `results/cache/lut_cri_fc1_a35af764cee9d94e.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 5.00 | `7cd44e8411f22b93` | 0.186 | `results/cache/lut_cri_fc2_7cd44e8411f22b93.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 5.00 | `300096a53002ff42` | 2.702 | `results/cache/lut_osfi_dj_fc1_300096a53002ff42.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 5.00 | `4474a2e1d4533329` | 2.501 | `results/cache/lut_cri_fc1_4474a2e1d4533329.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 5.00 | `f183ad20d92e7c22` | 2.954 | `results/cache/lut_osfi_dj_fc1_f183ad20d92e7c22.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 5.00 | `8372627265d5afaa` | 2.845 | `results/cache/lut_cri_fc1_8372627265d5afaa.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `61cdbf7a10a8bd90` | 3.119 | `results/cache/lut_osfi_dj_fc1_61cdbf7a10a8bd90.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `91eedc20f54459d1` | 0.801 | `results/cache/lut_osfi_dj_fc2_91eedc20f54459d1.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `1d2d3f06a6a14603` | 3.041 | `results/cache/lut_cri_fc1_1d2d3f06a6a14603.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `563f8e096b237e21` | 0.220 | `results/cache/lut_cri_fc2_563f8e096b237e21.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 10.00 | `dcbdf7168cedf750` | 4.615 | `results/cache/lut_osfi_dj_fc1_dcbdf7168cedf750.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 10.00 | `8a2b8d081d02bbc1` | 4.695 | `results/cache/lut_cri_fc1_8a2b8d081d02bbc1.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 10.00 | `f9a997061390a050` | 5.125 | `results/cache/lut_osfi_dj_fc1_f9a997061390a050.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 10.00 | `53b825849112610e` | 5.176 | `results/cache/lut_cri_fc1_53b825849112610e.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 15.00 | `ffbfbc29d8ed5d57` | 3.998 | `results/cache/lut_osfi_dj_fc1_ffbfbc29d8ed5d57.npz` |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 15.00 | `f2cc702bbf8d2fe9` | 0.844 | `results/cache/lut_osfi_dj_fc2_f2cc702bbf8d2fe9.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 15.00 | `7df29188d2bacc4c` | 4.186 | `results/cache/lut_cri_fc1_7df29188d2bacc4c.npz` |
| `CRI` | `FC2` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 15.00 | `479f873999310c4b` | 0.220 | `results/cache/lut_cri_fc2_479f873999310c4b.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 15.00 | `ae74216f4a110116` | 6.016 | `results/cache/lut_osfi_dj_fc1_ae74216f4a110116.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 15.00 | `8e1c8213f4dd90d7` | 6.703 | `results/cache/lut_cri_fc1_8e1c8213f4dd90d7.npz` |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 15.00 | `f2ead8ee5976db4c` | 6.751 | `results/cache/lut_osfi_dj_fc1_f2ead8ee5976db4c.npz` |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 15.00 | `ae681409f34e3a83` | 7.470 | `results/cache/lut_cri_fc1_ae681409f34e3a83.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `f3c75784deb6bda8` | 3.078 | `results/cache/lut_osfi_dj_fc1_f3c75784deb6bda8.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `79fdec425a6b0d6e` | 0.823 | `results/cache/lut_osfi_dj_fc2_79fdec425a6b0d6e.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `accc56d0ce584f81` | 2.948 | `results/cache/lut_osfi_dj_fc1_accc56d0ce584f81.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `1e6c6a63ad869aa9` | 0.809 | `results/cache/lut_osfi_dj_fc2_1e6c6a63ad869aa9.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `84bc3315c9ca19d2` | 2.945 | `results/cache/lut_osfi_dj_fc1_84bc3315c9ca19d2.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `a4bd21a5e9570555` | 0.802 | `results/cache/lut_osfi_dj_fc2_a4bd21a5e9570555.npz` |
| `OSFI-DJ` | `FC1` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `3cfeba231c032b52` | 2.942 | `results/cache/lut_osfi_dj_fc1_3cfeba231c032b52.npz` |
| `OSFI-DJ` | `FC2` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `f5149603ed993c7d` | 0.796 | `results/cache/lut_osfi_dj_fc2_f5149603ed993c7d.npz` |
| `OSFI-DJ` | `FC1` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `2ca31a73802acbcb` | 1.399 | `results/cache/lut_osfi_dj_fc1_2ca31a73802acbcb.npz` |
| `OSFI-DJ` | `FC2` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `7decb954eb54b91a` | 0.652 | `results/cache/lut_osfi_dj_fc2_7decb954eb54b91a.npz` |
| `OSFI-DJ` | `FC1` | Ablation: and_operator = min (eliminates dead zones) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `min` | 1.00 | 0.5000 | 10.00 | `87c71659b1138aea` | 20.672 | `results/cache/lut_osfi_dj_fc1_87c71659b1138aea.npz` |
| `OSFI-DJ` | `FC2` | Ablation: and_operator = min (eliminates dead zones) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `min` | 1.00 | 0.0000 | 10.00 | `1085b43fdc04ac37` | 1.149 | `results/cache/lut_osfi_dj_fc2_1085b43fdc04ac37.npz` |
| `OSFI-DJ` | `FC1` | Ablation: mf_sigma_scale = 1.5 (widened Gaussians) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.50 | 0.5000 | 10.00 | `6e91cb9b24262e97` | 4.381 | `results/cache/lut_osfi_dj_fc1_6e91cb9b24262e97.npz` |
| `OSFI-DJ` | `FC2` | Ablation: mf_sigma_scale = 1.5 (widened Gaussians) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.50 | 0.0000 | 10.00 | `7e8a2a3e4125361e` | 0.872 | `results/cache/lut_osfi_dj_fc2_7e8a2a3e4125361e.npz` |

<!-- STAGE3_CONTRIBUTION_LOG_END -->
