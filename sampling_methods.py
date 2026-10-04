"""
sampling_methods.py — the five sampling methods compared in this project (new in v3).

    Random          independent uniform draws (Monte Carlo baseline)
    LHS             Latin Hypercube: each input's range cut into n slices, one sample per slice
    Optimised LHS   LHS rearranged to minimise centred discrepancy (better spread across input pairs)
    Sobol           scrambled Sobol low-discrepancy sequence (best with n = power of 2)
    Halton          scrambled Halton low-discrepancy sequence

Every method produces points in the unit cube [0, 1)^d. They are then scaled to PARAM_RANGES and run through the
same BCA ETTV calculator (sample.evaluate_row), so the only thing that differs between datasets is *where* the
samples are placed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import qmc
from scipy.spatial.distance import pdist

from sample import PARAM_RANGES, INT_PARAMS, evaluate_row

METHODS = ["Random", "LHS", "Optimised LHS", "Sobol", "Halton"]
NAMES = list(PARAM_RANGES)
D = len(NAMES)
LO = np.array([PARAM_RANGES[k][0] for k in NAMES], dtype=float)
HI = np.array([PARAM_RANGES[k][1] for k in NAMES], dtype=float)


def unit_sample(method: str, n: int, seed: int, d: int = D) -> np.ndarray:
    """n points in [0, 1)^d from one of the five methods."""
    if method == "Random":
        return np.random.default_rng(seed).random((n, d))
    if method == "LHS":
        return qmc.LatinHypercube(d=d, seed=seed).random(n)
    if method == "Optimised LHS":
        return qmc.LatinHypercube(d=d, seed=seed, optimization="random-cd").random(n)
    if method == "Sobol":
        return qmc.Sobol(d=d, scramble=True, seed=seed).random(n)   # warns if n is not a power of 2
    if method == "Halton":
        return qmc.Halton(d=d, scramble=True, seed=seed).random(n)
    raise ValueError(f"unknown method {method!r}; choose from {METHODS}")


def scale_inputs(U: np.ndarray) -> pd.DataFrame:
    """Map unit-cube points to the real input ranges (value = min + u * (max - min))."""
    df = pd.DataFrame(qmc.scale(U, LO, HI), columns=NAMES)
    for k in INT_PARAMS:
        df[k] = df[k].round().astype(int)
    return df


def generate_dataset(method: str, n: int, seed: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Inputs + every calculator output, and the unit-cube points (for space-filling checks)."""
    U = unit_sample(method, n, seed)
    X = scale_inputs(U)
    Y = pd.DataFrame([evaluate_row(r) for _, r in X.iterrows()])
    df = pd.concat([X, Y], axis=1)
    df.insert(0, "method", method)
    return df, U


def space_filling_metrics(U: np.ndarray, n_dist: int = 2000, seed: int = 0) -> dict:
    """Verification of the sampling plan itself (no ETTV involved).
    - centred L2 discrepancy: how far the point set is from perfectly uniform (lower = more even)
    - empty-slice fraction: share of the n equal slices of each input that hold no point (0 for LHS by design)
    - min / mean nearest-neighbour distance on a subset (higher min = fewer clumps)"""
    n, d = U.shape
    slices = np.floor(U * n).astype(int)
    empty = np.mean([1 - len(np.unique(slices[:, j])) / n for j in range(d)])
    rng = np.random.default_rng(seed)
    sub = U[rng.choice(n, size=min(n_dist, n), replace=False)]
    dist = pdist(sub)
    m = len(sub)
    # nearest-neighbour distance for each point from the condensed distance matrix
    full = np.full((m, m), np.inf)
    iu = np.triu_indices(m, 1)
    full[iu] = dist
    full = np.minimum(full, full.T)
    nn = full.min(axis=1)
    return {"centred L2 discrepancy": float(qmc.discrepancy(U, method="CD")),
            "empty slices per input": float(empty),
            "min NN distance": float(nn.min()),
            "mean NN distance": float(nn.mean())}
