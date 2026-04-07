"""
Telegram Bot with Subscription System + Report Services
Подписки: дни, недели, месяцы
Валюта: сносы (reports)
ВСЕ КНОПКИ РАБОТАЮТ
Поддержка языков: Українська, Русский, English
"""

import asyncio
import sqlite3
import random
import datetime
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import aiohttp
import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8796055769:AAG1DRlpWd7Zft4oGb0_A8309qJgM3UOf3M")
CRYPTO_PAY_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN", "563714:AAoNQWxKCzZLDkotn5jjJdl0QFwMCAtEbtD")
CRYPTO_PAY_TESTNET = False

ADMIN_IDS = [964442694]

# Пакеты подписок
SUBSCRIPTIONS = {
    "day": {
        "name": "Дневная подписка",
        "reports": 2,  # количество сносов в день
        "duration_days": 1,
        "price": 1.99,
        "emoji": "📅"
    },
    "week": {
        "name": "Недельная подписка", 
        "reports": 3,  # количество сносов в неделю
        "duration_days": 7,
        "price": 4.99,
        "emoji": "📆"
    },
    "month": {
        "name": "Месячная подписка",
        "reports": 5,  # количество сносов в месяц
        "duration_days": 30,
        "price": 9.99,
        "emoji": "🗓️"
    }
}

# Дополнительные услуги (пакеты сносов)
EXTRA_REPORTS = {
    "single": {
        "name": "1 снос",
        "reports": 1,
        "price": 2.00,
        "emoji": "🎯"
    },
    "five": {
        "name": "5 сносов",
        "reports": 5,
        "price": 10.00,
        "emoji": "🔥"
    }
}

