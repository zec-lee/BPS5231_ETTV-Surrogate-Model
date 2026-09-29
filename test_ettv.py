"""Sanity tests for ettv.py. Run: python -m pytest -q  (or python test_ettv.py)"""
import math
from ettv import Facade, ettv_terms, building_ettv, azimuth_to_orientation, sc2_overhang, CF_TABLE


def test_hand_calc_single_facade():
    f = Facade(azimuth_deg=0, gross_area=100, wwr=0.4, u_wall=2.0, u_fen=5.8, sc1=0.5)
    expected = 12 * 0.6 * 2.0 + 3.4 * 0.4 * 5.8 + 211 * 0.4 * CF_TABLE["N"] * 0.5
    assert math.isclose(ettv_terms(f)["ettv"], expected, rel_tol=1e-9)


def test_orientation_bins():
    assert azimuth_to_orientation(0) == "N"
    assert azimuth_to_orientation(22.4) == "N"
    assert azimuth_to_orientation(22.6) == "NE"
    assert azimuth_to_orientation(90) == "E"
    assert azimuth_to_orientation(350) == "N"
    assert azimuth_to_orientation(-90) == "W"


def test_no_glass_means_wall_only():
    f = Facade(azimuth_deg=270, gross_area=50, wwr=0.0, u_wall=1.5, u_fen=5.8, sc1=0.8)
    assert math.isclose(ettv_terms(f)["ettv"], 12 * 1.5)


def test_shading_reduces_ettv():
    base = Facade(90, 100, 0.5, 1.0, 3.0, 0.6, overhang_r1=0.0)
    shaded = Facade(90, 100, 0.5, 1.0, 3.0, 0.6, overhang_r1=0.8)
    assert ettv_terms(shaded)["ettv"] < ettv_terms(base)["ettv"]
    assert sc2_overhang("E", 0.0) == 1.0


def test_area_weighting():
    a = Facade(0, 300, 0.4, 1.0, 3.0, 0.5)
    b = Facade(90, 100, 0.4, 1.0, 3.0, 0.5)
    ea, eb = ettv_terms(a)["ettv"], ettv_terms(b)["ettv"]
    assert math.isclose(building_ettv([a, b])["ettv"], (300 * ea + 100 * eb) / 400)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
