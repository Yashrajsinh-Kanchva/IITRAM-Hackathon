/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f3f7f3",
          100: "#dfeadf",
          600: "#2f7d4a",
          700: "#25633b",
          900: "#133120"
        }
      }
    }
  },
  plugins: []
};
