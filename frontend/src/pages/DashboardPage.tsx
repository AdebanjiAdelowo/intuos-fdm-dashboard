import { useEffect, useState } from 'react'
import { Plane, Users, Activity, AlertTriangle } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import {
  getRegistrationsWithFlightsCount,
  getPilotsWithFlightsCount,
  getTopRegistrationsByAlarms,
  AlarmSummary,
} from '../api'
import StatCard from '../components/StatCard'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import { useDateRange } from '../hooks/useDateRange'

const COLORS = ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe']

export default function DashboardPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [regCount, setRegCount] = useState<number | null>(null)
  const [pilotCount, setPilotCount] = useState<number | null>(null)
  const [topAlarms, setTopAlarms] = useState<AlarmSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    Promise.all([
      getRegistrationsWithFlightsCount(),
      getPilotsWithFlightsCount(),
      getTopRegistrationsByAlarms(10, startDate, endDate),
    ])
      .then(([rc, pc, alarms]) => {
        setRegCount(rc.data)
        setPilotCount(pc.data)
        setTopAlarms(Array.isArray(alarms.data) ? alarms.data : [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [startDate, endDate])

  const chartData = topAlarms
    .slice(0, 10)
    .map((a) => ({ name: String(a.registration ?? a['marche'] ?? '?'), total: Number(a.total ?? 0) }))

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
          <p className="text-sm text-gray-500 mt-0.5">Fleet performance summary</p>
        </div>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
        />
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Aircraft with Flights"
          value={regCount ?? '—'}
          icon={<Plane className="w-5 h-5" />}
        />
        <StatCard
          label="Pilots with Flights"
          value={pilotCount ?? '—'}
          icon={<Users className="w-5 h-5" />}
        />
        <StatCard
          label="Date Range"
          value={`${startDate} → ${endDate}`}
          icon={<Activity className="w-5 h-5" />}
        />
        <StatCard
          label="Top Alarm Registrations"
          value={chartData.length}
          icon={<AlertTriangle className="w-5 h-5" />}
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <h2 className="text-base font-semibold text-gray-900 mb-4">
          Top Registrations by Total Alarms
        </h2>
        {loading ? (
          <LoadingSpinner />
        ) : chartData.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-10">No alarm data for the selected range.</p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 4, right: 16, bottom: 40, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
