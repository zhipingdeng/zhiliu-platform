<template>
  <div class="analytics-view">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>Natural Language Query</span>
          </template>
          <el-input
            v-model="query"
            placeholder="e.g., How many users are there?"
            clearable
            @keyup.enter="executeQuery"
          >
            <template #append>
              <el-button :loading="querying" @click="executeQuery">
                <el-icon><Search /></el-icon>
                Query
              </el-button>
            </template>
          </el-input>

          <div v-if="queryResult" style="margin-top: 20px">
            <el-alert
              :title="queryResult.success ? 'Query Success' : 'Query Failed'"
              :type="queryResult.success ? 'success' : 'error'"
              :description="queryResult.explanation || queryResult.error"
              show-icon
              :closable="false"
            />

            <div v-if="queryResult.success && queryResult.data.length > 0" style="margin-top: 16px">
              <p><strong>SQL:</strong> {{ queryResult.sql }}</p>
              <p><strong>Rows:</strong> {{ queryResult.row_count }}</p>
              <el-table :data="queryResult.data" style="width: 100%; margin-top: 10px" max-height="400">
                <el-table-column
                  v-for="col in queryResult.columns"
                  :key="col"
                  :prop="col"
                  :label="col"
                  show-overflow-tooltip
                />
              </el-table>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>Database Schema</span>
          </template>
          <div v-loading="loadingSchema">
            <el-collapse v-model="activeTables">
              <el-collapse-item
                v-for="table in schema"
                :key="table.name"
                :title="table.name"
                :name="table.name"
              >
                <p v-if="table.description" style="color: #909399; margin-bottom: 8px">
                  {{ table.description }}
                </p>
                <el-table :data="table.columns" size="small">
                  <el-table-column prop="name" label="Column" />
                  <el-table-column prop="data_type" label="Type" />
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { analyticsApi } from '@/api'

const query = ref('')
const querying = ref(false)
const queryResult = ref(null)
const schema = ref([])
const loadingSchema = ref(false)
const activeTables = ref([])

onMounted(() => {
  fetchSchema()
})

async function fetchSchema() {
  loadingSchema.value = true
  try {
    const data = await analyticsApi.getSchema()
    schema.value = (data as { tables: [] }).tables
  } catch {
    // ignore
  } finally {
    loadingSchema.value = false
  }
}

async function executeQuery() {
  if (!query.value.trim()) {
    ElMessage.warning('Please enter a query')
    return
  }
  querying.value = true
  try {
    queryResult.value = await analyticsApi.query(query.value) as never
  } catch {
    ElMessage.error('Query failed')
  } finally {
    querying.value = false
  }
}
</script>
