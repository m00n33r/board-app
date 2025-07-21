// /server/api/toggleFavorite.ts
import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)
    
    const { user_id, event_id, action } = await readBody(event)

    if (!user_id || !event_id || !action) {
        setResponseStatus(event, 400)
        return { error: 'Отсутствует user_id, event_id или action' }
    }

    try {
        if (action === 'save') {
            // Вставляем или обновляем запись в избранном
            const { error: upsertError } = await supabase.from('user_favorites').upsert(
                { user_id: String(user_id), event_id: String(event_id) },
                { onConflict: 'user_id,event_id' }
            );

            if (upsertError) throw upsertError;

            // Вызываем нашу быструю SQL-функцию для увеличения счетчика
            const { error: rpcError } = await supabase.rpc('update_favorites_count', {
                event_id_text_param: event_id,
                increment_value: 1
            });
            if (rpcError) throw rpcError;

            return { success: true, newState: 'saved' }
        } 
        
        else if (action === 'unsave') {
            // Удаляем запись из избранного
            const { error: deleteError } = await supabase
                .from('user_favorites')
                .delete()
                .eq('user_id', String(user_id))
                .eq('event_id', String(event_id))

            if (deleteError) throw deleteError;

            // Вызываем нашу быструю SQL-функцию для уменьшения счетчика
            const { error: rpcError } = await supabase.rpc('update_favorites_count', {
                event_id_text_param: event_id,
                increment_value: -1
            });
            if (rpcError) throw rpcError;

            return { success: true, newState: 'none' }
        }

        else {
            setResponseStatus(event, 400);
            return { error: `Неизвестное действие: ${action}` }
        }

    } catch (e: any) {
        // Улучшенная обработка ошибок
        console.error(`[toggleFavorite] Ошибка при действии "${action}" для event_id ${event_id}:`, e.message);
        setResponseStatus(event, 500);
        return { error: `Ошибка базы данных: ${e.message}` }
    }
})