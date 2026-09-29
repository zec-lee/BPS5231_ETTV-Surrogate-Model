"""Tests for ettv.py against the BCA code's own worked examples.  Run: python test_ettv.py"""
import math
import numpy as np
from ettv import (Facade, ettv_terms, building_ettv, azimuth_to_orientation, sc2_horizontal,
                  correction_factor, ettv_facade_general)
from bca_tables import SC2_HORIZ, CF_WALL_ETTV

close = lambda a, b, tol: abs(a - b) <= tol


# ---- Table transcription sanity ----------------------------------------------------
def test_sc2_tables_non_increasing_in_r1():
    """More projection should never let in more sun. Catches most typing errors."""
    for o, t in SC2_HORIZ.items():
        assert (np.diff(t.values, axis=0) <= 1e-9).all(), o


def test_cf_table_c1_vertical_row():
    assert CF_WALL_ETTV.loc[90].tolist() == [0.80, 0.97, 1.13, 0.98, 0.83, 1.06, 1.23, 1.03]


# ---- SC2 lookups vs code examples --------------------------------------------------
def test_example_B51_southwest_overhang():
    assert close(sc2_horizontal("SW", 0.5, 0), 0.698, 5e-4)    # (a)
    assert close(sc2_horizontal("SW", 0.4, 30), 0.669, 5e-4)   # (b)


def test_example_B52_west_interpolation():
    assert close(sc2_horizontal("W", 1.5), 0.5051, 1e-4)
    assert close(sc2_horizontal("W", 0.32), 0.8123, 1e-4)      # code interpolates to 0.8123


def test_example_D14_overhang():
    assert close(sc2_horizontal("S", 1.0), 0.68, 5e-3)
    assert close(sc2_horizontal("E", 1.0), 0.58, 5e-3)


# ---- Appendix D full ETTV example --------------------------------------------------
# NOTE: the worked example uses CF = 0.58 (S), 0.77 (E), 0.57 (N), 0.87 (W), which do NOT
# match Table C1 (0.83, 1.13, 0.80, 1.23). We reproduce it with the example's own CFs.
APPX_D = {
    "S": dict(cf=0.58, Ao=2356.1, target=44.7,
              walls=[(49.5, 2.7), (507.5, 1.98), (684.4, 1.93)],
              fens=[(162, 5.82, 0.61 * 0.68), (952.7, 2.96, 0.47)]),
    "E": dict(cf=0.77, Ao=2100.0, target=52.1,
              walls=[(24.2, 2.71), (471.5, 1.98), (640, 1.93)],
              fens=[(79.2, 5.82, 0.61 * 0.58), (884.7, 2.96, 0.47)]),
    "N": dict(cf=0.57, Ao=2053.6, target=41.6,
              walls=[(268.6, 2.99), (420, 1.98), (577.5, 1.93)],
              fens=[(787.5, 2.96, 0.47)]),
    "W": dict(cf=0.87, Ao=1785.0, target=55.6,
              walls=[(420, 1.98), (577.5, 1.93)],
              fens=[(787.5, 2.96, 0.47)]),
}


def appendix_d(cf_override=None):
    res = {}
    for o, d in APPX_D.items():
        cf = d["cf"] if cf_override is None else cf_override[o]
        res[o] = ettv_facade_general(d["walls"], d["fens"], cf, d["Ao"])["ettv"]
    A = {o: d["Ao"] for o, d in APPX_D.items()}
    res["overall"] = sum(A[o] * res[o] for o in A) / sum(A.values())
    return res


def test_appendix_D_reproduced():
    r = appendix_d()
    for o, d in APPX_D.items():
        assert close(r[o], d["target"], 0.15), (o, r[o])
    assert close(r["overall"], 48.2, 0.15), r["overall"]


# ---- Core behaviour ----------------------------------------------------------------
def test_hand_calc_single_facade():
    f = Facade(azimuth_deg=0, gross_area=100, wwr=0.4, u_wall=2.0, u_fen=5.8, sc1=0.5)
    assert math.isclose(ettv_terms(f)["ettv"], 12 * 0.6 * 2.0 + 3.4 * 0.4 * 5.8 + 211 * 0.4 * 0.80 * 0.5)


def test_cf_interpolation():
    assert close(correction_factor(0), 0.80, 1e-9)
    assert close(correction_factor(22.5), (0.80 + 0.97) / 2, 1e-9)
    assert close(correction_factor(337.5), (1.03 + 0.80) / 2, 1e-9)   # wraps NW -> N
    assert close(correction_factor(22.5, interpolate=False), 0.97, 1e-9)
    assert close(correction_factor(0, pitch_deg=80), 0.98, 1e-9)


def test_orientation_bins():
    assert [azimuth_to_orientation(a) for a in (0, 22.4, 22.6, 90, 350, -90)] == ["N", "N", "NE", "E", "N", "W"]


def test_area_weighting():
    a, b = Facade(0, 300, 0.4, 1.0, 3.0, 0.5), Facade(90, 100, 0.4, 1.0, 3.0, 0.5)
    ea, eb = ettv_terms(a)["ettv"], ettv_terms(b)["ettv"]
    assert math.isclose(building_ettv([a, b])["ettv"], (300 * ea + 100 * eb) / 400)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
    r = appendix_d()
    print("\nAppendix D (example CFs):", {k: round(v, 2) for k, v in r.items()})
    c1 = {o: CF_WALL_ETTV.loc[90, o] for o in "SENW"}
    r2 = appendix_d(c1)
    print("Appendix D (Table C1 CFs):", {k: round(v, 2) for k, v in r2.items()})
