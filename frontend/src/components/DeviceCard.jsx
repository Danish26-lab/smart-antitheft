import { formatDateTime } from '../utils/dateFormatter'

const DeviceCard = ({ device, onAction }) => {
  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-emerald-500/20 text-emerald-400',
      missing: 'bg-red-500/20 text-red-400',
      locked: 'bg-amber-500/20 text-amber-400',
      alarm: 'bg-orange-500/20 text-orange-400',
      wiped: 'bg-slate-500/20 text-white',
      inactive: 'bg-slate-500/20 text-white'
    }
    return colors[status] || colors.active
  }

  const isOSDevice = (device.device_type || '').toLowerCase() === 'os_device'

  return (
    <div className="bg-slate-800/80 border border-slate-700/50 rounded-xl shadow-lg p-6 hover:shadow-xl hover:border-slate-600/50 transition-all duration-200 backdrop-blur">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold text-white">{device.name}</h3>
          <p className="text-sm text-white">{device.device_type || 'Unknown Device'}</p>
          <p className="text-xs text-white mt-1">ID: {device.device_id}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(device.status)}`}>
          {device.status}
        </span>
      </div>

      {device.last_lat && device.last_lng && (
        <div className="mb-4">
          <p className="text-sm text-white">
            📍 Location: {device.last_lat.toFixed(4)}, {device.last_lng.toFixed(4)}
          </p>
          <p className="text-xs text-white mt-1">
            Last seen: {formatDateTime(device.last_seen)}
          </p>
        </div>
      )}

      {device.is_missing && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p className="text-sm text-red-400 font-medium">
            ⚠️ Device marked as missing
          </p>
          {device.missing_since && (
            <p className="text-xs text-red-500/80 mt-1">
              Since: {formatDateTime(device.missing_since)}
            </p>
          )}
        </div>
      )}

      {!isOSDevice ? (
        <div className="flex space-x-2">
          <button
            onClick={() => onAction(device.device_id, 'lock')}
            className="flex-1 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-400 hover:to-indigo-500 text-white py-2 px-4 rounded-lg transition-all duration-200 text-sm font-medium shadow-lg shadow-indigo-500/20"
          >
            🔒 Lock
          </button>
          <button
            onClick={() => onAction(device.device_id, 'alarm')}
            className="flex-1 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white py-2 px-4 rounded-lg transition-all duration-200 text-sm font-medium shadow-lg shadow-orange-500/20"
          >
            🚨 Alarm
          </button>
          <button
            onClick={() => onAction(device.device_id, 'wipe')}
            className="flex-1 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 text-white py-2 px-4 rounded-lg transition-all duration-200 text-sm font-medium shadow-lg shadow-red-500/20"
          >
            🗑️ Wipe
          </button>
        </div>
      ) : (
        <p className="text-xs text-white mt-2">
          OS devices are view-only. Install the device agent for full control (lock, alarm, wipe).
        </p>
      )}
    </div>
  )
}

export default DeviceCard

