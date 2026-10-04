"""Tests for sampling_methods.py (v3).  Run: python test_sampling.py"""
import warnings
import numpy as np
from sampling_methods import METHODS, unit_sample, scale_inputs, space_filling_metrics, NAMES
from sample import PARAM_RANGES, lhs_sample
warnings.filterwarnings("ignore")


def test_all_methods_shape_and_unit_cube():
    for m in METHODS:
        U = unit_sample(m, 128, 0)
        assert U.shape == (128, len(NAMES)), m
        assert (U >= 0).all() and (U < 1).all(), m


def test_scaled_inputs_inside_ranges():
    for m in METHODS:
        X = scale_inputs(unit_sample(m, 128, 1))
        for k, (lo, hi) in PARAM_RANGES.items():
            assert X[k].between(lo, hi).all(), (m, k)


def test_lhs_fills_every_slice():
    for m in ("LHS", "Optimised LHS"):
        assert space_filling_metrics(unit_sample(m, 200, 0))["empty slices per input"] == 0, m


def test_random_leaves_gaps():
    assert space_filling_metrics(unit_sample("Random", 200, 0))["empty slices per input"] > 0.2


def test_lhs_matches_v2_sampler():
    """sampling_methods 'LHS' must give exactly the v1/v2 dataset inputs for the same seed."""
    a = lhs_sample(50, 42)
    b = scale_inputs(unit_sample("LHS", 50, 42))
    assert np.allclose(a.values.astype(float), b.values.astype(float))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
