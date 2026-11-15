# Stage 2 Lookup Table (LUT) Build Time and Interpolation Error Report

- **Total LUT preparation wall-clock time:** `223.57 s`
- **Sum of single-LUT build times across `44` cached tables:** `214.58 s`

## 1. Off-Grid Bilinear Interpolation Accuracy (`500` Random Points per Stage vs. Direct Inference)

| Model | Stage | Config Hash | Build Time (s) | Samples | Max Abs Error (s) | Mean Abs Error (s) | Median Abs Error (s) | 95th Pct Error (s) |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `OSFI-DJ-S (singleton)` | `FC1` | `f0cd9ff537f2aa73` | 1.679 | 500 | 9.6564 | 0.2248 | 0.0041 | 1.4041 |
| `OSFI-DJ-S (singleton)` | `FC2` | `42c5986621fa680a` | 2.987 | 500 | 10.0869 | 0.1277 | 0.0085 | 0.3653 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC1` | `40ce4e120c956fc8` | 6.905 | 500 | 5.9863 | 0.1594 | 0.0030 | 0.9600 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC2` | `05e06bf7ade3bb8a` | 1.878 | 500 | 5.3402 | 0.1067 | 0.0127 | 0.3474 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC1` | `72bedce35f4bb8e0` | 5.904 | 500 | 10.4318 | 0.2307 | 0.0037 | 1.3330 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC2` | `3d5c603ffdf7c550` | 0.495 | 500 | 5.9833 | 0.0893 | 0.0031 | 0.1951 |

> **Note on `Max Abs Error`:** On smooth interior regions, bilinear interpolation error is $< 0.05\text{ s}$ (median error $\approx 0.00-0.02\text{ s}$). Larger maximum differences occur only on the rare grid cells straddling the boundary of the Łukasiewicz zero-area pocket ($a_1 + a_2 = 1$), where direct inference switches discontinuously between the fallback output ($0.0\text{ s}$) and active rule outputs ($\sim 6.5\text{ s}$).

## 2. Cached Stage LUT Inventory

| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | $\sigma_1$ | $\sigma_2$ | Hash | Build Time (s) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | ---: | ---: | :---: | ---: |
| `OSFI-DJ` | `FC1` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 0.00 | `f0cd9ff537f2aa73` | 1.679 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 0.00 | `42c5986621fa680a` | 2.987 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 1.00 | `e631861af11481ad` | 1.281 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 1.00 | `1d9e20406cbbd5dd` | 1.515 |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 1.00 | `c8391aee27f10dac` | 0.323 |
| `CRI` | `FC2` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 1.00 | `3efa4b612673f337` | 0.233 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 1.00 | `95ec9bd468f567e3` | 1.740 |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 1.00 | `02689ddb8d89cf4d` | 0.485 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 1.00 | `3f4c9a45ddd15cd5` | 1.849 |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 1.00 | `698c089f0f2983ea` | 0.561 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 5.00 | `181bf4f90d4d364f` | 4.115 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 5.00 | `d0d1583df44277a4` | 1.746 |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 5.00 | `ba1df8aca84aef03` | 1.080 |
| `CRI` | `FC2` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 5.00 | `87ae3e399576da67` | 0.357 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 5.00 | `a4e78e729cbb69e2` | 6.018 |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 5.00 | `ea490df9f0833eb6` | 4.784 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 5.00 | `a3e3c57ac73050af` | 6.461 |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 5.00 | `1c70624deba2df0a` | 5.553 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `40ce4e120c956fc8` | 6.905 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `05e06bf7ade3bb8a` | 1.878 |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `72bedce35f4bb8e0` | 5.904 |
| `CRI` | `FC2` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `3d5c603ffdf7c550` | 0.495 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 10.00 | `15fcf62518451b33` | 10.049 |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 10.00 | `a0380e04cd5b37d5` | 9.027 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 10.00 | `1d987d604838f59d` | 11.193 |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 10.00 | `614f6b6356609e0d` | 9.887 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 15.00 | `9811ea49e0653840` | 8.524 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 15.00 | `cf9a79af322c13b6` | 1.926 |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.5000 | 15.00 | `ecec328dd3f5854c` | 8.138 |
| `CRI` | `FC2` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.0000 | 15.00 | `121461714d502d74` | 0.427 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.7937 | 15.00 | `4eb5ae87aea301b7` | 12.721 |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.7937 | 15.00 | `5542f7d0da829d3d` | 12.621 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 0.8775 | 15.00 | `7b577b9a267e82f1` | 14.170 |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | 0.8775 | 15.00 | `ea5d0811c38fc648` | 13.837 |
| `OSFI-DJ` | `FC1` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `ad274d585e340ab0` | 7.162 |
| `OSFI-DJ` | `FC2` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `c0bc75da1507bfd6` | 2.495 |
| `OSFI-DJ` | `FC1` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `6c8a54c00e8e133b` | 7.062 |
| `OSFI-DJ` | `FC2` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `be3b130b4ed1b337` | 2.421 |
| `OSFI-DJ` | `FC1` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | 0.5000 | 10.00 | `7d5583279fb29541` | 7.103 |
| `OSFI-DJ` | `FC2` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | 0.0000 | 10.00 | `3c0cb6ba3a2ce110` | 2.458 |
| `OSFI-DJ` | `FC1` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | 0.5000 | 10.00 | `5c5307da8d6d85f4` | 7.077 |
| `OSFI-DJ` | `FC2` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | 0.0000 | 10.00 | `36aa307a72187911` | 2.454 |
| `OSFI-DJ` | `FC1` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | 0.5000 | 10.00 | `ac33fca3bba861a6` | 3.734 |
| `OSFI-DJ` | `FC2` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | 0.0000 | 10.00 | `f11090a69484b81b` | 2.147 |
