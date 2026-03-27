import os
from datetime import timedelta


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    MONGO_URI = os.getenv(
        "MONGODB_URI",
        os.getenv("MONGO_URI", "mongodb://localhost:27017/farm_to_market"),
    )
    DATABASE_NAME = os.getenv("DATABASE_NAME", "farm_to_market")
    DEBUG = _as_bool(os.getenv("FLASK_DEBUG"), False)
    TESTING = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), False)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    WTF_CSRF_TIME_LIMIT = None
    ADMIN_PAGE_SIZE = 20
    OFFER_EXPIRY_HOURS = int(os.getenv("OFFER_EXPIRY_HOURS", "24"))


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
