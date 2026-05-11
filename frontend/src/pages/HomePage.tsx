import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plane, Users, Activity, Navigation2, GraduationCap, Clock } from 'lucide-react'
import { getRegistrationsWithFlightsCount, getPilotsWithFlightsCount, getTopRegistrationsByAlarms } from '../api'
import StatCard from '../components/StatCard'
import LoadingSpinner from '../components/LoadingSpinner'
import { useDateRange } from '../hooks/useDateRange'

const actions = [
  { to: '/fleet',       label: 'Fleet Overview',      desc: 'Alarm distribution across the fleet', icon: Activity      },
  { to: '/aircraft',    label: 'Aircraft Analysis',   desc: 'Per-aircraft flights and alerts',      icon: Plane         },
  { to: '/flights',     label: 'Flight Analysis',     desc: 'Inspect individual flight events',     icon: Navigation2   },
  { to: '/pilots',      label: 'Pilot Analysis',      desc: 'Pilot performance and alert trends',   icon: Users         },
  { to: '/instructors', label: 'Instructor Analysis', desc: 'Instructor-level flight review',       icon: GraduationCap },
]

export default function HomePage() {
  const navigate = useNavigate()
  const { startDate, endDate } = useDateRange()
  const [regCount, setRegCount] = useState<number | null>(null)
  const [pilotCount, setPilotCount] = useState<number | null>(null)
  const [totalAlarms, setTotalAlarms] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getRegistrationsWithFlightsCount(),
      getPilotsWithFlightsCount(),
      getTopRegistrationsByAlarms(50, startDate, endDate),
    ])
      .then(([rc, pc, alarms]) => {
        setRegCount(rc.data)
        setPilotCount(pc.data)
        const total = Array.isArray(alarms.data)
          ? alarms.data.reduce((sum, a) => sum + Number(a.total ?? 0), 0)
          : 0
        setTotalAlarms(total)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [startDate, endDate])

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: '#b8f04a' }}>
            <Plane className="w-5 h-5 text-black" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">INTUOS FDM</h1>
            <p className="text-sm text-gray-500">Flight Data Monitoring Platform</p>
          </div>
        </div>
        <p className="text-sm text-gray-400 mt-3">Last 30 days · {startDate} to {endDate}</p>
      </div>

      {/* KPIs */}
      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <StatCard
            label="Monitored Aircraft"
            value={regCount ?? '—'}
            icon={<Plane className="w-5 h-5" />}
            accent
          />
          <StatCard
            label="Active Pilots"
            value={pilotCount ?? '—'}
            icon={<Users className="w-5 h-5" />}
          />
          <StatCard
            label="Total Alerts"
            value={totalAlarms?.toLocaleString() ?? '—'}
            sub="across all aircraft"
            icon={<Clock className="w-5 h-5" />}
          />
        </div>
      )}

      {/* Quick actions */}
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">Quick Access</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {actions.map(({ to, label, desc, icon: Icon }) => (
          <button
            key={to}
            onClick={() => navigate(to)}
            className="text-left bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:border-green-300 hover:shadow-md transition-all group"
          >
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center mb-3 group-hover:scale-105 transition-transform"
              style={{ background: '#0d1f14' }}
            >
              <Icon className="w-4 h-4" style={{ color: '#b8f04a' }} />
            </div>
            <p className="font-semibold text-gray-900 text-sm">{label}</p>
            <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
          </button>
        ))}
      </div>
    </div>
  )
}
