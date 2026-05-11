import { useEffect, useState } from 'react'
import { ChevronLeft, Plane } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import {
  getRegistrationsWithFlights,
  getRegistrationAlarmsByDate,
  getRegistrationFlightsByDate,
  getRegistrationFlightsWithAlarms,
  getFlewHoursByRegistration,
} from '../api'
import DataTable from '../components/DataTable'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { useDateRange } from '../hooks/useDateRange'

type Reg = Record<string, unknown>

const REG_COLS = [
  { key: 'id', label: 'ID' },
  { key: 'marche', label: 'Registration' },
  { key: 'model', label: 'Model' },
  { key: 'type', label: 'Type' },
]

export default function RegistrationsPage() {
  const { startDate, endDate, setStartDate, setEndDate } = useDateRange()
  const [registrations, setRegistrations] = useState<Reg[]>([])
  const [selected, setSelected] = useState<Reg | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')

  // Detail state
  const [flights, setFlights] = useState<Reg[]>([])
  const [alarms, setAlarms] = useState<Reg[]>([])
  const [flightsWithAlarms, setFlightsWithAlarms] = useState<number | null>(null)
  const [flewHours, setFlewHours] = useState<Reg[]>([])

  useEffect(() => {
    setLoading(true)
    getRegistrationsWithFlights()
      .then((r) => setRegistrations(Array.isArray(r.data) ? r.data : []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    const id = String(selected.marche ?? selected.id ?? '')
    if (!id) return
    setDetailLoading(true)
    Promise.all([
      getRegistrationFlightsByDate(id, startDate, endDate),
      getRegistrationAlarmsByDate(id, startDate, endDate),
      getRegistrationFlightsWithAlarms(id, startDate, endDate),
      getFlewHoursByRegistration(id, startDate, endDate),
    ])
      .then(([fl, al, fwa, fh]) => {
        const flData = Array.isArray(fl.data) ? fl.data : (fl.data as any)?.flights ?? []
        setFlights(flData as Reg[])
        setAlarms(Array.isArray(al.data) ? al.data as Reg[] : [])
        const fwaVal = Array.isArray(fwa.data) ? fwa.data[0] : null
        setFlightsWithAlarms(typeof fwaVal === 'number' ? fwaVal : null)
        setFlewHours(Array.isArray(fh.data) ? fh.data as Reg[] : [])
      })
      .catch(() => {})
      .finally(() => setDetailLoading(false))
  }, [selected, startDate, endDate])

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
    const regId = String(selected.marche ?? selected.id ?? '?')
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-1 text-sm text-brand-600 hover:text-brand-800 mb-4"
        >
          <ChevronLeft className="w-4 h-4" /> Back to registrations
        </button>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Plane className="w-6 h-6 text-brand-600" />
              {regId}
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">Registration detail</p>
          </div>
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onStartChange={setStartDate}
            onEndChange={setEndDate}
          />
        </div>

        {detailLoading ? (
          <LoadingSpinner />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <StatCard label="Flights in Range" value={flights.length} />
              <StatCard label="Flights with Alarms" value={flightsWithAlarms ?? '—'} />
              <StatCard
                label="Flew Hours"
                value={flewHours.length > 0 ? String(Object.values(flewHours[0])[0] ?? '—') : '—'}
              />
            </div>

            {alarmChartData.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mb-6">
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
            )}

            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-3">Recent Flights</h2>
              <DataTable
                columns={[
                  { key: 'id_volo', label: 'Flight ID' },
                  { key: 'stick_on', label: 'Departure' },
                  { key: 'stick_off', label: 'Arrival' },
                ]}
                data={flights.slice(0, 50)}
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
          <h1 className="text-2xl font-bold text-gray-900">Registrations</h1>
          <p className="text-sm text-gray-500 mt-0.5">Aircraft with recorded flights</p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100">
          <span className="text-sm text-gray-500">{registrations.length} aircraft</span>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <DataTable
            columns={REG_COLS}
            data={registrations}
            onRowClick={(row) => setSelected(row)}
            emptyMessage="No registrations found."
          />
        )}
      </div>
    </div>
  )
}
