"""Interactive Matplotlib GUI for live two-stage fuzzy inference exploration."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import matplotlib

if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import RadioButtons, Slider

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from osfi_tsc.fuzzy.membership import (
    arrival_rate_memberships,
    extension_input_memberships,
    extension_output_memberships,
    queue_length_memberships,
)
from osfi_tsc.fuzzy.operators import tnorm_lukasiewicz, tnorm_min
from osfi_tsc.fuzzy.rules import FC1_RULES, FC2_RULES
from osfi_tsc.inference import (
    CRIInference,
    MamdaniInference,
    OSFIDJInference,
    OSFILiteralInference,
    SugenoInference,
)
from osfi_tsc.sim import compute_matched_input_sigmas

GUI_ENGINES: tuple[str, ...] = (
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "OSFI-DJ-S",
    "OSFI-DJ-NS",
    "CRI-NS",
)

LAM_TERMS: tuple[str, ...] = ("Z", "Lo", "M", "H")
QUEUE_TERMS: tuple[str, ...] = ("Sh", "M", "L", "VL")
EXT_TERMS: tuple[str, ...] = ("Z", "Sh", "M", "L")


def compute_fc1_firing_matrix(
    lam: float,
    q: float,
    and_op: str = "lukasiewicz",
) -> tuple[np.ndarray, list[list[str]]]:
    """Compute 4x4 firing strength matrix and consequent labels for FC1."""
    m_lam = arrival_rate_memberships(lam, shoulder_edges=True)
    m_q = queue_length_memberships(q, shoulder_edges=True)
    mat = np.zeros((4, 4), dtype=float)
    labels: list[list[str]] = [["" for _ in range(4)] for _ in range(4)]

    rule_map = {(r.antecedent1, r.antecedent2): r for r in FC1_RULES}
    for i, t_lam in enumerate(LAM_TERMS):
        for j, t_q in enumerate(QUEUE_TERMS):
            r = rule_map[(t_lam, t_q)]
            a1 = float(m_lam[t_lam])
            a2 = float(m_q[t_q])
            if and_op == "min":
                alpha = float(tnorm_min(a1, a2))
            else:
                alpha = float(tnorm_lukasiewicz(a1, a2))
            mat[i, j] = alpha
            labels[i][j] = f"R{r.rule_id}: {r.consequent}\n({alpha:.2f})"
    return mat, labels


def compute_stage_output_curve(
    engine_name: str,
    lam: float,
    q: float,
    qo: float,
    sigma_q: float,
) -> dict[str, Any]:
    """Evaluate direct FC1 and FC2 output sets and centroids for the selected engine."""
    y_grid = np.linspace(0.0, 25.0, 126)
    term_curves = extension_output_memberships(y_grid)

    if engine_name == "Mamdani":
        eng = MamdaniInference(shoulder_edges=True)
        m_lam = arrival_rate_memberships(lam, shoulder_edges=True)
        m_q = queue_length_memberships(q, shoulder_edges=True)
        b_fc1 = np.zeros_like(y_grid)
        for r in FC1_RULES:
            alpha = float(tnorm_min(m_lam[r.antecedent1], m_q[r.antecedent2]))
            b_fc1 = np.maximum(b_fc1, np.minimum(alpha, np.asarray(term_curves[r.consequent], dtype=float)))
        ext1, ext2 = eng.infer_gpe(lam, q, qo)
        m_ext1 = extension_input_memberships(ext1, shoulder_edges=True)
        m_qo = queue_length_memberships(qo, shoulder_edges=True)
        b_fc2 = np.zeros_like(y_grid)
        for r in FC2_RULES:
            is_wild = r.antecedent2 is None or r.antecedent2 == "ANY"
            alpha = (
                float(m_ext1[r.antecedent1])
                if is_wild
                else float(tnorm_min(m_ext1[r.antecedent1], m_qo[r.antecedent2]))
            )
            b_fc2 = np.maximum(b_fc2, np.minimum(alpha, np.asarray(term_curves[r.consequent], dtype=float)))
        return {
            "y_grid": y_grid,
            "b_fc1": b_fc1,
            "b_fc1_eff": b_fc1,
            "ext1": ext1,
            "b_fc2": b_fc2,
            "b_fc2_eff": b_fc2,
            "ext2": ext2,
            "and_op": "min",
            "fallback_fc1": False,
            "fallback_fc2": False,
        }

    if engine_name in ("Sugeno", "OSFI-literal"):
        and_op = "min" if engine_name == "Sugeno" else "lukasiewicz"
        eng = (
            SugenoInference(shoulder_edges=True)
            if engine_name == "Sugeno"
            else OSFILiteralInference(shoulder_edges=True)
        )
        if hasattr(eng, "reset_stats"):
            eng.reset_stats()
        ext1, ext2 = eng.infer_gpe(lam, q, qo)
        m_lam = arrival_rate_memberships(lam, shoulder_edges=True)
        m_q = queue_length_memberships(q, shoulder_edges=True)
        b_fc1 = np.zeros_like(y_grid)
        for r in FC1_RULES:
            a1 = float(m_lam[r.antecedent1])
            a2 = float(m_q[r.antecedent2])
            alpha = float(tnorm_min(a1, a2)) if and_op == "min" else float(tnorm_lukasiewicz(a1, a2))
            b_fc1 = np.maximum(b_fc1, alpha * np.asarray(term_curves[r.consequent], dtype=float))

        m_ext1 = extension_input_memberships(ext1, shoulder_edges=True)
        m_qo = queue_length_memberships(qo, shoulder_edges=True)
        b_fc2 = np.zeros_like(y_grid)
        for r in FC2_RULES:
            is_wild = r.antecedent2 is None or r.antecedent2 == "ANY"
            a1 = float(m_ext1[r.antecedent1])
            a2 = 1.0 if is_wild else float(m_qo[r.antecedent2])
            if is_wild:
                alpha = a1
            elif and_op == "min":
                alpha = float(tnorm_min(a1, a2))
            else:
                alpha = float(tnorm_lukasiewicz(a1, a2))
            b_fc2 = np.maximum(b_fc2, alpha * np.asarray(term_curves[r.consequent], dtype=float))

        return {
            "y_grid": y_grid,
            "b_fc1": b_fc1,
            "b_fc1_eff": b_fc1,
            "ext1": ext1,
            "b_fc2": b_fc2,
            "b_fc2_eff": b_fc2,
            "ext2": ext2,
            "and_op": and_op,
            "fallback_fc1": bool(getattr(eng, "fc1_fallbacks", 0) > 0),
            "fallback_fc2": bool(getattr(eng, "fc2_fallbacks", 0) > 0),
        }

    is_ns = engine_name.endswith("-NS")
    s_lam, s_q = compute_matched_input_sigmas(sigma_q=sigma_q, p_miss=0.0) if is_ns else (0.0, 0.0)
    if engine_name.startswith("OSFI-DJ"):
        eng_dj = OSFIDJInference(
            sigma_lambda=s_lam,
            sigma_queue=s_q,
            use_lut=False,
        )
        b_fc1 = eng_dj.fc1_engine.infer_aggregated_set(lam, q)
        ext1, fb1 = eng_dj.fc1_engine.infer_direct_with_flag(lam, q)
        b_fc2 = eng_dj.fc2_engine.infer_aggregated_set(ext1, qo)
        ext2, fb2 = eng_dj.fc2_engine.infer_direct_with_flag(ext1, qo)
    else:
        eng_cri = CRIInference(
            sigma_lambda=s_lam,
            sigma_queue=s_q,
            use_lut=False,
        )
        b_fc1 = eng_cri.fc1_engine.infer_aggregated_set(lam, q)
        ext1, fb1 = eng_cri.fc1_engine.infer_direct_with_flag(lam, q)
        b_fc2 = eng_cri.fc2_engine.infer_aggregated_set(ext1, qo)
        ext2, fb2 = eng_cri.fc2_engine.infer_direct_with_flag(ext1, qo)

    b_fc1_eff = np.maximum(0.0, b_fc1 - float(np.min(b_fc1)))
    b_fc2_eff = np.maximum(0.0, b_fc2 - float(np.min(b_fc2)))
    return {
        "y_grid": y_grid,
        "b_fc1": b_fc1,
        "b_fc1_eff": b_fc1_eff,
        "ext1": ext1,
        "b_fc2": b_fc2,
        "b_fc2_eff": b_fc2_eff,
        "ext2": ext2,
        "and_op": "lukasiewicz",
        "fallback_fc1": fb1,
        "fallback_fc2": fb2,
    }


class OSFIInteractiveGUI:
    """Interactive 4-panel Matplotlib dashboard for two-stage fuzzy inference."""

    def __init__(
        self,
        lam: float = 3.2,
        q: float = 18.0,
        qo: float = 30.0,
        sigma_q: float = 10.0,
        engine_name: str = "OSFI-DJ-NS",
    ) -> None:
        self.lam = float(lam)
        self.q = float(q)
        self.qo = float(qo)
        self.sigma_q = float(sigma_q)
        self.engine_name = engine_name if engine_name in GUI_ENGINES else "OSFI-DJ-NS"

        self.fig = plt.figure(figsize=(14, 8.5))
        self.fig.subplots_adjust(left=0.22, right=0.97, top=0.92, bottom=0.24, wspace=0.28, hspace=0.36)

        self.ax_mf = self.fig.add_subplot(2, 2, 1)
        self.ax_heat = self.fig.add_subplot(2, 2, 2)
        self.ax_fc1 = self.fig.add_subplot(2, 2, 3)
        self.ax_fc2 = self.fig.add_subplot(2, 2, 4)

        ax_radio = self.fig.add_axes([0.02, 0.42, 0.15, 0.42])
        ax_radio.set_title("Inference Engine", fontsize=10, fontweight="bold")
        active_idx = GUI_ENGINES.index(self.engine_name)
        self.radio = RadioButtons(ax_radio, GUI_ENGINES, active=active_idx)

        ax_s_lam = self.fig.add_axes([0.22, 0.14, 0.68, 0.025])
        ax_s_q = self.fig.add_axes([0.22, 0.10, 0.68, 0.025])
        ax_s_qo = self.fig.add_axes([0.22, 0.06, 0.68, 0.025])
        ax_s_sig = self.fig.add_axes([0.22, 0.02, 0.68, 0.025])

        self.s_lam = Slider(ax_s_lam, "λ [veh/10s]", 0.0, 12.0, valinit=self.lam, valstep=0.1)
        self.s_q = Slider(ax_s_q, "q [m/lane]", 0.0, 60.0, valinit=self.q, valstep=0.5)
        self.s_qo = Slider(ax_s_qo, "q' [m/lane]", 0.0, 60.0, valinit=self.qo, valstep=0.5)
        self.s_sig = Slider(ax_s_sig, "σ_q [m]", 0.0, 15.0, valinit=self.sigma_q, valstep=0.5)

        self.s_lam.on_changed(self._on_slider_change)
        self.s_q.on_changed(self._on_slider_change)
        self.s_qo.on_changed(self._on_slider_change)
        self.s_sig.on_changed(self._on_slider_change)
        self.radio.on_clicked(self._on_radio_change)

        self.redraw()

    def _on_slider_change(self, _val: float) -> None:
        self.lam = float(self.s_lam.val)
        self.q = float(self.s_q.val)
        self.qo = float(self.s_qo.val)
        self.sigma_q = float(self.s_sig.val)
        self.redraw()

    def _on_radio_change(self, label: str | None) -> None:
        if label is not None:
            self.engine_name = str(label)
            self.redraw()

    def redraw(self) -> dict[str, Any]:
        """Update all four panels using direct inference."""
        res = compute_stage_output_curve(
            engine_name=self.engine_name,
            lam=self.lam,
            q=self.q,
            qo=self.qo,
            sigma_q=self.sigma_q,
        )

        self.ax_mf.clear()
        x_q = np.linspace(0.0, 60.0, 241)
        q_mfs = queue_length_memberships(x_q, shoulder_edges=True)
        for term, curve in q_mfs.items():
            self.ax_mf.plot(x_q, curve, lw=1.6, label=f"Queue {term}")
        self.ax_mf.axvline(self.q, color="#0072B2", ls="--", lw=1.8, label=f"q={self.q:.1f} m")
        self.ax_mf.axvline(self.qo, color="#D55E00", ls=":", lw=1.8, label=f"q'={self.qo:.1f} m")
        if self.engine_name.endswith("-NS") and self.sigma_q > 0.0:
            ns_curve = np.exp(-0.5 * ((x_q - self.q) / self.sigma_q) ** 2)
            self.ax_mf.fill_between(
                x_q, 0.0, ns_curve, color="#0072B2", alpha=0.18, label=f"A*(q), σ_q={self.sigma_q:.1f}m"
            )
        self.ax_mf.set_title(
            f"(a) Queue MFs & Inputs (λ={self.lam:.1f} veh/10s, q={self.q:.1f} m, q'={self.qo:.1f} m)",
            fontsize=10,
            fontweight="bold",
        )
        self.ax_mf.set_xlabel("Queue length [m/lane]")
        self.ax_mf.set_ylabel("Membership degree")
        self.ax_mf.set_ylim(-0.02, 1.05)
        self.ax_mf.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.6)
        self.ax_mf.grid(True, alpha=0.25)

        self.ax_heat.clear()
        mat, labels = compute_fc1_firing_matrix(self.lam, self.q, and_op=res["and_op"])
        self.ax_heat.imshow(mat, cmap="YlOrRd", vmin=0.0, vmax=1.0, aspect="auto")
        self.ax_heat.set_xticks(range(4))
        self.ax_heat.set_xticklabels(QUEUE_TERMS)
        self.ax_heat.set_yticks(range(4))
        self.ax_heat.set_yticklabels(LAM_TERMS)
        self.ax_heat.set_xlabel("Current Queue Set (q)")
        self.ax_heat.set_ylabel("Arrival Rate Set (λ)")
        dz_tag = " [DEAD ZONE -> Fallback]" if res["fallback_fc1"] else ""
        self.ax_heat.set_title(
            f"(b) FC1 Firing Heatmap ({res['and_op']}){dz_tag}",
            fontsize=10,
            fontweight="bold",
        )
        for i in range(4):
            for j in range(4):
                txt_col = "white" if mat[i, j] > 0.55 else "black"
                self.ax_heat.text(
                    j,
                    i,
                    labels[i][j],
                    ha="center",
                    va="center",
                    color=txt_col,
                    fontsize=7.5,
                    fontweight="bold" if mat[i, j] > 0.01 else "normal",
                )

        y_grid = res["y_grid"]
        ext_mfs = extension_output_memberships(y_grid)

        self.ax_fc1.clear()
        for term, curve in ext_mfs.items():
            self.ax_fc1.plot(y_grid, curve, lw=1.0, ls="--", alpha=0.45, label=f"Set {term}")
        self.ax_fc1.plot(y_grid, res["b_fc1"], color="#333333", lw=1.4, label="Aggregated B*(y)")
        self.ax_fc1.fill_between(
            y_grid,
            0.0,
            res["b_fc1_eff"],
            color="#0072B2",
            alpha=0.35,
            label="Effective B*(y) - floor",
        )
        self.ax_fc1.axvline(
            res["ext1"],
            color="#D55E00",
            lw=2.2,
            label=f"Ext1 = {res['ext1']:.2f} s",
        )
        self.ax_fc1.set_title(
            f"(c) FC1 Output Set & Centroid (Ext1 = {res['ext1']:.2f} s"
            + (", empty set -> nearest-rule fallback)" if res["fallback_fc1"] else ")"),
            fontsize=10,
            fontweight="bold",
        )
        self.ax_fc1.set_xlabel("Extension1 [s]")
        self.ax_fc1.set_ylabel("Membership")
        self.ax_fc1.set_ylim(-0.02, 1.05)
        self.ax_fc1.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.6)
        self.ax_fc1.grid(True, alpha=0.25)

        self.ax_fc2.clear()
        for term, curve in ext_mfs.items():
            self.ax_fc2.plot(y_grid, curve, lw=1.0, ls="--", alpha=0.45, label=f"Set {term}")
        self.ax_fc2.plot(y_grid, res["b_fc2"], color="#333333", lw=1.4, label="Aggregated B*(y)")
        self.ax_fc2.fill_between(
            y_grid,
            0.0,
            res["b_fc2_eff"],
            color="#009E73",
            alpha=0.35,
            label="Effective B*(y) - floor",
        )
        self.ax_fc2.axvline(
            res["ext2"],
            color="#CC79A7",
            lw=2.2,
            label=f"Ext2 = {res['ext2']:.2f} s",
        )
        spm_txt = (
            f"Extend +{int(round(res['ext2']))} s"
            if res["ext2"] >= 1.0 or self.qo <= self.q
            else "Switch Phase"
        )
        self.ax_fc2.set_title(
            f"(d) FC2 Output Set (Ext2 = {res['ext2']:.2f} s -> {spm_txt})",
            fontsize=10,
            fontweight="bold",
        )
        self.ax_fc2.set_xlabel("Extension2 [s]")
        self.ax_fc2.set_ylabel("Membership")
        self.ax_fc2.set_ylim(-0.02, 1.05)
        self.ax_fc2.legend(loc="upper right", fontsize=7, ncol=2, framealpha=0.6)
        self.ax_fc2.grid(True, alpha=0.25)

        self.fig.suptitle(
            f"OSFI-TSC Interactive Inference Explorer — Engine: {self.engine_name} "
            f"(Ext1={res['ext1']:.2f}s, Ext2={res['ext2']:.2f}s, SPM: {spm_txt})",
            fontsize=12,
            fontweight="bold",
        )
        self.fig.canvas.draw_idle()
        return res


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive Matplotlib GUI for live two-stage fuzzy inference exploration."
    )
    parser.add_argument("--lam", type=float, default=3.2, help="Initial arrival rate [veh/10s].")
    parser.add_argument("--q", type=float, default=18.0, help="Initial current queue [m/lane].")
    parser.add_argument("--qo", type=float, default=30.0, help="Initial competing queue [m/lane].")
    parser.add_argument("--sigma-q", type=float, default=10.0, help="Initial queue uncertainty sigma_q [m].")
    parser.add_argument("--engine", type=str, default="OSFI-DJ-NS", help="Initial engine selection.")
    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Optional path to save a snapshot of the GUI figure and exit.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headlessly without opening a window (useful for CI/smoke tests).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    gui = OSFIInteractiveGUI(
        lam=args.lam,
        q=args.q,
        qo=args.qo,
        sigma_q=args.sigma_q,
        engine_name=args.engine,
    )
    if args.save:
        out_path = Path(args.save)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        gui.fig.savefig(out_path, dpi=200)
        print(f"Saved GUI snapshot to {out_path}")
    if not args.headless and not args.save and matplotlib.get_backend().lower() != "agg":
        plt.show()
    else:
        plt.close(gui.fig)


if __name__ == "__main__":
    main()
