"""Publication-grade figure generation for Stage 1 reproduction and analysis."""

from __future__ import annotations

from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from osfi_tsc.control import FuzzyController
from osfi_tsc.fuzzy.membership import (
    ARRIVAL_CENTERS,
    EXTENSION_TRIANGLES,
    QUEUE_CENTERS,
    arrival_rate_memberships,
    extension_input_memberships,
    extension_output_memberships,
    queue_length_memberships,
)
from osfi_tsc.inference import (
    MamdaniInference,
    OSFILiteralInference,
    SugenoInference,
)
from osfi_tsc.sim import (
    APPROACHES,
    IntersectionSimulator,
    ScenarioDemand,
)

matplotlib.use("Agg")

CONTROLLER_COLORS: dict[str, str] = {
    "Mamdani": "#E69F00",
    "Sugeno": "#D55E00",
    "OSFI-literal": "#0072B2",
    "Webster": "#009E73",
    "Actuated": "#CC79A7",
}

CONTROLLER_MARKERS: dict[str, str] = {
    "Mamdani": "o",
    "Sugeno": "s",
    "OSFI-literal": "^",
    "Webster": "D",
    "Actuated": "v",
}

APPROACH_COLORS: dict[str, str] = {
    "E": "#0072B2",
    "S": "#D55E00",
    "W": "#009E73",
    "N": "#CC79A7",
}

TERM_COLORS: tuple[str, ...] = ("#0072B2", "#E69F00", "#009E73", "#D55E00")


