# bot.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)
from supabase import create_client, Client
import re

# --- Настройка ---
load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- Инициализация клиентов ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- Состояния для диалога ---
WAITING_REASON = 0

# --- Причины отклонения ---
REJECTION_REASONS = {
    'content_quality': {
        'name': '📝 Качество контента',
        'reasons': [
            ('Нецензурная лексика', 'Нецензурная лексика в названии или описании'),
            ('Неподходящая фотография', 'Фотография не соответствует содержанию или правилам'),
            ('Низкое качество изображения', 'Изображение слишком размытое или некачественное'),
            ('Неинформативное описание', 'Описание слишком краткое или неинформативное')
        ]
    },
    'event_info': {
        'name': 'ℹ️ Информация о событии',
        'reasons': [
            ('Неполная информация', 'Отсутствует важная информация о событии'),
            ('Неточные данные', 'Данные о времени, месте или цене неточны'),
            ('Отсутствует важная информация', 'Не указано время, место или контакты'),
            ('Противоречивые сведения', 'Информация противоречит сама себе')
        ]
    },
    'technical': {
        'name': '🔧 Технические проблемы',
        'reasons': [
            ('Нерабочие ссылки', 'Ссылки на мероприятие не работают'),
            ('Недоступные изображения', 'Изображения не загружаются'),
            ('Ошибки в формате данных', 'Неправильный формат даты, времени или цены'),
            ('Дублирование контента', 'Событие уже существует на платформе')
        ]
    },
    'policy': {
        'name': '📋 Правила и политика',
        'reasons': [
            ('Нарушение правил платформы', 'Событие не соответствует правилам платформы'),
            ('Неподходящий контент', 'Контент не подходит для аудитории'),
            ('Спам или реклама', 'Событие является рекламой или спамом'),
            ('Нарушение авторских прав', 'Использован контент без разрешения')
        ]
    }
}

def is_image_url(url: str) -> bool:
    """
    Проверяет, заканчивается ли url на типичное расширение картинки.
    """
    return bool(url and re.match(r'^https?:\/\/.*\.(jpg|jpeg|png|gif|webp|bmp|tiff)(\?.*)?$', url, re.IGNORECASE))

