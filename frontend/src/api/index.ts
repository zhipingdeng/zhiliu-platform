import axios from 'axios'
import { useUserStore } from '@/stores/user'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// 认证 API
export const authApi = {
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
}

// 工作流 API
export const workflowApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/workflows', { params }),
  get: (id: number) => api.get(`/workflows/${id}`),
  create: (data: { name: string; description?: string; dag_definition?: string }) =>
    api.post('/workflows', data),
  activate: (id: number) => api.put(`/workflows/${id}/activate`),
  execute: (id: number, input_data: Record<string, unknown>) =>
    api.post(`/workflows/${id}/execute`, input_data),
  getExecutions: (id: number) => api.get(`/workflows/${id}/executions`),
}

// 意图识别 API
export const intentApi = {
  classify: (text: string) =>
    api.post(`/intent/classify-sync?text=${encodeURIComponent(text)}`),
}

// 数据分析 API
export const analyticsApi = {
  query: (question: string) =>
    api.post('/analytics/query', { question }),
  report: (topic: string, data: unknown[]) =>
    api.post('/analytics/report', { topic, data }),
  trend: (params: { table: string; date_column: string; value_column: string; days?: number }) =>
    api.post('/analytics/trend', params),
  getSchema: () => api.get('/analytics/schema'),
}

// 决策支持 API
export const decisionApi = {
  analyze: (data: {
    decision_type: string
    title: string
    description: string
    options: unknown[]
  }) => api.post('/decision/analyze', data),
  riskAssessment: (data: { decision_type: string; context: Record<string, unknown> }) =>
    api.post('/decision/risk-assessment', data),
  addKnowledge: (documents: unknown[]) =>
    api.post('/decision/knowledge/add', { documents }),
  queryKnowledge: (question: string, top_k?: number) =>
    api.post('/decision/knowledge/query', { question, top_k }),
}
