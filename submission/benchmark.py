#!/usr/bin/env python3
"""Train and benchmark LightGBM on the credit-card fraud dataset."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import sklearn
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
TEST_SIZE = 0.20
VALIDATION_SIZE_WITHIN_TRAIN = 0.10
SINGLE_ROW_REPETITIONS = 200
BATCH_REPETITIONS = 30
BATCH_SIZE = 1_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and benchmark a LightGBM fraud classifier."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("creditcard.csv"),
        help="Path to creditcard.csv (default: ./creditcard.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark_result.json"),
        help="JSON output path (default: ./benchmark_result.json)",
    )
    return parser.parse_args()


def load_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series, int, float]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    # float32 halves the feature memory footprint, which matters on t3.micro.
    feature_columns = ["Time", *(f"V{i}" for i in range(1, 29)), "Amount"]
    dtypes = {column: "float32" for column in feature_columns}
    dtypes["Class"] = "uint8"

    started = time.perf_counter()
    frame = pd.read_csv(path, dtype=dtypes)
    load_seconds = time.perf_counter() - started

    required = set(feature_columns) | {"Class"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    if frame.empty:
        raise ValueError("Dataset is empty")
    if frame[list(required)].isnull().any().any():
        raise ValueError("Dataset contains missing values")

    X = frame.drop(columns="Class")
    y = frame["Class"]
    memory_bytes = int(frame.memory_usage(deep=True).sum())
    return X, y, memory_bytes, load_seconds


def median_prediction_seconds(
    model: LGBMClassifier, rows: pd.DataFrame, repetitions: int
) -> float:
    # Warm up code paths and worker threads before recording measurements.
    model.predict_proba(rows, num_iteration=model.best_iteration_)
    samples: list[float] = []
    for _ in range(repetitions):
        started = time.perf_counter()
        model.predict_proba(rows, num_iteration=model.best_iteration_)
        samples.append(time.perf_counter() - started)
    return float(statistics.median(samples))


def main() -> None:
    args = parse_args()
    data_path = args.data.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    started_at = datetime.now(timezone.utc)

    print(f"Loading dataset: {data_path}")
    X, y, dataset_memory_bytes, load_seconds = load_dataset(data_path)

    split_started = time.perf_counter()
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_train_full,
        y_train_full,
        test_size=VALIDATION_SIZE_WITHIN_TRAIN,
        random_state=RANDOM_STATE,
        stratify=y_train_full,
    )
    split_seconds = time.perf_counter() - split_started

    model_parameters = {
        "objective": "binary",
        "n_estimators": 500,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": -1,
        "min_child_samples": 20,
        "subsample": 0.8,
        "subsample_freq": 1,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 0.1,
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
        "verbosity": -1,
    }
    model = LGBMClassifier(**model_parameters)

    print(
        "Training LightGBM "
        f"({len(X_train):,} train / {len(X_validation):,} validation rows)..."
    )
    training_started = time.perf_counter()
    # LightGBM 4.7 deprecates eval_set in favor of eval_X/eval_y. Keep eval_set
    # for compatibility with the older versions commonly installed on lab VMs.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"The argument 'eval_set' is deprecated.*",
            module=r"lightgbm\.sklearn",
        )
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_validation, y_validation)],
            eval_metric="auc",
            callbacks=[lgb.early_stopping(50, verbose=False)],
        )
    training_seconds = time.perf_counter() - training_started

    prediction_started = time.perf_counter()
    test_probabilities = model.predict_proba(
        X_test, num_iteration=model.best_iteration_
    )[:, 1]
    test_predictions = (test_probabilities >= 0.5).astype(np.uint8)
    test_prediction_seconds = time.perf_counter() - prediction_started

    metrics = {
        "auc_roc": float(roc_auc_score(y_test, test_probabilities)),
        "accuracy": float(accuracy_score(y_test, test_predictions)),
        "f1_score": float(f1_score(y_test, test_predictions, zero_division=0)),
        "precision": float(
            precision_score(y_test, test_predictions, zero_division=0)
        ),
        "recall": float(recall_score(y_test, test_predictions, zero_division=0)),
    }

    single_row = X_test.iloc[[0]]
    batch_size = min(BATCH_SIZE, len(X_test))
    batch_rows = X_test.iloc[:batch_size]
    single_latency_seconds = median_prediction_seconds(
        model, single_row, SINGLE_ROW_REPETITIONS
    )
    batch_latency_seconds = median_prediction_seconds(
        model, batch_rows, BATCH_REPETITIONS
    )
    throughput_rows_per_second = batch_size / batch_latency_seconds

    completed_at = datetime.now(timezone.utc)
    result = {
        "benchmark": {
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": completed_at.isoformat(),
            "random_state": RANDOM_STATE,
        },
        "dataset": {
            "path": str(data_path),
            "rows": int(len(X)),
            "features": int(X.shape[1]),
            "fraud_rows": int(y.sum()),
            "fraud_rate": float(y.mean()),
            "memory_bytes": dataset_memory_bytes,
        },
        "split": {
            "train_rows": int(len(X_train)),
            "validation_rows": int(len(X_validation)),
            "test_rows": int(len(X_test)),
            "test_size": TEST_SIZE,
            "validation_size_within_train": VALIDATION_SIZE_WITHIN_TRAIN,
            "stratified": True,
        },
        "model": {
            "name": "LGBMClassifier",
            "parameters": model_parameters,
            "best_iteration": int(model.best_iteration_),
            "decision_threshold": 0.5,
        },
        "timings_seconds": {
            "load_data": load_seconds,
            "split_data": split_seconds,
            "training": training_seconds,
            "test_prediction": test_prediction_seconds,
        },
        "metrics": metrics,
        "inference": {
            "single_row": {
                "rows": 1,
                "repetitions": SINGLE_ROW_REPETITIONS,
                "median_latency_seconds": single_latency_seconds,
                "median_latency_ms": single_latency_seconds * 1_000,
            },
            "batch_1000_rows": {
                "rows": batch_size,
                "repetitions": BATCH_REPETITIONS,
                "median_latency_seconds": batch_latency_seconds,
                "median_latency_ms": batch_latency_seconds * 1_000,
                "throughput_rows_per_second": throughput_rows_per_second,
            },
        },
        "environment": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "logical_cpu_count": os.cpu_count(),
            "lightgbm": lgb.__version__,
            "scikit_learn": sklearn.__version__,
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print("\nBenchmark results")
    print(f"  Load data:                {load_seconds:.3f} s")
    print(f"  Split data:               {split_seconds:.3f} s")
    print(f"  Training:                 {training_seconds:.3f} s")
    print(f"  Best iteration:           {model.best_iteration_}")
    print(f"  AUC-ROC:                  {metrics['auc_roc']:.6f}")
    print(f"  Accuracy:                 {metrics['accuracy']:.6f}")
    print(f"  F1-Score:                 {metrics['f1_score']:.6f}")
    print(f"  Precision:                {metrics['precision']:.6f}")
    print(f"  Recall:                   {metrics['recall']:.6f}")
    print(f"  Inference latency (1):    {single_latency_seconds * 1_000:.3f} ms")
    print(
        "  Inference throughput:     "
        f"{throughput_rows_per_second:,.2f} rows/s "
        f"({batch_latency_seconds * 1_000:.3f} ms per {batch_size} rows)"
    )
    print(f"  JSON result:              {output_path}")


if __name__ == "__main__":
    main()
