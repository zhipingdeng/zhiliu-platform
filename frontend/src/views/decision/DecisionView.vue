<template>
  <div class="decision-view">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>Decision Analysis</span>
          </template>

          <el-form :model="form" label-width="120px">
            <el-form-item label="Decision Type">
              <el-select v-model="form.decision_type" placeholder="Select type">
                <el-option label="Investment" value="investment" />
                <el-option label="Hiring" value="hiring" />
                <el-option label="Project" value="project" />
                <el-option label="Budget" value="budget" />
                <el-option label="Strategy" value="strategy" />
              </el-select>
            </el-form-item>

            <el-form-item label="Title">
              <el-input v-model="form.title" placeholder="Decision title" />
            </el-form-item>

            <el-form-item label="Description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="Describe the decision"
              />
            </el-form-item>

            <el-form-item label="Options">
              <div v-for="(option, index) in form.options" :key="index" class="option-item">
                <el-input v-model="option.name" placeholder="Option name" style="width: 200px" />
                <el-input v-model="option.description" placeholder="Description" style="flex: 1" />
                <el-button type="danger" @click="removeOption(index)">Remove</el-button>
              </div>
              <el-button @click="addOption">Add Option</el-button>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="analyzing" @click="analyzeDecision">
                Analyze
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="result" style="margin-top: 20px">
            <el-divider />
            <h3>Analysis Result</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Recommended">
                {{ result.recommended_option }}
              </el-descriptions-item>
              <el-descriptions-item label="Confidence">
                <el-progress :percentage="Math.round(result.confidence * 100)" />
              </el-descriptions-item>
              <el-descriptions-item label="Analysis">
                {{ result.analysis }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>Knowledge Base Query</span>
          </template>
          <el-input
            v-model="kbQuery"
            placeholder="Ask a question..."
            clearable
            @keyup.enter="queryKnowledge"
          >
            <template #append>
              <el-button :loading="queryingKb" @click="queryKnowledge">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>

          <div v-if="kbResult" style="margin-top: 16px">
            <p><strong>Answer:</strong></p>
            <p>{{ kbResult.answer }}</p>
            <p style="margin-top: 8px; color: #909399">
              Confidence: {{ Math.round(kbResult.confidence * 100) }}%
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { decisionApi } from '@/api'

const analyzing = ref(false)
const result = ref(null)
const kbQuery = ref('')
const queryingKb = ref(false)
const kbResult = ref(null)

const form = reactive({
  decision_type: 'project',
  title: '',
  description: '',
  options: [
    { name: '', description: '' },
  ],
})

function addOption() {
  form.options.push({ name: '', description: '' })
}

function removeOption(index: number) {
  form.options.splice(index, 1)
}

async function analyzeDecision() {
  if (!form.title) {
    ElMessage.warning('Please enter a title')
    return
  }
  analyzing.value = true
  try {
    result.value = await decisionApi.analyze(form) as never
  } catch {
    ElMessage.error('Analysis failed')
  } finally {
    analyzing.value = false
  }
}

async function queryKnowledge() {
  if (!kbQuery.value.trim()) return
  queryingKb.value = true
  try {
    kbResult.value = await decisionApi.queryKnowledge(kbQuery.value) as never
  } catch {
    ElMessage.error('Query failed')
  } finally {
    queryingKb.value = false
  }
}
</script>

<style scoped>
.option-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
