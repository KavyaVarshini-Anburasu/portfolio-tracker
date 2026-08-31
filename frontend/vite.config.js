import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Django's CORS_ALLOWED_ORIGINS only trusts 5173, so fail loudly instead
    // of silently moving to 5174 and breaking every request.
    port: 5173,
    strictPort: true,
  },
})
