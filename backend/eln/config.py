from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Workspace
    workspaces_root: Path = Path("workspaces")
    default_user: str = "default"

    # Vector store
    # Empty string = embedded Qdrant (local path, default for dev/bare-metal).
    # Set QDRANT_URL=http://qdrant:6333 when running via Docker Compose.
    qdrant_url: str = ""

    # Embeddings
    # Provider: "local" (HuggingFace, no API key) or "openai"
    # Model: empty string means use the provider's default
    embedding_provider: str = "local"
    embedding_model: str = ""

    # Models
    default_provider: str = "anthropic"
    default_model: str = "claude-sonnet-4-6"
    supervisor_model: str = "claude-haiku-4-5-20251001"

    # Literature
    ncbi_email: str = ""  # required for PubMed E-utilities
    semantic_scholar_api_key: str = ""  # optional; raises rate limit

    # BiomedParse (optional external segmentation endpoint)
    biomedparse_endpoint_url: str | None = None

    # Storage backend
    storage_backend: str = "local"       # "local" | "s3"
    s3_bucket: str = "eln-kb"
    s3_endpoint_url: str = ""            # empty = AWS S3; "http://localhost:9000" = MinIO
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "us-east-1"
    s3_presign_expires: int = 3600

    # Premium add-ons
    # R analysis: set R_ANALYSIS_ENABLED=true + install R in your environment
    r_analysis_enabled: bool = False
    # ColabFold novel structure prediction: set COLABFOLD_ENABLED=true
    # Free tier uses AlphaFold DB lookup (fetch_alphafold_structure) — instant, no flag needed
    colabfold_enabled: bool = False

    # OpenTelemetry
    otel_enabled: bool = False
    otel_exporter: str = "otlp"  # "otlp" | "console"
    otel_endpoint: str = "http://localhost:4317"

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Merge a settings.yaml on top of env-based settings."""
        base = cls()
        if path.exists():
            with open(path) as f:
                overrides = yaml.safe_load(f) or {}
            return base.model_copy(update=overrides)
        return base


# Module-level singleton; callers do `from eln.config import settings`
settings = Settings()
