"""
bca_examples.py — the BCA code's worked examples, used to validate the calculator (new in v5).

Appendix D (25-storey office building) is evaluated two ways:

  * cf="table_c1"  (DEFAULT, the correct result): solar correction factors from Table C1 for vertical walls
                    (S 0.83, E 1.13, N 0.80, W 1.23). Result: S 56.2, E 68.1, N 50.3, W 71.3, overall 61.0 W/m2,
                    which EXCEEDS the 50 W/m2 limit.
  * cf="printed"    (arithmetic check only): the CFs printed in the example (S 0.58, E 0.77, N 0.57, W 0.87).
                    These do not match Table C1 and are wrong. Using them reproduces the printed values
                    (44.7, 52.1, 41.6, 55.6, overall 48.2 W/m2), which shows our arithmetic matches the code's.

Areas, U-values and SC values are exactly as printed in Appendix D (D1.2-D1.5), with two known typos corrected
(see AUDIT_NOTES): the West gross area is 1,785 m2 (the summary table prints 2,356.1), and the overhang R1 is
3.6/3.6 = 1.0 (printed as "0.1").
"""
from bca_tables import CF_WALL_ETTV
from ettv import ettv_facade_general, sc2_horizontal

CF_PRINTED = {"S": 0.58, "E": 0.77, "N": 0.57, "W": 0.87}           # as printed in D1.5 (wrong)
CF_TABLE_C1 = {o: float(CF_WALL_ETTV.loc[90, o]) for o in "SENW"}  # Table C1, pitch 90° (correct)

# SC2 of the 1st-storey overhang (D1.4): R1 = 3.6 / 3.6 = 1.0. The code prints 0.68 (S) and 0.58 (E).
SC2_S, SC2_E = 0.68, 0.58

# Per facade: gross area Ao, walls [(area m2, U)], fenestration [(area m2, U, SC = SC1 x SC2)], as printed
APPENDIX_D = {
    "S": dict(Ao=2356.1, walls=[(49.5, 2.7), (507.5, 1.98), (684.4, 1.93)],
              fens=[(162.0, 5.82, 0.61 * SC2_S), (952.7, 2.96, 0.47)]),
    "E": dict(Ao=2100.0, walls=[(24.2, 2.71), (471.5, 1.98), (640.0, 1.93)],
              fens=[(79.2, 5.82, 0.61 * SC2_E), (884.7, 2.96, 0.47)]),
    "N": dict(Ao=2053.6, walls=[(268.6, 2.99), (420.0, 1.98), (577.5, 1.93)],
              fens=[(787.5, 2.96, 0.47)]),
    "W": dict(Ao=1785.0, walls=[(420.0, 1.98), (577.5, 1.93)],
              fens=[(787.5, 2.96, 0.47)]),
}
PRINTED_RESULT = {"S": 44.7, "E": 52.1, "N": 41.6, "W": 55.6, "overall": 48.2}


def appendix_d(cf: str = "table_c1") -> dict:
    """ETTV of the Appendix D building per facade and overall (W/m2). cf = 'table_c1' (correct) or 'printed'."""
    cfs = {"table_c1": CF_TABLE_C1, "printed": CF_PRINTED}[cf]
    out = {o: ettv_facade_general(d["walls"], d["fens"], cfs[o], d["Ao"])["ettv"] for o, d in APPENDIX_D.items()}
    A = {o: d["Ao"] for o, d in APPENDIX_D.items()}
    out["overall"] = sum(A[o] * out[o] for o in A) / sum(A.values())
    return out


def validation_table():
    """Rows (example, case, BCA printed value, this work) for reports and the notebook."""
    d_ok, d_chk = appendix_d("table_c1"), appendix_d("printed")
    return [
        ("B5.1(a)", "SC2, SW overhang, R1 = 0.5, φ = 0°", 0.698, round(sc2_horizontal("SW", 0.5, 0), 4)),
        ("B5.1(b)", "SC2, SW overhang, R1 = 0.4, φ = 30°", 0.669, round(sc2_horizontal("SW", 0.4, 30), 4)),
        ("B5.2", "SC2, W overhang, R1 = 1.5", 0.5051, round(sc2_horizontal("W", 1.5), 4)),
        ("B5.2", "SC2, W overhang, R1 = 0.32 (interpolated)", 0.8123, round(sc2_horizontal("W", 0.32), 4)),
        ("D1.4", "SC2, S overhang, R1 = 1.0", 0.68, round(sc2_horizontal("S", 1.0), 2)),
        ("D1.4", "SC2, E overhang, R1 = 1.0", 0.58, round(sc2_horizontal("E", 1.0), 2)),
        ("App. D", "Building ETTV, Table C1 CFs (correct)", PRINTED_RESULT["overall"], round(d_ok["overall"], 1)),
        ("App. D", "Building ETTV, printed CFs (arithmetic check)", PRINTED_RESULT["overall"], round(d_chk["overall"], 2)),
    ]


AUDIT_NOTES = [
    "D1.5: CFs printed as S 0.58, E 0.77, N 0.57, W 0.87; Table C1 gives 0.83, 1.13, 0.80, 1.23. With Table C1 the "
    "building scores 61.0 W/m2 (fails), not 48.2 W/m2.",
    "Summary of envelope area: West Ao printed as 2,356.1 m2; the calculation (and the sum of its parts) is 1,785 m2.",
    "D1.4: R1 printed as '0.1'; 3.6/3.6 = 1.0, and the SC2 values used (0.68, 0.58) are the R1 = 1.0 table values.",
    "D1.2.2: North wall printed as '3.7 x (20 + 3.6) x 2 = 74.6 m2'; the product is 174.6 m2, as used in the summary.",
    "D1.5 East: Aw4 used as 640 m2 (summary: 640.4 m2); South r.c. beam U used as 2.7 (D1.3: 2.71). Negligible.",
    "D1.3 U-values recomputed from the listed layers: double glazing 2.95 (printed 2.96), clad r.c. beam 1.97 "
    "(printed 1.98). Using recomputed U-values changes the corrected result from 61.04 to 60.99 W/m2.",
    "D1.3(c) brick parapet: the layers as listed in the PDF text sum to R = 0.635 m2K/W (U = 1.57), not the printed "
    "R = 0.519 (U = 1.93). The printed U = 1.93 is used here; check the original page.",
]

if __name__ == "__main__":
    for r in validation_table():
        print(f"{r[0]:8s} {r[1]:48s} BCA {r[2]:>7}  this work {r[3]:>7}")
    print("\nAppendix D, Table C1 CFs:", {k: round(v, 1) for k, v in appendix_d('table_c1').items()})
    print("Appendix D, printed CFs :", {k: round(v, 1) for k, v in appendix_d('printed').items()})
