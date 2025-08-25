// /server/api/loadEventsByDates.ts
import { createClient } from '@supabase/supabase-js';

export default defineEventHandler(async (event) => {
  const { dates } = await readBody(event);
  const config = useRuntimeConfig();
  const supabase = createClient(config.supabaseUrl as string, config.supabaseKey as string);

  if (!dates || dates.length === 0) {
    // Если даты не выбраны, возвращаем все события
    const { data, error } = await supabase
      .from('events')
      .select('*')
      .order('event_date', { ascending: true });

    if (error) {
      console.error('Supabase query error:', error.message);
      setResponseStatus(event, 500);
      return { error: error.message };
    }

    return { data: data || [] };
  }

  try {
    // Фильтруем события по выбранным датам
    const { data, error } = await supabase
      .from('events')
      .select('*')
      .in('event_date', dates)
      .order('event_date', { ascending: true });

    if (error) {
      console.error('Supabase query error:', error.message);
      setResponseStatus(event, 500);
      return { error: error.message };
    }

    return { data: data || [] };
  } catch (error) {
    console.error('Error filtering events by dates:', error);
    setResponseStatus(event, 500);
    return { error: 'Internal server error' };
  }
});
