import os


class Settings:
    """Application configuration loaded from environment variables."""
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/dispatcher_db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-key")
    jwt_algorithm: str = "HS256"
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "internal-dev-key")
    login_service_url: str = os.getenv("LOGIN_SERVICE_URL", "http://localhost:5001")
    message_service_url: str = os.getenv("MESSAGE_SERVICE_URL", "http://localhost:5002")
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://localhost:5003")
    product_service_url: str = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:5004")
    report_service_url: str = os.getenv("REPORT_SERVICE_URL", "http://localhost:5005")


settings = Settings()
