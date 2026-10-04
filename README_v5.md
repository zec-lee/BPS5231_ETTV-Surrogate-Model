# ETTV Surrogate Model — BPS5231 (v5)

A pipeline that generates a synthetic ETTV dataset with the BCA method, explores it, and trains a surrogate model
that predicts a design's **actual ETTV** in W/m². Predictions are never capped or forced towards 50 W/m². The limit
is only used afterwards to flag whether a design complies.

## Changes in v5 (from v4)
- **Appendix D now reports the correct result, 61.0 W/m² (fails the 50 W/m² limit).** The code's worked example prints
  48.2 W/m², but it uses solar correction factors that contradict Table C1. Our calculator uses Table C1:
  S 56.2, E 68.1, N 50.3, W 71.3, overall **61.0 W/m²**. The printed 48.2 W/m² is kept only as an arithmetic check
  (substituting the example's wrong CFs gives 48.15 W/m²).
- **New `bca_examples.py`:** all BCA worked-example inputs in one place, `appendix_d(cf="table_c1" | "printed")`,
  `validation_table()` and `AUDIT_NOTES` (every discrepancy found in Appendix D).
- **`test_ettv.py`:** `test_appendix_D_correct_table_c1` asserts 61.0 W/m² and non-compliance;
  `test_appendix_D_arithmetic_check_with_printed_cfs` replaces the old test that asserted 48.2 as "reproduced".
- **Notebook §1b (new):** validation table against the BCA examples and the Appendix D audit notes.
- **Audit:** the whole notebook was re-executed; every other number is unchanged from v4.
- **Unchanged:** `ettv.py`, `bca_tables.py`, `sample.py`, `sampling_methods.py`, `compare_sampling.py`, `test_sampling.py`, all datasets.

## Changes in v4 (from v3)
- **Parity plots for all five surrogate models (§6.1, `08b_parity_by_model.png`).** Each panel shows that model's own
  **borderline band** (orange shading) and highlights **pass/fail-flipped** designs as orange dots, with residual
  histograms below. A table gives each model's band, coverage, flips, flips caught by the band, silent flips, and the
  share of designs flagged borderline.
- **Conference-style parity figure for the selected model (`08_parity.png`):** (a) test set with band and flips,
  (b) residuals with band.
- **Learning curves for all five models (§8, `10_learning_curve.png`):** 7 training sizes × 3 seeds, with error bars,
  showing (a) validation MAE and (b) pass/fail accuracy.
- **The borderline band is now calibrated on the validation set,** not the test set. It is ±3.35 W/m² (v2/v3: ±3.4) and
  covers 94.5% of the unseen test set. A new "Why this band width?" section compares the 80th, 90th, 95th and 99th
  percentiles and 2 × RMSE.
- **The Part B parity plots (§15.2, `21_parity_by_method.png`)** also show bands and flips, with each band calibrated
  on that method's held-out 15%.
- **All saved figures are at 300 dpi** (v3: 110 dpi).
- **Unchanged:** all `.py` files. Only the notebook and README changed.

## Changes in v3 (from v2)
- **All five sampling methods are now in the notebook (Part B, §12–§16):** Random, LHS, Optimised LHS, Sobol and Halton,
  with n = 8,192 each (a power of 2 for Sobol).
  - **Verification of the sampling plans (§13):** centred L2 discrepancy, empty slices per input, nearest-neighbour
    distances, and a 2-D projection figure.
  - **Verification of the data (§12, §14):** the §3 EDA graphs repeated for every method (input coverage, ETTV
    distribution, component share, Spearman sensitivity, orientation, WWR × SC1, rotation), plus a KS test against LHS.
  - **Validation of the surrogates (§15):** learning curves for 128 / 512 / 2,048 samples × 4 seeds × 2 models, and
    full-size parity and residual plots. All are tested on one common independent test set, with the neural net trained
    on 3 seeds so that initialisation luck isn't mistaken for a sampling effect.
  - **Conclusions (§16).**
- **New `sampling_methods.py`:** the five methods, scaling to `PARAM_RANGES`, dataset generation and space-filling metrics.
- **New `test_sampling.py`:** checks ranges, LHS slice coverage, and that "LHS" reproduces the v1/v2 sampler exactly.
- **`sample.py`:** new `--method` option. The default stays LHS, so the Part A dataset is identical to v2.
- **`compare_sampling.py`:** rewritten to use `sampling_methods.py`. It now also records pass/fail accuracy, and the
  notebook imports it, so the script and the notebook can't drift apart.
- **New figures 12–21** in `figures/`, and new datasets `data/ettv_dataset_<method>.csv`.
- **Unchanged:** `ettv.py`, `bca_tables.py`, `test_ettv.py`, and all of Part A's results.
- **Runtime:** about 8 minutes for the whole notebook, of which Part B is about 6.

## Changes in v2 (from v1)
- **Compliance check (notebook §9):** `assess_design()` returns the predicted ETTV and a status: ✅ COMPLIES,
  ⚠️ BORDERLINE or ❌ EXCEEDS by X W/m². The borderline band (±3.4 W/m²) is the 95th percentile of test-set errors.
  It also warns when inputs are outside the training ranges, or the prediction is beyond the ETTV range seen in training.
- **Feature engineering (§4)** is explained in more depth, and a new **ablation study (§6.2)** measures how much each step helps.
- Notebook renamed `ettv_surrogate_walkthrough_v2.ipynb`; this file renamed `README_v2.md`.
- Unchanged from v1: `ettv.py`, `bca_tables.py`, `sample.py`, `test_ettv.py`, `compare_sampling.py` and the dataset.

| File | What it does |
|---|---|
| `bca_tables.py` | BCA Table C1 (CF for walls) and Tables C12–C15 (SC2 of horizontal projections), transcribed from the code |
| `ettv.py` | ETTV calculator: CF interpolation, SC2 lookup, per-façade and area-weighted building ETTV |
| `sample.py` | Latin Hypercube sampling of box massing and façade parameters → `data/ettv_dataset.csv` |
| `sampling_methods.py` | The five sampling methods (Random, LHS, Optimised LHS, Sobol, Halton), dataset generation and space-filling metrics |
| `test_sampling.py` | Tests for the sampling methods |
| `compare_sampling.py` | Trains the same surrogates on data from 5 sampling methods (random, LHS, optimised LHS, Sobol, Halton) and compares test error → `data/sampling_comparison.csv` |
| `bca_examples.py` | BCA worked-example inputs, Appendix D evaluated with Table C1 (correct, 61.0 W/m²) or printed CFs (check), audit notes |
| `test_ettv.py` | Checks against the BCA code's worked examples (B5.1, B5.2, D1.4) and the corrected Appendix D result (61.0 W/m²) |
| `ettv_surrogate_walkthrough_v5.ipynb` | Part A: step-by-step pipeline on LHS data (EDA, feature engineering and ablation, 5 models, evaluation, importance, learning curve, compliance check). Part B: the 5 sampling methods compared, with verification EDA and validation |
| `figures/` | Charts exported from the notebook for the interim report |

Quick start: `pip install -r requirements.txt && python test_ettv.py && python test_sampling.py && python sample.py --n 10000`, then open the notebook. On Colab, upload `ettv.py`, `sample.py`, `bca_tables.py`, `sampling_methods.py`, `compare_sampling.py` and `bca_examples.py` next to the notebook (its first cell prompts you).

## Validation against the BCA code
- SC2 lookups reproduce examples B5.1 (0.698, 0.669), B5.2 (0.5051, 0.8123 by interpolation) and D1.4 (0.68 S, 0.58 E).
- **Appendix D office building, correct result (Table C1 CFs): S 56.2, E 68.1, N 50.3, W 71.3, overall 61.0 W/m² — fails the 50 W/m² limit.**
- Arithmetic check: with the example's printed (wrong) CFs, the calculator returns S 44.7, E 52.1, N 41.6, W 55.6,
  overall 48.15 W/m², matching the printed 48.2 W/m². So the only difference is the CFs.

### ⚠️ Discrepancy found in the code
Appendix D uses CF = 0.58 (S), 0.77 (E), 0.57 (N), 0.87 (W), but **Table C1** gives 0.83, 1.13, 0.80 and 1.23 for vertical walls.
With the Table C1 values, the same building scores **61.0 W/m² and fails** the 50 W/m² limit.
**Confirmed:** the Appendix D CF values are wrong and Table C1 is correct. This dataset uses Table C1.
Further discrepancies in the example (all in `bca_examples.AUDIT_NOTES`):
- West Ao listed as 2,356.1 m² in the summary but 1,785 m² in the calculation (1,785 is correct).
- R1 prints as "0.1" where 3.6/3.6 = 1.0.
- D1.2.2: north wall "3.7 × (20 + 3.6) × 2 = 74.6 m²"; the product is 174.6 m², as used in the summary.
- East Aw4 used as 640 m² (summary 640.4); South r.c. beam U used as 2.7 (D1.3: 2.71). Negligible.
- U-values recomputed from the listed layers: double glazing 2.95 (printed 2.96), clad r.c. beam 1.97 (printed 1.98);
  with these the corrected result is 60.99 instead of 61.04 W/m².
- Brick parapet (D1.3 c): the layers as listed sum to R = 0.635 m²K/W (U = 1.57), not the printed R = 0.519 (U = 1.93).
  The printed U = 1.93 is used; with U = 1.57 the building would score 59.8 W/m², which still fails. Check the original page.

## Assumptions
1. **Formula:** ETTV = 12(1−WWR)Uw + 3.4(WWR)Uf + 211(WWR)(CF)(SC), area-weighted by gross wall area per orientation (Sections 5.1–5.3).
2. **Limit:** 50 W/m² (Section 4.2), used only to label predictions, never to constrain them. Green Mark schemes may be stricter; change `ETTV_LIMIT` in `ettv.py` to use another limit.
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
