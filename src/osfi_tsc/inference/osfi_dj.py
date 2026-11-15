"""Deng & Jiang (2014) Optimization Similarity Fuzzy Inference (OSFI-DJ) engine."""

from __future__ import annotations

import hashlib
import json
from multiprocessing import Pool, cpu_count
from pathlib import Path
import time
from typing import Any
import numpy as np
from scipy.spatial.distance import cdist

from osfi_tsc.inference.cri import (
    IMPLICATOR_MAP,
    bilinear_interpolate_2d,
    build_marginal_input_mf,
    d1_similarity,
    defuzzify_set,
    precompute_stage_antecedents_and_consequents,
)

TIE_BREAK_OPTIONS = ("smallest", "largest", "midpoint")


def _select_b_from_objectives(
    obj_ub: np.ndarray,
    b_grid: np.ndarray,
    tie_break: str,
) -> np.ndarray:
    """Select optimal b in [0, 1] per y-row with plateau tie-breaking and V-kink vertex recovery."""
    min_vals = np.min(obj_ub, axis=1, keepdims=True)
    mask = obj_ub <= (min_vals + 1e-12)
    counts = np.sum(mask, axis=1)

    n_rows, n_b = obj_ub.shape
    first_idx = np.argmax(mask, axis=1)
    last_idx = (n_b - 1) - np.argmax(mask[:, ::-1], axis=1)

    if tie_break == "smallest":
        b_out = b_grid[first_idx].copy()
    elif tie_break == "largest":
        b_out = b_grid[last_idx].copy()
    elif tie_break == "midpoint":
        b_out = 0.5 * (b_grid[first_idx] + b_grid[last_idx])
    else:
        raise ValueError(f"Unsupported tie_break option: {tie_break}")

    if n_b < 2:
        return b_out

    db = float(b_grid[1] - b_grid[0])
    unique_rows = np.flatnonzero(counts == 1)
    for r_idx in unique_rows:
        k = int(first_idx[r_idx])
        f_k = float(obj_ub[r_idx, k])
        if k > 0:
            f_left = float(obj_ub[r_idx, k - 1])
            if abs((f_left + f_k) - db) <= 1e-11:
                b_out[r_idx] = 0.5 * (
                    float(b_grid[k - 1]) + float(b_grid[k]) + f_left - f_k
                )
                continue
        if k + 1 < n_b:
            f_right = float(obj_ub[r_idx, k + 1])
            if abs((f_k + f_right) - db) <= 1e-11:
                b_out[r_idx] = 0.5 * (
                    float(b_grid[k]) + float(b_grid[k + 1]) + f_k - f_right
                )
    return np.clip(b_out, 0.0, 1.0)


def _osfi_lut_row_worker(
    args: tuple[int, float, np.ndarray, dict[str, Any]],
) -> tuple[int, np.ndarray, np.ndarray]:
    i_idx, x1_val, x2_lut, cfg = args
    eng = OSFIDJStageEngine(**cfg)
    row_vals = np.zeros(len(x2_lut), dtype=float)
    row_fb = np.zeros(len(x2_lut), dtype=bool)
    for j_idx, x2_val in enumerate(x2_lut):
        val, fb = eng.infer_direct_with_flag(float(x1_val), float(x2_val))
        row_vals[j_idx] = val
        row_fb[j_idx] = fb
    return i_idx, row_vals, row_fb


