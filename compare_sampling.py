"""compare_sampling.py — train the same surrogates on datasets from the 5 sampling methods and compare test error
on one common, independent random test set. Run: python compare_sampling.py  (~3 min).
Results -> data/sampling_comparison.csv   (v3: now uses sampling_methods.py, so it matches the notebook exactly)"""
import warnings
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from sampling_methods import METHODS, generate_dataset
warnings.filterwarnings("ignore")

def features(df):
    F = df[list(__import__("sample").PARAM_RANGES)].copy()
    rad = np.deg2rad(F.pop("rotation_deg")); F["rot_sin"], F["rot_cos"] = np.sin(rad), np.cos(rad)
    F["aspect"] = df.length_m / df.width_m
    return F

MODELS = {"Gradient boosting": lambda: HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, random_state=0),
          "Neural net": lambda: make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 64), max_iter=1500,
                                                                           early_stopping=True, random_state=0))}

def run(sizes=(128, 512, 2048), seeds=range(4), n_test=3000, test_seed=999):
    test, _ = generate_dataset("Random", n_test, test_seed)     # common, independent test set
    Xte, yte = features(test), test.ettv.values
    rows = []
    for n in sizes:
        for m in METHODS:
            for s in seeds:
                df, _ = generate_dataset(m, n, s)
                X, y = features(df), df.ettv.values
                for name, make in MODELS.items():
                    mdl = make().fit(X, y)
                    p = mdl.predict(Xte)
                    rows.append(dict(n=n, method=m, model=name, seed=s, mae=mean_absolute_error(yte, p),
                                     passfail_acc=float(np.mean((p <= 50) == (yte <= 50)))))
        print("done n =", n, flush=True)
    return pd.DataFrame(rows)

if __name__ == "__main__":
    r = run()
    r.to_csv("data/sampling_comparison.csv", index=False)
    print(r.groupby(["model", "n", "method"]).mae.mean().unstack("method").round(2))
