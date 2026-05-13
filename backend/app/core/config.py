from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "GIS Spatial System"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
