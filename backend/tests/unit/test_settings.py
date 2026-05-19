"""
配置测试
"""

import pytest
from src.config.settings import Settings, get_settings


class TestSettings:
    """配置测试类"""

    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()

        assert settings.app_name == "智流平台"
        assert settings.app_port == 8000
        assert settings.mysql_port == 3307
        assert settings.redis_port == 6380

    def test_mysql_url(self):
        """测试 MySQL URL 生成"""
        settings = Settings(
            mysql_user="testuser",
            mysql_password="testpass",
            mysql_host="testhost",
            mysql_port=3306,
            mysql_database="testdb",
        )

        url = settings.mysql_url
        assert "testuser" in url
        assert "testpass" in url
        assert "testhost" in url
        assert "3306" in url
        assert "testdb" in url
        assert "aiomysql" in url

    def test_redis_url(self):
        """测试 Redis URL 生成"""
        settings = Settings(
            redis_host="redishost",
            redis_port=6379,
            redis_db=1,
        )

        url = settings.redis_url
        assert "redishost" in url
        assert "6379" in url
        assert "/1" in url

    def test_get_settings_cached(self):
        """测试配置缓存"""
        settings1 = get_settings()
        settings2 = get_settings()

        # 应该返回同一个实例（缓存）
        assert settings1 is settings2
