// /server/api/loadMyEvents.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const supabase = createClient(config.supabaseUrl as string, config.supabaseKey as string)

  const { user_id } = await readBody(event);

  if (!user_id) {
    setResponseStatus(event, 400);
    return { error: 'user_id is required' };
  }

  // 1. Сначала получаем user_name, так как он используется как event_host
  const { data: userData, error: userError } = await supabase
    .from('users')
    .select('user_name')
    .eq('user_id', user_id)
    .single();

  if (userError) {
    return { error: 'Не удалось найти пользователя' };
  }
  const userName = userData.user_name;

  // 2. Загружаем опубликованные события из основной таблицы events
  const { data: publishedEvents, error: publishedError } = await supabase
    .from('events')
    .select('*') // `event_id` здесь уже есть
    .eq('event_host', userName);

  if (publishedError) {
    return { error: `Ошибка загрузки опубликованных событий: ${publishedError.message}` };
  }
  
  // 3. Загружаем события "на модерации" из временной таблицы events_raw
  const { data: rawEvents, error: rawError } = await supabase
    .from('events_raw')
    .select('*')
    .eq('user_id', user_id)
    .in('event_moderation_step', ['На модерации', 'Отклонено']); // Захватим и отклоненные

  if (rawError) {
    return { error: `Ошибка загрузки событий на модерации: ${rawError.message}` };
  }

  // 4. Объединяем результаты
  const allMyEvents = [
    ...(publishedEvents || []),
    ...(rawEvents || [])
  ];

  return { data: allMyEvents };
});