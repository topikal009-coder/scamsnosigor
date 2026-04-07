import asyncio
import sqlite3
import random
import datetime
import os
import sys
import json
import time
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8796055769:AAG1DRlpWd7Zft4oGb0_A8309qJgM3UOf3M")
CRYPTO_PAY_TOKEN = os.environ.get("CRYPTO_PAY_TOKEN", "563714:AAoNQWxKCzZLDkotn5jjJdl0QFwMCAtEbtD")
CRYPTO_PAY_TESTNET = False

ADMIN_IDS = [964442694]
MODERATORS_FILE = "moderators.json"
USERS_FILE = "users_list.json"

SUBSCRIPTIONS = {
    "starter": {
        "reports": 50,
        "price": 4.99,
        "emoji": "🌟"
    },
    "standard": {
        "reports": 120,
        "price": 9.99,
        "emoji": "⭐"
    },
    "premium": {
        "reports": 250,
        "price": 19.99,
        "emoji": "👑"
    },
    "vip": {
        "reports": 500,
        "price": 39.99,
        "emoji": "💎"
    },
    "extreme": {
        "reports": 1000,
        "price": 79.99,
        "emoji": "🔥"
    }
}

EXTRA_REPORTS = {
    "single": {
        "reports": 1,
        "price": 2.00,
        "emoji": "🎯"
    },
    "five": {
        "reports": 5,
        "price": 8.00,
        "emoji": "🔥"
    },
    "ten": {
        "reports": 10,
        "price": 15.00,
        "emoji": "⚡"
    },
    "twenty": {
        "reports": 20,
        "price": 28.00,
        "emoji": "💥"
    },
    "fifty": {
        "reports": 50,
        "price": 65.00,
        "emoji": "👑"
    }
}

