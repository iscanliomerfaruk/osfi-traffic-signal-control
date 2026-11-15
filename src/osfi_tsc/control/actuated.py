"""Full vehicle-actuated traffic signal controller with gap-out and phase skipping."""

from __future__ import annotations

from typing import Any
from osfi_tsc.sim.demand import APPROACHES
from osfi_tsc.sim.intersection import SensorReading


class ActuatedController:
    """Round-robin vehicle-actuated controller with stop-line presence, unit extension, and max-out."""

    def __init__(
        self,
        g_min: int = 7,
        unit_extension: int = 3,
        g_max: int = 60,
        initial_phase: str = "E",
    ) -> None:
        self.g_min = int(g_min)
        self.unit_extension = int(unit_extension)
        self.g_max = int(g_max)
        self.current_phase = initial_phase
        self._target_green = int(g_min)
        self._internal_green_elapsed = 0
        self._gap_timer = 0
        self._last_in_intergreen = False
        self.decision_log: list[dict[str, Any]] = []

    def _next_non_empty_phase(self, queues_m: dict[str, float]) -> str:
        curr_idx = APPROACHES.index(self.current_phase)
        for offset in range(1, len(APPROACHES) + 1):
            candidate = APPROACHES[(curr_idx + offset) % len(APPROACHES)]
            if queues_m[candidate] > 1e-9:
                return candidate
        return self.current_phase

    def step(self, t: float, sensors: SensorReading) -> str:
        """Apply actuated control rules with stop-line presence detection at time t."""
        if sensors.in_intergreen:
            self.current_phase = sensors.active_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            self._gap_timer = 0
            self._last_in_intergreen = True
            return self.current_phase

        if self._last_in_intergreen or sensors.active_phase != self.current_phase:
            self.current_phase = sensors.active_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            self._gap_timer = 0
            self._last_in_intergreen = False

        green_elapsed = (
            sensors.green_elapsed
            if sensors.green_elapsed > 0 or self._internal_green_elapsed == 0
            else self._internal_green_elapsed
        )

        if sensors.arrivals_this_step.get(self.current_phase, 0) > 0:
            self._gap_timer = 0
        else:
            self._gap_timer += 1

        if green_elapsed < self._target_green and green_elapsed < self.g_max:
            self._internal_green_elapsed = green_elapsed + 1
            return self.current_phase

        if max(sensors.queues_m.values()) <= 1e-9:
            self._target_green = green_elapsed + 1
            self._internal_green_elapsed = green_elapsed + 1
            return self.current_phase

        q_cur = float(sensors.queues_m[self.current_phase])
        has_demand = (q_cur > 1e-9) or (self._gap_timer < self.unit_extension)

        if green_elapsed < self.g_max and has_demand:
            self._target_green = min(self.g_max, green_elapsed + self.unit_extension)
            self._internal_green_elapsed = green_elapsed + 1
            self.decision_log.append(
                {
                    "time": t,
                    "phase": self.current_phase,
                    "green_elapsed": green_elapsed,
                    "action": f"extend_{self.unit_extension}s",
                    "next_phase": self.current_phase,
                }
            )
            return self.current_phase

        next_phase = self._next_non_empty_phase(sensors.queues_m)
        if next_phase != self.current_phase:
            reason = "max_out" if green_elapsed >= self.g_max else "gap_out"
            self.decision_log.append(
                {
                    "time": t,
                    "phase": self.current_phase,
                    "green_elapsed": green_elapsed,
                    "action": reason,
                    "next_phase": next_phase,
                }
            )
            self.current_phase = next_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            self._gap_timer = 0
            return next_phase

        self._target_green = green_elapsed + 1
        self._internal_green_elapsed = green_elapsed + 1
        return self.current_phase

