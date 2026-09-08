/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        paimana: {
          navy: '#0B192C',
          slate: '#1E293B',
          blue: '#1D4ED8',
          'blue-light': '#3B82F6',
          'blue-subtle': '#EFF6FF',
          border: '#E2E8F0',
        },
        tier: {
          1: {
            bg: '#FEF2F2',
            text: '#B91C1C',
            border: '#FECACA',
            badge: '#DC2626',
          },
          2: {
            bg: '#FFFBEB',
            text: '#B45309',
            border: '#FDE68A',
            badge: '#D97706',
          },
          3: {
            bg: '#FEFCE8',
            text: '#A16207',
            border: '#FEF08A',
            badge: '#CA8A04',
          },
          4: {
            bg: '#F8FAFC',
            text: '#475569',
            border: '#E2E8F0',
            badge: '#64748B',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
