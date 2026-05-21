import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import { Maximize2, Minimize2 } from 'lucide-react'

export interface TelemetryPoint {
  latitude: number
  longitude: number
  attitude: string
  altitude?: number | null
  ground_speed?: number | null
  pitch?: number | null
  roll?: number | null
  heading?: number | null
  alarms?: string[]
  date_time?: string
}

export interface MapMarker {
  lat: number
  lng: number
  type: string
  label?: string
}

interface Props {
  telemetry?: TelemetryPoint[]
  markers?: MapMarker[]
  center?: [number, number]
  zoom?: number
  height?: number
}

// ─── Tile sources ─────────────────────────────────────────────────────────────

const TILE_LAYERS = {
  dark: {
    label: 'Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 19,
  },
  voyager: {
    label: 'Map',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 19,
  },
  satellite: {
    label: 'Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Esri, Maxar, Earthstar Geographics',
    maxZoom: 18,
  },
} as const

type TileStyle = keyof typeof TILE_LAYERS
type ColorMode = 'phase' | 'altitude'

// ─── Colours ──────────────────────────────────────────────────────────────────

const ATTITUDE_COLORS: Record<string, string> = {
  ascending_straight:  '#16a34a',
  ascending_left:      '#22c55e',
  ascending_right:     '#22c55e',
  stable_straight:     '#2563eb',
  stable_left:         '#60a5fa',
  stable_right:        '#60a5fa',
  descending_straight: '#ea580c',
  descending_left:     '#f59e0b',
  descending_right:    '#f59e0b',
  'landing-takeoff':   '#7c3aed',
  taxing:              '#6b7280',
}

const ATTITUDE_LABELS: Record<string, string> = {
  ascending_straight:  'Ascending',
  ascending_left:      'Ascending Left',
  ascending_right:     'Ascending Right',
  stable_straight:     'Level Flight',
  stable_left:         'Level Left',
  stable_right:        'Level Right',
  descending_straight: 'Descending',
  descending_left:     'Descending Left',
  descending_right:    'Descending Right',
  'landing-takeoff':   'Landing / Takeoff',
  taxing:              'Taxiing',
}

function attitudeColor(att: string): string {
  return ATTITUDE_COLORS[att] ?? '#94a3b8'
}

// Altitude gradient: blue → green → yellow → red
const ALT_STOPS = ['#3b82f6', '#22c55e', '#eab308', '#ef4444']

function lerpHex(c1: string, c2: string, t: number): string {
  const p = (h: string) => [
    parseInt(h.slice(1, 3), 16),
    parseInt(h.slice(3, 5), 16),
    parseInt(h.slice(5, 7), 16),
  ]
  const [r1, g1, b1] = p(c1)
  const [r2, g2, b2] = p(c2)
  return `rgb(${Math.round(r1 + (r2 - r1) * t)},${Math.round(g1 + (g2 - g1) * t)},${Math.round(b1 + (b2 - b1) * t)})`
}

function altColor(alt: number, minAlt: number, maxAlt: number): string {
  if (maxAlt <= minAlt) return ALT_STOPS[0]
  const t = Math.max(0, Math.min(1, (alt - minAlt) / (maxAlt - minAlt)))
  const n = ALT_STOPS.length - 1
  const scaled = t * n
  const idx = Math.min(Math.floor(scaled), n - 1)
  return lerpHex(ALT_STOPS[idx], ALT_STOPS[idx + 1], scaled - idx)
}

// ─── Icons ────────────────────────────────────────────────────────────────────

function bearing(p1: TelemetryPoint, p2: TelemetryPoint): number {
  const toRad = (d: number) => d * Math.PI / 180
  const lat1 = toRad(p1.latitude), lat2 = toRad(p2.latitude)
  const dLon = toRad(p2.longitude - p1.longitude)
  const y = Math.sin(dLon) * Math.cos(lat2)
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon)
  return ((Math.atan2(y, x) * 180 / Math.PI) + 360) % 360
}

// Top-down aircraft silhouette, pointing north (0°)
const AIRCRAFT_PATH = 'M12 2L14 9L22 13L22 15L14 12.5L15.5 20L18 21V22L12 21L6 22V21L8.5 20L10 12.5L2 15V13L10 9Z'

function aircraftIcon(hdg: number, color = '#b8f04a'): L.DivIcon {
  return L.divIcon({
    html: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
      width="34" height="34"
      style="transform:rotate(${hdg}deg);filter:drop-shadow(0 2px 6px rgba(0,0,0,0.7));overflow:visible">
      <path d="${AIRCRAFT_PATH}"
        fill="${color}" stroke="rgba(0,0,0,0.5)" stroke-width="0.6" stroke-linejoin="round"/>
    </svg>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    className: '',
  })
}

