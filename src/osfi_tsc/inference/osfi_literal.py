"""OSFI-literal fuzzy inference engine as formulated in Section 4.1.2 of the paper."""

from __future__ import annotations

from osfi_tsc.fuzzy.membership import (
    EXTENSION_PEAKS,
    arrival_rate_memberships,
    extension_input_memberships,
    queue_length_memberships,
)
from osfi_tsc.fuzzy.operators import tnorm_lukasiewicz, tnorm_min
from osfi_tsc.fuzzy.rules import (
    DEAD_ZONE_THRESHOLD,
    FC1_RULES,
    FC2_RULES,
    FuzzyRule,
    nearest_rule_fallback,
)


class OSFILiteralInference:
    """OSFI-literal engine using configured AND t-norm and nearest-rule dead-zone fallback."""

    def __init__(
        self,
        stage: str = "fc1",
        shoulder_edges: bool = True,
        and_operator: str = "lukasiewicz",
        mf_sigma_scale: float = 1.0,
    ) -> None:
        if stage not in ("fc1", "fc2"):
            raise ValueError(f"Unsupported stage: {stage}")
        if and_operator not in ("lukasiewicz", "min"):
            raise ValueError(f"Unsupported and_operator: {and_operator}")
        self.stage = stage
        self.shoulder_edges = shoulder_edges
        self.and_operator = and_operator
        self.mf_sigma_scale = float(mf_sigma_scale)
        self.peaks = dict(EXTENSION_PEAKS)
        self.total_calls: int = 0
        self.fallback_count: int = 0
        self.fc1_calls: int = 0
        self.fc1_fallbacks: int = 0
        self.fc2_calls: int = 0
        self.fc2_fallbacks: int = 0

    @property
    def fallback_rate(self) -> float:
        """Return overall fraction of inference calls that triggered dead-zone fallback."""
        if self.total_calls == 0:
            return 0.0
        return self.fallback_count / self.total_calls

    @property
    def fc1_fallback_rate(self) -> float:
        """Return fraction of FC1 calls that triggered dead-zone fallback."""
        if self.fc1_calls == 0:
            return 0.0
        return self.fc1_fallbacks / self.fc1_calls

    @property
    def fc2_fallback_rate(self) -> float:
        """Return fraction of FC2 calls that triggered dead-zone fallback."""
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

    def _evaluate_rules(
        self,
        m1: dict[str, float],
        m2: dict[str, float],
        rules: tuple[FuzzyRule, ...],
        is_fc1: bool,
    ) -> float:
        num = 0.0
        den = 0.0
        max_alpha = 0.0
        use_luk = self.and_operator == "lukasiewicz"
        for rule in rules:
            f1 = float(m1[rule.antecedent1])
            f2 = 1.0 if rule.antecedent2 == "ANY" else float(m2[rule.antecedent2])
            alpha = (
                float(tnorm_lukasiewicz(f1, f2))
                if use_luk
                else float(tnorm_min(f1, f2))
            )
            if alpha > max_alpha:
                max_alpha = alpha
            if alpha > 0.0:
                num += alpha * self.peaks[rule.consequent]
                den += alpha
        if max_alpha < DEAD_ZONE_THRESHOLD or den <= 1e-12:
            self.fallback_count += 1
            if is_fc1:
                self.fc1_fallbacks += 1
            else:
                self.fc2_fallbacks += 1
            return nearest_rule_fallback(m1, m2, rules, self.peaks)
        return num / den

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
        return self._evaluate_rules(m1, m2, FC1_RULES, is_fc1=True)

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
        return self._evaluate_rules(m1, m2, FC2_RULES, is_fc1=False)

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
