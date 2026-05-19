"""
JWT 工具模块

提供 JWT token 的创建和验证功能。
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt import InvalidTokenError

from src.config.settings import get_settings


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建 JWT access token

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        编码后的 JWT token 字符串
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    解码 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的数据字典

    Raises:
        ValueError: token 无效或过期
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建 JWT refresh token

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量（默认 7 天）

    Returns:
        编码后的 JWT refresh token 字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode.update({"exp": expire, "type": "refresh"})
    settings = get_settings()
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt
