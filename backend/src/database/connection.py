"""
数据库连接管理模块

使用 SQLAlchemy 2.0 异步引擎，支持连接池和会话管理。
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from src.config.settings import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


_engine = None
_session_factory = None


async def init_db() -> None:
    """初始化数据库连接"""
    global _engine, _session_factory

    settings = get_settings()
    _engine = create_async_engine(
        settings.mysql_url,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # 创建所有表
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None


def get_session() -> AsyncSession:
    """获取数据库会话"""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取数据库会话"""
    session = get_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def check_db_health() -> bool:
    """检查数据库健康状态"""
    try:
        session = get_session()
        async with session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
