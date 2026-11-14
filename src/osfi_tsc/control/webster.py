"""Webster fixed-time traffic signal controller."""

from __future__ import annotations

from typing import Any
import numpy as np

from osfi_tsc.sim.demand import (
    APPROACHES,
    ScenarioDemand,
    compute_webster_flow_ratios,
)
from osfi_tsc.sim.intersection import SensorReading


class WebsterController:
    """Fixed-time controller with cycle and green splits from Webster's formula."""

    def __init__(
        self,
        scenario: ScenarioDemand | str,
        service_rate_per_lane: float = 0.5,
        lanes_per_approach: int = 2,
        yellow_time: float = 3.0,
        all_red_time: float = 2.0,
        startup_lost_time: float = 2.0,
        cycle_bounds: tuple[float, float] = (40.0, 180.0),
        g_min: int = 7,
    ) -> None:
        self.scenario = (
            ScenarioDemand.from_name(scenario) if isinstance(scenario, str) else scenario
        )
        self.yellow_time = yellow_time
        self.all_red_time = all_red_time
        self.startup_lost_time = startup_lost_time
        self.intergreen_s = yellow_time + all_red_time
        self.lost_time_per_phase = self.intergreen_s + startup_lost_time
        self.total_lost_time = float(len(APPROACHES)) * self.lost_time_per_phase
        self.cycle_bounds = cycle_bounds
        self.g_min = int(g_min)

        y_map, y_total = compute_webster_flow_ratios(
            self.scenario,
            service_rate_per_lane=service_rate_per_lane,
            lanes_per_approach=lanes_per_approach,
        )
        self.y_per_approach = y_map
        self.y_total = y_total

        raw_c0 = (1.5 * self.total_lost_time + 5.0) / max(1e-6, 1.0 - self.y_total)
        self.cycle_length_s = float(np.clip(raw_c0, cycle_bounds[0], cycle_bounds[1]))

        effective_green_total = max(
            float(len(APPROACHES) * self.g_min),
            self.cycle_length_s - self.total_lost_time,
        )
        self.green_durations: dict[str, int] = {}
        for app in APPROACHES:
            share = self.y_per_approach[app] / self.y_total
            eff_g = share * effective_green_total
            disp_g = max(self.g_min, int(round(eff_g + self.startup_lost_time)))
            self.green_durations[app] = disp_g

        self.current_phase = "E"
        self._internal_green_elapsed = 0
        self._last_in_intergreen = False
        self.decision_log: list[dict[str, Any]] = []

    def step(self, t: float, sensors: SensorReading) -> str:
        """Advance fixed-time round-robin schedule E->S->W->N."""
        if sensors.in_intergreen:
            self.current_phase = sensors.active_phase
            self._internal_green_elapsed = 0
            self._last_in_intergreen = True
            return self.current_phase

        if self._last_in_intergreen or sensors.active_phase != self.current_phase:
            self.current_phase = sensors.active_phase
            self._internal_green_elapsed = 0
            self._last_in_intergreen = False

        green_elapsed = (
            sensors.green_elapsed
            if sensors.green_elapsed > 0 or self._internal_green_elapsed == 0
            else self._internal_green_elapsed
        )

        target_g = self.green_durations[self.current_phase]
        if green_elapsed < target_g:
            self._internal_green_elapsed = green_elapsed + 1
            return self.current_phase

        curr_idx = APPROACHES.index(self.current_phase)
        next_phase = APPROACHES[(curr_idx + 1) % len(APPROACHES)]
        self.decision_log.append(
            {
                "time": t,
                "phase": self.current_phase,
                "green_elapsed": green_elapsed,
                "action": "switch_fixed_cycle",
                "next_phase": next_phase,
            }
        )
        self.current_phase = next_phase
        self._internal_green_elapsed = 0
        return next_phase
