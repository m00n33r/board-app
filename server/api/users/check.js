import { createClient } from '@supabase/supabase-js'

export default defineEventHandler(async (event) => {
    // Чтение данных из тела запроса
    const body = await readBody(event);
    const userId = parseInt(body.userId, 10);
    const userFirstName = body.userFirstName;
    const userLastName = body.userLastName;
    const userName = body.userName;
    const createdDate = body.userCreatedDate;

    if (!userId) {
        return {
            statusCode: 400,
            message: 'user_id отсутствует',
        };
    }

    // Проверка, существует ли пользователь в базе данных
    const { data: existingUser, error: fetchError } = await supabase
        .from('users')
        .select('*')
        .eq('user_id', userId)
        .single();

    if (fetchError && fetchError.code !== 'PGRST116') {
        return {
            statusCode: 500,
            message: 'Ошибка проверки пользователя',
            error: fetchError.message,
        };
    }

    if (existingUser) {
        return {
            statusCode: 200,
            message: 'Пользователь уже существует',
            user: existingUser,
        };
    }


    // Добавление нового пользователя
    const { data: newUser, error: insertError } = await supabase
        .from('users')
        .insert([{
                            user_id: userId,
                            user_first_name:  userFirstName,
                            user_last_name: userLastName,
                            user_name: userName,
                            user_created_date: createdDate
                        }])
        .single();

    if (insertError) {
        return {
            statusCode: 500,
            message: 'Ошибка добавления пользователя',
            error: insertError.message,
        };
    }

    return {
        statusCode: 201,
        message: 'Пользователь добавлен',
        user: newUser,
    };
});
