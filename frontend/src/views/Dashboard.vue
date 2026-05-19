<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff">
              <el-icon :size="28"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.workflows }}</div>
              <div class="stat-label">工作流总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon :size="28"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.executions }}</div>
              <div class="stat-label">执行次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon :size="28"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.queries }}</div>
              <div class="stat-label">数据查询</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon :size="28"><Opportunity /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.decisions }}</div>
              <div class="stat-label">决策分析</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>快速入口</span>
          </template>
          <el-row :gutter="16">
            <el-col :span="8">
              <el-button
                class="quick-btn"
                type="primary"
                plain
                @click="$router.push('/workflows')"
              >
                <el-icon :size="24"><Connection /></el-icon>
                <span>流程管理</span>
              </el-button>
            </el-col>
            <el-col :span="8">
              <el-button
                class="quick-btn"
                type="success"
                plain
                @click="$router.push('/analytics')"
              >
                <el-icon :size="24"><DataAnalysis /></el-icon>
                <span>数据分析</span>
              </el-button>
            </el-col>
            <el-col :span="8">
              <el-button
                class="quick-btn"
                type="warning"
                plain
                @click="$router.push('/decision')"
              >
                <el-icon :size="24"><Opportunity /></el-icon>
                <span>决策支持</span>
              </el-button>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">智流平台</el-descriptions-item>
            <el-descriptions-item label="版本">v0.1.0</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag type="success">运行中</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const stats = reactive({
  workflows: 12,
  executions: 1580,
  queries: 342,
  decisions: 56,
})
</script>

<style scoped>
.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.quick-btn {
  width: 100%;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>
