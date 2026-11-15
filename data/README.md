# Dataset & Synthetic Traffic Demand Generation (`data/`)

No external empirical dataset is used in this project. In the reference paper — Esmaeili et al. (2025), *"An optimization similarity fuzzy inference method for traffic signal control at an isolated intersection"* (`Multimodal Transportation`, vol. 4, 100234) — traffic arrivals at the four-phase isolated intersection are modeled as stochastic Poisson arrival processes with exponential service ($M/M/1$ queueing per approach, Section 4), and no external dataset files or exact hourly demand volumes are published alongside the paper.

## 1. Calibration to the Reference Paper

Our synthetic Poisson demand generator (`src/osfi_tsc/sim/demand.py`) is calibrated directly to two quantitative constraints from the reference paper:

1. **Directional Approach Split (`Table 1` Mamdani Exit Counts):**
   In Table 1 (`Moderate`), the reference paper reports per-phase Mamdani exit counts of:
   - East (`E`): $328\text{ veh}$ ($328 / 1064 = 0.30827$)
   - South (`S`): $398\text{ veh}$ ($398 / 1064 = 0.37406$)
   - West (`W`): $165\text{ veh}$ ($165 / 1064 = 0.15508$)
   - North (`N`): $173\text{ veh}$ ($173 / 1064 = 0.16259$)
   - **Total hourly exit sum:** $328 + 398 + 165 + 173 = 1064\text{ veh/h}$.

2. **Queue Length Universe Calibration (`[0, 60] m/lane`):**
   Figures 5 and 7 define the queue length universe as $[0, 60]\text{ m/lane}$ with Gaussian membership function centers at $\text{Sh}=0, \text{M}=15, \text{L}=30, \text{VL}=45\text{ m}$ ($\sigma_q = 5.0\text{ m}$). At $7.0\text{ m/veh}$ across $2\text{ lanes/approach}$ ($3.5\text{ m/lane}$ per queued vehicle), $60\text{ m/lane}$ corresponds to $\approx 8.6\text{ veh/lane}$ ($17\text{ vehicles}$ per approach).

## 2. Scenario Definitions (`configs/scenarios/*.yaml`)

All scenario demand profiles are loaded from `configs/scenarios/*.yaml` (single source of truth):

| Scenario | YAML File | Profile Type | Total Demand $Q_{\text{tot}}(t)$ | Webster Flow Ratio $Y = \sum_i q_i / s_i$ | Purpose |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `moderate` | `configs/scenarios/moderate.yaml` | Constant | $1100\text{ veh/h}$ | $0.3056$ | Matches Table 1 exit volume ($\approx 1064\text{ veh/h}$) |
| `heavy` | `configs/scenarios/heavy.yaml` | Constant | $1500\text{ veh/h}$ | $0.4167$ | Exercises interior of $[0, 60]\text{ m}$ queue universe (`Sh`, `M`, `L`) |
| `peak` | `configs/scenarios/peak.yaml` | Trapezoid | $1100 \to 1800 \to 1100\text{ veh/h}$ ($900\text{ s}$ ramp up, $1800\text{ s}$ plateau, $900\text{ s}$ ramp down; mean $1625\text{ veh/h}$) | $0.4514$ | Time-of-day rush-hour surge evaluation |
| `stress` | `configs/scenarios/stress.yaml` | Constant | $1800\text{ veh/h}$ | $0.5000$ | Near-saturation regime exposing zero-order TSK/OSFI-literal collapse |

## 3. Common Random Numbers (CRN) and How to Regenerate Streams

For every seed $s \in \{202501, \dots, 202530\}$ and scenario (`warmup_s = 600`, `measurement_s = 3600`, $\Delta t = 1\text{ s}$), identical arrival and sensor-noise streams are pre-generated deterministically using isolated `numpy.random.Generator` (`PCG64`) streams:
- **True Poisson vehicle arrivals:** `seed = s` via `pregenerate_arrivals(scenario, seed=s)`
- **Exponential departure service capacity:** `seed = s + 1_000_003`
- **Additive Gaussian queue sensor noise ($\sigma_q$):** `seed = s + 2_000_003`
- **Binomial missed-arrival thinning ($p_{\text{miss}}$) + Poisson false detections ($\varepsilon = 0.02\text{ veh/s}$):** `seed = s + 3_000_003`

To regenerate a demand stream or inspect per-step arrival counts from Python:

```bash
python -c "
from osfi_tsc.sim import ScenarioDemand, pregenerate_arrivals
scen = ScenarioDemand.from_name('moderate')
arr = pregenerate_arrivals(scen, seed=202501, warmup_s=600, measurement_s=3600, dt=1.0)
print({k: int(v[600:].sum()) for k, v in arr.items()})
"
```

To regenerate all simulation datasets and summary tables from scratch:

```bash
python scripts/run_reproduction.py
python scripts/run_contribution.py
```
