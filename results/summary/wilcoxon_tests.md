# Paired Wilcoxon Signed-Rank Tests (`n = 30` Common-Random-Number Seeds)

| Scenario | Metric | Comparison | OSFI-literal Mean | Baseline Mean | Mean Diff (OSFI - Base) | Wilcoxon Stat | Raw $p$-value | Holm $p$ (Pair) | Holm $p$ (All) | Sig. ($\alpha=0.05$)? |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| `heavy` | `avg_delay_s` | OSFI-literal vs Mamdani | 63.788 | 25.583 | +38.206 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `heavy` | `avg_delay_s` | OSFI-literal vs Sugeno | 63.788 | 44.520 | +19.269 | 53.0 | 7.911e-05 | 7.911e-05 | 0.0007911 | Yes |
| `heavy` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 63.547 | 25.560 | +37.987 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `heavy` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 63.547 | 44.528 | +19.018 | 57.0 | 0.0001233 | 0.0001233 | 0.00111 | Yes |
| `heavy` | `throughput_veh` | OSFI-literal vs Mamdani | 1483.933 | 1502.600 | -18.667 | 51.5 | 0.0003298 | 0.0006596 | 0.002638 | Yes |
| `heavy` | `throughput_veh` | OSFI-literal vs Sugeno | 1483.933 | 1491.400 | -7.467 | 109.0 | 0.03226 | 0.03226 | 0.129 | Yes |
| `moderate` | `avg_delay_s` | OSFI-literal vs Mamdani | 24.745 | 21.127 | +3.619 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `moderate` | `avg_delay_s` | OSFI-literal vs Sugeno | 24.745 | 21.515 | +3.231 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `moderate` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 24.704 | 21.119 | +3.585 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `moderate` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 24.704 | 21.509 | +3.195 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `moderate` | `throughput_veh` | OSFI-literal vs Mamdani | 1108.000 | 1108.500 | -0.500 | 159.0 | 0.672 | 0.672 | 0.672 | No |
| `moderate` | `throughput_veh` | OSFI-literal vs Sugeno | 1108.000 | 1109.133 | -1.133 | 97.0 | 0.07596 | 0.1519 | 0.2279 | No |
| `peak` | `avg_delay_s` | OSFI-literal vs Mamdani | 219.229 | 27.716 | +191.513 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `peak` | `avg_delay_s` | OSFI-literal vs Sugeno | 219.229 | 192.967 | +26.262 | 51.0 | 6.287e-05 | 6.287e-05 | 0.0006915 | Yes |
| `peak` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 225.286 | 27.688 | +197.598 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `peak` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 225.286 | 198.699 | +26.587 | 48.0 | 4.408e-05 | 4.408e-05 | 0.0005289 | Yes |
| `peak` | `throughput_veh` | OSFI-literal vs Mamdani | 1471.933 | 1627.567 | -155.633 | 0.0 | 1.727e-06 | 3.454e-06 | 2.417e-05 | Yes |
| `peak` | `throughput_veh` | OSFI-literal vs Sugeno | 1471.933 | 1487.100 | -15.167 | 65.0 | 0.0009724 | 0.0009724 | 0.005585 | Yes |
| `stress` | `avg_delay_s` | OSFI-literal vs Mamdani | 390.919 | 29.476 | +361.442 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `stress` | `avg_delay_s` | OSFI-literal vs Sugeno | 390.919 | 366.763 | +24.156 | 76.0 | 0.0007979 | 0.0007979 | 0.005585 | Yes |
| `stress` | `avg_delay_incl_queued_s` | OSFI-literal vs Mamdani | 393.052 | 29.430 | +363.623 | 0.0 | 1.863e-09 | 3.725e-09 | 4.47e-08 | Yes |
| `stress` | `avg_delay_incl_queued_s` | OSFI-literal vs Sugeno | 393.052 | 370.081 | +22.971 | 77.0 | 0.0008718 | 0.0008718 | 0.005585 | Yes |
| `stress` | `throughput_veh` | OSFI-literal vs Mamdani | 1500.633 | 1800.767 | -300.133 | 0.0 | 1.732e-06 | 3.464e-06 | 2.417e-05 | Yes |
| `stress` | `throughput_veh` | OSFI-literal vs Sugeno | 1500.633 | 1506.300 | -5.667 | 144.0 | 0.1116 | 0.1116 | 0.2279 | No |
