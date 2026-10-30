import { fileURLToPath, URL } from 'node:url'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      // Em desenvolvimento o proxy evita CORS e mantém a URL do backend fora do bundle
      proxy: {
        '/api': {
          target: env.VITE_PROXY_BACKEND ?? 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      sourcemap: false,
    },
    test: {
      environment: 'jsdom',
      globals: false,
      include: ['src/**/*.spec.ts'],
    },
  }
})
