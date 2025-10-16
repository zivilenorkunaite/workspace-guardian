import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

console.log('🔧 [API] Initializing API client')
console.log('🔧 [API] Base URL:', API_BASE_URL)
console.log('🔧 [API] Environment:', {
  VITE_API_URL: import.meta.env.VITE_API_URL,
  MODE: import.meta.env.MODE,
  DEV: import.meta.env.DEV,
  PROD: import.meta.env.PROD
})

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  config => {
    console.log(`📤 [API] ${config.method.toUpperCase()} ${config.url}`, {
      baseURL: config.baseURL,
      params: config.params,
      data: config.data
    })
    return config
  },
  error => {
    console.error('❌ [API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and logging
apiClient.interceptors.response.use(
  response => {
    console.log(`📥 [API] ${response.config.method.toUpperCase()} ${response.config.url} - ${response.status}`, {
      status: response.status,
      statusText: response.statusText,
      data: response.data
    })
    return response
  },
  error => {
    const message = error.response?.data?.detail || error.message
    console.error('❌ [API] Response error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      message: message,
      data: error.response?.data,
      error: error
    })
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




