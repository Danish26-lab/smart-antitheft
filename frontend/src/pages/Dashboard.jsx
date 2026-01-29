import { useState, useEffect } from 'react'
import apiClient from '../api/axios'
import MapView from '../components/MapView'
import { formatDateTime } from '../utils/dateFormatter'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalDevices: 0,
    missingDevices: 0,
    activeDevices: 0,
    breachAlerts: 0,
  })
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token')
      const headers = { Authorization: `Bearer ${token}` }

      const [devicesRes, breachRes] = await Promise.all([
        apiClient.get('/api/get_devices', { headers }),
        apiClient.get('/api/get_breach_reports', { headers }),
      ])

      const devicesData = devicesRes.data.devices || []
      const missingDevices = devicesData.filter(d => d.is_missing)
      const activeDevices = devicesData.filter(d => d.status === 'active')

      setStats({
        totalDevices: devicesData.length,
        missingDevices: missingDevices.length,
        activeDevices: activeDevices.length,
        breachAlerts: breachRes.data.reports?.length || 0,
      })

      setDevices(devicesData)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8 text-slate-400">Loading dashboard...</div>
  }

  const StatCard = ({ title, value, icon, color }) => (
    <div className={`bg-slate-800/80 border border-slate-700/50 rounded-xl shadow-lg p-4 sm:p-6 ${color} backdrop-blur`}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-slate-400 text-xs sm:text-sm font-medium truncate">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold text-white mt-1 sm:mt-2">{value}</p>
        </div>
        <div className="text-3xl sm:text-4xl ml-2 flex-shrink-0">{icon}</div>
      </div>
    </div>
  )

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
        <h2 className="text-2xl sm:text-3xl font-bold text-white">Dashboard</h2>
        <button
          onClick={fetchDashboardData}
          className="w-full sm:w-auto bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white px-4 py-2.5 rounded-lg transition-all duration-200 shadow-lg shadow-purple-500/25 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 touch-manipulation"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard
          title="Total Devices"
          value={stats.totalDevices}
          icon="💻"
          color="border-l-4 border-indigo-500"
        />
        <StatCard
          title="Missing Devices"
          value={stats.missingDevices}
          icon="🚨"
          color="border-l-4 border-red-500"
        />
        <StatCard
          title="Active Devices"
          value={stats.activeDevices}
          icon="✅"
          color="border-l-4 border-emerald-500"
        />
        <StatCard
          title="Breach Alerts"
          value={stats.breachAlerts}
          icon="🔒"
          color="border-l-4 border-amber-500"
        />
      </div>

      <div className="bg-slate-800/80 border border-slate-700/50 rounded-xl shadow-lg p-4 sm:p-6 backdrop-blur">
        <h3 className="text-lg sm:text-xl font-semibold text-white mb-3 sm:mb-4">Device Locations</h3>
        <div className="w-full rounded-lg overflow-hidden" style={{ minHeight: '300px' }}>
          <MapView devices={devices} />
        </div>
      </div>

      <div className="bg-slate-800/80 border border-slate-700/50 rounded-xl shadow-lg p-4 sm:p-6 backdrop-blur">
        <h3 className="text-lg sm:text-xl font-semibold text-white mb-3 sm:mb-4">Recent Activity</h3>
        <div className="space-y-2">
          {devices.slice(0, 5).map((device) => (
            <div key={device.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 bg-slate-700/30 rounded-lg gap-2 sm:gap-0 border border-slate-600/30">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-white truncate">{device.name}</p>
                <p className="text-xs sm:text-sm text-slate-400 truncate">
                  Status: {device.status} • Last seen: {formatDateTime(device.last_seen)}
                </p>
              </div>
              <span className={`px-2 sm:px-3 py-1 rounded-full text-xs whitespace-nowrap ${
                device.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                device.status === 'missing' ? 'bg-red-500/20 text-red-400' :
                'bg-slate-500/20 text-slate-400'
              }`}>
                {device.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

