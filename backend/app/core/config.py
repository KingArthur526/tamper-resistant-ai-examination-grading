import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STORAGE_DIR = BASE_DIR / 'storage'
ORIGINAL_DIR = STORAGE_DIR / 'original'
PREPROCESSED_DIR = STORAGE_DIR / 'preprocessed'
OCR_DIR = STORAGE_DIR / 'ocr'
REPORTS_DIR = STORAGE_DIR / 'reports'
DEMO_SAMPLES_DIR = STORAGE_DIR / 'demo_samples'

# Ensure directories exist
for p in [STORAGE_DIR, ORIGINAL_DIR, PREPROCESSED_DIR, OCR_DIR, REPORTS_DIR, DEMO_SAMPLES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = 'Tamper Resistant AI-Powered Examination Grading System'
    VERSION: str = '1.0.0'
    API_V1_STR: str = '/api'
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'TAMPER_RESISTANT_SECRET_KEY_EXAM_AI_2026_SECURE_9812401')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/grading_system.db')
    
    # Storage Paths
    STORAGE_PATH: Path = STORAGE_DIR
    ORIGINAL_PATH: Path = ORIGINAL_DIR
    PREPROCESSED_PATH: Path = PREPROCESSED_DIR
    OCR_PATH: Path = OCR_DIR
    REPORTS_PATH: Path = REPORTS_DIR
    DEMO_SAMPLES_PATH: Path = DEMO_SAMPLES_DIR
    
    # Default AI / ML Parameters
    DEFAULT_MODEL_NAME: str = 'all-MiniLM-L6-v2'
    DEFAULT_SIMILARITY_METHOD: str = 'Cosine Similarity'
    DEFAULT_FULL_MATCH_THRESHOLD: float = 0.78
    DEFAULT_PARTIAL_MATCH_THRESHOLD: float = 0.52
    DEFAULT_SCORING_POLICY_VERSION: str = 'v1.0-deterministic'
    DEFAULT_OR_POLICY: str = 'best_attempted'  # 'best_attempted', 'first_attempted'
    
    # OCR Settings
    OCR_CONFIDENCE_THRESHOLD: float = 0.70  # Below this flags manual review

    class Config:
        case_sensitive = True

settings = Settings()
