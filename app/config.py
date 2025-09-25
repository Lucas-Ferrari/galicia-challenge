from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):

    postgres_db: str = "example_db"
    postgres_user: str = "example_usr"
    postgres_password: str = "eXaMpLe_pWd"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: Optional[str] = None

    api_title: str = "Galicia API"
    api_version: str = "1.0.0"
    api_description: str = (
        "API para gestión de aeropuertos, aerolíneas y rutas de vuelo"
    )

    high_occupancy_threshold: float = 0.85
    min_altitude: int = 1000

    log_level: str = "INFO"

    environment: str = "development"

    @property
    def db_url(self) -> str:
        if self.dababase_url:
            return self.database_url
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

