<template>
  <div class="workflow-detail">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">{{ workflow?.name || '工作流详情' }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>工作流信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="名称">{{ workflow?.name }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(workflow?.status || '')">
                {{ getStatusLabel(workflow?.status || '') }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ workflow?.description || '暂无描述' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(workflow?.created_at || '') }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDate(workflow?.updated_at || '') }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card style="margin-top: 20px">
          <template #header>
            <span>执行记录</span>
          </template>
          <el-table :data="executions" style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getExecStatusType(row.status)">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" />
            <el-table-column prop="completed_at" label="完成时间" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>执行工作流</span>
          </template>
          <el-form label-width="80px">
            <el-form-item label="输入数据">
              <el-input
                v-model="executeInput"
                type="textarea"
                :rows="6"
                placeholder='请输入 JSON 格式的输入数据，例如：{"key": "value"}'
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="executing"
                :disabled="workflow?.status !== 'active'"
                @click="executeWorkflow"
              >
                执行
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { workflowApi } from '@/api'

const route = useRoute()
const workflow = ref(null)
const executions = ref([])
const executeInput = ref('{}')
const executing = ref(false)

onMounted(() => {
  const id = Number(route.params.id)
  fetchWorkflow(id)
  fetchExecutions(id)
})

async function fetchWorkflow(id: number) {
  try {
    workflow.value = await workflowApi.get(id) as never
  } catch {
    ElMessage.error('获取工作流详情失败')
  }
}

async function fetchExecutions(id: number) {
  try {
    executions.value = await workflowApi.getExecutions(id) as never
  } catch {
    // ignore
  }
}

async function executeWorkflow() {
  if (!workflow.value) return
  executing.value = true
  try {
    const inputData = JSON.parse(executeInput.value)
    await workflowApi.execute((workflow.value as { id: number }).id, inputData)
    ElMessage.success('执行成功')
    fetchExecutions((workflow.value as { id: number }).id)
  } catch (error: unknown) {
    if (error instanceof SyntaxError) {
      ElMessage.error('输入数据格式错误，请输入有效的 JSON')
    } else {
      ElMessage.error('执行失败')
    }
  } finally {
    executing.value = false
  }
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    draft: 'info', active: 'success', paused: 'warning',
    completed: '', failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    draft: '草稿', active: '运行中', paused: '已暂停',
    completed: '已完成', failed: '失败',
  }
  return map[status] || status
}

function getExecStatusType(status: string) {
  const map: Record<string, string> = {
    pending: 'info', running: 'warning', success: 'success',
    failed: 'danger', cancelled: 'info',
  }
  return map[status] || 'info'
}

function formatDate(dateStr: string) {
  return dateStr ? new Date(dateStr).toLocaleString('zh-CN') : '-'
}
</script>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: bold;
}
</style>
