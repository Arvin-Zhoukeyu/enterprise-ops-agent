from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from pydantic import model_validator
from sqlalchemy.engine import make_url


class Settings(BaseSettings):

    app_name: str = (
        "EnterpriseOps Agent"
    )

    database_url: str

    database_host_override: str | None = None

    environment: str = "development"

    dashscope_api_key: str | None = None

    dashscope_base_url: str = (
        "https://dashscope.aliyuncs.com/"
        "compatible-mode/v1"
    )

    dashscope_chat_model: str = "qwen-plus"

    dashscope_embedding_model: str = (
        "text-embedding-v4"
    )

    dashscope_embedding_dimensions: int = 1024

    vector_collection_name: str = (
        "enterprise_policy_bailian_v4"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    redis_url: str = (
        "redis://localhost:6379/0"
    )

    @model_validator(mode="after")
    def apply_database_host_override(self):
        if self.database_host_override:
            url = make_url(self.database_url).set(
                host=self.database_host_override
            )
            self.database_url = url.render_as_string(
                hide_password=False
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
