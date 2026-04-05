import os


class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/report_db")
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "internal-dev-key")
    port: int = int(os.getenv("PORT", "5005"))


settings = Settings()
