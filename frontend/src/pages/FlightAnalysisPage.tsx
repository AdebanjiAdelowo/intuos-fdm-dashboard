import { useEffect, useState } from 'react'
import { ChevronLeft, Navigation2, Clock, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getFlights, getFlightAlarms, getFlightTimeDuration, getFlightTelemetry } from '../api'
import AlarmDonut from '../components/AlarmDonut'
import FlightMap, { TelemetryPoint } from '../components/FlightMap'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { alarmColor, alarmLabel } from '../constants/alarmColors'
import { flightDuration, formatDate, formatTime } from '../utils/format'

type Row = Record<string, unknown>

const ALARM_KEYS = [
  'g_tot','ground_speed','vertical_speed','pitch','roll','altitude',
  'hard_landing','high_roll_at_low_height','low_ground_speed_at_low_height_with_low_acceleration',
  'high_pitch_at_low_height_with_low_acceleration',
]

function AlarmBreakdown({ entries, total }: { entries: { name: string; value: number }[]; total: number }) {
  return (
    <div className="space-y-2.5">
      {entries.map(({ name, value }) => {
        const pct = total > 0 ? (value / total) * 100 : 0
        return (
          <div key={name} className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: alarmColor(name) }} />
            <span className="text-sm text-gray-700 w-44 truncate">{alarmLabel(name)}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-1.5">
              <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, background: alarmColor(name) }} />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-14 text-right tabular-nums">{value.toLocaleString()}</span>
            <span className="text-xs text-gray-400 w-10 text-right tabular-nums">{pct.toFixed(1)}%</span>
          </div>
        )
      })}
    </div>
  )
}

