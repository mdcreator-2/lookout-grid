from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Lookout Grid"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # --- Database ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "lookoutgrid"
    DB_USER: str = "lookoutgrid_user"
    DB_PASSWORD: str = "CHANGE_ME"
    DATABASE_URL: str = "postgresql+asyncpg://lookoutgrid_user:CHANGE_ME@localhost:5432/lookoutgrid"
    
    # --- MQTT Broker ---
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = "lookoutgrid_backend"
    MQTT_PASSWORD: str = "CHANGE_ME"
    
    # --- JWT Auth ---
    JWT_SECRET_KEY: str = "CHANGE_ME_TO_A_RANDOM_64_CHAR_STRING"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # --- Firebase (Push Notifications) ---
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"
    
    # --- SMS Gateway (Fast2SMS or Twilio) ---
    SMS_PROVIDER: str = "fast2sms"
    FAST2SMS_API_KEY: str = "CHANGE_ME"
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None
    
    # --- Server ---
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    
settings = Settings()
if __name__ == '__main__':
    s = Settings()
    print(s)
