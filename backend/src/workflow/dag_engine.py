"""
DAG 工作流引擎

实现轻量级的有向无环图（DAG）执行引擎，支持：
- 条件分支
- 并行执行
- 错误重试
- 超时熔断
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodeType(str, Enum):
    """节点类型"""
    TASK = "task"           # 普通任务
    CONDITION = "condition" # 条件判断
    PARALLEL = "parallel"   # 并行执行
    START = "start"         # 开始节点
    END = "end"             # 结束节点


@dataclass
class NodeConfig:
    """节点配置"""
    name: str
    node_type: NodeType = NodeType.TASK
    handler: Optional[str] = None  # 处理函数名
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # 超时时间（秒）
    retry_count: int = 0  # 重试次数
    retry_delay: int = 5  # 重试延迟（秒）
    condition: Optional[str] = None  # 条件表达式（用于条件节点）


@dataclass
class EdgeConfig:
    """边配置"""
    source: str
    target: str
    condition: Optional[str] = None  # 条件表达式


@dataclass
class DAGDefinition:
    """DAG 定义"""
    name: str
    description: str = ""
    nodes: List[NodeConfig] = field(default_factory=list)
    edges: List[EdgeConfig] = field(default_factory=list)
    start_node: str = ""
    end_node: str = ""


@dataclass
class NodeExecution:
    """节点执行记录"""
    node_name: str
    status: NodeStatus = NodeStatus.PENDING
    input_data: Any = None
    output_data: Any = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[NodeExecution] = field(default_factory=list)


# 任务处理器注册表
_task_handlers: Dict[str, Callable] = {}


def register_handler(name: str):
    """装饰器：注册任务处理器"""
    def decorator(func: Callable):
        _task_handlers[name] = func
        return func
    return decorator


def get_handler(name: str) -> Optional[Callable]:
    """获取任务处理器"""
    return _task_handlers.get(name)


class DAGEngine:
    """DAG 执行引擎"""

    def __init__(self, dag_definition: DAGDefinition):
        self.dag = dag_definition
        self.graph: Dict[str, List[str]] = {}  # 邻接表
        self._build_graph()

    def _build_graph(self):
        """构建图"""
        # 初始化所有节点
        for node in self.dag.nodes:
            self.graph[node.name] = []

        # 添加边
        for edge in self.dag.edges:
            if edge.source in self.graph:
                self.graph[edge.source].append(edge.target)

    def get_node(self, name: str) -> Optional[NodeConfig]:
        """获取节点配置"""
        for node in self.dag.nodes:
            if node.name == name:
                return node
        return None

    def get_successors(self, node_name: str) -> List[str]:
        """获取后继节点"""
        return self.graph.get(node_name, [])

    def validate(self) -> List[str]:
        """
        验证 DAG 定义

        Returns:
            错误消息列表，空表示验证通过
        """
        errors = []

        # 检查开始节点
        if not self.dag.start_node:
            errors.append("Missing start node")
        elif self.dag.start_node not in self.graph:
            errors.append(f"Start node '{self.dag.start_node}' not found")

        # 检查结束节点
        if not self.dag.end_node:
            errors.append("Missing end node")
        elif self.dag.end_node not in self.graph:
            errors.append(f"End node '{self.dag.end_node}' not found")

        # 检查是否有环
        if self._has_cycle():
            errors.append("DAG contains cycles")

        return errors

    def _has_cycle(self) -> bool:
        """检测是否有环"""
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.discard(node)
            return False

        for node in self.graph:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    async def execute(
        self,
        context: WorkflowContext,
        handlers: Optional[Dict[str, Callable]] = None,
    ) -> WorkflowContext:
        """
        执行工作流

        Args:
            context: 工作流上下文
            handlers: 自定义处理器（可选，覆盖全局注册的处理器）

        Returns:
            更新后的上下文
        """
        # 验证 DAG
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid DAG: {', '.join(errors)}")

        current_node = self.dag.start_node

        while current_node and current_node != self.dag.end_node:
            node_config = self.get_node(current_node)
            if not node_config:
                raise ValueError(f"Node '{current_node}' not found")

            # 执行节点
            execution = await self._execute_node(
                node_config, context, handlers
            )
            context.execution_history.append(execution)

            # 根据执行结果决定下一个节点
            if execution.status == NodeStatus.FAILED:
                # 失败时结束工作流
                break
            elif execution.status == NodeStatus.SKIPPED:
                # 跳过时跳过所有后继节点
                current_node = self.dag.end_node
            else:
                # 成功时继续执行后继节点
                successors = self.get_successors(current_node)
                if not successors:
                    current_node = self.dag.end_node
                else:
                    # 如果有多个后继节点，需要根据条件选择
                    if len(successors) == 1:
                        current_node = successors[0]
                    else:
                        # 条件分支
                        current_node = self._resolve_condition(
                            node_config, successors, context
                        )

        # 执行结束节点
        end_node = self.get_node(self.dag.end_node)
        if end_node:
            end_execution = NodeExecution(
                node_name=self.dag.end_node,
                status=NodeStatus.SUCCESS,
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )
            context.execution_history.append(end_execution)

        return context

    async def _execute_node(
        self,
        node_config: NodeConfig,
        context: WorkflowContext,
        handlers: Optional[Dict[str, Callable]] = None,
    ) -> NodeExecution:
        """执行单个节点"""
        execution = NodeExecution(
            node_name=node_config.name,
            status=NodeStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            # 获取处理器
            handler = None
            if handlers and node_config.handler in handlers:
                handler = handlers[node_config.handler]
            elif node_config.handler:
                handler = get_handler(node_config.handler)

            if handler:
                # 准备输入数据
                input_data = {
                    **context.input_data,
                    **context.variables,
                    **node_config.params,
                }
                execution.input_data = input_data

                # 执行处理器（支持重试）
                for attempt in range(node_config.retry_count + 1):
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            result = await asyncio.wait_for(
                                handler(input_data),
                                timeout=node_config.timeout,
                            )
                        else:
                            result = handler(input_data)

                        execution.output_data = result
                        execution.status = NodeStatus.SUCCESS
                        break

                    except asyncio.TimeoutError:
                        execution.error_message = f"Timeout after {node_config.timeout}s"
                        execution.retry_count = attempt + 1
                        if attempt < node_config.retry_count:
                            await asyncio.sleep(node_config.retry_delay)
                        else:
                            execution.status = NodeStatus.FAILED

                    except Exception as e:
                        execution.error_message = str(e)
                        execution.retry_count = attempt + 1
                        if attempt < node_config.retry_count:
                            await asyncio.sleep(node_config.retry_delay)
                        else:
                            execution.status = NodeStatus.FAILED
            else:
                # 没有处理器，视为成功
                execution.status = NodeStatus.SUCCESS

        except Exception as e:
            execution.status = NodeStatus.FAILED
            execution.error_message = str(e)

        execution.completed_at = datetime.now()
        return execution

    def _resolve_condition(
        self,
        current_node: NodeConfig,
        successors: List[str],
        context: WorkflowContext,
    ) -> str:
        """解析条件分支"""
        # 简单的条件解析（实际项目中应使用更复杂的表达式引擎）
        for successor in successors:
            edge = self._find_edge(current_node.name, successor)
            if edge and edge.condition:
                # 评估条件
                try:
                    result = eval(
                        edge.condition,
                        {"context": context, **context.variables}
                    )
                    if result:
                        return successor
                except Exception:
                    continue

        # 默认返回第一个后继节点
        return successors[0] if successors else self.dag.end_node

    def _find_edge(self, source: str, target: str) -> Optional[EdgeConfig]:
        """查找边"""
        for edge in self.dag.edges:
            if edge.source == source and edge.target == target:
                return edge
        return None


def create_dag_from_json(json_str: str) -> DAGEngine:
    """
    从 JSON 创建 DAG 引擎

    Args:
        json_str: JSON 格式的 DAG 定义

    Returns:
        DAG 引擎实例
    """
    data = json.loads(json_str)

    nodes = [NodeConfig(**node) for node in data.get("nodes", [])]
    edges = [EdgeConfig(**edge) for edge in data.get("edges", [])]

    dag_def = DAGDefinition(
        name=data.get("name", ""),
        description=data.get("description", ""),
        nodes=nodes,
        edges=edges,
        start_node=data.get("start_node", ""),
        end_node=data.get("end_node", ""),
    )

    return DAGEngine(dag_def)
