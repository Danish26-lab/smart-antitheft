/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0f172a',
          card: '#1e293b',
          elevated: '#334155',
          border: '#475569',
          muted: '#94a3b8',
        },
      },
      backgroundImage: {
        'gradient-accent': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
        'gradient-dark': 'linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-lg': '0 0 40px rgba(99, 102, 241, 0.2)',
      },
    },
  },
  plugins: [],
}

