/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',       // All HTML templates
    './attendance/**/*.html',      // Your attendance folder templates
  ],
  theme: {
    extend: {},                    // Keep default Tailwind theme, extend if needed
  },
  plugins: [],                     // Add Tailwind plugins here if needed
};
