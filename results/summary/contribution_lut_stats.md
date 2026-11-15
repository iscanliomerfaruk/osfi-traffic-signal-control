# Lookup Table (LUT) Build Time and Interpolation Error Report

- **Total LUT preparation wall-clock time:** `131.23 s`
- **Sum of single-LUT build times across `50` cached tables:** `125.98 s`

## 1. Off-Grid Bilinear Interpolation Accuracy (`500` Random Points per Stage vs. Direct Inference)

| Model | Stage | Config Hash | Build Time (s) | Samples | Max Abs Error (s) | Mean Abs Error (s) | Median Abs Error (s) | 95th Pct Error (s) |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `OSFI-DJ-S (singleton)` | `FC1` | `5467b11367eca185` | 0.326 | 500 | 3.5549 | 0.1313 | 0.0040 | 0.7172 |
| `OSFI-DJ-S (singleton)` | `FC2` | `33c33e2dc94c4df7` | 0.599 | 500 | 2.4611 | 0.0921 | 0.0086 | 0.3467 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC1` | `61cdbf7a10a8bd90` | 3.119 | 500 | 4.9499 | 0.1037 | 0.0026 | 0.4621 |
| `OSFI-DJ-NS (sigma_q=10, p_miss=0)` | `FC2` | `91eedc20f54459d1` | 0.801 | 500 | 3.5845 | 0.0864 | 0.0127 | 0.3036 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC1` | `1d2d3f06a6a14603` | 3.041 | 500 | 6.8461 | 0.1292 | 0.0035 | 0.5031 |
| `CRI-NS (sigma_q=10, p_miss=0)` | `FC2` | `563f8e096b237e21` | 0.220 | 500 | 1.9216 | 0.0591 | 0.0031 | 0.1951 |

> **Note on `Max Abs Error`:** On smooth interior regions, bilinear interpolation error is $< 0.05\text{ s}$ (median error $\approx 0.00-0.02\text{ s}$). Larger maximum differences occur only on the narrow grid cells straddling the boundary of the Łukasiewicz dead-zone pocket ($a_1 + a_2 = 1$), where direct inference switches between the nearest-rule fallback and active rule outputs.

## 2. Cached Stage LUT Inventory

