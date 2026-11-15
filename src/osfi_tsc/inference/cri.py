"""Compositional Rule of Inference (CRI) engine with singleton and non-singleton inputs."""

from __future__ import annotations

import hashlib
import json
from multiprocessing import Pool, cpu_count
from pathlib import Path
import time
from typing import Any, Callable
import numpy as np

from osfi_tsc.fuzzy.membership import (
    ARRIVAL_UNIVERSE,
    EXTENSION_UNIVERSE,
    QUEUE_UNIVERSE,
    arrival_rate_memberships,
    clip_to_universe,
    extension_input_memberships,
    extension_output_memberships,
    gaussian_mf,
    queue_length_memberships,
)
from osfi_tsc.fuzzy.operators import (
    defuzz_centroid,
    implicator_goguen,
    implicator_kleene_dienes,
    implicator_lukasiewicz,
    implicator_mamdani,
    implicator_zadeh,
    tnorm_lukasiewicz,
    tnorm_min,
)
from osfi_tsc.fuzzy.rules import FC1_RULES, FC2_RULES, FuzzyRule

IMPLICATOR_MAP: dict[str, Callable[[ Any, Any], Any]] = {
    "lukasiewicz": implicator_lukasiewicz,
    "goguen": implicator_goguen,
    "kleene_dienes": implicator_kleene_dienes,
    "zadeh": implicator_zadeh,
    "mamdani": implicator_mamdani,
}


def d1_similarity(r1: np.ndarray, r2: np.ndarray) -> float:
    """Compute normalized L1 (d1) similarity 1 - mean(|r1 - r2|) in [0, 1]."""
    a1 = np.asarray(r1, dtype=float)
    a2 = np.asarray(r2, dtype=float)
    return float(1.0 - np.mean(np.abs(a1 - a2)))


def build_marginal_input_mf(
    grid: np.ndarray,
    val: float,
    sigma: float,
    bilinear_singleton: bool = False,
) -> np.ndarray:
    """Construct 1D input fuzzy set A*_k on grid (singleton if sigma <= 0 else Gaussian)."""
    clipped = float(np.clip(val, float(grid[0]), float(grid[-1])))
    if sigma <= 1e-12:
        out = np.zeros_like(grid, dtype=float)
        if not bilinear_singleton:
            idx = int(np.argmin(np.abs(grid - clipped)))
            out[idx] = 1.0
            return out
        right_idx = int(np.searchsorted(grid, clipped, side="right"))
        if right_idx <= 0:
            out[0] = 1.0
        elif right_idx >= len(grid):
            out[-1] = 1.0
        else:
            left_idx = right_idx - 1
            x_l = float(grid[left_idx])
            x_r = float(grid[right_idx])
            w_r = (clipped - x_l) / max(1e-12, x_r - x_l)
            out[left_idx] = 1.0 - w_r
            out[right_idx] = w_r
        return out

    mf = np.asarray(gaussian_mf(grid, center=clipped, sigma=sigma), dtype=float)
    if float(np.max(mf)) <= 1e-3:
        out = np.zeros_like(grid, dtype=float)
        idx = int(np.argmin(np.abs(grid - clipped)))
        out[idx] = 1.0
        return out
    return mf


def defuzzify_set(
    y_grid: np.ndarray,
    b_agg: np.ndarray,
    method: str = "centroid_above_floor",
) -> tuple[float, bool]:
    """Defuzzify aggregated output set B*(y) and return (crisp_value, used_fallback)."""
    if method == "centroid_above_floor":
        floor_val = float(np.min(b_agg))
        eff = np.maximum(0.0, b_agg - floor_val)
    elif method == "centroid":
        eff = np.maximum(0.0, b_agg)
    else:
        raise ValueError(f"Unknown defuzzification method: {method}")

    area = float(np.sum(eff))
    if area <= 1e-12:
        return 0.0, True
    return defuzz_centroid(y_grid, eff), False


