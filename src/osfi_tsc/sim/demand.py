"""Traffic demand profiles, directional splits, Webster flow ratios, and arrival generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np
import yaml

APPROACHES: tuple[str, ...] = ("E", "S", "W", "N")
SCENARIO_NAMES: tuple[str, ...] = ("moderate", "heavy", "peak", "stress")
NON_STRESS_SCENARIOS: tuple[str, ...] = ("moderate", "heavy", "peak")

TABLE1_MAMDANI_EXITS: dict[str, int] = {
    "E": 328,
    "S": 398,
    "W": 165,
    "N": 173,
}


def compute_directional_splits(
    exit_counts: dict[str, int] | None = None,
) -> dict[str, float]:
    """Compute exact normalized directional splits from Table 1 Mamdani exit counts."""
    counts = exit_counts if exit_counts is not None else TABLE1_MAMDANI_EXITS
    total = float(sum(counts.values()))
    return {app: float(counts[app]) / total for app in APPROACHES}


DIRECTIONAL_SPLITS: dict[str, float] = compute_directional_splits()


def _resolve_scenario_yaml_path(name: str, scenarios_dir: str | Path | None = None) -> Path:
    key = name.lower().strip()
    if scenarios_dir is not None:
        candidate = Path(scenarios_dir) / f"{key}.yaml"
        if candidate.is_file():
            return candidate
    repo_root = Path(__file__).resolve().parents[3]
    for base in (repo_root / "configs" / "scenarios", Path("configs") / "scenarios"):
        candidate = base / f"{key}.yaml"
        if candidate.is_file():
            return candidate
    raise ValueError(f"Unknown scenario name or missing YAML config: {name}")


@dataclass(frozen=True)
class ScenarioDemand:
    """Demand specification for a simulation scenario loaded from YAML."""

    name: str
    profile: str
    total_demand_vph: float = 0.0
    base_demand_vph: float = 0.0
    peak_demand_vph: float = 0.0
    ramp_up_s: float = 0.0
    plateau_s: float = 0.0
    ramp_down_s: float = 0.0

    @classmethod
    def from_name(
        cls,
        name: str,
        scenarios_dir: str | Path | None = None,
    ) -> ScenarioDemand:
        """Load scenario demand specification from configs/scenarios/<name>.yaml."""
        yaml_path = _resolve_scenario_yaml_path(name, scenarios_dir=scenarios_dir)
        with yaml_path.open("r", encoding="utf-8") as fh:
            data = dict(yaml.safe_load(fh))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScenarioDemand:
        """Create ScenarioDemand from parsed YAML dictionary."""
        profile = str(data.get("profile", "constant"))
        if profile == "constant":
            return cls(
                name=str(data["name"]),
                profile="constant",
                total_demand_vph=float(data["total_demand_vph"]),
            )
        return cls(
            name=str(data["name"]),
            profile="trapezoid",
            base_demand_vph=float(data["base_demand_vph"]),
            peak_demand_vph=float(data["peak_demand_vph"]),
            ramp_up_s=float(data["ramp_up_s"]),
            plateau_s=float(data["plateau_s"]),
            ramp_down_s=float(data["ramp_down_s"]),
        )

    def total_rate_vph_at(self, t: float, warmup_s: float = 600.0) -> float:
        """Return total intersection arrival rate [veh/h] at time t [s]."""
        if self.profile == "constant":
            return self.total_demand_vph
        tau = t - warmup_s
        if tau <= 0.0:
            return self.base_demand_vph
        if tau <= self.ramp_up_s:
            frac = tau / self.ramp_up_s
            return self.base_demand_vph + frac * (self.peak_demand_vph - self.base_demand_vph)
        if tau <= self.ramp_up_s + self.plateau_s:
            return self.peak_demand_vph
        total_active = self.ramp_up_s + self.plateau_s + self.ramp_down_s
        if tau <= total_active:
            frac = (tau - (self.ramp_up_s + self.plateau_s)) / self.ramp_down_s
            return self.peak_demand_vph - frac * (self.peak_demand_vph - self.base_demand_vph)
        return self.base_demand_vph

    def mean_total_demand_vph(self) -> float:
        """Return hourly mean total demand [veh/h] over the 3600 s measurement period."""
        if self.profile == "constant":
            return self.total_demand_vph
        total_dur = self.ramp_up_s + self.plateau_s + self.ramp_down_s
        ramp_mean = 0.5 * (self.base_demand_vph + self.peak_demand_vph)
        weighted = (
            self.ramp_up_s * ramp_mean
            + self.plateau_s * self.peak_demand_vph
            + self.ramp_down_s * ramp_mean
        )
        return weighted / total_dur

    def approach_mean_rates_vps(
        self,
        splits: dict[str, float] | None = None,
    ) -> dict[str, float]:
        """Return mean arrival rate [veh/s] per approach over the measurement hour."""
        sp = splits if splits is not None else DIRECTIONAL_SPLITS
        mean_vph = self.mean_total_demand_vph()
        return {app: (mean_vph * sp[app]) / 3600.0 for app in APPROACHES}


def compute_webster_flow_ratios(
    scenario: ScenarioDemand | str,
    service_rate_per_lane: float = 0.5,
    lanes_per_approach: int = 2,
    splits: dict[str, float] | None = None,
) -> tuple[dict[str, float], float]:
    """Compute per-phase flow ratios y_i and total Webster flow ratio Y = sum(y_i)."""
    scen = ScenarioDemand.from_name(scenario) if isinstance(scenario, str) else scenario
    sp = splits if splits is not None else DIRECTIONAL_SPLITS
    sat_flow_vps = service_rate_per_lane * float(lanes_per_approach)
    mean_rates = scen.approach_mean_rates_vps(splits=sp)
    y_per_approach = {app: mean_rates[app] / sat_flow_vps for app in APPROACHES}
    y_total = float(sum(y_per_approach.values()))
    assert y_total < 0.95, f"Webster Y={y_total:.4f} must be < 0.95 for {scen.name}"
    return y_per_approach, y_total


def validate_and_print_webster_ratios(
    service_rate_per_lane: float = 0.5,
    lanes_per_approach: int = 2,
    scenario_names: tuple[str, ...] = SCENARIO_NAMES,
) -> dict[str, float]:
    """Print and assert Y < 0.95 for all configured scenarios."""
    results: dict[str, float] = {}
    for name in scenario_names:
        y_map, y_tot = compute_webster_flow_ratios(
            name,
            service_rate_per_lane=service_rate_per_lane,
            lanes_per_approach=lanes_per_approach,
        )
        assert y_tot < 0.95
        results[name] = y_tot
        parts = ", ".join(f"{k}:{v:.4f}" for k, v in y_map.items())
        print(f"Scenario '{name}': Webster Y = {y_tot:.4f} ({parts}) < 0.95")
    return results


def pregenerate_arrivals(
    scenario: ScenarioDemand | str,
    seed: int,
    warmup_s: int = 600,
    measurement_s: int = 3600,
    dt: float = 1.0,
    splits: dict[str, float] | None = None,
) -> dict[str, np.ndarray]:
    """Pre-generate per-step Poisson arrival counts for all approaches using common random numbers."""
    scen = ScenarioDemand.from_name(scenario) if isinstance(scenario, str) else scenario
    sp = splits if splits is not None else DIRECTIONAL_SPLITS
    horizon_steps = int(round((warmup_s + measurement_s) / dt))
    times = (np.arange(horizon_steps, dtype=float) + 0.5) * dt
    total_vph = np.array([scen.total_rate_vph_at(float(t), warmup_s=float(warmup_s)) for t in times])
    rng = np.random.default_rng(seed)
    arrivals: dict[str, np.ndarray] = {}
    for app in APPROACHES:
        lam_step = (total_vph * sp[app] / 3600.0) * dt
        arrivals[app] = rng.poisson(lam_step).astype(np.int64)
    return arrivals


def pregenerate_arrival_timestamps(
    scenario: ScenarioDemand | str,
    seed: int,
    warmup_s: int = 600,
    measurement_s: int = 3600,
    dt: float = 1.0,
    splits: dict[str, float] | None = None,
) -> dict[str, np.ndarray]:
    """Pre-generate arrival timestamps [s] for every arriving vehicle per approach."""
    counts = pregenerate_arrivals(
        scenario=scenario,
        seed=seed,
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        dt=dt,
        splits=splits,
    )
    timestamps: dict[str, np.ndarray] = {}
    for app, step_counts in counts.items():
        step_indices = np.repeat(np.arange(len(step_counts), dtype=float), step_counts)
        timestamps[app] = step_indices * dt
    return timestamps
