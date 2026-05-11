import { useEffect, useState } from 'react'
import { Activity, Plane, AlertTriangle, Users } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import {
  getRegistrationsWithFlightsCount,
  getPilotsWithFlightsCount,
  getTopRegistrationsByAlarms,
  getAllAlarms,
  AlarmSummary,
} from '../api'
import AlarmDonut from '../components/AlarmDonut'
import StatCard from '../components/StatCard'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import { useDateRange } from '../hooks/useDateRange'
import { alarmColor, alarmLabel } from '../constants/alarmColors'

export default function FleetOverviewPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [regCount, setRegCount] = useState<number | null>(null)
  const [pilotCount, setPilotCount] = useState<number | null>(null)
  const [allAlarms, setAllAlarms] = useState<AlarmSummary[]>([])
  const [topAlarms, setTopAlarms] = useState<AlarmSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getRegistrationsWithFlightsCount(),
      getPilotsWithFlightsCount(),
      getAllAlarms(startDate, endDate),
      getTopRegistrationsByAlarms(10, startDate, endDate),
    ])
      .then(([rc, pc, al, top]) => {
        setRegCount(rc.data)
        setPilotCount(pc.data)
        setAllAlarms(Array.isArray(al.data) ? al.data : [])
        setTopAlarms(Array.isArray(top.data) ? top.data : [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [startDate, endDate])

  // Sum all alarm types across all registrations for the donut
  const alarmTypeTotals: Record<string, number> = {}
  for (const row of allAlarms) {
    for (const [k, v] of Object.entries(row)) {
      if (k === 'registration' || k === 'total') continue
      if (Number(v) > 0) alarmTypeTotals[k] = (alarmTypeTotals[k] ?? 0) + Number(v)
    }
  }
  const donutData = Object.entries(alarmTypeTotals)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  const totalAlerts = donutData.reduce((s, d) => s + d.value, 0)
  const withAlerts = allAlarms.filter((a) => Number(a.total ?? 0) > 0).length

  const barData = topAlarms
    .slice(0, 10)
    .map((a) => ({ name: String(a.registration ?? '?').trim(), total: Number(a.total ?? 0) }))

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-6 h-6" style={{ color: '#0d1f14' }} />
            Fleet Overview
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Fleet-wide alert distribution</p>
        </div>
        <DateRangePicker
          startDate={startDate}
          endDate={endDate}
          onStartChange={setStartDate}
          onEndChange={setEndDate}
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* KPI row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <StatCard label="Aircraft Monitored" value={regCount ?? '—'} icon={<Plane className="w-5 h-5" />} accent />
            <StatCard label="With Flights" value={allAlarms.length} icon={<Plane className="w-5 h-5" />} />
            <StatCard label="With Alerts" value={withAlerts} icon={<AlertTriangle className="w-5 h-5" />} />
            <StatCard label="Total Alerts" value={totalAlerts.toLocaleString()} icon={<Users className="w-5 h-5" />} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Donut */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">Alert Type Distribution</h2>
              <p className="text-xs text-gray-400 mb-4">{totalAlerts.toLocaleString()} total alerts</p>
              <AlarmDonut data={donutData} height={280} />
            </div>

            {/* Bar */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">Top Aircraft by Alerts</h2>
              <p className="text-xs text-gray-400 mb-4">Top 10 registrations</p>
              {barData.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-10">No data for this range</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={barData} margin={{ top: 4, right: 16, bottom: 50, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                      {barData.map((_, i) => (
                        <Cell key={i} fill={i === 0 ? '#b8f04a' : '#0d1f14'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Alert breakdown table */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Alert Breakdown by Type</h2>
            <div className="space-y-2">
              {donutData.map(({ name, value }) => {
                const pct = totalAlerts > 0 ? (value / totalAlerts) * 100 : 0
                return (
                  <div key={name} className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: alarmColor(name) }} />
                    <span className="text-sm text-gray-700 w-48 truncate">{alarmLabel(name)}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-2">
                      <div
                        className="h-2 rounded-full"
                        style={{ width: `${pct}%`, background: alarmColor(name) }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 w-16 text-right">
                      {value.toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-400 w-12 text-right">{pct.toFixed(1)}%</span>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
