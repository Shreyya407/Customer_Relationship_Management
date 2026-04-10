from __future__ import annotations

from pathlib import Path
import sys

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.config import settings
from app.data import build_customer_features

FEATURE_COLUMNS = [
    "recency_days",
    "invoices_count",
    "line_items_count",
    "quantity_sum",
    "monetary",
    "average_line_amount",
    "tenure_days",
    "purchase_rate",
]


def build_label_vector(feature_frame):
    monetary_threshold = feature_frame["monetary"].quantile(0.75)
    frequency_threshold = feature_frame["invoices_count"].quantile(0.75)
    return ((feature_frame["monetary"] >= monetary_threshold) | (feature_frame["invoices_count"] >= frequency_threshold)).astype(
        int
    )


def train_and_log_model() -> Path:
    feature_frame = build_customer_features().copy()
    targets = build_label_vector(feature_frame)

    x_data = feature_frame[FEATURE_COLUMNS]
    y_data = targets

    x_train, x_test, y_train, y_test = train_test_split(
        x_data,
        y_data,
        test_size=0.2,
        random_state=42,
        stratify=y_data,
    )

    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)),
        ]
    )
    pipeline.fit(x_train, y_train)

    y_pred = pipeline.predict(x_test)
    y_prob = pipeline.predict_proba(x_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "train_rows": int(x_train.shape[0]),
        "test_rows": int(x_test.shape[0]),
        "class_balance": float(np.mean(y_data)),
    }

    mlruns_dir = Path(__file__).resolve().parent / "mlruns"
    mlruns_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"file:{mlruns_dir.as_posix()}")
    mlflow.set_experiment("crm-customer-value")

    with mlflow.start_run(run_name="logreg-customer-value"):
        mlflow.log_params(
            {
                "model": "logistic_regression",
                "features": ",".join(FEATURE_COLUMNS),
                "dataset_path": str(settings.dataset_path),
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(pipeline, artifact_path="model")

    artifact_dir = Path(__file__).resolve().parent / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / "customer_value_model.joblib"
    joblib.dump(pipeline, output_path)

    print(f"Model trained and saved to: {output_path}")
    print(f"MLFlow tracking URI: file:{mlruns_dir.as_posix()}")
    print(f"Metrics: {metrics}")

    return output_path


if __name__ == "__main__":
    train_and_log_model()
