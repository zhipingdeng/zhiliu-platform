"""
决策支持路由模块

提供决策分析、风险评估、知识库管理等 API。
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.database.connection import get_db
from src.database.models import User
from src.decision.engine import DecisionRequest, DecisionResult, DecisionType
from src.services.decision_service import DecisionService
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/decision", tags=["决策支持"])


class RiskAssessmentRequest(BaseModel):
    """风险评估请求"""
    decision_type: DecisionType = Field(description="决策类型")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class RiskAssessmentResponse(BaseModel):
    """风险评估响应"""
    overall_risk_level: str = "medium"
    risk_factors: List[Dict[str, Any]] = []
    mitigation_strategies: List[str] = []


class KnowledgeAddRequest(BaseModel):
    """知识添加请求"""
    documents: List[Dict[str, Any]] = Field(description="文档列表")


class KnowledgeAddResponse(BaseModel):
    """知识添加响应"""
    ids: List[str]


class KnowledgeQueryRequest(BaseModel):
    """知识查询请求"""
    question: str = Field(description="问题")
    top_k: int = Field(default=5, description="返回数量")


class KnowledgeQueryResponse(BaseModel):
    """知识查询响应"""
    answer: str = ""
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0


@router.post("/analyze", response_model=DecisionResult)
async def analyze_decision(
    request: DecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DecisionResult:
    """
    决策分析

    分析决策选项并给出推荐。
    """
    service = DecisionService(db)
    result = await service.analyze_decision(request)
    return result


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def risk_assessment(
    request: RiskAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentResponse:
    """
    风险评估

    对决策进行风险评估。
    """
    service = DecisionService(db)
    result = await service.assess_risk(request.decision_type, request.context)
    return RiskAssessmentResponse(**result)


@router.post("/knowledge/add", response_model=KnowledgeAddResponse)
async def add_knowledge(
    request: KnowledgeAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeAddResponse:
    """
    添加知识

    添加文档到知识库。
    """
    service = DecisionService(db)
    ids = await service.add_knowledge(request.documents)
    return KnowledgeAddResponse(ids=ids)


@router.post("/knowledge/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(
    request: KnowledgeQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeQueryResponse:
    """
    查询知识库

    基于 RAG 检索知识库并回答问题。
    """
    service = DecisionService(db)
    result = await service.query_knowledge(request.question, request.top_k)
    return KnowledgeQueryResponse(**result)
