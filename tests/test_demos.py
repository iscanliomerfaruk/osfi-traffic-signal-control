"""Headless smoke tests for the three live-demo scripts."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import matplotlib

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str) -> ModuleType:
    path = REPO_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"demo_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_demo_inference_prints_tables_and_detects_dead_zone() -> None:
    demo = _load_script("demo_inference")
    normal = demo.run_demo_inference(
        lam=3.2, q=18.0, qo=30.0, sigma_q=10.0, engines_arg="all", queues_arg=None
    )
    assert "FUZZIFICATION" in normal
    assert "OSFI-DJ-NS" in normal and "Mamdani" in normal
    assert "extend" in normal or "switch" in normal
    dead = demo.run_demo_inference(
        lam=4.5, q=22.5, qo=22.5, sigma_q=10.0, engines_arg="all", queues_arg=None
    )
    assert "DEAD ZONE" in dead
    assert "YES (FC1" in dead


def test_demo_gui_builds_all_engines_headless(tmp_path: Path) -> None:
    demo = _load_script("demo_gui")
    gui = demo.OSFIInteractiveGUI(lam=4.5, q=22.5, qo=22.5, sigma_q=10.0, engine_name="Mamdani")
    for engine in demo.GUI_ENGINES:
        gui.engine_name = engine
        res = gui.redraw()
        assert 0.0 <= res["ext1"] <= 25.0
        assert 0.0 <= res["ext2"] <= 25.0
    out = tmp_path / "gui.png"
    gui.fig.savefig(out)
    assert out.stat().st_size > 0
    matplotlib.pyplot.close(gui.fig)


def test_demo_sim_runs_and_saves_outputs(tmp_path: Path) -> None:
    demo = _load_script("demo_sim")
    cwd = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        out = tmp_path / "timeline.png"
        demo.main(
            [
                "--scenario",
                "moderate",
                "--controllers",
                "Mamdani,Webster",
                "--seed",
                "3",
                "--animate",
                "--headless",
                "--out",
                str(out),
            ]
        )
    finally:
        os.chdir(cwd)
    assert out.exists()
    assert (tmp_path / "demo_sim_anim_frame.png").exists()
