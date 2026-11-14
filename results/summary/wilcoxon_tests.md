# Paired Wilcoxon Signed-Rank Tests (`n = 30` Common-Random-Number Seeds)

| Scenario | Metric | Comparison | OSFI-literal Mean | Baseline Mean | Mean Diff (OSFI - Base) | Wilcoxon Stat | Raw $p$-value | Holm $p$ (Pair) | Holm $p$ (All) | Sig. ($\alpha=0.05$)? |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `heavy` | `avg_delay_s` | OSFI-literal vs Mamdani | 921.426 | 780.636 | +140.790 | 0.0 | 1.863e-09 | 3.725e-09 | 3.353e-08 | Yes |
| `heavy` | `avg_delay_s` | OSFI-literal vs Sugeno | 921.426 | 922.691 | -1.265 | 131.0 | 0.3967 | 0.3967 | 1 | No |
| `heavy` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 947.782 | 795.554 | +152.229 | 0.0 | 1.863e-09 | 3.725e-09 | 3.353e-08 | Yes |
| `heavy` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 947.782 | 948.476 | -0.694 | 140.0 | 0.5449 | 0.5449 | 1 | No |
| `heavy` | `throughput_veh` | OSFI-literal vs Mamdani | 1502.367 | 1673.433 | -171.067 | 0.0 | 1.731e-06 | 3.462e-06 | 2.073e-05 | Yes |
| `heavy` | `throughput_veh` | OSFI-literal vs Sugeno | 1502.367 | 1502.267 | +0.100 | 107.5 | 0.7805 | 0.7805 | 1 | No |
| `moderate` | `avg_delay_s` | OSFI-literal vs Mamdani | 405.132 | 258.617 | +146.516 | 0.0 | 1.863e-09 | 3.725e-09 | 3.353e-08 | Yes |
| `moderate` | `avg_delay_s` | OSFI-literal vs Sugeno | 405.132 | 400.522 | +4.610 | 140.0 | 0.09378 | 0.09378 | 0.844 | No |
| `moderate` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 405.404 | 258.198 | +147.206 | 0.0 | 1.863e-09 | 3.725e-09 | 3.353e-08 | Yes |
| `moderate` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 405.404 | 401.658 | +3.746 | 143.0 | 0.1072 | 0.1072 | 0.8576 | No |
| `moderate` | `throughput_veh` | OSFI-literal vs Mamdani | 1500.400 | 1626.033 | -125.633 | 0.0 | 1.728e-06 | 3.456e-06 | 2.073e-05 | Yes |
| `moderate` | `throughput_veh` | OSFI-literal vs Sugeno | 1500.400 | 1500.033 | +0.367 | 178.5 | 0.8003 | 0.8003 | 1 | No |
| `peak` | `avg_delay_s` | OSFI-literal vs Mamdani | 585.745 | 505.600 | +80.145 | 0.0 | 1.863e-09 | 3.725e-09 | 3.353e-08 | Yes |
| `peak` | `avg_delay_s` | OSFI-literal vs Sugeno | 585.745 | 582.110 | +3.635 | 171.0 | 0.2129 | 0.2129 | 1 | No |
| `peak` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 695.020 | 583.356 | +111.663 | 0.0 | 1.863e-09 | 3.725e-09 | 3.353e-08 | Yes |
| `peak` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 695.020 | 692.015 | +3.005 | 177.0 | 0.2621 | 0.2621 | 1 | No |
| `peak` | `throughput_veh` | OSFI-literal vs Mamdani | 1509.167 | 1657.067 | -147.900 | 0.0 | 1.728e-06 | 3.456e-06 | 2.073e-05 | Yes |
| `peak` | `throughput_veh` | OSFI-literal vs Sugeno | 1509.167 | 1509.967 | -0.800 | 202.5 | 0.7455 | 0.7455 | 1 | No |
