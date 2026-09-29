"""
ettv.py — ETTV calculator (Singapore BCA method), written to generate training data
for a surrogate model.

Formula (BCA Code on Envelope Thermal Performance for Buildings):

    ETTV = 12 (1 - WWR) Uw  +  3.4 (WWR) Uf  +  211 (WWR) (CF) (SC)

    Uw  : U-value of opaque wall            [W/m2K]
    Uf  : U-value of fenestration (glazing) [W/m2K]
    WWR : window-to-wall ratio              [-]
    CF  : solar correction factor (depends on orientation and tilt) [-]
    SC  : shading coefficient = SC1 (glass) x SC2 (external shading) [-]

    12, 3.4 and 211 are the code's fixed coefficients. They are equivalent
    temperature differences / solar factor derived by BCA for Singapore's climate.

The ETTV of the whole building is the area-weighted average over all facades:

    ETTV_bldg = sum(A_i * ETTV_i) / sum(A_i)      (A_i = gross wall area of facade i)

-----------------------------------------------------------------------------------
!!  PLACEHOLDER VALUES  !!
CF_TABLE and SC2_OVERHANG_TABLE below are NOT the official BCA values. Web access
was unavailable when this was written, so they are made-up numbers in a plausible
range, there only so the pipeline runs. Replace them with the tables in the BCA
code before using any results in a submission.
-----------------------------------------------------------------------------------
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

# ---------------------------------------------------------------------------------
# 1. Code coefficients (these ARE the BCA formula constants)
# ---------------------------------------------------------------------------------
K_WALL = 12.0    # opaque wall conduction coefficient
K_FEN = 3.4      # fenestration conduction coefficient
K_SOLAR = 211.0  # solar radiation coefficient

ETTV_LIMIT = 50.0  # W/m2 — regulatory max for applicable non-residential buildings (verify vs. current code)

# ---------------------------------------------------------------------------------
# 2. Lookup tables — PLACEHOLDERS, replace from the BCA code
# ---------------------------------------------------------------------------------
ORIENTATIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]  # 45° apart, N = 0°

# CF for VERTICAL facades (tilt = 90°). PLACEHOLDER.
# Pattern assumed: E/W get more low-angle sun than N/S near the equator.
CF_TABLE = {
    "N": 0.80, "NE": 1.00, "E": 1.15, "SE": 1.00,
    "S": 0.85, "SW": 1.05, "W": 1.20, "NW": 1.05,
}

# SC2 for a HORIZONTAL OVERHANG as a function of R1 = projection depth / window height.
# The BCA code gives separate tables per orientation (and for fins / egg-crates).
# PLACEHOLDER: one curve for all orientations.
SC2_R1 = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.5])
SC2_OVERHANG_TABLE = {o: np.array([1.00, 0.84, 0.73, 0.65, 0.60, 0.57, 0.53]) for o in ORIENTATIONS}


# ---------------------------------------------------------------------------------
# 3. Helper functions
# ---------------------------------------------------------------------------------
def azimuth_to_orientation(azimuth_deg: float) -> str:
    """Assign a facade's outward-facing azimuth (0° = N, clockwise) to the nearest of
    8 orientations. ASSUMPTION: each orientation covers ±22.5°. Check the code's rule."""
    idx = int(((azimuth_deg % 360) + 22.5) // 45) % 8
    return ORIENTATIONS[idx]


def correction_factor(orientation: str) -> float:
    """CF for a vertical facade. (Tilted facades would need the code's tilt tables.)"""
    return CF_TABLE[orientation]


def sc2_overhang(orientation: str, r1: float) -> float:
    """SC2 for a horizontal overhang via linear interpolation of the table.
    Values beyond the table range are clamped to the end values."""
    return float(np.interp(r1, SC2_R1, SC2_OVERHANG_TABLE[orientation]))


# ---------------------------------------------------------------------------------
# 4. Core calculation
# ---------------------------------------------------------------------------------
@dataclass
class Facade:
    azimuth_deg: float      # outward normal direction, 0 = N, 90 = E
    gross_area: float       # m2, wall + window
    wwr: float              # 0..1
    u_wall: float           # W/m2K
    u_fen: float            # W/m2K
    sc1: float              # glass shading coefficient
    overhang_r1: float = 0  # projection / window height (0 = no shading)


def ettv_terms(f: Facade) -> dict:
    """ETTV for one facade, split into its three components (useful for EDA)."""
    orient = azimuth_to_orientation(f.azimuth_deg)
    cf = correction_factor(orient)
    sc2 = sc2_overhang(orient, f.overhang_r1)
    sc = f.sc1 * sc2
    wall = K_WALL * (1 - f.wwr) * f.u_wall
    fen = K_FEN * f.wwr * f.u_fen
    solar = K_SOLAR * f.wwr * cf * sc
    return {"orientation": orient, "cf": cf, "sc2": sc2, "sc": sc,
            "q_wall": wall, "q_fen": fen, "q_solar": solar,
            "ettv": wall + fen + solar}


def building_ettv(facades: list[Facade]) -> dict:
    """Area-weighted ETTV over all facades, plus area-weighted component breakdown."""
    areas = np.array([f.gross_area for f in facades])
    terms = [ettv_terms(f) for f in facades]
    w = areas / areas.sum()
    out = {k: float(np.dot(w, [t[k] for t in terms])) for k in ("q_wall", "q_fen", "q_solar", "ettv")}
    out["per_facade"] = terms
    out["passes"] = out["ettv"] <= ETTV_LIMIT
    return out


if __name__ == "__main__":
    # Worked example: one facade, check by hand
    f = Facade(azimuth_deg=0, gross_area=100, wwr=0.4, u_wall=2.0, u_fen=5.8, sc1=0.5, overhang_r1=0)
    t = ettv_terms(f)
    # Hand calc (CF_N placeholder 0.80, SC2 = 1.0):
    # wall  = 12 * 0.6 * 2.0        = 14.40
    # fen   = 3.4 * 0.4 * 5.8       =  7.888
    # solar = 211 * 0.4 * 0.80*0.5  = 33.76
    # total                          = 56.048 W/m2
    print(t)
