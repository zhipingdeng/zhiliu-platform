"""
JWT 工具测试
"""

import pytest
from datetime import datetime, timedelta, timezone
from src.auth.jwt import create_access_token, decode_token, create_refresh_token


class TestJWT:
    """JWT 工具测试类"""

    def test_create_access_token(self):
        """测试创建 access token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        """测试解码有效 token"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_decode_token_expired(self):
        """测试解码过期 token"""
        data = {"sub": "testuser"}
        token = create_access_token(
            data, expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(ValueError, match="Invalid token"):
            decode_token(token)

    def test_decode_token_invalid(self):
        """测试解码无效 token"""
        with pytest.raises(ValueError, match="Invalid token"):
            decode_token("invalid.token.here")

    def test_create_refresh_token(self):
        """测试创建 refresh token"""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

        payload = decode_token(token)
        assert payload["sub"] == "testuser"
        assert payload["type"] == "refresh"

    def test_token_with_custom_expiry(self):
        """测试自定义过期时间的 token"""
        data = {"sub": "testuser"}
        expires = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires)

        payload = decode_token(token)
        assert payload["sub"] == "testuser"
