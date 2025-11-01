import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Adjust proxy if your backend runs on a different host/port.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