# Тексты на разных языках
TEXTS = {
    "ru": {
        "start": "🔥 *Привет, {}!* 🔥\n\nДобро пожаловать в сервис сносов!\n\n👇 *Выберите действие:*",
        "balance": "📊 *Мои сносы*\n\nДоступно: *{}* сносов\n\nАктивные подписки:\n{}",
        "btn_subscriptions": "🎫 Подписки",
        "btn_extra_reports": "⚡ Доп. сносы",
        "btn_my_reports": "📊 Мои сносы",
        "btn_history": "📜 История",
        "btn_language": "🌐 Сменить язык",
        "btn_back": "🔙 Главное меню",
        "no_active_subs": "Нет активных подписок",
        "subscription_expired": "⚠️ Ваша подписка истекла!",
        "report_used": "✅ Использован 1 снос на @{}\nОсталось сносов: {}",
        "no_reports_left": "❌ У вас закончились сносы!\nКупите подписку или дополнительные сносы.",
        "target_username": "📝 *Введите username цели:*\n\nПример: @username или t.me/username",
        "confirm_report": "🎯 *Подтверждение сноса*\n\nЦель: @{}\nОстанется сносов: {}\n\n✅ Подтверждаете?",
        "report_success": "✅ *Снос выполнен!*\n\n🎯 Цель: @{}\n💥 Использовано сносов: 1\n📊 Осталось: {}\n\nРезультат: {}",
        "buy_subscription": "🎫 *Выберите подписку:*",
        "buy_extra": "⚡ *Выберите пакет дополнительных сносов:*",
        "purchase_success": "✅ *Покупка успешна!*\n\n📦 {}\n🎁 Получено сносов: {}\n💰 Цена: ${}\n\n📊 Всего сносов: {}",
        "history_empty": "📜 *История*\n\nУ вас пока нет операций.",
        "history": "📜 *История операций*\n\n{}",
        "sub_active": "✅ *Активная подписка*\n\nТип: {}\nДействует до: {}\nДоступно сносов в период: {}",
        "crypto_payment": "🧾 *Оплата через CryptoPay*\n\n💰 Сумма: ${}\n🆔 Invoice: `{}`\n\nПосле оплаты нажмите «Проверить»",
        "check_payment": "🔄 Проверить оплату",
        "payment_success": "✅ *Оплата подтверждена!*\n\nТовар активирован!",
        "payment_wait": "⏳ Ожидаем оплату...\nСчет действителен 30 минут.",
        "payment_error": "❌ Ошибка при создании счета: {}",
        "payment_not_found": "❌ Платеж не найден или еще не оплачен",
    },
    "uk": {
        "start": "🔥 *Вітаю, {}!* 🔥\n\nЛаскаво просимо до сервісу сносів!\n\n👇 *Оберіть дію:*",
        "balance": "📊 *Мої сноси*\n\nДоступно: *{}* сносів\n\nАктивні підписки:\n{}",
        "btn_subscriptions": "🎫 Підписки",
        "btn_extra_reports": "⚡ Дод. сноси",
        "btn_my_reports": "📊 Мої сноси",
        "btn_history": "📜 Історія",
        "btn_language": "🌐 Змінити мову",
        "btn_back": "🔙 Головне меню",
        "no_active_subs": "Немає активних підписок",
        "subscription_expired": "⚠️ Ваша підписка закінчилася!",
        "report_used": "✅ Використано 1 снос на @{}\nЗалишилось сносів: {}",
        "no_reports_left": "❌ У вас закінчилися сноси!\nКупіть підписку або додаткові сноси.",
        "target_username": "📝 *Введіть username цілі:*\n\nПриклад: @username або t.me/username",
        "confirm_report": "🎯 *Підтвердження сносу*\n\nЦіль: @{}\nЗалишиться сносів: {}\n\n✅ Підтверджуєте?",
        "report_success": "✅ *Снос виконано!*\n\n🎯 Ціль: @{}\n💥 Використано сносів: 1\n📊 Залишилось: {}\n\nРезультат: {}",
        "buy_subscription": "🎫 *Оберіть підписку:*",
        "buy_extra": "⚡ *Оберіть пакет додаткових сносів:*",
        "purchase_success": "✅ *Покупка успішна!*\n\n📦 {}\n🎁 Отримано сносів: {}\n💰 Ціна: ${}\n\n📊 Всього сносів: {}",
        "history_empty": "📜 *Історія*\n\nУ вас поки що немає операцій.",
        "history": "📜 *Історія операцій*\n\n{}",
        "sub_active": "✅ *Активна підписка*\n\nТип: {}\nДіє до: {}\nДоступно сносів у період: {}",
        "crypto_payment": "🧾 *Оплата через CryptoPay*\n\n💰 Сума: ${}\n🆔 Invoice: `{}`\n\nПісля оплати натисніть «Перевірити»",
        "check_payment": "🔄 Перевірити оплату",
        "payment_success": "✅ *Оплата підтверджена!*\n\nТовар активовано!",
        "payment_wait": "⏳ Очікуємо оплату...\nРахунок дійсний 30 хвилин.",
        "payment_error": "❌ Помилка при створенні рахунку: {}",
        "payment_not_found": "❌ Платіж не знайдено або ще не оплачений",
    },
    "en": {
        "start": "🔥 *Hello, {}!* 🔥\n\nWelcome to the report service!\n\n👇 *Choose an action:*",
        "balance": "📊 *My reports*\n\nAvailable: *{}* reports\n\nActive subscriptions:\n{}",
        "btn_subscriptions": "🎫 Subscriptions",
        "btn_extra_reports": "⚡ Extra reports",
        "btn_my_reports": "📊 My reports",
        "btn_history": "📜 History",
        "btn_language": "🌐 Change language",
        "btn_back": "🔙 Main menu",
        "no_active_subs": "No active subscriptions",
        "subscription_expired": "⚠️ Your subscription has expired!",
        "report_used": "✅ Used 1 report on @{}\nReports left: {}",
        "no_reports_left": "❌ You have no reports left!\nBuy a subscription or extra reports.",
        "target_username": "📝 *Enter target username:*\n\nExample: @username or t.me/username",
        "confirm_report": "🎯 *Confirm report*\n\nTarget: @{}\nReports left: {}\n\n✅ Confirm?",
        "report_success": "✅ *Report completed!*\n\n🎯 Target: @{}\n💥 Reports used: 1\n📊 Left: {}\n\nResult: {}",
        "buy_subscription": "🎫 *Choose subscription:*",
        "buy_extra": "⚡ *Choose extra reports package:*",
        "purchase_success": "✅ *Purchase successful!*\n\n📦 {}\n🎁 Reports received: {}\n💰 Price: ${}\n\n📊 Total reports: {}",
        "history_empty": "📜 *History*\n\nNo transactions yet.",
        "history": "📜 *Transaction history*\n\n{}",
        "sub_active": "✅ *Active subscription*\n\nType: {}\nValid until: {}\nReports available in period: {}",
        "crypto_payment": "🧾 *Payment via CryptoPay*\n\n💰 Amount: ${}\n🆔 Invoice: `{}`\n\nAfter payment click «Check»",
        "check_payment": "🔄 Check payment",
        "payment_success": "✅ *Payment confirmed!*\n\nProduct activated!",
        "payment_wait": "⏳ Waiting for payment...\nInvoice valid for 30 minutes.",
        "payment_error": "❌ Error creating invoice: {}",
        "payment_not_found": "❌ Payment not found or not paid yet",
    }
}

