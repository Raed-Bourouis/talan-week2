/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        f360: {
          50: '#f0f4ff',
          100: '#dbe4ff',
          200: '#b4c6ff',
          300: '#8da8ff',
          400: '#668aff',
          500: '#3366ff',
          600: '#1a4dff',
          700: '#0039e6',
          800: '#002db3',
          900: '#002080',
          950: '#001452',
        },
      },
    },
  },
  plugins: [],
};