class OSFIDJStageEngine:
    """Single-stage (FC1 or FC2) Deng & Jiang (2014) OSFI engine."""

    def __init__(
        self,
        stage: str = "fc1",
        implicator: str = "lukasiewicz",
        tie_break: str = "smallest",
        defuzz_method: str = "centroid_above_floor",
        shoulder_edges: bool = True,
        sigma1: float = 0.0,
        sigma2: float = 0.0,
        x1_pts: int = 61,
        x2_pts: int = 61,
        y_step: float = 0.2,
        b_pts: int = 201,
        bilinear_singleton: bool = False,
    ) -> None:
        if implicator not in IMPLICATOR_MAP:
            raise ValueError(f"Unsupported implicator: {implicator}")
        if tie_break not in TIE_BREAK_OPTIONS:
            raise ValueError(f"Unsupported tie_break: {tie_break}")

        self.stage = stage
        self.implicator_name = implicator
        self.implicator_fn = IMPLICATOR_MAP[implicator]
        self.tie_break = tie_break
        self.defuzz_method = defuzz_method
        self.shoulder_edges = shoulder_edges
        self.sigma1 = float(sigma1)
        self.sigma2 = float(sigma2)
        self.x1_pts = int(x1_pts)
        self.x2_pts = int(x2_pts)
        self.y_step = float(y_step)
        self.b_pts = int(b_pts)
        self.bilinear_singleton = bool(bilinear_singleton)

        self.b_grid = np.linspace(0.0, 1.0, self.b_pts, dtype=float)

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

        self._rule_pos_idx: list[np.ndarray] = []
        self._rule_u_inv: list[np.ndarray] = []
        self._rule_r_pos_u: list[np.ndarray] = []
        for idx in range(len(self.rules)):
            pos = np.flatnonzero(self.a_rules[idx] > 0.0)
            u_vals, u_inv = np.unique(self.b_rules[idx], return_inverse=True)
            r_pu = np.asarray(
                self.implicator_fn(self.a_rules[idx, pos][:, None], u_vals[None, :]),
                dtype=float,
            )
            self._rule_pos_idx.append(pos)
            self._rule_u_inv.append(u_inv)
            self._rule_r_pos_u.append(r_pu)

    def _init_kwargs(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "implicator": self.implicator_name,
            "tie_break": self.tie_break,
            "defuzz_method": self.defuzz_method,
            "shoulder_edges": self.shoulder_edges,
            "sigma1": self.sigma1,
            "sigma2": self.sigma2,
            "x1_pts": self.x1_pts,
            "x2_pts": self.x2_pts,
            "y_step": self.y_step,
            "b_pts": self.b_pts,
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
        """Compute B*_i(y) = argmin_b sum_{x in act} |R_i(x, y) - I(A*(x), b)| for one rule."""
        all_b = self.infer_all_rule_conclusions(
            a_star_flat, active_idx=active_idx, rule_indices=(rule_idx,)
        )
        return all_b[0]

    def infer_all_rule_conclusions(
        self,
        a_star_flat: np.ndarray,
        active_idx: np.ndarray | None = None,
        rule_indices: tuple[int, ...] | None = None,
    ) -> np.ndarray:
        """Compute B*_i(y) for selected rules (default: all rules) using exact L1 decomposition."""
        act = (
            active_idx
            if active_idx is not None
            else np.flatnonzero(a_star_flat > 1e-3)
        )
        if len(act) == 0:
            act = np.array([int(np.argmax(a_star_flat))], dtype=np.int64)

        indices = (
            rule_indices
            if rule_indices is not None
            else tuple(range(len(self.rules)))
        )

        a_act = a_star_flat[act]
        i_act_b = np.asarray(
            self.implicator_fn(a_act[:, None], self.b_grid[None, :]),
            dtype=float,
        )

        is_mamdani = self.implicator_name == "mamdani"
        zero_diff_act = i_act_b if is_mamdani else (1.0 - i_act_b)
        base_b = np.sum(zero_diff_act, axis=0)

        active_mask = np.zeros(len(a_star_flat), dtype=bool)
        active_mask[act] = True

        full_zero_diff = np.zeros((len(a_star_flat), self.b_pts), dtype=float)
        full_zero_diff[act, :] = zero_diff_act
        full_i_b = np.zeros((len(a_star_flat), self.b_pts), dtype=float)
        full_i_b[act, :] = i_act_b

        out = np.zeros((len(indices), len(self.y_grid)), dtype=float)
        for out_k, r_idx in enumerate(indices):
            pos = self._rule_pos_idx[r_idx]
            u_inv = self._rule_u_inv[r_idx]
            r_pu = self._rule_r_pos_u[r_idx]

            in_act = active_mask[pos]
            if not np.any(in_act):
                obj_ub = np.tile(base_b[None, :], (r_pu.shape[1], 1))
            else:
                pos_act = pos[in_act]
                r_sub = r_pu[in_act, :]
                sub_base = np.sum(full_zero_diff[pos_act, :], axis=0)
                active_l1 = cdist(
                    r_sub.T, full_i_b[pos_act, :].T, metric="cityblock"
                )
                obj_ub = (base_b - sub_base)[None, :] + active_l1

            b_u = _select_b_from_objectives(obj_ub, self.b_grid, self.tie_break)
            out[out_k, :] = b_u[u_inv]

        return out

    def infer_aggregated_set(self, x1: float, x2: float) -> np.ndarray:
        """Compute aggregated output fuzzy set B*(y) across all rules."""
        a_star = self.build_input_fuzzy_set(x1, x2)
        act = np.flatnonzero(a_star > 1e-3)
        if len(act) == 0:
            act = np.array([int(np.argmax(a_star))], dtype=np.int64)

        b_all = self.infer_all_rule_conclusions(a_star, active_idx=act)
        if self.implicator_name == "mamdani":
            return np.max(b_all, axis=0)
        return np.min(b_all, axis=0)

    def evaluate_rule_detail(
        self,
        rule_idx: int,
        x1: float,
        x2: float,
    ) -> dict[str, Any]:
        """Return complete intermediate arrays (A, B, R, A*, B*, R*, Sim) for one rule."""
        a_star = self.build_input_fuzzy_set(x1, x2)
        act = np.flatnonzero(a_star > 1e-3)
        if len(act) == 0:
            act = np.array([int(np.argmax(a_star))], dtype=np.int64)

        b_star = self.infer_rule_conclusion(rule_idx, a_star, active_idx=act)
        r_table = self.r_tables[rule_idx]
        r_star = np.asarray(
            self.implicator_fn(a_star[:, None], b_star[None, :]),
            dtype=float,
        )
        sim_full = d1_similarity(r_table, r_star)
        sim_active = d1_similarity(r_table[act, :], r_star[act, :])

        return {
            "x1_grid": self.x1_grid,
            "x2_grid": self.x2_grid,
            "y_grid": self.y_grid,
            "b_grid": self.b_grid,
            "rule": self.rules[rule_idx],
            "a_rule_2d": self.a_rules[rule_idx].reshape(self.x1_pts, self.x2_pts),
            "b_rule": self.b_rules[rule_idx],
            "r_table": r_table,
            "a_star_2d": a_star.reshape(self.x1_pts, self.x2_pts),
            "b_star": b_star,
            "r_star": r_star,
            "similarity_full": sim_full,
            "similarity_active": sim_active,
        }

    def infer_direct_with_flag(self, x1: float, x2: float) -> tuple[float, bool]:
        """Perform direct OSFI-DJ inference and return (crisp_output, fallback_used)."""
        b_agg = self.infer_aggregated_set(x1, x2)
        return defuzzify_set(self.y_grid, b_agg, method=self.defuzz_method)

    def infer_direct(self, x1: float, x2: float) -> float:
        """Perform direct OSFI-DJ inference returning crisp output."""
        val, _ = self.infer_direct_with_flag(x1, x2)
        return val


def measure_stage_lut_interpolation_error(
    stage_engine: Any,
    lut_dict: dict[str, Any],
    n_samples: int = 500,
    seed: int = 42,
) -> dict[str, float]:
    """Measure LUT bilinear interpolation accuracy on random off-grid points vs direct inference."""
    rng = np.random.default_rng(seed)
    x1_min = float(lut_dict["x1_lut"][0])
    x1_max = float(lut_dict["x1_lut"][-1])
    x2_min = float(lut_dict["x2_lut"][0])
    x2_max = float(lut_dict["x2_lut"][-1])

    x1_samples = rng.uniform(x1_min, x1_max, size=n_samples)
    x2_samples = rng.uniform(x2_min, x2_max, size=n_samples)

    abs_errors = np.zeros(n_samples, dtype=float)
    for k in range(n_samples):
        x1_v = float(x1_samples[k])
        x2_v = float(x2_samples[k])
        direct_val = stage_engine.infer_direct(x1_v, x2_v)
        interp_val = bilinear_interpolate_2d(
            lut_dict["x1_lut"],
            lut_dict["x2_lut"],
            lut_dict["table"],
            x1_v,
            x2_v,
        )
        abs_errors[k] = abs(direct_val - interp_val)

    return {
        "n_samples": float(n_samples),
        "max_abs_error": float(np.max(abs_errors)),
        "mean_abs_error": float(np.mean(abs_errors)),
        "median_abs_error": float(np.median(abs_errors)),
        "p95_abs_error": float(np.percentile(abs_errors, 95)),
    }


class OSFIDJInference:
    """Two-stage Deng & Jiang (2014) OSFI engine supporting LUT caching and bilinear interpolation."""

    def __init__(
        self,
        stage: str = "fc1",
        implicator: str = "lukasiewicz",
        tie_break: str = "smallest",
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
        self.tie_break = tie_break
        self.defuzz_method = defuzz_method
        self.shoulder_edges = shoulder_edges
        self.sigma_lambda = float(sigma_lambda)
        self.sigma_queue = float(sigma_queue)
        self.sigma_ext1 = float(sigma_ext1)
        self.use_lut = bool(use_lut)
        self.cache_dir = Path(cache_dir)

        self.fc1_engine = OSFIDJStageEngine(
            stage="fc1",
            implicator=implicator,
            tie_break=tie_break,
            defuzz_method=defuzz_method,
            shoulder_edges=shoulder_edges,
            sigma1=self.sigma_lambda,
            sigma2=self.sigma_queue,
        )
        self.fc2_engine = OSFIDJStageEngine(
            stage="fc2",
            implicator=implicator,
            tie_break=tie_break,
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
        stage_eng: OSFIDJStageEngine,
        n_workers: int | None = None,
    ) -> dict[str, Any]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cfg_hash = stage_eng.config_hash()
        cache_file = self.cache_dir / f"lut_osfi_dj_{stage_eng.stage}_{cfg_hash}.npz"
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
                for i_idx, row_vals, row_fb in pool.map(_osfi_lut_row_worker, tasks):
                    table[i_idx, :] = row_vals
                    fb_table[i_idx, :] = row_fb
        else:
            for task in tasks:
                i_idx, row_vals, row_fb = _osfi_lut_row_worker(task)
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

    def measure_lut_errors(
        self,
        n_samples: int = 500,
        seed: int = 42,
    ) -> dict[str, dict[str, float]]:
        """Measure LUT interpolation error on random off-grid points for FC1 and FC2."""
        self.ensure_luts()
        assert self.fc1_lut is not None and self.fc2_lut is not None
        return {
            "fc1": measure_stage_lut_interpolation_error(
                self.fc1_engine, self.fc1_lut, n_samples=n_samples, seed=seed
            ),
            "fc2": measure_stage_lut_interpolation_error(
                self.fc2_engine, self.fc2_lut, n_samples=n_samples, seed=seed + 1
            ),
        }

    def infer_fc1(self, arrival_rate: float, queue_current: float) -> float:
        """Evaluate FC1 via LUT interpolation (if enabled) or direct OSFI-DJ."""
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
        """Evaluate FC2 via LUT interpolation (if enabled) or direct OSFI-DJ."""
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
