import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/

export default defineConfig({
  plugins: [react()],
    server: {
    proxy: {
      // string shorthand: http://localhost:5000/asm -> http://localhost:5000/asm
      '/asm': 'http://localhost:5000',
    },
  },
})