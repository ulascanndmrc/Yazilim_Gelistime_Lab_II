import os


class Settings:
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/login_db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-key")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "internal-dev-key")
    port: int = int(os.getenv("PORT", "5001"))


settings = Settings()
