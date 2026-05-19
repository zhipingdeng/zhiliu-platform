"""
Pydantic 模型定义

定义请求和响应的数据模型。
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ============================================
# 用户相关模型
# ============================================

class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = None
    department: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    department: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """用户更新请求"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None


# ============================================
# 认证相关模型
# ============================================

class Token(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token 数据"""
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """刷新 token 请求"""
    refresh_token: str


# ============================================
# 工作流相关模型
# ============================================

class WorkflowCreate(BaseModel):
    """工作流创建请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    dag_definition: Optional[str] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    id: int
    workflow_id: int
    status: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# 通用响应模型
# ============================================

class MessageResponse(BaseModel):
    """消息响应"""
    message: str


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
