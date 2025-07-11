import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const supabase = createClient(config.supabaseUrl as string, config.supabaseKey as string)

  const { user_id } = await readBody(event);

  if (!user_id) {
    setResponseStatus(event, 400);
    return { error: 'user_id is required' };
  }

  const { data, error } = await supabase.from('events_raw').select('*, event_moderation_step').eq('user_id', user_id);

  if (error) return { error: error.message };
  return { data };
});