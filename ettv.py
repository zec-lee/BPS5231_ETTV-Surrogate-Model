"""
ettv.py — ETTV calculator following the BCA *Code on Envelope Thermal Performance for Buildings*.

Formula (Section 5.1):

    ETTV = 12 (1 - WWR) Uw  +  3.4 (WWR) Uf  +  211 (WWR) (CF) (SC)

    Uw  : U-value of opaque wall            [W/m2K]
    Uf  : U-value of fenestration (glazing) [W/m2K]
    WWR : window-to-wall ratio = fenestration area / gross exterior wall area
    CF  : solar correction factor, Table C1 (depends on orientation and pitch)
    SC  : shading coefficient = SC1 (glass, from manufacturer) x SC2 (external shading, Tables C12-C23)

With several wall or glass types on one facade (Section 5.2):

    ETTV_i = [12 Σ(Aw·Uw) + 3.4 Σ(Af·Uf) + 211·CF·Σ(Af·SC)] / Ao

Whole building (Section 5.3), area-weighted over orientations:

    ETTV = Σ(Ao_i · ETTV_i) / Σ Ao_i

Maximum permissible ETTV = 50 W/m2 (Section 4.2).
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from bca_tables import ORIENTATIONS, CF_WALL_ETTV, SC2_HORIZ

K_WALL, K_FEN, K_SOLAR = 12.0, 3.4, 211.0
ETTV_LIMIT = 50.0  # W/m2, Section 4.2


# ---------------------------------------------------------------------------------
# Orientation helpers
# ---------------------------------------------------------------------------------
def azimuth_to_orientation(azimuth_deg: float) -> str:
    """Nearest of the 8 primary orientations (each covers ±22.5°), 0° = N, clockwise.
    ASSUMPTION: used only to pick which SC2 table to read. The code gives SC2 tables
    for the 8 primary orientations only and doesn't say to interpolate between them."""
    idx = int(((azimuth_deg % 360) + 22.5) // 45) % 8
    return ORIENTATIONS[idx]


def correction_factor(azimuth_deg: float, pitch_deg: float = 90.0, interpolate: bool = True) -> float:
    """Table C1 CF. The code note permits interpolation for other orientations and pitch angles.
    interpolate=True : linear in azimuth between the two neighbouring primary orientations
                       (wrapping NW -> N), and linear in pitch.
    interpolate=False: nearest primary orientation (the ±22.5° rule)."""
    pitches = CF_WALL_ETTV.index.values.astype(float)
    if not pitches.min() <= pitch_deg <= pitches.max():
        raise ValueError(f"pitch {pitch_deg}° outside Table C1 range {pitches.min()}-{pitches.max()}°")
    # CF at this pitch for each of the 8 orientations
    cf8 = np.array([np.interp(pitch_deg, pitches, CF_WALL_ETTV[o].values) for o in ORIENTATIONS])
    if not interpolate:
        return float(cf8[ORIENTATIONS.index(azimuth_to_orientation(azimuth_deg))])
    az = azimuth_deg % 360
    angles = np.append(np.arange(0, 360, 45), 360.0)
    return float(np.interp(az, angles, np.append(cf8, cf8[0])))


# ---------------------------------------------------------------------------------
# SC2 of a horizontal projection (Tables C12-C15)
# ---------------------------------------------------------------------------------
def sc2_horizontal(orientation: str, r1: float, angle_deg: float = 0.0) -> float:
    """Bilinear interpolation in R1 = P/H and inclination angle phi1 (0-50°).
    R1 = 0 gives 1.0 (no shading). R1 > 3.0 is clamped to 3.0, where the tables have flattened out."""
    t = SC2_HORIZ[orientation]
    r1 = float(np.clip(r1, 0.0, 3.0))
    angles = t.columns.values.astype(float)
    if not angles.min() <= angle_deg <= angles.max():
        raise ValueError("inclination angle must be 0-50°")
    col = np.array([np.interp(angle_deg, angles, row) for row in t.values])  # SC2 vs R1 at this angle
    return float(np.interp(r1, t.index.values.astype(float), col))


# ---------------------------------------------------------------------------------
# General facade calculation (Section 5.2), used to validate against Appendix D
# ---------------------------------------------------------------------------------
def ettv_facade_general(walls, fens, cf: float, gross_area: float | None = None) -> dict:
    """walls: list of (area, U). fens: list of (area, U, SC) with SC = SC1*SC2.
    gross_area defaults to the sum of all wall and glass areas."""
    Ao = gross_area or (sum(a for a, _ in walls) + sum(a for a, _, _ in fens))
    q_wall = K_WALL * sum(a * u for a, u in walls) / Ao
    q_fen = K_FEN * sum(a * u for a, u, _ in fens) / Ao
    q_solar = K_SOLAR * cf * sum(a * sc for a, _, sc in fens) / Ao
    return {"q_wall": q_wall, "q_fen": q_fen, "q_solar": q_solar, "ettv": q_wall + q_fen + q_solar, "Ao": Ao}


# ---------------------------------------------------------------------------------
# Simple parametric facade (what sample.py uses)
# ---------------------------------------------------------------------------------
@dataclass
class Facade:
    azimuth_deg: float      # outward normal, 0 = N, 90 = E (clockwise)
    gross_area: float       # m2 (opaque wall + glass)
    wwr: float              # 0..1
    u_wall: float           # W/m2K
    u_fen: float            # W/m2K
    sc1: float              # glass shading coefficient
    overhang_r1: float = 0  # P/H of a continuous horizontal overhang at window head (0 = none)
    overhang_angle: float = 0.0  # inclination phi1, 0-50°
    pitch_deg: float = 90.0      # 90 = vertical wall


def ettv_terms(f: Facade, interpolate_cf: bool = True) -> dict:
    orient = azimuth_to_orientation(f.azimuth_deg)
    cf = correction_factor(f.azimuth_deg, f.pitch_deg, interpolate=interpolate_cf)
    sc2 = sc2_horizontal(orient, f.overhang_r1, f.overhang_angle)
    sc = f.sc1 * sc2
    wall = K_WALL * (1 - f.wwr) * f.u_wall
    fen = K_FEN * f.wwr * f.u_fen
    solar = K_SOLAR * f.wwr * cf * sc
    return {"orientation": orient, "cf": cf, "sc2": sc2, "sc": sc,
            "q_wall": wall, "q_fen": fen, "q_solar": solar, "ettv": wall + fen + solar}


def building_ettv(facades: list[Facade], interpolate_cf: bool = True) -> dict:
    areas = np.array([f.gross_area for f in facades])
    terms = [ettv_terms(f, interpolate_cf) for f in facades]
    w = areas / areas.sum()
    out = {k: float(np.dot(w, [t[k] for t in terms])) for k in ("q_wall", "q_fen", "q_solar", "ettv")}
    out["per_facade"] = terms
    out["passes"] = out["ettv"] <= ETTV_LIMIT
    return out


if __name__ == "__main__":
    f = Facade(azimuth_deg=0, gross_area=100, wwr=0.4, u_wall=2.0, u_fen=5.8, sc1=0.5)
    print(ettv_terms(f))  # 12*0.6*2 + 3.4*0.4*5.8 + 211*0.4*0.80*0.5 = 56.048
