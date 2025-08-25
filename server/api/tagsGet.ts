import { createClient } from '@supabase/supabase-js';

export default defineEventHandler(async (event) => {
  try {
    const config = useRuntimeConfig();
    const supabase = createClient(config.supabaseUrl as string, config.supabaseKey as string);

    // Загружаем теги из таблицы tags
    const { data: tags, error } = await supabase
      .from('tags')
      .select('tag_name, tag_color')
      .order('tag_name');

    if (error) {
      console.error('Ошибка при загрузке тегов:', error);
      throw createError({
        statusCode: 500,
        statusMessage: 'Ошибка при загрузке тегов из БД'
      });
    }

    // console.log('Загружено тегов:', tags?.length || 0);
    return tags || [];

  } catch (error) {
    console.error('Ошибка в API tagsGet:', error);
    throw createError({
      statusCode: 500,
      statusMessage: 'Внутренняя ошибка сервера'
    });
  }
});
