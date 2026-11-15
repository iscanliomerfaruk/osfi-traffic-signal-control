"""CLI live demo for inspecting two-stage fuzzy inference (FC1, FC2) and SPM decisions."""

from __future__ import annotations

import argparse
from typing import Any

from osfi_tsc.fuzzy.membership import (
    ARRIVAL_CENTERS,
    EXTENSION_PEAKS,
    EXTENSION_TRIANGLES,
    QUEUE_CENTERS,
    arrival_rate_memberships,
    extension_input_memberships,
    queue_length_memberships,
)
from osfi_tsc.fuzzy.operators import tnorm_lukasiewicz, tnorm_min
from osfi_tsc.fuzzy.rules import FC1_RULES, FC2_RULES, FuzzyRule
from osfi_tsc.inference import (
    CRIInference,
    MamdaniInference,
    OSFIDJInference,
    OSFILiteralInference,
    SugenoInference,
)
from osfi_tsc.sim import APPROACHES, compute_matched_input_sigmas

ALL_ENGINE_NAMES: tuple[str, ...] = (
    "Mamdani",
    "Sugeno",
    "OSFI-literal",
    "OSFI-DJ-S",
    "CRI-S",
    "OSFI-DJ-NS",
    "CRI-NS",
)


def _format_fuzzification_row(name: str, val: float, unit: str, mfs: dict[str, Any]) -> str:
    terms_str = " | ".join(f"{k}: {float(v):.4f}" for k, v in mfs.items())
    return f"  {name:<22s} = {val:6.2f} {unit:<9s} ->  {terms_str}"


def _top_fired_rules(
    m1: dict[str, Any],
    m2: dict[str, Any],
    rules: tuple[FuzzyRule, ...],
    and_op: str,
    top_k: int = 5,
) -> list[tuple[FuzzyRule, float, float, float]]:
    scored: list[tuple[FuzzyRule, float, float, float]] = []
    for r in rules:
        a1 = float(m1[r.antecedent1])
        is_wildcard = r.antecedent2 is None or r.antecedent2 == "ANY"
        a2 = 1.0 if is_wildcard else float(m2[r.antecedent2])
        if is_wildcard:
            alpha = a1
        elif and_op == "min":
            alpha = float(tnorm_min(a1, a2))
        else:
            alpha = float(tnorm_lukasiewicz(a1, a2))
        scored.append((r, a1, a2, alpha))
    scored.sort(key=lambda item: (item[3], min(item[1], item[2])), reverse=True)
    return scored[:top_k]


def _select_nps_next_phase(queues_m: dict[str, float], current_phase: str = "E") -> str:
    candidates = [app for app in APPROACHES if app != current_phase]
    max_q = max(queues_m[app] for app in candidates)
    for app in candidates:
        if abs(queues_m[app] - max_q) <= 1e-9:
            return app
    return candidates[0]


def _spm_decision_line(
    ext2: float,
    q_cur: float,
    queues_m: dict[str, float],
    current_phase: str = "E",
    green_elapsed: int = 7,
    g_max: int = 60,
) -> str:
    other_max = max(queues_m[a] for a in APPROACHES if a != current_phase)
    if other_max <= 1e-9:
        return f"stay on {current_phase} (re-evaluate in 1 s; no competing queue)"
    if ext2 >= 1.0 and q_cur > 1e-9 and green_elapsed < g_max:
        ext_s = int(round(ext2))
        return f"extend {ext_s} s (on phase {current_phase})"
    next_p = _select_nps_next_phase(queues_m, current_phase=current_phase)
    return f"switch to {next_p} (q_{next_p}={queues_m[next_p]:.1f} m)"


