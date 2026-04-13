/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Primary
        primary: {
          DEFAULT: '#3b82f6',
          light: '#60a5fa',
          dark: '#2563eb',
        },
        accent: {
          DEFAULT: '#8b5cf6',
          light: '#a78bfa',
          dark: '#7c3aed',
        },
        // Dark theme backgrounds
        dark: {
          bg: '#080c14',
          card: '#0d1526',
          border: '#1e2d4a',
          hover: '#162038',
        },
        // Text
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#64748b',
        },
        // Status colors
        status: {
          lead: '#60a5fa',
          'lead-bg': 'rgba(59,130,246,0.15)',
          following: '#4ade80',
          'following-bg': 'rgba(34,197,94,0.15)',
          negotiating: '#fbbf24',
          'negotiating-bg': 'rgba(245,158,11,0.15)',
          won: '#a78bfa',
          'won-bg': 'rgba(139,92,246,0.15)',
          lost: '#f87171',
          'lost-bg': 'rgba(239,68,68,0.15)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
