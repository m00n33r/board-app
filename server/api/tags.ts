// server/api/tags.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)

    try {
        const { data, error } = await supabase
            .from('tags')
            .select('tag_id, tag_name, tag_color')
            .order('tag_name', { ascending: true })

        if (error) {
            console.error('Ошибка загрузки тегов:', error)
            return []
        }

        return data || []
    } catch (err) {
        console.error('Ошибка при загрузке тегов:', err)
        return []
    }
})