import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.detail || error.message
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

export const fetchWorkspaces = async () => {
  const response = await apiClient.get('/workspaces')
  return response.data
}

export const fetchApps = async (workspaceId) => {
  const params = workspaceId ? { workspace_id: workspaceId } : {}
  const response = await apiClient.get('/apps', { params })
  return response.data
}

export const approveApp = async (approvalData) => {
  const response = await apiClient.post('/apps/approve', approvalData)
  return response.data
}

export const revokeApproval = async (revokeData) => {
  const response = await apiClient.post('/apps/revoke', revokeData)
  return response.data
}

export const refreshApps = async (workspaceId) => {
  const params = workspaceId ? { workspace_id: workspaceId } : {}
  const response = await apiClient.post('/apps/refresh', null, { params })
  return response.data
}

export const checkHealth = async () => {
  const response = await apiClient.get('/health')
  return response.data
}

export default apiClient




