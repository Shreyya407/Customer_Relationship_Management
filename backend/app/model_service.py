from __future__ import annotations

from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from app.config import settings


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


class CustomerValueModel:
    def __init__(self, model) -> None:
        self.model = model

    def predict_probability(self, feature_row: dict) -> float:
        frame = pd.DataFrame([{column: feature_row[column] for column in FEATURE_COLUMNS}])
        if hasattr(self.model, "predict_proba"):
            probability = float(self.model.predict_proba(frame)[0][1])
        else:
            prediction = float(self.model.predict(frame)[0])
            probability = min(max(prediction, 0.0), 1.0)
        return probability


@lru_cache(maxsize=1)
def load_model() -> CustomerValueModel | None:
    if not settings.model_artifact_path.exists():
        return None
    model = joblib.load(settings.model_artifact_path)
    return CustomerValueModel(model=model)


def heuristic_probability(feature_row: dict) -> float:
    # Fallback score if a trained model is not available yet.
    monetary_signal = np.log1p(feature_row["monetary"]) / 8.5
    frequency_signal = feature_row["invoices_count"] / 40.0
    recency_penalty = min(feature_row["recency_days"] / 365.0, 1.0)

    raw_score = 0.6 * monetary_signal + 0.35 * frequency_signal - 0.25 * recency_penalty
    return float(np.clip(raw_score, 0.01, 0.99))


def score_customer(feature_row: dict) -> tuple[float, str, str]:
    model = load_model()
    if model is None:
        probability = heuristic_probability(feature_row)
        source = "heuristic"
    else:
        probability = model.predict_probability(feature_row)
        source = "mlflow-model"

    segment = "high_value" if probability >= 0.5 else "regular"
    return probability, segment, source
