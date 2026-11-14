"""Discrete-time four-approach isolated intersection queueing simulator."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Protocol
import numpy as np

from osfi_tsc.sim.demand import (
    APPROACHES,
    ScenarioDemand,
    pregenerate_arrivals,
)


@dataclass
class Vehicle:
    """Single vehicle in the intersection queue."""

    vehicle_id: int
    approach: str
    arrival_time: float
    departure_time: float | None = None


@dataclass(frozen=True)
class SensorReading:
    """Traffic sensor observation and signal timing state at step t."""

    t: float
    queues_m: dict[str, float]
    queues_veh: dict[str, int]
    arrival_rates: dict[str, float]
    arrivals_this_step: dict[str, int]
    active_phase: str = "E"
    in_intergreen: bool = False
    intergreen_remaining: int = 0
    green_elapsed: int = 0


class ControllerProtocol(Protocol):
    """Protocol for intersection signal controllers."""

    def step(self, t: float, sensors: SensorReading) -> str:
        """Return target green phase command ('E', 'S', 'W', or 'N')."""


class Sensor:
    """Traffic sensor for approach queue lengths [m/lane] and 10-s arrival rates [veh/10s]."""

    def __init__(
        self,
        lanes_per_approach: int = 2,
        vehicle_length_m: float = 7.0,
        arrival_window_steps: int = 10,
        queue_noise_std_m: float = 0.0,
        arrival_noise_std: float = 0.0,
        seed: int | None = None,
    ) -> None:
        self.lanes_per_approach = lanes_per_approach
        self.vehicle_length_m = vehicle_length_m
        self.arrival_window_steps = arrival_window_steps
        self.queue_noise_std_m = queue_noise_std_m
        self.arrival_noise_std = arrival_noise_std
        self._rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng(0)

    def observe(
        self,
        step_idx: int,
        dt: float,
        queues: dict[str, deque[Vehicle]],
        arrival_counts: dict[str, np.ndarray],
        active_phase: str,
        in_intergreen: bool,
        intergreen_remaining: int,
        green_elapsed: int,
    ) -> SensorReading:
        """Measure queue lengths per lane and 10-second arrival counts."""
        queues_veh: dict[str, int] = {}
        queues_m: dict[str, float] = {}
        arrival_rates: dict[str, float] = {}
        arrivals_this_step: dict[str, int] = {}
        win_start = max(0, step_idx - self.arrival_window_steps + 1)

        for app in APPROACHES:
            q_cnt = len(queues[app])
            queues_veh[app] = q_cnt
            q_m = (float(q_cnt) / float(self.lanes_per_approach)) * self.vehicle_length_m
            if self.queue_noise_std_m > 0.0:
                q_m = max(0.0, q_m + float(self._rng.normal(0.0, self.queue_noise_std_m)))
            queues_m[app] = q_m

            arr_win = float(np.sum(arrival_counts[app][win_start : step_idx + 1]))
            if self.arrival_noise_std > 0.0:
                arr_win = max(0.0, arr_win + float(self._rng.normal(0.0, self.arrival_noise_std)))
            arrival_rates[app] = arr_win
            arrivals_this_step[app] = int(arrival_counts[app][step_idx])

        return SensorReading(
            t=float(step_idx) * dt,
            queues_m=queues_m,
            queues_veh=queues_veh,
            arrival_rates=arrival_rates,
            arrivals_this_step=arrivals_this_step,
            active_phase=active_phase,
            in_intergreen=in_intergreen,
            intergreen_remaining=intergreen_remaining,
            green_elapsed=green_elapsed,
        )


@dataclass
class SimulationResult:
    """Complete record of a single simulation run."""

    scenario_name: str
    controller_name: str
    seed: int
    warmup_s: int
    measurement_s: int
    dt: float
    lanes_per_approach: int
    vehicle_length_m: float
    arrival_counts: dict[str, np.ndarray]
    departed_vehicles: dict[str, list[Vehicle]]
    remaining_queues: dict[str, list[Vehicle]]
    queue_veh_history: dict[str, np.ndarray]
    queue_m_history: dict[str, np.ndarray]
    active_phase_history: list[str]
    signal_state_history: list[str]
    num_switches_total: int
    num_switches_measurement: int
    green_durations_measurement: list[int]
    decision_log: list[dict[str, Any]] = field(default_factory=list)


class IntersectionSimulator:
    """Discrete-time (dt = 1 s) M/M/1-per-approach isolated intersection simulator."""

    def __init__(
        self,
        dt: float = 1.0,
        lanes_per_approach: int = 2,
        service: str = "exponential",
        service_rate_per_lane: float = 0.5,
        startup_lost_time: float = 2.0,
        yellow_time: float = 3.0,
        all_red_time: float = 2.0,
        vehicle_length_m: float = 7.0,
        arrival_window_s: float = 10.0,
        warmup_s: int = 600,
        measurement_s: int = 3600,
        queue_noise_std_m: float = 0.0,
        arrival_noise_std: float = 0.0,
    ) -> None:
        if service not in ("exponential", "deterministic"):
            raise ValueError(f"Unsupported service mode: {service}")
        self.dt = dt
        self.lanes_per_approach = lanes_per_approach
        self.service = service
        self.service_rate_per_lane = service_rate_per_lane
        self.startup_lost_time = startup_lost_time
        self.yellow_time = yellow_time
        self.all_red_time = all_red_time
        self.intergreen_steps = int(round((yellow_time + all_red_time) / dt))
        self.yellow_steps = int(round(yellow_time / dt))
        self.startup_lost_steps = int(round(startup_lost_time / dt))
        self.vehicle_length_m = vehicle_length_m
        self.arrival_window_steps = int(round(arrival_window_s / dt))
        self.warmup_s = warmup_s
        self.measurement_s = measurement_s
        self.horizon_steps = int(round((warmup_s + measurement_s) / dt))
        self.queue_noise_std_m = queue_noise_std_m
        self.arrival_noise_std = arrival_noise_std

    def run(
        self,
        controller: ControllerProtocol,
        scenario: ScenarioDemand | str,
        seed: int,
        controller_name: str = "controller",
        arrival_counts: dict[str, np.ndarray] | None = None,
        verify_conservation: bool = True,
    ) -> SimulationResult:
        """Execute simulation for one scenario and seed using common random numbers."""
        scen = ScenarioDemand.from_name(scenario) if isinstance(scenario, str) else scenario
        arr_counts = (
            {app: arrival_counts[app].copy() for app in APPROACHES}
            if arrival_counts is not None
            else pregenerate_arrivals(
                scenario=scen,
                seed=seed,
                warmup_s=self.warmup_s,
                measurement_s=self.measurement_s,
                dt=self.dt,
            )
        )

        service_rng = np.random.default_rng(seed + 1_000_003)
        sensor = Sensor(
            lanes_per_approach=self.lanes_per_approach,
            vehicle_length_m=self.vehicle_length_m,
            arrival_window_steps=self.arrival_window_steps,
            queue_noise_std_m=self.queue_noise_std_m,
            arrival_noise_std=self.arrival_noise_std,
            seed=seed + 2_000_003,
        )

        queues: dict[str, deque[Vehicle]] = {app: deque() for app in APPROACHES}
        departed: dict[str, list[Vehicle]] = {app: [] for app in APPROACHES}
        queue_veh_hist: dict[str, np.ndarray] = {
            app: np.zeros(self.horizon_steps, dtype=np.int64) for app in APPROACHES
        }
        queue_m_hist: dict[str, np.ndarray] = {
            app: np.zeros(self.horizon_steps, dtype=float) for app in APPROACHES
        }
        active_phase_hist: list[str] = []
        signal_state_hist: list[str] = []

        active_phase = "E"
        in_intergreen = False
        intergreen_remaining = 0
        green_elapsed = 0
        det_service_accum = 0.0

        num_switches_total = 0
        num_switches_measurement = 0
        green_durations_measurement: list[int] = []

        next_vehicle_id = 0
        total_arrivals_so_far = 0
        total_departures_so_far = 0
        mu_total = self.service_rate_per_lane * float(self.lanes_per_approach) * self.dt
        warmup_steps = int(round(self.warmup_s / self.dt))

        for step_idx in range(self.horizon_steps):
            if step_idx == warmup_steps and warmup_steps > 0:
                if hasattr(controller, "reset_diagnostics"):
                    controller.reset_diagnostics()
            t_now = float(step_idx) * self.dt

            for app in APPROACHES:
                n_new = int(arr_counts[app][step_idx])
                for _ in range(n_new):
                    queues[app].append(
                        Vehicle(
                            vehicle_id=next_vehicle_id,
                            approach=app,
                            arrival_time=t_now,
                        )
                    )
                    next_vehicle_id += 1
                total_arrivals_so_far += n_new

            reading = sensor.observe(
                step_idx=step_idx,
                dt=self.dt,
                queues=queues,
                arrival_counts=arr_counts,
                active_phase=active_phase,
                in_intergreen=in_intergreen,
                intergreen_remaining=intergreen_remaining,
                green_elapsed=green_elapsed,
            )

            commanded_phase = controller.step(t_now, reading)

            if not in_intergreen and commanded_phase != active_phase:
                if t_now >= float(self.warmup_s) and green_elapsed > 0:
                    green_durations_measurement.append(green_elapsed)
                active_phase = commanded_phase
                in_intergreen = True
                intergreen_remaining = self.intergreen_steps
                green_elapsed = 0
                det_service_accum = 0.0
                num_switches_total += 1
                if t_now >= float(self.warmup_s):
                    num_switches_measurement += 1

            if in_intergreen:
                elapsed_ig = self.intergreen_steps - intergreen_remaining
                sig_state = "YELLOW" if elapsed_ig < self.yellow_steps else "ALL_RED"
                intergreen_remaining -= 1
                if intergreen_remaining <= 0:
                    in_intergreen = False
                    intergreen_remaining = 0
                    green_elapsed = 0
                    det_service_accum = 0.0
            else:
                sig_state = "GREEN"
                if green_elapsed >= self.startup_lost_steps:
                    if self.service == "exponential":
                        capacity = int(service_rng.poisson(mu_total))
                    else:
                        det_service_accum += mu_total
                        capacity = int(np.floor(det_service_accum + 1e-9))
                        det_service_accum -= float(capacity)

                    q_active = queues[active_phase]
                    n_dep = min(len(q_active), capacity)
                    for _ in range(n_dep):
                        veh = q_active.popleft()
                        veh.departure_time = t_now
                        departed[active_phase].append(veh)
                    total_departures_so_far += n_dep
                green_elapsed += 1

            active_phase_hist.append(active_phase)
            signal_state_hist.append(sig_state)

            queued_now = 0
            for app in APPROACHES:
                q_len = len(queues[app])
                queued_now += q_len
                queue_veh_hist[app][step_idx] = q_len
                queue_m_hist[app][step_idx] = (
                    float(q_len) / float(self.lanes_per_approach)
                ) * self.vehicle_length_m

            if verify_conservation:
                assert total_arrivals_so_far == total_departures_so_far + queued_now, (
                    f"Conservation violated at step {step_idx}: "
                    f"arrivals={total_arrivals_so_far}, departures={total_departures_so_far}, queued={queued_now}"
                )

        if not in_intergreen and green_elapsed > 0:
            green_durations_measurement.append(green_elapsed)

        decision_log = getattr(controller, "decision_log", [])

        return SimulationResult(
            scenario_name=scen.name,
            controller_name=controller_name,
            seed=seed,
            warmup_s=self.warmup_s,
            measurement_s=self.measurement_s,
            dt=self.dt,
            lanes_per_approach=self.lanes_per_approach,
            vehicle_length_m=self.vehicle_length_m,
            arrival_counts=arr_counts,
            departed_vehicles=departed,
            remaining_queues={app: list(queues[app]) for app in APPROACHES},
            queue_veh_history=queue_veh_hist,
            queue_m_history=queue_m_hist,
            active_phase_history=active_phase_hist,
            signal_state_history=signal_state_hist,
            num_switches_total=num_switches_total,
            num_switches_measurement=num_switches_measurement,
            green_durations_measurement=green_durations_measurement,
            decision_log=list(decision_log),
        )
