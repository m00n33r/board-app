// server/api/createEvent.ts
import { createClient } from '@supabase/supabase-js'


const FORBIDDEN_KEYWORDS = ["курение", "кальян", "вейп", "наркотики", "алкоголь"];
const FORBIDDEN_PLACES = ["бар", "клуб", "паб", "рюмочная", "кальянная"];
const FORBIDDEN_LINKS = ["instagram.com", "facebook.com", "twitter.com"];

const containsForbiddenWords = (text: string, wordList: string[]): boolean => {
    const lowerCaseText = text.toLowerCase();
    return wordList.some(word => lowerCaseText.includes(word));
};

export default defineEventHandler(async (event) => {

    const config = useRuntimeConfig()
    const supabase = createClient(config.supabaseUrl, config.supabaseKey)

    const body = await readBody(event)

    // Проверка на запрещенные слова
    const eventText = `${body.event_name} ${body.event_description}`.toLowerCase();
    const locationText = body.event_location.toLowerCase();

    if (containsForbiddenWords(eventText, FORBIDDEN_KEYWORDS) || containsForbiddenWords(locationText, FORBIDDEN_PLACES)) {
        setResponseStatus(event, 400);
        return { error: 'Мероприятие содержит недопустимые слова или относится к запрещенному типу заведения.' };
    }

    const { error } = await supabase.from('events_raw').insert([
        {
            user_id: body.user_id,
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

    if (error) {
        return { error: error.message }
    }

    return { success: true }
})