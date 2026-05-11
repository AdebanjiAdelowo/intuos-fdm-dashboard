import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { alarmColor, alarmLabel } from '../constants/alarmColors'

export interface MapMarker {
  lat: number
  lng: number
  type: string
  label?: string
}

interface Props {
  markers?: MapMarker[]
  center?: [number, number]
  zoom?: number
  height?: number
}

const TURIN: [number, number] = [45.07, 7.67]

export default function FlightMap({ markers = [], center = TURIN, zoom = 9, height = 320 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    if (mapRef.current) return  // already initialized in this mount cycle

    const map = L.map(containerRef.current, { scrollWheelZoom: false }).setView(center, zoom)
    mapRef.current = map

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map)

    markers.forEach((m) => {
      L.circleMarker([m.lat, m.lng], {
        radius: 6,
        color: alarmColor(m.type),
        fillColor: alarmColor(m.type),
        fillOpacity: 0.8,
      })
        .bindPopup(m.label ?? alarmLabel(m.type))
        .addTo(map)
    })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [center, zoom, markers])

  return (
    <div
      ref={containerRef}
      style={{ height }}
      className="rounded-xl overflow-hidden border border-gray-200"
    />
  )
}
