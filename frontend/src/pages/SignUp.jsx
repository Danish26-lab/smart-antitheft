import { useState } from 'react'
import apiClient from '../api/axios'
import axios from 'axios' // Keep for full URL usage
import { useNavigate, Link } from 'react-router-dom'
import { detectOSDevice } from '../utils/deviceDetection'
import { discoverLocalDevice } from '../utils/deviceDiscovery'

// API URL helper
const getApiUrl = () => {
  return import.meta.env.PROD 
    ? (import.meta.env.VITE_API_URL || 'https://antitheft-backend.vercel.app')
    : (import.meta.env.VITE_API_URL || 'http://localhost:5000')
}

const SignUp = ({ onLogin }) => {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Validation
    if (password.length < 6) {
      setError('Password must be at least 6 characters long')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address')
      return
    }

    setLoading(true)

    try {
      // Prey Project-style: Discover running agent device on localhost
      const deviceDiscovery = await discoverLocalDevice()

      // Browser / OS-level device detection (for auto-registering a device row)
      let osDevice = null
      try {
        osDevice = await detectOSDevice()
        console.log('[DEVICE-DETECTION] Detected OS device:', osDevice)
      } catch (detectErr) {
        console.warn('[DEVICE-DETECTION] Failed to detect OS device:', detectErr)
      }
      
      // Build registration payload
      const registrationData = {
        email,
        password,
        name: name || email.split('@')[0]
      }
      
      // Attach OS/browser device metadata so backend can auto-create a device
      if (osDevice) {
        registrationData.os_device = osDevice
      }
      
      // Link existing agent device if discovered
      if (deviceDiscovery.success && deviceDiscovery.device_id) {
        registrationData.device_id = deviceDiscovery.device_id
        console.log(`[DEVICE-LINK] Linking discovered device: ${deviceDiscovery.device_id}`)
      }
      
      // Register user (will link device if device_id provided)
      const response = await apiClient.post('/api/register_user', registrationData)

      if (response.data.user) {
        // Check if email verification is required
        if (response.data.verification_required) {
          // Store email and password for verification flow
          localStorage.setItem('pending_verification_email', email)
          
          // Redirect to verification page
          navigate('/verify-email', {
            state: {
              email,
              password,
              device_id: deviceDiscovery.success ? deviceDiscovery.device_id : null
            }
          })
          return
        }
        
        // Check if device was linked
        if (response.data.device_linked && response.data.device) {
          console.log(`[DEVICE-LINK] Device linked: ${response.data.device.name}`)
        } else {
          console.log('[DEVICE-LINK] No device linked. Start the agent to link your device.')
        }
        
        // Auto-download agent installer ZIP after successful registration
        // Only download if device was NOT linked (user needs to install agent)
        if (!response.data.device_linked) {
          try {
            const apiUrl = getApiUrl()
            const downloadUrl = `${apiUrl}/api/download_agent`
            
            // Small delay to ensure registration completes
            setTimeout(() => {
              // Create a temporary link and trigger download
              const link = document.createElement('a')
              link.href = downloadUrl
              link.download = 'antitheft-agent-installer.zip'
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
              
              console.log('[DOWNLOAD] Agent installer download started')
            }, 500)
          } catch (downloadErr) {
            console.warn('[DOWNLOAD] Failed to auto-download agent installer:', downloadErr)
            // Don't block registration if download fails
          }
        }
        
        // If no verification required, log in immediately
        try {
          const loginData = {
            email,
            password
          }
          
          // Include device_id in login if available
          if (deviceDiscovery.success && deviceDiscovery.device_id) {
            loginData.device_id = deviceDiscovery.device_id
          }
          
          const loginResponse = await apiClient.post('/api/login', loginData)

          if (loginResponse.data.access_token) {
            onLogin(loginResponse.data.access_token, loginResponse.data.user)
            navigate('/dashboard')
            return
          }
        } catch (loginErr) {
          // Registration successful but auto-login failed
          setError('Account created successfully! Please login.')
          setTimeout(() => {
            navigate('/login')
          }, 2000)
          return
        }
      }
    } catch (err) {
      // Get error message from backend response
      const errorMessage = err.response?.data?.message || err.response?.data?.error || err.message || 'Registration failed. Please try again.'
      setError(errorMessage)
      console.error('Registration error:', err.response?.data || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-4 sm:p-6">
      <div className="bg-slate-800/80 backdrop-blur-xl rounded-2xl shadow-2xl shadow-black/50 border border-slate-700/50 p-4 sm:p-6 md:p-8 w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">🛡️ Anti-Theft System</h1>
          <p className="text-sm sm:text-base text-white">Create your account</p>
        </div>

        {error && (
          <div className={`${error.includes('successfully') ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' : 'bg-red-500/10 border-red-500/50 text-red-400'} border px-4 py-3 rounded-lg mb-4`}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-white mb-2">
              Full Name
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 text-base bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 touch-manipulation"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-white mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 text-base bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 touch-manipulation"
              placeholder="your.email@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-white mb-2">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full px-4 py-3 text-base bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 touch-manipulation"
              placeholder="At least 6 characters"
            />
            <p className="text-xs text-white mt-1">Must be at least 6 characters</p>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-white mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-4 py-3 text-base bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 touch-manipulation"
              placeholder="Re-enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-purple-600 hover:from-indigo-400 hover:via-purple-400 hover:to-purple-500 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 shadow-lg shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-800 touch-manipulation text-base"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-white">
            Already have an account?{' '}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default SignUp

