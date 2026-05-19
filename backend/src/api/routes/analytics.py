"""
数据分析路由模块

提供 NL2SQL 查询、数据分析、报告生成等 API。
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.database.connection import get_db
from src.database.models import User
from src.services.analytics_service import AnalyticsService
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/analytics", tags=["数据分析"])


class NLQueryRequest(BaseModel):
    """自然语言查询请求"""
    question: str = Field(description="自然语言问题")


class NLQueryResponse(BaseModel):
    """自然语言查询响应"""
    success: bool
    sql: str = ""
    explanation: str = ""
    confidence: float = 0.0
    data: List[Dict[str, Any]] = []
    columns: List[str] = []
    row_count: int = 0
    error: str = ""


class ReportRequest(BaseModel):
    """报告生成请求"""
    topic: str = Field(description="报告主题")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="数据")


class ReportResponse(BaseModel):
    """报告生成响应"""
    report: str


class TrendRequest(BaseModel):
    """趋势分析请求"""
    table: str = Field(description="表名")
    date_column: str = Field(description="日期列")
    value_column: str = Field(description="值列")
    days: int = Field(default=30, description="天数")


class TrendResponse(BaseModel):
    """趋势分析响应"""
    success: bool
    data: List[Dict[str, Any]] = []
    columns: List[str] = []
    error: str = ""


@router.post("/query", response_model=NLQueryResponse)
async def nl_query(
    request: NLQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NLQueryResponse:
    """
    自然语言数据查询

    将自然语言问题转换为 SQL 并执行查询。
    """
    service = AnalyticsService(db)
    result = await service.query_with_nl(request.question)
    return NLQueryResponse(**result)


@router.post("/report", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """
    生成分析报告

    根据主题和数据生成分析报告。
    """
    service = AnalyticsService(db)
    report = await service.generate_report(request.topic, request.data)
    return ReportResponse(report=report)


@router.post("/trend", response_model=TrendResponse)
async def trend_analysis(
    request: TrendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    """
    趋势分析

    获取指定表的时间趋势分析。
    """
    service = AnalyticsService(db)
    result = await service.get_trend_analysis(
        request.table,
        request.date_column,
        request.value_column,
        request.days,
    )
    return TrendResponse(**result)


@router.get("/schema")
async def get_schema(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取数据库 Schema

    返回当前数据库的表结构信息。
    """
    service = AnalyticsService(db)
    schema = await service.get_database_schema()

    return {
        "tables": [
            {
                "name": table.name,
                "description": table.description,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "description": col.description,
                        "is_primary_key": col.is_primary_key,
                    }
                    for col in table.columns
                ],
            }
            for table in schema.tables
        ]
    }