| Engine | Stage | Configuration Label | Implicator | Tie-Break | Defuzzifier | Shoulders | AND | $\sigma$-Scale | $\sigma_1$ | $\sigma_2$ | Hash | Build Time (s) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | ---: | ---: | ---: | :---: | ---: |
| `OSFI-DJ` | `FC1` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `5467b11367eca185` | 0.326 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-S (singleton) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `33c33e2dc94c4df7` | 0.599 |
| `CRI` | `FC1` | CRI-S (singleton) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `55863fa0c1815312` | 0.075 |
| `CRI` | `FC2` | CRI-S (singleton) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 0.00 | `461adcde876d56d3` | 0.125 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 1.00 | `799342566747e257` | 0.544 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 1.00 | `d331653e94d5a38d` | 0.631 |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 1.00 | `bb50a04f7bde095a` | 0.162 |
| `CRI` | `FC2` | CRI-NS (sigma_q=0, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 1.00 | `7a6ae6cc803af0a7` | 0.131 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 1.00 | `1862e7646f4d88c2` | 0.671 |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 1.00 | `7b1470e133d0ef7e` | 0.222 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 1.00 | `090d272085f2ad7d` | 0.718 |
| `CRI` | `FC1` | CRI-NS (sigma_q=0, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 1.00 | `ab7a34a4419b483c` | 0.240 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 5.00 | `d178b295c11485b2` | 1.827 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 5.00 | `fd58aee87bba4e8a` | 0.754 |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 5.00 | `a35af764cee9d94e` | 0.520 |
| `CRI` | `FC2` | CRI-NS (sigma_q=5, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 5.00 | `7cd44e8411f22b93` | 0.186 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 5.00 | `300096a53002ff42` | 2.702 |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 5.00 | `4474a2e1d4533329` | 2.501 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 5.00 | `f183ad20d92e7c22` | 2.954 |
| `CRI` | `FC1` | CRI-NS (sigma_q=5, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 5.00 | `8372627265d5afaa` | 2.845 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `61cdbf7a10a8bd90` | 3.119 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `91eedc20f54459d1` | 0.801 |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `1d2d3f06a6a14603` | 3.041 |
| `CRI` | `FC2` | CRI-NS (sigma_q=10, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `563f8e096b237e21` | 0.220 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 10.00 | `dcbdf7168cedf750` | 4.615 |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 10.00 | `8a2b8d081d02bbc1` | 4.695 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 10.00 | `f9a997061390a050` | 5.125 |
| `CRI` | `FC1` | CRI-NS (sigma_q=10, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 10.00 | `53b825849112610e` | 5.176 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 15.00 | `ffbfbc29d8ed5d57` | 3.998 |
| `OSFI-DJ` | `FC2` | OSFI-DJ-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 15.00 | `f2cc702bbf8d2fe9` | 0.844 |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 15.00 | `7df29188d2bacc4c` | 4.186 |
| `CRI` | `FC2` | CRI-NS (sigma_q=15, p_miss=0) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 15.00 | `479f873999310c4b` | 0.220 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 15.00 | `ae74216f4a110116` | 6.016 |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.1) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.7937 | 15.00 | `8e1c8213f4dd90d7` | 6.703 |
| `OSFI-DJ` | `FC1` | OSFI-DJ-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 15.00 | `f2ead8ee5976db4c` | 6.751 |
| `CRI` | `FC1` | CRI-NS (sigma_q=15, p_miss=0.2) | `lukasiewicz` | `n/a` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.8775 | 15.00 | `ae681409f34e3a83` | 7.470 |
| `OSFI-DJ` | `FC1` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `f3c75784deb6bda8` | 3.078 |
| `OSFI-DJ` | `FC2` | Ablation: Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `79fdec425a6b0d6e` | 0.823 |
| `OSFI-DJ` | `FC1` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `accc56d0ce584f81` | 2.948 |
| `OSFI-DJ` | `FC2` | Ablation: Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `1e6c6a63ad869aa9` | 0.809 |
| `OSFI-DJ` | `FC1` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `84bc3315c9ca19d2` | 2.945 |
| `OSFI-DJ` | `FC2` | Ablation: Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `a4bd21a5e9570555` | 0.802 |
| `OSFI-DJ` | `FC1` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `3cfeba231c032b52` | 2.942 |
| `OSFI-DJ` | `FC2` | Ablation: Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `f5149603ed993c7d` | 0.796 |
| `OSFI-DJ` | `FC1` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | `lukasiewicz` | 1.00 | 0.5000 | 10.00 | `2ca31a73802acbcb` | 1.399 |
| `OSFI-DJ` | `FC2` | Ablation: shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | `lukasiewicz` | 1.00 | 0.0000 | 10.00 | `7decb954eb54b91a` | 0.652 |
| `OSFI-DJ` | `FC1` | Ablation: and_operator = min (eliminates dead zones) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `min` | 1.00 | 0.5000 | 10.00 | `87c71659b1138aea` | 20.672 |
| `OSFI-DJ` | `FC2` | Ablation: and_operator = min (eliminates dead zones) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `min` | 1.00 | 0.0000 | 10.00 | `1085b43fdc04ac37` | 1.149 |
| `OSFI-DJ` | `FC1` | Ablation: mf_sigma_scale = 1.5 (widened Gaussians) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.50 | 0.5000 | 10.00 | `6e91cb9b24262e97` | 4.381 |
| `OSFI-DJ` | `FC2` | Ablation: mf_sigma_scale = 1.5 (widened Gaussians) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.50 | 0.0000 | 10.00 | `7e8a2a3e4125361e` | 0.872 |