def build_demo_engines(
    selected_names: list[str],
    sigma_q: float,
) -> dict[str, tuple[Any, str]]:
    """Instantiate requested inference engines with direct inference for live inspection."""
    sig_lam, sig_q = compute_matched_input_sigmas(sigma_q=sigma_q, p_miss=0.0)
    out: dict[str, tuple[Any, str]] = {}
    for name in selected_names:
        if name == "Mamdani":
            out[name] = (MamdaniInference(shoulder_edges=True), "min")
        elif name == "Sugeno":
            out[name] = (SugenoInference(shoulder_edges=True), "min")
        elif name == "OSFI-literal":
            out[name] = (OSFILiteralInference(shoulder_edges=True), "lukasiewicz")
        elif name == "OSFI-DJ-S":
            out[name] = (
                OSFIDJInference(
                    sigma_lambda=0.0,
                    sigma_queue=0.0,
                    use_lut=False,
                ),
                "lukasiewicz",
            )
        elif name == "CRI-S":
            out[name] = (
                CRIInference(
                    sigma_lambda=0.0,
                    sigma_queue=0.0,
                    use_lut=False,
                ),
                "lukasiewicz",
            )
        elif name == "OSFI-DJ-NS":
            out[name] = (
                OSFIDJInference(
                    sigma_lambda=sig_lam,
                    sigma_queue=sig_q,
                    use_lut=False,
                ),
                "lukasiewicz",
            )
        elif name == "CRI-NS":
            out[name] = (
                CRIInference(
                    sigma_lambda=sig_lam,
                    sigma_queue=sig_q,
                    use_lut=False,
                ),
                "lukasiewicz",
            )
        else:
            raise ValueError(f"Unknown engine '{name}'. Choices: {ALL_ENGINE_NAMES}")
    return out


