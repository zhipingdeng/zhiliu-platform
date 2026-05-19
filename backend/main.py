"""
应用入口点
"""

import uvicorn
from src.config.settings import get_settings


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.api.app:create_app",
        factory=True,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
