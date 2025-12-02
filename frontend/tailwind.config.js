/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cisco-blue': '#049fd9',
        'cisco-dark': '#1a2f43',
        'cisco-light': '#6abf4b',
      }
    },
  },
  plugins: [],
}
