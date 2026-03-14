/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,sss,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        // 基础品牌色 [cite: 4, 8, 17, 20]
        brand: {
          blue: '#A3D1CC',      // 主色调：Blue [cite: 4]
          surface: '#E1FCF6',   // 次级背景：Light blue [cite: 8]
          cream: '#F7F7EA',     // 页面大背景：Cream [cite: 17]
          sand: '#FAEDCD',      // 卡片/交互色：Light orange [cite: 20]
        },
        // 优先级颜色映射，用于气泡点 (Annotations) [cite: 24, 27]
        priority: {
          critical: '#E9A254',  // 核心考点：Deep Orange [cite: 27]
          important: '#EEBF79', // 重要补充：Orange [cite: 24]
          normal: '#A3D1CC',    // 普通注释（复用主蓝） [cite: 4]
          low: '#D1D1C7',       // 细节说明（基于 Cream 调暗的灰色）
        }
      },
      // 针对学习应用优化的字体间距或阴影
      boxShadow: {
        'bubble': '0 4px 14px 0 rgba(0, 0, 0, 0.1)', // 气泡浮动感
      }
    },
  },
  plugins: [],
}