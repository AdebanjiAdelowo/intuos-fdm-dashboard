import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Home, Activity, Plane, Navigation2, Users, GraduationCap, LogOut } from 'lucide-react'

const nav = [
  { to: '/',            label: 'Home',                icon: Home,          end: true  },
  { to: '/fleet',       label: 'Fleet Overview',      icon: Activity,      end: false },
  { to: '/aircraft',    label: 'Aircraft Analysis',   icon: Plane,         end: false },
  { to: '/flights',     label: 'Flight Analysis',     icon: Navigation2,   end: false },
  { to: '/pilots',      label: 'Pilot Analysis',      icon: Users,         end: false },
  { to: '/instructors', label: 'Instructor Analysis', icon: GraduationCap, end: false },
]

export default function Layout() {
  const navigate = useNavigate()

  function logout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col" style={{ background: '#0d1f14' }}>
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: '#b8f04a' }}
            >
              <Plane className="w-4 h-4 text-black" />
            </div>
            <div>
              <p className="text-white font-bold text-sm leading-tight">INTUOS FDM</p>
              <p className="text-white/40 text-xs leading-tight">Flight Data Monitoring</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-black'
                    : 'text-white/60 hover:text-white hover:bg-white/8'
                }`
              }
              style={({ isActive }) => isActive ? { background: '#b8f04a' } : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-white/10">
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-white/50 hover:text-white hover:bg-white/8 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <Outlet />
      </main>
    </div>
  )
}
