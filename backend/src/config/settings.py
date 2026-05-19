"""
智流平台配置管理模块

使用 pydantic-settings 管理所有配置项，支持 .env 文件和环境变量。
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # --- 应用配置 ---
    app_name: str = "智流平台"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # --- 数据库配置 ---
    mysql_host: str = "localhost"
    mysql_port: int = 3307
    mysql_user: str = "root"
    mysql_password: str = "123456"
    mysql_database: str = "zhiliu"

    # --- Redis 配置 ---
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0

    # --- Neo4j 配置 ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "12345678"

    # --- Milvus 配置 ---
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # --- LLM 配置 ---
    llm_model_name: str = "mimo-v2.5-pro"
    llm_api_key: str = ""
    llm_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"

    # --- Embedding 模型配置 ---
    embedding_model_name: str = "bge-m3"
    embedding_base_url: str = "http://172.22.80.1:11434"
    embedding_api_key: str = "ollama"

    # --- JWT 配置 ---
    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # --- Celery 配置 ---
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6380/1"

    @property
    def mysql_url(self) -> str:
        """异步 MySQL 连接 URL"""
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        """Redis 连接 URL"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
