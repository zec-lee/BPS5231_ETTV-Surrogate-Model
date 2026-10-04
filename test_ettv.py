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


# ---- Appendix D full ETTV example (v5) ---------------------------------------------
# The worked example prints CF = 0.58 (S), 0.77 (E), 0.57 (N), 0.87 (W), which do NOT match Table C1
# (0.83, 1.13, 0.80, 1.23). The CORRECT result uses Table C1: 61.0 W/m2, which fails the 50 W/m2 limit.
from bca_examples import appendix_d, PRINTED_RESULT


def test_appendix_D_correct_table_c1():
    """Our result for the Appendix D building, with the correct Table C1 CFs."""
    r = appendix_d("table_c1")
    for o, target in {"S": 56.2, "E": 68.1, "N": 50.3, "W": 71.3}.items():
        assert close(r[o], target, 0.06), (o, r[o])
    assert close(r["overall"], 61.0, 0.06), r["overall"]
    assert r["overall"] > 50.0                      # the building does NOT comply


def test_appendix_D_arithmetic_check_with_printed_cfs():
    """Substituting the example's own (wrong) CFs reproduces the printed numbers, so our arithmetic matches."""
    r = appendix_d("printed")
    for o in "SENW":
        assert close(r[o], PRINTED_RESULT[o], 0.06), (o, r[o])
    assert close(r["overall"], PRINTED_RESULT["overall"], 0.06), r["overall"]   # 48.15 vs printed 48.2


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
    print("\nAppendix D, Table C1 CFs (correct):", {k: round(float(v), 2) for k, v in appendix_d("table_c1").items()})
    print("Appendix D, printed CFs (check)    :", {k: round(float(v), 2) for k, v in appendix_d("printed").items()})
