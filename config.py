from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/nom"

    # OpenAI
    openai_llm_model: str = Field(
        default="gpt-5.4-nano", validation_alias="OPENAI_LLM_MODEL"
    )
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_api_key_prefix: str = Field(
        default="", validation_alias="OPENAI_API_KEY_PREFIX"
    )
    openai_api_key_suffix: str = Field(
        default="", validation_alias="OPENAI_API_KEY_SUFFIX"
    )

    # HuggingFace
    hf_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="HF_EMBEDDING_MODEL",
    )
    hf_api_token: str = Field(default="", validation_alias="HF_API_TOKEN")
    hf_endpoint_url: str = Field(default="", validation_alias="HF_ENDPOINT_URL")

    # Model Validation
    @model_validator(mode="after")
    def combine_openai_api_key(self) -> "Settings":
        """Combine prefix + suffix if main API key is not set."""
        if (
            not self.openai_api_key
            and self.openai_api_key_prefix
            and self.openai_api_key_suffix
        ):
            self.openai_api_key = (
                self.openai_api_key_prefix + self.openai_api_key_suffix
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Available source types in the knowledge base
AVAILABLE_SOURCE_TYPES = ["service", "case_study", "blog", "company"]
