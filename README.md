# ETTV Surrogate Model — BPS5231

A pipeline that generates a synthetic ETTV dataset, explores it, and trains a first surrogate model.

| File | What it does |
|---|---|
| `ettv.py` | ETTV calculator (BCA formula): orientation binning, CF and SC2 lookups, area-weighted building ETTV |
| `sample.py` | Latin Hypercube sampling of box-massing and façade parameters → `data/ettv_dataset.csv` |
| `test_ettv.py` | Sanity tests, including a hand-calculated example (`python test_ettv.py`) |
| `ettv_surrogate_walkthrough.ipynb` | Step-by-step guide covering sampling, EDA, features, split, 5 models, evaluation, importance and a learning curve |
| `figures/` | Charts exported from the notebook for the interim report |

Quick start: `pip install -r requirements.txt && python sample.py --n 10000`, then open the notebook. It also runs as-is on Colab.

## ⚠️ Must fix before submission
**CF and SC2 tables in `ettv.py` are PLACEHOLDERS.** Web access was unavailable when this was written.
Copy the real tables from the BCA code into `CF_TABLE` and `SC2_OVERHANG_TABLE`, then re-run the sampler and the notebook.

## Assumptions
1. **Formula:** ETTV = 12(1−WWR)Uw + 3.4(WWR)Uf + 211(WWR)(CF)(SC), area-weighted over façades. Check it against the current code edition.
2. **Limit:** 50 W/m² (non-residential). Green Mark 2021 may set a stricter target, so confirm.
3. **Orientation binning:** nearest of 8 orientations, each covering ±22.5°. Confirm the code's rule.
4. **Vertical façades only** (tilt 90°). No tilted glazing or roofs yet.
5. **Shading:** horizontal overhangs only, SC2 from R1 = projection / window height, linearly interpolated. Fins and egg-crate devices are not modelled.
6. **SC = SC1 × SC2.**
7. **Geometry:** rectangular box with 4 façades and the same wall and glass specification on every face. WWR and overhang vary per face.
8. **Parameter ranges** (`PARAM_RANGES` in `sample.py`) are judgement calls, not from a survey of Singapore buildings.
9. **U_fen and SC1 are sampled independently.** Real glass products correlate them (low-e glass is low in both), so some combinations are unrealistic. A possible improvement is to sample from a glass product catalogue.

## Sources
I couldn't verify these online during this session. Check the editions you cite.
- Building and Construction Authority (BCA), Singapore. *Code on Envelope Thermal Performance for Buildings* (2008). ETTV formula, CF and SC2 tables.
- BCA. *Green Mark 2021* technical guides. Envelope performance criteria.
- McKay, M. D., Beckman, R. J. & Conover, W. J. (1979). A comparison of three methods for selecting values of input variables in the analysis of output from a computer code. *Technometrics*, 21(2). The origin of Latin Hypercube Sampling.
- Westermann, P. & Evins, R. (2019). Surrogate modelling for sustainable building design – A review. *Energy and Buildings*, 198. A good literature anchor for your introduction.
- SciPy documentation, `scipy.stats.qmc.LatinHypercube`.
- scikit-learn documentation: model selection, `permutation_importance`, `HistGradientBoostingRegressor`, `MLPRegressor`.
- Ladybug Tools (open source, ladybug.tools). Suggested for the SC2 solar-simulation stage.
