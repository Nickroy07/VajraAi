from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    sqlite_path: str



def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "VAJRA AI Gateway"),
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        sqlite_path=os.getenv("SQLITE_PATH", "./vajra.db"),
    )
