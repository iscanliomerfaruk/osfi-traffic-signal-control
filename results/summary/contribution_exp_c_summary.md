# Experiment C — Ablation Study on `OSFI-DJ-NS` (`heavy`, $\sigma_q = 10\text{ m}$, $p_{\text{miss}} = 0$, `n = 30` Seeds)

| Factor | Variant | Implicator | Tie-Break | Defuzzifier | `shoulder_edges` | Avg Delay (s/veh) $\pm$ 95% CI | Throughput (veh) $\pm$ 95% CI | Switches | Fallback Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: |
| Baseline | Łukasiewicz + smallest + above_floor + shoulder | `lukasiewicz` | `smallest` | `centroid_above_floor` | `True` | 808.53 $\pm$ 21.53 | 1653.5 $\pm$ 16.9 | 277.5 | 0.00% |
| Implicator | Goguen implicator | `goguen` | `smallest` | `centroid_above_floor` | `True` | 834.66 $\pm$ 18.95 | 1615.9 $\pm$ 15.6 | 282.8 | 6.98% |
| Implicator | Kleene-Dienes implicator | `kleene_dienes` | `smallest` | `centroid_above_floor` | `True` | 809.44 $\pm$ 21.23 | 1651.7 $\pm$ 13.5 | 277.8 | 0.00% |
| Tie-break | Midpoint tie-break | `lukasiewicz` | `midpoint` | `centroid_above_floor` | `True` | 809.21 $\pm$ 21.92 | 1651.8 $\pm$ 16.7 | 277.7 | 0.00% |
| Defuzzifier | Standard centroid (with floor) | `lukasiewicz` | `smallest` | `centroid` | `True` | 795.63 $\pm$ 22.68 | 1653.2 $\pm$ 16.0 | 277.7 | 0.00% |
| Boundary MFs | shoulder_edges = False | `lukasiewicz` | `smallest` | `centroid_above_floor` | `False` | 802.85 $\pm$ 20.49 | 1647.9 $\pm$ 13.8 | 278.0 | 34.70% |
