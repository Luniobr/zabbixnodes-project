import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'useAuth'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    console.error('Failed to load auth state from storage:', e)
    return null
  }
}

function saveToStorage(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {
    console.error('Failed to save auth state to storage:', e)
  }
}

export const useAuthStore = defineStore('auth', () => {
  const stored = loadFromStorage()

  const token = ref(stored?.token || null)
  const user = ref(stored?.username || null)
  const role = ref(stored?.role || null)

  function setAuth(data) {
    token.value = data.token
    user.value = data.username
    role.value = data.role
    saveToStorage({ token: data.token, username: data.username, role: data.role })
  }

  function logout() {
    token.value = null
    user.value = null
    role.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    token,
    user,
    role,
    setAuth,
    logout,
  }
})
