/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        panel: {
          DEFAULT: '#12182b',
          light: '#1a2138',
          border: '#26304f',
        },
        base: {
          DEFAULT: '#0a0e1a',
        },
        accent: {
          blue: '#4f8bf2',
          teal: '#3fb6c4',
          orange: '#e8a03f',
          red: '#e8664b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        panel: '0 0 0 1px rgba(79,139,242,0.06), 0 8px 24px rgba(0,0,0,0.35)',
      },
    },
  },
  plugins: [],
}
