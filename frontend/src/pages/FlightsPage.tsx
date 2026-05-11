import { useEffect, useState } from 'react'
import { ChevronLeft, BarChart2 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { getFlights, getFlightAlarms, getFlightTimeDuration } from '../api'
import DataTable from '../components/DataTable'
import LoadingSpinner from '../components/LoadingSpinner'

type Row = Record<string, unknown>

export default function FlightsPage() {
  const [flights, setFlights] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Row | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [alarms, setAlarms] = useState<Row[]>([])
  const [duration, setDuration] = useState<Row[]>([])
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
    Promise.all([
      getFlightAlarms(id),
      getFlightTimeDuration(id),
    ])
      .then(([al, dur]) => {
        setAlarms(Array.isArray(al.data) ? al.data as Row[] : [])
        setDuration(Array.isArray(dur.data) ? dur.data as Row[] : [])
      })
      .catch(() => {})
      .finally(() => setDetailLoading(false))
  }, [selected])

  const alarmChartData = alarms
    .slice(0, 1)
    .flatMap((row) =>
      Object.entries(row)
        .filter(([k, v]) => k !== 'registration' && k !== 'total' && Number(v) > 0)
        .map(([k, v]) => ({ name: k, count: Number(v) }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 15)
    )

  if (selected) {
    const flightId = String(selected.id_volo ?? selected.id ?? '?')
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-800 mb-4"
        >
          <ChevronLeft className="w-4 h-4" /> Back to flights
        </button>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart2 className="w-6 h-6 text-brand-600" />
            Flight #{flightId}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {String(selected.stick_on ?? '')} → {String(selected.stick_off ?? '')}
            {selected.marche ? ` · ${selected.marche}` : ''}
          </p>
        </div>

        {detailLoading ? (
          <LoadingSpinner />
        ) : (
          <>
            {duration.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
                <h2 className="text-base font-semibold text-gray-900 mb-3">Time Duration</h2>
                <DataTable
                  columns={Object.keys(duration[0]).map((k) => ({ key: k, label: k }))}
                  data={duration}
                />
              </div>
            )}

            {alarmChartData.length > 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <h2 className="text-base font-semibold text-gray-900 mb-4">Alarm Breakdown</h2>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={alarmChartData} margin={{ top: 4, right: 16, bottom: 60, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-40} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No alarms recorded for this flight.</p>
            )}
          </>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Flights</h1>
        <p className="text-sm text-gray-500 mt-0.5">All recorded flights — click to inspect</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100">
          <span className="text-sm text-gray-500">{flights.length} flights</span>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <DataTable
            columns={[
              { key: 'id_volo', label: 'Flight ID' },
              { key: 'marche', label: 'Registration' },
              { key: 'stick_on', label: 'Departure' },
              { key: 'stick_off', label: 'Arrival' },
            ]}
            data={flights.slice(0, 200)}
            onRowClick={(row) => setSelected(row)}
            emptyMessage="No flights found."
          />
        )}
      </div>
    </div>
  )
}
