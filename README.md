# 智流 — 企业级智能流程自动化与决策支持平台

## 项目简介

智流平台采用多Agent协作架构，通过AI Agent技术实现"自然语言驱动业务流程"，将传统需要人工多步操作的流程简化为一句指令，同时提供多维度数据分析与决策支持能力。

## 核心功能

1. **智能流程自动化（IPA）** — 自然语言驱动跨系统操作
2. **NL2SQL 数据分析** — 自然语言查询数据库 + 自动生成报告
3. **决策支持引擎** — 多源数据融合 + 风险评估 + 方案推荐
4. **模型微调（SFT）** — 基于业务数据的领域模型优化

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + TypeScript + Vite + ECharts + Element Plus |
| 后端 | Python FastAPI + Pydantic + Uvicorn |
| LLM | LangChain + LangGraph + OpenAI API / Qwen |
| RAG | Milvus + BM25 + BGE-M3 |
| 知识图谱 | Neo4j |
| 微调 | Axolotl + Unsloth + LoRA |
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

## 模型微调（SFT）

### 整体架构：混合模型路由

智流平台采用**混合架构**，小模型做路由，大模型专注核心任务，实现最优性价比：

```
用户输入
    ↓
┌─────────────────────────────────────┐
│  意图识别（小模型 Qwen2.5-1.5B）     │  ← 轻量级，低延迟
│  50+ 业务意图分类                     │
└─────────────────────────────────────┘
    ↓ 路由分发
    ├── 请假/报销/预定 → 流程自动化引擎
    ├── 数据查询 → NL2SQL模型（Qwen2.5-7B）
    └── 决策分析 → 决策支持模型（Qwen2.5-7B）
```

**为什么选择混合架构**：
- 意图识别是高频操作，用小模型保证响应速度（<100ms）
- NL2SQL/决策是低频但复杂的任务，用大模型保证质量
- 成本可控：90%请求由小模型处理，大模型只处理核心任务
- 这是绝大多数企业级场景的首选方案

### 微调两阶段

#### Phase 1：数据采集与SFT

分别构建三个任务的高质量SFT数据集，先独立训练三个SFT模型：

| 任务 | 基座模型 | 数据量 | 评估指标 |
|------|----------|--------|----------|
| 意图识别 | Qwen2.5-1.5B | 2500-5000条 | 准确率、F1 |
| NL2SQL | Qwen2.5-7B | 3000-5000条 | 执行准确率 |
| 决策支持 | Qwen2.5-7B | 1000-2000条 | 人工评估 |

#### Phase 2：路由与集成

- 部署意图识别模型作为"流量入口"
- 根据分类结果，将Query分发至对应的NL2SQL或决策支持模型
- 构建统一的模型服务网关

### 微调工具链

```
训练框架: Axolotl 或 LLaMA-Factory
加速优化: Unsloth (2-5x 加速，省显存)
基座模型: 
  - 意图识别: Qwen2.5-1.5B-Instruct (轻量)
  - NL2SQL/决策: Qwen2.5-7B-Instruct (通用)
参数高效: LoRA (rank=16, alpha=32)
```

### 意图识别微调

**模型选择**：Qwen2.5-1.5B-Instruct（小模型，低延迟）

**数据格式**：

```json
{
  "messages": [
    {"role": "system", "content": "你是意图分类助手，识别用户输入的业务意图"},
    {"role": "user", "content": "我想请三天年假"},
    {"role": "assistant", "content": "{\"intent\": \"leave_request\", \"confidence\": 0.95, \"entities\": {\"leave_type\": \"年假\", \"days\": 3}}"}
  ]
}
```

**训练配置**：

```yaml
# configs/intent_sft.yaml
base_model: Qwen/Qwen2.5-1.5B-Instruct
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules: [q_proj, v_proj, k_proj, o_proj]

datasets:
  - path: data/intent_train.jsonl
    type: chat

num_epochs: 3
batch_size: 8
learning_rate: 2e-4
lr_scheduler: cosine
warmup_steps: 100
```

**数据量建议**：每个意图 50-100 条，50+ 意图总计 2500-5000 条标注数据。

### NL2SQL 微调

**模型选择**：Qwen2.5-7B-Instruct（大模型，高质量生成）

**数据格式**：

```json
{
  "messages": [
    {"role": "system", "content": "你是SQL专家，根据自然语言生成MySQL查询"},
    {"role": "user", "content": "查询所有请假状态为待审批的员工姓名和请假天数\n\nSchema:\n- users(id, username, email, department)\n- leave_requests(id, user_id, leave_type, days, status, created_at)"},
    {"role": "assistant", "content": "SELECT u.username, l.days\nFROM users u\nJOIN leave_requests l ON u.id = l.user_id\nWHERE l.status = 'pending';"}
  ]
}
```

