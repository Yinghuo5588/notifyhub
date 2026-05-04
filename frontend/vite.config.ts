import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:9800',
      '/hook': 'http://127.0.0.1:9800',
      '/static': 'http://127.0.0.1:9800',
    },
  },
  build: {
    outDir: '../app/static/frontend',
    emptyOutDir: true,
  },
})