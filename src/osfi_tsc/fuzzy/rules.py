"""Rule bases for FC1 (16 rules) and FC2 (13 rules)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ARRIVAL_TERMS: tuple[str, ...] = ("Z", "Lo", "M", "H")
QUEUE_TERMS: tuple[str, ...] = ("Sh", "M", "L", "VL")
EXTENSION_TERMS: tuple[str, ...] = ("Z", "Sh", "M", "L")

QUEUE_PENALTY: dict[str, int] = {
    "Sh": 0,
    "M": 0,
    "L": 1,
    "VL": 2,
}

PAPER_FC1_RULES: dict[tuple[str, str], tuple[str, str]] = {
    ("Z", "Sh"): ("Z", "FC1 Rule 1 (p. 12)"),
    ("Lo", "L"): ("Sh", "FC1 Rule 2 (p. 12)"),
    ("M", "Sh"): ("Sh", "FC1 Rule 3 (p. 12)"),
}

PAPER_FC2_RULES: dict[tuple[str, str], tuple[str, str]] = {
    ("Z", "Sh"): ("Z", "FC2 Rule 1 (p. 13)"),
    ("Sh", "M"): ("Sh", "FC2 Rule 2 (p. 13)"),
    ("M", "Sh"): ("M", "FC2 Rule 3 (p. 13)"),
}


@dataclass(frozen=True)
class FuzzyRule:
    """Single fuzzy rule for two-input single-output controller."""

    rule_id: int
    antecedent1: str
    antecedent2: str
    consequent: str
    in_paper: bool
    paper_ref: str
    covered_antecedent2: tuple[str, ...]


def build_fc1_rules() -> tuple[FuzzyRule, ...]:
    """Construct the 16 monotone rules for FC1: floor((a + q) / 2)."""
    rules: list[FuzzyRule] = []
    rule_id = 1
    for a_idx, a_term in enumerate(ARRIVAL_TERMS):
        for q_idx, q_term in enumerate(QUEUE_TERMS):
            ext_idx = (a_idx + q_idx) // 2
            consequent = EXTENSION_TERMS[ext_idx]
            in_paper = (a_term, q_term) in PAPER_FC1_RULES
            paper_ref = PAPER_FC1_RULES[(a_term, q_term)][1] if in_paper else "-"
            rules.append(
                FuzzyRule(
                    rule_id=rule_id,
                    antecedent1=a_term,
                    antecedent2=q_term,
                    consequent=consequent,
                    in_paper=in_paper,
                    paper_ref=paper_ref,
                    covered_antecedent2=(q_term,),
                )
            )
            rule_id += 1
    return tuple(rules)


def build_fc2_rules() -> tuple[FuzzyRule, ...]:
    """Construct the 13 monotone rules for FC2 with collapsed e=Z rule."""
    rules: list[FuzzyRule] = [
        FuzzyRule(
            rule_id=1,
            antecedent1="Z",
            antecedent2="ANY",
            consequent="Z",
            in_paper=True,
            paper_ref=PAPER_FC2_RULES[("Z", "Sh")][1],
            covered_antecedent2=QUEUE_TERMS,
        )
    ]
    rule_id = 2
    for e_idx in range(1, len(EXTENSION_TERMS)):
        e_term = EXTENSION_TERMS[e_idx]
        for q_term in QUEUE_TERMS:
            pen = QUEUE_PENALTY[q_term]
            out_idx = max(0, e_idx - pen)
            consequent = EXTENSION_TERMS[out_idx]
            in_paper = (e_term, q_term) in PAPER_FC2_RULES
            paper_ref = PAPER_FC2_RULES[(e_term, q_term)][1] if in_paper else "-"
            rules.append(
                FuzzyRule(
                    rule_id=rule_id,
                    antecedent1=e_term,
                    antecedent2=q_term,
                    consequent=consequent,
                    in_paper=in_paper,
                    paper_ref=paper_ref,
                    covered_antecedent2=(q_term,),
                )
            )
            rule_id += 1
    return tuple(rules)


FC1_RULES: tuple[FuzzyRule, ...] = build_fc1_rules()
FC2_RULES: tuple[FuzzyRule, ...] = build_fc2_rules()


def lookup_fc1(arrival_term: str, queue_term: str) -> str:
    """Return FC1 consequent term for given linguistic antecedents."""
    for rule in FC1_RULES:
        if rule.antecedent1 == arrival_term and queue_term in rule.covered_antecedent2:
            return rule.consequent
    raise KeyError(f"Unknown FC1 antecedents: ({arrival_term}, {queue_term})")


def lookup_fc2(ext1_term: str, queue_other_term: str) -> str:
    """Return FC2 consequent term for given linguistic antecedents."""
    for rule in FC2_RULES:
        if rule.antecedent1 == ext1_term and queue_other_term in rule.covered_antecedent2:
            return rule.consequent
    raise KeyError(f"Unknown FC2 antecedents: ({ext1_term}, {queue_other_term})")


def format_rule_bases_markdown() -> str:
    """Render both FC1 and FC2 rule tables as markdown documentation."""
    lines: list[str] = [
        "# Fuzzy Rule Bases (`FC1` and `FC2`)",
        "",
        "The reference paper (Esmaeili et al., 2025, Sec. 4.1.2, pp. 12-13) specifies that:",
        "- `FC1` contains **16 rules** mapping `(Arrival rate, Queue length) -> Extension1`, but lists only 3 example rules.",
        "- `FC2` contains **13 rules** mapping `(Extension1, Queue length of other phases) -> Extension2`, and lists 3 example rules.",
        "",
        "## 1. `FC1` Rule Base (16 Rules)",
        "",
        "Design rule: with `Arrival rate` $a \\in \\{\\text{Z}:0, \\text{Lo}:1, \\text{M}:2, \\text{H}:3\\}$ and `Queue length` $q \\in \\{\\text{Sh}:0, \\text{M}:1, \\text{L}:2, \\text{VL}:3\\}$,",
        "$$\\text{Extension1} = \\lfloor (a + q) / 2 \\rfloor \\in \\{\\text{Z}:0, \\text{Sh}:1, \\text{M}:2, \\text{L}:3\\}.$$",
        "",
        "| Rule # | Arrival Rate ($\\lambda$) | Queue Length ($q$) | Consequent (`Extension1`) | Verbatim in Paper? | Paper Reference |",
        "| :---: | :---: | :---: | :---: | :---: | :--- |",
    ]
    for r in FC1_RULES:
        verbatim = "Yes" if r.in_paper else "No (completed)"
        lines.append(
            f"| {r.rule_id} | `{r.antecedent1}` | `{r.antecedent2}` | `{r.consequent}` | {verbatim} | {r.paper_ref} |"
        )

    lines.extend(
        [
            "",
            "## 2. `FC2` Rule Base (13 Rules)",
            "",
            "Design rule: with `Extension1` $e \\in \\{\\text{Z}:0, \\text{Sh}:1, \\text{M}:2, \\text{L}:3\\}$ and competing queue penalty $\\text{penalty}(q') \\in \\{\\text{Sh}:0, \\text{M}:0, \\text{L}:1, \\text{VL}:2\\}$,",
            "$$\\text{Extension2} = \\max(0, e - \\text{penalty}(q')).$$",
            "All four $e = \\text{Z}$ combinations yield `Extension2 = Z` and collapse into a single rule (Rule 1), yielding $1 + 3 \\times 4 = 13$ rules.",
            "",
            "| Rule # | `Extension1` ($e$) | Other Phases Queue ($q'$) | Consequent (`Extension2`) | Verbatim in Paper? | Paper Reference |",
            "| :---: | :---: | :---: | :---: | :---: | :--- |",
        ]
    )
    for r in FC2_RULES:
        verbatim = "Yes" if r.in_paper else "No (completed)"
        ant2_display = "`ANY` (`Sh`, `M`, `L`, `VL`)" if r.antecedent2 == "ANY" else f"`{r.antecedent2}`"
        lines.append(
            f"| {r.rule_id} | `{r.antecedent1}` | {ant2_display} | `{r.consequent}` | {verbatim} | {r.paper_ref} |"
        )
    lines.append("")
    return "\n".join(lines)


def export_rule_bases_markdown(output_path: str | Path) -> None:
    """Write the markdown documentation of FC1 and FC2 rule bases to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_rule_bases_markdown(), encoding="utf-8")
