from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    AGENT_MODEL_NAME: str = "llama3-70b-8192"
    AGENT_SYSTEM_PROMPT: str = "You are a helpful MLOps agent."

    class Config:
        env_file = ".env"

settings = Settings()
