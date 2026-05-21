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

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 flex flex-col" style={{ background: '#0d1f14' }}>
        {/* Logo */}
        <div className="px-5 pt-6 pb-5" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: '#b8f04a' }}>
              <Plane className="w-4 h-4 text-black" />
            </div>
            <div>
              <p className="text-white font-bold text-sm leading-tight tracking-wide">INTUOS FDM</p>
              <p className="text-xs leading-tight" style={{ color: 'rgba(255,255,255,0.38)' }}>Flight Data Monitoring</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-5 space-y-0.5 overflow-y-auto">
          <p className="px-3 mb-3 text-xs font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.22)' }}>
            Menu
          </p>
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive ? 'shadow-md' : ''
                }`
              }
              style={({ isActive }) =>
                isActive
                  ? { background: '#b8f04a', color: '#0d1f14' }
                  : { color: 'rgba(255,255,255,0.58)' }
              }
              onMouseEnter={(e) => {
                if (!(e.currentTarget as HTMLElement).style.background.includes('b8f04a')) {
                  ;(e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.07)'
                  ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.9)'
                }
              }}
              onMouseLeave={(e) => {
                if (!(e.currentTarget as HTMLElement).style.background.includes('b8f04a')) {
                  ;(e.currentTarget as HTMLElement).style.background = ''
                  ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.58)'
                }
              }}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-4" style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <button
            onClick={() => { localStorage.removeItem('token'); navigate('/login') }}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm transition-colors"
            style={{ color: 'rgba(255,255,255,0.45)' }}
            onMouseEnter={(e) => {
              ;(e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.07)'
              ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.8)'
            }}
            onMouseLeave={(e) => {
              ;(e.currentTarget as HTMLElement).style.background = ''
              ;(e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.45)'
            }}
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto" style={{ background: '#f8fafc' }}>
        <Outlet />
      </main>
    </div>
  )
}
