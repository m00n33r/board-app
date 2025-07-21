// server/api/isFavorite.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)
    const { user_id, event_id } = await readBody(event)

    if (!user_id || !event_id) {
        setResponseStatus(event, 400);
        return { isFavorite: false };
    }

    // Проверяем таблицу user_favorites, где хранятся только актуальные лайки
    const { data, error } = await supabase
        .from('user_favorites')
        .select('event_id')
        .eq('user_id', user_id)
        .eq('event_id', event_id)
        .limit(1)
        .single();
        
    // Возвращаем true, если запись найдена, иначе false
    return { isFavorite: !!data };
})