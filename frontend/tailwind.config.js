/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@tremor/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        fdm: {
          950: '#081209',
          900: '#0d1f14',
          800: '#152b1c',
          700: '#1f3d27',
          600: '#2a5234',
          400: '#4a9a5e',
          lime: '#b8f04a',
        },
        tremor: {
          brand: {
            faint:   '#f0fdf4',
            muted:   '#bbf7d0',
            subtle:  '#4ade80',
            DEFAULT: '#0d1f14',
            emphasis:'#052e0a',
            inverted:'#ffffff',
          },
          background: {
            muted:   '#f9fafb',
            subtle:  '#f3f4f6',
            DEFAULT: '#ffffff',
            emphasis:'#374151',
          },
          border:    { DEFAULT: '#e5e7eb' },
          ring:      { DEFAULT: '#e5e7eb' },
          content: {
            subtle:  '#9ca3af',
            DEFAULT: '#6b7280',
            emphasis:'#374151',
            strong:  '#111827',
            inverted:'#ffffff',
          },
        },
      },
      boxShadow: {
        'tremor-input':  '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'tremor-card':   '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'tremor-dropdown':'0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
      },
      borderRadius: {
        'tremor-small': '0.375rem',
        'tremor-default':'0.5rem',
        'tremor-full':  '9999px',
      },
      fontSize: {
        'tremor-label':  ['0.75rem', { lineHeight: '1rem' }],
        'tremor-default':['0.875rem', { lineHeight: '1.25rem' }],
        'tremor-title':  ['1.125rem', { lineHeight: '1.75rem' }],
        'tremor-metric': ['1.875rem', { lineHeight: '2.25rem' }],
      },
    },
  },
  safelist: [
    { pattern: /^(bg|text|border|ring|fill|stroke)-(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-(50|100|200|300|400|500|600|700|800|900|950)/ },
  ],
  plugins: [],
}