def apply_academic_style() -> None:
    """Configure Matplotlib rcParams for academic publication figures."""
    plt.rcParams.update(
        {
            "font.size": 9.5,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.5,
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.28,
            "grid.linestyle": "--",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _save_both(fig: plt.Figure, out_dir: Path, stem: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{stem}.pdf"
    png_path = out_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
    fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    return [pdf_path, png_path]


def plot_mf_inputs_outputs(out_dir: Path) -> list[Path]:
    """Render 2x2 panel reproducing paper Figs. 4-7 with shoulder indicator."""
    apply_academic_style()
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.8), constrained_layout=True)

    x_arr = np.linspace(0.0, 12.0, 400)
    m_arr_pure = arrival_rate_memberships(x_arr, shoulder_edges=False)
    m_arr_sh = arrival_rate_memberships(x_arr, shoulder_edges=True)
    ax = axes[0, 0]
    for idx, (term, _) in enumerate(ARRIVAL_CENTERS.items()):
        color = TERM_COLORS[idx]
        ax.plot(x_arr, m_arr_pure[term], color=color, lw=1.8, label=term)
        ax.fill_between(x_arr, 0.0, m_arr_pure[term], color=color, alpha=0.18)
        if idx == len(ARRIVAL_CENTERS) - 1:
            ax.plot(x_arr, m_arr_sh[term], color=color, lw=1.3, ls=":")
    ax.set_xlabel(r"Arrival rate $\lambda$ [veh / 10 s] (FC$_1$)")
    ax.set_ylabel("Membership degree")
    ax.set_xlim(0.0, 12.0)
    ax.set_ylim(0.0, 1.25)
    ax.legend(loc="upper right", frameon=True, ncol=4, columnspacing=0.8, handlelength=1.4)

    x_q = np.linspace(0.0, 60.0, 400)
    m_q_pure = queue_length_memberships(x_q, shoulder_edges=False)
    m_q_sh = queue_length_memberships(x_q, shoulder_edges=True)
    ax = axes[0, 1]
    for idx, (term, _) in enumerate(QUEUE_CENTERS.items()):
        color = TERM_COLORS[idx]
        ax.plot(x_q, m_q_pure[term], color=color, lw=1.8, label=term)
        ax.fill_between(x_q, 0.0, m_q_pure[term], color=color, alpha=0.18)
        if idx == len(QUEUE_CENTERS) - 1:
            ax.plot(x_q, m_q_sh[term], color=color, lw=1.3, ls=":")
    ax.set_xlabel(r"Current queue length $q$ [m / lane] (FC$_1$)")
    ax.set_ylabel("Membership degree")
    ax.set_xlim(0.0, 60.0)
    ax.set_ylim(0.0, 1.25)
    ax.legend(loc="upper right", frameon=True, ncol=4, columnspacing=0.8, handlelength=1.4)

    x_ext = np.linspace(0.0, 25.0, 500)
    m_ext_pure = extension_output_memberships(x_ext)
    m_ext_sh = extension_input_memberships(x_ext, shoulder_edges=True)
    ax = axes[1, 0]
    for idx, (term, _) in enumerate(EXTENSION_TRIANGLES.items()):
        color = TERM_COLORS[idx]
        ax.plot(x_ext, m_ext_pure[term], color=color, lw=1.8, label=term)
        ax.fill_between(x_ext, 0.0, m_ext_pure[term], color=color, alpha=0.18)
        if idx == len(EXTENSION_TRIANGLES) - 1:
            ax.plot(x_ext, m_ext_sh[term], color=color, lw=1.3, ls=":")
    ax.set_xlabel(r"Extension1 / Extension2 [s] (FC$_1$ out, FC$_2$ in/out)")
    ax.set_ylabel("Membership degree")
    ax.set_xlim(0.0, 25.0)
    ax.set_ylim(0.0, 1.25)
    ax.legend(loc="upper right", frameon=True, ncol=4, columnspacing=0.8, handlelength=1.4)

    ax = axes[1, 1]
    for idx, (term, _) in enumerate(QUEUE_CENTERS.items()):
        color = TERM_COLORS[idx]
        ax.plot(x_q, m_q_pure[term], color=color, lw=1.8, label=term)
        ax.fill_between(x_q, 0.0, m_q_pure[term], color=color, alpha=0.18)
        if idx == len(QUEUE_CENTERS) - 1:
            ax.plot(x_q, m_q_sh[term], color=color, lw=1.3, ls=":")
    ax.set_xlabel(r"Competing queue length $q'$ [m / lane] (FC$_2$)")
    ax.set_ylabel("Membership degree")
    ax.set_xlim(0.0, 60.0)
    ax.set_ylim(0.0, 1.25)
    ax.legend(loc="upper right", frameon=True, ncol=4, columnspacing=0.8, handlelength=1.4)

    return _save_both(fig, out_dir, "mf_inputs_outputs")


def plot_control_surfaces(out_dir: Path, shoulder_edges: bool = True) -> list[Path]:
    """Render individual and 1x3 combined control surfaces for FC1 and FC2."""
    apply_academic_style()
    saved: list[Path] = []

    engines = [
        ("mamdani", "Mamdani", MamdaniInference(shoulder_edges=shoulder_edges)),
        ("sugeno", "Sugeno", SugenoInference(shoulder_edges=shoulder_edges)),
        ("osfi_literal", "OSFI-literal", OSFILiteralInference(shoulder_edges=shoulder_edges)),
    ]

    lam_grid = np.linspace(0.0, 12.0, 61)
    q_grid = np.linspace(0.0, 60.0, 61)
    ext1_grid = np.linspace(0.0, 25.0, 61)

    fc1_surfaces: dict[str, np.ndarray] = {}
    fc2_surfaces: dict[str, np.ndarray] = {}

    for slug, label, eng in engines:
        z_fc1 = np.zeros((len(q_grid), len(lam_grid)), dtype=float)
        for i, q_val in enumerate(q_grid):
            for j, l_val in enumerate(lam_grid):
                z_fc1[i, j] = eng.infer_fc1(float(l_val), float(q_val))
        fc1_surfaces[slug] = z_fc1

        fig, ax = plt.subplots(figsize=(3.6, 2.9), constrained_layout=True)
        mesh = ax.contourf(
            lam_grid,
            q_grid,
            z_fc1,
            levels=np.linspace(0.0, 18.0, 19),
            cmap="viridis",
        )
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
        cbar.set_label(f"Extension1 [s] ({label})")
        ax.set_xlabel(r"Arrival rate $\lambda$ [veh / 10 s]")
        ax.set_ylabel(r"Current queue $q$ [m / lane]")
        saved.extend(_save_both(fig, out_dir, f"control_surface_fc1_{slug}"))

        z_fc2 = np.zeros((len(q_grid), len(ext1_grid)), dtype=float)
        for i, q_val in enumerate(q_grid):
            for j, e_val in enumerate(ext1_grid):
                z_fc2[i, j] = eng.infer_fc2(float(e_val), float(q_val))
        fc2_surfaces[slug] = z_fc2

        fig, ax = plt.subplots(figsize=(3.6, 2.9), constrained_layout=True)
        mesh = ax.contourf(
            ext1_grid,
            q_grid,
            z_fc2,
            levels=np.linspace(0.0, 18.0, 19),
            cmap="viridis",
        )
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
        cbar.set_label(f"Extension2 [s] ({label})")
        ax.set_xlabel("Extension1 [s]")
        ax.set_ylabel(r"Competing queue $q'$ [m / lane]")
        saved.extend(_save_both(fig, out_dir, f"control_surface_fc2_{slug}"))

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.45), sharey=True, constrained_layout=True)
    levels = np.linspace(0.0, 18.0, 19)
    last_mesh = None
    for idx, (slug, label, _) in enumerate(engines):
        ax = axes[idx]
        last_mesh = ax.contourf(lam_grid, q_grid, fc1_surfaces[slug], levels=levels, cmap="viridis")
        ax.set_xlabel(f"$\\lambda$ [veh / 10 s] ({label})")
        if idx == 0:
            ax.set_ylabel(r"Current queue $q$ [m / lane]")
    if last_mesh is not None:
        cbar = fig.colorbar(last_mesh, ax=axes.tolist(), pad=0.02, shrink=0.92)
        cbar.set_label("Extension1 [s]")
    saved.extend(_save_both(fig, out_dir, "control_surface_fc1_combined"))

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.45), sharey=True, constrained_layout=True)
    last_mesh = None
    for idx, (slug, label, _) in enumerate(engines):
        ax = axes[idx]
        last_mesh = ax.contourf(ext1_grid, q_grid, fc2_surfaces[slug], levels=levels, cmap="viridis")
        ax.set_xlabel(f"Extension1 [s] ({label})")
        if idx == 0:
            ax.set_ylabel(r"Competing queue $q'$ [m / lane]")
    if last_mesh is not None:
        cbar = fig.colorbar(last_mesh, ax=axes.tolist(), pad=0.02, shrink=0.92)
        cbar.set_label("Extension2 [s]")
    saved.extend(_save_both(fig, out_dir, "control_surface_fc2_combined"))

    return saved


