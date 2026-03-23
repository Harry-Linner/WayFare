import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

export default defineConfig({
  output: 'server',
  adapter: node({
    mode: 'standalone',
  }),
  server: {
    host: '127.0.0.1',
    port: 4321,
    strictPort: true,
  },
  integrations: [tailwind()],
});
