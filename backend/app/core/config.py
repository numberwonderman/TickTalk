import os


class Settings:
    vision_model_backend: str = os.environ.get("VISION_MODEL_BACKEND", "mock")
    s3_bucket: str | None = os.environ.get("TICKCHECK_S3_BUCKET")
    aws_region: str = os.environ.get("AWS_REGION", "us-east-1")
    cors_allow_origins: list[str] = os.environ.get(
        "CORS_ALLOW_ORIGINS", "http://localhost:5173"
    ).split(",")


settings = Settings()
