"""Configuration management for BAT POD using pydantic-settings."""

from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System settings loaded from environment variables and .env file."""

    # Operation Mode
    BAT_POD_MODE: Literal["mock", "hardware"] = "mock"

    # Serial Hardware Ports & Parameters
    ARDUINO_PORT: str = "COM3"
    ARDUINO_BAUD: int = 115200
    ESP32_PORT: str = "COM4"
    ESP32_BAUD: int = 115200
    SERIAL_TIMEOUT_SEC: float = 2.0

    # Storage
    SQLITE_DB_PATH: str = "data/bat_pod.db"

    # Polling & Thresholds
    SENSOR_POLL_INTERVAL_SEC: float = 1.0
    GAS_CRITICAL_THRESHOLD_PPM: float = 300.0
    GAS_WARNING_THRESHOLD_PPM: float = 150.0
    TEMP_CRITICAL_HIGH_C: float = 50.0
    TEMP_WARNING_HIGH_C: float = 38.0
    SOIL_DRY_THRESHOLD_PCT: float = 25.0

    # Human-in-the-Loop
    APPROVAL_TIMEOUT_SEC: float = 30.0

    # AI & Voice Pipeline
    AI_BACKEND: Literal["local", "sarvam", "ollama"] = "local"
    SARVAM_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    VOICE_LANGUAGE: str = "en-IN"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_db_path(self) -> Path:
        """Resolve database path and ensure directory exists."""
        p = Path(self.SQLITE_DB_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
