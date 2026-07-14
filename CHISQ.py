"""Compute chi-square summary values from COSMOSIS chain outputs."""

from pathlib import Path
import csv

import numpy as np
from cosmosis.postprocessing.inputs import read_input
from cosmosis.postprocessing.plots import MetropolisHastingsPlots1D
from cosmosis.postprocessing.postprocess import postprocessor_for_sampler


def _split_header_tokens(raw_header: list[str]) -> list[str]:
    """Return whitespace-delimited tokens from the first header row."""
    return raw_header[0].split()


def ch(path: str, ini_file: str) -> float:
    """Compute chi-square from a COSMOSIS run output.

    Args:
        path: Directory containing the COSMOSIS output text file.
        ini_file: COSMOSIS ini file path.

    Returns:
        Chi-square value computed from the reduced chain column.
    """
    burn = 10  # Keep legacy CHISQ output compatible with historical postprocessing defaults.
    output_dir = Path(path)
    ini_path = Path(ini_file)
    sampler, ini_config = read_input(ini_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    postprocessor = postprocessor_for_sampler(sampler)(
        ini_config,
        ini_path.stem,
        0,
        burn=burn,
        no_2d=False,
    )

    txt_path = output_dir / f"{ini_path.stem}.txt"
    with txt_path.open() as chain_file:
        reader = csv.reader(chain_file)
        row = next(reader)
    row = [word.replace("\t", "  ") for word in row]
    row = [word.replace("#", "  ") for word in row]
    header_tokens = _split_header_tokens(row)

    plotter = MetropolisHastingsPlots1D(postprocessor)
    reduced_column = plotter.reduced_col(header_tokens[-1])
    chi_square = -2 * np.min(reduced_column)
    return chi_square
