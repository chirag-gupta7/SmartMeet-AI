/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81'
        },
        ink: {
          900: '#0b1020',
          800: '#111733',
          700: '#1a2142',
          600: '#252c52'
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 1px 2px rgba(16,24,40,0.04), 0 8px 24px -8px rgba(16,24,40,0.12)',
        glow: '0 10px 40px -12px rgba(99,102,241,0.55)',
        card: '0 2px 4px rgba(16,24,40,0.04), 0 12px 32px -12px rgba(16,24,40,0.16)',
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      keyframes: {
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0) translateX(0)' },
          '50%': { transform: 'translateY(-18px) translateX(10px)' },
        },
        'gradient-pan': {
          '0%,100%': { 'background-position': '0% 50%' },
          '50%': { 'background-position': '100% 50%' },
        },
        'ring-pulse': {
          '0%': { transform: 'scale(0.95)', opacity: '0.7' },
          '70%': { transform: 'scale(1.35)', opacity: '0' },
          '100%': { opacity: '0' },
        },
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.5s ease-out both',
        'fade-in': 'fade-in 0.4s ease-out both',
        float: 'float 9s ease-in-out infinite',
        'gradient-pan': 'gradient-pan 8s ease infinite',
        'ring-pulse': 'ring-pulse 1.6s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      backgroundImage: {
        'brand-mesh': 'radial-gradient(at 12% 18%, rgba(99,102,241,0.45) 0px, transparent 55%), radial-gradient(at 84% 12%, rgba(168,85,247,0.40) 0px, transparent 50%), radial-gradient(at 70% 80%, rgba(59,130,246,0.40) 0px, transparent 55%)',
        'brand-gradient': 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #6366f1 100%)',
        'sidebar-gradient': 'linear-gradient(180deg, #111733 0%, #1a2142 55%, #252c52 100%)',
      },
    }
  },
  plugins: []
};