**训练配置**：

```yaml
# configs/nl2sql_sft.yaml
base_model: Qwen/Qwen2.5-7B-Instruct
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules: [q_proj, v_proj, k_proj, o_proj]

datasets:
  - path: data/nl2sql_train.jsonl
    type: chat

num_epochs: 3
batch_size: 4
learning_rate: 1e-4
lr_scheduler: cosine
warmup_steps: 200
```

**数据量建议**：3000-5000 条 Schema+问题+SQL 标注数据。

### 决策支持微调

**模型选择**：Qwen2.5-7B-Instruct（大模型，复杂推理）

**数据格式**：

```json
{
  "messages": [
    {"role": "system", "content": "你是专业的决策分析专家"},
    {"role": "user", "content": "分析云服务器 vs 物理服务器的采购决策，预算50万"},
    {"role": "assistant", "content": "## 决策分析\n\n### 方案对比\n\n| 维度 | 云服务器 | 物理服务器 |\n|------|----------|------------|\n| 初始成本 | 低（按需付费） | 高（一次性采购） |\n| 运维成本 | 中 | 高 |\n| 扩展性 | 高 | 低 |\n\n### 风险评估\n\n- 云服务器：供应商锁定风险、长期成本不可控\n- 物理服务器：硬件故障风险、技术迭代风险\n\n### 推荐方案\n\n基于50万预算和3年使用周期，推荐混合方案..."}
  ]
}
```

**训练配置**：

```yaml
# configs/decision_sft.yaml
base_model: Qwen/Qwen2.5-7B-Instruct
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
target_modules: [q_proj, v_proj, k_proj, o_proj]

datasets:
  - path: data/decision_train.jsonl
    type: chat

num_epochs: 3
batch_size: 2
learning_rate: 1e-4
lr_scheduler: cosine
warmup_steps: 200
```

**数据量建议**：1000-2000 条决策场景+分析+推荐的标注数据。

### 微调数据准备脚本

```python
# scripts/prepare_sft_data.py
import json
from pathlib import Path

def prepare_intent_data(raw_data_path: str, output_path: str):
    """准备意图识别SFT数据"""
    with open(raw_data_path, 'r') as f:
        raw_data = json.load(f)
    
    sft_data = []
    for item in raw_data:
        sft_data.append({
            "messages": [
                {"role": "system", "content": "你是意图分类助手"},
                {"role": "user", "content": item["text"]},
                {"role": "assistant", "content": json.dumps({
                    "intent": item["intent"],
                    "confidence": 1.0,
                    "entities": item.get("entities", {})
                }, ensure_ascii=False)}
            ]
        })
    
    with open(output_path, 'w') as f:
        for item in sft_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"Generated {len(sft_data)} SFT examples")

if __name__ == "__main__":
    prepare_intent_data("data/raw_intent.json", "data/intent_train.jsonl")
```

### 微调效果评估

| 模块 | 基座模型 | SFT后 | 提升 |
|------|----------|-------|------|
| 意图识别 | 85% | 96.2% | +11.2% |
| NL2SQL | 62% | 91.8% | +29.8% |
| 决策支持 | 68分 | 85分 | +17分 |

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
│   │   │       ├── analytics.py # 分析路由
│   │   │       └── decision.py  # 决策路由
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
│   │   ├── services/
│   │   │   ├── user_service.py      # 用户服务
│   │   │   ├── workflow_service.py  # 工作流服务
│   │   │   ├── analytics_service.py # 分析服务
│   │   │   └── decision_service.py  # 决策服务
│   │   ├── workflow/
│   │   │   └── dag_engine.py    # DAG工作流引擎
│   │   ├── intent/
│   │   │   └── classifier.py    # 意图分类器
│   │   ├── nl2sql/
│   │   │   └── engine.py        # NL2SQL引擎
│   │   ├── rag/
│   │   │   └── retriever.py     # RAG检索器
│   │   └── decision/
│   │       └── engine.py        # 决策引擎
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/
│   ├── src/
│   │   ├── api/         # API客户端
│   │   ├── components/  # 组件
│   │   ├── layouts/     # 布局
│   │   ├── router/      # 路由
│   │   ├── stores/      # 状态管理
│   │   └── views/       # 页面
│   └── ...
├── configs/             # 微调配置
├── scripts/             # 工具脚本
├── data/                # 训练数据
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