function alarmMarkerIcon(): L.DivIcon {
  return L.divIcon({
    html: `<div style="
      width:22px;height:22px;
      background:#dc2626;
      border:2.5px solid white;
      border-radius:50%;
      box-shadow:0 0 0 4px rgba(220,38,38,0.3);
      color:white;font-size:13px;font-weight:800;
      line-height:17px;text-align:center;
    ">!</div>`,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    className: '',
  })
}

const DEFAULT_CENTER: [number, number] = [42.4, 13.3]

// ─── Component ────────────────────────────────────────────────────────────────

export default function FlightMap({ telemetry = [], markers = [], center, zoom, height = 460 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const dataSigRef = useRef('')
  const [fullscreen, setFullscreen] = useState(false)
  const [tileStyle, setTileStyle] = useState<TileStyle>('dark')
  const [colorMode, setColorMode] = useState<ColorMode>('phase')

  const validPts = telemetry.filter(
    (p) => p.latitude != null && p.longitude != null && !isNaN(p.latitude) && !isNaN(p.longitude)
  )

  const derivedCenter: [number, number] = center ?? (
    validPts.length > 0
      ? [validPts[Math.floor(validPts.length / 2)].latitude, validPts[Math.floor(validPts.length / 2)].longitude]
      : DEFAULT_CENTER
  )
  const derivedZoom = zoom ?? (validPts.length > 0 ? 11 : 9)

  // ─── Fullscreen ─────────────────────────────────────────────────────────────

  useEffect(() => {
    document.body.style.overflow = fullscreen ? 'hidden' : ''
    if (mapRef.current) {
      if (fullscreen) mapRef.current.scrollWheelZoom.enable()
      else mapRef.current.scrollWheelZoom.disable()
    }
    let raf2: number
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(() => mapRef.current?.invalidateSize())
    })
    return () => {
      cancelAnimationFrame(raf1)
      cancelAnimationFrame(raf2)
      document.body.style.overflow = ''
    }
  }, [fullscreen])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setFullscreen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // ─── Map ────────────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!containerRef.current) return

    const dataSig = JSON.stringify(validPts) + JSON.stringify(markers)
    const dataChanged = dataSig !== dataSigRef.current
    dataSigRef.current = dataSig

    const savedCenter = mapRef.current?.getCenter()
    const savedZoom   = mapRef.current?.getZoom()
    if (mapRef.current) { mapRef.current.remove(); mapRef.current = null }

    const map = L.map(containerRef.current, {
      scrollWheelZoom: false,
      zoomControl: false,
      attributionControl: true,
    })
    mapRef.current = map

    // Restore view when only tile/colour mode changed
    if (!dataChanged && savedCenter && savedZoom != null) {
      map.setView([savedCenter.lat, savedCenter.lng], savedZoom)
    } else {
      map.setView(derivedCenter, derivedZoom)
    }

    // Move zoom control to bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map)

    const { url, attribution, maxZoom } = TILE_LAYERS[tileStyle]
    L.tileLayer(url, { attribution, maxZoom, subdomains: 'abcd' }).addTo(map)

    if (validPts.length > 1) {
      const latLngs = validPts.map((p) => [p.latitude, p.longitude] as [number, number])
      const altValues = validPts.map((p) => p.altitude).filter((v): v is number => v != null)
      const minAlt = altValues.length ? altValues.reduce((m, v) => Math.min(m, v), Infinity) : 0
      const maxAlt = altValues.length ? altValues.reduce((m, v) => Math.max(m, v), -Infinity) : 1

      // White outline for contrast (thicker on dark tiles)
      L.polyline(latLngs, {
        color: tileStyle === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.7)',
        weight: 8,
        opacity: 1,
      }).addTo(map)

      if (colorMode === 'phase') {
        // Coloured segments by flight phase
        let segStart = 0
        for (let i = 1; i <= validPts.length; i++) {
          const att = validPts[segStart].attitude
          if (validPts[i]?.attitude !== att || i === validPts.length) {
            const segPts = validPts.slice(segStart, i)
            const seg = segPts.map((p) => [p.latitude, p.longitude] as [number, number])
            if (seg.length >= 2) {
              const color = attitudeColor(att)
              const alarmPts = segPts.filter((p) => p.alarms && p.alarms.length > 0)
              const timeFrom = segPts[0]?.date_time?.slice(11, 19) ?? '—'
              const timeTo = segPts[segPts.length - 1]?.date_time?.slice(11, 19) ?? '—'
              const altVals = segPts.map((p) => p.altitude).filter((v): v is number => v != null)
              const spdVals = segPts.map((p) => p.ground_speed).filter((v): v is number => v != null)
              const avgAlt = altVals.length ? altVals.reduce((s, v) => s + v, 0) / altVals.length : null
              const avgSpd = spdVals.length ? spdVals.reduce((s, v) => s + v, 0) / spdVals.length : null

              const popup = `
                <div style="font-family:sans-serif;font-size:12px;line-height:1.8;min-width:190px">
                  <div style="display:flex;align-items:center;gap:7px;margin-bottom:7px;padding-bottom:6px;border-bottom:1px solid #e5e7eb">
                    <div style="width:11px;height:11px;border-radius:50%;background:${color};flex-shrink:0"></div>
                    <b style="font-size:13px;color:#111">${ATTITUDE_LABELS[att] ?? att}</b>
                  </div>
                  <div style="color:#555;display:grid;grid-template-columns:auto 1fr;gap:2px 10px">
                    <span>Time</span><b>${timeFrom} – ${timeTo}</b>
                    <span>Avg altitude</span><b>${avgAlt != null ? avgAlt.toFixed(0) + ' ft' : '—'}</b>
                    <span>Avg speed</span><b>${avgSpd != null ? avgSpd.toFixed(1) + ' kt' : '—'}</b>
                    <span>Points</span><b>${segPts.length}</b>
                  </div>
                  ${alarmPts.length > 0
                    ? `<div style="margin-top:7px;padding-top:6px;border-top:1px solid #fee2e2;color:#dc2626;font-weight:600">
                        ⚠ ${alarmPts.length} alarm point${alarmPts.length > 1 ? 's' : ''} in this segment
                      </div>`
                    : ''}
                </div>`
              L.polyline(seg, { color, weight: 4, opacity: 0.95 })
                .bindPopup(popup, { maxWidth: 260 })
                .addTo(map)
            }
            segStart = i
          }
        }
      } else {
        // Altitude gradient — group into colour buckets to avoid thousands of polylines
        const BUCKETS = 24
        const getBucket = (alt: number | null | undefined) => {
          if (alt == null || maxAlt <= minAlt) return 0
          return Math.min(BUCKETS - 1, Math.floor(((alt - minAlt) / (maxAlt - minAlt)) * BUCKETS))
        }

        let altSegStart = 0
        let curBucket = getBucket(validPts[0].altitude)

        for (let i = 1; i <= validPts.length; i++) {
          const nextBucket = i < validPts.length ? getBucket(validPts[i].altitude) : -1
          if (nextBucket !== curBucket || i === validPts.length) {
            const segPts = validPts.slice(altSegStart, i)
            // Extend by one point for visual continuity between segments
            const drawPts = i < validPts.length ? [...segPts, validPts[i]] : segPts
            const seg = drawPts.map((p) => [p.latitude, p.longitude] as [number, number])

            if (seg.length >= 2) {
              const altNums = segPts.map((p) => p.altitude).filter((v): v is number => v != null)
              const spdNums = segPts.map((p) => p.ground_speed).filter((v): v is number => v != null)
              const avgAlt = altNums.length ? altNums.reduce((s, v) => s + v, 0) / altNums.length : null
              const avgSpd = spdNums.length ? spdNums.reduce((s, v) => s + v, 0) / spdNums.length : null
              const color = altColor(avgAlt ?? minAlt, minAlt, maxAlt)
              const timeFrom = segPts[0]?.date_time?.slice(11, 19) ?? '—'
              const timeTo = segPts[segPts.length - 1]?.date_time?.slice(11, 19) ?? '—'

              L.polyline(seg, { color, weight: 4, opacity: 0.95 })
                .bindPopup(
                  `<div style="font-family:sans-serif;font-size:12px;line-height:1.8;min-width:180px">
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;padding-bottom:5px;border-bottom:1px solid #e5e7eb">
                      <div style="width:10px;height:10px;border-radius:2px;background:${color};flex-shrink:0"></div>
                      <b>${avgAlt != null ? avgAlt.toFixed(0) + ' ft' : '—'}</b>
                    </div>
                    <div style="color:#555;display:grid;grid-template-columns:auto 1fr;gap:2px 10px">
                      <span>Time</span><b>${timeFrom} – ${timeTo}</b>
                      <span>Avg altitude</span><b>${avgAlt != null ? avgAlt.toFixed(0) + ' ft' : '—'}</b>
                      <span>Avg speed</span><b>${avgSpd != null ? avgSpd.toFixed(1) + ' kt' : '—'}</b>
                      <span>Points</span><b>${segPts.length}</b>
                    </div>
                  </div>`,
                  { maxWidth: 230 }
                )
                .addTo(map)
            }
            altSegStart = i
            curBucket = nextBucket
          }
        }
      }

      // Aircraft icon at last position (rotated to heading)
      const lastPt = validPts[validPts.length - 1]
      const prevPt = validPts.length >= 2 ? validPts[validPts.length - 2] : null
      const hdg = lastPt.heading != null
        ? lastPt.heading
        : prevPt ? bearing(prevPt, lastPt) : 0

      L.marker([lastPt.latitude, lastPt.longitude], { icon: aircraftIcon(hdg), zIndexOffset: 500 })
        .bindPopup(`
          <div style="font-family:sans-serif;font-size:12px;line-height:1.8">
            <b style="font-size:13px">Last position</b><br/>
            <div style="color:#555;display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin-top:4px">
              <span>Time</span><b>${lastPt.date_time ?? '—'}</b>
              <span>Altitude</span><b>${lastPt.altitude != null ? lastPt.altitude.toFixed(0) + ' ft' : '—'}</b>
              <span>Speed</span><b>${lastPt.ground_speed != null ? lastPt.ground_speed.toFixed(1) + ' kt' : '—'}</b>
              <span>Heading</span><b>${hdg.toFixed(0)}°</b>
            </div>
          </div>`)
        .addTo(map)

      // Takeoff marker (start dot)
      L.circleMarker([validPts[0].latitude, validPts[0].longitude], {
        radius: 7, color: '#fff', weight: 2.5, fillColor: '#16a34a', fillOpacity: 1,
      }).bindPopup(`<b>Takeoff</b><br/><span style="color:#555">${validPts[0].date_time ?? ''}</span>`).addTo(map)

      // Alarm markers
      validPts
        .filter((p) => p.alarms && p.alarms.length > 0)
        .forEach((p) => {
          const alarmList = p.alarms!
            .map((a) => `<div style="color:#dc2626">• ${a.replace(/_/g, ' ')}</div>`)
            .join('')
          const popup = `
            <div style="font-family:sans-serif;font-size:12px;line-height:1.7;min-width:190px">
              <div style="color:#dc2626;font-weight:700;font-size:13px;margin-bottom:5px">⚠ Alarm triggered</div>
              <div style="background:#fef2f2;border-radius:5px;padding:5px 8px;margin-bottom:7px">${alarmList}</div>
              <div style="color:#555;display:grid;grid-template-columns:auto 1fr;gap:2px 10px">
                <span>Time</span><b>${p.date_time ?? '—'}</b>
                <span>Phase</span><b>${ATTITUDE_LABELS[p.attitude] ?? p.attitude}</b>
                <span>Altitude</span><b>${p.altitude != null ? p.altitude.toFixed(0) + ' ft' : '—'}</b>
                <span>Speed</span><b>${p.ground_speed != null ? p.ground_speed.toFixed(1) + ' kt' : '—'}</b>
                ${p.pitch != null ? `<span>Pitch</span><b>${p.pitch.toFixed(1)}°</b>` : ''}
                ${p.roll != null ? `<span>Roll</span><b>${p.roll.toFixed(1)}°</b>` : ''}
              </div>
            </div>`
          L.marker([p.latitude, p.longitude], { icon: alarmMarkerIcon() })
            .bindPopup(popup, { maxWidth: 280 })
            .addTo(map)
        })

      if (dataChanged) {
        map.fitBounds(L.latLngBounds(latLngs), { padding: [32, 32] })
      }
    }

    markers.forEach((m) => {
      L.circleMarker([m.lat, m.lng], {
        radius: 6, color: '#fff', weight: 1.5, fillColor: '#ef4444', fillOpacity: 0.85,
      }).bindPopup(m.label ?? m.type).addTo(map)
    })

    return () => { map.remove(); mapRef.current = null }
  }, [JSON.stringify(validPts), JSON.stringify(markers), tileStyle, colorMode])

  // ─── Render ─────────────────────────────────────────────────────────────────

  const presentAttitudes = [...new Set(validPts.map((p) => p.attitude))].filter(Boolean)
  const alarmCount = validPts.filter((p) => p.alarms && p.alarms.length > 0).length

  const isDark = tileStyle === 'dark'

  // Altitude range for legend
  const altVals = validPts.map((p) => p.altitude).filter((v): v is number => v != null)
  const minAlt = altVals.length ? altVals.reduce((m, v) => Math.min(m, v), Infinity) : 0
  const maxAlt = altVals.length ? altVals.reduce((m, v) => Math.max(m, v), -Infinity) : 0

  const controlBg = isDark
    ? 'bg-gray-900/90 border-gray-700 text-gray-100 hover:bg-gray-800'
    : 'bg-white/90 border-gray-200 text-gray-700 hover:bg-white'

  return (
    <div className="relative">
      {fullscreen && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9998, background: isDark ? '#1a1a2e' : 'white' }} />
      )}

      {/* Map container */}
      <div
        ref={containerRef}
        style={fullscreen
          ? { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }
          : { height }}
        className={fullscreen ? '' : 'rounded-xl overflow-hidden border border-gray-200'}
      />

      {/* ── Top-right control bar ───────────────────────────────────── */}
      <div
        style={fullscreen ? { position: 'fixed', top: 12, right: 12, zIndex: 10001 } : {}}
        className={`${fullscreen ? '' : 'absolute top-3 right-3 z-[1001]'} flex items-center gap-1.5`}
      >
        {/* Color mode toggle */}
        <div className={`flex rounded-lg overflow-hidden shadow-md border backdrop-blur-sm ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          {(['phase', 'altitude'] as ColorMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setColorMode(mode)}
              className={`px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                colorMode === mode
                  ? 'bg-gray-900 text-white'
                  : isDark ? 'bg-gray-800/80 text-gray-300 hover:bg-gray-700' : 'bg-white/90 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {mode === 'phase' ? 'Phase' : 'Altitude'}
            </button>
          ))}
        </div>

        {/* Tile switcher */}
        <div className={`flex rounded-lg overflow-hidden shadow-md border backdrop-blur-sm ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
          {(Object.keys(TILE_LAYERS) as TileStyle[]).map((key) => (
            <button
              key={key}
              onClick={() => setTileStyle(key)}
              className={`px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                tileStyle === key
                  ? 'bg-gray-900 text-white'
                  : isDark ? 'bg-gray-800/80 text-gray-300 hover:bg-gray-700' : 'bg-white/90 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {TILE_LAYERS[key].label}
            </button>
          ))}
        </div>

        {/* Fullscreen toggle */}
        <button
          onClick={() => setFullscreen((f) => !f)}
          className={`${controlBg} backdrop-blur-sm rounded-lg p-1.5 shadow-md transition-colors border`}
          title={fullscreen ? 'Exit fullscreen (Esc)' : 'Expand map'}
        >
          {fullscreen
            ? <Minimize2 className="w-4 h-4" />
            : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* ── Bottom-left legend ──────────────────────────────────────── */}
      {(presentAttitudes.length > 0 || alarmCount > 0) && (
        <div
          className={`${fullscreen ? '' : 'absolute bottom-3 left-3 z-[1000]'} rounded-xl shadow-lg p-3 backdrop-blur-sm`}
          style={{
            ...(fullscreen ? { position: 'fixed' as const, bottom: 52, left: 12, zIndex: 10001 } : {}),
            background: isDark ? 'rgba(15,17,26,0.88)' : 'rgba(255,255,255,0.93)',
            backdropFilter: 'blur(8px)',
            maxWidth: 200,
            border: isDark ? '1px solid rgba(255,255,255,0.08)' : '1px solid #e5e7eb',
          }}
        >
          {colorMode === 'phase' ? (
            <>
              <p className={`text-xs font-bold mb-1 uppercase tracking-wider ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Flight Phase
              </p>
              <p className={`text-xs mb-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Click path for details</p>
              <div className="space-y-1.5">
                {presentAttitudes.map((att) => (
                  <div key={att} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: attitudeColor(att) }} />
                    <span className={`text-xs ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{ATTITUDE_LABELS[att] ?? att}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <p className={`text-xs font-bold mb-1 uppercase tracking-wider ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Altitude
              </p>
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 h-2.5 rounded" style={{
                  background: `linear-gradient(to right, ${ALT_STOPS.join(',')})`
                }} />
              </div>
              <div className={`flex justify-between text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <span>{minAlt.toFixed(0)} ft</span>
                <span>{maxAlt.toFixed(0)} ft</span>
              </div>
            </>
          )}
          {alarmCount > 0 && (
            <div className={`flex items-center gap-2 pt-1.5 mt-1.5 ${isDark ? 'border-t border-gray-700' : 'border-t border-gray-100'}`}>
              <div className="w-3 h-3 rounded-full flex-shrink-0 bg-red-600 text-white"
                style={{ fontSize: 7, fontWeight: 800, lineHeight: '12px', textAlign: 'center' }}>!</div>
              <span className={`text-xs ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Alarm ({alarmCount})</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
