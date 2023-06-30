import numpy as np
import pandas as pd
from cosmosis.postprocess import parser
from cosmosis.postprocessing.inputs import read_input
from cosmosis.postprocessing.postprocess import postprocessor_for_sampler
from cosmosis.postprocessing.plots import (
    MetropolisHastingsPlots2D,
    MetropolisHastingsPlots1D,
)
import os
import csv
import warnings

warnings.filterwarnings("ignore")


def convert(lst):
    return lst[0].split()


def ch(Path, Ini):
    Burnin = 10  # token value
    path = Path
    sampler, ini = read_input(Ini)
    os.makedirs(path, exist_ok=True)
    proc = postprocessor_for_sampler(sampler)(
        ini, Ini[:-4], 0, burn=Burnin, no_2d=False
    )
    # ---------------------------------------------------
    with open(Path + Ini.replace(".ini", ".txt")) as f:
        reader = csv.reader(f)
        row1 = next(reader)  # gets the first line
    row1 = [word.replace("\t", "  ") for word in row1]
    row1 = [word.replace("#", "  ") for word in row1]
    row1 = convert(row1)
    plotter = MetropolisHastingsPlots1D(proc)
    x = plotter.reduced_col(row1[-1])
    Chisquare = -2 * np.min(x)
    return Chisquare
