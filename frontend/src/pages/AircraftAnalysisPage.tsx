import { useEffect, useState } from 'react'
import { ChevronLeft, Plane, AlertTriangle, Clock, Navigation2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
  getRegistrationsWithFlights,
  getRegistrationAlarmsByDate,
  getRegistrationFlightsByDate,
  getRegistrationFlightsWithAlarms,
  getRegistrationTopFlightsWithAlarms,
  getFlewHoursByRegistration,
} from '../api'
import AlarmDonut from '../components/AlarmDonut'
import FlightMap from '../components/FlightMap'
import DataTable from '../components/DataTable'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { useDateRange } from '../hooks/useDateRange'
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
              <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, background: alarmColor(name) }} />
            </div>
            <span className="text-sm font-semibold text-gray-900 w-14 text-right tabular-nums">{value.toLocaleString()}</span>
            <span className="text-xs text-gray-400 w-10 text-right tabular-nums">{pct.toFixed(1)}%</span>
          </div>
        )
      })}
    </div>
  )
}

export default function AircraftAnalysisPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [registrations, setRegistrations] = useState<Row[]>([])
  const [selected, setSelected] = useState<Row | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')

  const [flights, setFlights] = useState<Row[]>([])
  const [flightsTotal, setFlightsTotal] = useState<number>(0)
  const [alarms, setAlarms] = useState<Row[]>([])
  const [flightsWithAlarms, setFlightsWithAlarms] = useState<number | null>(null)
  const [topFlights, setTopFlights] = useState<Row[]>([])
  const [flewHours, setFlewHours] = useState<Row[]>([])

  useEffect(() => {
    setLoading(true)
    getRegistrationsWithFlights()
      .then((r) => setRegistrations(Array.isArray(r.data) ? r.data : []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    const id = String(selected.marche ?? selected.id ?? '').trim()
    if (!id) return
    setDetailLoading(true)
    Promise.all([
      getRegistrationFlightsByDate(id, startDate, endDate),
      getRegistrationAlarmsByDate(id, startDate, endDate),
      getRegistrationFlightsWithAlarms(id, startDate, endDate),
      getRegistrationTopFlightsWithAlarms(id, 10, startDate, endDate),
      getFlewHoursByRegistration(id, startDate, endDate),
    ])
      .then(([fl, al, fwa, topFl, fh]) => {
        // flights are nested: data[0].flights
        const raw = Array.isArray(fl.data) ? fl.data : []
        const inner = raw[0] as any
        const flList: Row[] = inner?.flights ?? (Array.isArray(fl.data) ? fl.data as Row[] : [])
        setFlights(flList)
        setFlightsTotal(inner?.flights_length ?? flList.length)

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
  const totalAlarms = alarmEntries.reduce((s, e) => s + e.value, 0)

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
    const regId = String(selected.marche ?? selected.id ?? '?').trim()
    const model = String(selected.typedesignator ?? selected.model ?? '').trim()
    const country = String(selected.country ?? '').trim()

    return (
      <div className="p-6 max-w-7xl mx-auto">
        {/* Back */}
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-1.5 text-sm font-medium mb-5 hover:opacity-70 transition-opacity"
          style={{ color: '#0d1f14' }}
        >
          <ChevronLeft className="w-4 h-4" /> Back to aircraft list
        </button>

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: '#0d1f14' }}>
              <Plane className="w-6 h-6" style={{ color: '#b8f04a' }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">{regId}</h1>
                {model && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{model}</span>
                )}
                {country && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full text-white" style={{ background: '#0d1f14' }}>{country}</span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-0.5">Aircraft Analysis · {flightsTotal} flights in range</p>
            </div>
          </div>
          <DateRangePicker startDate={startDate} endDate={endDate} onStartChange={setStartDate} onEndChange={setEndDate} />
        </div>

        {detailLoading ? <LoadingSpinner /> : (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <StatCard label="Total Flights" value={flightsTotal} icon={<Navigation2 className="w-5 h-5" />} accent />
              <StatCard label="Flights with Alerts" value={flightsWithAlarms ?? '—'} icon={<AlertTriangle className="w-5 h-5" />} />
              <StatCard label="Total Alerts" value={totalAlarms.toLocaleString()} icon={<AlertTriangle className="w-5 h-5" />} />
              <StatCard label="Flew Hours" value={flewVal} icon={<Clock className="w-5 h-5" />} />
            </div>

            {/* Charts row */}
            {alarmEntries.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                  <p className="text-sm font-semibold text-gray-900">Alert Distribution</p>
                  <p className="text-xs text-gray-400 mb-3">{totalAlarms.toLocaleString()} total alerts</p>
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
            )}

            {/* Alarm breakdown detail */}
            {alarmEntries.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
                <p className="text-sm font-semibold text-gray-900 mb-4">Alert Type Detail</p>
                <AlarmBreakdown entries={alarmEntries} total={totalAlarms} />
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
                        {ALARM_KEYS.filter((k) => topFlights.some((f) => Number(f[k]) > 0)).map((k) => (
                          <th key={k} className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide" style={{ color: alarmColor(k) }}>
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
                            <td className="px-3 py-2.5 font-medium text-gray-900">#{String(f.id_volo ?? '—')}</td>
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
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
              <p className="text-sm font-semibold text-gray-900 mb-3">Flight Path Map</p>
              <FlightMap height={300} />
            </div>

            {/* Flights table */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <p className="text-sm font-semibold text-gray-900 mb-1">All Flights</p>
              <p className="text-xs text-gray-400 mb-4">{flightsTotal} flights in selected range</p>
              <DataTable
                columns={[
                  { key: 'id_volo', label: 'Flight #', render: (v) => <span className="font-mono font-medium text-gray-900">#{v as string}</span> },
                  {
                    key: 'stick_on', label: 'Date',
                    render: (v) => (
                      <div>
                        <p className="font-medium text-gray-900">{formatDate(String(v))}</p>
                        <p className="text-xs text-gray-400">{formatTime(String(v))}</p>
                      </div>
                    ),
                  },
                  {
                    key: 'apt_takeoff', label: 'Route',
                    render: (_, row) => (
                      <span className="font-mono text-sm">
                        {String(row.apt_takeoff ?? '—')} → {String(row.apt_landing ?? '—')}
                      </span>
                    ),
                  },
                  {
                    key: 'stick_off', label: 'Duration',
                    render: (v, row) => (
                      <span className="tabular-nums text-gray-700">
                        {flightDuration(String(row.stick_on ?? ''), String(v))}
                      </span>
                    ),
                  },
                  {
                    key: 'codcf_pilot', label: 'Pilot ID',
                    render: (v) => {
                      const s = String(v ?? '').trim()
                      return s ? <span className="font-mono text-xs text-gray-600">{s}</span> : <span className="text-gray-300">—</span>
                    },
                  },
                ]}
                data={flights.slice(0, 100)}
                emptyMessage="No flights in this date range."
              />
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
          <h1 className="text-2xl font-bold text-gray-900">Aircraft Analysis</h1>
          <p className="text-sm text-gray-500 mt-0.5">Select an aircraft to analyse its flights and alerts</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">{registrations.length} aircraft</span>
          <span className="text-xs text-gray-400">Click a row to analyse</span>
        </div>
        {loading ? <LoadingSpinner /> : (
          <DataTable
            columns={[
              { key: 'marche', label: 'Registration', render: (v) => <span className="font-semibold font-mono text-gray-900">{String(v ?? '').trim()}</span> },
              { key: 'typedesignator', label: 'Type', render: (v) => <span className="text-gray-600">{String(v ?? '').trim() || '—'}</span> },
              { key: 'country', label: 'Country', render: (v) => {
                const s = String(v ?? '').trim()
                return s ? <span className="inline-block text-xs font-semibold px-2 py-0.5 rounded-full text-white" style={{ background: '#0d1f14' }}>{s}</span> : <span className="text-gray-300">—</span>
              }},
            ]}
            data={registrations}
            onRowClick={(row) => setSelected(row)}
            emptyMessage="No registrations found."
          />
        )}
      </div>
    </div>
  )
}
