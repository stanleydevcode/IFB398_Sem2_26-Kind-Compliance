import os

class Config:
    SECRET_KEY = "dev-only-change-me"
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://kind:kind@localhost:5432/kind_compliance"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def from_environment(cls):
        """Read runtime settings after the factory has loaded the project .env."""
        return {
            "SECRET_KEY": os.getenv("SECRET_KEY", cls.SECRET_KEY),
            "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URL", cls.SQLALCHEMY_DATABASE_URI),
            "SQLALCHEMY_TRACK_MODIFICATIONS": cls.SQLALCHEMY_TRACK_MODIFICATIONS,
        }
