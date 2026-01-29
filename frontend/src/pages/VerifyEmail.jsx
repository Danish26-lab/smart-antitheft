import { useState, useEffect } from 'react'
import apiClient from '../api/axios'
import { useNavigate, useLocation, Link } from 'react-router-dom'

const VerifyEmail = ({ onLogin }) => {
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [email, setEmail] = useState('')
  const [countdown, setCountdown] = useState(0)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    // Get email from location state or localStorage
    const emailFromState = location.state?.email
    const emailFromStorage = localStorage.getItem('pending_verification_email')
    
    if (emailFromState) {
      setEmail(emailFromState)
      localStorage.setItem('pending_verification_email', emailFromState)
    } else if (emailFromStorage) {
      setEmail(emailFromStorage)
    } else {
      // No email found, redirect to signup
      navigate('/signup')
    }
  }, [location, navigate])

  useEffect(() => {
    // Countdown timer for resend
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  const handleCodeChange = (index, value) => {
    if (value.length > 1) return // Only allow single digit
    
    const newCode = [...code]
    newCode[index] = value.replace(/\D/g, '') // Only numbers
    setCode(newCode)
    setError('')

    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`code-${index + 1}`)
      if (nextInput) nextInput.focus()
    }
  }

  const handleKeyDown = (index, e) => {
    // Handle backspace to go to previous input
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      const prevInput = document.getElementById(`code-${index - 1}`)
      if (prevInput) prevInput.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const newCode = [...code]
    
    for (let i = 0; i < 6; i++) {
      newCode[i] = pastedData[i] || ''
    }
    
    setCode(newCode)
    setError('')
    
    // Focus last filled input or first empty
    const lastFilledIndex = Math.min(pastedData.length - 1, 5)
    const nextInput = document.getElementById(`code-${lastFilledIndex}`)
    if (nextInput) nextInput.focus()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const verificationCode = code.join('')
    
    if (verificationCode.length !== 6) {
      setError('Please enter the complete 6-digit code')
      return
    }

    if (!email) {
      setError('Email not found. Please sign up again.')
      navigate('/signup')
      return
    }

    setLoading(true)

    try {
      const response = await apiClient.post('/api/verify_email', {
        email,
        code: verificationCode
      })

      if (response.data.user) {
        // Email verified successfully
        // Clear pending email
        localStorage.removeItem('pending_verification_email')
        
        // Try to auto-login if password is available
        const password = location.state?.password
        if (password) {
          try {
            const loginResponse = await apiClient.post('/api/login', {
              email,
              password
            })

            if (loginResponse.data.access_token) {
              onLogin(loginResponse.data.access_token, loginResponse.data.user)
              navigate('/dashboard')
              return
            }
          } catch (loginErr) {
            // Auto-login failed, redirect to login page
            setError('Email verified! Please login with your credentials.')
            setTimeout(() => {
              navigate('/login')
            }, 2000)
            return
          }
        } else {
          // No password available, redirect to login
          setError('Email verified! Please login with your credentials.')
          setTimeout(() => {
            navigate('/login')
          }, 2000)
          return
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid verification code. Please try again.')
      // Clear code on error
      setCode(['', '', '', '', '', ''])
      const firstInput = document.getElementById('code-0')
      if (firstInput) firstInput.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (countdown > 0 || !email) return

    setResending(true)
    setError('')

    try {
      await apiClient.post('/api/resend_verification', { email })
      setCountdown(60) // 60 second cooldown
      setError('')
      alert('Verification code resent! Please check your email.')
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to resend code. Please try again.')
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-4 sm:p-6">
      <div className="bg-slate-800/80 backdrop-blur-xl rounded-2xl shadow-2xl shadow-black/50 border border-slate-700/50 p-4 sm:p-6 md:p-8 w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">🛡️ Anti-Theft System</h1>
          <p className="text-sm sm:text-base text-slate-400">Verify your email address</p>
        </div>

        <div className="mb-6 text-center">
          <p className="text-sm text-slate-400 mb-2">
            We've sent a verification code to
          </p>
          <p className="text-base font-semibold text-white">{email}</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="code-0" className="block text-sm font-medium text-slate-300 mb-4 text-center">
              Enter the 6-digit code
            </label>
            <div className="flex justify-center gap-2 sm:gap-3">
              {code.map((digit, index) => (
                <input
                  key={index}
                  id={`code-${index}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleCodeChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  onPaste={index === 0 ? handlePaste : undefined}
                  className="w-12 h-14 sm:w-14 sm:h-16 text-center text-2xl sm:text-3xl font-bold bg-slate-900/50 border-2 border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 touch-manipulation"
                  autoFocus={index === 0}
                />
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-3 text-center">
              This code will expire in 15 minutes
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || code.join('').length !== 6}
            className="w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-purple-600 hover:from-indigo-400 hover:via-purple-400 hover:to-purple-500 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 shadow-lg shadow-purple-500/25 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-800 touch-manipulation text-base"
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </button>
        </form>

        <div className="mt-6 text-center space-y-3">
          <button
            type="button"
            onClick={handleResend}
            disabled={resending || countdown > 0}
            className="text-sm text-indigo-400 hover:text-indigo-300 font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {resending 
              ? 'Sending...' 
              : countdown > 0 
                ? `Resend code in ${countdown}s` 
                : "Didn't receive the code? Resend"}
          </button>
          
          <div className="pt-3 border-t border-slate-600">
            <p className="text-sm text-slate-400">
              Wrong email?{' '}
              <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
                Sign up again
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VerifyEmail