# --- Хелпер для отправки следующего мероприятия ---
async def send_next_event_for_moderation(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Находит и отправляет следующее мероприятие на модерацию, если режим включен."""

    # Удаляем предыдущее сообщение с кнопками, если есть
    last_msg_id = context.user_data.pop('last_mod_msg_id', None)
    if last_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=last_msg_id)
        except Exception as e:
            logging.warning(f"Не удалось удалить старое сообщение модерации: {e}")

    if not context.user_data.get('in_moderation_mode', False):
        return

    res = supabase.from_("events_raw").select("*").eq("event_moderation_step", "На модерации").limit(1).single().execute()

    if not res.data:
        await context.bot.send_message(chat_id, "🎉 Новых мероприятий для модерации нет! Режим модерации выключен.")
        context.user_data['in_moderation_mode'] = False
        return

    event = res.data
    caption = (
        f"<b>{event['event_name']}</b>\n\n"
        f"<b>📍 Адрес:</b> {event['event_location']}\n"
        f"<b>📝 Описание:</b> {event.get('event_description', 'Нет')}\n"
        f"<b>🔗 Ссылка:</b> {event.get('event_link', 'Нет')}"
    )
    keyboard = [[
        InlineKeyboardButton("✅ Принять", callback_data=f"approve_{event['id']}"),
        InlineKeyboardButton("🚫 Отклонить", callback_data=f"reject_{event['id']}"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    banner_url = event.get('event_banner')
    try:
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=banner_url,
            caption=caption,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    except Exception as e:
        # Если не удалось отправить фото — отправляем текст
        logging.error(f"Ошибка отправки баннера как фото: {e} [{banner_url}]")
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode='HTML',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    context.user_data['last_mod_msg_id'] = msg.message_id


# --- Основные функции бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение и главную клавиатуру."""
    keyboard = [["📊 Статистика", "▶️ Модерация"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать в бот модерации!", reply_markup=reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику по мероприятиям."""
    pending_res = supabase.from_("events_raw").select("id", count='exact').eq("event_moderation_step", "На модерации").execute()
    active_res = supabase.from_("events").select("event_id", count='exact').execute()
    
    # Получаем статистику по причинам отклонения
    rejection_stats = await get_rejection_reasons_stats()
    
    stats_text = f"🔍 Статистика:\n\n- Ожидают модерации: {pending_res.count}\n- Активных событий: {active_res.count}"
    
    if rejection_stats:
        stats_text += "\n\n📊 Топ причин отклонения:\n"
        for i, (reason, count) in enumerate(rejection_stats[:5], 1):
            stats_text += f"{i}. {reason}: {count}\n"
    
    await update.message.reply_text(stats_text)

async def toggle_moderation_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включает или выключает режим непрерывной модерации."""
    # Проверяем текущее состояние, по умолчанию — выключено
    is_in_mode = context.user_data.get('in_moderation_mode', False)

    if not is_in_mode:
        # Включаем режим
        context.user_data['in_moderation_mode'] = True
        await update.message.reply_text("Вы вошли в режим модерации. Чтобы выйти, нажмите кнопку еще раз.")
        await send_next_event_for_moderation(update.message.chat_id, context)
    else:
        # Выключаем режим
        context.user_data['in_moderation_mode'] = False
        await update.message.reply_text("Вы вышли из режима модерации.")

# --- Обработчики инлайн-кнопок и диалога ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Проверяем, является ли это выбором категории
    if query.data.startswith('category_'):
        # Формат: category_eventId_categoryKey
        parts = query.data.split('_')
        event_id = int(parts[1])
        category_key = parts[2]
        
        # Показываем причины для выбранной категории
        await show_reasons_for_category(query, event_id, category_key, context)
        return
    
    # Проверяем, является ли это выбором конкретной причины
    elif query.data.startswith('reason_'):
        # Формат: reason_eventId_categoryKey_reasonIndex
        parts = query.data.split('_')
        event_id = int(parts[1])
        category_key = parts[2]
        reason_index = int(parts[3])
        
        # Получаем причину и отклоняем событие
        reason = REJECTION_REASONS[category_key]['reasons'][reason_index][0]
        await reject_event_with_reason(query, event_id, reason, context)
        return
    
    # Проверяем, является ли это запросом на ручной ввод причины
    elif query.data.startswith('manual_reason_'):
        # Формат: manual_reason_eventId
        event_id = int(query.data.split('_')[2])
        context.user_data['event_to_reject'] = event_id
        
        # Запрашиваем ручной ввод причины
        text_for_reason = "✍️ Напишите причину отклонения одним сообщением:"
        is_photo_message = bool(query.message.photo)
        
        if is_photo_message:
            await query.edit_message_caption(caption=text_for_reason, reply_markup=None)
        else:
            await query.edit_message_text(text=text_for_reason, reply_markup=None)
        
        return WAITING_REASON
    
    # Обработка стандартных действий approve/reject
    action, event_id_str = query.data.split('_')
    event_id = int(event_id_str)

    # Определяем, какой метод редактирования использовать
    is_photo_message = bool(query.message.photo)

    if action == "approve":
        try:
            res = supabase.rpc('approve_event', {'raw_event_id': event_id}).execute()
            if res.data and res.data[0].get('organizer_user_id'):
                organizer_id = res.data[0]['organizer_user_id']
                await context.bot.send_message(organizer_id, '🎉 Ваше мероприятие одобрено и опубликовано!')
            
            # Редактируем подпись или текст в зависимости от типа сообщения
            if is_photo_message:
                await query.edit_message_caption(caption="✅ Мероприятие одобрено!", reply_markup=None)
            else:
                await query.edit_message_text(text="✅ Мероприятие одобрено!", reply_markup=None)

        except Exception as e:
            logging.error(f"Ошибка при одобрении события {event_id}: {e}")
            error_text = "❌ Произошла ошибка при одобрении."
            if is_photo_message:
                await query.edit_message_caption(caption=error_text, reply_markup=None)
            else:
                await query.edit_message_text(text=error_text, reply_markup=None)
        
        # Сразу отправляем следующее
        await send_next_event_for_moderation(query.message.chat_id, context)
        

    elif action == "reject":
        context.user_data['event_to_reject'] = event_id
        
        # Создаем клавиатуру с причинами отклонения
        keyboard = []
        
        # Добавляем категории причин
        for category_key, category_data in REJECTION_REASONS.items():
            keyboard.append([InlineKeyboardButton(
                category_data['name'], 
                callback_data=f"category_{event_id}_{category_key}"
            )])
        
        # Добавляем кнопку для ручного ввода причины
        keyboard.append([InlineKeyboardButton(
            "✍️ Другая причина", 
            callback_data=f"manual_reason_{event_id}"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Редактируем подпись или текст в зависимости от типа сообщения
        text_for_reason = "🚫 Выберите причину отклонения:"
        if is_photo_message:
            await query.edit_message_caption(caption=text_for_reason, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=text_for_reason, reply_markup=reply_markup)
            
        return WAITING_REASON

# --- Функции для работы с причинами отклонения ---
async def show_reasons_for_category(query, event_id: int, category_key: str, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список причин для выбранной категории."""
    category_data = REJECTION_REASONS[category_key]
    
    # Создаем клавиатуру с причинами
    keyboard = []
    for i, (reason_name, reason_desc) in enumerate(category_data['reasons']):
        keyboard.append([InlineKeyboardButton(
            reason_name, 
            callback_data=f"reason_{event_id}_{category_key}_{i}"
        )])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton(
        "⬅️ Назад к категориям", 
        callback_data=f"reject_{event_id}"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Обновляем сообщение
    text = f"🚫 {category_data['name']}\n\nВыберите конкретную причину:"
    is_photo_message = bool(query.message.photo)
    
    if is_photo_message:
        await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    else:
        await query.edit_message_text(text=text, reply_markup=reply_markup)

async def reject_event_with_reason(query, event_id: int, reason: str, context: ContextTypes.DEFAULT_TYPE):
    """Отклоняет событие с указанной причиной."""
    try:
        res = supabase.rpc('reject_event', {'raw_event_id': event_id, 'reason': reason}).execute()
        
        # Уведомляем организатора
        if res.data and res.data[0].get('organizer_user_id'):
            await context.bot.send_message(
                res.data[0]['organizer_user_id'], 
                f'К сожалению, ваше мероприятие отклонено.\nПричина: "{reason}"'
            )
        
        # Обновляем сообщение
        text = f"🚫 Мероприятие отклонено.\nПричина: {reason}\nОрганизатор уведомлен."
        is_photo_message = bool(query.message.photo)
        
        if is_photo_message:
            await query.edit_message_caption(caption=text, reply_markup=None)
        else:
            await query.edit_message_text(text=text, reply_markup=None)
            
    except Exception as e:
        logging.error(f"Ошибка при отклонении события {event_id}: {e}")
        error_text = f"❌ Произошла ошибка при отклонении: {e}"
        is_photo_message = bool(query.message.photo)
        
        if is_photo_message:
            await query.edit_message_caption(caption=error_text, reply_markup=None)
        else:
            await query.edit_message_text(text=error_text, reply_markup=None)
    
    # Отправляем следующее событие на модерацию
    await send_next_event_for_moderation(query.message.chat_id, context)


async def get_rejection_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text
    event_id = context.user_data.pop('event_to_reject', None)
    if not event_id: return ConversationHandler.END

    try:
        res = supabase.rpc('reject_event', {'raw_event_id': event_id, 'reason': reason}).execute()
        if res.data and res.data[0].get('organizer_user_id'):
            await context.bot.send_message(res.data[0]['organizer_user_id'], f'К сожалению, ваше мероприятие отклонено.\nПричина: "{reason}"')
        await update.message.reply_text("🚫 Мероприятие отклонено. Организатор уведомлен.")
    except Exception as e:
        await update.message.reply_text(e)
        
    await send_next_event_for_moderation(update.message.chat_id, context)
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Действие отменено. Вы все еще в режиме модерации.")
    return ConversationHandler.END

async def get_rejection_reasons_stats():
    """Получает статистику по причинам отклонения."""
    try:
        # Получаем все отклоненные события с причинами
        res = supabase.from_("events_raw").select("rejection_reason").eq("event_moderation_step", "Отклонено").execute()
        
        if not res.data:
            return []
        
        # Подсчитываем частоту каждой причины
        reason_counts = {}
        for event in res.data:
            reason = event.get('rejection_reason', 'Не указана')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Сортируем по частоте
        sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_reasons
        
    except Exception as e:
        logging.error(f"Ошибка при получении статистики отклонений: {e}")
        return []

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    rejection_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern='^reject_')],
        states={
            WAITING_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rejection_reason)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conversation)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex('^📊 Статистика$'), show_stats))
    # Единый обработчик для кнопки-переключателя
    application.add_handler(MessageHandler(filters.Regex('^▶️ Модерация$'), toggle_moderation_mode))
    application.add_handler(CallbackQueryHandler(button_callback, pattern='^approve_'))
    application.add_handler(rejection_conversation)

    application.run_polling()

if __name__ == "__main__":
    main()