TEXTS = {
    "ru": {
        "welcome": "🌟 *Добро пожаловать в Report Bot!* 🌟\n\n"
                   "💪 *Мы поможем вам:*\n"
                   "• Удалить нежелательный контент\n"
                   "• Защитить свой аккаунт\n"
                   "• Наказать нарушителей\n\n"
                   "👇 *Выберите действие в меню ниже:*",
        "profile": "👤 *Мой профиль*\n\n"
                   "🆔 ID: `{}`\n"
                   "👑 Роль: {}\n"
                   "💥 Доступно сносов: *{}*\n"
                   "📊 Всего куплено: *{}*\n"
                   "📤 Всего использовано: *{}*\n\n"
                   "🎫 Активные подписки:\n{}",
        "btn_shop": "🛒 Магазин",
        "btn_profile": "👤 Профиль",
        "btn_start_report": "🎯 Начать снос",
        "btn_history": "📜 История",
        "btn_my_reports": "💥 Мои сносы",
        "btn_admin_panel": "👑 Админ панель",
        "btn_back": "🔙 Назад",
        "btn_language": "🌐 Сменить язык",
        "no_active_subs": "Нет активных подписок",
        "target_username": "📝 *Введите username цели:*\n\nПример: @username или t.me/username",
        "confirm_report": "🎯 *Подтверждение сноса*\n\nЦель: @{}\nОстанется сносов: {}\n\n✅ Подтверждаете?",
        "report_success": "✅ *Снос выполнен!*\n\n🎯 Цель: @{}\n💥 Осталось сносов: {}\n\nРезультат: Успешно!",
        "no_reports_left": "❌ *Нет сносов!*\n\nКупите подписку или дополнительные сносы в магазине.",
        "buy_subscription": "🛒 *Магазин - Подписки*\n\nВыберите подписку (все подписки работают пока не закончатся сносы):",
        "buy_extra": "🛒 *Магазин - Дополнительные сносы*\n\nВыберите пакет:",
        "purchase_success": "✅ *Покупка успешна!*\n\n📦 {}\n🎁 Получено: {} сносов\n💰 Цена: ${}\n\n💥 Всего сносов: {}",
        "history_empty": "📜 *История*\n\nУ вас пока нет операций.",
        "history": "📜 *История операций*\n\n{}",
        "crypto_payment": "🧾 *Оплата через CryptoPay*\n\n💰 Сумма: ${}\n🆔 Invoice: `{}`\n\n💳 Нажмите на кнопку ниже для оплаты",
        "check_payment": "✅ Проверить оплату",
        "payment_error": "❌ Ошибка при создании счета: {}",
        "payment_not_found": "❌ Платеж не найден",
        "sending_reports": "🚀 *Отправка жалоб*\n\n🎯 Цель: @{}\n📊 Прогресс: {}%\n┗━━━━━━━━━━━━━━━━━━━━┛\n█{}█\n\n📨 Отправлено: {} / {}\n⏱️ Скорость: {} жалоб/сек\n\n⏳ Пожалуйста, подождите...",
        "send_success": "✅ *Готово!*\n\n🎯 Цель: @{}\n📊 Отправлено жалоб: {}\n⏱️ Время: {}\n💥 Осталось сносов: {}",
        "role_user": "👤 Пользователь",
        "role_moder": "🛡️ Модератор",
        "role_admin": "👑 Администратор",
        "admin_give_subscription": "🎫 *Выдача подписки*\n\nВыберите подписку для выдачи пользователю:",
        "subscription_given": "✅ *Подписка выдана!*\n\nПользователь {} получил подписку {} (+{} сносов)"
    },
    "uk": {
        "welcome": "🌟 *Ласкаво просимо до Report Bot!* 🌟\n\n"
                   "💪 *Ми допоможемо вам:*\n"
                   "• Видалити небажаний контент\n"
                   "• Захистити свій акаунт\n"
                   "• Покарати порушників\n\n"
                   "👇 *Оберіть дію в меню нижче:*",
        "profile": "👤 *Мій профіль*\n\n"
                   "🆔 ID: `{}`\n"
                   "👑 Роль: {}\n"
                   "💥 Доступно сносів: *{}*\n"
                   "📊 Всього куплено: *{}*\n"
                   "📤 Всього використано: *{}*\n\n"
                   "🎫 Активні підписки:\n{}",
        "btn_shop": "🛒 Магазин",
        "btn_profile": "👤 Профіль",
        "btn_start_report": "🎯 Почати снос",
        "btn_history": "📜 Історія",
        "btn_my_reports": "💥 Мої сноси",
        "btn_admin_panel": "👑 Адмін панель",
        "btn_back": "🔙 Назад",
        "btn_language": "🌐 Змінити мову",
        "no_active_subs": "Немає активних підписок",
        "target_username": "📝 *Введіть username цілі:*\n\nПриклад: @username або t.me/username",
        "confirm_report": "🎯 *Підтвердження сносу*\n\nЦіль: @{}\nЗалишиться сносів: {}\n\n✅ Підтверджуєте?",
        "report_success": "✅ *Снос виконано!*\n\n🎯 Ціль: @{}\n💥 Залишилось сносів: {}\n\nРезультат: Успішно!",
        "no_reports_left": "❌ *Немає сносів!*\n\nКупіть підписку або додаткові сноси в магазині.",
        "buy_subscription": "🛒 *Магазин - Підписки*\n\nОберіть підписку (всі підписки працюють поки не закінчаться сноси):",
        "buy_extra": "🛒 *Магазин - Додаткові сноси*\n\nОберіть пакет:",
        "purchase_success": "✅ *Покупка успішна!*\n\n📦 {}\n🎁 Отримано: {} сносів\n💰 Ціна: ${}\n\n💥 Всього сносів: {}",
        "history_empty": "📜 *Історія*\n\nУ вас поки що немає операцій.",
        "history": "📜 *Історія операцій*\n\n{}",
        "crypto_payment": "🧾 *Оплата через CryptoPay*\n\n💰 Сума: ${}\n🆔 Invoice: `{}`\n\n💳 Натисніть на кнопку нижче для оплати",
        "check_payment": "✅ Перевірити оплату",
        "payment_error": "❌ Помилка при створенні рахунку: {}",
        "payment_not_found": "❌ Платіж не знайдено",
        "sending_reports": "🚀 *Відправка скарг*\n\n🎯 Ціль: @{}\n📊 Прогрес: {}%\n┗━━━━━━━━━━━━━━━━━━━━┛\n█{}█\n\n📨 Відправлено: {} / {}\n⏱️ Швидкість: {} скарг/сек\n\n⏳ Будь ласка, зачекайте...",
        "send_success": "✅ *Готово!*\n\n🎯 Ціль: @{}\n📊 Відправлено скарг: {}\n⏱️ Час: {}\n💥 Залишилось сносів: {}",
        "role_user": "👤 Користувач",
        "role_moder": "🛡️ Модератор",
        "role_admin": "👑 Адміністратор",
        "admin_give_subscription": "🎫 *Видача підписки*\n\nВиберіть підписку для видачі користувачу:",
        "subscription_given": "✅ *Підписка видана!*\n\nКористувач {} отримав підписку {} (+{} сносів)"
    },
    "en": {
        "welcome": "🌟 *Welcome to Report Bot!* 🌟\n\n"
                   "💪 *We help you:*\n"
                   "• Remove unwanted content\n"
                   "• Protect your account\n"
                   "• Punish violators\n\n"
                   "👇 *Choose an action in the menu below:*",
        "profile": "👤 *My profile*\n\n"
                   "🆔 ID: `{}`\n"
                   "👑 Role: {}\n"
                   "💥 Available reports: *{}*\n"
                   "📊 Total purchased: *{}*\n"
                   "📤 Total used: *{}*\n\n"
                   "🎫 Active subscriptions:\n{}",
        "btn_shop": "🛒 Shop",
        "btn_profile": "👤 Profile",
        "btn_start_report": "🎯 Start report",
        "btn_history": "📜 History",
        "btn_my_reports": "💥 My reports",
        "btn_admin_panel": "👑 Admin panel",
        "btn_back": "🔙 Back",
        "btn_language": "🌐 Change language",
        "no_active_subs": "No active subscriptions",
        "target_username": "📝 *Enter target username:*\n\nExample: @username or t.me/username",
        "confirm_report": "🎯 *Confirm report*\n\nTarget: @{}\nReports left: {}\n\n✅ Confirm?",
        "report_success": "✅ *Report completed!*\n\n🎯 Target: @{}\n💥 Reports left: {}\n\nResult: Success!",
        "no_reports_left": "❌ *No reports left!*\n\nBuy a subscription or extra reports in the shop.",
        "buy_subscription": "🛒 *Shop - Subscriptions*\n\nChoose a subscription (all subscriptions work until reports run out):",
        "buy_extra": "🛒 *Shop - Extra reports*\n\nChoose a package:",
        "purchase_success": "✅ *Purchase successful!*\n\n📦 {}\n🎁 Received: {} reports\n💰 Price: ${}\n\n💥 Total reports: {}",
        "history_empty": "📜 *History*\n\nNo transactions yet.",
        "history": "📜 *Transaction history*\n\n{}",
        "crypto_payment": "🧾 *Payment via CryptoPay*\n\n💰 Amount: ${}\n🆔 Invoice: `{}`\n\n💳 Click the button below to pay",
        "check_payment": "✅ Check payment",
        "payment_error": "❌ Error creating invoice: {}",
        "payment_not_found": "❌ Payment not found",
        "sending_reports": "🚀 *Sending reports*\n\n🎯 Target: @{}\n📊 Progress: {}%\n┗━━━━━━━━━━━━━━━━━━━━┛\n█{}█\n\n📨 Sent: {} / {}\n⏱️ Speed: {} reports/sec\n\n⏳ Please wait...",
        "send_success": "✅ *Done!*\n\n🎯 Target: @{}\n📊 Reports sent: {}\n⏱️ Time: {}\n💥 Reports left: {}",
        "role_user": "👤 User",
        "role_moder": "🛡️ Moderator",
        "role_admin": "👑 Administrator",
        "admin_give_subscription": "🎫 *Give subscription*\n\nChoose a subscription to give to the user:",
        "subscription_given": "✅ *Subscription given!*\n\nUser {} received {} subscription (+{} reports)"
    }
}

