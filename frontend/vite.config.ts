import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isLabs = mode === 'labs'

  return {
    plugins: [
      vue(),
      vueDevTools(),
      tailwindcss(),
      // Custom middleware plugin to redirect / to /labs.html in dev labs mode
      {
        name: 'html-redirect',
        configureServer(server) {
          if (isLabs) {
            server.middlewares.use((req, res, next) => {
              const url = req.url ? req.url.split('?')[0] : ''
              if (
                !url.includes('.') &&
                !url.startsWith('/@') &&
                !url.startsWith('/src/') &&
                !url.startsWith('/node_modules/')
              ) {
                req.url = '/labs.html'
              }
              next()
            })
          }
        }
      }
    ],
    server: {
      port: isLabs ? 5000 : 5001,
    },
    build: {
      rollupOptions: {
        input: (isLabs
          ? { labs: path.resolve(__dirname, 'labs.html') }
          : { main: path.resolve(__dirname, 'index.html') }) as Record<string, string>
      }
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  }
})