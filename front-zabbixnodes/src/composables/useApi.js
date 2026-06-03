import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://142.93.116.237:8001/api/v1/',
  headers: {
    'Content-Type': 'application/json',
  },
})

export function useApi() {
  return { client }
}
