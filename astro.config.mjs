import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

export default defineConfig({
  output: 'server',            // 2. 开启服务端渲染模式
  adapter: node({              // 3. 配置适配器
    mode: 'standalone',
  }),
  integrations: [tailwind()]
});