def run_demo_inference(
    lam: float,
    q: float,
    qo: float,
    sigma_q: float = 10.0,
    engines_arg: str = "all",
    queues_arg: str | None = None,
) -> str:
    """Execute live inference across engines and return formatted console report."""
    if engines_arg.strip().lower() == "all":
        selected = list(ALL_ENGINE_NAMES)
    else:
        selected = [e.strip() for e in engines_arg.split(",") if e.strip()]

    if queues_arg is not None:
        parts = [float(x.strip()) for x in queues_arg.split(",")]
        if len(parts) != 4:
            raise ValueError("--queues must provide 4 comma-separated values: E,S,W,N")
        queues_m = {app: parts[idx] for idx, app in enumerate(APPROACHES)}
        q = float(queues_m["E"])
        qo = float(max(queues_m["S"], queues_m["W"], queues_m["N"]))
    else:
        queues_m = {
            "E": float(q),
            "S": float(qo),
            "W": round(float(qo) * 0.6, 2),
            "N": round(float(qo) * 0.4, 2),
        }

    m_lam = arrival_rate_memberships(lam, shoulder_edges=True)
    m_q = queue_length_memberships(q, shoulder_edges=True)
    m_qo = queue_length_memberships(qo, shoulder_edges=True)

    mamdani_ref = MamdaniInference(shoulder_edges=True)
    ext1_ref = mamdani_ref.infer_fc1(lam, q)
    m_ext1_ref = extension_input_memberships(ext1_ref, shoulder_edges=True)

    lines: list[str] = [
        "=" * 94,
        "OSFI-TSC LIVE FUZZY INFERENCE & SPM DECISION INSPECTOR",
        "=" * 94,
        f"Inputs: lambda={lam:.2f} veh/10s | q_cur={q:.2f} m/lane | q_others_max={qo:.2f} m/lane | sigma_q={sigma_q:.2f} m",
        f"Approach Queues [m/lane] (Active Phase = E): E={queues_m['E']:.1f}, S={queues_m['S']:.1f}, W={queues_m['W']:.1f}, N={queues_m['N']:.1f}",
        "-" * 94,
        "1. INPUT FUZZIFICATION TABLE (Membership Degrees in Linguistic Sets)",
        "-" * 94,
        _format_fuzzification_row("Arrival rate (lambda)", lam, "veh/10s", m_lam),
        _format_fuzzification_row("Current queue (q)", q, "m/lane", m_q),
        _format_fuzzification_row("Competing queue (q')", qo, "m/lane", m_qo),
        _format_fuzzification_row("Extension1 (Mamdani)", ext1_ref, "s", m_ext1_ref),
        "-" * 94,
        "2. TOP-5 FIRED RULES PER ANTECEDENT AND OPERATOR (min vs. Lukasiewicz)",
        "-" * 94,
    ]

    for and_label, and_key in (
        ("Godel / Zadeh T-norm: min(a, b) [Mamdani, Sugeno]", "min"),
        ("Lukasiewicz T-norm: max(0, a + b - 1) [OSFI-literal, OSFI-DJ, CRI]", "lukasiewicz"),
    ):
        lines.append(f"  [{and_label}]")
        top_fc1 = _top_fired_rules(m_lam, m_q, FC1_RULES, and_op=and_key, top_k=5)
        max_a1 = max(item[3] for item in top_fc1)
        dz_fc1 = " (DEAD ZONE: max alpha < 1e-6 -> nearest-rule fallback)" if max_a1 < 1e-6 else ""
        lines.append(f"    FC1 Top-5 Rules{dz_fc1}:")
        for r, a1, a2, alpha in top_fc1:
            peak_v = EXTENSION_PEAKS[r.consequent]
            lines.append(
                f"      Rule {r.rule_id:2d}: IF lam={r.antecedent1:<2s} ({a1:.3f}) AND q={r.antecedent2:<2s} ({a2:.3f}) "
                f"THEN Ext1={r.consequent:<2s} (peak={peak_v:4.1f}s) | alpha = {alpha:.4f}"
            )

        top_fc2 = _top_fired_rules(m_ext1_ref, m_qo, FC2_RULES, and_op=and_key, top_k=5)
        max_a2 = max(item[3] for item in top_fc2)
        dz_fc2 = " (DEAD ZONE: max alpha < 1e-6 -> nearest-rule fallback)" if max_a2 < 1e-6 else ""
        lines.append(f"    FC2 Top-5 Rules (at Ext1={ext1_ref:.2f}s){dz_fc2}:")
        for r, a1, a2, alpha in top_fc2:
            ant2_lbl = r.antecedent2 if r.antecedent2 is not None else "ANY"
            peak_v = EXTENSION_PEAKS[r.consequent]
            lines.append(
                f"      Rule {r.rule_id:2d}: IF Ext1={r.antecedent1:<2s} ({a1:.3f}) AND q'={ant2_lbl:<3s} ({a2:.3f}) "
                f"THEN Ext2={r.consequent:<2s} (peak={peak_v:4.1f}s) | alpha = {alpha:.4f}"
            )
        lines.append("")

    lines.extend(
        [
            "-" * 94,
            "3. TWO-STAGE GPE OUTPUTS, DEAD-ZONE FALLBACKS & SPM DECISIONS PER ENGINE",
            "-" * 94,
            f"  {'Engine':<14s} | {'AND':<11s} | {'Ext1 [s]':>9s} | {'Ext2 [s]':>9s} | {'Fallback (FC1/FC2)':<18s} | {'SPM Decision (gpe_first)'}",
            "  " + "-" * 90,
        ]
    )

    engines = build_demo_engines(selected, sigma_q=sigma_q)
    for eng_name, (eng, and_op) in engines.items():
        if hasattr(eng, "reset_stats"):
            eng.reset_stats()
        ext1, ext2 = eng.infer_gpe(lam, q, qo)
        fb_fc1 = bool(getattr(eng, "fc1_fallbacks", 0) > 0)
        fb_fc2 = bool(getattr(eng, "fc2_fallbacks", 0) > 0)
        if fb_fc1 or fb_fc2:
            fb_str = f"YES ({'FC1' if fb_fc1 else '-'}/{'FC2' if fb_fc2 else '-'})"
        else:
            fb_str = "No  (0 / 0)"
        spm_str = _spm_decision_line(ext2=ext2, q_cur=q, queues_m=queues_m, current_phase="E")
        lines.append(
            f"  {eng_name:<14s} | {and_op:<11s} | {ext1:9.3f} | {ext2:9.3f} | {fb_str:<18s} | {spm_str}"
        )

    lines.append("=" * 94)
    report = "\n".join(lines)
    print(report)
    return report


def main() -> None:
    """Parse CLI arguments and run the live inference inspector."""
    parser = argparse.ArgumentParser(
        description="Inspect fuzzification, rule firing strengths, Extension1/2, and SPM decision."
    )
    parser.add_argument("--lam", type=float, default=3.2, help="Arrival rate lambda [veh / 10 s].")
    parser.add_argument("--q", type=float, default=18.0, help="Current phase queue length [m / lane].")
    parser.add_argument("--qo", type=float, default=30.0, help="Max competing queue length [m / lane].")
    parser.add_argument("--sigma-q", type=float, default=10.0, help="Queue sensor noise std [m / lane].")
    parser.add_argument(
        "--engines",
        type=str,
        default="all",
        help="Comma-separated list of engines or 'all'.",
    )
    parser.add_argument(
        "--queues",
        type=str,
        default=None,
        help="Optional comma-separated approach queues E,S,W,N [m/lane].",
    )
    args = parser.parse_args()

    run_demo_inference(
        lam=args.lam,
        q=args.q,
        qo=args.qo,
        sigma_q=args.sigma_q,
        engines_arg=args.engines,
        queues_arg=args.queues,
    )


if __name__ == "__main__":
    main()
