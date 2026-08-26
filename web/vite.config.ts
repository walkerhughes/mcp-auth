import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', '')
  if (!env.STYTCH_PUBLIC_TOKEN) {
    throw new Error('STYTCH_PUBLIC_TOKEN is required in the repository-root .env')
  }

  return {
    envDir: '..',
    plugins: [react()],
    server: {
      host: 'localhost',
      port: 3000,
      strictPort: true,
    },
    define: {
      __STYTCH_PUBLIC_TOKEN__: JSON.stringify(env.STYTCH_PUBLIC_TOKEN),
    },
  }
})
