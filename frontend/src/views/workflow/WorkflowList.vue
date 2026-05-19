<template>
  <div class="workflow-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工作流管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建工作流
          </el-button>
        </div>
      </template>

      <el-table :data="workflows" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row.id)">查看</el-button>
            <el-button
              size="small"
              type="success"
              :disabled="row.status !== 'draft'"
              @click="activateWorkflow(row.id)"
            >
              激活
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建工作流对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建工作流" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" placeholder="请输入工作流名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入工作流描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createWorkflow">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { workflowApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const showCreateDialog = ref(false)
const workflows = ref([])

const createForm = reactive({
  name: '',
  description: '',
})

onMounted(() => {
  fetchWorkflows()
})

async function fetchWorkflows() {
  loading.value = true
  try {
    const data = await workflowApi.list()
    workflows.value = data as []
  } catch {
    ElMessage.error('获取工作流列表失败')
  } finally {
    loading.value = false
  }
}

async function createWorkflow() {
  if (!createForm.name) {
    ElMessage.warning('请输入工作流名称')
    return
  }
  try {
    await workflowApi.create(createForm)
    ElMessage.success('创建工作流成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    fetchWorkflows()
  } catch {
    ElMessage.error('创建工作流失败')
  }
}

async function activateWorkflow(id: number) {
  try {
    await workflowApi.activate(id)
    ElMessage.success('激活成功')
    fetchWorkflows()
  } catch {
    ElMessage.error('激活失败')
  }
}

function viewDetail(id: number) {
  router.push(`/workflows/${id}`)
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    draft: 'info',
    active: 'success',
    paused: 'warning',
    completed: '',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
