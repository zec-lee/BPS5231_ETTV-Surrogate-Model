# ETTV Surrogate Model — BPS5231

A pipeline that generates a synthetic ETTV dataset with the BCA method, explores it, and trains a first surrogate model.

| File | What it does |
|---|---|
| `bca_tables.py` | BCA Table C1 (CF for walls) and Tables C12–C15 (SC2 of horizontal projections), transcribed from the code |
| `ettv.py` | ETTV calculator: CF interpolation, SC2 lookup, per-façade and area-weighted building ETTV |
| `sample.py` | Latin Hypercube sampling of box massing and façade parameters → `data/ettv_dataset.csv` |
| `test_ettv.py` | Checks against the BCA code's worked examples (B5.1, B5.2, D1.4 and the full Appendix D building) |
| `ettv_surrogate_walkthrough.ipynb` | Step-by-step guide covering sampling, EDA, features, split, 5 models, evaluation, importance and a learning curve |
| `figures/` | Charts exported from the notebook for the interim report |

Quick start: `pip install -r requirements.txt && python test_ettv.py && python sample.py --n 10000`, then open the notebook.

## Validation against the BCA code
- SC2 lookups reproduce examples B5.1 (0.698, 0.669), B5.2 (0.5051, 0.8123 by interpolation) and D1.4 (0.68 S, 0.58 E).
- The Appendix D office building is reproduced exactly: S 44.7, E 52.1, N 41.6, W 55.6, overall **48.2 W/m²**.

### ⚠️ Discrepancy found in the code
Appendix D uses CF = 0.58 (S), 0.77 (E), 0.57 (N), 0.87 (W), but **Table C1** gives 0.83, 1.13, 0.80 and 1.23 for vertical walls.
With the Table C1 values, the same building scores **61.0 W/m² and fails** the 50 W/m² limit.
**Confirmed:** the Appendix D CF values are wrong and Table C1 is correct. This dataset uses Table C1.
Two further typos in the example: the West Ao is listed as 2356.1 m² in the summary but 1785 m² in the calculation (1785 is correct), and R1 prints as "0.1" where 3.6/3.6 = 1.0.

## Assumptions
1. **Formula:** ETTV = 12(1−WWR)Uw + 3.4(WWR)Uf + 211(WWR)(CF)(SC), area-weighted by gross wall area per orientation (Sections 5.1–5.3).
2. **Limit:** 50 W/m² (Section 4.2). Green Mark schemes may be stricter.
3. **CF:** Table C1, interpolated linearly between the 8 orientations and between pitch angles, as the Table C1 note permits.
4. **SC2 table choice:** nearest primary orientation (±22.5°). The code gives no rule for interpolating SC2 between orientations, so SC2 jumps at those boundaries.
5. **Shading:** continuous horizontal overhang at window head level only (Tables C12–C15), with R1 clamped at 3.0. Fins (C16–C19) and egg-crates (C20–C23) are not used yet.
6. **Geometry:** rectangular box with 4 vertical façades and the same wall and glass specification on every face. WWR and overhang depth vary per face; one overhang inclination applies to all faces.
7. **Parameter ranges** (`PARAM_RANGES`), anchored to the code's examples where possible:
   - WWR 0.2–0.8 (the Appendix D tower is ≈0.44)
   - U_wall 0.5–3.0 W/m²K (Appendix D walls: 1.93–2.99)
   - U_fen 1.6–5.8 W/m²K (Appendix D: 5.82 single, 2.96 double; 1.6 is my assumption for low-e double glazing)
   - SC1 0.25–0.75 (code examples: 0.47–0.70; 0.25 is my assumption for high-performance glass)
   - R1 0–1.5, inclination 0–30°
8. **U-values are inputs directly; k-values (Table C5) are not.** ETTV depends on materials only through U = 1/(Ro + Σb/k + Ri) (Appendix A2), so U carries all the information. A layer-by-layer U calculator could be added as a deterministic front end.
9. **U_fen and SC1 are sampled independently.** Real products correlate them, so some combinations are unrealistic.

## Sources
- Building and Construction Authority (BCA), Singapore. *Code on Envelope Thermal Performance for Buildings*. Formula (§5), CF Table C1, SC2 Tables C12–C15, SC2 calculation method (Appendix B2), worked examples (B5, Appendix D). Provided by the user.
- Chou, S.K., Liew, H.T., Ko, J.R. & Goh, A. (2007). *Envelope Thermal Transfer Value criterion for buildings in Singapore*. BCA project report. Cited in the code's bibliography as the basis of ETTV.
- McKay, M.D., Beckman, R.J. & Conover, W.J. (1979). A comparison of three methods for selecting values of input variables in the analysis of output from a computer code. *Technometrics*, 21(2). The origin of Latin Hypercube Sampling.
- Westermann, P. & Evins, R. (2019). Surrogate modelling for sustainable building design – A review. *Energy and Buildings*, 198. Not verified online this session.
- SciPy (`scipy.stats.qmc.LatinHypercube`) and scikit-learn documentation.
