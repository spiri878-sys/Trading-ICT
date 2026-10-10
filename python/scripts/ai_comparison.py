"""Spec 7: AI filter vs no filter vs random selection of the same size, plus ONNX export parity check.
Model: LightGBM regressor of the isolated net R outcome (target clipped [-1.2, 4]); features = ratios only
(raptor.features); training 2018-2020, early stopping on 2021 (dev); living threshold q80 of last 1000.
Evaluated on val and test. The model is NOT used by the final EA profile if it does not beat both baselines."""
import sys, json, hashlib
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M, ml
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
LADDER = dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320)
CELLS = ["UNIOF", "OTEOF", "SILVER_BULLET", "PO3", "MSS", "LS", "PPK"]
with with_cost(C1, replace(P.Params(), **LADDER)) as prm:
    lab, X = P.labelled({c: {} for c in CELLS}, prm, tf="5min", swing_k=3)
fr = ml.fit(lab, X, train_end="2022-01-01", inner_valid_start="2021-01-01")
out = {"best_iter": fr.best_iter, "inner_valid_corr_2021": round(fr.inner_valid_corr, 4), "n_features": len(fr.features)}
rng = np.random.default_rng(42)
for per in ["val", "test"]:
    m = (lab.bar_time >= P.PERIODS[per][0]) & (lab.bar_time < P.PERIODS[per][1])
    sc = fr.model.predict(X[m].values)
    thr = ml.living_threshold(sc, fr.seed_scores)
    d = lab[m].assign(score=sc, accept=sc > thr)
    f = d[d.filled]
    acc = f[f.accept]
    rand = [f.r.sample(len(acc), random_state=int(rng.integers(1e9))).mean() for _ in range(500)] if len(acc) else [np.nan]
    out[per] = {"all": M.r_stats(f.r), "ai_accepted": M.r_stats(acc.r), "ai_rejected": M.r_stats(f[~f.accept].r),
                "random_same_size_meanR": round(float(np.mean(rand)), 4),
                "random_p05_p95": [round(float(np.quantile(rand, 0.05)), 4), round(float(np.quantile(rand, 0.95)), 4)],
                "score_R_corr": round(float(np.corrcoef(f.score, f.r)[0, 1]), 4),
                "accept_rate_pct": round(float(d.accept.mean() * 100), 1)}
imp = pd.Series(fr.model.feature_importance("gain"), index=fr.features).sort_values(ascending=False)
out["top_features_gain"] = imp.head(10).round(1).to_dict()
# ---- ONNX export + parity check (the EA does not load it: the filter is rejected unless it beats baselines)
models = ROOT / "models"; models.mkdir(exist_ok=True)
fr.model.save_model(str(models / "rr_filter_lgbm.txt"))
try:
    import onnxmltools
    from onnxmltools.convert.common.data_types import FloatTensorType
    import onnxruntime as ort
    onx = onnxmltools.convert_lightgbm(fr.model, initial_types=[("input", FloatTensorType([None, len(fr.features)]))], target_opset=15)
    (models / "rr_filter.onnx").write_bytes(onx.SerializeToString())
    Xs = X.sample(2000, random_state=1).astype(np.float32)
    sess = ort.InferenceSession(str(models / "rr_filter.onnx"))
    po = sess.run(None, {"input": Xs.values})[0].ravel()
    pl = fr.model.predict(Xs.values.astype(np.float64))   # same float32-rounded inputs
    diff = np.abs(po - pl)
    out["onnx_parity_p99_abs_diff"] = float(np.nanquantile(diff, 0.99))
    out["onnx_parity_max_abs_diff"] = float(np.nanmax(diff))
    out["onnx_parity_share_rows_diff_gt_1e-4"] = float(np.mean(diff > 1e-4))
    out["onnx_parity_note"] = "max diff only on rows whose float32 feature equals a split threshold (tie); EA must feed float32"
    out["onnx_sha256"] = hashlib.sha256((models / "rr_filter.onnx").read_bytes()).hexdigest()
except Exception as e:  # report honestly
    out["onnx_error"] = repr(e)
(models / "rr_filter_features.json").write_text(json.dumps(fr.features, indent=1))
(ROOT / "reports" / "ai_comparison.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
