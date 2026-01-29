import { useState } from 'react'

const Navbar = ({ user, onLogout, onMenuClick }) => {
  const [showMenu, setShowMenu] = useState(false)

  return (
    <nav className="bg-slate-900/95 backdrop-blur border-b border-slate-700/50 px-3 sm:px-4 md:px-6 py-3 md:py-4 shadow-lg shadow-black/20">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg text-white hover:text-white hover:bg-slate-700/50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-white">🛡️ Anti-Theft System</h1>
        </div>
        
        <div className="flex items-center space-x-2 sm:space-x-4">
          <div className="relative hidden sm:block">
            <button className="text-white hover:text-white p-2 rounded-lg hover:bg-slate-700/50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors">
              <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center space-x-2 text-white hover:text-white p-1 sm:p-2 rounded-lg hover:bg-slate-700/50 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
              aria-label="User menu"
            >
              <div className="w-8 h-8 sm:w-9 sm:h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm sm:text-base shadow-lg shadow-purple-500/30">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="hidden sm:block text-sm md:text-base text-white">{user?.name || 'User'}</span>
            </button>

            {showMenu && (
              <>
                <div 
                  className="fixed inset-0 z-[9998]"
                  onClick={() => setShowMenu(false)}
                  aria-hidden="true"
                />
                <div className="absolute right-0 mt-2 w-48 sm:w-56 bg-slate-800 rounded-xl shadow-xl py-1 z-[9999] border border-slate-600/50 backdrop-blur">
                  <div className="px-4 py-3 border-b border-slate-600/50">
                    <p className="text-sm font-medium text-white truncate">{user?.name || 'User'}</p>
                    <p className="text-xs text-white truncate">{user?.email || ''}</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowMenu(false)
                      onLogout()
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar

