# Program to compute Dark Energy FoM from covariance matrix
# Ayan Mitra

import pandas as pd
import numpy as np
import itertools


def FoM(input_file):  # With full path name
    a = pd.read_csv(input_file, sep=r"\s+")
    mat = np.asarray(a)
    names = ["cosmological_parameters--w", "cosmological_parameters--wa"]
    ind = []
    FoM_COV = []
    for n in list(a):
        if n == names[0] or n == names[1]:
            N = list(a).index(n)
            ind.append(N)
    cov = list(itertools.product(ind, repeat=2))
    for i in cov:
        tmp = mat[i]
        FoM_COV.append(tmp)
    FoM_COV = np.reshape(FoM_COV, (2, 2))
    X = np.linalg.det(FoM_COV)
    FoM = 1 / np.sqrt(X)
    return FoM
#    print(FoM)
