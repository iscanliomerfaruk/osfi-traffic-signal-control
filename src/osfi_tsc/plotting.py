"""Publication-grade figure generation for the reproduction, contribution, and Stage 3 diagnostics."""

from __future__ import annotations

from pathlib import Path
import matplotlib
from matplotlib.colors import TwoSlopeNorm
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
    CRIInference,
    CRIStageEngine,
    MamdaniInference,
    OSFIDJInference,
    OSFIDJStageEngine,
    OSFILiteralInference,
    SugenoInference,
)
from osfi_tsc.sim import (
    APPROACHES,
    IntersectionSimulator,
    ScenarioDemand,
    compute_matched_input_sigmas,
)

matplotlib.use("Agg")

CONTROLLER_COLORS: dict[str, str] = {
    "Mamdani": "#E69F00",
    "Sugeno": "#D55E00",
    "OSFI-literal": "#0072B2",
    "OSFI-DJ-S": "#56B4E9",
    "CRI-NS": "#882255",
    "OSFI-DJ-NS": "#117733",
    "OSFI-DJ-NS-mis": "#AA4499",
    "Webster": "#009E73",
    "Actuated": "#CC79A7",
}

CONTROLLER_MARKERS: dict[str, str] = {
    "Mamdani": "o",
    "Sugeno": "s",
    "OSFI-literal": "^",
    "OSFI-DJ-S": "P",
    "CRI-NS": "X",
    "OSFI-DJ-NS": "*",
    "OSFI-DJ-NS-mis": "d",
    "Webster": "D",
    "Actuated": "v",
}