# ==================== БАЗА ДАННЫХ ====================
class Database:
    def __init__(self, db_name: str = "users.db"):
        self.db_name = db_name
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Основная таблица пользователей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    reports INTEGER DEFAULT 0,
                    total_purchased INTEGER DEFAULT 0,
                    total_used INTEGER DEFAULT 0,
                    registered_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    language TEXT DEFAULT 'ru'
                )
            """)
            
            # Таблица подписок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER PRIMARY KEY,
                    sub_type TEXT,
                    reports_limit INTEGER,
                    reports_used INTEGER DEFAULT 0,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица покупок
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_type TEXT,
                    item_name TEXT,
                    reports_added INTEGER,
                    price REAL,
                    purchased_at TIMESTAMP
                )
            """)
            
            # Таблица операций (использование сносов)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_usage (
                    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    target TEXT,
                    used_at TIMESTAMP
                )
            """)
            
            # Таблица платежных сессий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payment_sessions (
                    user_id INTEGER PRIMARY KEY,
                    invoice_id INTEGER,
                    item_type TEXT,
                    item_key TEXT,
                    amount REAL,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    def get_user(self, user_id: int) -> dict:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            username = username.lstrip('@')
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_all_users(self) -> List[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, first_name, reports, total_purchased, total_used, language FROM users ORDER BY reports DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, language: str = 'ru') -> dict:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, reports, registered_at, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, 0, datetime.now(), language))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())
    
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> dict:
        user = self.get_user(user_id)
        if not user:
            user = self.create_user(user_id, username, first_name, last_name)
            logger.info(f"Создан новый пользователь: {user_id}")
        return user
    
    def update_language(self, user_id: int, language: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
    
    def add_reports(self, user_id: int, amount: int, purchase_type: str, item_name: str, price: float):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Обновляем баланс сносов
            cursor.execute("UPDATE users SET reports = reports + ?, total_purchased = total_purchased + ? WHERE user_id = ?", 
                          (amount, amount, user_id))
            # Добавляем запись о покупке
            cursor.execute("""
                INSERT INTO purchases (user_id, item_type, item_name, reports_added, price, purchased_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, purchase_type, item_name, amount, price, datetime.now()))
            conn.commit()
    
    def use_report(self, user_id: int, target: str) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Проверяем есть ли сносы
            cursor.execute("SELECT reports FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if not result or result[0] <= 0:
                return False
            
            # Уменьшаем количество сносов
            cursor.execute("UPDATE users SET reports = reports - 1, total_used = total_used + 1 WHERE user_id = ?", (user_id,))
            
            # Записываем использование
            cursor.execute("""
                INSERT INTO report_usage (user_id, target, used_at)
                VALUES (?, ?, ?)
            """, (user_id, target, datetime.now()))
            
            conn.commit()
            return True
    
    def get_active_subscription(self, user_id: int) -> Optional[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND active = 1 AND end_date > ?
            """, (user_id, datetime.now()))
            sub = cursor.fetchone()
            return dict(sub) if sub else None
    
    def add_subscription(self, user_id: int, sub_type: str, reports_limit: int, duration_days: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Деактивируем старую подписку
            cursor.execute("UPDATE subscriptions SET active = 0 WHERE user_id = ?", (user_id,))
            
            # Создаем новую
            start_date = datetime.now()
            end_date = start_date + timedelta(days=duration_days)
            cursor.execute("""
                INSERT OR REPLACE INTO subscriptions (user_id, sub_type, reports_limit, reports_used, start_date, end_date, active)
                VALUES (?, ?, ?, 0, ?, ?, 1)
            """, (user_id, sub_type, reports_limit, start_date, end_date))
            
            # Добавляем сносы
            cursor.execute("UPDATE users SET reports = reports + ? WHERE user_id = ?", (reports_limit, user_id))
            
            conn.commit()
    
    def get_user_purchases(self, user_id: int, limit: int = 10) -> List[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM purchases WHERE user_id = ? ORDER BY purchased_at DESC LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_usage(self, user_id: int, limit: int = 10) -> List[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM report_usage WHERE user_id = ? ORDER BY used_at DESC LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def save_payment_session(self, user_id: int, invoice_id: int, item_type: str, item_key: str, amount: float, expires_in: int = 1800):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            cursor.execute("""
                INSERT OR REPLACE INTO payment_sessions (user_id, invoice_id, item_type, item_key, amount, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, invoice_id, item_type, item_key, amount, datetime.now(), expires_at))
            conn.commit()
    
    def get_payment_session(self, user_id: int) -> Optional[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM payment_sessions WHERE user_id = ? AND expires_at > ?
            """, (user_id, datetime.now()))
            session = cursor.fetchone()
            return dict(session) if session else None
    
    def delete_payment_session(self, user_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM payment_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
    
    def set_reports_direct(self, user_id: int, new_reports: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET reports = ? WHERE user_id = ?", (new_reports, user_id))
            conn.commit()

db = Database()

# ==================== CRYPTO PAY КЛИЕНТ ====================
class CryptoPayClient:
    def __init__(self, api_token: str, testnet: bool = False):
        self.api_token = api_token
        self.base_url = "https://testnet-pay.crypt.bot/api" if testnet else "https://pay.crypt.bot/api"
    
    async def _request(self, method: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{method}"
        headers = {
            "Crypto-Pay-API-Token": self.api_token,
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=params or {}) as response:
                result = await response.json()
                if not result.get("ok"):
                    raise Exception(f"Crypto Pay error: {result.get('error')}")
                return result["result"]
    
    async def create_invoice(self, asset: str, amount: str, description: str = None, payload: str = None, expires_in: int = 1800) -> dict:
        params = {"asset": asset, "amount": str(amount), "expires_in": expires_in}
        if description:
            params["description"] = description
        if payload:
            params["payload"] = payload
        return await self._request("createInvoice", params)
    
    async def get_invoices(self, invoice_ids: list = None) -> dict:
        params = {}
        if invoice_ids:
            params["invoice_ids"] = ",".join(map(str, invoice_ids))
        return await self._request("getInvoices", params)

crypto_client = CryptoPayClient(CRYPTO_PAY_TOKEN, testnet=CRYPTO_PAY_TESTNET)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_text(user_id: int, key: str, *args) -> str:
    user = db.get_user(user_id)
    lang = user['language'] if user else 'ru'
    text = TEXTS.get(lang, TEXTS['ru']).get(key, "Ошибка")
    if args:
        return text.format(*args)
    return text

def get_active_subscription_text(user_id: int) -> str:
    sub = db.get_active_subscription(user_id)
    if not sub:
        return get_text(user_id, "no_active_subs")
    
    sub_names = {
        "day": get_text(user_id, "sub_day") if "sub_day" in TEXTS[db.get_user(user_id)['language']] else "Дневная",
        "week": "Недельная",
        "month": "Месячная"
    }
    end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y')
    remaining = sub['reports_limit'] - sub['reports_used']
    
    return f"• {sub_names.get(sub['sub_type'], sub['sub_type'])}: до {end_date} ({remaining}/{sub['reports_limit']} сносов)"

def extract_username(text: str) -> str:
    text = text.strip()
    if text.startswith('@'):
        text = text[1:]
    if 't.me/' in text:
        match = re.search(r't\.me/([^/?]+)', text)
        if match:
            return match.group(1)
    if len(text) >= 3 and not re.search(r'[\s<>]', text):
        return text
    return text

def is_valid_username(username: str) -> bool:
    if not username:
        return False
    if 3 <= len(username) <= 32:
        if not re.search(r'[\s<>{}[\]\\]', username):
            return True
    return False

# ==================== КЛАВИАТУРЫ ====================
async def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, "btn_subscriptions"), callback_data="action_subscriptions")],
        [InlineKeyboardButton(get_text(user_id, "btn_extra_reports"), callback_data="action_extra_reports")],
        [InlineKeyboardButton(get_text(user_id, "btn_my_reports"), callback_data="action_my_reports")],
        [InlineKeyboardButton(get_text(user_id, "btn_history"), callback_data="action_history")],
        [InlineKeyboardButton(get_text(user_id, "btn_language"), callback_data="action_language")]
    ])

async def get_subscriptions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for sub_id, sub in SUBSCRIPTIONS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{sub['emoji']} {sub['name']} - ${sub['price']} ({sub['reports']} сносов)",
                callback_data=f"buy_sub_{sub_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")])
    return InlineKeyboardMarkup(keyboard)

async def get_extra_reports_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for rep_id, rep in EXTRA_REPORTS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{rep['emoji']} {rep['name']} - ${rep['price']}",
                callback_data=f"buy_extra_{rep_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")])
    return InlineKeyboardMarkup(keyboard)

async def get_admin_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton("💰 Изменить сносы", callback_data="admin_change_reports")],
        [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("🔚 Завершить админку", callback_data="admin_exit")],
        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
    ])

async def get_language_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
    ])

# ==================== ОБРАБОТЧИКИ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    text = get_text(user.id, "start", user.first_name)
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=await get_main_keyboard(user.id)
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет доступа к админ-панели!")
        return
    
    # Очищаем состояние админа
    context.user_data.pop("admin_waiting_user", None)
    context.user_data.pop("admin_waiting_reports", None)
    
    await update.message.reply_text(
        "👑 *Админ панель*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=await get_admin_keyboard(user_id)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    user = db.get_or_create_user(
        user_id, 
        query.from_user.username, 
        query.from_user.first_name, 
        query.from_user.last_name
    )
    
    logger.info(f"Нажата кнопка: {data} от пользователя {user_id}")
    
    # Смена языка
    if data == "action_language":
        await query.edit_message_text(
            "🌐 *Выберите язык:*",
            parse_mode="Markdown",
            reply_markup=await get_language_keyboard(user_id)
        )
        return
    
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        db.update_language(user_id, lang)
        await query.edit_message_text(
            f"🌐 *Язык изменен на {lang.upper()}*",
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Главное меню
    if data == "action_back_to_main":
        await query.edit_message_text(
            get_text(user_id, "start", query.from_user.first_name),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "action_my_reports":
        sub_text = get_active_subscription_text(user_id)
        await query.edit_message_text(
            get_text(user_id, "balance", user['reports'], sub_text),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "action_history":
        purchases = db.get_user_purchases(user_id)
        usage = db.get_user_usage(user_id)
        
        if not purchases and not usage:
            await query.edit_message_text(
                get_text(user_id, "history_empty"),
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
        
        history_text = ""
        if purchases:
            history_text += "*Покупки:*\n"
            for p in purchases[:5]:
                date = datetime.strptime(p['purchased_at'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y %H:%M')
                history_text += f"• {p['item_name']} (+{p['reports_added']} сносов) - ${p['price']} ({date})\n"
        
        if usage:
            history_text += "\n*Использование:*\n"
            for u in usage[:5]:
                date = datetime.strptime(u['used_at'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y %H:%M')
                history_text += f"• Снос на @{u['target']} ({date})\n"
        
        await query.edit_message_text(
            get_text(user_id, "history", history_text),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # Подписки
    if data == "action_subscriptions":
        await query.edit_message_text(
            get_text(user_id, "buy_subscription"),
            parse_mode="Markdown",
            reply_markup=await get_subscriptions_keyboard(user_id)
        )
        return
    
    if data.startswith("buy_sub_"):
        sub_id = data.replace("buy_sub_", "")
        sub = SUBSCRIPTIONS.get(sub_id)
        if sub:
            await create_payment_invoice(update, query, user_id, "subscription", sub_id, sub['price'])
        return
    
    # Дополнительные сносы
    if data == "action_extra_reports":
        await query.edit_message_text(
            get_text(user_id, "buy_extra"),
            parse_mode="Markdown",
            reply_markup=await get_extra_reports_keyboard(user_id)
        )
        return
    
    if data.startswith("buy_extra_"):
        extra_id = data.replace("buy_extra_", "")
        extra = EXTRA_REPORTS.get(extra_id)
        if extra:
            await create_payment_invoice(update, query, user_id, "extra", extra_id, extra['price'])
        return
    
    # Проверка платежа
    if data.startswith("check_payment_"):
        invoice_id = int(data.split("_")[2])
        session = db.get_payment_session(user_id)
        
        if not session or session['invoice_id'] != invoice_id:
            await query.edit_message_text("❌ Сессия платежа не найдена")
            return
        
        try:
            invoices = await crypto_client.get_invoices([invoice_id])
            if invoices and invoices.get('items'):
                invoice = invoices['items'][0]
                if invoice.get('status') == 'paid':
                    # Активируем товар
                    if session['item_type'] == 'subscription':
                        sub = SUBSCRIPTIONS[session['item_key']]
                        db.add_subscription(user_id, session['item_key'], sub['reports'], sub['duration_days'])
                        db.add_reports(user_id, sub['reports'], "subscription", sub['name'], session['amount'])
                        db.delete_payment_session(user_id)
                        
                        await query.edit_message_text(
                            get_text(user_id, "purchase_success", 
                                    sub['name'], sub['reports'], session['amount'], 
                                    db.get_user(user_id)['reports']),
                            parse_mode="Markdown",
                            reply_markup=await get_main_keyboard(user_id)
                        )
                    else:
                        extra = EXTRA_REPORTS[session['item_key']]
                        db.add_reports(user_id, extra['reports'], "extra", extra['name'], session['amount'])
                        db.delete_payment_session(user_id)
                        
                        await query.edit_message_text(
                            get_text(user_id, "purchase_success",
                                    extra['name'], extra['reports'], session['amount'],
                                    db.get_user(user_id)['reports']),
                            parse_mode="Markdown",
                            reply_markup=await get_main_keyboard(user_id)
                        )
                else:
                    await query.answer("⏳ Платеж еще не подтвержден", show_alert=True)
            else:
                await query.answer(get_text(user_id, "payment_not_found"), show_alert=True)
        except Exception as e:
            await query.answer(f"Ошибка: {str(e)}", show_alert=True)
        return
    
    # Админ панель
    if data == "admin_exit":
        context.user_data.clear()
        await query.edit_message_text(
            "👑 *Админ панель закрыта*",
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "admin_users":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Доступ запрещен!")
            return
        
        users = db.get_all_users()
        if not users:
            text = "📊 *Список пользователей*\n\nПользователей нет"
        else:
            text = "📊 *Список пользователей*\n\n"
            for u in users[:20]:
                name = u.get('username') or u.get('first_name') or str(u['user_id'])
                text += f"• ID: `{u['user_id']}` | @{name} | 💥 {u['reports']} сносов\n"
            text += f"\nВсего: {len(users)}"
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    if data == "admin_stats":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Доступ запрещен!")
            return
        
        users = db.get_all_users()
        total_reports = sum(u['reports'] for u in users)
        total_purchased = sum(u['total_purchased'] for u in users)
        total_used = sum(u['total_used'] for u in users)
        
        await query.edit_message_text(
            f"📈 *Статистика*\n\n"
            f"👥 Пользователей: {len(users)}\n"
            f"💥 Всего сносов: {total_reports}\n"
            f"📥 Куплено: {total_purchased}\n"
            f"📤 Использовано: {total_used}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    if data == "admin_change_reports":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Доступ запрещен!")
            return
        
        context.user_data["admin_waiting_user"] = True
        
        await query.edit_message_text(
            "💰 *Изменение количества сносов*\n\n"
            "Введите ID пользователя или @username:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
            ])
        )
        return
    
    if data == "admin_back":
        await query.edit_message_text(
            "👑 *Админ панель*",
            parse_mode="Markdown",
            reply_markup=await get_admin_keyboard(user_id)
        )
        return
    
    # Использование сноса (из главного меню)
    if data.startswith("use_report_"):
        target = context.user_data.get("target_for_report")
        if not target:
            context.user_data["awaiting_target"] = True
            await query.edit_message_text(
                get_text(user_id, "target_username"),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
                ])
            )
            return
        
        # Используем снос
        if db.use_report(user_id, target):
            user = db.get_user(user_id)
            await query.edit_message_text(
                get_text(user_id, "report_success", target, user['reports'], "Успешно!"),
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
            context.user_data.pop("target_for_report", None)
        else:
            await query.edit_message_text(
                get_text(user_id, "no_reports_left"),
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
        return

async def create_payment_invoice(update, query, user_id: int, item_type: str, item_key: str, amount: float):
    try:
        invoice = await crypto_client.create_invoice(
            asset="USDT",
            amount=str(amount),
            description=f"Покупка: {item_type} - {item_key}",
            payload=f"{item_type}_{item_key}_{user_id}",
            expires_in=1800
        )
        
        invoice_id = invoice["invoice_id"]
        pay_url = invoice["bot_invoice_url"]
        
        db.save_payment_session(user_id, invoice_id, item_type, item_key, amount, 1800)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 ОПЛАТИТЬ", url=pay_url)],
            [InlineKeyboardButton(get_text(user_id, "check_payment"), callback_data=f"check_payment_{invoice_id}")],
            [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
        ])
        
        await query.edit_message_text(
            get_text(user_id, "crypto_payment", amount, invoice_id),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        await query.edit_message_text(
            get_text(user_id, "payment_error", str(e)),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    db.get_or_create_user(
        user_id, 
        update.effective_user.username, 
        update.effective_user.first_name, 
        update.effective_user.last_name
    )
    
    # Админ режим - ожидание ID пользователя
    if context.user_data.get("admin_waiting_user"):
        user_input = text
        
        # Ищем пользователя
        target_user = None
        try:
            target_id = int(user_input)
            target_user = db.get_user(target_id)
        except ValueError:
            username = user_input.lstrip('@')
            target_user = db.get_user_by_username(username)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь не найден: {user_input}")
            return
        
        context.user_data["admin_target_user_id"] = target_user['user_id']
        context.user_data["admin_waiting_user"] = False
        context.user_data["admin_waiting_reports"] = True
        
        await update.message.reply_text(
            f"💰 Введите новое количество сносов для пользователя `{target_user['user_id']}`:\n"
            f"Текущее количество: {target_user['reports']}",
            parse_mode="Markdown"
        )
        return
    
    # Админ режим - ожидание суммы
    if context.user_data.get("admin_waiting_reports"):
        try:
            new_reports = int(text)
            if new_reports < 0:
                await update.message.reply_text("❌ Количество сносов не может быть отрицательным!")
                return
            
            target_user_id = context.user_data.get("admin_target_user_id")
            db.set_reports_direct(target_user_id, new_reports)
            
            await update.message.reply_text(f"✅ Количество сносов изменено на {new_reports}")
            
            # Очищаем состояние админа
            context.user_data.pop("admin_waiting_reports", None)
            context.user_data.pop("admin_target_user_id", None)
            
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число!")
        return
    
    # Ожидание цели для сноса
    if context.user_data.get("awaiting_target"):
        target = extract_username(text)
        
        if not is_valid_username(target):
            await update.message.reply_text("❌ Неверный формат username. Попробуйте еще раз:")
            return
        
        user = db.get_user(user_id)
        if user['reports'] <= 0:
            await update.message.reply_text(
                get_text(user_id, "no_reports_left"),
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
            context.user_data.pop("awaiting_target", None)
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить", callback_data="use_report_confirm")],
            [InlineKeyboardButton("❌ Отмена", callback_data="action_back_to_main")]
        ])
        
        context.user_data["target_for_report"] = target
        context.user_data["awaiting_target"] = False
        
        await update.message.reply_text(
            get_text(user_id, "confirm_report", target, user['reports'] - 1),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return
    
    # Если не в специальном режиме - показываем меню
    await update.message.reply_text(
        get_text(user_id, "start", update.effective_user.first_name),
        parse_mode="Markdown",
        reply_markup=await get_main_keyboard(user_id)
    )

async def run_fake_reporting(user_id: int, target: str, claims_count: int, bot):
    """Имитация процесса (для совместимости с старым кодом)"""
    # Просто отправляем уведомление
    await bot.send_message(
        user_id,
        f"✅ *Снос выполнен!*\n\n🎯 Цель: @{target}\n💥 Использовано: {claims_count} сносов",
        parse_mode="Markdown"
    )

# ==================== ЗАПУСК ====================
async def run_bot():
    """Запуск бота"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Бот запущен и готов к работе!")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise

def main():
    """Главная функция для Railway"""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
