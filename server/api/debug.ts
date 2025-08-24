export default defineEventHandler(async (event) => {
  // Только для разработки
  if (process.env.NODE_ENV === 'production') {
    throw createError({
      statusCode: 404,
      statusMessage: 'Not Found'
    })
  }

  return {
    nodeEnv: process.env.NODE_ENV,
    supabaseUrl: process.env.SUPABASE_URL ? '✅ Установлен' : '❌ Отсутствует',
    supabaseKey: process.env.SUPABASE_KEY ? '✅ Установлен' : '❌ Отсутствует',
    supabaseServiceKey: process.env.SUPABASE_SERVICE_KEY ? '✅ Установлен' : '❌ Отсутствует',
    telegramAppUrl: process.env.NUXT_PUBLIC_TELEGRAM_APP_URL ? '✅ Установлен' : '❌ Отсутствует',
    telegramBotToken: process.env.TELEGRAM_BOT_TOKEN ? '✅ Установлен' : '❌ Отсутствует',
    host: process.env.HOST,
    port: process.env.PORT,
    timestamp: new Date().toISOString()
  }
})
