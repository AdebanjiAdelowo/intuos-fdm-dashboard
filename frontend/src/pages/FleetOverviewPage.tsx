import { useEffect, useState } from 'react'
import { Activity, Plane, AlertTriangle, Users } from 'lucide-react'
import { Card, Title, Text, DonutChart, Legend, BarChart as TremorBar } from '@tremor/react'
import {
  getRegistrationsWithFlightsCount,
  getPilotsWithFlightsCount,
  getTopRegistrationsByAlarms,
  getAllAlarms,
  AlarmSummary,
} from '../api'
import StatCard from '../components/StatCard'
import DateRangePicker from '../components/DateRangePicker'
import LoadingSpinner from '../components/LoadingSpinner'
import { useDateRange } from '../hooks/useDateRange'
import { alarmColor, alarmLabel } from '../constants/alarmColors'

const TREMOR_COLORS = ['blue','yellow','violet','orange','red','cyan','purple','green','pink','lime','indigo','rose']

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

  const alarmTypeTotals: Record<string, number> = {}
  for (const row of allAlarms) {
    for (const [k, v] of Object.entries(row)) {
      if (k === 'registration' || k === 'total') continue
      if (Number(v) > 0) alarmTypeTotals[k] = (alarmTypeTotals[k] ?? 0) + Number(v)
    }
  }
  const donutData = Object.entries(alarmTypeTotals)
    .map(([name, value]) => ({ name: alarmLabel(name), value, key: name }))
    .sort((a, b) => b.value - a.value)

  const totalAlerts = donutData.reduce((s, d) => s + d.value, 0)
  const withAlerts = allAlarms.filter((a) => Number(a.total ?? 0) > 0).length

  const barData = topAlarms
    .slice(0, 10)
    .map((a) => ({ name: String(a.registration ?? '?').trim(), Alerts: Number(a.total ?? 0) }))

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-tremor-content-strong flex items-center gap-2">
            <Activity className="w-6 h-6" style={{ color: '#0d1f14' }} />
            Fleet Overview
          </h1>
          <Text className="mt-0.5">Fleet-wide alert distribution</Text>
        </div>
        <DateRangePicker startDate={startDate} endDate={endDate} onStartChange={setStartDate} onEndChange={setEndDate} />
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
            <Card>
              <Title>Alert Type Distribution</Title>
              <Text className="mt-1">{totalAlerts.toLocaleString()} total alerts</Text>
              <DonutChart
                data={donutData}
                category="value"
                index="name"
                colors={TREMOR_COLORS}
                valueFormatter={(v) => v.toLocaleString()}
                className="h-60 mt-4"
              />
              <Legend
                categories={donutData.slice(0, 6).map((d) => d.name)}
                colors={TREMOR_COLORS.slice(0, 6)}
                className="mt-4"
              />
            </Card>

            <Card>
              <Title>Top Aircraft by Alerts</Title>
              <Text className="mt-1">Top 10 registrations in range</Text>
              {barData.length === 0 ? (
                <p className="text-sm text-tremor-content text-center py-10">No data for this range</p>
              ) : (
                <TremorBar
                  data={barData}
                  index="name"
                  categories={['Alerts']}
                  colors={['green']}
                  valueFormatter={(v) => v.toLocaleString()}
                  showLegend={false}
                  className="h-60 mt-4"
                />
              )}
            </Card>
          </div>

          {/* Breakdown table */}
          <Card>
            <Title>Alert Breakdown by Type</Title>
            <div className="mt-4 space-y-3">
              {donutData.map(({ name, value, key }, i) => {
                const pct = totalAlerts > 0 ? (value / totalAlerts) * 100 : 0
                return (
                  <div key={name} className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: alarmColor(key) }} />
                    <span className="text-sm text-tremor-content-emphasis w-52 truncate">{name}</span>
                    <div className="flex-1 bg-tremor-background-subtle rounded-full h-2">
                      <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: alarmColor(key) }} />
                    </div>
                    <span className="text-sm font-semibold text-tremor-content-strong w-16 text-right tabular-nums">
                      {value.toLocaleString()}
                    </span>
                    <span className="text-xs text-tremor-content w-12 text-right tabular-nums">{pct.toFixed(1)}%</span>
                  </div>
                )
              })}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
