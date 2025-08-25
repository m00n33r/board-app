# bot.py
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from simple_supabase import create_client
import re

# --- Настройка ---
load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- Инициализация клиентов ---
# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Проверяем наличие необходимых переменных окружения
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL не найден в переменных окружения")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY не найден в переменных окружения")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("✅ Supabase клиент успешно инициализирован")
except Exception as e:
    logging.error(f"❌ Ошибка инициализации Supabase клиента: {e}")
    raise

# --- Состояния для диалога ---
# Убираем неиспользуемые функции
# async def toggle_moderation_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
# async def get_rejection_reasons_stats():
# async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):

# --- Причины отклонения ---
# Список причин отклонения для модераторов
REJECTION_REASONS = [
    "Ненормативная лексика",
    "Некорректное описание", 
    "Неприличное фото",
    "Спам/реклама",
    "Несоответствие тематике",
    "Другое"
]

def is_image_url(url: str) -> bool:
    """
    Проверяет, заканчивается ли url на типичное расширение картинки.
    """
    return bool(url and re.match(r'^https?:\/\/.*\.(jpg|jpeg|png|gif|webp|bmp|tiff)(\?.*)?$', url, re.IGNORECASE))

# --- Хелпер для отправки следующего мероприятия ---
async def send_next_event_for_moderation(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет следующее событие на модерацию"""
    try:
        # Получаем следующее событие на модерации
        res = supabase.from_("events_raw").select("*").eq("event_moderation_step", "На модерации").limit(1).execute()
        
        # Логируем ответ для отладки
        logging.info(f"Supabase query response: {res}, data: {res.data if res else 'None'}, type: {type(res.data) if res else 'None'}")
        
        # Проверяем, что res.data существует, не None и не пустой
        if not res or not res.data or len(res.data) == 0:
            await context.bot.send_message(chat_id, "✅ Все события обработаны! Нет новых событий на модерации.")
            return
        
        event = res.data[0]
        
        # Формируем простой текст события без Markdown разметки
        event_description = event.get('event_description', 'Не указано')
        if event_description:
            description_text = str(event_description)[:200] + ('...' if len(str(event_description)) > 200 else '')
        else:
            description_text = 'Не указано'
            
        event_name = event.get('event_name', 'Не указано') or 'Не указано'
        event_location = event.get('event_location', 'Не указано') or 'Не указано'
        event_start_dttm = event.get('event_start_dttm', 'Не указано') or 'Не указано'
        event_price_status = event.get('event_price_status', 'Не указано') or 'Не указано'
        event_user_id = event.get('user_id', 'Не указано') or 'Не указано'
        event_link = event.get('event_link', 'Не указано') or 'Не указано'
        event_banner = event.get('event_banner', 'Не указано') or 'Не указано'
            
        event_text = f"""
📋 Событие на модерации

🏷️ Название: {event_name}
📍 Место: {event_location}
📅 Дата: {event_start_dttm}
💰 Цена: {event_price_status}
👤 Организатор: {event_user_id}
📝 Описание: {description_text}
🔗 Ссылка: {event_link}
🖼️ Баннер: {event_banner}
        """.strip()
        
        # Создаем клавиатуру с кнопками одобрения/отклонения
        keyboard = [
            [
                InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{event['id']}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{event['id']}")
            ],
            [InlineKeyboardButton("🚪 Выйти из модерации", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Проверяем, есть ли фото у события
        if event_banner and event_banner != 'Не указано' and is_image_url(event_banner):
            try:
                # Отправляем фото с подписью и кнопками
                await context.bot.send_photo(
                    chat_id,
                    photo=event_banner,
                    caption=event_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.warning(f"Не удалось отправить фото {event_banner}: {e}")
                # Если фото не отправилось, отправляем только текст
                await context.bot.send_message(
                    chat_id, 
                    event_text, 
                    reply_markup=reply_markup
                )
        else:
            # Если фото нет, отправляем только текст
            await context.bot.send_message(
                chat_id, 
                event_text, 
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logging.error(f"Ошибка при отправке события на модерацию: {e}")
        logging.error(f"Тип ошибки: {type(e)}")
        logging.error(f"Детали ошибки: {str(e)}")
        
        # Отправляем понятное сообщение пользователю
        error_message = "❌ Ошибка при загрузке события. Попробуйте позже."
        try:
            await context.bot.send_message(chat_id, error_message)
        except Exception as send_error:
            logging.error(f"Не удалось отправить сообщение об ошибке: {send_error}")


# --- Основные функции бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение и главную клавиатуру."""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("▶️ Модерация", callback_data="moderation")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать в бот модерации!", reply_markup=reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику модерации"""
    try:
        # Получаем общую статистику
        total_events = supabase.from_("events_raw").select("id").execute()
        pending_events = supabase.from_("events_raw").select("id").eq("event_moderation_step", "На модерации").execute()
        approved_events = supabase.from_("events_raw").select("id").eq("event_moderation_step", "Одобрено").execute()
        rejected_events = supabase.from_("events_raw").select("id").eq("event_moderation_step", "Отклонено").execute()
        
        # Подсчитываем количество с проверкой на None
        total_count = len(total_events.data) if total_events and total_events.data else 0
        pending_count = len(pending_events.data) if pending_events and pending_events.data else 0
        approved_count = len(approved_events.data) if approved_events and approved_events.data else 0
        rejected_count = len(rejected_events.data) if rejected_events and rejected_events.data else 0
        
        stats_text = f"""
📊 **Статистика модерации**

📝 Всего событий: {total_count}
⏳ На модерации: {pending_count}
✅ Одобрено: {approved_count}
❌ Отклонено: {rejected_count}
        """.strip()
        
        # Создаем клавиатуру для возврата
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем статистику
        query = update.callback_query
        await query.edit_message_text(text=stats_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Ошибка при получении статистики: {e}")
        error_text = "❌ Произошла ошибка при получении статистики. Попробуйте позже или обратитесь к администратору."
        
        query = update.callback_query
        await query.edit_message_text(text=error_text)

# Убираем неиспользуемые функции
# async def toggle_moderation_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
# async def get_rejection_reasons_stats():
# async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):

# --- Обработчики инлайн-кнопок и диалога ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "moderation":
        await send_next_event_for_moderation(query.message.chat_id, context)
    elif data == "stats":
        await show_stats(update, context)
    elif data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("▶️ Модерация", callback_data="moderation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Добро пожаловать в бот модерации!", reply_markup=reply_markup)
    elif data.startswith("approve_"):
        event_id = int(data.split("_")[1])
        await approve_event(update, context, event_id)
    elif data.startswith("reject_"):
        event_id = int(data.split("_")[1])
        await show_rejection_reasons(update, context, event_id)
    elif data.startswith("reason_"):
        # Формат: reason_123_Ненормативная лексика
        parts = data.split("_", 2)
        event_id = int(parts[1])
        reason = parts[2]
        await reject_event_with_reason(update, context, event_id, reason)
    elif data.startswith("manual_reason_"):
        event_id = int(data.split("_")[2])
        await ask_for_manual_reason(update, context, event_id)
    else:
        await query.edit_message_text("❌ Неизвестная команда")

# --- Функции для работы с причинами отклонения ---
async def show_rejection_reasons(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Показывает список причин отклонения для выбранного события"""
    query = update.callback_query
    
    # Создаем клавиатуру с причинами
    keyboard = []
    for reason in REJECTION_REASONS:
        keyboard.append([InlineKeyboardButton(
            reason, 
            callback_data=f"reason_{event_id}_{reason}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Обновляем сообщение
    text = "🚫 Выберите причину отклонения:"
    
    try:
        # Пробуем обновить подпись к фото
        await query.edit_message_caption(caption=text, reply_markup=reply_markup)
    except Exception:
        try:
            # Если не получилось обновить подпись, обновляем текст
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except Exception as e:
            logging.warning(f"Не удалось обновить сообщение: {e}")
            # Отправляем новое сообщение
            await query.message.reply_text(text, reply_markup=reply_markup)

async def ask_for_manual_reason(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Запрашивает ручной ввод причины отклонения"""
    query = update.callback_query
    
    # Сохраняем ID события для отклонения
    context.user_data['event_to_reject'] = event_id
    
    text = "✍️ Напишите причину отклонения одним сообщением:"
    
    try:
        # Пробуем обновить подпись к фото
        await query.edit_message_caption(caption=text, reply_markup=None)
    except Exception:
        try:
            # Если не получилось обновить подпись, обновляем текст
            await query.edit_message_text(text=text, reply_markup=None)
        except Exception as e:
            logging.warning(f"Не удалось обновить сообщение: {e}")
            # Отправляем новое сообщение
            await query.message.reply_text(text)
    
    # Устанавливаем состояние ожидания причины
    context.user_data['waiting_for_reason'] = True

async def reject_event_with_reason(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, reason: str):
    """Отклоняет событие с указанной причиной"""
    try:
        # Вызываем функцию отклонения в базе данных
        logging.info(f"Вызываем RPC reject_event с параметрами: raw_event_id={event_id}, reason={reason}")
        res = supabase.rpc('reject_event', {'raw_event_id': event_id, 'reason': reason}).execute()
        
        # Логируем полный ответ для отладки
        logging.info(f"Supabase reject_event полный ответ: {res}")
        logging.info(f"Supabase reject_event response: {res.data}, type: {type(res.data)}")
        logging.info(f"Supabase reject_event error: {getattr(res, 'error', 'Нет ошибки')}")
        
        # Проверяем на ошибки RPC
        if hasattr(res, 'error') and res.error:
            logging.error(f"RPC ошибка: {res.error}")
            error_text = f"❌ Ошибка базы данных: {res.error}"
            query = update.callback_query
            
            try:
                await query.edit_message_caption(caption=error_text, reply_markup=None)
            except Exception:
                try:
                    await query.edit_message_text(text=error_text, reply_markup=None)
                except Exception as e:
                    logging.warning(f"Не удалось обновить сообщение: {e}")
                    await query.message.reply_text(error_text)
            return
        
        # Безопасно извлекаем данные из ответа
        success = False
        organizer_id = None
        
        if res and res.data:
            if isinstance(res.data, dict):
                success = res.data.get('success', False)
                organizer_id = res.data.get('organizer_user_id')
            elif isinstance(res.data, list) and len(res.data) > 0:
                first_result = res.data[0]
                if isinstance(first_result, dict):
                    success = first_result.get('success', False)
                    organizer_id = first_result.get('organizer_user_id')
        
        if success:
            # Уведомляем организатора
            if organizer_id:
                try:
                    await context.bot.send_message(
                        organizer_id, 
                        f'🚫 Ваше мероприятие отклонено.\nПричина: {reason}'
                    )
                except Exception as e:
                    logging.warning(f"Не удалось уведомить организатора {organizer_id}: {e}")
            
            # Обновляем сообщение
            text = f"🚫 Мероприятие отклонено.\nПричина: {reason}"
            query = update.callback_query
            
            try:
                # Пробуем обновить подпись к фото
                await query.edit_message_caption(caption=text, reply_markup=None)
            except Exception:
                try:
                    # Если не получилось обновить подпись, обновляем текст
                    await query.edit_message_text(text=text, reply_markup=None)
                except Exception as e:
                    logging.warning(f"Не удалось обновить сообщение: {e}")
                    # Отправляем новое сообщение
                    await query.message.reply_text(text)
        else:
            error_text = "❌ Ошибка при отклонении события"
            query = update.callback_query
            
            try:
                await query.edit_message_caption(caption=error_text, reply_markup=None)
            except Exception:
                try:
                    await query.edit_message_text(text=error_text, reply_markup=None)
                except Exception as e:
                    logging.warning(f"Не удалось обновить сообщение: {e}")
                    await query.message.reply_text(error_text)
                    
    except Exception as e:
        logging.error(f"Ошибка при отклонении события {event_id}: {e}")
        error_text = f"❌ Произошла ошибка при отклонении: {e}"
        query = update.callback_query
        
        try:
            await query.edit_message_caption(caption=error_text, reply_markup=None)
        except Exception:
            try:
                await query.edit_message_text(text=error_text, reply_markup=None)
            except Exception as e2:
                logging.warning(f"Не удалось обновить сообщение: {e2}")
                await query.message.reply_text(error_text)
    
    # Отправляем следующее событие на модерацию
    query = update.callback_query
    await send_next_event_for_moderation(query.message.chat_id, context)

async def approve_event(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Одобряет событие"""
    try:
        # Вызываем функцию одобрения в базе данных
        logging.info(f"Вызываем RPC approve_event с параметрами: raw_event_id={event_id}")
        res = supabase.rpc('approve_event', {'raw_event_id': event_id}).execute()
        
        # Логируем полный ответ для отладки
        logging.info(f"Supabase approve_event полный ответ: {res}")
        logging.info(f"Supabase approve_event response: {res.data}, type: {type(res.data)}")
        logging.info(f"Supabase approve_event error: {getattr(res, 'error', 'Нет ошибки')}")
        
        # Проверяем на ошибки RPC
        if hasattr(res, 'error') and res.error:
            logging.error(f"RPC ошибка: {res.error}")
            error_text = f"❌ Ошибка базы данных: {res.error}"
            query = update.callback_query
            
            try:
                await query.edit_message_caption(caption=error_text, reply_markup=None)
            except Exception:
                try:
                    await query.edit_message_text(text=error_text, reply_markup=None)
                except Exception as e:
                    logging.warning(f"Не удалось обновить сообщение: {e}")
                    await query.message.reply_text(error_text)
            return
        
        # Безопасно извлекаем данные из ответа
        success = False
        organizer_id = None
        
        if res and res.data:
            if isinstance(res.data, dict):
                success = res.data.get('success', False)
                organizer_id = res.data.get('organizer_user_id')
            elif isinstance(res.data, list) and len(res.data) > 0:
                first_result = res.data[0]
                if isinstance(first_result, dict):
                    success = first_result.get('success', False)
                    organizer_id = first_result.get('organizer_user_id')
        
        if success:
            # Уведомляем организатора
            if organizer_id:
                try:
                    await context.bot.send_message(
                        organizer_id, 
                        '🎉 Ваше мероприятие одобрено и опубликовано!'
                    )
                except Exception as e:
                    logging.warning(f"Не удалось уведомить организатора {organizer_id}: {e}")
            
            # Обновляем сообщение
            text = "✅ Мероприятие одобрено!"
            query = update.callback_query
            
            try:
                # Пробуем обновить подпись к фото
                await query.edit_message_caption(caption=text, reply_markup=None)
            except Exception:
                try:
                    # Если не получилось обновить подпись, обновляем текст
                    await query.edit_message_text(text=text, reply_markup=None)
                except Exception as e:
                    logging.warning(f"Не удалось обновить сообщение: {e}")
                    # Отправляем новое сообщение
                    await query.message.reply_text(text)
        else:
            error_text = "❌ Ошибка при одобрении события"
            query = update.callback_query
            
            try:
                await query.edit_message_caption(caption=error_text, reply_markup=None)
            except Exception:
                try:
                    await query.edit_message_text(text=error_text, reply_markup=None)
                except Exception as e:
                    logging.warning(f"Не удалось обновить сообщение: {e}")
                    await query.message.reply_text(error_text)
                
    except Exception as e:
        logging.error(f"Ошибка при одобрении события {event_id}: {e}")
        error_text = f"❌ Произошла ошибка при одобрении: {e}"
        query = update.callback_query
        
        try:
            await query.edit_message_caption(caption=error_text, reply_markup=None)
        except Exception:
            try:
                await query.edit_message_text(text=error_text, reply_markup=None)
            except Exception as e2:
                logging.warning(f"Не удалось обновить сообщение: {e2}")
                await query.message.reply_text(error_text)
    
    # Отправляем следующее событие на модерацию
    query = update.callback_query
    await send_next_event_for_moderation(query.message.chat_id, context)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.message.from_user.id
    
    # Проверяем, ожидаем ли мы причину отклонения
    if context.user_data.get('waiting_for_reason') and context.user_data.get('event_to_reject'):
        event_id = context.user_data['event_to_reject']
        reason = update.message.text
        
        try:
            # Отклоняем событие с ручной причиной
            logging.info(f"Вызываем RPC reject_event с параметрами: raw_event_id={event_id}, reason={reason}")
            res = supabase.rpc('reject_event', {'raw_event_id': event_id, 'reason': reason}).execute()
            
            # Логируем полный ответ для отладки
            logging.info(f"Supabase reject_event полный ответ: {res}")
            logging.info(f"Supabase reject_event response: {res.data}, type: {type(res.data)}")
            logging.info(f"Supabase reject_event error: {getattr(res, 'error', 'Нет ошибки')}")
            
            # Проверяем на ошибки RPC
            if hasattr(res, 'error') and res.error:
                logging.error(f"RPC ошибка: {res.error}")
                await update.message.reply_text(f"❌ Ошибка базы данных: {res.error}")
                return
            
            # Безопасно извлекаем данные из ответа
            success = False
            organizer_id = None
            
            if res and res.data:
                if isinstance(res.data, dict):
                    success = res.data.get('success', False)
                    organizer_id = res.data.get('organizer_user_id')
                elif isinstance(res.data, list) and len(res.data) > 0:
                    first_result = res.data[0]
                    if isinstance(first_result, dict):
                        success = first_result.get('success', False)
                        organizer_id = first_result.get('organizer_user_id')
            
            if success:
                # Уведомляем организатора
                if organizer_id:
                    try:
                        await context.bot.send_message(
                            organizer_id, 
                            f'🚫 Ваше мероприятие отклонено.\nПричина: {reason}'
                        )
                    except Exception as e:
                        logging.warning(f"Не удалось уведомить организатора {organizer_id}: {e}")
                
                # Отправляем подтверждение модератору
                await update.message.reply_text(f"✅ Мероприятие отклонено с причиной: {reason}")
                
                # Очищаем данные
                context.user_data.pop('waiting_for_reason', None)
                context.user_data.pop('event_to_reject', None)
                
                # Отправляем следующее событие на модерацию
                await send_next_event_for_moderation(update.message.chat_id, context)
            else:
                await update.message.reply_text("❌ Ошибка при отклонении события. Попробуйте еще раз.")
                
        except Exception as e:
            logging.error(f"Ошибка при отклонении события {event_id}: {e}")
            await update.message.reply_text(f"❌ Произошла ошибка: {e}")
    else:
        # Обычное сообщение
        await update.message.reply_text("Используйте команду /start для начала работы с ботом.")

def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling(drop_pending_updates=True)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок бота"""
    logging.error(f"❌ Ошибка в боте: {context.error}")
    
    # Отправляем сообщение пользователю об ошибке
    if update and hasattr(update, 'effective_chat'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            )
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение об ошибке: {e}")

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # Проверяем переменные окружения перед запуском
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не найден!")
        exit(1)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL или SUPABASE_KEY не найдены!")
        exit(1)
    
    print("🔧 Проверка переменных окружения...")
    print(f"📡 SUPABASE_URL: {'✅' if SUPABASE_URL else '❌'}")
    print(f"🔑 SUPABASE_KEY: {'✅' if SUPABASE_KEY else '❌'}")
    print(f"🤖 TELEGRAM_TOKEN: {'✅' if TELEGRAM_TOKEN else '❌'}")
    
    # Запускаем бота
    exit(main())