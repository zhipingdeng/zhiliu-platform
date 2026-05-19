# 智流 — 企业级智能流程自动化与决策支持平台

## 项目简介

智流平台采用多Agent协作架构，通过AI Agent技术实现"自然语言驱动业务流程"，将传统需要人工多步操作的流程简化为一句指令，同时提供多维度数据分析与决策支持能力。

## 核心功能

1. **智能流程自动化（IPA）** — 自然语言驱动跨系统操作
2. **NL2SQL 数据分析** — 自然语言查询数据库 + 自动生成报告
3. **决策支持引擎** — 多源数据融合 + 风险评估 + 方案推荐

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + TypeScript + Vite + ECharts + Element Plus |
| 后端 | Python FastAPI + Pydantic + Uvicorn |
| LLM | LangChain + LangGraph + OpenAI API / Qwen |
| RAG | Milvus + BM25 + BGE-M3 |
| 知识图谱 | Neo4j |
| 数据库 | MySQL 8.0 + Redis |
| 任务调度 | Celery + RabbitMQ |
| 工作流 | 自研DAG执行引擎 + FSM |
| 部署 | Docker + Docker Compose + Nginx |

## 快速开始

### 1. 创建 Conda 环境

```bash
conda create -n zhiliu python=3.11 -y
conda activate zhiliu
```

### 2. 安装依赖

```bash
pip install -e .
pip install -e ".[dev]"
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 4. 启动数据库

```bash
docker-compose up -d
```

### 5. 运行测试

```bash
pytest backend/tests/ -v
```

### 6. 启动服务

```bash
cd backend
python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

## 项目结构

```
zhiliu-platform/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── app.py           # FastAPI 应用工厂
│   │   │   └── routes/
│   │   │       ├── auth.py      # 认证路由
│   │   │       ├── workflow.py  # 工作流路由
│   │   │       └── analytics.py # 分析路由
│   │   ├── config/
│   │   │   └── settings.py      # 配置管理
│   │   ├── database/
│   │   │   ├── connection.py    # 数据库连接
│   │   │   └── models.py        # SQLAlchemy 模型
│   │   ├── auth/
│   │   │   ├── jwt.py           # JWT 工具
│   │   │   └── dependencies.py  # 认证依赖
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic 模型
│   │   └── services/
│   │       └── user_service.py  # 用户服务
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/
├── docs/
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── .gitignore
```

## 开发规范

- **TDD**: 测试驱动开发，先写测试再写代码
- **Conventional Commits**: 使用规范化的 Git 提交信息
- **Async/Await**: 优先使用异步编程
- **代码风格**: PEP8 / Google Style

## 许可证

MIT License
