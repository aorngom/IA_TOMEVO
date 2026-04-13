from pydantic_settings import BaseSettings

class Parametres(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    GROQ_API_KEY: str 

    class Config:
        env_file = ".env"
        # Cette ligne permet d'éviter les erreurs si autres 
        # variables dans ton .env que tu n'as pas encore déclarées ici
        extra = "ignore" 

parametres = Parametres()