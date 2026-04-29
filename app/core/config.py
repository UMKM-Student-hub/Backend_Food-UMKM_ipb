from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "UniBites API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str
    SECRET_KEY: str = "unibites_super_secret_key_123_ganti_nanti_di_production"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()