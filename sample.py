"""
sample.py — generate a synthetic ETTV dataset with Latin Hypercube Sampling (LHS).

Design space: a rectangular box building ("massing") with 4 facades.
    face 1 faces `rotation_deg` (0 = North), face 2 = +90°, face 3 = +180°, face 4 = +270°
    faces 1 & 3 are `length_m` wide, faces 2 & 4 are `width_m` wide.

The "area takeoff" is done exactly by geometry here — no ML needed for that part.

Usage:
    python sample.py --n 10000 --seed 42 --out data/ettv_dataset.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import qmc

from ettv import Facade, building_ettv, ETTV_LIMIT

# ---------------------------------------------------------------------------------
# Parameter ranges (ASSUMPTIONS — adjust to your project's scope)
# ---------------------------------------------------------------------------------
PARAM_RANGES = {
    # massing
    "length_m":       (20.0, 80.0),
    "width_m":        (20.0, 60.0),
    "storeys":        (5, 40),        # integer
    "floor_height_m": (3.6, 4.2),
    "rotation_deg":   (0.0, 360.0),
    # facade, per face (independent WWR and overhang on each face)
    "wwr_1": (0.2, 0.8), "wwr_2": (0.2, 0.8), "wwr_3": (0.2, 0.8), "wwr_4": (0.2, 0.8),
    "r1_1":  (0.0, 1.0), "r1_2":  (0.0, 1.0), "r1_3":  (0.0, 1.0), "r1_4":  (0.0, 1.0),
    # materials, same on all faces
    "u_wall": (0.4, 2.5),   # insulated panel .. uninsulated masonry/concrete
    "u_fen":  (1.4, 5.8),   # low-e double glazing .. single clear glass
    "sc1":    (0.2, 0.9),   # high-performance tinted/low-e .. clear glass
}
INT_PARAMS = {"storeys"}


def lhs_sample(n: int, seed: int) -> pd.DataFrame:
    names = list(PARAM_RANGES)
    lo = np.array([PARAM_RANGES[k][0] for k in names], dtype=float)
    hi = np.array([PARAM_RANGES[k][1] for k in names], dtype=float)
    sampler = qmc.LatinHypercube(d=len(names), seed=seed)
    X = qmc.scale(sampler.random(n), lo, hi)
    df = pd.DataFrame(X, columns=names)
    for k in INT_PARAMS:
        df[k] = df[k].round().astype(int)
    return df


def evaluate_row(r: pd.Series) -> dict:
    h = r.storeys * r.floor_height_m
    widths = [r.length_m, r.width_m, r.length_m, r.width_m]
    facades = [
        Facade(azimuth_deg=(r.rotation_deg + 90 * i) % 360,
               gross_area=widths[i] * h,
               wwr=r[f"wwr_{i+1}"], u_wall=r.u_wall, u_fen=r.u_fen,
               sc1=r.sc1, overhang_r1=r[f"r1_{i+1}"])
        for i in range(4)
    ]
    res = building_ettv(facades)
    out = {"ettv": res["ettv"], "q_wall": res["q_wall"], "q_fen": res["q_fen"],
           "q_solar": res["q_solar"], "passes": res["passes"]}
    for i, t in enumerate(res["per_facade"], start=1):
        out[f"orient_{i}"] = t["orientation"]
        out[f"ettv_{i}"] = t["ettv"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default="data/ettv_dataset.csv")
    a = ap.parse_args()

    X = lhs_sample(a.n, a.seed)
    Y = pd.DataFrame([evaluate_row(r) for _, r in X.iterrows()])
    df = pd.concat([X, Y], axis=1)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(f"Wrote {len(df):,} rows -> {a.out}")
    print(f"ETTV range {df.ettv.min():.1f}–{df.ettv.max():.1f} W/m2, "
          f"{df.passes.mean():.0%} pass the {ETTV_LIMIT:.0f} W/m2 limit")


if __name__ == "__main__":
    main()