def bilinear_interpolate_2d(
    x1_grid: np.ndarray,
    x2_grid: np.ndarray,
    table: np.ndarray,
    x1: float,
    x2: float,
) -> float:
    """Perform 2D bilinear interpolation on a precomputed regular grid table."""
    c1 = float(np.clip(x1, float(x1_grid[0]), float(x1_grid[-1])))
    c2 = float(np.clip(x2, float(x2_grid[0]), float(x2_grid[-1])))

    dx1 = float(x1_grid[1] - x1_grid[0])
    dx2 = float(x2_grid[1] - x2_grid[0])

    pos1 = (c1 - float(x1_grid[0])) / dx1
    pos2 = (c2 - float(x2_grid[0])) / dx2

    i0 = int(np.clip(np.floor(pos1), 0, len(x1_grid) - 2))
    j0 = int(np.clip(np.floor(pos2), 0, len(x2_grid) - 2))
    i1 = i0 + 1
    j1 = j0 + 1

    u = float(np.clip(pos1 - float(i0), 0.0, 1.0))
    v = float(np.clip(pos2 - float(j0), 0.0, 1.0))

    v00 = float(table[i0, j0])
    v10 = float(table[i1, j0])
    v01 = float(table[i0, j1])
    v11 = float(table[i1, j1])

    return (
        (1.0 - u) * (1.0 - v) * v00
        + u * (1.0 - v) * v10
        + (1.0 - u) * v * v01
        + u * v * v11
    )


def precompute_stage_antecedents_and_consequents(
    stage: str,
    shoulder_edges: bool,
    x1_pts: int = 61,
    x2_pts: int = 61,
    y_step: float = 0.2,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    tuple[FuzzyRule, ...],
    np.ndarray,
    np.ndarray,
    dict[str, np.ndarray],
]:
    """Precompute grids, rule antecedents A_i(x1,x2), and rule consequents B_i(y)."""
    if stage == "fc1":
        x1_grid = np.linspace(ARRIVAL_UNIVERSE[0], ARRIVAL_UNIVERSE[1], x1_pts)
        m1_dict = arrival_rate_memberships(x1_grid, shoulder_edges=shoulder_edges)
        rules = FC1_RULES
    elif stage == "fc2":
        x1_grid = np.linspace(EXTENSION_UNIVERSE[0], EXTENSION_UNIVERSE[1], x1_pts)
        m1_dict = extension_input_memberships(x1_grid, shoulder_edges=shoulder_edges)
        rules = FC2_RULES
    else:
        raise ValueError(f"Unsupported stage: {stage}")

    x2_grid = np.linspace(QUEUE_UNIVERSE[0], QUEUE_UNIVERSE[1], x2_pts)
    m2_dict = queue_length_memberships(x2_grid, shoulder_edges=shoulder_edges)

    y_grid = np.arange(
        EXTENSION_UNIVERSE[0],
        EXTENSION_UNIVERSE[1] + 0.5 * y_step,
        y_step,
        dtype=float,
    )
    out_mfs = extension_output_memberships(y_grid)

    a_list: list[np.ndarray] = []
    b_list: list[np.ndarray] = []
    ones_x2 = np.ones_like(x2_grid, dtype=float)

    for rule in rules:
        a1 = np.asarray(m1_dict[rule.antecedent1], dtype=float)[:, None]
        a2_vec = (
            ones_x2
            if rule.antecedent2 == "ANY"
            else np.asarray(m2_dict[rule.antecedent2], dtype=float)
        )
        a2 = a2_vec[None, :]
        a_joint = np.asarray(tnorm_lukasiewicz(a1, a2), dtype=float).ravel()
        a_list.append(a_joint)
        b_list.append(np.asarray(out_mfs[rule.consequent], dtype=float))

    return (
        x1_grid,
        x2_grid,
        y_grid,
        rules,
        np.array(a_list, dtype=float),
        np.array(b_list, dtype=float),
        out_mfs,
    )


def _cri_lut_row_worker(
    args: tuple[int, float, np.ndarray, dict[str, Any]],
) -> tuple[int, np.ndarray, np.ndarray]:
    i_idx, x1_val, x2_lut, cfg = args
    eng = CRIStageEngine(**cfg)
    row_vals = np.zeros(len(x2_lut), dtype=float)
    row_fb = np.zeros(len(x2_lut), dtype=bool)
    for j_idx, x2_val in enumerate(x2_lut):
        val, fb = eng.infer_direct_with_flag(float(x1_val), float(x2_val))
        row_vals[j_idx] = val
        row_fb[j_idx] = fb
    return i_idx, row_vals, row_fb


