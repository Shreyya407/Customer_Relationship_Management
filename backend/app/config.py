from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    dataset_path: str = os.getenv("DATASET_PATH", "../online_retail_listing.csv")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "file:../mlruns")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()
    )


settings = Settings()
