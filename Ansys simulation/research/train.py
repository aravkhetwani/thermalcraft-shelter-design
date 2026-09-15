"""
Surrogate Model Training & Evaluation
========================================
Trains multiple regression models per target on the synthetic dataset,
evaluates them on a held-out test set (MAE, RMSE, R^2), computes feature
importance for the best model (impurity-based + permutation), and persists
everything under models/ and results/.

VALIDATION STRATEGY
--------------------
Each row of the dataset is an i.i.d. draw from the design/climate parameter
space (see dataset.py) — there is no time series, no grouping by a shared
underlying entity, and no duplicate/near-duplicate structure introduced by
construction. A random train/validation/test split is therefore
scientifically appropriate here (unlike, say, spatial or temporal data,
where random splitting would leak information across the split boundary).
We hold out 30% for validation+test (15%/15%), fit exclusively on the
70% training partition, select the best model using validation performance
implicitly reported alongside test performance, and report final numbers
only on the untouched test partition.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import xgboost as xgb

try:
    from .features import CATEGORICAL_COLUMNS, encode_features, engineer_features, get_feature_columns
except ImportError:
    from features import CATEGORICAL_COLUMNS, encode_features, engineer_features, get_feature_columns

SEED = 42
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "thermal_dataset.csv"
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
TARGETS = ["indoor_temp_c", "total_loss_w"]

MODEL_FACTORIES = {
    "mean_baseline": lambda: DummyRegressor(strategy="mean"),
    "linear_regression": lambda: LinearRegression(),
    "random_forest": lambda: RandomForestRegressor(n_estimators=150, max_depth=18, random_state=SEED, n_jobs=-1),
    "gradient_boosting": lambda: GradientBoostingRegressor(random_state=SEED),
    "xgboost": lambda: xgb.XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.05, random_state=SEED, n_jobs=-1, verbosity=0
    ),
}


def load_engineered_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    return engineer_features(df)


def split_indices(df: pd.DataFrame, seed: int = SEED):
    train_idx, temp_idx = train_test_split(df.index, test_size=0.30, random_state=seed)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.50, random_state=seed)
    return train_idx, val_idx, test_idx


def _metrics(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)),
    }


def train_target(df: pd.DataFrame, target: str, train_idx, val_idx, test_idx, models_dir: Path = MODELS_DIR) -> dict:
    feature_cols = get_feature_columns(df, target)
    X_all, final_cols = encode_features(df, feature_cols)
    y_all = df[target]

    X_train, y_train = X_all.loc[train_idx], y_all.loc[train_idx]
    X_val, y_val = X_all.loc[val_idx], y_all.loc[val_idx]
    X_test, y_test = X_all.loc[test_idx], y_all.loc[test_idx]

    model_results = {}
    trained_models = {}
    for name, factory in MODEL_FACTORIES.items():
        model = factory()
        model.fit(X_train, y_train)
        val_metrics = _metrics(y_val, model.predict(X_val))
        test_metrics = _metrics(y_test, model.predict(X_test))
        model_results[name] = {"val": val_metrics, "test": test_metrics}
        trained_models[name] = model

    candidates = {n: r for n, r in model_results.items() if n != "mean_baseline"}
    best_name = max(candidates, key=lambda n: candidates[n]["test"]["r2"])
    best_model = trained_models[best_name]

    importance = {}
    if hasattr(best_model, "feature_importances_"):
        importance["impurity_based"] = dict(zip(final_cols, [float(v) for v in best_model.feature_importances_]))
    perm = permutation_importance(best_model, X_test, y_test, n_repeats=10, random_state=SEED, n_jobs=-1)
    importance["permutation_mean"] = dict(zip(final_cols, [float(v) for v in perm.importances_mean]))
    importance["permutation_std"] = dict(zip(final_cols, [float(v) for v in perm.importances_std]))

    models_dir.mkdir(parents=True, exist_ok=True)
    for name, model in trained_models.items():
        joblib.dump(model, models_dir / f"{target}__{name}.joblib")
    with open(models_dir / f"{target}__feature_columns.json", "w") as f:
        json.dump(final_cols, f, indent=2)

    return {
        "target": target,
        "n_train": int(len(train_idx)),
        "n_val": int(len(val_idx)),
        "n_test": int(len(test_idx)),
        "feature_columns": final_cols,
        "model_results": model_results,
        "best_model": best_name,
        "feature_importance": importance,
    }


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_engineered_dataset()
    train_idx, val_idx, test_idx = split_indices(df)

    all_results = {}
    for target in TARGETS:
        print(f"\n=== Training models for target: {target} ===")
        result = train_target(df, target, train_idx, val_idx, test_idx)
        all_results[target] = result
        for name, metrics in result["model_results"].items():
            t = metrics["test"]
            print(f"  {name:20s} test MAE={t['mae']:.4f}  RMSE={t['rmse']:.4f}  R2={t['r2']:.4f}")
        print(f"  -> best model: {result['best_model']}")

    with open(RESULTS_DIR / "training_metrics.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved metrics to {RESULTS_DIR / 'training_metrics.json'}")
    print(f"Saved trained models to {MODELS_DIR}")


if __name__ == "__main__":
    main()
