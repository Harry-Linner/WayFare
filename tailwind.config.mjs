/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,sss,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"LXGW WenKai"', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['"LXGW WenKai"', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'monospace'],
      },
      colors: {
        brand: {
          blue: '#A3D1CC',
          surface: '#E1FCF6',
          cream: '#F7F7EA',
          sand: '#FAEDCD',
        },
        priority: {
          critical: '#E9A254',
          important: '#EEBF79',
          normal: '#A3D1CC',
          low: '#D1D1C7',
        },
      },
      boxShadow: {
        bubble: '0 4px 14px 0 rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
};
