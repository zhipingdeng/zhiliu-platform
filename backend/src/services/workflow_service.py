"""
工作流服务模块

提供工作流的创建、执行、查询等业务逻辑。
"""

from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    Workflow,
    WorkflowStatus,
    WorkflowExecution,
    ExecutionStatus,
)
from src.models.schemas import WorkflowCreate
from src.workflow.dag_engine import (
    DAGEngine,
    DAGDefinition,
    NodeConfig,
    EdgeConfig,
    NodeType,
    WorkflowContext,
    create_dag_from_json,
)


class WorkflowService:
    """工作流服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(
        self, owner_id: int, workflow_data: WorkflowCreate
    ) -> Workflow:
        """
        创建工作流

        Args:
            owner_id: 所有者 ID
            workflow_data: 工作流创建数据

        Returns:
            创建的工作流对象
        """
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            owner_id=owner_id,
            status=WorkflowStatus.DRAFT,
            dag_definition=workflow_data.dag_definition,
        )

        self.db.add(workflow)
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """获取工作流"""
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self, owner_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[Workflow]:
        """获取工作流列表"""
        query = select(Workflow)
        if owner_id:
            query = query.where(Workflow.owner_id == owner_id)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_workflow_status(
        self, workflow_id: int, status: WorkflowStatus
    ) -> Optional[Workflow]:
        """更新工作流状态"""
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        workflow.status = status
        await self.db.flush()
        await self.db.refresh(workflow)
        return workflow

    async def execute_workflow(
        self, workflow_id: int, input_data: Dict[str, Any]
    ) -> WorkflowExecution:
        """
        执行工作流

        Args:
            workflow_id: 工作流 ID
            input_data: 输入数据

        Returns:
            执行记录
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            input_data=json.dumps(input_data, ensure_ascii=False),
            started_at=datetime.now(),
        )
        self.db.add(execution)
        await self.db.flush()
        await self.db.refresh(execution)

        try:
            # 解析 DAG 定义
            if not workflow.dag_definition:
                raise ValueError("Workflow has no DAG definition")

            # 创建 DAG 引擎
            dag_engine = create_dag_from_json(workflow.dag_definition)

            # 创建执行上下文
            context = WorkflowContext(
                workflow_id=str(workflow_id),
                input_data=input_data,
            )

            # 执行工作流
            context = await dag_engine.execute(context)

            # 更新执行记录
            execution.status = ExecutionStatus.SUCCESS
            execution.output_data = json.dumps(
                {"execution_history": [
                    {
                        "node": ex.node_name,
                        "status": ex.status.value,
                        "output": ex.output_data,
                    }
                    for ex in context.execution_history
                ]},
                ensure_ascii=False,
            )
            execution.completed_at = datetime.now()

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()

        await self.db.flush()
        await self.db.refresh(execution)
        return execution

    async def get_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """获取执行记录"""
        result = await self.db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def list_executions(
        self, workflow_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[WorkflowExecution]:
        """获取执行记录列表"""
        query = select(WorkflowExecution)
        if workflow_id:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)
        query = query.order_by(WorkflowExecution.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
