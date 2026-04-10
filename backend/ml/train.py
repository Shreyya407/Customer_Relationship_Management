from __future__ import annotations

from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.data import build_customer_table


def main() -> None:
    data = build_customer_table()
    customers = data.segments.copy()
    features = customers[["recency_score", "frequency_score", "monetary_score"]].astype(float)

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("crm-retail-segmentation")

    scaler = StandardScaler()
    model = KMeans(n_clusters=4, random_state=42, n_init=10)
    scaled = scaler.fit_transform(features)
    cluster_ids = model.fit_predict(scaled)

    customers["cluster_id"] = cluster_ids
    output_dir = Path("ml") / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run():
        mlflow.log_param("n_clusters", 4)
        mlflow.log_param("dataset_path", settings.dataset_path)
        mlflow.log_metric("customers", len(customers))
        mlflow.sklearn.log_model(model, "model")
        joblib.dump({"scaler": scaler, "model": model}, output_dir / "customer_segmenter.joblib")
        customers.to_csv(output_dir / "customer_segments.csv", index=False)


if __name__ == "__main__":
    main()
