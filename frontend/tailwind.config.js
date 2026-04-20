/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0a0a0a',
          secondary: '#111111',
          panel: '#1e1e1e',
          hover: '#2a2a2a',
        },
        accent: {
          green: '#00ff88',
          amber: '#ffaa00',
          red: '#ff4444',
        },
        border: {
          subtle: '#333333',
        },
      },
    },
  },
  plugins: [],
}
