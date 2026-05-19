"""
用户服务测试
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from src.services.user_service import hash_password, verify_password


class TestPasswordUtils:
    """密码工具测试类"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_hash_password_different_each_time(self):
        """测试每次哈希结果不同"""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        # 但都能验证通过
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