CONTROLLER_LINESTYLES: dict[str, str] = {
    "Mamdani": "-",
    "Sugeno": "--",
    "OSFI-literal": ":",
    "OSFI-DJ-S": "-.",
    "CRI-NS": "--",
    "OSFI-DJ-NS": "-",
    "OSFI-DJ-NS-mis": ":",
    "Webster": "-",
    "Actuated": "-.",
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
    fig.savefig(pdf_path, bbox_inches="tight", dpi=300, metadata={"CreationDate": None})
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


PHASE_PLOT_CONTROLLERS: tuple[str, ...] = ("Mamdani", "Sugeno", "OSFI-literal", "Webster", "Actuated")
PHASE_PLOT_SCENARIOS: tuple[str, ...] = ("moderate", "heavy", "peak")
BOXPLOT_SCENARIOS: tuple[str, ...] = ("moderate", "heavy", "peak", "stress")
LOG_SCALE_SCENARIOS: tuple[str, ...] = ("peak", "stress")


def _available_scenarios(df: pd.DataFrame, wanted: tuple[str, ...]) -> list[str]:
    present = set(df["scenario"].unique())
    return [scen for scen in wanted if scen in present]


def plot_phase_delays(summary_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render per-phase mean delay with 95% CI error bars for all reproduction controllers."""
    apply_academic_style()
    saved: list[Path] = []
    ctrls = [c for c in PHASE_PLOT_CONTROLLERS if c in set(summary_df["controller"])]
    offsets = np.linspace(-0.3, 0.3, len(ctrls))
    x_base = np.arange(len(APPROACHES), dtype=float)

    for scen in _available_scenarios(summary_df, PHASE_PLOT_SCENARIOS):
        sub = summary_df[
            (summary_df["scenario"] == scen)
            & (summary_df["approach"].isin(APPROACHES))
        ]
        fig, ax = plt.subplots(figsize=(4.4, 3.0), constrained_layout=True)
        for ctrl, offset in zip(ctrls, offsets):
            c_sub = (
                sub[sub["controller"] == ctrl]
                .set_index("approach")
                .reindex(APPROACHES)
            )
            ax.errorbar(
                x_base + offset,
                c_sub["avg_delay_s_mean"].to_numpy(dtype=float),
                yerr=c_sub["avg_delay_s_ci95"].to_numpy(dtype=float),
                fmt=CONTROLLER_MARKERS[ctrl],
                color=CONTROLLER_COLORS[ctrl],
                markersize=5.5,
                capsize=3.0,
                elinewidth=1.2,
                label=ctrl,
                linestyle="none",
            )
        ax.set_xticks(x_base)
        ax.set_xticklabels(list(APPROACHES))
        ax.set_xlabel("Signal phase (approach)")
        ax.set_ylabel("Average vehicle delay [s / veh]")
        if scen in LOG_SCALE_SCENARIOS:
            ax.set_yscale("log")
            ax.set_ylabel("Average vehicle delay [s / veh, log]")
        ax.set_title(f"Scenario: {scen}", fontsize=9.5)
        fig.legend(loc="outside lower center", ncol=3, frameon=False)
        saved.extend(_save_both(fig, out_dir, f"phase_delay_{scen}"))

    return saved


def plot_phase_exits(summary_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render grouped bar charts of per-phase throughput with 95% CI error bars."""
    apply_academic_style()
    saved: list[Path] = []
    ctrls = [c for c in PHASE_PLOT_CONTROLLERS if c in set(summary_df["controller"])]
    width = 0.8 / len(ctrls)
    offsets = (np.arange(len(ctrls)) - 0.5 * (len(ctrls) - 1)) * width
    x_base = np.arange(len(APPROACHES), dtype=float)

    for scen in _available_scenarios(summary_df, PHASE_PLOT_SCENARIOS):
        sub = summary_df[
            (summary_df["scenario"] == scen)
            & (summary_df["approach"].isin(APPROACHES))
        ]
        fig, ax = plt.subplots(figsize=(4.4, 3.0), constrained_layout=True)
        for ctrl, offset in zip(ctrls, offsets):
            c_sub = (
                sub[sub["controller"] == ctrl]
                .set_index("approach")
                .reindex(APPROACHES)
            )
            ax.bar(
                x_base + offset,
                c_sub["throughput_veh_mean"].to_numpy(dtype=float),
                width=width * 0.92,
                yerr=c_sub["throughput_veh_ci95"].to_numpy(dtype=float),
                capsize=2.0,
                color=CONTROLLER_COLORS[ctrl],
                edgecolor="black",
                linewidth=0.4,
                alpha=0.88,
                label=ctrl,
                error_kw={"elinewidth": 0.9},
            )
        ax.set_xticks(x_base)
        ax.set_xticklabels(list(APPROACHES))
        ax.set_xlabel("Signal phase (approach)")
        ax.set_ylabel("Discharged vehicles [veh / h]")
        ax.set_ylim(0.0, float(sub["throughput_veh_mean"].max()) * 1.12)
        ax.set_title(f"Scenario: {scen}", fontsize=9.5)
        fig.legend(loc="outside lower center", ncol=3, frameon=False)
        saved.extend(_save_both(fig, out_dir, f"phase_exit_{scen}"))

    return saved


def plot_overall_delay_boxplot(raw_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render per-seed overall delay distributions for 5 controllers in all 4 scenarios."""
    apply_academic_style()
    overall = raw_df[raw_df["approach"] == "overall"].copy()
    scenarios = _available_scenarios(overall, BOXPLOT_SCENARIOS)
    controllers = [c for c in PHASE_PLOT_CONTROLLERS if c in set(overall["controller"])]
    short = {"OSFI-literal": "OSFI-lit."}

    n_cols = 2
    n_rows = int(np.ceil(len(scenarios) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(7.2, 2.7 * n_rows), constrained_layout=True)
    flat_axes = np.atleast_1d(axes).ravel()

    for idx, scen in enumerate(scenarios):
        ax = flat_axes[idx]
        s_df = overall[overall["scenario"] == scen]
        data = [s_df[s_df["controller"] == c]["avg_delay_s"].to_numpy(dtype=float) for c in controllers]
        bp = ax.boxplot(
            data,
            positions=np.arange(len(controllers)),
            widths=0.55,
            patch_artist=True,
            showfliers=True,
            flierprops={"marker": "o", "markersize": 2.5, "alpha": 0.6},
            medianprops={"color": "black", "linewidth": 1.2},
        )
        for patch, ctrl in zip(bp["boxes"], controllers):
            patch.set_facecolor(CONTROLLER_COLORS[ctrl])
            patch.set_alpha(0.82)
            patch.set_edgecolor("black")
            patch.set_linewidth(0.7)
        ax.set_xticks(np.arange(len(controllers)))
        ax.set_xticklabels([short.get(c, c) for c in controllers], rotation=20, ha="right")
        scale_tag = ""
        if scen in LOG_SCALE_SCENARIOS:
            ax.set_yscale("log")
            scale_tag = " (log scale)"
        ax.set_title(f"Scenario: {scen}{scale_tag}", fontsize=9.5)
        if idx % n_cols == 0:
            ax.set_ylabel("Overall delay [s / veh]")
    for ax in flat_axes[len(scenarios):]:
        ax.set_visible(False)

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


def plot_osfi_inference_example(out_dir: Path) -> list[Path]:
    """Render 2x2 teaching figure of OSFI-DJ vs CRI on one rule and full FC1 aggregation."""
    apply_academic_style()
    x1_val = 9.5
    x2_val = 2.5
    sigma1 = 1.0
    sigma2 = 10.0
    rule_idx = 12

    osfi_s = OSFIDJStageEngine(stage="fc1", sigma1=0.0, sigma2=0.0)
    osfi_ns = OSFIDJStageEngine(stage="fc1", sigma1=sigma1, sigma2=sigma2)
    cri_ns = CRIStageEngine(stage="fc1", sigma1=sigma1, sigma2=sigma2)

    detail_ns = osfi_ns.evaluate_rule_detail(rule_idx=rule_idx, x1=x1_val, x2=x2_val)
    detail_s = osfi_s.evaluate_rule_detail(rule_idx=rule_idx, x1=x1_val, x2=x2_val)

    a_star_ns = osfi_ns.build_input_fuzzy_set(x1_val, x2_val)
    b_star_cri_rule = cri_ns.infer_rule_conclusion(rule_idx, a_star_ns)

    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.0), constrained_layout=True)

    ax_a = axes[0, 0]
    x1_g = detail_ns["x1_grid"]
    x2_g = detail_ns["x2_grid"]
    a_rule_2d = detail_ns["a_rule_2d"].T
    a_star_2d = detail_ns["a_star_2d"].T

    cf_a = ax_a.contourf(
        x1_g,
        x2_g,
        a_rule_2d,
        levels=np.linspace(0.0, 1.0, 11),
        cmap="Blues",
        alpha=0.85,
    )
    cs_star = ax_a.contour(
        x1_g,
        x2_g,
        a_star_2d,
        levels=[0.1, 0.3, 0.6, 0.9],
        colors="#D55E00",
        linewidths=1.35,
        linestyles="--",
    )
    ax_a.clabel(cs_star, inline=True, fontsize=7.5, fmt="%.1f")
    ax_a.scatter(
        [x1_val],
        [x2_val],
        color="#D55E00",
        edgecolor="black",
        marker="*",
        s=95,
        zorder=5,
        label=r"Measurement $(9.5, 2.5)$",
    )
    cbar_a = fig.colorbar(cf_a, ax=ax_a, pad=0.02)
    cbar_a.set_label(r"Rule 13 $A(\lambda, q)$ (H, Sh)")
    ax_a.set_xlabel(r"(a) Arrival rate $\lambda$ [veh / 10 s]")
    ax_a.set_ylabel(r"Queue length $q$ [m / lane]")
    ax_a.set_ylim(0.0, 35.0)
    ax_a.legend(loc="upper left", frameon=True)

    ax_b = axes[0, 1]
    y_g = detail_ns["y_grid"]
    b_grid = detail_ns["b_grid"]
    r_table = detail_ns["r_table"]
    act = np.flatnonzero(a_star_ns > 1e-3)
    a_act = a_star_ns[act]
    i_act_b = np.asarray(osfi_ns.implicator_fn(a_act[:, None], b_grid[None, :]), dtype=float)
    y_probe = (2.0, 7.5, 15.0)
    probe_colors = ("#0072B2", "#D55E00", "#009E73")
    offsets = ((-10, -14), (-44, 8), (-10, 7))
    for y_val, col, xytext in zip(y_probe, probe_colors, offsets):
        k = int(np.argmin(np.abs(y_g - y_val)))
        cost = np.mean(np.abs(r_table[act, k][:, None] - i_act_b), axis=0)
        b_opt = float(detail_ns["b_star"][k])
        j_opt = int(np.argmin(np.abs(b_grid - b_opt)))
        ax_b.plot(b_grid, cost, color=col, lw=1.6, label=f"$y={y_g[k]:.1f}$ s")
        ax_b.scatter(
            [b_grid[j_opt]],
            [cost[j_opt]],
            color=col,
            edgecolor="black",
            s=42,
            zorder=5,
        )
        ax_b.annotate(
            f"$b^*={b_opt:.2f}$",
            xy=(b_grid[j_opt], cost[j_opt]),
            xytext=xytext,
            textcoords="offset points",
            fontsize=7.5,
            color=col,
            bbox={"boxstyle": "square,pad=0.08", "fc": "white", "ec": "none", "alpha": 0.75},
        )
    ax_b.set_xlabel(r"(b) Candidate conclusion value $b = B^*(y)$")
    ax_b.set_ylabel(r"$d_1$ cost $\frac{1}{|X^*|}\sum_x |R(x,y) - I(A^*(x), b)|$")
    ax_b.set_xlim(0.0, 1.0)
    ax_b.set_ylim(-0.015, 0.21)
    ax_b.legend(loc="upper right", frameon=True, title="Rule 13, OSFI-DJ-NS", title_fontsize=7.5)

    ax_c = axes[1, 0]
    b_rule = detail_ns["b_rule"]
    b_star_s = detail_s["b_star"]
    b_star_ns = detail_ns["b_star"]

    ax_c.fill_between(
        y_g,
        0.0,
        b_rule,
        color="#7F7F7F",
        alpha=0.22,
        label=r"Consequent $B(y)$ (Sh)",
    )
    ax_c.plot(y_g, b_rule, color="#7F7F7F", lw=1.2, ls=":")
    ax_c.plot(
        y_g,
        b_star_s,
        color=CONTROLLER_COLORS["OSFI-DJ-S"],
        lw=1.8,
        ls="-.",
        label="OSFI-DJ-S (= CRI-S)",
    )
    ax_c.plot(
        y_g,
        b_star_cri_rule,
        color=CONTROLLER_COLORS["CRI-NS"],
        lw=1.8,
        ls="--",
        label=r"CRI-NS ($\sigma_q=10$ m)",
    )
    ax_c.plot(
        y_g,
        b_star_ns,
        color=CONTROLLER_COLORS["OSFI-DJ-NS"],
        lw=2.0,
        ls="-",
        label=r"OSFI-DJ-NS ($\sigma_q=10$ m)",
    )
    ax_c.set_xlabel("(c) Output universe $y$ [s] (Rule 13: H, Sh $\\to$ Sh)")
    ax_c.set_ylabel(r"Rule conclusion $B^*_{13}(y)$")
    ax_c.set_xlim(0.0, 25.0)
    ax_c.set_ylim(-0.04, 1.08)
    ax_c.legend(loc="lower right", frameon=True, fontsize=7.8)

    ax_d = axes[1, 1]
    b_agg_s = osfi_s.infer_aggregated_set(x1_val, x2_val)
    b_agg_ns = osfi_ns.infer_aggregated_set(x1_val, x2_val)
    b_agg_cri = cri_ns.infer_aggregated_set(x1_val, x2_val)

    eff_s = np.maximum(0.0, b_agg_s - float(np.min(b_agg_s)))
    eff_ns = np.maximum(0.0, b_agg_ns - float(np.min(b_agg_ns)))
    eff_cri = np.maximum(0.0, b_agg_cri - float(np.min(b_agg_cri)))

    c_s = osfi_s.infer_direct(x1_val, x2_val)
    c_ns = osfi_ns.infer_direct(x1_val, x2_val)
    c_cri = cri_ns.infer_direct(x1_val, x2_val)

    ax_d.plot(
        y_g,
        eff_s,
        color=CONTROLLER_COLORS["OSFI-DJ-S"],
        lw=1.7,
        ls="-.",
        label=f"OSFI-DJ-S ({c_s:.2f} s)",
    )
    ax_d.plot(
        y_g,
        eff_cri,
        color=CONTROLLER_COLORS["CRI-NS"],
        lw=1.7,
        ls="--",
        label=f"CRI-NS ({c_cri:.2f} s)",
    )
    ax_d.plot(
        y_g,
        eff_ns,
        color=CONTROLLER_COLORS["OSFI-DJ-NS"],
        lw=2.0,
        ls="-",
        label=f"OSFI-DJ-NS ({c_ns:.2f} s)",
    )
    ax_d.fill_between(
        y_g,
        0.0,
        eff_ns,
        color=CONTROLLER_COLORS["OSFI-DJ-NS"],
        alpha=0.16,
    )
    ax_d.axvline(c_s, color=CONTROLLER_COLORS["OSFI-DJ-S"], lw=1.2, ls="-.")
    ax_d.axvline(c_cri, color=CONTROLLER_COLORS["CRI-NS"], lw=1.2, ls="--")
    ax_d.axvline(c_ns, color=CONTROLLER_COLORS["OSFI-DJ-NS"], lw=1.5, ls="-")

    ax_d.set_xlabel("(d) Output universe $y$ [s] (16-rule FITA aggregation)")
    ax_d.set_ylabel(r"Above-floor $B^*(y) - \min B^*$")
    ax_d.set_xlim(0.0, 25.0)
    ax_d.set_ylim(0.0, max(float(np.max(eff_s)), float(np.max(eff_ns)), 0.25) * 1.1)
    ax_d.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=3,
        frameon=False,
        fontsize=7.5,
        handlelength=1.8,
        columnspacing=0.9,
    )

    return _save_both(fig, out_dir, "osfi_inference_example")


def plot_control_surfaces_osfi(out_dir: Path, cache_dir: str | Path = "results/cache") -> list[Path]:
    """Render 2x2 FC1 control surfaces for OSFI-DJ-S, OSFI-DJ-NS, CRI-NS, and difference map."""
    apply_academic_style()
    sig_lam, sig_q = compute_matched_input_sigmas(
        sigma_q=10.0,
        p_miss=0.0,
    )
    sig_e1 = 0.0

    eng_s = OSFIDJInference(
        sigma_lambda=0.0,
        sigma_queue=0.0,
        sigma_ext1=0.0,
        use_lut=True,
        cache_dir=cache_dir,
    )
    eng_ns = OSFIDJInference(
        sigma_lambda=sig_lam,
        sigma_queue=sig_q,
        sigma_ext1=sig_e1,
        use_lut=True,
        cache_dir=cache_dir,
    )
    eng_cri = CRIInference(
        sigma_lambda=sig_lam,
        sigma_queue=sig_q,
        sigma_ext1=sig_e1,
        use_lut=True,
        cache_dir=cache_dir,
    )

    assert eng_s.fc1_lut is not None
    assert eng_ns.fc1_lut is not None
    assert eng_cri.fc1_lut is not None

    lam_grid = eng_s.fc1_lut["x1_lut"]
    q_grid = eng_s.fc1_lut["x2_lut"]

    z_s = eng_s.fc1_lut["table"].T
    z_ns = eng_ns.fc1_lut["table"].T
    z_cri = eng_cri.fc1_lut["table"].T
    z_diff = z_ns - z_cri

    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.1), constrained_layout=True)
    levels = np.linspace(0.0, 18.0, 19)

    panels = [
        (axes[0, 0], z_s, "(a) $\\lambda$ [veh / 10 s] — OSFI-DJ-S ($\\sigma_q=0$ m)"),
        (axes[0, 1], z_ns, "(b) $\\lambda$ [veh / 10 s] — OSFI-DJ-NS ($\\sigma_q=10$ m)"),
        (axes[1, 0], z_cri, "(c) $\\lambda$ [veh / 10 s] — CRI-NS ($\\sigma_q=10$ m)"),
    ]
    for ax, z_mat, xlabel in panels:
        mesh = ax.contourf(lam_grid, q_grid, z_mat, levels=levels, cmap="viridis")
        cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
        cbar.set_label("Extension1 [s]")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r"Current queue $q$ [m / lane]")

    ax_d = axes[1, 1]
    max_abs = max(0.5, float(np.max(np.abs(z_diff))))
    diff_levels = np.linspace(-max_abs, max_abs, 21)
    norm = TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)
    mesh_d = ax_d.contourf(
        lam_grid,
        q_grid,
        z_diff,
        levels=diff_levels,
        cmap="RdBu_r",
        norm=norm,
    )
    cbar_d = fig.colorbar(mesh_d, ax=ax_d, pad=0.02)
    cbar_d.set_label(r"$\Delta$ Extension1 [s]")
    ax_d.set_xlabel(r"(d) $\lambda$ [veh / 10 s] — (OSFI-DJ-NS $-$ CRI-NS)")
    ax_d.set_ylabel(r"Current queue $q$ [m / lane]")

    return _save_both(fig, out_dir, "control_surfaces_osfi")


NOISE_PLOT_CONTROLLERS: tuple[str, ...] = (
    "OSFI-DJ-NS",
    "OSFI-DJ-S",
    "CRI-NS",
    "OSFI-DJ-NS-mis",
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "Actuated",
    "Webster",
)
NOISE_P_MISS: tuple[float, ...] = (0.0, 0.1, 0.2)
NOISE_SCENARIOS: tuple[str, ...] = ("heavy", "peak")


def _noise_panel_series(
    scen_df: pd.DataFrame,
    p_miss: float,
    ctrl: str,
    relative: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    c_df = scen_df[
        np.isclose(scen_df["p_miss"], p_miss) & (scen_df["controller"] == ctrl)
    ].sort_values("sigma_q")
    if c_df.empty:
        return None
    sig_q = c_df["sigma_q"].to_numpy(dtype=float)
    means = c_df["avg_delay_s_mean"].to_numpy(dtype=float)
    cis = c_df["avg_delay_s_ci95"].to_numpy(dtype=float)
    if not relative:
        return sig_q, means, cis
    ref = float(means[int(np.argmin(sig_q))])
    return sig_q, 100.0 * (means / ref - 1.0), 100.0 * cis / ref


def _render_noise_figure(
    scen_df: pd.DataFrame,
    scen: str,
    relative: bool,
) -> plt.Figure:
    fig, axes = plt.subplots(1, len(NOISE_P_MISS), figsize=(7.5, 3.4), sharey=True, constrained_layout=True)
    for p_idx, p_miss in enumerate(NOISE_P_MISS):
        ax = axes[p_idx]
        for ctrl in NOISE_PLOT_CONTROLLERS:
            series = _noise_panel_series(scen_df, p_miss, ctrl, relative)
            if series is None:
                continue
            sig_q, vals, errs = series
            ax.errorbar(
                sig_q,
                vals,
                yerr=errs,
                color=CONTROLLER_COLORS[ctrl],
                marker=CONTROLLER_MARKERS[ctrl],
                linestyle=CONTROLLER_LINESTYLES[ctrl],
                lw=1.4,
                markersize=4.5,
                capsize=2.3,
                elinewidth=0.9,
                label=ctrl if p_idx == 0 else None,
            )
        ax.set_xticks([0.0, 5.0, 10.0, 15.0])
        ax.set_title(f"$p_{{\\mathrm{{miss}}}}={p_miss:.1f}$", fontsize=9.5)
        ax.set_xlabel(r"Queue noise $\sigma_q$ [m / lane]")
        if relative:
            ax.axhline(0.0, color="black", lw=0.7)
        elif scen == "peak":
            ax.set_yscale("log")
    if relative:
        axes[0].set_ylabel(f"Delay change vs. own $\\sigma_q=0$ [%] ({scen})")
    else:
        log_tag = ", log" if scen == "peak" else ""
        axes[0].set_ylabel(f"Overall delay [s / veh{log_tag}] ({scen})")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="outside lower center",
        ncol=5,
        frameon=False,
        fontsize=8.0,
        columnspacing=1.0,
        handlelength=2.0,
    )
    return fig


def plot_noise_degradation(exp_b_sum_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render absolute delay vs sigma_q across p_miss panels (shared y) for heavy and peak."""
    apply_academic_style()
    saved: list[Path] = []
    overall = exp_b_sum_df[exp_b_sum_df["approach"] == "overall"]
    for scen in NOISE_SCENARIOS:
        fig = _render_noise_figure(overall[overall["scenario"] == scen], scen, relative=False)
        saved.extend(_save_both(fig, out_dir, f"noise_degradation_{scen}"))
    return saved


def plot_noise_degradation_relative(exp_b_sum_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render delay change relative to each controller's own sigma_q = 0 value, in percent."""
    apply_academic_style()
    saved: list[Path] = []
    overall = exp_b_sum_df[exp_b_sum_df["approach"] == "overall"]
    for scen in NOISE_SCENARIOS:
        fig = _render_noise_figure(overall[overall["scenario"] == scen], scen, relative=True)
        saved.extend(_save_both(fig, out_dir, f"noise_degradation_rel_{scen}"))
    return saved


def compute_max_firing_map(
    lam_grid: np.ndarray,
    q_grid: np.ndarray,
    and_operator: str,
    sigma_scale: float,
) -> np.ndarray:
    """Return max_i alpha_i of the 16 FC1 rules over a (q, lambda) grid."""
    lam_mfs = arrival_rate_memberships(lam_grid, shoulder_edges=True, sigma_scale=sigma_scale)
    q_mfs = queue_length_memberships(q_grid, shoulder_edges=True, sigma_scale=sigma_scale)
    best = np.zeros((len(q_grid), len(lam_grid)), dtype=float)
    for mu_lam in lam_mfs.values():
        for mu_q in q_mfs.values():
            a = np.asarray(mu_lam, dtype=float)[None, :]
            b = np.asarray(mu_q, dtype=float)[:, None]
            if and_operator == "min":
                alpha = np.minimum(a, b)
            else:
                alpha = np.maximum(0.0, a + b - 1.0)
            best = np.maximum(best, alpha)
    return best


def plot_dead_zone_map(out_dir: Path) -> list[Path]:
    """Render max_i alpha_i over (lambda, q) for Lukasiewicz, min, and widened-Lukasiewicz AND."""
    apply_academic_style()
    lam_grid = np.linspace(0.0, 12.0, 481)
    q_grid = np.linspace(0.0, 60.0, 481)
    variants = (
        ("(a) Łukasiewicz AND, $\\sigma\\times1.0$", "lukasiewicz", 1.0),
        ("(b) min AND, $\\sigma\\times1.0$", "min", 1.0),
        ("(c) Łukasiewicz AND, $\\sigma\\times1.5$", "lukasiewicz", 1.5),
    )
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.9), sharey=True, constrained_layout=True)
    last_im = None
    for ax, (title, and_op, scale) in zip(axes, variants):
        fmap = compute_max_firing_map(lam_grid, q_grid, and_op, scale)
        dead_frac = 100.0 * float(np.mean(fmap < 1e-6))
        last_im = ax.pcolormesh(lam_grid, q_grid, fmap, cmap="magma", vmin=0.0, vmax=1.0, shading="auto")
        if np.any(fmap < 1e-6):
            ax.contourf(lam_grid, q_grid, fmap, levels=[-1.0, 1e-6], colors="none", hatches=["////"])
            ax.contour(lam_grid, q_grid, fmap, levels=[1e-6], colors="#00E5FF", linewidths=1.3)
        ax.set_title(f"{title}\ndead zone = {dead_frac:.1f}% of plane", fontsize=8.5)
        ax.set_xlabel(r"Arrival rate $\lambda$ [veh / 10 s]")
        ax.grid(False)
    axes[0].set_ylabel(r"Queue length $q$ [m / lane]")
    if last_im is not None:
        cbar = fig.colorbar(last_im, ax=axes.tolist(), pad=0.02, shrink=0.95)
        cbar.set_label(r"$\max_i \alpha_i(\lambda, q)$ (FC1)")
    return _save_both(fig, out_dir, "dead_zone_map")


def plot_noise_heatmap(exp_b_sum_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render annotated heatmap of % delay change (OSFI-DJ-NS vs OSFI-DJ-S) over (sigma_q, p_miss)."""
    apply_academic_style()
    overall = exp_b_sum_df[exp_b_sum_df["approach"] == "overall"].copy()
    sig_vals = [0.0, 5.0, 10.0, 15.0]
    p_vals = [0.0, 0.1, 0.2]
    scenarios = ("heavy", "peak")

    matrices: dict[str, np.ndarray] = {}
    diff_s_mats: dict[str, np.ndarray] = {}
    max_abs = 0.5

    for scen in scenarios:
        s_df = overall[overall["scenario"] == scen]
        pct_mat = np.zeros((len(p_vals), len(sig_vals)), dtype=float)
        ds_mat = np.zeros((len(p_vals), len(sig_vals)), dtype=float)
        for i, p_val in enumerate(p_vals):
            for j, sig_val in enumerate(sig_vals):
                cell = s_df[
                    np.isclose(s_df["p_miss"], p_val)
                    & np.isclose(s_df["sigma_q"], sig_val)
                ]
                d_s = float(
                    cell[cell["controller"] == "OSFI-DJ-S"]["avg_delay_s_mean"].iloc[0]
                )
                d_ns = float(
                    cell[cell["controller"] == "OSFI-DJ-NS"]["avg_delay_s_mean"].iloc[0]
                )
                pct = 100.0 * (d_ns - d_s) / d_s
                pct_mat[i, j] = pct
                ds_mat[i, j] = d_ns - d_s
        matrices[scen] = pct_mat
        diff_s_mats[scen] = ds_mat
        max_abs = max(max_abs, float(np.max(np.abs(pct_mat))))

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.75), sharey=True, constrained_layout=True)
    norm = TwoSlopeNorm(vmin=-max_abs * 1.1, vcenter=0.0, vmax=max_abs * 1.1)
    last_im = None

    for idx, scen in enumerate(scenarios):
        ax = axes[idx]
        pct_mat = matrices[scen]
        ds_mat = diff_s_mats[scen]
        last_im = ax.imshow(
            pct_mat,
            cmap="RdBu_r",
            norm=norm,
            aspect="auto",
            origin="upper",
        )
        for i in range(len(p_vals)):
            for j in range(len(sig_vals)):
                val = pct_mat[i, j]
                ds = ds_mat[i, j]
                txt_color = "white" if abs(val) > 0.68 * max_abs else "black"
                ax.text(
                    j,
                    i,
                    f"{val:+.2f}%\n({ds:+.1f} s)",
                    ha="center",
                    va="center",
                    fontsize=7.8,
                    color=txt_color,
                    fontweight="bold" if val < 0.0 else "normal",
                )
        ax.set_xticks(range(len(sig_vals)))
        ax.set_xticklabels([f"{int(s)}" for s in sig_vals])
        ax.set_yticks(range(len(p_vals)))
        ax.set_yticklabels([f"{p:.1f}" for p in p_vals])
        ax.set_xlabel(f"Queue noise $\\sigma_q$ [m / lane] ({scen})")
        if idx == 0:
            ax.set_ylabel(r"Arrival miss prob. $p_{\mathrm{miss}}$")
        ax.grid(False)

    if last_im is not None:
        cbar = fig.colorbar(last_im, ax=axes.tolist(), pad=0.02, shrink=0.92)
        cbar.set_label("Delay change vs. OSFI-DJ-S [%]")

    return _save_both(fig, out_dir, "noise_heatmap")


def plot_ablation_bars(exp_c_sum_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Render horizontal bar chart with 95% CI and fallback rates for Experiment C."""
    apply_academic_style()
    df = exp_c_sum_df.copy()

    short_labels = {
        "baseline_luk_smallest_abovefloor_shoulder": "Baseline OSFI-DJ-NS (Łukasiewicz,\nsmallest, above-floor, gpe_first)",
        "implicator_goguen": "Implicator: Goguen",
        "implicator_kleene_dienes": "Implicator: Kleene-Dienes",
        "tie_break_midpoint": "Tie-break: midpoint",
        "defuzz_standard_centroid": "Defuzzifier: standard centroid\n(includes 1-α floor)",
        "shoulder_edges_false": "Boundary MFs: pure Gaussian\n(shoulder_edges=False)",
        "and_operator_min": "Antecedent AND: min\n(no dead zones)",
        "mf_sigma_scale_1_5": "MF width: σ × 1.5",
        "spm_mode_preempt": "SPM: preempt\n(Stage 2 thrashing logic)",
    }
    bar_colors = [
        "#117733",
        "#D55E00",
        "#56B4E9",
        "#E69F00",
        "#0072B2",
        "#CC79A7",
        "#882255",
        "#44AA99",
        "#7F7F7F",
    ]

    y_pos = np.arange(len(df), dtype=float)
    means = df["avg_delay_s_mean"].to_numpy(dtype=float)
    cis = df["avg_delay_s_ci95"].to_numpy(dtype=float)
    fb_rates = 100.0 * df["fallback_rate_mean"].to_numpy(dtype=float)
    labels = [
        short_labels.get(str(vid), str(lbl))
        for vid, lbl in zip(df["variant_id"], df["label"])
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    bars = ax.barh(
        y_pos,
        means,
        xerr=cis,
        height=0.58,
        color=bar_colors[: len(df)],
        edgecolor="black",
        linewidth=0.6,
        alpha=0.88,
        capsize=3.2,
        error_kw={"elinewidth": 1.2},
    )

    base_mean = float(means[0])
    ax.axvline(base_mean, color="#117733", ls="--", lw=1.2, alpha=0.8)

    for idx, (bar, mean_v, ci_v, fb_v) in enumerate(zip(bars, means, cis, fb_rates)):
        fb_str = f", fb={fb_v:.1f}%" if fb_v > 0.01 else ", fb=0%"
        ax.text(
            mean_v + ci_v + 0.8,
            bar.get_y() + bar.get_height() / 2.0,
            f"{mean_v:.1f} ± {ci_v:.1f} s{fb_str}",
            va="center",
            ha="left",
            fontsize=8.0,
            bbox={"boxstyle": "square,pad=0.1", "fc": "white", "ec": "none", "alpha": 0.78},
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0.0, max(75.0, float(np.max(means + cis)) * 1.35))
    ax.set_xlabel(r"Overall average vehicle delay [s / veh] (heavy, $\sigma_q=10$ m, $p_{\mathrm{miss}}=0$)")

    return _save_both(fig, out_dir, "ablation_bars")


def generate_all_figures(
    results_root: str | Path = "results",
    figures_dir: str | Path = "results/figures",
) -> list[Path]:
    """Generate all PDF and PNG figures from saved experiment results."""
    res_path = Path(results_root)
    fig_path = Path(figures_dir)

    raw_df = pd.read_csv(res_path / "raw" / "reproduction_runs.csv")
    summary_df = pd.read_csv(res_path / "tables" / "metrics_summary_ci.csv")

    generated: list[Path] = []
    generated.extend(plot_mf_inputs_outputs(fig_path))
    generated.extend(plot_control_surfaces(fig_path, shoulder_edges=True))
    generated.extend(plot_phase_delays(summary_df, fig_path))
    generated.extend(plot_phase_exits(summary_df, fig_path))
    generated.extend(plot_overall_delay_boxplot(raw_df, fig_path))
    generated.extend(plot_timeline_example(fig_path))

    exp_b_path = res_path / "tables" / "contribution_exp_b_summary.csv"
    exp_c_path = res_path / "tables" / "contribution_exp_c_summary.csv"
    generated.extend(plot_osfi_inference_example(fig_path))
    generated.extend(plot_dead_zone_map(fig_path))
    generated.extend(plot_control_surfaces_osfi(fig_path, cache_dir=res_path / "cache"))
    if exp_b_path.exists():
        exp_b_df = pd.read_csv(exp_b_path)
        generated.extend(plot_noise_degradation(exp_b_df, fig_path))
        generated.extend(plot_noise_degradation_relative(exp_b_df, fig_path))
        generated.extend(plot_noise_heatmap(exp_b_df, fig_path))
    if exp_c_path.exists():
        exp_c_df = pd.read_csv(exp_c_path)
        generated.extend(plot_ablation_bars(exp_c_df, fig_path))

    return generated

