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
        // Deep Teal brand. Keep in sync with the CDN config in templates/base.html
        // and the --brand-* scale in static/css/tokens.css.
        // 300 and 950 were absent, so every `border-primary-300` and
        // `dark:hover:bg-primary-950` in the templates compiled to nothing.
        primary: {
          50: '#f0fdfa', 100: '#ccfbf1', 200: '#99f6e4', 300: '#5eead4', 400: '#2dd4bf',
          500: '#0d9488', 600: '#0f766e', 700: '#115e59', 800: '#134e4a', 900: '#0b3b38',
          950: '#042f2e',
        },
        accent: { 400: '#fb923c', 500: '#f97316', 600: '#ea580c' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};
