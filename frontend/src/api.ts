const BASE = '/api'

function token(): string | null {
  return localStorage.getItem('token')
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const t = token()
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(t ? { Authorization: `Bearer ${t}` } : {}),
      ...(opts.headers ?? {}),
    },
  })
  if (res.status === 204) return [] as unknown as T
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.message ?? `HTTP ${res.status}`)
  }
  return res.json()
}

function post<T>(path: string, body: unknown): Promise<T> {
  return req<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export type LoginResponse = { data: { user: { email: string }; token: string } }

export const login = (email: string, password: string) =>
  post<LoginResponse>('/login', { email, password })

// ─── Registrations ───────────────────────────────────────────────────────────

export type Registration = Record<string, unknown>

export const getRegistrations = () =>
  req<{ data: Registration[] }>('/all_registrations')

export const getRegistrationsCount = () =>
  req<{ data: number }>('/all_registrations_count')

export const getRegistrationsWithFlights = () =>
  req<{ data: Registration[] }>('/registrations_with_flights')

export const getRegistrationsWithFlightsCount = () =>
  req<{ data: number }>('/registrations_with_flights_count')

export const getRegistrationFlights = (id: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/flights`)

export const getRegistrationFlightsByDate = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/flights/${start}/${end}`)

export const getFlightsByRegistrationIds = (ids: string[], start: string, end: string) =>
  post<{ data: unknown[] }>(`/registration/flights/${start}/${end}`, { registration_ids: ids })

export const getFlewHoursByRegistration = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/flewhours/registration/${id}/flights/${start}/${end}`)

export const getRegistrationAlarms = (id: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/alarms`)

export const getRegistrationAlarmsByDate = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/alarms/${start}/${end}`)

export const getRegistrationTopAlarms = (id: string, top: number, start: string, end: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/${top}/alarms/${start}/${end}`)

export const getRegistrationFlightsWithAlarms = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/flightswithalarms/${start}/${end}`)

export const getRegistrationTopFlightsWithAlarms = (id: string, top: number, start: string, end: string) =>
  req<{ data: unknown[] }>(`/registration/${id}/top_flightswithalarms/${top}/${start}/${end}`)

// ─── Pilots ──────────────────────────────────────────────────────────────────

export type Pilot = Record<string, unknown>

export const getPilots = () =>
  req<{ data: Pilot[] }>('/all_pilots')

export const getPilotsCount = () =>
  req<{ data: number }>('/all_pilots_count')

export const getPilotsWithFlights = () =>
  req<{ data: Pilot[] }>('/pilots_with_flights')

export const getPilotsWithFlightsCount = () =>
  req<{ data: number }>('/pilots_with_flights_count')

export const getPaginatedPilots = (start: string, end: string, page = 1, pageSize = 20) =>
  req<{ data: Pilot[]; pagination: { total_items: number; total_pages: number; has_next: boolean; has_prev: boolean } }>(
    `/all_pilots_pg/${start}/${end}?page=${page}&page_size=${pageSize}`
  )

export const searchPilots = (start: string, end: string, search = '', page = 1, pageSize = 20) =>
  req<{ data: Pilot[]; pagination: { total_items: number; total_pages: number; has_next: boolean; has_prev: boolean } }>(
    `/all_pilots_search/${start}/${end}?search=${encodeURIComponent(search)}&page=${page}&page_size=${pageSize}`
  )

export const getPilotFlights = (id: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/flights`)

export const getPilotFlightsByDate = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/flights/${start}/${end}`)

export const getFlewHoursByPilot = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/flewhours/pilot/${id}/flights/${start}/${end}`)

export const getPilotAlarms = (id: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/alarms`)

export const getPilotAlarmsByDate = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/alarms/${start}/${end}`)

export const getPilotTopAlarms = (id: string, top: number, start: string, end: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/${top}/alarms/${start}/${end}`)

export const getPilotFlightsWithAlarms = (id: string, start: string, end: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/flightswithalarms/${start}/${end}`)

export const getPilotTopFlightsWithAlarms = (id: string, top: number, start: string, end: string) =>
  req<{ data: unknown[] }>(`/pilot/${id}/top_flightswithalarms/${top}/${start}/${end}`)

// ─── Flights ─────────────────────────────────────────────────────────────────

export const getFlights = () =>
  req<{ data: unknown[] }>('/flights')

export const getFlightTimeDuration = (id: number) =>
  req<{ data: unknown[] }>(`/flight/${id}/time_duration`)

export const getFlightTelemetry = (id: number) =>
  req<{ data: unknown[] }>(`/telemetry/flight/${id}`)

// ─── Alarms / Telemetry ───────────────────────────────────────────────────────

export type AlarmSummary = { registration: string; total: number } & Record<string, number>

export const getAllAlarms = (start: string, end: string) =>
  req<{ data: AlarmSummary[] }>(`/registrations/alarms/${start}/${end}`)

export const getTopRegistrationsByAlarms = (top: number, start: string, end: string) =>
  req<{ data: AlarmSummary[] }>(`/top_registrations/alarms/${top}/${start}/${end}`)

export const getFlightAlarms = (id: number) =>
  req<{ data: unknown[] }>(`/alarms/flight/${id}`)

export const getFlightTopAlarms = (id: number, top: number) =>
  req<{ data: unknown[] }>(`/alarms/flight/${id}/${top}`)

export const getAllAlarmsTelemetry = (start: string, end: string) =>
  req<{ data: unknown[] }>(`/registrations/alarms/telemetry/${start}/${end}`)

export const getAlarmsTelemetryByRegistrations = (ids: string[], start: string, end: string) =>
  post<{ data: unknown[] }>(`/registration/alarms/telemetry/${start}/${end}`, { registration_ids: ids })
