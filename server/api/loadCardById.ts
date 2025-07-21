// /server/api/loadCardById.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    const { id } = await readBody(event)
    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)

    // Запрашиваем все поля, включая favorites_count
    const { data, error } = await supabase
        .from('events')
        .select('*') // Просто и надежно
        .eq('event_id', id)
        .single()

    if (error) {
        setResponseStatus(event, 500);
        return { error: error.message }
    }
    
    // Добавляем защиту на случай, если events_stats будет использоваться где-то еще
    if (data && !data.events_stats) {
        data.events_stats = [{ uniq_users_likes: Number(data.favorites_count) || 0 }];
    }

    return { data }
})