export default function FlightAnalysisPage() {
  const [flights, setFlights] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Row | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [alarms, setAlarms] = useState<Row[]>([])
  const [duration, setDuration] = useState<Row[]>([])
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    getFlights()
      .then((r) => setFlights(Array.isArray(r.data) ? r.data as Row[] : []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    const id = Number(selected.id_volo ?? selected.id ?? 0)
    if (!id) return
    setDetailLoading(true)
    setTelemetry([])
    Promise.all([getFlightAlarms(id), getFlightTimeDuration(id), getFlightTelemetry(id)])
      .then(([al, dur, tel]) => {
        setAlarms(Array.isArray(al.data) ? al.data as Row[] : [])
        setDuration(Array.isArray(dur.data) ? dur.data as Row[] : [])
        const telData = tel.data?.telemetry_alarms
        setTelemetry(Array.isArray(telData) ? telData as TelemetryPoint[] : [])
      })
      .catch(() => {})
      .finally(() => setDetailLoading(false))
  }, [selected])

  const alarmRow = alarms[0] ?? {}
  const alarmEntries = ALARM_KEYS
    .map((k) => ({ name: k, value: Number(alarmRow[k] ?? 0) }))
    .filter((e) => e.value > 0)
    .sort((a, b) => b.value - a.value)
  const totalAlerts = alarmEntries.reduce((s, e) => s + e.value, 0)

  const barData = alarmEntries.slice(0, 10).map((e) => ({
    name: alarmLabel(e.name), count: e.value, key: e.name,
  }))

  const durRow = duration[0] ?? {}
  const durH = Number(durRow.hours ?? 0)
  const durM = Number(durRow.minutes ?? 0)
  const durS = Number(durRow.seconds ?? 0)
  const durDisplay = durH > 0 ? `${durH}h ${durM}m` : durM > 0 ? `${durM}m ${durS}s` : durS > 0 ? `${durS}s` : '—'

  if (selected) {
    const flightId = String(selected.id_volo ?? selected.id ?? '?')
    const stickOn = String(selected.stick_on ?? '')
    const stickOff = String(selected.stick_off ?? '')
    const reg = String(selected.registration_id ?? selected.marche ?? '').trim()
    const aptFrom = String(selected.airport_takeoff ?? '').trim()
    const aptTo = String(selected.airport_landing ?? '').trim()

    return (
      <div className="p-6 max-w-7xl mx-auto">
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-1.5 text-sm font-medium mb-5 hover:opacity-70 transition-opacity"
          style={{ color: '#0d1f14' }}
        >
          <ChevronLeft className="w-4 h-4" /> Back to all flights
        </button>

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: '#0d1f14' }}>
              <Navigation2 className="w-6 h-6" style={{ color: '#b8f04a' }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">Flight #{flightId}</h1>
                {reg && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{reg}</span>
                )}
                {totalAlerts > 0 && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full text-white" style={{ background: '#ef4444' }}>
                    {totalAlerts} alerts
                  </span>
                )}
                {totalAlerts === 0 && alarms.length > 0 && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-700">No alerts</span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                {aptFrom && aptTo && (
                  <span className="text-sm font-mono text-gray-700 font-semibold">{aptFrom} → {aptTo}</span>
                )}
                {aptFrom && <span className="text-gray-300">·</span>}
                <span className="text-sm text-gray-500">{formatDate(stickOn)}</span>
                <span className="text-gray-300">·</span>
                <span className="text-sm text-gray-500">{formatTime(stickOn)} – {formatTime(stickOff)}</span>
              </div>
            </div>
          </div>
        </div>

        {detailLoading ? <LoadingSpinner /> : (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <StatCard
                label="Total Alerts"
                value={totalAlerts}
                icon={<AlertTriangle className="w-5 h-5" />}
                accent={totalAlerts > 0}
              />
              <StatCard label="Flight Duration" value={durDisplay} icon={<Clock className="w-5 h-5" />} />
              <StatCard label="Alert Types Triggered" value={alarmEntries.length} icon={<Navigation2 className="w-5 h-5" />} />
            </div>

            {alarmEntries.length > 0 ? (
              <>
                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                    <p className="text-sm font-semibold text-gray-900">Alert Distribution</p>
                    <p className="text-xs text-gray-400 mb-3">{totalAlerts.toLocaleString()} alerts this flight</p>
                    <AlarmDonut data={alarmEntries} height={260} />
                  </div>
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                    <p className="text-sm font-semibold text-gray-900 mb-4">Alert Breakdown</p>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={barData} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 116 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 11 }} />
                        <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={116} />
                        <Tooltip formatter={(v: number) => [v.toLocaleString(), 'Alerts']} />
                        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                          {barData.map((e) => <Cell key={e.key} fill={alarmColor(e.key)} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Breakdown detail */}
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
                  <p className="text-sm font-semibold text-gray-900 mb-4">Alert Type Detail</p>
                  <AlarmBreakdown entries={alarmEntries} total={totalAlerts} />
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-10 mb-6 text-center">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                  <Navigation2 className="w-6 h-6 text-green-600" />
                </div>
                <p className="font-semibold text-gray-900">No alerts on this flight</p>
                <p className="text-sm text-gray-500 mt-1">This flight completed without triggering any alert conditions.</p>
              </div>
            )}

            {/* Map */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <p className="text-sm font-semibold text-gray-900 mb-1">Flight Path</p>
              <p className="text-xs text-gray-400 mb-3">
                Coloured by ML-predicted flight phase · {telemetry.length} telemetry points
              </p>
              <FlightMap telemetry={telemetry} height={400} />
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Flight Analysis</h1>
        <p className="text-sm text-gray-500 mt-0.5">All recorded flights — click any row to inspect alerts</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">{flights.length} flights</span>
          <span className="text-xs text-gray-400">Click a row to inspect</span>
        </div>
        {loading ? <LoadingSpinner /> : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {['Flight #', 'Registration', 'Date', 'Route', 'Duration'].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {flights.slice(0, 200).map((f, i) => {
                  const stickOn = String(f.stick_on ?? '')
                  const stickOff = String(f.stick_off ?? '')
                  const aptFrom = String(f.airport_takeoff ?? f.apt_takeoff ?? '').trim()
                  const aptTo = String(f.airport_landing ?? f.apt_landing ?? '').trim()
                  return (
                    <tr
                      key={i}
                      onClick={() => setSelected(f)}
                      className="cursor-pointer hover:bg-green-50 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono font-semibold text-gray-900">
                        #{String(f.id_volo ?? f.id ?? '—')}
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                          {String(f.registration_id ?? f.marche ?? '—').trim()}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{formatDate(stickOn)}</p>
                        <p className="text-xs text-gray-400">{formatTime(stickOn)}</p>
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-gray-700">
                        {aptFrom && aptTo ? `${aptFrom} → ${aptTo}` : '—'}
                      </td>
                      <td className="px-4 py-3 tabular-nums text-gray-700">
                        {flightDuration(stickOn, stickOff)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
