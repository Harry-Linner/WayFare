import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

const goBackendUrl =
  process.env.GO_BACKEND_URL ||
  process.env.API_URL ||
  process.env.PUBLIC_API_PROXY_TARGET ||
  'http://localhost:8080';

const publicApiUrl = process.env.PUBLIC_API_URL || '';

const proxyConfig = {
  '/api': {
    target: goBackendUrl,
    changeOrigin: true,
    secure: false,
  },
  '/health': {
    target: goBackendUrl,
    changeOrigin: true,
    secure: false,
  },
  '/uploads': {
    target: goBackendUrl,
    changeOrigin: true,
    secure: false,
  },
};

export default defineConfig({
  integrations: [tailwind()],
  server: {
    port: 3000,
    host: true
  },
  vite: {
    server: {
      proxy: proxyConfig
    },
    preview: {
      proxy: proxyConfig
    },
    define: {
      'import.meta.env.PUBLIC_API_URL': JSON.stringify(publicApiUrl)
    }
  }
});
