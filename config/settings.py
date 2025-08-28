from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    DATABASE_URL: str
    
    # HuggingFace Configuration
    HUGGINGFACE_API_KEY: Optional[str] = None
    HF_HOME: str = "./models"  # Local model cache
    
    # AI Model Settings
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    CLASSIFICATION_MODEL: str = "facebook/bart-large-mnli"
    QA_MODEL: str = "deepset/roberta-base-squad2"
    SUMMARIZATION_MODEL: str = "facebook/bart-large-cnn"
    
    # Processing Settings
    SIMILARITY_THRESHOLD: float = 0.85
    MIN_CONFIDENCE_SCORE: float = 0.1
    BATCH_SIZE: int = 32
    MAX_CONTEXT_LENGTH: int = 2000
    
    # Scraping Settings
    SCRAPING_DELAY: float = 2.0
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_TIMEOUT: int = 30
    
    # Cache Settings
    ENABLE_AI_CACHING: bool = True
    CACHE_EXPIRY_HOURS: int = 24
    
    # Rate Limiting
    HF_API_CALLS_PER_HOUR: int = 1000  # Free tier limit
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
