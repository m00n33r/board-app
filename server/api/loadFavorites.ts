// server/api/load-favorites.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
  const { user_id } = await readBody(event)
  const config = useRuntimeConfig()
  const supabase = createClient(config.supabaseUrl, config.supabaseKey)

  const { data, error } = await supabase
    .from('user_favorites')
    .select(`
      event_id,
      events (
        event_name,
        event_date,
        event_time,
        event_location,
        event_host,
        event_banner
      )
    `)
    .eq('user_id', user_id)

  if (error) {
    console.error('Ошибка при загрузке избранного:', error.message);
    setResponseStatus(event, 500);
    return { error: error.message };
  }

  // Преобразуем данные, чтобы убрать вложенность
  const favorites = data.map(fav => ({
    event_id: fav.event_id,
    ...(fav.events || {}) // Используем spread и защиту от null
  }));

  // Возвращаем данные под правильным ключом 'data'
  return { data: favorites };
})