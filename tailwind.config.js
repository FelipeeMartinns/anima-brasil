/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#7c3aed',
        secundaria: '#ec4899',
        escuro: '#1e1b4b',
      },
    },
  },
  plugins: [],
};