// API Configuration
// Uses environment variable in production, falls back to localhost in development
const API_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.DEV ? 'http://localhost:5000' : 'https://antitheft-backend.vercel.app')

export default {
  API_URL,
  API_BASE: `${API_URL}/api`
}
