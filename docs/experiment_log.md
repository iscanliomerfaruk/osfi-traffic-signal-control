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
