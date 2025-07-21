// /server/api/recalculateFavorites.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)
    
    const { event_id } = await readBody(event);

    if (!event_id) {
        setResponseStatus(event, 400)
        return { error: 'Необходим event_id для пересчета' }
    }

    // 1. Считаем, сколько всего записей в user_favorites для этого события
    const { count, error: countError } = await supabase
        .from('user_favorites')
        .select('*', { count: 'exact', head: true })
        .eq('event_id', event_id);

    if (countError) {
        setResponseStatus(event, 500);
        return { error: `Ошибка подсчета: ${countError.message}` };
    }

    // 2. Обновляем поле favorites_count в таблице events
    const { error: updateError } = await supabase
        .from('events')
        .update({ favorites_count: String(count || 0) }) // Обновляем на новое значение
        .eq('event_id', event_id);

    if (updateError) {
        setResponseStatus(event, 500);
        return { error: `Ошибка обновления счетчика: ${updateError.message}` };
    }

    return { success: true, new_count: count };
})