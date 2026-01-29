import { NavLink } from 'react-router-dom'

const Sidebar = ({ onClose }) => {
  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/devices', label: 'Devices', icon: '💻' },
    { path: '/breach-report', label: 'Breach Report', icon: '🔒' },
    { path: '/missing-mode', label: 'Missing Mode', icon: '🚨' },
  ]

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-700/50 text-white h-full overflow-y-auto">
      <div className="p-4 sm:p-6 flex items-center justify-between lg:justify-start">
        <h2 className="text-lg sm:text-xl font-bold text-white">Navigation</h2>
        <button
          onClick={onClose}
          className="lg:hidden p-2 rounded-lg text-white hover:text-white hover:bg-slate-700/50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
          aria-label="Close menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <nav className="mt-2 sm:mt-6">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={() => {
              if (window.innerWidth < 1024 && onClose) {
                onClose()
              }
            }}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 sm:px-6 py-3 sm:py-3 hover:bg-slate-700/50 transition-colors touch-manipulation ${
                isActive ? 'bg-slate-700/50 border-r-4 border-indigo-500 text-white' : 'text-white'
              }`
            }
          >
            <span className="text-xl sm:text-2xl">{item.icon}</span>
            <span className="text-sm sm:text-base">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar

