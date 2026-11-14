"""CLI script to execute Stage 1 reproduction experiments and statistical summaries."""

from __future__ import annotations

import argparse
from pathlib import Path
import time

from osfi_tsc.experiment import run_all_experiments
from osfi_tsc.fuzzy.rules import export_rule_bases_markdown


def main() -> None:
    """Parse arguments and run the full reproduction suite."""
    parser = argparse.ArgumentParser(
        description="Run Stage 1 OSFI-TSC reproduction experiments."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default.yaml",
        help="Path to default YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for raw and summary results.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel worker processes.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    export_rule_bases_markdown(repo_root / "docs" / "rule_bases.md")

    t0 = time.perf_counter()
    results = run_all_experiments(
        config_path=args.config,
        output_root=args.output,
        n_workers=args.workers,
    )
    elapsed = time.perf_counter() - t0
    print(f"Completed {len(results['raw'])} metric rows in {elapsed:.2f} s.")


if __name__ == "__main__":
    main()
