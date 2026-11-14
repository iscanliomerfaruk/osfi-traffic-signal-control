# Reference Paper (Tables 1–2) vs. Our Reproduction (`n = 30` Seeds)

> **Note on physical comparability:** In Esmaeili et al. (2025), Tables 1 and 2 report average delays of `1.011–1.210 s/veh` across a 4-phase intersection where only one approach receives green at a time. Under any physically realizable 4-phase signal cycle ($G_{\min} = 7\text{ s}$, intergreen $= 5\text{ s}$, minimum cycle $\ge 48\text{ s}$), vehicles arriving on the three red approaches wait tens of seconds on average. Hence absolute delay magnitudes in our queueing simulation are on the physically expected scale ($\sim 50–180\text{ s/veh}$), and comparison focuses on **relative rankings, directional changes, and structural behavior**.
> Furthermore, in the paper's Tables 1 and 2, the `Average Exit (veh)` percentage columns report lower OSFI throughput (e.g., `310` vs `328` in Table 1 Phase E) as a positive `+5.49%` improvement; in our columns we use the physically correct sign convention where higher throughput is positive.

## Moderate Traffic (Paper Table 1 vs. Ours)

| Indicator | Phase | Paper Mamdani | Paper Sugeno | Paper OSFI | Paper % vs M | Paper % vs S | Our Mamdani | Our Sugeno | Our OSFI-literal | Our % vs M | Our % vs S |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Average Delay (s) | E | 1.048 | 1.018 | 1.011 | 3.55% | 0.69% | 216.06 | 335.94 | 339.00 | -56.90% | -0.91% |
| Average Delay (s) | S | 1.210 | 1.199 | 1.182 | 2.31% | 1.42% | 181.57 | 289.47 | 291.93 | -60.78% | -0.85% |
| Average Delay (s) | W | 1.172 | 1.183 | 1.153 | 1.62% | 2.54% | 419.99 | 658.65 | 667.63 | -58.96% | -1.36% |
| Average Delay (s) | N | 1.062 | 1.074 | 1.022 | 3.78% | 4.84% | 400.48 | 628.13 | 636.51 | -58.94% | -1.33% |
| Average Exit (veh) | E | 328 | 320 | 310 | 5.49% | 3.13% | 513.2 | 482.6 | 480.9 | -6.29% | -0.35% |
| Average Exit (veh) | S | 398 | 397 | 387 | 2.76% | 2.52% | 627.3 | 594.2 | 594.0 | -5.31% | -0.04% |
| Average Exit (veh) | W | 165 | 145 | 138 | 16.36% | 4.83% | 235.5 | 204.2 | 205.3 | -12.84% | +0.51% |
| Average Exit (veh) | N | 173 | 175 | 173 | 0.58% | 1.14% | 250.1 | 219.0 | 220.2 | -11.93% | +0.58% |

## Heavy Traffic (Paper Table 2 vs. Ours)

| Indicator | Phase | Paper Mamdani | Paper Sugeno | Paper OSFI | Paper % vs M | Paper % vs S | Our Mamdani | Our Sugeno | Our OSFI-literal | Our % vs M | Our % vs S |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Average Delay (s) | E | 1.137 | 1.126 | 1.098 | 3.64% | 2.55% | 687.76 | 830.03 | 831.30 | -20.87% | -0.15% |
| Average Delay (s) | S | 1.178 | 1.201 | 1.165 | 1.11% | 3.09% | 565.73 | 709.36 | 704.57 | -24.54% | +0.68% |
| Average Delay (s) | W | 1.172 | 1.154 | 1.132 | 3.53% | 1.94% | 1491.89 | 1881.75 | 1887.90 | -26.54% | -0.33% |
| Average Delay (s) | N | 1.144 | 1.131 | 1.082 | 5.73% | 4.52% | 1390.82 | 1734.05 | 1739.71 | -25.09% | -0.33% |
| Average Exit (veh) | E | 347 | 321 | 298 | 16.44% | 7.71% | 568.0 | 527.2 | 527.2 | -7.19% | -0.01% |
| Average Exit (veh) | S | 381 | 385 | 362 | 5.20% | 6.35% | 727.3 | 682.7 | 683.0 | -6.09% | +0.05% |
| Average Exit (veh) | W | 152 | 137 | 128 | 18.75% | 2.34% | 181.7 | 137.6 | 137.9 | -24.12% | +0.19% |
| Average Exit (veh) | N | 186 | 185 | 178 | 4.49% | 3.93% | 196.4 | 154.8 | 154.3 | -21.43% | -0.30% |
