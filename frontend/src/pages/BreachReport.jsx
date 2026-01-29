import { useState, useEffect } from 'react'
import apiClient from '../api/axios'

const BreachReport = () => {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    fetchBreachReports()
  }, [])

  const fetchBreachReports = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await apiClient.get('/api/get_breach_reports', {
        headers: { Authorization: `Bearer ${token}` },
        params: { resolved: false }
      })
      setReports(response.data.reports || [])
    } catch (error) {
      console.error('Error fetching breach reports:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCheckBreach = async () => {
    setChecking(true)
    try {
      const token = localStorage.getItem('token')
      await apiClient.get('/api/detect_breach', {
        headers: { Authorization: `Bearer ${token}` }
      })
      alert('Breach check completed!')
      fetchBreachReports()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to check for breaches')
    } finally {
      setChecking(false)
    }
  }

  const handleMarkResolved = async (reportId) => {
    try {
      const token = localStorage.getItem('token')
      await apiClient.post(
        '/api/mark_breach_resolved',
        { report_id: reportId }
      )
      fetchBreachReports()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to mark as resolved')
    }
  }

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'bg-blue-500/20 text-blue-400',
      medium: 'bg-amber-500/20 text-amber-400',
      high: 'bg-orange-500/20 text-orange-400',
      critical: 'bg-red-500/20 text-red-400',
    }
    return colors[severity] || colors.medium
  }

  if (loading) {
    return <div className="text-center py-8 text-slate-400">Loading breach reports...</div>
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
        <h2 className="text-2xl sm:text-3xl font-bold text-white">Breach Report</h2>
        <button
          onClick={handleCheckBreach}
          disabled={checking}
          className="w-full sm:w-auto bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white px-4 py-2.5 rounded-lg transition-all duration-200 shadow-lg shadow-purple-500/25 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 touch-manipulation text-sm sm:text-base"
        >
          {checking ? 'Checking...' : '🔍 Check for Breaches'}
        </button>
      </div>

      {reports.length === 0 ? (
        <div className="bg-slate-800/80 border border-slate-700/50 rounded-xl shadow-lg p-8 text-center backdrop-blur">
          <p className="text-slate-300 text-lg">✅ No breaches detected!</p>
          <p className="text-slate-500 text-sm mt-2">Your credentials appear to be safe.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.id} className="bg-slate-800/80 border border-slate-700/50 rounded-xl shadow-lg p-4 sm:p-6 backdrop-blur">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 mb-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg sm:text-xl font-semibold text-white mb-2 break-words">
                    {report.breach_name}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-400 mb-2 break-words">{report.description || 'No description available'}</p>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-1 sm:space-y-0 text-xs sm:text-sm text-slate-500">
                    <span className="truncate">📧 {report.email}</span>
                    <span>📅 {new Date(report.date_detected).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-start space-x-2 sm:space-x-0 sm:space-y-2">
                  <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getSeverityColor(report.severity)}`}>
                    {report.severity}
                  </span>
                  <button
                    onClick={() => handleMarkResolved(report.id)}
                    className="text-xs text-indigo-400 hover:text-indigo-300 touch-manipulation px-2 py-1 transition-colors"
                  >
                    Mark Resolved
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
        <p className="text-sm text-amber-200">
          <strong>Note:</strong> This system uses the HaveIBeenPwned API to check for compromised credentials.
          If breaches are detected, change your passwords immediately and enable two-factor authentication.
        </p>
      </div>
    </div>
  )
}

export default BreachReport

