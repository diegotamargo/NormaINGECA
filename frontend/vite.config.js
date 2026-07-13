import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// NormaINGECA frontend (React + Vite).
//
// The browser only ever talks to our own FastAPI server (never to an LLM
// provider directly), so every request goes to a relative "/api/..." path.
//
//   - In dev, Vite proxies "/api" to the FastAPI backend below.
//   - In production the backend serves the built SPA via StaticFiles at "/",
//     so the same relative "/api" paths resolve to the same origin with no
//     proxy and no CORS involved.
//
// The backend's default port is 58734 (see backend/app/config.py — chosen on
// purpose because 8000/8080/3000 collide with other local dev tools). Override
// with VITE_API_TARGET in a .env file if you run the backend elsewhere.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:58734'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: false,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
