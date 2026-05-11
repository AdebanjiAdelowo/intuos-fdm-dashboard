export const ALARM_COLORS: Record<string, string> = {
  vertical_speed: '#3b82f6',
  pitch: '#eab308',
  roll: '#8b5cf6',
  ground_speed: '#f97316',
  g_tot: '#ef4444',
  hard_landing: '#06b6d4',
  high_roll_at_low_height: '#a855f7',
  low_ground_speed_at_low_height_with_low_acceleration: '#f43f5e',
  altitude: '#10b981',
  acc_z: '#64748b',
}

export function alarmColor(key: string): string {
  return ALARM_COLORS[key] ?? '#94a3b8'
}

export const ALARM_LABELS: Record<string, string> = {
  vertical_speed: 'Vertical Speed',
  pitch: 'Pitch',
  roll: 'Roll',
  ground_speed: 'Ground Speed',
  g_tot: 'G-Force',
  hard_landing: 'Hard Landing',
  high_roll_at_low_height: 'High Roll',
  low_ground_speed_at_low_height_with_low_acceleration: 'Low GS',
  altitude: 'Altitude',
  acc_z: 'Acc Z',
}

export function alarmLabel(key: string): string {
  return ALARM_LABELS[key] ?? key.replace(/_/g, ' ')
}
