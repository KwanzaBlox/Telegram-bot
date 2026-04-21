import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ========== НАСТРОЙКИ ==========
TOKEN = "8692515951:AAFoPto-22C9rilnMJHAif36bXvUDm08nP4"

ADMINS = [
    'annaapanfilova1',
    'PepeChilI',
    'CH4EBYRAHKA',
    'dmitriiiy_22'
]

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== БАЗА ДАННЫХ ==========
db = sqlite3.connect('users.db', check_same_thread=False)
cursor = db.cursor()

# Создаем таблицу пользователей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
db.commit()
logger.info("✅ База данных готова")

# ========== ФУНКЦИИ БАЗЫ ДАННЫХ ==========
def save_user(user_id: int, username: str, first_name: str):
    """Сохраняет или обновляет пользователя"""
    cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_seen)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_seen = CURRENT_TIMESTAMP
    ''', (user_id, username or '', first_name or ''))
    db.commit()

def is_admin(username: str) -> bool:
    """Проверяет, является ли пользователь админом"""
    if not username:
        return False
    return username.lower() in [a.lower() for a in ADMINS]

def get_total_users() -> int:
    """Общее количество пользователей"""
    cursor.execute('SELECT COUNT(*) FROM users')
    return cursor.fetchone()[0]

def get_today_users() -> int:
    """Пользователей за сегодня"""
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(last_seen) = DATE('now', 'localtime')
    ''')
    return cursor.fetchone()[0]

def get_week_users() -> int:
    """Пользователей за неделю"""
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-7 days')
    ''')
    return cursor.fetchone()[0]

def get_month_users() -> int:
    """Пользователей за месяц"""
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE last_seen >= datetime('now', 'localtime', '-30 days')
    ''')
    return cursor.fetchone()[0]

def get_recent_users(limit: int = 5) -> List[Tuple]:
    """Последние пользователи"""
    cursor.execute('''
        SELECT username, first_name, last_seen 
        FROM users 
        ORDER BY last_seen DESC 
        LIMIT ?
    ''', (limit,))
    return cursor.fetchall()

# ========== КЛАВИАТУРЫ ==========
def get_main_menu(is_admin_user: bool) -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [
            InlineKeyboardButton("👻 Дyxлec | Поиск по номеру 📱", 
                                 url="https://t.me/Vospominaniybazabot")
        ],
        [
            InlineKeyboardButton("🕵️‍♂️ Шepлok | Поиск по фото 👁", 
                                 url="https://t.me/Vospominaniy_baza_bot?start=_ref_eMe87xc6o_4SW6Ie8hn"),
            InlineKeyboardButton("🔐 RuVPN | Безопасный VPN 🌐", 
                                 url="https://t.me/ruvpn?start=partner_1860340689")
        ],
        [
            InlineKeyboardButton("📸 Инcтa Шnuoн | Просмотр сторис 👀", 
                                 url="https://instashpion.ru?p=9cd42aee57cb325637213b895e815200"),
            InlineKeyboardButton("👥 BK Шnuoн | Анализ профилей 🔍", 
                                 url="https://kogdavseti.ru/?p=0e11c1032d9ed026dcf04fdedad15355")
        ]
    ]
    
    if is_admin_user:
        keyboard.append([
            InlineKeyboardButton("👑 АДМИН-ПАНЕЛЬ 👑", callback_data="admin_panel")
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_panel")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Сохраняем пользователя
    save_user(user.id, user.username, user.first_name)
    
    # Формируем приветствие
    text = (
        f"🔍 <b>ВЫБЕРИТЕ НУЖНЫЙ СЕРВИС</b> 🔍\n\n"
        f"Привет, {user.first_name or 'друг'}! 👋\n\n"
        f"👻 <b>Дyxлec</b> - поиск по номеру\n"
        f"🕵️‍♂️ <b>Шepлok</b> - поиск по фото\n"
        f"🔐 <b>RuVPN</b> - безопасный VPN\n"
        f"📸 <b>Инcтa Шnuoн</b> - Instagram\n"
        f"👥 <b>BK Шnuoн</b> - ВКонтакте\n\n"
        f"👇 <b>Нажми на кнопку:</b>"
    )
    
    await update.message.reply_text(
        text=text,
        reply_markup=get_main_menu(is_admin(user.username)),
        parse_mode=ParseMode.HTML
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user = update.effective_user
    text = "📚 /start - Главное меню\n/help - Помощь"
    await update.message.reply_text(
        text=text,
        reply_markup=get_main_menu(is_admin(user.username)),
        parse_mode=ParseMode.HTML
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    data = query.data
    
    if data == "admin_panel":
        # Проверяем админа
        if not is_admin(user.username):
            await query.answer("⛔ Только для админов", show_alert=True)
            return
        
        # Получаем статистику
        total = get_total_users()
        today = get_today_users()
        week = get_week_users()
        month = get_month_users()
        recent = get_recent_users(5)
        
        # Текущее время
        now = datetime.now().strftime("%d.%m %H:%M")
        
        text = f"👑 <b>АДМИН-ПАНЕЛЬ</b> (МСК {now})\n\n"
        text += f"📊 <b>СТАТИСТИКА:</b>\n"
        text += f"• Всего пользователей: <b>{total}</b>\n"
        text += f"• За сегодня: <b>{today}</b>\n"
        text += f"• За неделю: <b>{week}</b>\n"
        text += f"• За месяц: <b>{month}</b>\n\n"
        
        text += f"🕐 <b>Последние 5 пользователей (МСК):</b>\n"
        if not recent:
            text += "   Пока нет пользователей\n"
        else:
            for i, (username, first_name, last_seen) in enumerate(recent, 1):
                name = first_name or "Без имени"
                uname = f"@{username}" if username else "нет username"
                try:
                    date = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S").strftime("%d.%m %H:%M")
                except:
                    date = last_seen
                text += f"{i}. {name} ({uname})\n   🕐 {date}\n"
        
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
        except:
            await query.message.reply_text(
                text=text,
                reply_markup=get_admin_keyboard(),
                parse_mode=ParseMode.HTML
            )
    
    elif data == "back":
        try:
            await query.delete_message()
            user_obj = update.effective_user
            await query.message.reply_text(
                text="🔍 Главное меню:",
                reply_markup=get_main_menu(is_admin(user.username)),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Ошибка при возврате: {e}")

# ========== ЗАПУСК ==========
def main():
    print("🤖 БОТ ЗАПУСКАЕТСЯ...")
    print(f"👑 Админы: {', '.join(ADMINS)}")
    print("🕐 Время: Московское (МСК)")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()