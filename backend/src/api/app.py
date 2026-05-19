"""
FastAPI 应用工厂模块

创建和配置 FastAPI 应用实例。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.database.connection import init_db, close_db
from src.api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时清理资源
    await close_db()


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    Returns:
        配置好的 FastAPI 应用
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="智流 — 企业级智能流程自动化与决策支持平台",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth_router, prefix="/api/v1")

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": settings.app_name}

    return app
