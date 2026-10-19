import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // GitHub Pages serves the site at teghsingh123.github.io/cap-sheet/
  base: '/cap-sheet/',
})
