"""
DAG 引擎测试
"""

import pytest
import asyncio
from src.workflow.dag_engine import (
    DAGEngine,
    DAGDefinition,
    NodeConfig,
    EdgeConfig,
    NodeType,
    WorkflowContext,
    NodeStatus,
    register_handler,
)


class TestDAGEngine:
    """DAG 引擎测试类"""

    def test_dag_validation_success(self):
        """测试 DAG 验证成功"""
        dag = DAGDefinition(
            name="test",
            nodes=[
                NodeConfig(name="start", node_type=NodeType.START),
                NodeConfig(name="task1", node_type=NodeType.TASK),
                NodeConfig(name="end", node_type=NodeType.END),
            ],
            edges=[
                EdgeConfig(source="start", target="task1"),
                EdgeConfig(source="task1", target="end"),
            ],
            start_node="start",
            end_node="end",
        )

        engine = DAGEngine(dag)
        errors = engine.validate()

        assert len(errors) == 0

    def test_dag_validation_missing_start(self):
        """测试 DAG 验证失败 - 缺少开始节点"""
        dag = DAGDefinition(
            name="test",
            nodes=[
                NodeConfig(name="task1", node_type=NodeType.TASK),
                NodeConfig(name="end", node_type=NodeType.END),
            ],
            edges=[
                EdgeConfig(source="task1", target="end"),
            ],
            start_node="",
            end_node="end",
        )

        engine = DAGEngine(dag)
        errors = engine.validate()

        assert len(errors) > 0
        assert any("start" in e.lower() for e in errors)

    def test_dag_validation_cycle(self):
        """测试 DAG 验证失败 - 存在环"""
        dag = DAGDefinition(
            name="test",
            nodes=[
                NodeConfig(name="start", node_type=NodeType.START),
                NodeConfig(name="task1", node_type=NodeType.TASK),
                NodeConfig(name="task2", node_type=NodeType.TASK),
                NodeConfig(name="end", node_type=NodeType.END),
            ],
            edges=[
                EdgeConfig(source="start", target="task1"),
                EdgeConfig(source="task1", target="task2"),
                EdgeConfig(source="task2", target="task1"),  # 环
                EdgeConfig(source="task2", target="end"),
            ],
            start_node="start",
            end_node="end",
        )

        engine = DAGEngine(dag)
        errors = engine.validate()

        assert len(errors) > 0
        assert any("cycle" in e.lower() for e in errors)

    def test_dag_get_node(self):
        """测试获取节点"""
        dag = DAGDefinition(
            name="test",
            nodes=[
                NodeConfig(name="start", node_type=NodeType.START),
                NodeConfig(name="task1", node_type=NodeType.TASK, handler="test"),
            ],
            edges=[],
            start_node="start",
            end_node="start",
        )

        engine = DAGEngine(dag)

        node = engine.get_node("start")
        assert node is not None
        assert node.name == "start"

        node = engine.get_node("task1")
        assert node is not None
        assert node.handler == "test"

        node = engine.get_node("nonexistent")
        assert node is None

    def test_dag_get_successors(self):
        """测试获取后继节点"""
        dag = DAGDefinition(
            name="test",
            nodes=[
                NodeConfig(name="start", node_type=NodeType.START),
                NodeConfig(name="task1", node_type=NodeType.TASK),
                NodeConfig(name="task2", node_type=NodeType.TASK),
            ],
            edges=[
                EdgeConfig(source="start", target="task1"),
                EdgeConfig(source="start", target="task2"),
            ],
            start_node="start",
            end_node="start",
        )

        engine = DAGEngine(dag)

        successors = engine.get_successors("start")
        assert len(successors) == 2
        assert "task1" in successors
        assert "task2" in successors

        successors = engine.get_successors("task1")
        assert len(successors) == 0


@pytest.mark.asyncio
class TestDAGExecution:
    """DAG 执行测试类"""

    async def test_simple_execution(self):
        """测试简单执行"""
        # 注册处理器
        @register_handler("echo")
        async def echo_handler(data):
            return {"echo": data.get("input", "")}

        dag = DAGDefinition(
            name="test",
            nodes=[
                NodeConfig(name="start", node_type=NodeType.START),
                NodeConfig(name="echo", node_type=NodeType.TASK, handler="echo"),
                NodeConfig(name="end", node_type=NodeType.END),
            ],
            edges=[
                EdgeConfig(source="start", target="echo"),
                EdgeConfig(source="echo", target="end"),
            ],
            start_node="start",
            end_node="end",
        )

        engine = DAGEngine(dag)
        context = WorkflowContext(
            workflow_id="test",
            input_data={"input": "hello"},
        )

        result = await engine.execute(context)

        assert len(result.execution_history) >= 2
        # echo 节点应该成功
        echo_execution = next(
            (e for e in result.execution_history if e.node_name == "echo"),
            None,
        )
        assert echo_execution is not None
        assert echo_execution.status == NodeStatus.SUCCESS
