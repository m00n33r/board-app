// server/api/load-card.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    const { eventId, direction, tagId } = await readBody(event)
    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)

    let query

    // Базовый запрос с фильтрацией по тегу
    const baseQuery = () => {
        let q = supabase
            .from('events')
            .select(`
                *,
                event_tags!inner(
                    tag_id
                )
            `)
        
        if (tagId) {
            q = q.eq('event_tags.tag_id', tagId)
        }
        
        return q
    }

    if (direction === 'current') {
        query = baseQuery().eq('event_id', eventId).limit(1)
    } else if (direction === 'next') {
        query = baseQuery()
            .order('event_id', { ascending: true })
            .gt('event_id', eventId || 0)
            .limit(1)
    } else {
        query = baseQuery()
            .order('event_id', { ascending: false })
            .lt('event_id', eventId ?? Number.MAX_SAFE_INTEGER)
            .limit(1)
    }

    const { data, error } = await query.single()

    if (!data && direction === 'next') {
        // Вернуть первую карточку с учетом тега
        const fallbackQuery = baseQuery()
            .order('event_id', { ascending: true })
            .limit(1)
        
        const { data: fallback } = await fallbackQuery.single()
        return fallback || null
    }

    if (!data && direction === 'prev') {
        // Вернуть последнюю карточку с учетом тега
        const fallbackQuery = baseQuery()
            .order('event_id', { ascending: false })
            .limit(1)
        
        const { data: fallback } = await fallbackQuery.single()
        return fallback || null
    }

    return data || null
})
