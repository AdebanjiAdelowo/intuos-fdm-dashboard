import { useEffect, useState, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Search, Users, AlertTriangle, Clock, GraduationCap } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
  searchPilots,
  getPilotAlarmsByDate,
  getPilotFlightsWithAlarms,
  getPilotTopFlightsWithAlarms,
  getFlewHoursByPilot,
  Pilot,
} from '../api'
import AlarmDonut from '../components/AlarmDonut'
import FlightMap from '../components/FlightMap'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { useDateRange } from '../hooks/useDateRange'
import { alarmColor, alarmLabel } from '../constants/alarmColors'

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

interface Props {
  title?: string
  subtitle?: string
}

export default function PilotAnalysisPage({ title = 'Pilot Analysis', subtitle = 'Pilot performance and alert trends' }: Props) {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [pilots, setPilots] = useState<Pilot[]>([])
  const [totalItems, setTotalItems] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [inputVal, setInputVal] = useState('')
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Pilot | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const [alarms, setAlarms] = useState<Row[]>([])
  const [flightsWithAlarms, setFlightsWithAlarms] = useState<number | null>(null)
  const [topFlights, setTopFlights] = useState<Row[]>([])
  const [flewHours, setFlewHours] = useState<Row[]>([])

  const fetchPilots = useCallback(() => {
    setLoading(true)
    searchPilots(startDate, endDate, search, page, 20)
      .then((r) => {
        setPilots(Array.isArray(r.data) ? r.data : [])
        setTotalItems(r.pagination?.total_items ?? 0)
        setTotalPages(r.pagination?.total_pages ?? 1)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [startDate, endDate, search, page])

  useEffect(() => { fetchPilots() }, [fetchPilots])
  useEffect(() => { setPage(1) }, [startDate, endDate, search])

  useEffect(() => {
    if (!selected) return
    // pilot id is in the 'id' field
    const id = String((selected as any).id ?? (selected as any).codcf ?? (selected as any).pilot_id ?? '').trim()
    if (!id) return
    setDetailLoading(true)
    Promise.all([
      getPilotAlarmsByDate(id, startDate, endDate),
      getPilotFlightsWithAlarms(id, startDate, endDate),
      getPilotTopFlightsWithAlarms(id, 10, startDate, endDate),
      getFlewHoursByPilot(id, startDate, endDate),
    ])
      .then(([al, fwa, topFl, fh]) => {
        setAlarms(Array.isArray(al.data) ? al.data as Row[] : [])
        const fwaVal = Array.isArray(fwa.data) ? fwa.data[0] : null
        setFlightsWithAlarms(typeof fwaVal === 'number' ? fwaVal : null)
        setTopFlights(Array.isArray(topFl.data) ? topFl.data as Row[] : [])
        setFlewHours(Array.isArray(fh.data) ? fh.data as Row[] : [])
      })
      .catch(() => {})
      .finally(() => setDetailLoading(false))
  }, [selected, startDate, endDate])

  const alarmRow = alarms[0] ?? {}
  const alarmEntries = ALARM_KEYS
    .map((k) => ({ name: k, value: Number(alarmRow[k] ?? 0) }))
    .filter((e) => e.value > 0)
    .sort((a, b) => b.value - a.value)
  const totalAlerts = alarmEntries.reduce((s, e) => s + e.value, 0)

  const barData = alarmEntries.slice(0, 10).map((e) => ({
    name: alarmLabel(e.name), count: e.value, key: e.name,
  }))

  const flewVal = (() => {
    if (flewHours.length === 0) return '—'
    const row = flewHours[0]
    const h = Number(row.hours ?? 0)
    const m = Number(row.minutes ?? 0)
    if (h === 0 && m === 0) return String(Object.values(row)[0] ?? '—')
    return h > 0 ? `${h}h ${m}m` : `${m}m`
  })()

  if (selected) {
    const s = selected as any
    const pilotId = String(s.id ?? s.codcf ?? s.pilot_id ?? '?').trim()
    const pilotName = String(s.pilot_name ?? s.nome ?? pilotId)
    const nationality = String(s.nationality ?? '').trim()
    const isInstructor = String(s.instructor ?? '') === 'S'
    const isStudent = String(s.student ?? '') === 'S'

    return (
      <div className="p-6 max-w-7xl mx-auto">
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-1.5 text-sm font-medium mb-5 hover:opacity-70 transition-opacity"
          style={{ color: '#0d1f14' }}
        >
          <ChevronLeft className="w-4 h-4" /> Back to {title.toLowerCase()}
        </button>

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: '#0d1f14' }}>
              {isInstructor
                ? <GraduationCap className="w-6 h-6" style={{ color: '#b8f04a' }} />
                : <Users className="w-6 h-6" style={{ color: '#b8f04a' }} />}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold text-gray-900">{pilotName}</h1>
                {isInstructor && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full text-white" style={{ background: '#0d1f14' }}>Instructor</span>
                )}
                {isStudent && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Student</span>
                )}
                {nationality && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{nationality}</span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-0.5">{title} · ID {pilotId}</p>
            </div>
          </div>
          <DateRangePicker startDate={startDate} endDate={endDate} onStartChange={setStartDate} onEndChange={setEndDate} />
        </div>

        {detailLoading ? <LoadingSpinner /> : (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <StatCard label="Flights with Alerts" value={flightsWithAlarms ?? '—'} icon={<AlertTriangle className="w-5 h-5" />} accent />
              <StatCard label="Total Alerts" value={totalAlerts.toLocaleString()} icon={<AlertTriangle className="w-5 h-5" />} />
              <StatCard label="Alert Types" value={alarmEntries.length} icon={<Users className="w-5 h-5" />} />
              <StatCard label="Flew Hours" value={flewVal} icon={<Clock className="w-5 h-5" />} />
            </div>

            {alarmEntries.length > 0 ? (
              <>
                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                    <p className="text-sm font-semibold text-gray-900">Alert Distribution</p>
                    <p className="text-xs text-gray-400 mb-3">{totalAlerts.toLocaleString()} total alerts</p>
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
                  <Users className="w-6 h-6 text-green-600" />
                </div>
                <p className="font-semibold text-gray-900">No alerts in this range</p>
                <p className="text-sm text-gray-500 mt-1">Try expanding the date range to see alert history.</p>
              </div>
            )}

            {/* Top alerting flights */}
            {topFlights.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
                <p className="text-sm font-semibold text-gray-900 mb-1">Top Alerting Flights</p>
                <p className="text-xs text-gray-400 mb-4">Flights with the highest alert counts in this range</p>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Flight</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Aircraft</th>
                        {ALARM_KEYS.filter((k) => topFlights.some((f) => Number(f[k]) > 0)).map((k) => (
                          <th key={k} className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide whitespace-nowrap" style={{ color: alarmColor(k) }}>
                            {alarmLabel(k).split(' ')[0]}
                          </th>
                        ))}
                        <th className="px-3 py-2 text-right text-xs font-semibold text-gray-900 uppercase tracking-wide">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {topFlights.map((f, i) => {
                        const activeKeys = ALARM_KEYS.filter((k) => topFlights.some((tf) => Number(tf[k]) > 0))
                        return (
                          <tr key={i} className="hover:bg-gray-50 transition-colors">
                            <td className="px-3 py-2.5 font-mono font-medium text-gray-900">#{String(f.id_volo ?? '—')}</td>
                            <td className="px-3 py-2.5">
                              <span className="font-mono text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                                {String(f.marche ?? '—').trim()}
                              </span>
                            </td>
                            {activeKeys.map((k) => (
                              <td key={k} className="px-3 py-2.5 text-right tabular-nums">
                                {Number(f[k]) > 0
                                  ? <span className="font-semibold" style={{ color: alarmColor(k) }}>{Number(f[k]).toLocaleString()}</span>
                                  : <span className="text-gray-300">—</span>}
                              </td>
                            ))}
                            <td className="px-3 py-2.5 text-right font-bold text-gray-900 tabular-nums">
                              {Number(f.total_alarms ?? 0).toLocaleString()}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Map */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <p className="text-sm font-semibold text-gray-900 mb-3">Flight Path Map</p>
              <FlightMap height={280} />
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{subtitle} — {totalItems} found</p>
        </div>
        <DateRangePicker startDate={startDate} endDate={endDate} onStartChange={setStartDate} onEndChange={setEndDate} />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        {/* Search bar */}
        <div className="px-5 py-3 border-b border-gray-100 flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { setSearch(inputVal); setPage(1) } }}
              placeholder="Search by name…"
              className="pl-9 pr-3 py-1.5 border border-gray-300 rounded-md text-sm w-full focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>
          <button
            onClick={() => { setSearch(inputVal); setPage(1) }}
            className="text-sm px-4 py-1.5 rounded-md font-semibold transition-opacity hover:opacity-80"
            style={{ background: '#b8f04a', color: '#0d1f14' }}
          >
            Search
          </button>
        </div>

        {loading ? <LoadingSpinner /> : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {['Name', 'ID', 'Nationality', 'Role'].map((h) => (
                      <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {pilots.map((p: any, i) => {
                    const isInstructor = String(p.instructor ?? '') === 'S'
                    const isStudent = String(p.student ?? '') === 'S'
                    return (
                      <tr
                        key={i}
                        onClick={() => setSelected(p)}
                        className="cursor-pointer hover:bg-green-50 transition-colors"
                      >
                        <td className="px-4 py-3 font-semibold text-gray-900">{String(p.pilot_name ?? p.nome ?? '—')}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-600">{String(p.id ?? p.codcf ?? '—')}</td>
                        <td className="px-4 py-3 text-gray-600">{String(p.nationality ?? '—')}</td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1.5">
                            {isInstructor && (
                              <span className="text-xs font-semibold px-2 py-0.5 rounded-full text-white" style={{ background: '#0d1f14' }}>Instructor</span>
                            )}
                            {isStudent && (
                              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">Student</span>
                            )}
                            {!isInstructor && !isStudent && (
                              <span className="text-xs text-gray-400">Pilot</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                  {pilots.length === 0 && (
                    <tr>
                      <td colSpan={4} className="text-center py-12 text-gray-500 text-sm">No pilots found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-600">
              <span>Page {page} of {totalPages} ({totalItems} total)</span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="p-1 rounded hover:bg-gray-100 disabled:opacity-40">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-1 rounded hover:bg-gray-100 disabled:opacity-40">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
