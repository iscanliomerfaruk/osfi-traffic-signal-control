# Reference Paper (Tables 1–2) vs. Our Reproduction (`n = 30` Seeds)

> **Note on physical comparability:** In Esmaeili et al. (2025), Tables 1 and 2 report average delays of `1.011–1.210 s/veh` across a 4-phase intersection where only one approach receives green at a time. Under any physically realizable 4-phase signal cycle ($G_{\min} = 7\text{ s}$, intergreen $= 5\text{ s}$, minimum cycle $\ge 48\text{ s}$), vehicles arriving on the three red approaches wait tens of seconds on average. Hence absolute delay magnitudes in our queueing simulation are on the physically expected scale ($\sim 50–180\text{ s/veh}$), and comparison focuses on **relative rankings, directional changes, and structural behavior**.
> Furthermore, in the paper's Tables 1 and 2, the `Average Exit (veh)` percentage columns report lower OSFI throughput (e.g., `310` vs `328` in Table 1 Phase E) as a positive `+5.49%` improvement; in our columns we use the physically correct sign convention where higher throughput is positive.

## Moderate Traffic (Paper Table 1 vs. Ours)

| Indicator | Phase | Paper Mamdani | Paper Sugeno | Paper OSFI | Paper % vs M | Paper % vs S | Our Mamdani | Our Sugeno | Our OSFI-literal | Our % vs M | Our % vs S |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Average Delay (s) | E | 1.048 | 1.018 | 1.011 | 3.55% | 0.69% | 17.15 | 17.26 | 20.15 | -17.52% | -16.73% |
| Average Delay (s) | S | 1.210 | 1.199 | 1.182 | 2.31% | 1.42% | 16.26 | 17.04 | 19.82 | -21.88% | -16.32% |
| Average Delay (s) | W | 1.172 | 1.183 | 1.153 | 1.62% | 2.54% | 30.35 | 29.87 | 33.81 | -11.40% | -13.17% |
| Average Delay (s) | N | 1.062 | 1.074 | 1.022 | 3.78% | 4.84% | 31.55 | 32.43 | 36.72 | -16.38% | -13.23% |
| Average Exit (veh) | E | 328 | 320 | 310 | 5.49% | 3.13% | 342.8 | 343.4 | 343.1 | +0.11% | -0.09% |
| Average Exit (veh) | S | 398 | 397 | 387 | 2.76% | 2.52% | 415.9 | 416.2 | 415.5 | -0.08% | -0.15% |
| Average Exit (veh) | W | 165 | 145 | 138 | 16.36% | 4.83% | 173.8 | 173.8 | 173.4 | -0.27% | -0.27% |
| Average Exit (veh) | N | 173 | 175 | 173 | 0.58% | 1.14% | 176.0 | 175.7 | 176.0 | -0.04% | +0.15% |

## Heavy Traffic (Paper Table 2 vs. Ours)

| Indicator | Phase | Paper Mamdani | Paper Sugeno | Paper OSFI | Paper % vs M | Paper % vs S | Our Mamdani | Our Sugeno | Our OSFI-literal | Our % vs M | Our % vs S |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Average Delay (s) | E | 1.137 | 1.126 | 1.098 | 3.64% | 2.55% | 21.23 | 37.05 | 53.23 | -150.73% | -43.68% |
| Average Delay (s) | S | 1.178 | 1.201 | 1.165 | 1.11% | 3.09% | 19.25 | 32.93 | 47.82 | -148.42% | -45.22% |
| Average Delay (s) | W | 1.172 | 1.154 | 1.132 | 3.53% | 1.94% | 37.50 | 66.35 | 92.92 | -147.83% | -40.04% |
| Average Delay (s) | N | 1.144 | 1.131 | 1.082 | 5.73% | 4.52% | 37.40 | 65.47 | 94.35 | -152.27% | -44.11% |
| Average Exit (veh) | E | 347 | 321 | 298 | 16.44% | 7.71% | 465.3 | 462.1 | 459.7 | -1.19% | -0.51% |
| Average Exit (veh) | S | 381 | 385 | 362 | 5.20% | 6.35% | 560.5 | 556.8 | 554.5 | -1.08% | -0.41% |
| Average Exit (veh) | W | 152 | 137 | 128 | 18.75% | 2.34% | 232.0 | 230.7 | 228.7 | -1.44% | -0.87% |
| Average Exit (veh) | N | 186 | 185 | 178 | 4.49% | 3.93% | 244.8 | 241.9 | 241.1 | -1.54% | -0.33% |
