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
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    }
    return colors[severity] || colors.medium
  }

  if (loading) {
    return <div className="text-center py-8">Loading breach reports...</div>
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-800">Breach Report</h2>
        <button
          onClick={handleCheckBreach}
          disabled={checking}
          className="w-full sm:w-auto bg-blue-500 hover:bg-blue-600 text-white px-4 py-2.5 rounded-lg transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 touch-manipulation text-sm sm:text-base"
        >
          {checking ? 'Checking...' : '🔍 Check for Breaches'}
        </button>
      </div>

      {reports.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <p className="text-gray-600 text-lg">✅ No breaches detected!</p>
          <p className="text-gray-500 text-sm mt-2">Your credentials appear to be safe.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.id} className="bg-white rounded-lg shadow-md p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4 mb-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg sm:text-xl font-semibold text-gray-800 mb-2 break-words">
                    {report.breach_name}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600 mb-2 break-words">{report.description || 'No description available'}</p>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-1 sm:space-y-0 text-xs sm:text-sm text-gray-500">
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
                    className="text-xs text-blue-600 hover:text-blue-800 touch-manipulation px-2 py-1"
                  >
                    Mark Resolved
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> This system uses the HaveIBeenPwned API to check for compromised credentials.
          If breaches are detected, change your passwords immediately and enable two-factor authentication.
        </p>
      </div>
    </div>
  )
}

export default BreachReport