def load_moderators():
    if os.path.exists(MODERATORS_FILE):
        with open(MODERATORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_moderators(moderators):
    with open(MODERATORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(moderators, f, ensure_ascii=False, indent=2)

def get_user_role(user_id: int) -> str:
    if user_id in ADMIN_IDS:
        return "admin"
    elif user_id in load_moderators():
        return "moder"
    else:
        return "user"

def is_admin_or_moderator(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    moderators = load_moderators()
    return user_id in moderators

def load_users_list():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users_list(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

class Database:
    def __init__(self, db_name: str = "users.db"):
        self.db_name = db_name
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    reports INTEGER DEFAULT 0,
                    total_purchased INTEGER DEFAULT 0,
                    total_used INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'ru'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    sub_type TEXT,
                    reports_limit INTEGER,
                    reports_used INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    purchased_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_usage (
                    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    target TEXT,
                    used_at TIMESTAMP
                )
            """)
            
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
    
    def get_user(self, user_id: int) -> dict:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_all_users_data(self) -> List[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, reports, total_purchased, total_used, language FROM users ORDER BY reports DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def create_user(self, user_id: int, language: str = 'ru') -> dict:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, reports, language)
                VALUES (?, ?, ?)
            """, (user_id, 0, language))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())
    
    def get_or_create_user(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if not user:
            user = self.create_user(user_id)
        return user
    
    def update_language(self, user_id: int, language: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
    
    def add_reports(self, user_id: int, amount: int, purchase_type: str, item_name: str, price: float):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET reports = reports + ?, total_purchased = total_purchased + ? WHERE user_id = ?", 
                          (amount, amount, user_id))
            cursor.execute("""
                INSERT INTO purchases (user_id, item_type, item_name, reports_added, price, purchased_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, purchase_type, item_name, amount, price, datetime.now()))
            conn.commit()
    
    def use_report(self, user_id: int, target: str) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT reports FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if not result or result[0] <= 0:
                return False
            
            cursor.execute("UPDATE users SET reports = reports - 1, total_used = total_used + 1 WHERE user_id = ?", (user_id,))
            
            cursor.execute("""
                INSERT INTO report_usage (user_id, target, used_at)
                VALUES (?, ?, ?)
            """, (user_id, target, datetime.now()))
            
            conn.commit()
            return True
    
    def get_active_subscriptions(self, user_id: int) -> List[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND active = 1
                ORDER BY purchased_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_subscription(self, user_id: int, sub_type: str, reports_limit: int, price: float = 0):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO subscriptions (user_id, sub_type, reports_limit, active, purchased_at)
                VALUES (?, ?, ?, 1, ?)
            """, (user_id, sub_type, reports_limit, datetime.now()))
            
            cursor.execute("UPDATE users SET reports = reports + ? WHERE user_id = ?", (reports_limit, user_id))
            
            if price > 0:
                sub_names = {"starter": "Starter", "standard": "Standard", "premium": "Premium", "vip": "VIP", "extreme": "Extreme"}
                sub_name = sub_names.get(sub_type, sub_type)
                cursor.execute("""
                    INSERT INTO purchases (user_id, item_type, item_name, reports_added, price, purchased_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, "subscription", sub_name, reports_limit, price, datetime.now()))
            
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

def get_text(user_id: int, key: str, *args) -> str:
    user = db.get_user(user_id)
    lang = user['language'] if user else 'ru'
    text = TEXTS.get(lang, TEXTS['ru']).get(key, "Ошибка")
    if args:
        return text.format(*args)
    return text

def get_active_subscriptions_text(user_id: int) -> str:
    subs = db.get_active_subscriptions(user_id)
    if not subs:
        return get_text(user_id, "no_active_subs")
    
    sub_names = {"starter": "🌟 Starter", "standard": "⭐ Standard", "premium": "👑 Premium", "vip": "💎 VIP", "extreme": "🔥 Extreme"}
    text = ""
    for sub in subs:
        remaining = sub['reports_limit'] - sub['reports_used']
        text += f"• {sub_names.get(sub['sub_type'], sub['sub_type'])}: {remaining}/{sub['reports_limit']} сносов\n"
    
    return text

def extract_username(text: str) -> str:
    text = text.strip()
    if text.startswith('@'):
        text = text[1:]
    if 't.me/' in text:
        match = re.search(r't\.me/([^/?]+)', text)
        if match:
            return match.group(1)
    return text

def is_valid_username(username: str) -> bool:
    if not username:
        return False
    return 3 <= len(username) <= 32 and not re.search(r'[\s<>{}[\]\\]', username)

async def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(get_text(user_id, "btn_shop"), callback_data="action_shop")],
        [InlineKeyboardButton(get_text(user_id, "btn_profile"), callback_data="action_profile")],
        [InlineKeyboardButton(get_text(user_id, "btn_start_report"), callback_data="action_start_report")],
        [InlineKeyboardButton(get_text(user_id, "btn_language"), callback_data="action_language")]
    ]
    
    if is_admin_or_moderator(user_id):
        buttons.append([InlineKeyboardButton(get_text(user_id, "btn_admin_panel"), callback_data="action_admin_panel")])
    
    return InlineKeyboardMarkup(buttons)

async def get_shop_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎫 Подписки", callback_data="shop_subscriptions")],
        [InlineKeyboardButton("⚡ Дополнительные сносы", callback_data="shop_extra")],
        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
    ])

async def get_subscriptions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for sub_id, sub in SUBSCRIPTIONS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{sub['emoji']} ${sub['price']} - {sub['reports']} сносов",
                callback_data=f"buy_sub_{sub_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_shop")])
    return InlineKeyboardMarkup(keyboard)

async def get_extra_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for rep_id, rep in EXTRA_REPORTS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{rep['emoji']} ${rep['price']} - {rep['reports']} сносов",
                callback_data=f"buy_extra_{rep_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_shop")])
    return InlineKeyboardMarkup(keyboard)

async def get_admin_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton("💰 Изменить сносы", callback_data="admin_change_reports")],
        [InlineKeyboardButton("🎫 Выдать подписку", callback_data="admin_give_subscription")],
        [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("➕ Добавить модератора", callback_data="admin_add_moderator")],
        [InlineKeyboardButton("➖ Удалить модератора", callback_data="admin_remove_moderator")],
        [InlineKeyboardButton("🔚 Выйти из админки", callback_data="admin_exit")],
        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_admin_subscriptions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for sub_id, sub in SUBSCRIPTIONS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{sub['emoji']} {sub['reports']} сносов",
                callback_data=f"admin_give_sub_{sub_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")])
    return InlineKeyboardMarkup(keyboard)

async def get_language_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    db.get_or_create_user(user_id)
    
    users_list = load_users_list()
    if str(user_id) not in users_list:
        users_list[str(user_id)] = {
            "id": user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "joined_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_users_list(users_list)
    
    text = get_text(user_id, "welcome")
    
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=await get_main_keyboard(user_id)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    db.get_or_create_user(user_id)
    
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
            get_text(user_id, "welcome"),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "action_back_to_main":
        await query.edit_message_text(
            get_text(user_id, "welcome"),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "action_shop":
        await query.edit_message_text(
            "🛒 *Магазин*\n\nВыберите категорию:",
            parse_mode="Markdown",
            reply_markup=await get_shop_keyboard(user_id)
        )
        return
    
    if data == "shop_subscriptions":
        await query.edit_message_text(
            get_text(user_id, "buy_subscription"),
            parse_mode="Markdown",
            reply_markup=await get_subscriptions_keyboard(user_id)
        )
        return
    
    if data == "shop_extra":
        await query.edit_message_text(
            get_text(user_id, "buy_extra"),
            parse_mode="Markdown",
            reply_markup=await get_extra_keyboard(user_id)
        )
        return
    
    if data.startswith("buy_sub_"):
        sub_id = data.replace("buy_sub_", "")
        sub = SUBSCRIPTIONS.get(sub_id)
        if sub:
            await create_payment_invoice(update, query, user_id, "subscription", sub_id, sub['price'])
        return
    
    if data.startswith("buy_extra_"):
        extra_id = data.replace("buy_extra_", "")
        extra = EXTRA_REPORTS.get(extra_id)
        if extra:
            await create_payment_invoice(update, query, user_id, "extra", extra_id, extra['price'])
        return
    
    if data == "action_profile":
        user = db.get_user(user_id)
        role = get_text(user_id, f"role_{get_user_role(user_id)}")
        sub_text = get_active_subscriptions_text(user_id)
        await query.edit_message_text(
            get_text(user_id, "profile", user_id, role, user['reports'], user['total_purchased'], user['total_used'], sub_text),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_history"), callback_data="action_history")],
                [InlineKeyboardButton(get_text(user_id, "btn_my_reports"), callback_data="action_my_reports")],
                [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
            ])
        )
        return
    
    if data == "action_history":
        purchases = db.get_user_purchases(user_id)
        usage = db.get_user_usage(user_id)
        
        if not purchases and not usage:
            await query.edit_message_text(
                get_text(user_id, "history_empty"),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_profile")]
                ])
            )
            return
        
        history_text = ""
        if purchases:
            history_text += "*📦 Покупки:*\n"
            for p in purchases[:5]:
                date = datetime.strptime(p['purchased_at'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y %H:%M')
                history_text += f"• {p['item_name']} (+{p['reports_added']}) - ${p['price']} ({date})\n"
        
        if usage:
            history_text += "\n*🎯 Использование:*\n"
            for u in usage[:5]:
                date = datetime.strptime(u['used_at'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d.%m.%Y %H:%M')
                history_text += f"• Снос на @{u['target']} ({date})\n"
        
        await query.edit_message_text(
            get_text(user_id, "history", history_text),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_profile")]
            ])
        )
        return
    
    if data == "action_my_reports":
        user = db.get_user(user_id)
        role = get_text(user_id, f"role_{get_user_role(user_id)}")
        await query.edit_message_text(
            get_text(user_id, "profile", user_id, role, user['reports'], user['total_purchased'], user['total_used'], get_active_subscriptions_text(user_id)),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_profile")]
            ])
        )
        return
    
    if data == "action_start_report":
        user = db.get_user(user_id)
        if user['reports'] <= 0:
            await query.edit_message_text(
                get_text(user_id, "no_reports_left"),
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
            return
        
        context.user_data["awaiting_target"] = True
        await query.edit_message_text(
            get_text(user_id, "target_username"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
            ])
        )
        return
    
    if data == "action_admin_panel":
        if not is_admin_or_moderator(user_id):
            await query.edit_message_text("❌ Доступ запрещен!")
            return
        
        context.user_data.clear()
        await query.edit_message_text(
            "👑 *Админ панель*",
            parse_mode="Markdown",
            reply_markup=await get_admin_keyboard(user_id)
        )
        return
    
    if data == "admin_exit":
        context.user_data.clear()
        await query.edit_message_text(
            get_text(user_id, "welcome"),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "admin_give_subscription":
        if not is_admin_or_moderator(user_id):
            await query.answer("❌ Доступ запрещен!", show_alert=True)
            return
        
        context.user_data["admin_giving_subscription"] = True
        await query.edit_message_text(
            "🎫 *Выдача подписки*\n\nВведите ID пользователя:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
            ])
        )
        return
    
    if data.startswith("admin_give_sub_"):
        sub_id = data.replace("admin_give_sub_", "")
        target_id = context.user_data.get("admin_subscription_target")
        
        if target_id:
            sub = SUBSCRIPTIONS.get(sub_id)
            if sub:
                sub_names = {"starter": "Starter", "standard": "Standard", "premium": "Premium", "vip": "VIP", "extreme": "Extreme"}
                sub_name = sub_names.get(sub_id, sub_id)
                
                db.add_subscription(target_id, sub_id, sub['reports'])
                
                await query.edit_message_text(
                    get_text(user_id, "subscription_given", target_id, sub_name, sub['reports']),
                    parse_mode="Markdown",
                    reply_markup=await get_admin_keyboard(user_id)
                )
                
                try:
                    await query.bot.send_message(
                        target_id,
                        f"🎉 *Вам выдана подписка {sub_name}!*\n\n🎁 Получено: {sub['reports']} сносов\n💥 Всего сносов: {db.get_user(target_id)['reports']}",
                        parse_mode="Markdown"
                    )
                except:
                    pass
                
                context.user_data.pop("admin_subscription_target", None)
        return
    
    if data == "admin_users":
        if not is_admin_or_moderator(user_id):
            await query.answer("❌ Доступ запрещен!", show_alert=True)
            return
        
        users_list = load_users_list()
        users_data = db.get_all_users_data()
        moderators = load_moderators()
        
        if not users_list:
            text = "📊 *Список пользователей*\n\nПользователей нет"
        else:
            text = "📊 *Список пользователей*\n\n"
            count = 0
            for uid, u in users_list.items():
                if count >= 20:
                    break
                name = u.get('username') or u.get('first_name') or str(uid)
                user_data = next((x for x in users_data if str(x['user_id']) == str(uid)), None)
                reports = user_data['reports'] if user_data else 0
                
                if int(uid) in ADMIN_IDS:
                    role_icon = "👑"
                elif int(uid) in moderators:
                    role_icon = "🛡️"
                else:
                    role_icon = "👤"
                
                text += f"• {role_icon} `{uid}` | {name} | 💥 {reports}\n"
                count += 1
            text += f"\nВсего: {len(users_list)}"
        
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
            ])
        )
        await query.answer()
        return
    
    if data == "admin_stats":
        if not is_admin_or_moderator(user_id):
            await query.answer("❌ Доступ запрещен!", show_alert=True)
            return
        
        users_data = db.get_all_users_data()
        users_list = load_users_list()
        moderators = load_moderators()
        total_reports = sum(u['reports'] for u in users_data)
        total_purchased = sum(u['total_purchased'] for u in users_data)
        total_used = sum(u['total_used'] for u in users_data)
        
        await query.message.reply_text(
            f"📈 *Статистика*\n\n"
            f"👥 Пользователей: {len(users_list)}\n"
            f"👑 Администраторов: {len(ADMIN_IDS)}\n"
            f"🛡️ Модераторов: {len(moderators)}\n"
            f"💥 Всего сносов: {total_reports}\n"
            f"📥 Куплено: {total_purchased}\n"
            f"📤 Использовано: {total_used}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
            ])
        )
        await query.answer()
        return
    
    if data == "admin_change_reports":
        if not is_admin_or_moderator(user_id):
            await query.answer("❌ Доступ запрещен!", show_alert=True)
            return
        
        context.user_data["admin_waiting_user"] = True
        
        await query.edit_message_text(
            "💰 *Изменение количества сносов*\n\nВведите ID пользователя:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
            ])
        )
        return
    
    if data == "admin_add_moderator":
        if user_id not in ADMIN_IDS:
            await query.answer("❌ Только администратор может добавлять модераторов!", show_alert=True)
            return
        
        context.user_data["admin_adding_moderator"] = True
        await query.edit_message_text(
            "👮 *Добавление модератора*\n\nВведите ID пользователя:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
            ])
        )
        return
    
    if data == "admin_remove_moderator":
        if user_id not in ADMIN_IDS:
            await query.answer("❌ Только администратор может удалять модераторов!", show_alert=True)
            return
        
        moderators = load_moderators()
        if not moderators:
            await query.edit_message_text(
                "📋 *Список модераторов пуст*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
                ])
            )
            return
        
        text = "📋 *Список модераторов:*\n\n"
        for mod_id in moderators:
            text += f"• ID: `{mod_id}`\n"
        
        context.user_data["admin_removing_moderator"] = True
        await query.edit_message_text(
            text + "\nВведите ID модератора для удаления:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад", callback_data="action_admin_panel")]
            ])
        )
        return
    
    if data == "use_report_confirm":
        target = context.user_data.get("target_for_report")
        if not target:
            await query.edit_message_text(
                get_text(user_id, "target_username"),
                parse_mode="Markdown"
            )
            return
        
        if db.use_report(user_id, target):
            context.user_data.pop("target_for_report", None)
            await send_reports_with_animation(update, user_id, target, query.bot)
            await query.delete_message()
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
            [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_shop")]
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
            reply_markup=await get_shop_keyboard(user_id)
        )

async def check_payment_and_activate(update, query, user_id: int, invoice_id: int):
    session = db.get_payment_session(user_id)
    
    if not session or session['invoice_id'] != invoice_id:
        await query.edit_message_text("❌ Сессия платежа не найдена")
        return
    
    try:
        invoices = await crypto_client.get_invoices([invoice_id])
        if invoices and invoices.get('items'):
            invoice = invoices['items'][0]
            if invoice.get('status') == 'paid':
                if session['item_type'] == 'subscription':
                    sub = SUBSCRIPTIONS[session['item_key']]
                    sub_names = {"starter": "Starter", "standard": "Standard", "premium": "Premium", "vip": "VIP", "extreme": "Extreme"}
                    sub_name = sub_names.get(session['item_key'], session['item_key'])
                    db.add_subscription(user_id, session['item_key'], sub['reports'], session['amount'])
                    db.delete_payment_session(user_id)
                    
                    await query.edit_message_text(
                        get_text(user_id, "purchase_success", sub_name, sub['reports'], session['amount'], db.get_user(user_id)['reports']),
                        parse_mode="Markdown",
                        reply_markup=await get_main_keyboard(user_id)
                    )
                else:
                    extra = EXTRA_REPORTS[session['item_key']]
                    extra_names = {"single": "1 снос", "five": "5 сносов", "ten": "10 сносов", "twenty": "20 сносов", "fifty": "50 сносов"}
                    extra_name = extra_names.get(session['item_key'], session['item_key'])
                    db.add_reports(user_id, extra['reports'], "extra", extra_name, session['amount'])
                    db.delete_payment_session(user_id)
                    
                    await query.edit_message_text(
                        get_text(user_id, "purchase_success", extra_name, extra['reports'], session['amount'], db.get_user(user_id)['reports']),
                        parse_mode="Markdown",
                        reply_markup=await get_main_keyboard(user_id)
                    )
            else:
                await query.answer("⏳ Платеж еще не подтвержден", show_alert=True)
        else:
            await query.answer(get_text(user_id, "payment_not_found"), show_alert=True)
    except Exception as e:
        await query.answer(f"Ошибка: {str(e)}", show_alert=True)

async def send_reports_with_animation(update, user_id: int, target: str, bot):
    min_reports = random.randint(26, 56)
    max_reports = random.randint(226, 359)
    total = random.randint(min_reports, max_reports)
    
    status_msg = await bot.send_message(
        user_id,
        get_text(user_id, "sending_reports", target, 0, "░░░░░░░░░░░░░░░░░░░░", 0, total, 0),
        parse_mode="Markdown"
    )
    
    sent = 0
    start_time = time.time()
    
    while sent < total:
        batch = random.randint(26, 56)
        if sent + batch > total:
            batch = total - sent
        
        sent += batch
        progress = int(20 * sent / total)
        filled = "█" * progress
        empty = "░" * (20 - progress)
        percent = int(100 * sent / total)
        
        elapsed = time.time() - start_time
        speed = int(sent / elapsed) if elapsed > 0 else 0
        
        try:
            await status_msg.edit_text(
                get_text(user_id, "sending_reports", target, percent, filled + empty, sent, total, speed),
                parse_mode="Markdown"
            )
        except:
            pass
        
        await asyncio.sleep(1)
    
    elapsed_time = int(time.time() - start_time)
    user = db.get_user(user_id)
    
    await status_msg.edit_text(
        get_text(user_id, "send_success", target, total, f"{elapsed_time} сек", user['reports']),
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    db.get_or_create_user(user_id)
    
    if context.user_data.get("admin_waiting_user"):
        try:
            target_id = int(text)
            target_user = db.get_user(target_id)
            
            if not target_user:
                await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден!")
                return
            
            context.user_data["admin_target_user_id"] = target_id
            context.user_data["admin_waiting_user"] = False
            context.user_data["admin_waiting_reports"] = True
            
            await update.message.reply_text(
                f"💰 Введите новое количество сносов для пользователя `{target_id}`:\n"
                f"Текущее количество: {target_user['reports']}",
                parse_mode="Markdown"
            )
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID пользователя!")
        return
    
    if context.user_data.get("admin_waiting_reports"):
        try:
            new_reports = int(text)
            if new_reports < 0:
                await update.message.reply_text("❌ Количество сносов не может быть отрицательным!")
                return
            
            target_user_id = context.user_data.get("admin_target_user_id")
            db.set_reports_direct(target_user_id, new_reports)
            
            await update.message.reply_text(f"✅ Количество сносов изменено на {new_reports}")
            
            context.user_data.pop("admin_waiting_reports", None)
            context.user_data.pop("admin_target_user_id", None)
            
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число!")
        return
    
    if context.user_data.get("admin_giving_subscription"):
        try:
            target_id = int(text)
            target_user = db.get_user(target_id)
            
            if not target_user:
                await update.message.reply_text(f"❌ Пользователь с ID {target_id} не найден!")
                return
            
            context.user_data["admin_subscription_target"] = target_id
            context.user_data["admin_giving_subscription"] = False
            
            await update.message.reply_text(
                get_text(user_id, "admin_give_subscription"),
                parse_mode="Markdown",
                reply_markup=await get_admin_subscriptions_keyboard(user_id)
            )
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID пользователя!")
        return
    
    if context.user_data.get("admin_adding_moderator"):
        try:
            mod_id = int(text)
            
            if mod_id in ADMIN_IDS:
                await update.message.reply_text("❌ Нельзя добавить администратора как модератора!")
                return
            
            moderators = load_moderators()
            if mod_id in moderators:
                await update.message.reply_text(f"❌ Пользователь {mod_id} уже является модератором!")
                return
            
            moderators.append(mod_id)
            save_moderators(moderators)
            
            await update.message.reply_text(f"✅ Пользователь {mod_id} добавлен как модератор!")
            context.user_data.pop("admin_adding_moderator", None)
            
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID пользователя!")
        return
    
    if context.user_data.get("admin_removing_moderator"):
        try:
            mod_id = int(text)
            
            if mod_id in ADMIN_IDS:
                await update.message.reply_text("❌ Нельзя удалить администратора!")
                return
            
            moderators = load_moderators()
            if mod_id not in moderators:
                await update.message.reply_text(f"❌ Пользователь {mod_id} не является модератором!")
                return
            
            moderators.remove(mod_id)
            save_moderators(moderators)
            
            await update.message.reply_text(f"✅ Пользователь {mod_id} удален из модераторов!")
            context.user_data.pop("admin_removing_moderator", None)
            
        except ValueError:
            await update.message.reply_text("❌ Введите корректный ID пользователя!")
        return
    
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
        context.user_data.pop("awaiting_target", None)
        
        await update.message.reply_text(
            get_text(user_id, "confirm_report", target, user['reports'] - 1),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return
    
    await update.message.reply_text(
        get_text(user_id, "welcome"),
        parse_mode="Markdown",
        reply_markup=await get_main_keyboard(user_id)
    )

async def run_bot():
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Бот запущен!")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(3600)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise

def main():
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
