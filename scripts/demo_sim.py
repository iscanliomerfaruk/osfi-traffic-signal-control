"""Live simulation runner, timeline plotter, and fast-forward intersection animator."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib

if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
    matplotlib.use("Agg")

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from osfi_tsc.contribution import build_controller
from osfi_tsc.experiment import load_config
from osfi_tsc.metrics import compute_run_metrics
from osfi_tsc.plotting import CONTROLLER_COLORS
from osfi_tsc.sim.demand import APPROACHES, ScenarioDemand, pregenerate_arrivals
from osfi_tsc.sim.intersection import (
    IntersectionSimulator,
    SimulationResult,
    pregenerate_sensor_noise,
)


def run_demo_simulations(
    scenario_name: str = "heavy",
    controllers: list[str] | None = None,
    seed: int = 1,
    sigma_q: float = 0.0,
    p_miss: float = 0.0,
    config_path: str = "configs/default.yaml",
) -> tuple[dict[str, SimulationResult], list[dict[str, Any]], str]:
    """Run common-random-number simulation across selected controllers and format metrics table."""
    ctrl_list = controllers or ["Mamdani", "OSFI-DJ-S", "Webster"]
    config = load_config(config_path)
    sim_cfg = config.get("simulator", {})
    noise_cfg = sim_cfg.get("sensor_noise", {})
    false_rate = float(noise_cfg.get("arrival_false_rate_vps", 0.02))

    scen = ScenarioDemand.from_name(scenario_name)
    warmup_s = int(sim_cfg.get("warmup_s", 600))
    measurement_s = int(sim_cfg.get("measurement_s", 3600))
    dt = float(sim_cfg.get("dt", 1.0))

    common_arrivals = pregenerate_arrivals(
        scenario=scen,
        seed=seed,
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        dt=dt,
    )
    horizon_steps = int(round((warmup_s + measurement_s) / dt))
    common_noise = pregenerate_sensor_noise(
        arrival_counts=common_arrivals,
        seed=seed,
        horizon_steps=horizon_steps,
        queue_noise_std_m=float(sigma_q),
        arrival_p_miss=float(p_miss),
        arrival_false_rate_vps=false_rate,
        dt=dt,
    )

    simulator = IntersectionSimulator(
        dt=dt,
        lanes_per_approach=int(sim_cfg.get("lanes_per_approach", 2)),
        service=str(sim_cfg.get("service", "exponential")),
        service_rate_per_lane=float(sim_cfg.get("service_rate_per_lane", 0.5)),
        startup_lost_time=float(sim_cfg.get("startup_lost_time", 2.0)),
        yellow_time=float(sim_cfg.get("yellow_time", 3.0)),
        all_red_time=float(sim_cfg.get("all_red_time", 2.0)),
        vehicle_length_m=float(sim_cfg.get("vehicle_length_m", 7.0)),
        arrival_window_s=float(sim_cfg.get("arrival_window_s", 10.0)),
        warmup_s=warmup_s,
        measurement_s=measurement_s,
        queue_noise_std_m=float(sigma_q),
        arrival_p_miss=float(p_miss),
        arrival_false_rate_vps=false_rate,
    )

    results: dict[str, SimulationResult] = {}
    overall_rows: list[dict[str, Any]] = []

    for ctrl_name in ctrl_list:
        ctrl = build_controller(
            ctrl_name,
            scen,
            config,
            sigma_q=float(sigma_q),
            p_miss=float(p_miss),
            use_lut=True,
        )
        res = simulator.run(
            controller=ctrl,
            scenario=scen,
            seed=seed,
            controller_name=ctrl_name,
            arrival_counts=common_arrivals,
            pregenerated_noise=common_noise,
            verify_conservation=True,
        )
        results[ctrl_name] = res
        m_rows, _ = compute_run_metrics(res, controller=ctrl)
        for r in m_rows:
            if r["approach"] == "overall":
                overall_rows.append(r)

    lines: list[str] = [
        "=" * 96,
        f"OSFI-TSC LIVE INTERSECTION SIMULATION DEMO — Scenario: {scenario_name} | Seed: {seed} | sigma_q: {sigma_q:.1f} m",
        "=" * 96,
        f"  {'Controller':<14s} | {'Delay [s/veh]':>13s} | {'Exits [veh]':>11s} | {'Mean Queue [m]':>14s} | {'Max Queue [m]':>13s} | {'Switches/h':>10s} | {'Fallback %':>10s}",
        "  " + "-" * 92,
    ]
    for r in overall_rows:
        fb_pct = 100.0 * float(r.get("fallback_rate", 0.0))
        lines.append(
            f"  {str(r['controller']):<14s} | "
            f"{float(r['avg_delay_s']):13.2f} | "
            f"{int(r['throughput_veh']):11d} | "
            f"{float(r['mean_queue_m']):14.2f} | "
            f"{float(r['max_queue_m']):13.2f} | "
            f"{int(r['num_switches']):10d} | "
            f"{fb_pct:9.2f}%"
        )
    lines.append("=" * 96)
    table_str = "\n".join(lines)
    return results, overall_rows, table_str


def plot_demo_timeline(
    results: dict[str, SimulationResult],
    out_path: str | Path = "results/figures/demo_sim_timeline.png",
) -> plt.Figure:
    """Plot and save approach queue timelines and active phases across controllers."""
    first_res = next(iter(results.values()))
    w_s = first_res.warmup_s
    m_s = first_res.measurement_s
    t_axis = np.arange(m_s, dtype=float)

    fig, axes = plt.subplots(2, 1, figsize=(11, 6.2), sharex=True)
    ax_q, ax_tot = axes

    for ctrl_name, res in results.items():
        col = CONTROLLER_COLORS.get(ctrl_name, "#333333")
        q_south = res.queue_m_history["S"][w_s : w_s + m_s]
        q_tot = sum(res.queue_m_history[app][w_s : w_s + m_s] for app in APPROACHES) / 4.0
        window = 30
        kernel = np.ones(window, dtype=float) / window
        q_south_sm = np.convolve(q_south, kernel, mode="same")
        q_tot_sm = np.convolve(q_tot, kernel, mode="same")
        ax_q.plot(t_axis, q_south_sm, label=ctrl_name, color=col, lw=1.6)
        ax_tot.plot(t_axis, q_tot_sm, label=ctrl_name, color=col, lw=1.6)

    ax_q.set_ylabel("South Queue [m/lane]")
    ax_q.set_title(
        f"Queue Length Timelines (30-s Moving Average) — Scenario: {first_res.scenario_name} (Seed {first_res.seed})",
        fontweight="bold",
    )
    ax_q.legend(loc="upper right", ncol=min(4, len(results)))
    ax_q.grid(True, alpha=0.3)

    ax_tot.set_ylabel("Mean 4-Approach Queue [m/lane]")
    ax_tot.set_xlabel("Measurement Time [s]")
    ax_tot.legend(loc="upper right", ncol=min(4, len(results)))
    ax_tot.grid(True, alpha=0.3)

    fig.tight_layout()
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=200)
    return fig


def create_fast_forward_animation(
    res: SimulationResult,
    step_stride: int = 10,
    max_frames: int = 120,
    build_animation: bool = True,
) -> tuple[plt.Figure, animation.FuncAnimation | None]:
    """Build a fast-forward bar animation of E/S/W/N queues; without animation, step all frames statically."""
    w_s = res.warmup_s
    m_s = res.measurement_s
    frame_indices = list(range(w_s, min(w_s + m_s, w_s + max_frames * step_stride), step_stride))

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    bars = ax.bar(APPROACHES, [0.0, 0.0, 0.0, 0.0], color=["#999999"] * 4, edgecolor="black", width=0.55)
    max_q = max(66.0, float(max(np.max(res.queue_m_history[app][w_s:]) for app in APPROACHES)) * 1.1)
    ax.set_ylim(0.0, max_q)
    ax.set_ylabel("Queue Length [m/lane]")
    ax.set_xlabel("Intersection Approach")
    ax.axhline(60.0, color="#D55E00", ls="--", lw=1.2, label="Fuzzy Universe Max (60 m)")
    ax.legend(loc="upper right")
    ax.grid(True, axis="y", alpha=0.3)

    title_text = ax.set_title("", fontsize=11, fontweight="bold")

    def _update(frame_pos: int) -> Any:
        t_idx = frame_indices[frame_pos]
        t_meas = t_idx - w_s
        act_phase = res.active_phase_history[t_idx]
        sig_state = str(res.signal_state_history[t_idx]).upper()
        for idx, app in enumerate(APPROACHES):
            q_val = float(res.queue_m_history[app][t_idx])
            bars[idx].set_height(q_val)
            if app == act_phase:
                if sig_state == "GREEN":
                    bars[idx].set_color("#009E73")
                elif sig_state == "YELLOW":
                    bars[idx].set_color("#F0E442")
                else:
                    bars[idx].set_color("#CC79A7")
            else:
                bars[idx].set_color("#7F7F7F")
            bars[idx].set_edgecolor("black")
        title_text.set_text(
            f"{res.controller_name} ({res.scenario_name}) | Clock: t = {t_meas:4d} s | "
            f"Active Phase: {act_phase} ({sig_state})"
        )
        return (*bars, title_text)

    if not build_animation:
        for pos in range(len(frame_indices)):
            _update(pos)
        return fig, None

    anim = animation.FuncAnimation(
        fig,
        _update,
        frames=len(frame_indices),
        interval=60,
        blit=False,
        repeat=False,
    )
    _update(0)
    return fig, anim


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run live CRN intersection simulation, print metrics, and plot/animate queues."
    )
    parser.add_argument("--scenario", type=str, default="heavy", help="Scenario name (moderate, heavy, peak, stress).")
    parser.add_argument(
        "--controllers",
        type=str,
        default="Mamdani,OSFI-DJ-S,Webster",
        help="Comma-separated controller names.",
    )
    parser.add_argument("--seed", type=int, default=1, help="Random seed.")
    parser.add_argument("--sigma-q", type=float, default=0.0, help="Queue sensor noise std [m].")
    parser.add_argument("--p-miss", type=float, default=0.0, help="Arrival detector miss probability.")
    parser.add_argument(
        "--out",
        type=str,
        default="results/figures/demo_sim_timeline.png",
        help="Output path for timeline figure.",
    )
    parser.add_argument("--animate", action="store_true", help="Show fast-forward Matplotlib queue bar animation.")
    parser.add_argument("--headless", action="store_true", help="Run headlessly without opening GUI windows.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    ctrl_list = [c.strip() for c in args.controllers.split(",") if c.strip()]
    results, _, table_str = run_demo_simulations(
        scenario_name=args.scenario,
        controllers=ctrl_list,
        seed=args.seed,
        sigma_q=args.sigma_q,
        p_miss=args.p_miss,
    )
    print(table_str)
    fig_tl = plot_demo_timeline(results, out_path=args.out)
    print(f"Saved timeline figure to {args.out}")

    interactive = not args.headless and matplotlib.get_backend().lower() != "agg"
    fig_anim = None
    anim_obj = None
    if args.animate:
        target_ctrl = "OSFI-DJ-S" if "OSFI-DJ-S" in results else next(iter(results.keys()))
        fig_anim, anim_obj = create_fast_forward_animation(
            results[target_ctrl], build_animation=interactive
        )
        if not interactive:
            frame_path = Path(args.out).with_name("demo_sim_anim_frame.png")
            fig_anim.savefig(frame_path, dpi=150)
            print(f"Headless mode: saved final animation frame to {frame_path}")

    if interactive:
        plt.show()
    else:
        plt.close(fig_tl)
        if fig_anim is not None:
            plt.close(fig_anim)
    _ = anim_obj


if __name__ == "__main__":
    main()
