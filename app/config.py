import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://kind:kind@localhost:5432/kind_compliance",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
