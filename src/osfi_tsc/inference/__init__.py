"""Fuzzy inference engines: Mamdani, Sugeno, and OSFI-literal."""

from osfi_tsc.inference.mamdani import MamdaniInference
from osfi_tsc.inference.osfi_literal import OSFILiteralInference
from osfi_tsc.inference.sugeno import SugenoInference

__all__ = [
    "MamdaniInference",
    "SugenoInference",
    "OSFILiteralInference",
]
