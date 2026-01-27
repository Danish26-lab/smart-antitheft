// Centralized Axios configuration
import axios from 'axios'

// Determine API URL based on environment
const getApiUrl = () => {
  // In production (Vercel), use the deployed backend URL
  if (import.meta.env.PROD) {
    const url = import.meta.env.VITE_API_URL || 'https://antitheft-backend-2.vercel.app'
    // Remove trailing slash to prevent double slashes
    return url.replace(/\/+$/, '')
  }
  // In development, use localhost
  const url = import.meta.env.VITE_API_URL || 'http://localhost:5000'
  return url.replace(/\/+$/, '')
}

// Create axios instance with base URL
const apiClient = axios.create({
  baseURL: getApiUrl(),
  timeout: 10000,  // Reduced timeout for faster response (10s instead of 30s)
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default apiClient
