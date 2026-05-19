"""
工作流路由模块

提供工作流的 CRUD 和执行 API。
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.database.models import User, WorkflowStatus
from src.models.schemas import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowExecutionResponse,
    MessageResponse,
)
from src.services.workflow_service import WorkflowService
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/workflows", tags=["工作流"])


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """
    创建工作流
    """
    service = WorkflowService(db)
    workflow = await service.create_workflow(current_user.id, workflow_data)
    return WorkflowResponse.model_validate(workflow)


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WorkflowResponse]:
    """
    获取工作流列表
    """
    service = WorkflowService(db)
    workflows = await service.list_workflows(
        owner_id=current_user.id, skip=skip, limit=limit
    )
    return [WorkflowResponse.model_validate(w) for w in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """
    获取工作流详情
    """
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    # 检查权限
    if workflow.owner_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return WorkflowResponse.model_validate(workflow)


@router.put("/{workflow_id}/activate", response_model=WorkflowResponse)
async def activate_workflow(
    workflow_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """
    激活工作流
    """
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    if workflow.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    workflow = await service.update_workflow_status(
        workflow_id, WorkflowStatus.ACTIVE
    )
    return WorkflowResponse.model_validate(workflow)


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    input_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowExecutionResponse:
    """
    执行工作流
    """
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    if workflow.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if workflow.status != WorkflowStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow is not active",
        )

    try:
        execution = await service.execute_workflow(workflow_id, input_data)
        return WorkflowExecutionResponse.model_validate(execution)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[WorkflowExecutionResponse]:
    """
    获取工作流执行记录
    """
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    if workflow.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    executions = await service.list_executions(
        workflow_id=workflow_id, skip=skip, limit=limit
    )
    return [WorkflowExecutionResponse.model_validate(e) for e in executions]
