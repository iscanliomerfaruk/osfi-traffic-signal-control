"""Mamdani (Compositional Rule of Inference) fuzzy inference engine."""

from __future__ import annotations

import numpy as np

from osfi_tsc.fuzzy.membership import (
    EXTENSION_UNIVERSE,
    arrival_rate_memberships,
    extension_input_memberships,
    extension_output_memberships,
    queue_length_memberships,
)
from osfi_tsc.fuzzy.operators import (
    defuzz_centroid,
    implicator_mamdani,
    snorm_max,
    tnorm_min,
)
from osfi_tsc.fuzzy.rules import EXTENSION_TERMS, FC1_RULES, FC2_RULES, FuzzyRule


class MamdaniInference:
    """Mamdani fuzzy inference engine using min AND, min implication, max aggregation, and centroid."""

    def __init__(
        self,
        stage: str = "fc1",
        shoulder_edges: bool = True,
        grid_step: float = 0.05,
        mf_sigma_scale: float = 1.0,
    ) -> None:
        if stage not in ("fc1", "fc2"):
            raise ValueError(f"Unsupported stage: {stage}")
        self.stage = stage
        self.shoulder_edges = shoulder_edges
        self.grid_step = grid_step
        self.mf_sigma_scale = float(mf_sigma_scale)
        self.universe = np.arange(
            EXTENSION_UNIVERSE[0],
            EXTENSION_UNIVERSE[1] + 0.5 * grid_step,
            grid_step,
            dtype=float,
        )
        self.output_mfs = extension_output_memberships(self.universe)
        self.total_calls: int = 0
        self.fallback_count: int = 0
        self.fc1_calls: int = 0
        self.fc1_fallbacks: int = 0
        self.fc2_calls: int = 0
        self.fc2_fallbacks: int = 0

    @property
    def fallback_rate(self) -> float:
        """Return fraction of inference calls that required fallback."""
        if self.total_calls == 0:
            return 0.0
        return self.fallback_count / self.total_calls

    def reset_stats(self) -> None:
        """Reset call and fallback counters."""
        self.total_calls = 0
        self.fallback_count = 0
        self.fc1_calls = 0
        self.fc1_fallbacks = 0
        self.fc2_calls = 0
        self.fc2_fallbacks = 0

    def _evaluate_rules(
        self,
        m1: dict[str, float],
        m2: dict[str, float],
        rules: tuple[FuzzyRule, ...],
    ) -> float:
        consequent_alphas: dict[str, float] = {term: 0.0 for term in EXTENSION_TERMS}
        for rule in rules:
            f1 = float(m1[rule.antecedent1])
            f2 = 1.0 if rule.antecedent2 == "ANY" else float(m2[rule.antecedent2])
            alpha = float(tnorm_min(f1, f2))
            if alpha > consequent_alphas[rule.consequent]:
                consequent_alphas[rule.consequent] = alpha

        aggregated = np.zeros_like(self.universe)
        for term, alpha in consequent_alphas.items():
            if alpha > 0.0:
                implied = implicator_mamdani(alpha, self.output_mfs[term])
                aggregated = snorm_max(aggregated, implied)

        return defuzz_centroid(self.universe, aggregated)

    def infer_fc1(self, arrival_rate: float, queue_current: float) -> float:
        """Evaluate FC1: (arrival_rate, queue_current) -> Extension1."""
        self.total_calls += 1
        self.fc1_calls += 1
        m1 = arrival_rate_memberships(
            arrival_rate,
            shoulder_edges=self.shoulder_edges,
            sigma_scale=self.mf_sigma_scale,
        )
        m2 = queue_length_memberships(
            queue_current,
            shoulder_edges=self.shoulder_edges,
            sigma_scale=self.mf_sigma_scale,
        )
        return self._evaluate_rules(m1, m2, FC1_RULES)

    def infer_fc2(self, extension1: float, queue_others_max: float) -> float:
        """Evaluate FC2: (extension1, queue_others_max) -> Extension2."""
        self.total_calls += 1
        self.fc2_calls += 1
        m1 = extension_input_memberships(extension1, shoulder_edges=self.shoulder_edges)
        m2 = queue_length_memberships(
            queue_others_max,
            shoulder_edges=self.shoulder_edges,
            sigma_scale=self.mf_sigma_scale,
        )
        return self._evaluate_rules(m1, m2, FC2_RULES)

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
