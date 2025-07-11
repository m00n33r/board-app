// server/api/create-event.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {

    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)

    const body = await readBody(event)

    const { error } = await supabase.from('events_raw').insert([
        {
            event_name: body.event_name,
            event_banner: body.event_banner,
            event_start_dttm: body.event_start_dttm,
            event_end_dttm: body.event_end_dttm,
            event_location: body.event_location,
            event_description: body.event_description,
            event_tag: body.event_tag,
            event_link: body.event_link,
            event_approval: body.event_approval,
            event_price_status: body.event_price_status,
            event_price: body.event_price,
            event_visibility: body.event_visibility,
            event_capacity: body.event_capacity,
            event_moderation_step: 'На модерации'
        }
    ])

    if (error) return { error: error.message }

    return { success: true }
})
