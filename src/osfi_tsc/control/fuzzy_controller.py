"""Fuzzy traffic signal controller implementing NPS, two-stage GPE, and SPM."""

from __future__ import annotations

from typing import Any, Protocol
from osfi_tsc.fuzzy.membership import (
    ARRIVAL_CENTERS,
    EXTENSION_TRIANGLES,
    QUEUE_CENTERS,
    arrival_rate_memberships,
    dominant_linguistic_term,
    extension_input_memberships,
    queue_length_memberships,
)
from osfi_tsc.sim.demand import APPROACHES
from osfi_tsc.sim.intersection import SensorReading


class InferenceEngineProtocol(Protocol):
    """Protocol for two-stage GPE inference engines."""

    shoulder_edges: bool
    total_calls: int
    fallback_count: int
    fc1_calls: int
    fc1_fallbacks: int
    fc2_calls: int
    fc2_fallbacks: int

    @property
    def fallback_rate(self) -> float:
        """Fraction of inference calls that required fallback."""

    def reset_stats(self) -> None:
        """Reset call and fallback counters."""

    def infer_gpe(
        self,
        arrival_rate: float,
        queue_current: float,
        queue_others_max: float,
    ) -> tuple[float, float]:
        """Compute (Extension1, Extension2)."""


class FuzzyController:
    """Two-stage fuzzy traffic signal controller (NPS + GPE + SPM)."""

    def __init__(
        self,
        engine: InferenceEngineProtocol,
        g_min: int = 7,
        g_max: int = 60,
        initial_phase: str = "E",
    ) -> None:
        self.engine = engine
        self.g_min = int(g_min)
        self.g_max = int(g_max)
        self.current_phase = initial_phase
        self._target_green = int(g_min)
        self._internal_green_elapsed = 0
        self._last_in_intergreen = False
        self.decision_log: list[dict[str, Any]] = []
        self.input_coverage_counts: dict[str, dict[str, int]] = {
            "arrival_rate": {k: 0 for k in ARRIVAL_CENTERS},
            "queue_current": {k: 0 for k in QUEUE_CENTERS},
            "extension1": {k: 0 for k in EXTENSION_TRIANGLES},
            "queue_others_max": {k: 0 for k in QUEUE_CENTERS},
        }
        self.gpe_evaluations: int = 0

    def reset_diagnostics(self) -> None:
        """Reset input coverage and engine fallback statistics after warm-up."""
        for var in self.input_coverage_counts:
            for term in self.input_coverage_counts[var]:
                self.input_coverage_counts[var][term] = 0
        self.gpe_evaluations = 0
        if hasattr(self.engine, "reset_stats"):
            self.engine.reset_stats()

    def select_next_phase_nps(
        self,
        queues_m: dict[str, float],
        current_phase: str,
        exclude_current: bool = False,
    ) -> str:
        """Select approach with longest queue; ties keep current, then E->S->W->N."""
        candidates = [
            app for app in APPROACHES if not (exclude_current and app == current_phase)
        ]
        max_q = max(queues_m[app] for app in candidates)
        if not exclude_current and abs(queues_m[current_phase] - max_q) <= 1e-9:
            return current_phase
        for app in candidates:
            if abs(queues_m[app] - max_q) <= 1e-9:
                return app
        return candidates[0]

    def _record_input_coverage(
        self,
        lam_cur: float,
        q_cur: float,
        ext1: float,
        q_others: float,
    ) -> None:
        shoulder = getattr(self.engine, "shoulder_edges", True)
        m_arr = arrival_rate_memberships(lam_cur, shoulder_edges=shoulder)
        m_qcur = queue_length_memberships(q_cur, shoulder_edges=shoulder)
        m_ext1 = extension_input_memberships(ext1, shoulder_edges=shoulder)
        m_qoth = queue_length_memberships(q_others, shoulder_edges=shoulder)

        self.input_coverage_counts["arrival_rate"][dominant_linguistic_term(m_arr)] += 1
        self.input_coverage_counts["queue_current"][dominant_linguistic_term(m_qcur)] += 1
        self.input_coverage_counts["extension1"][dominant_linguistic_term(m_ext1)] += 1
        self.input_coverage_counts["queue_others_max"][dominant_linguistic_term(m_qoth)] += 1
        self.gpe_evaluations += 1

    def get_input_coverage_shares(self) -> dict[str, dict[str, float]]:
        """Return share of decisions in which each linguistic set had largest membership."""
        denom = float(max(1, self.gpe_evaluations))
        return {
            var: {term: cnt / denom for term, cnt in term_counts.items()}
            for var, term_counts in self.input_coverage_counts.items()
        }

    def step(self, t: float, sensors: SensorReading) -> str:
        """Evaluate NPS + GPE + SPM at step t and return phase command."""
        if sensors.in_intergreen:
            self.current_phase = sensors.active_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            self._last_in_intergreen = True
            return self.current_phase

        if self._last_in_intergreen or sensors.active_phase != self.current_phase:
            self.current_phase = sensors.active_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            self._last_in_intergreen = False

        green_elapsed = (
            sensors.green_elapsed
            if sensors.green_elapsed > 0 or self._internal_green_elapsed == 0
            else self._internal_green_elapsed
        )

        if green_elapsed < self._target_green and green_elapsed < self.g_max:
            self._internal_green_elapsed = green_elapsed + 1
            return self.current_phase

        queues_m = sensors.queues_m
        q_cur = float(queues_m[self.current_phase])
        other_phases = [app for app in APPROACHES if app != self.current_phase]
        q_others_max = float(max(queues_m[app] for app in other_phases))
        lam_cur = float(sensors.arrival_rates[self.current_phase])

        ext1, ext2 = self.engine.infer_gpe(lam_cur, q_cur, q_others_max)
        self._record_input_coverage(lam_cur, q_cur, ext1, q_others_max)

        if max(queues_m.values()) <= 1e-9:
            self._target_green = green_elapsed + 1
            self._internal_green_elapsed = green_elapsed + 1
            self.decision_log.append(
                {
                    "time": t,
                    "phase": self.current_phase,
                    "green_elapsed": green_elapsed,
                    "lambda_current": lam_cur,
                    "q_current_m": q_cur,
                    "q_others_max_m": q_others_max,
                    "extension1": ext1,
                    "extension2": ext2,
                    "action": "stay_empty",
                    "next_phase": self.current_phase,
                }
            )
            return self.current_phase

        if q_others_max > q_cur + 1e-9:
            next_phase = self.select_next_phase_nps(
                queues_m, self.current_phase, exclude_current=True
            )
            self.decision_log.append(
                {
                    "time": t,
                    "phase": self.current_phase,
                    "green_elapsed": green_elapsed,
                    "lambda_current": lam_cur,
                    "q_current_m": q_cur,
                    "q_others_max_m": q_others_max,
                    "extension1": ext1,
                    "extension2": ext2,
                    "action": "switch_longer_queue",
                    "next_phase": next_phase,
                }
            )
            self.current_phase = next_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            return next_phase

        if ext2 < 1.0 or green_elapsed >= self.g_max:
            if q_others_max <= 1e-9 and q_cur > 1e-9 and green_elapsed < self.g_max:
                ext_steps = max(1, int(round(ext2))) if ext2 >= 1.0 else self.g_min
                self._target_green = min(self.g_max, green_elapsed + ext_steps)
                self._internal_green_elapsed = green_elapsed + 1
                self.decision_log.append(
                    {
                        "time": t,
                        "phase": self.current_phase,
                        "green_elapsed": green_elapsed,
                        "lambda_current": lam_cur,
                        "q_current_m": q_cur,
                        "q_others_max_m": q_others_max,
                        "extension1": ext1,
                        "extension2": ext2,
                        "action": "extend_no_competing_queue",
                        "next_phase": self.current_phase,
                    }
                )
                return self.current_phase

            next_phase = self.select_next_phase_nps(
                queues_m, self.current_phase, exclude_current=True
            )
            reason = "switch_max_green" if green_elapsed >= self.g_max else "switch_short_ext"
            self.decision_log.append(
                {
                    "time": t,
                    "phase": self.current_phase,
                    "green_elapsed": green_elapsed,
                    "lambda_current": lam_cur,
                    "q_current_m": q_cur,
                    "q_others_max_m": q_others_max,
                    "extension1": ext1,
                    "extension2": ext2,
                    "action": reason,
                    "next_phase": next_phase,
                }
            )
            self.current_phase = next_phase
            self._target_green = self.g_min
            self._internal_green_elapsed = 0
            return next_phase

        ext_steps = int(round(ext2))
        self._target_green = green_elapsed + ext_steps
        self._internal_green_elapsed = green_elapsed + 1
        self.decision_log.append(
            {
                "time": t,
                "phase": self.current_phase,
                "green_elapsed": green_elapsed,
                "lambda_current": lam_cur,
                "q_current_m": q_cur,
                "q_others_max_m": q_others_max,
                "extension1": ext1,
                "extension2": ext2,
                "action": f"extend_{ext_steps}s",
                "next_phase": self.current_phase,
            }
        )
        return self.current_phase
