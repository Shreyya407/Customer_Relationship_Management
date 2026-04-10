from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CRM_", case_sensitive=False)

    app_name: str = "Retail CRM API"
    app_version: str = "0.1.0"
    dataset_path: Path = Path(__file__).resolve().parents[2] / "online_retail_listing.csv"
    model_artifact_path: Path = (
        Path(__file__).resolve().parents[1] / "ml" / "artifacts" / "customer_value_model.joblib"
    )
    mlflow_tracking_uri: str = (
        f"file:{(Path(__file__).resolve().parents[1] / 'ml' / 'mlruns').as_posix()}"
    )


settings = Settings()
