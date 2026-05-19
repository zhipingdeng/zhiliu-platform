import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  department?: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refreshToken') || '')
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const data = await authApi.login({ username, password }) as {
      access_token: string
      refresh_token: string
    }
    token.value = data.access_token
    refreshToken.value = data.refresh_token
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('refreshToken', data.refresh_token)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register({ username, email, password })
  }

  async function fetchUser() {
    try {
      const data = await authApi.getMe() as User
      user.value = data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    login,
    register,
    fetchUser,
    logout,
  }
})
