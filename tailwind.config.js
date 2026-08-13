/** TechZone TailwindCSS config (Module 12) — mirrors the CDN config in base.html. */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
    // Behaviour was extracted out of the templates into these files, and some of
    // it builds class strings at runtime (setView, updateCompareUI, …). Without
    // this glob those utilities are purged from the bundle and the styles break.
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Keep in sync with the CDN config in templates/base.html.
        // 300 and 950 were absent, so every `border-primary-300` and
        // `dark:hover:bg-primary-950` in the templates compiled to nothing.
        primary: {
          50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd', 400: '#60a5fa',
          500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8', 800: '#1e40af', 900: '#1e3a8a',
          950: '#172554',
        },
        accent: { 400: '#fb923c', 500: '#f97316', 600: '#ea580c' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};
