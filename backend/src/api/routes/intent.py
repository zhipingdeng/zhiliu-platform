"""
意图识别路由模块

提供意图识别 API。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.database.models import User
from src.models.schemas import MessageResponse
from src.intent.classifier import IntentClassifier, IntentResult
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/intent", tags=["意图识别"])


@router.post("/classify", response_model=IntentResult)
async def classify_intent(
    text: str,
    current_user: User = Depends(get_current_user),
) -> IntentResult:
    """
    分类用户意图

    Args:
        text: 用户输入文本

    Returns:
        意图识别结果
    """
    classifier = IntentClassifier()
    result = await classifier.classify(text)
    return result


@router.post("/classify-sync", response_model=IntentResult)
async def classify_intent_sync(
    text: str,
    current_user: User = Depends(get_current_user),
) -> IntentResult:
    """
    同步分类用户意图（用于测试）

    Args:
        text: 用户输入文本

    Returns:
        意图识别结果
    """
    classifier = IntentClassifier()
    result = classifier.classify_sync(text)
    return result
