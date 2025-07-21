// /server/api/loadCard.ts
import { createClient } from '@supabase/supabase-js';

export default defineEventHandler(async (event) => {
  const { eventId, direction } = await readBody(event);
  const config = useRuntimeConfig();
  const supabase = createClient(config.supabaseUrl as string, config.supabaseKey as string);

  let query;
  const currentEventId = eventId ? String(eventId) : null;

  // Теперь мы запрашиваем все поля (*) из таблицы events без лишних соединений
  const baseQuery = supabase.from('events').select('*');

  if (direction === 'current' && currentEventId) {
    query = baseQuery.eq('event_id', currentEventId).limit(1);
  } else if (direction === 'next') {
    let nextQuery = baseQuery.order('event_id', { ascending: true });
    if (currentEventId) {
      nextQuery = nextQuery.gt('event_id', currentEventId);
    }
    query = nextQuery.limit(1);
  } else { // direction === 'prev'
    let prevQuery = baseQuery.order('event_id', { ascending: false });
    if (currentEventId) {
        prevQuery = prevQuery.lt('event_id', currentEventId);
    }
    query = prevQuery.limit(1);
  }

  const { data, error } = await query.single();

  if (error && error.code !== 'PGRST116') {
    console.error('Supabase query error:', error.message);
    setResponseStatus(event, 500);
    return null;
  }

  // Логика зацикливания остается
  if (!data && direction === 'next') {
    const { data: fallback } = await supabase.from('events').select('*').order('event_id', { ascending: true }).limit(1).single();
    return fallback || null;
  }
  if (!data && direction === 'prev' && currentEventId) {
      const { data: fallback } = await supabase.from('events').select('*').order('event_id', { ascending: false }).limit(1).single();
      return fallback || null;
  }

  return data || null;
});