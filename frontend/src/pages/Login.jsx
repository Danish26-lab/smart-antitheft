import { useState } from 'react'
import apiClient from '../api/axios'
import { useNavigate, Link } from 'react-router-dom'
import { discoverLocalDevice } from '../utils/deviceDiscovery'

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Prey Project-style: Discover running agent device on localhost
      const deviceDiscovery = await discoverLocalDevice()
      
      // Build login payload
      const loginData = {
        email,
        password
      }
      
      // Link existing agent device if discovered
      if (deviceDiscovery.success && deviceDiscovery.device_id) {
        loginData.device_id = deviceDiscovery.device_id
        if (deviceDiscovery.fingerprint_hash) {
          loginData.fingerprint_hash = deviceDiscovery.fingerprint_hash
        }
        console.log(`[DEVICE-LINK] Linking discovered device: ${deviceDiscovery.device_id}`)
      }

      const response = await apiClient.post('/api/login', loginData)

      if (response.data.access_token) {
        onLogin(response.data.access_token, response.data.user)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4 sm:p-6">
      <div className="bg-white rounded-lg shadow-2xl p-4 sm:p-6 md:p-8 w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">🛡️ Anti-Theft System</h1>
          <p className="text-sm sm:text-base text-gray-600">Sign in to your account</p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent touch-manipulation"
              placeholder="admin@antitheft.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent touch-manipulation"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 touch-manipulation text-base"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 space-y-3">
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="text-blue-500 hover:text-blue-600 font-medium">
                Sign up
              </Link>
            </p>
          </div>
          <div className="text-center text-sm text-gray-600">
            <p>Default credentials:</p>
            <p className="font-mono text-xs mt-1">admin@antitheft.com / admin123</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login

