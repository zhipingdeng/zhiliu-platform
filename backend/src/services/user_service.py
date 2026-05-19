"""
用户服务模块

提供用户相关的业务逻辑。
"""

from typing import Optional, List
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, UserRole
from src.models.schemas import UserCreate, UserUpdate


def hash_password(password: str) -> str:
    """
    哈希密码

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


class UserService:
    """用户服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户

        Args:
            user_data: 用户创建数据

        Returns:
            创建的用户对象

        Raises:
            ValueError: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing = await self.get_user_by_username(user_data.username)
        if existing:
            raise ValueError(f"Username '{user_data.username}' already exists")

        # 检查邮箱是否已存在
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError(f"Email '{user_data.email}' already exists")

        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            department=user_data.department,
            role=UserRole.USER,
            is_active=True,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def authenticate_user(
        self, username: str, password: str
    ) -> Optional[User]:
        """
        验证用户

        Args:
            username: 用户名
            password: 密码

        Returns:
            验证成功返回用户对象，失败返回 None
        """
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user(
        self, user_id: int, user_data: UserUpdate
    ) -> Optional[User]:
        """
        更新用户信息

        Args:
            user_id: 用户 ID
            user_data: 更新数据

        Returns:
            更新后的用户对象
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """获取用户列表"""
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())