def plot_phase_delays(summary_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render per-phase mean delay with 95% CI error bars using grouped markers."""
    apply_academic_style()
    saved: list[Path] = []
    fuzzy_ctrls = ("Mamdani", "Sugeno", "OSFI-literal")
    offsets = (-0.18, 0.0, 0.18)
    x_base = np.arange(len(APPROACHES), dtype=float)

    for scen in ("moderate", "heavy"):
        sub = summary_df[
            (summary_df["scenario"] == scen)
            & (summary_df["approach"].isin(APPROACHES))
        ]
        fig, ax = plt.subplots(figsize=(3.6, 2.7), constrained_layout=True)
        for ctrl, offset in zip(fuzzy_ctrls, offsets):
            c_sub = (
                sub[sub["controller"] == ctrl]
                .set_index("approach")
                .reindex(APPROACHES)
            )
            means = c_sub["avg_delay_s_mean"].to_numpy(dtype=float)
            cis = c_sub["avg_delay_s_ci95"].to_numpy(dtype=float)
            ax.errorbar(
                x_base + offset,
                means,
                yerr=cis,
                fmt=CONTROLLER_MARKERS[ctrl],
                color=CONTROLLER_COLORS[ctrl],
                markersize=6.0,
                capsize=3.5,
                elinewidth=1.3,
                label=ctrl,
                linestyle="none",
            )
        ax.set_xticks(x_base)
        ax.set_xticklabels(list(APPROACHES))
        ax.set_xlabel("Signal phase (approach)")
        ax.set_ylabel("Average vehicle delay [s / veh]")
        ax.legend(loc="upper left", frameon=True)
        saved.extend(_save_both(fig, out_dir, f"phase_delay_{scen}"))

    return saved


def plot_phase_exits(summary_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render grouped bar charts of per-phase throughput with 95% CI error bars."""
    apply_academic_style()
    saved: list[Path] = []
    fuzzy_ctrls = ("Mamdani", "Sugeno", "OSFI-literal")
    width = 0.25
    offsets = (-width, 0.0, width)
    x_base = np.arange(len(APPROACHES), dtype=float)

    for scen in ("moderate", "heavy"):
        sub = summary_df[
            (summary_df["scenario"] == scen)
            & (summary_df["approach"].isin(APPROACHES))
        ]
        fig, ax = plt.subplots(figsize=(3.6, 2.7), constrained_layout=True)
        for ctrl, offset in zip(fuzzy_ctrls, offsets):
            c_sub = (
                sub[sub["controller"] == ctrl]
                .set_index("approach")
                .reindex(APPROACHES)
            )
            means = c_sub["throughput_veh_mean"].to_numpy(dtype=float)
            cis = c_sub["throughput_veh_ci95"].to_numpy(dtype=float)
            ax.bar(
                x_base + offset,
                means,
                width=width * 0.9,
                yerr=cis,
                capsize=2.8,
                color=CONTROLLER_COLORS[ctrl],
                edgecolor="black",
                linewidth=0.5,
                alpha=0.88,
                label=ctrl,
                error_kw={"elinewidth": 1.0},
            )
        ax.set_xticks(x_base)
        ax.set_xticklabels(list(APPROACHES))
        ax.set_xlabel("Signal phase (approach)")
        ax.set_ylabel("Discharged vehicles [veh / h]")
        ax.set_ylim(0.0, float(sub["throughput_veh_mean"].max()) * 1.24)
        ax.legend(loc="upper right", frameon=True)
        saved.extend(_save_both(fig, out_dir, f"phase_exit_{scen}"))

    return saved


def plot_overall_delay_boxplot(raw_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render per-seed overall delay distributions across 5 controllers x 3 scenarios."""
    apply_academic_style()
    overall = raw_df[raw_df["approach"] == "overall"].copy()
    scenarios = ("moderate", "heavy", "peak")
    controllers = ("Mamdani", "Sugeno", "OSFI-literal", "Webster", "Actuated")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.85), sharey=False, constrained_layout=True)

    for idx, scen in enumerate(scenarios):
        ax = axes[idx]
        s_df = overall[overall["scenario"] == scen]
        data = [
            s_df[s_df["controller"] == c]["avg_delay_s"].to_numpy(dtype=float)
            for c in controllers
        ]
        bp = ax.boxplot(
            data,
            positions=np.arange(len(controllers)),
            widths=0.55,
            patch_artist=True,
            showfliers=True,
            flierprops={"marker": "o", "markersize": 3.0, "alpha": 0.6},
            medianprops={"color": "black", "linewidth": 1.3},
        )
        for patch, ctrl in zip(bp["boxes"], controllers):
            patch.set_facecolor(CONTROLLER_COLORS[ctrl])
            patch.set_alpha(0.82)
            patch.set_edgecolor("black")
            patch.set_linewidth(0.7)

        ax.set_xticks(np.arange(len(controllers)))
        ax.set_xticklabels(
            ["Mamdani", "Sugeno", "OSFI-lit.", "Webster", "Actuated"],
            rotation=28,
            ha="right",
        )
        ax.set_xlabel(f"Scenario: {scen}")
        if idx == 0:
            ax.set_ylabel("Overall average delay [s / veh]")

    return _save_both(fig, out_dir, "overall_delay_boxplot")


def plot_timeline_example(
    out_dir: Path,
    seed: int = 202501,
    window_start_s: int = 0,
    window_duration_s: int = 600,
) -> list[Path]:
    """Render 600 s heavy-scenario timeline of queues, active green band, and Extension2."""
    apply_academic_style()
    sim = IntersectionSimulator()
    eng = OSFILiteralInference(shoulder_edges=True)
    ctrl = FuzzyController(engine=eng)
    res = sim.run(
        controller=ctrl,
        scenario=ScenarioDemand.from_name("heavy"),
        seed=seed,
        controller_name="OSFI-literal",
    )

    t0 = window_start_s
    t1 = window_start_s + window_duration_s
    times = np.arange(t0, t1, dtype=float)

    fig, (ax_q, ax_ext) = plt.subplots(
        2,
        1,
        figsize=(7.2, 4.2),
        sharex=True,
        gridspec_kw={"height_ratios": [2.1, 1.1]},
        constrained_layout=True,
    )

    for step in range(t0, t1):
        sig_state = res.signal_state_history[step]
        phase = res.active_phase_history[step]
        if sig_state == "GREEN":
            ax_q.axvspan(
                step,
                step + 1,
                color=APPROACH_COLORS[phase],
                alpha=0.13,
                lw=0,
            )

    max_q_win = 0.0
    for app in APPROACHES:
        q_slice = res.queue_m_history[app][t0:t1]
        if len(q_slice) > 0:
            max_q_win = max(max_q_win, float(np.max(q_slice)))
        ax_q.plot(
            times,
            q_slice,
            color=APPROACH_COLORS[app],
            lw=1.35,
            label=f"Phase {app}",
        )

    band_patches = [
        Patch(facecolor=APPROACH_COLORS[app], alpha=0.25, label=f"Green {app}")
        for app in APPROACHES
    ]
    handles, labels = ax_q.get_legend_handles_labels()
    ax_q.legend(
        handles=handles + band_patches,
        labels=labels + [f"Green {a}" for a in APPROACHES],
        loc="upper left",
        ncol=4,
        frameon=True,
        columnspacing=0.9,
        handlelength=1.4,
    )
    ax_q.set_ylabel("Queue length [m / lane]")
    ax_q.set_xlim(float(t0), float(t1))
    ax_q.set_ylim(0.0, max_q_win * 1.28)

    dec_in_win = [
        d
        for d in res.decision_log
        if float(t0) <= float(d["time"]) <= float(t1)
    ]
    dec_times = [float(d["time"]) for d in dec_in_win]
    dec_ext2 = [float(d["extension2"]) for d in dec_in_win]
    dec_ext1 = [float(d["extension1"]) for d in dec_in_win]

    ax_ext.step(
        dec_times,
        dec_ext1,
        where="post",
        color="#7F7F7F",
        lw=1.1,
        ls="--",
        label="Extension1 (FC$_1$)",
    )
    ax_ext.step(
        dec_times,
        dec_ext2,
        where="post",
        color=CONTROLLER_COLORS["OSFI-literal"],
        lw=1.5,
        label="Extension2 (FC$_2$)",
    )
    ax_ext.scatter(
        dec_times,
        dec_ext2,
        color=CONTROLLER_COLORS["OSFI-literal"],
        s=14,
        zorder=4,
    )
    ax_ext.set_xlabel("Simulation time $t$ [s] (heavy scenario, OSFI-literal)")
    ax_ext.set_ylabel("Extension [s]")
    ax_ext.set_ylim(-0.8, 19.5)
    ax_ext.legend(loc="upper right", frameon=True, ncol=2)

    return _save_both(fig, out_dir, "timeline_example")


def generate_all_figures(
    results_root: str | Path = "results",
    figures_dir: str | Path = "figures",
) -> list[Path]:
    """Generate all required PDF and PNG figures from saved experiment results."""
    res_path = Path(results_root)
    fig_path = Path(figures_dir)

    raw_df = pd.read_csv(res_path / "raw" / "reproduction_runs.csv")
    summary_df = pd.read_csv(res_path / "summary" / "metrics_summary_ci.csv")

    generated: list[Path] = []
    generated.extend(plot_mf_inputs_outputs(fig_path))
    generated.extend(plot_control_surfaces(fig_path, shoulder_edges=True))
    generated.extend(plot_phase_delays(summary_df, fig_path))
    generated.extend(plot_phase_exits(summary_df, fig_path))
    generated.extend(plot_overall_delay_boxplot(raw_df, fig_path))
    generated.extend(plot_timeline_example(fig_path))
    return generated
