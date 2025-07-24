// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({

  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  plugins: [],
  ssr: false,

  app: {
    head: {
      script: [
        {
          src: 'https://telegram.org/js/telegram-web-app.js',
          defer: true,
        },
      ],

      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
        },
      ],

    },


  },

  modules: ['@nuxt/image'],

  runtimeConfig: {
    // Только на сервере
    supabaseUrl: process.env.SUPABASE_URL,
    supabaseKey: process.env.SUPABASE_KEY,

    // Переменные, доступные и на клиенте, и на сервере
    public: {
      telegramAppUrl: process.env.NUXT_PUBLIC_TELEGRAM_APP_URL || '',
    },
    vite: {
    server: {
      host: true, // 0.0.0.0 для внешнего доступа
      port: 3000,
    },
  },
  },
  
  vite: {
    server: {
      // host: true, // В Nuxt это обычно не требуется, но можно оставить
      allowedHosts: [
        '.ngrok-free.app',
        'toboard.org',
        'tunnel.toboard.org',
      ],
      hmr: {
        clientPort: 443,
      },
    },
  },

  });