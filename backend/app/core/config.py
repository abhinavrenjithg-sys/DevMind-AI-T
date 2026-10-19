from pathlib import Path
from typing import List, Set
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    class BaseSettings:
        pass

class Settings:
    PROJECT_NAME: str = "DevMind AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    REPOS_DIR: Path = STORAGE_DIR / "repositories"
    UPLOADS_DIR: Path = STORAGE_DIR / "uploads"
    REPORTS_DIR: Path = STORAGE_DIR / "reports"
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{(BASE_DIR / 'devmind.db').as_posix()}"
    
    # Security & limits
    MAX_ARCHIVE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024     # 10 MB
    MAX_FILE_COUNT: int = 10000
    SAFE_REQUEST_TIMEOUT_SECONDS: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # Analysis Configuration
    SUPPORTED_EXTENSIONS: Set[str] = {
        ".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
        ".json", ".yaml", ".yml", ".toml", ".md", ".txt", ".sql", ".html", ".css"
    }
    
    EXCLUDED_DIRS: Set[str] = {
        ".git", ".svn", ".hg", "node_modules", ".venv", "venv", "env",
        "__pycache__", "dist", "build", ".next", ".nuxt", "target",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".coverage",
        "htmlcov", ".idea", ".vscode", "coverage", ".turbo", ".cache"
    }

    # AI Configuration (Optional API keys)
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_PROVIDER: str = "heuristic" # "heuristic", "openai", "gemini", "anthropic"

    def ensure_directories(self) -> None:
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.REPOS_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
