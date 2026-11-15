# Experiment C — Ablation Study on `OSFI-DJ-NS` (`heavy`, $\sigma_q = 10\text{ m}$, $p_{\text{miss}} = 0$, `n = 30` Seeds)

| Factor | Variant | Implicator | Tie-Break | Defuzzifier | `shoulder_edges` | AND | $\sigma$-Scale | `spm_mode` | Avg Delay (s/veh) $\pm$ 95% CI | Throughput (veh) $\pm$ 95% CI | Switches | Dead-Zone Fallback Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | ---: | :---: | ---: | ---: | ---: | ---: |
| Baseline | Łukasiewicz + smallest + above_floor + shoulder + gpe_first | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.0 | `gpe_first` | 33.44 $\pm$ 0.59 | 1500.6 $\pm$ 16.4 | 193.7 | 2.56% |
| Implicator | Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.0 | `gpe_first` | 32.04 $\pm$ 0.35 | 1502.4 $\pm$ 16.6 | 206.1 | 1.04% |
| Implicator | Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.0 | `gpe_first` | 34.31 $\pm$ 0.59 | 1501.8 $\pm$ 16.4 | 216.8 | 27.88% |
| Tie-break | Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.0 | `gpe_first` | 33.34 $\pm$ 0.46 | 1500.7 $\pm$ 16.4 | 194.0 | 2.65% |
| Defuzzifier | Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | `lukasiewicz` | 1.0 | `gpe_first` | 49.60 $\pm$ 0.75 | 1502.0 $\pm$ 16.1 | 110.0 | 0.00% |
| Boundary MFs | shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | `lukasiewicz` | 1.0 | `gpe_first` | 33.31 $\pm$ 0.50 | 1500.9 $\pm$ 16.5 | 194.5 | 2.65% |
| Antecedent AND | and_operator = min (eliminates dead zones) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `min` | 1.0 | `gpe_first` | 33.88 $\pm$ 0.47 | 1501.5 $\pm$ 16.3 | 188.8 | 0.00% |
| MF Width | mf_sigma_scale = 1.5 (widened Gaussians) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.5 | `gpe_first` | 32.90 $\pm$ 0.48 | 1501.8 $\pm$ 16.0 | 193.9 | 0.00% |
| Phase Switching | spm_mode = preempt (thrashing ablation) | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | `lukasiewicz` | 1.0 | `preempt` | 55.54 $\pm$ 9.97 | 1499.4 $\pm$ 17.7 | 276.0 | 2.90% |