class CRIStageEngine:
    """Single-stage (FC1 or FC2) sup-T Compositional Rule of Inference engine."""

    def __init__(
        self,
        stage: str = "fc1",
        implicator: str = "lukasiewicz",
        defuzz_method: str = "centroid_above_floor",
        shoulder_edges: bool = True,
        sigma1: float = 0.0,
        sigma2: float = 0.0,
        x1_pts: int = 61,
        x2_pts: int = 61,
        y_step: float = 0.2,
        bilinear_singleton: bool = False,
    ) -> None:
        if implicator not in IMPLICATOR_MAP:
            raise ValueError(f"Unsupported implicator: {implicator}")
        self.stage = stage
        self.implicator_name = implicator
        self.implicator_fn = IMPLICATOR_MAP[implicator]
        self.defuzz_method = defuzz_method
        self.shoulder_edges = shoulder_edges
        self.sigma1 = float(sigma1)
        self.sigma2 = float(sigma2)
        self.x1_pts = int(x1_pts)
        self.x2_pts = int(x2_pts)
        self.y_step = float(y_step)
        self.bilinear_singleton = bool(bilinear_singleton)

        (
            self.x1_grid,
            self.x2_grid,
            self.y_grid,
            self.rules,
            self.a_rules,
            self.b_rules,
            self.out_mfs,
        ) = precompute_stage_antecedents_and_consequents(
            stage=stage,
            shoulder_edges=shoulder_edges,
            x1_pts=x1_pts,
            x2_pts=x2_pts,
            y_step=y_step,
        )

        self.r_tables = np.asarray(
            self.implicator_fn(self.a_rules[:, :, None], self.b_rules[:, None, :]),
            dtype=float,
        )

    def _init_kwargs(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "implicator": self.implicator_name,
            "defuzz_method": self.defuzz_method,
            "shoulder_edges": self.shoulder_edges,
            "sigma1": self.sigma1,
            "sigma2": self.sigma2,
            "x1_pts": self.x1_pts,
            "x2_pts": self.x2_pts,
            "y_step": self.y_step,
            "bilinear_singleton": self.bilinear_singleton,
        }

    def config_hash(self) -> str:
        """Compute deterministic SHA-256 hash of stage engine configuration."""
        payload = json.dumps(self._init_kwargs(), sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def build_input_fuzzy_set(self, x1: float, x2: float) -> np.ndarray:
        """Build 2D input fuzzy set A*(x1, x2) = A*_1(x1) * A*_2(x2) flattened."""
        a1 = build_marginal_input_mf(
            self.x1_grid, x1, self.sigma1, bilinear_singleton=self.bilinear_singleton
        )
        a2 = build_marginal_input_mf(
            self.x2_grid, x2, self.sigma2, bilinear_singleton=self.bilinear_singleton
        )
        return (a1[:, None] * a2[None, :]).ravel()

    def infer_rule_conclusion(
        self,
        rule_idx: int,
        a_star_flat: np.ndarray,
        active_idx: np.ndarray | None = None,
    ) -> np.ndarray:
        """Compute B*_i(y) = sup_x T(A*(x), R_i(x, y)) for a single rule."""
        act = (
            active_idx
            if active_idx is not None
            else np.flatnonzero(a_star_flat > 1e-3)
        )
        if len(act) == 0:
            act = np.array([int(np.argmax(a_star_flat))], dtype=np.int64)
        a_act = a_star_flat[act][:, None]
        r_act = self.r_tables[rule_idx, act, :]
        if self.implicator_name == "mamdani":
            composed = tnorm_min(a_act, r_act)
        else:
            composed = tnorm_lukasiewicz(a_act, r_act)
        return np.max(composed, axis=0)

    def infer_aggregated_set(self, x1: float, x2: float) -> np.ndarray:
        """Compute aggregated output fuzzy set B*(y) across all rules."""
        a_star = self.build_input_fuzzy_set(x1, x2)
        act = np.flatnonzero(a_star > 1e-3)
        if len(act) == 0:
            act = np.array([int(np.argmax(a_star))], dtype=np.int64)

        is_mamdani = self.implicator_name == "mamdani"
        b_agg = (
            np.zeros_like(self.y_grid, dtype=float)
            if is_mamdani
            else np.ones_like(self.y_grid, dtype=float)
        )

        for idx in range(len(self.rules)):
            b_i = self.infer_rule_conclusion(idx, a_star, active_idx=act)
            if is_mamdani:
                b_agg = np.maximum(b_agg, b_i)
            else:
                b_agg = np.minimum(b_agg, b_i)
        return b_agg

    def infer_direct_with_flag(self, x1: float, x2: float) -> tuple[float, bool]:
        """Perform direct CRI inference and return (crisp_output, fallback_used)."""
        b_agg = self.infer_aggregated_set(x1, x2)
        return defuzzify_set(self.y_grid, b_agg, method=self.defuzz_method)

    def infer_direct(self, x1: float, x2: float) -> float:
        """Perform direct CRI inference returning crisp output."""
        val, _ = self.infer_direct_with_flag(x1, x2)
        return val


class CRIInference:
    """Two-stage CRI inference engine supporting LUT caching and bilinear interpolation."""

    def __init__(
        self,
        stage: str = "fc1",
        implicator: str = "lukasiewicz",
        defuzz_method: str = "centroid_above_floor",
        shoulder_edges: bool = True,
        sigma_lambda: float = 0.0,
        sigma_queue: float = 0.0,
        sigma_ext1: float = 0.0,
        use_lut: bool = False,
        cache_dir: str | Path = "results/cache",
        n_workers: int | None = None,
    ) -> None:
        if stage not in ("fc1", "fc2"):
            raise ValueError(f"Unsupported stage: {stage}")
        self.stage = stage
        self.implicator = implicator
        self.defuzz_method = defuzz_method
        self.shoulder_edges = shoulder_edges
        self.sigma_lambda = float(sigma_lambda)
        self.sigma_queue = float(sigma_queue)
        self.sigma_ext1 = float(sigma_ext1)
        self.use_lut = bool(use_lut)
        self.cache_dir = Path(cache_dir)

        self.fc1_engine = CRIStageEngine(
            stage="fc1",
            implicator=implicator,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder_edges,
            sigma1=self.sigma_lambda,
            sigma2=self.sigma_queue,
        )
        self.fc2_engine = CRIStageEngine(
            stage="fc2",
            implicator=implicator,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder_edges,
            sigma1=self.sigma_ext1,
            sigma2=self.sigma_queue,
        )

        self.fc1_lut: dict[str, Any] | None = None
        self.fc2_lut: dict[str, Any] | None = None
        if self.use_lut:
            self.ensure_luts(n_workers=n_workers)

        self.total_calls: int = 0
        self.fallback_count: int = 0
        self.fc1_calls: int = 0
        self.fc1_fallbacks: int = 0
        self.fc2_calls: int = 0
        self.fc2_fallbacks: int = 0

    @property
    def fallback_rate(self) -> float:
        """Return fraction of inference calls that triggered zero-area fallback."""
        if self.total_calls == 0:
            return 0.0
        return self.fallback_count / self.total_calls

    @property
    def fc1_fallback_rate(self) -> float:
        """Return fraction of FC1 calls that triggered fallback."""
        if self.fc1_calls == 0:
            return 0.0
        return self.fc1_fallbacks / self.fc1_calls

    @property
    def fc2_fallback_rate(self) -> float:
        """Return fraction of FC2 calls that triggered fallback."""
        if self.fc2_calls == 0:
            return 0.0
        return self.fc2_fallbacks / self.fc2_calls

    def reset_stats(self) -> None:
        """Reset call and fallback counters."""
        self.total_calls = 0
        self.fallback_count = 0
        self.fc1_calls = 0
        self.fc1_fallbacks = 0
        self.fc2_calls = 0
        self.fc2_fallbacks = 0

    def _build_or_load_stage_lut(
        self,
        stage_eng: CRIStageEngine,
        n_workers: int | None = None,
    ) -> dict[str, Any]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cfg_hash = stage_eng.config_hash()
        cache_file = self.cache_dir / f"lut_cri_{stage_eng.stage}_{cfg_hash}.npz"
        if cache_file.exists():
            data = np.load(cache_file)
            return {
                "x1_lut": data["x1_lut"],
                "x2_lut": data["x2_lut"],
                "table": data["table"],
                "fallback_table": data["fallback_table"],
                "build_time_s": float(data["build_time_s"]),
                "cache_file": str(cache_file),
                "from_cache": True,
            }

        if stage_eng.stage == "fc1":
            x1_lut = np.arange(0.0, 12.0 + 0.1, 0.25, dtype=float)
        else:
            x1_lut = np.arange(0.0, 25.0 + 0.1, 0.25, dtype=float)
        x2_lut = np.arange(0.0, 60.0 + 0.5, 1.0, dtype=float)

        t0 = time.perf_counter()
        cfg = stage_eng._init_kwargs()
        tasks = [(i, float(x1_v), x2_lut, cfg) for i, x1_v in enumerate(x1_lut)]
        workers = n_workers if n_workers is not None else max(1, min(cpu_count() or 4, 8))

        table = np.zeros((len(x1_lut), len(x2_lut)), dtype=float)
        fb_table = np.zeros((len(x1_lut), len(x2_lut)), dtype=bool)

        if workers > 1:
            with Pool(processes=workers) as pool:
                for i_idx, row_vals, row_fb in pool.map(_cri_lut_row_worker, tasks):
                    table[i_idx, :] = row_vals
                    fb_table[i_idx, :] = row_fb
        else:
            for task in tasks:
                i_idx, row_vals, row_fb = _cri_lut_row_worker(task)
                table[i_idx, :] = row_vals
                fb_table[i_idx, :] = row_fb

        build_time = time.perf_counter() - t0
        np.savez_compressed(
            cache_file,
            x1_lut=x1_lut,
            x2_lut=x2_lut,
            table=table,
            fallback_table=fb_table,
            build_time_s=np.array(build_time, dtype=float),
        )
        return {
            "x1_lut": x1_lut,
            "x2_lut": x2_lut,
            "table": table,
            "fallback_table": fb_table,
            "build_time_s": build_time,
            "cache_file": str(cache_file),
            "from_cache": False,
        }

    def ensure_luts(self, n_workers: int | None = None) -> None:
        """Build or load cached LUTs for FC1 and FC2."""
        if self.fc1_lut is None:
            self.fc1_lut = self._build_or_load_stage_lut(self.fc1_engine, n_workers=n_workers)
        if self.fc2_lut is None:
            self.fc2_lut = self._build_or_load_stage_lut(self.fc2_engine, n_workers=n_workers)

    def infer_fc1(self, arrival_rate: float, queue_current: float) -> float:
        """Evaluate FC1 via LUT interpolation (if enabled) or direct CRI."""
        self.total_calls += 1
        self.fc1_calls += 1
        if self.use_lut and self.fc1_lut is not None:
            val = bilinear_interpolate_2d(
                self.fc1_lut["x1_lut"],
                self.fc1_lut["x2_lut"],
                self.fc1_lut["table"],
                arrival_rate,
                queue_current,
            )
            i_near = int(np.argmin(np.abs(self.fc1_lut["x1_lut"] - arrival_rate)))
            j_near = int(np.argmin(np.abs(self.fc1_lut["x2_lut"] - queue_current)))
            if bool(self.fc1_lut["fallback_table"][i_near, j_near]):
                self.fallback_count += 1
                self.fc1_fallbacks += 1
            return val

        val, fb = self.fc1_engine.infer_direct_with_flag(arrival_rate, queue_current)
        if fb:
            self.fallback_count += 1
            self.fc1_fallbacks += 1
        return val

    def infer_fc2(self, extension1: float, queue_others_max: float) -> float:
        """Evaluate FC2 via LUT interpolation (if enabled) or direct CRI."""
        self.total_calls += 1
        self.fc2_calls += 1
        if self.use_lut and self.fc2_lut is not None:
            val = bilinear_interpolate_2d(
                self.fc2_lut["x1_lut"],
                self.fc2_lut["x2_lut"],
                self.fc2_lut["table"],
                extension1,
                queue_others_max,
            )
            i_near = int(np.argmin(np.abs(self.fc2_lut["x1_lut"] - extension1)))
            j_near = int(np.argmin(np.abs(self.fc2_lut["x2_lut"] - queue_others_max)))
            if bool(self.fc2_lut["fallback_table"][i_near, j_near]):
                self.fallback_count += 1
                self.fc2_fallbacks += 1
            return val

        val, fb = self.fc2_engine.infer_direct_with_flag(extension1, queue_others_max)
        if fb:
            self.fallback_count += 1
            self.fc2_fallbacks += 1
        return val

    def infer(self, x1: float, x2: float) -> float:
        """Common inference interface for configured stage ('fc1' or 'fc2')."""
        if self.stage == "fc1":
            return self.infer_fc1(x1, x2)
        return self.infer_fc2(x1, x2)

    def infer_gpe(
        self,
        arrival_rate: float,
        queue_current: float,
        queue_others_max: float,
    ) -> tuple[float, float]:
        """Two-stage GPE: compute Extension1 via FC1 and Extension2 via FC2."""
        ext1 = self.infer_fc1(arrival_rate, queue_current)
        ext2 = self.infer_fc2(ext1, queue_others_max)
        return ext1, ext2
