"""CLI script to render all PDF and PNG figures for Stage 1."""

from __future__ import annotations

import argparse
from pathlib import Path

from osfi_tsc.plotting import generate_all_figures


def main() -> None:
    """Parse arguments and generate all figures."""
    parser = argparse.ArgumentParser(
        description="Generate Stage 1 figures in PDF and PNG formats (300 dpi)."
    )
    parser.add_argument(
        "--results",
        type=str,
        default="results",
        help="Directory containing raw/ and summary/ experiment outputs.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="figures",
        help="Target directory for generated PDF and PNG figures.",
    )
    args = parser.parse_args()

    paths = generate_all_figures(
        results_root=Path(args.results),
        figures_dir=Path(args.output),
    )
    print(f"Generated {len(paths)} figure files in '{args.output}/':")
    for p in paths:
        print(f" - {p}")


if __name__ == "__main__":
    main()
