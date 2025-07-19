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
    await update.message.reply_text(f"🔍 Статистика:\n\n- Ожидают модерации: {pending_res.count}\n- Активных событий: {active_res.count}")

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
        
        # Редактируем подпись или текст в зависимости от типа сообщения
        text_for_reason = "✍️ Напишите причину отклонения одним сообщением."
        if is_photo_message:
            await query.edit_message_caption(caption=text_for_reason, reply_markup=None)
        else:
            await query.edit_message_text(text=text_for_reason, reply_markup=None)
            
        return WAITING_REASON


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