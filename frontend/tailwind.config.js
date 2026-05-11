/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
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
      },
    },
  },
  plugins: [],
}
