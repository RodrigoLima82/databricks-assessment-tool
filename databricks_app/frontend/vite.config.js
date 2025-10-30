import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',  // Use relative paths for assets (works with proxies)
  server: {
    port: 3002,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8002',
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  }
})

