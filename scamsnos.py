"""
Telegram Bot with Balance System + Crypto Pay + Admin Panel
ВСЕ КНОПКИ РАБОТАЮТ
Поддержка языков: Українська, Русский, English
"""

import asyncio
import sqlite3
import random
import datetime
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import aiohttp
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8796055769:AAG1DRlpWd7Zft4oGb0_A8309qJgM3UOf3M"
CRYPTO_PAY_TOKEN = "563269:AA4Y8OUEyuY3qRFkDUIZXO5VBrC6lyh4j0M"
CRYPTO_PAY_TESTNET = False

ADMIN_IDS = [964442694]

# Пакеты услуг
PACKAGES = {
    "basic": {
        "price": 2.99,
        "claims_min": 90,
        "claims_max": 100,
        "success_rate": 60,
        "emoji": "💎"
    },
    "pro": {
        "price": 6.99,
        "claims_min": 150,
        "claims_max": 200,
        "success_rate": 85,
        "emoji": "🔥"
    },
    "vip": {
        "price": 9.99,
        "claims_min": 250,
        "claims_max": 300,
        "success_rate": 100,
        "emoji": "👑"
    }
}

# Мультиязычные тексты
TEXTS = {
    "ru": {
        "package_basic_name": "Базовый",
        "package_pro_name": "Pro", 
        "package_vip_name": "VIP",
        "btn_deposit": "💰 Пополнить баланс",
        "btn_buy": "🛒 Купить услугу",
        "btn_balance": "📊 Мой баланс",
        "btn_history": "📜 История покупок",
        "btn_language": "🌐 Сменить язык",
        "btn_back": "🔙 Главное меню",
        "btn_back_admin": "🔙 Назад в админ-панель",
        "btn_back_deposit": "🔙 Назад",
        "btn_custom": "💰 Своя сумма",
        "btn_check": "🔄 Проверить оплату",
        "btn_pay": "💳 ОПЛАТИТЬ",
        "btn_confirm": "✅ Подтвердить заказ",
        "btn_back_packages": "🔙 Назад к пакетам",
        "btn_admin_users": "📊 Список пользователей",
        "btn_admin_balance": "💰 Изменить баланс",
        "btn_admin_stats": "📈 Статистика",
        "start": "🔥 *Привет, {}!* 🔥\n\nДобро пожаловать в сервис массовых жалоб!\n💪 Мы помогаем блокировать нежелательные аккаунты.\n\n💰 *Система баланса:*\n• Пополните баланс через CryptoBot\n• Выберите пакет услуг\n• Получите результат\n\n📦 *Пакеты:*\n💎 Базовый (90-100 жалоб) - $2.99\n🔥 Pro (150-200 жалоб) - $6.99  \n👑 VIP (250-300 жалоб) - $9.99\n\n👇 *Выберите действие:*",
        "balance": "💰 *Ваш баланс*\n\nДоступно: *${:.2f}*\nВсего пополнено: ${:.2f}\nВсего потрачено: ${:.2f}",
        "insufficient_funds": "❌ *Недостаточно средств!*\n\nВаш баланс: ${:.2f}\nСамый дешевый пакет: ${:.2f}\n\nПополните баланс:",
        "select_package": "🛒 *Выберите пакет услуг:*\n\n⚠️ *Форматы цели:*\n• `@username`\n• `https://t.me/username`\n• `username`\n\nПоддерживаются любые username.",
        "enter_target": "{}\n\n📝 *Введите цель для атаки:*\n\nПоддерживаемые форматы:\n• `@username`\n• `https://t.me/username`\n• `username`\n\n*Примеры:*\n`@durov`\n`https://t.me/durov`\n`its_naverla`",
        "confirm_purchase": "🎯 *Подтверждение заказа*\n\n📦 Пакет: {}\n🎯 Цель: @{}\n💰 Сумма: ${:.2f}\n\n✅ Подтвердите заказ:",
        "purchase_success": "✅ *Заказ выполнен!* ✅\n\n📦 Пакет: {}\n🎯 Цель: @{}\n💰 Списано: ${:.2f}\n📊 Отправлено жалоб: {}\n🎯 Статус: {}\n\n{}💰 Остаток: ${:.2f}\n\n➡️ /start — главное меню",
        "success_result": "✅ ЖАЛОБЫ ДОСТАВЛЕНЫ",
        "fail_result": "⚠️ ЧАСТИЧНО ДОСТАВЛЕНО",
        "no_history": "📜 *История заказов*\n\nУ вас еще не было заказов.",
        "history": "📜 *История заказов*\n\n",
        "deposit": "💰 *Пополнение баланса*\n\nВыберите сумму:",
        "enter_amount": "💰 *Введите сумму пополнения*\n\nОтправьте число от $1 до $500 (например: 25):",
        "invalid_amount": "❌ Сумма должна быть от $1 до $500. Попробуйте еще раз:",
        "invalid_number": "❌ Введите корректное число (например: 25):",
        "invoice_created": "🧾 *Счет на пополнение*\n\n💰 Сумма: ${}\n🆔 Номер: `{}`\n⏱️ Действителен 30 минут\n\nПосле оплаты нажмите «Проверить оплату»",
        "payment_success": "✅ *Баланс пополнен!*\n\n💰 Сумма: ${:.2f}\n💳 Новый баланс: ${:.2f}\n\nТеперь вы можете заказать услугу:",
        "payment_waiting": "⏳ *Ожидание оплаты*\n\nСумма: ${:.2f}\nСтатус: {}\n\nОплатите счет и нажмите проверку снова.",
        "session_not_found": "❌ Сессия не найдена",
        "invoice_not_found": "❌ Счет не найден",
        "invoice_expired": "❌ Счет просрочен",
        "invalid_username": "❌ *Неверный формат!*\n\nВведите корректный username или ссылку.\n\n📝 *Примеры:*\n• `@username`\n• `https://t.me/username`\n• `username123`\n\nПожалуйста, введите цель еще раз:",
        "language_changed": "🌐 *Язык изменен на Русский*",
        "select_language": "🌐 *Выберите язык:*",
        "admin_panel": "👑 *Админ панель*\n\nВыберите действие:",
        "admin_users": "📊 *Список пользователей*\n\n",
        "admin_stats": "📈 *Статистика сервиса*\n\n👥 Пользователей: {}\n💰 Общий баланс: ${:.2f}\n💵 Всего пополнений: ${:.2f}\n💸 Всего потрачено: ${:.2f}\n\n📦 Пакеты:\n• Базовый: ${}\n• Pro: ${}\n• VIP: ${}",
        "admin_change_balance": "💰 *Изменение баланса пользователя*\n\nВведите ID пользователя или @username:\n\nПримеры:\n`123456789`\n`@username`",
        "enter_new_balance": "💰 Введите новую сумму баланса для пользователя `{}`:\n\nПример: `50` или `0`",
        "balance_changed": "✅ *Баланс изменен!*\n\nПользователь: @{}\nID: `{}`\nНовый баланс: *${:.2f}*",
        "user_not_found": "❌ Пользователь с ID {} не найден!",
        "user_not_found_username": "❌ Пользователь с username @{} не найден!",
        "no_access": "❌ У вас нет доступа к админ-панели!",
        "error": "❌ Ошибка: {}",
        "package_info": "{} *{}*\n\n💰 Цена: ${}\n📊 Жалоб: {}-{}\n🎯 Эффективность: {}%",
        "process_start": "🚀 *Запущен процесс жалоб*\n🎯 Цель: @{}\n📊 Всего заявок: {}\n\n📨 Обработано: 0 / {}\n🔄 Статус: 🔴 АКТИВЕН",
        "process_progress": "🚀 *Процесс жалоб*\n🎯 Цель: @{}\n📊 Всего заявок: {}\n\n📨 Обработано: {} / {}\n📈 `{}`\n🔄 Статус: 🔴 АКТИВЕН",
        "process_complete": "✅ *ЖАЛОБЫ УСПЕШНО ДОСТАВЛЕНЫ* ✅\n\n🎯 Цель: @{}\n📊 Отправлено жалоб: {}\n\n🕒 Время выполнения: {} сек.\n💪 Статус: ВЫПОЛНЕНО\n\n➡️ /start — главное меню",
        "reports_short": "жалоб"
    },
    "uk": {
        "package_basic_name": "Базовий",
        "package_pro_name": "Pro",
        "package_vip_name": "VIP",
        "btn_deposit": "💰 Поповнити баланс",
        "btn_buy": "🛒 Купити послугу",
        "btn_balance": "📊 Мій баланс",
        "btn_history": "📜 Історія замовлень",
        "btn_language": "🌐 Змінити мову",
        "btn_back": "🔙 Головне меню",
        "btn_back_admin": "🔙 Назад в адмін-панель",
        "btn_back_deposit": "🔙 Назад",
        "btn_custom": "💰 Своя сума",
        "btn_check": "🔄 Перевірити оплату",
        "btn_pay": "💳 ОПЛАТИТИ",
        "btn_confirm": "✅ Підтвердити замовлення",
        "btn_back_packages": "🔙 Назад до пакетів",
        "btn_admin_users": "📊 Список користувачів",
        "btn_admin_balance": "💰 Змінити баланс",
        "btn_admin_stats": "📈 Статистика",
        "start": "🔥 *Вітаю, {}!* 🔥\n\nЛаскаво просимо до сервісу масових скарг!\n💪 Ми допомагаємо блокувати небажані акаунти.\n\n💰 *Система балансу:*\n• Поповніть баланс через CryptoBot\n• Виберіть пакет послуг\n• Отримайте результат\n\n📦 *Пакети:*\n💎 Базовий (90-100 скарг) - $2.99\n🔥 Pro (150-200 скарг) - $6.99\n👑 VIP (250-300 скарг) - $9.99\n\n👇 *Виберіть дію:*",
        "balance": "💰 *Ваш баланс*\n\nДоступно: *${:.2f}*\nВсього поповнено: ${:.2f}\nВсього витрачено: ${:.2f}",
        "insufficient_funds": "❌ *Недостатньо коштів!*\n\nВаш баланс: ${:.2f}\nНайдешевший пакет: ${:.2f}\n\nПоповніть баланс:",
        "select_package": "🛒 *Виберіть пакет послуг:*\n\n⚠️ *Формати цілі:*\n• `@username`\n• `https://t.me/username`\n• `username`\n\nПідтримуються будь-які username.",
        "enter_target": "{}\n\n📝 *Введіть ціль для атаки:*\n\nПідтримувані формати:\n• `@username`\n• `https://t.me/username`\n• `username`\n\n*Приклади:*\n`@durov`\n`https://t.me/durov`\n`its_naverla`",
        "confirm_purchase": "🎯 *Підтвердження замовлення*\n\n📦 Пакет: {}\n🎯 Ціль: @{}\n💰 Сума: ${:.2f}\n\n✅ Підтвердіть замовлення:",
        "purchase_success": "✅ *Замовлення виконано!* ✅\n\n📦 Пакет: {}\n🎯 Ціль: @{}\n💰 Списано: ${:.2f}\n📊 Відправлено скарг: {}\n🎯 Статус: {}\n\n{}💰 Залишок: ${:.2f}\n\n➡️ /start — головне меню",
        "success_result": "✅ СКАРГИ ДОСТАВЛЕНО",
        "fail_result": "⚠️ ЧАСТКОВО ДОСТАВЛЕНО",
        "no_history": "📜 *Історія замовлень*\n\nУ вас ще не було замовлень.",
        "history": "📜 *Історія замовлень*\n\n",
        "deposit": "💰 *Поповнення балансу*\n\nВиберіть суму:",
        "enter_amount": "💰 *Введіть суму поповнення*\n\nВідправте число від $1 до $500 (наприклад: 25):",
        "invalid_amount": "❌ Сума повинна бути від $1 до $500. Спробуйте ще раз:",
        "invalid_number": "❌ Введіть коректне число (наприклад: 25):",
        "invoice_created": "🧾 *Рахунок на поповнення*\n\n💰 Сума: ${}\n🆔 Номер: `{}`\n⏱️ Дійсний 30 хвилин\n\nПісля оплати натисніть «Перевірити оплату»",
        "payment_success": "✅ *Баланс поповнено!*\n\n💰 Сума: ${:.2f}\n💳 Новий баланс: ${:.2f}\n\nТепер ви можете замовити послугу:",
        "payment_waiting": "⏳ *Очікування оплати*\n\nСума: ${:.2f}\nСтатус: {}\n\nОплатіть рахунок і натисніть перевірку знову.",
        "session_not_found": "❌ Сесію не знайдено",
        "invoice_not_found": "❌ Рахунок не знайдено",
        "invoice_expired": "❌ Рахунок прострочено",
        "invalid_username": "❌ *Невірний формат!*\n\nВведіть коректний username або посилання.\n\n📝 *Приклади:*\n• `@username`\n• `https://t.me/username`\n• `username123`\n\nБудь ласка, введіть ціль ще раз:",
        "language_changed": "🌐 *Мову змінено на Українську*",
        "select_language": "🌐 *Виберіть мову:*",
        "admin_panel": "👑 *Адмін панель*\n\nВиберіть дію:",
        "admin_users": "📊 *Список користувачів*\n\n",
        "admin_stats": "📈 *Статистика сервісу*\n\n👥 Користувачів: {}\n💰 Загальний баланс: ${:.2f}\n💵 Всього поповнень: ${:.2f}\n💸 Всього витрачено: ${:.2f}\n\n📦 Пакети:\n• Базовий: ${}\n• Pro: ${}\n• VIP: ${}",
        "admin_change_balance": "💰 *Зміна балансу користувача*\n\nВведіть ID користувача або @username:\n\nПриклади:\n`123456789`\n`@username`",
        "enter_new_balance": "💰 Введіть нову суму балансу для користувача `{}`:\n\nПриклад: `50` або `0`",
        "balance_changed": "✅ *Баланс змінено!*\n\nКористувач: @{}\nID: `{}`\nНовий баланс: *${:.2f}*",
        "user_not_found": "❌ Користувача з ID {} не знайдено!",
        "user_not_found_username": "❌ Користувача з username @{} не знайдено!",
        "no_access": "❌ У вас немає доступу до адмін-панелі!",
        "error": "❌ Помилка: {}",
        "package_info": "{} *{}*\n\n💰 Ціна: ${}\n📊 Скарг: {}-{}\n🎯 Ефективність: {}%",
        "process_start": "🚀 *Запущено процес скарг*\n🎯 Ціль: @{}\n📊 Всього заявок: {}\n\n📨 Оброблено: 0 / {}\n🔄 Статус: 🔴 АКТИВНИЙ",
        "process_progress": "🚀 *Процес скарг*\n🎯 Ціль: @{}\n📊 Всього заявок: {}\n\n📨 Оброблено: {} / {}\n📈 `{}`\n🔄 Статус: 🔴 АКТИВНИЙ",
        "process_complete": "✅ *СКАРГИ УСПІШНО ДОСТАВЛЕНО* ✅\n\n🎯 Ціль: @{}\n📊 Відправлено скарг: {}\n\n🕒 Час виконання: {} сек.\n💪 Статус: ВИКОНАНО\n\n➡️ /start — головне меню",
        "reports_short": "скарг"
    },
    "en": {
        "package_basic_name": "Basic",
        "package_pro_name": "Pro",
        "package_vip_name": "VIP",
        "btn_deposit": "💰 Top Up Balance",
        "btn_buy": "🛒 Buy Service",
        "btn_balance": "📊 My Balance",
        "btn_history": "📜 Order History",
        "btn_language": "🌐 Change Language",
        "btn_back": "🔙 Main Menu",
        "btn_back_admin": "🔙 Back to Admin Panel",
        "btn_back_deposit": "🔙 Back",
        "btn_custom": "💰 Custom Amount",
        "btn_check": "🔄 Check Payment",
        "btn_pay": "💳 PAY",
        "btn_confirm": "✅ Confirm Order",
        "btn_back_packages": "🔙 Back to Packages",
        "btn_admin_users": "📊 User List",
        "btn_admin_balance": "💰 Change Balance",
        "btn_admin_stats": "📈 Statistics",
        "start": "🔥 *Hello, {}!* 🔥\n\nWelcome to the mass reporting service!\n💪 We help block unwanted accounts.\n\n💰 *Balance System:*\n• Top up via CryptoBot\n• Select a service package\n• Get results\n\n📦 *Packages:*\n💎 Basic (90-100 reports) - $2.99\n🔥 Pro (150-200 reports) - $6.99\n👑 VIP (250-300 reports) - $9.99\n\n👇 *Choose an action:*",
        "balance": "💰 *Your Balance*\n\nAvailable: *${:.2f}*\nTotal deposits: ${:.2f}\nTotal spent: ${:.2f}",
        "insufficient_funds": "❌ *Insufficient funds!*\n\nYour balance: ${:.2f}\nCheapest package: ${:.2f}\n\nTop up your balance:",
        "select_package": "🛒 *Select a service package:*\n\n⚠️ *Target formats:*\n• `@username`\n• `https://t.me/username`\n• `username`\n\nAny username is supported.",
        "enter_target": "{}\n\n📝 *Enter target for attack:*\n\nSupported formats:\n• `@username`\n• `https://t.me/username`\n• `username`\n\n*Examples:*\n`@durov`\n`https://t.me/durov`\n`its_naverla`",
        "confirm_purchase": "🎯 *Confirm Order*\n\n📦 Package: {}\n🎯 Target: @{}\n💰 Amount: ${:.2f}\n\n✅ Confirm order:",
        "purchase_success": "✅ *Order completed!* ✅\n\n📦 Package: {}\n🎯 Target: @{}\n💰 Debited: ${:.2f}\n📊 Reports sent: {}\n🎯 Status: {}\n\n{}💰 Remaining: ${:.2f}\n\n➡️ /start — main menu",
        "success_result": "✅ REPORTS DELIVERED",
        "fail_result": "⚠️ PARTIALLY DELIVERED",
        "no_history": "📜 *Order History*\n\nYou have no orders yet.",
        "history": "📜 *Order History*\n\n",
        "deposit": "💰 *Top Up Balance*\n\nSelect amount:",
        "enter_amount": "💰 *Enter deposit amount*\n\nSend a number from $1 to $500 (example: 25):",
        "invalid_amount": "❌ Amount must be from $1 to $500. Try again:",
        "invalid_number": "❌ Enter a valid number (example: 25):",
        "invoice_created": "🧾 *Deposit Invoice*\n\n💰 Amount: ${}\n🆔 Number: `{}`\n⏱️ Valid for 30 minutes\n\nAfter payment, click «Check payment»",
        "payment_success": "✅ *Balance topped up!*\n\n💰 Amount: ${:.2f}\n💳 New balance: ${:.2f}\n\nNow you can order the service:",
        "payment_waiting": "⏳ *Waiting for payment*\n\nAmount: ${:.2f}\nStatus: {}\n\nPay the invoice and check again.",
        "session_not_found": "❌ Session not found",
        "invoice_not_found": "❌ Invoice not found",
        "invoice_expired": "❌ Invoice expired",
        "invalid_username": "❌ *Invalid format!*\n\nEnter a valid username or link.\n\n📝 *Examples:*\n• `@username`\n• `https://t.me/username`\n• `username123`\n\nPlease enter target again:",
        "language_changed": "🌐 *Language changed to English*",
        "select_language": "🌐 *Select language:*",
        "admin_panel": "👑 *Admin Panel*\n\nSelect action:",
        "admin_users": "📊 *User List*\n\n",
        "admin_stats": "📈 *Service Statistics*\n\n👥 Users: {}\n💰 Total balance: ${:.2f}\n💵 Total deposits: ${:.2f}\n💸 Total spent: ${:.2f}\n\n📦 Packages:\n• Basic: ${}\n• Pro: ${}\n• VIP: ${}",
        "admin_change_balance": "💰 *Change User Balance*\n\nEnter user ID or @username:\n\nExamples:\n`123456789`\n`@username`",
        "enter_new_balance": "💰 Enter new balance amount for user `{}`:\n\nExample: `50` or `0`",
        "balance_changed": "✅ *Balance changed!*\n\nUser: @{}\nID: `{}`\nNew balance: *${:.2f}*",
        "user_not_found": "❌ User with ID {} not found!",
        "user_not_found_username": "❌ User with username @{} not found!",
        "no_access": "❌ You don't have access to admin panel!",
        "error": "❌ Error: {}",
        "package_info": "{} *{}*\n\n💰 Price: ${}\n📊 Reports: {}-{}\n🎯 Efficiency: {}%",
        "process_start": "🚀 *Report process started*\n🎯 Target: @{}\n📊 Total requests: {}\n\n📨 Processed: 0 / {}\n🔄 Status: 🔴 ACTIVE",
        "process_progress": "🚀 *Report process*\n🎯 Target: @{}\n📊 Total requests: {}\n\n📨 Processed: {} / {}\n📈 `{}`\n🔄 Status: 🔴 ACTIVE",
        "process_complete": "✅ *REPORTS SUCCESSFULLY DELIVERED* ✅\n\n🎯 Target: @{}\n📊 Reports sent: {}\n\n🕒 Time taken: {} sec.\n💪 Status: COMPLETED\n\n➡️ /start — main menu",
        "reports_short": "reports"
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0,
                    total_deposits REAL DEFAULT 0,
                    total_spent REAL DEFAULT 0,
                    registered_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    language TEXT DEFAULT 'ru'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deposits (
                    deposit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    invoice_id INTEGER,
                    amount REAL,
                    asset TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    paid_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    package_name TEXT,
                    target TEXT,
                    claims_count INTEGER,
                    success_rate INTEGER,
                    price REAL,
                    purchased_at TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deposit_sessions (
                    user_id INTEGER PRIMARY KEY,
                    invoice_id INTEGER,
                    amount REAL,
                    asset TEXT,
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
            cursor.execute("SELECT user_id, username, first_name, balance, total_deposits, total_spent, language FROM users ORDER BY balance DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, language: str = 'ru') -> dict:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, balance, registered_at, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, 0.0, datetime.now(), language))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())
    
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> dict:
        user = self.get_user(user_id)
        if not user:
            user = self.create_user(user_id, username, first_name, last_name)
        return user
    
    def update_language(self, user_id: int, language: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
    
    def update_balance(self, user_id: int, amount: float, operation: str = "add"):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if operation == "add":
                cursor.execute("UPDATE users SET balance = balance + ?, total_deposits = total_deposits + ? WHERE user_id = ?", 
                               (amount, amount, user_id))
            elif operation == "subtract":
                cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id = ?", 
                               (amount, amount, user_id))
            elif operation == "set":
                cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
    
    def set_balance_direct(self, user_id: int, new_balance: float):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
    
    def add_deposit(self, user_id: int, invoice_id: int, amount: float, asset: str, status: str = "pending") -> int:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deposits (user_id, invoice_id, amount, asset, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, invoice_id, amount, asset, status, datetime.now()))
            deposit_id = cursor.lastrowid
            conn.commit()
            return deposit_id
    
    def update_deposit_status(self, invoice_id: int, status: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            paid_at = datetime.now() if status == "paid" else None
            cursor.execute("""
                UPDATE deposits SET status = ?, paid_at = ?
                WHERE invoice_id = ?
            """, (status, paid_at, invoice_id))
            
            if status == "paid":
                cursor.execute("SELECT user_id, amount FROM deposits WHERE invoice_id = ?", (invoice_id,))
                deposit = cursor.fetchone()
                if deposit:
                    self.update_balance(deposit[0], deposit[1], "add")
            conn.commit()
    
    def save_deposit_session(self, user_id: int, invoice_id: int, amount: float, asset: str, expires_in: int = 3600):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            cursor.execute("""
                INSERT OR REPLACE INTO deposit_sessions (user_id, invoice_id, amount, asset, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, invoice_id, amount, asset, datetime.now(), expires_at))
            conn.commit()
    
    def get_deposit_session(self, user_id: int) -> Optional[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM deposit_sessions WHERE user_id = ? AND expires_at > ?
            """, (user_id, datetime.now()))
            session = cursor.fetchone()
            return dict(session) if session else None
    
    def delete_deposit_session(self, user_id: int):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM deposit_sessions WHERE user_id = ?", (user_id,))
            conn.commit()
    
    def add_purchase(self, user_id: int, package_name: str, target: str, claims_count: int, success_rate: int, price: float):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO purchases (user_id, package_name, target, claims_count, success_rate, price, purchased_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, package_name, target, claims_count, success_rate, price, datetime.now()))
            conn.commit()
    
    def get_user_purchases(self, user_id: int, limit: int = 10) -> List[dict]:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM purchases WHERE user_id = ? ORDER BY purchased_at DESC LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

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
    
    async def create_invoice(self, asset: str, amount: str, description: str = None, payload: str = None, expires_in: int = 3600) -> dict:
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
    text = TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'][key])
    if args:
        return text.format(*args)
    return text

def get_package_name(user_id: int, package_id: str) -> str:
    user = db.get_user(user_id)
    lang = user['language'] if user else 'ru'
    key = f"package_{package_id}_name"
    return TEXTS.get(lang, TEXTS['ru']).get(key, package_id.capitalize())

def extract_username(text: str) -> str:
    """Извлекает username из текста или ссылки - поддерживает любые символы"""
    text = text.strip()
    
    # Удаляем @ если есть в начале
    if text.startswith('@'):
        text = text[1:]
    
    # Если это ссылка на Telegram
    if 't.me/' in text:
        # Извлекаем все после t.me/
        match = re.search(r't\.me/([^/?]+)', text)
        if match:
            return match.group(1)
    
    # Принимаем любые символы (не только буквы и цифры)
    # Telegram username может содержать: a-z, A-Z, 0-9, _
    # Но для реализма принимаем почти все, кроме пробелов и спецсимволов
    if len(text) >= 3 and not re.search(r'[\s<>]', text):
        return text
    
    return text

def is_valid_username(username: str) -> bool:
    """Проверяет валидность username - теперь более гибкая"""
    if not username:
        return False
    # Минимальная длина 3 символа, максимальная 32
    # Разрешаем буквы, цифры, underscore, дефис, точку
    if 3 <= len(username) <= 32:
        # Запрещаем только пробелы и спецсимволы
        if not re.search(r'[\s<>{}[\]\\]', username):
            return True
    return False

# ==================== КЛАВИАТУРЫ ====================
async def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, "btn_deposit"), callback_data="action_deposit")],
        [InlineKeyboardButton(get_text(user_id, "btn_buy"), callback_data="action_buy_service")],
        [InlineKeyboardButton(get_text(user_id, "btn_balance"), callback_data="action_my_balance")],
        [InlineKeyboardButton(get_text(user_id, "btn_history"), callback_data="action_history")],
        [InlineKeyboardButton(get_text(user_id, "btn_language"), callback_data="action_language")]
    ])

async def get_deposit_amounts_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💵 $5", callback_data="deposit_5"), InlineKeyboardButton("💵 $10", callback_data="deposit_10")],
        [InlineKeyboardButton("💵 $20", callback_data="deposit_20"), InlineKeyboardButton("💵 $50", callback_data="deposit_50")],
        [InlineKeyboardButton(get_text(user_id, "btn_custom"), callback_data="deposit_custom")],
        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
    ])

async def get_packages_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for pkg_id, pkg in PACKAGES.items():
        pkg_name = get_package_name(user_id, pkg_id)
        keyboard.append([
            InlineKeyboardButton(
                f"{pkg['emoji']} {pkg_name} - ${pkg['price']} ({pkg['claims_min']}-{pkg['claims_max']} {get_text(user_id, 'reports_short')})",
                callback_data=f"package_{pkg_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")])
    return InlineKeyboardMarkup(keyboard)

async def get_admin_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(user_id, "btn_admin_users"), callback_data="admin_users")],
        [InlineKeyboardButton(get_text(user_id, "btn_admin_balance"), callback_data="admin_change_balance")],
        [InlineKeyboardButton(get_text(user_id, "btn_admin_stats"), callback_data="admin_stats")],
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
        await update.message.reply_text(get_text(user_id, "no_access"))
        return
    
    await update.message.reply_text(
        get_text(user_id, "admin_panel"),
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
    
    print(f"[DEBUG] Нажата кнопка: {data}")
    
    # ========== СМЕНА ЯЗЫКА ==========
    if data == "action_language":
        await query.edit_message_text(
            get_text(user_id, "select_language"),
            parse_mode="Markdown",
            reply_markup=await get_language_keyboard(user_id)
        )
        return
    
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        db.update_language(user_id, lang)
        user = db.get_user(user_id)
        await query.edit_message_text(
            get_text(user_id, "language_changed"),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    # ========== ОБРАБОТКА ПРОВЕРКИ ОПЛАТЫ ==========
    if data.startswith("check_deposit_"):
        invoice_id = int(data.split("_")[2])
        
        session = db.get_deposit_session(user_id)
        if not session:
            await query.edit_message_text(get_text(user_id, "session_not_found"), reply_markup=await get_main_keyboard(user_id))
            return
        
        try:
            invoices = await crypto_client.get_invoices([invoice_id])
            if not invoices.get("items"):
                await query.edit_message_text(get_text(user_id, "invoice_not_found"))
                return
            
            invoice_data = invoices["items"][0]
            status = invoice_data.get("status")
            
            if status == "paid":
                db.update_deposit_status(invoice_id, "paid")
                db.delete_deposit_session(user_id)
                user = db.get_user(user_id)
                
                await query.edit_message_text(
                    get_text(user_id, "payment_success", session['amount'], user['balance']),
                    parse_mode="Markdown",
                    reply_markup=await get_main_keyboard(user_id)
                )
            elif status == "expired":
                await query.edit_message_text(get_text(user_id, "invoice_expired"), reply_markup=await get_main_keyboard(user_id))
                db.delete_deposit_session(user_id)
            else:
                await query.edit_message_text(
                    get_text(user_id, "payment_waiting", session['amount'], status),
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(user_id, "btn_check"), callback_data=f"check_deposit_{invoice_id}")],
                        [InlineKeyboardButton(get_text(user_id, "btn_back_deposit"), callback_data="action_deposit")]
                    ])
                )
        except Exception as e:
            await query.edit_message_text(get_text(user_id, "error", str(e)))
        return
    
    # ========== ГЛАВНОЕ МЕНЮ ==========
    if data == "action_back_to_main":
        await query.edit_message_text(
            get_text(user_id, "start", query.from_user.first_name),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "action_my_balance":
        await query.edit_message_text(
            get_text(user_id, "balance", user['balance'], user['total_deposits'], user['total_spent']),
            parse_mode="Markdown",
            reply_markup=await get_main_keyboard(user_id)
        )
        return
    
    if data == "action_history":
        purchases = db.get_user_purchases(user_id)
        if not purchases:
            await query.edit_message_text(
                get_text(user_id, "no_history"),
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
        else:
            text = get_text(user_id, "history")
            for p in purchases[:5]:
                text += f"• {p['package_name']} | @{p['target']} | {p['claims_count']} {get_text(user_id, 'reports_short')} | ${p['price']:.2f}\n"
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=await get_main_keyboard(user_id)
            )
        return
    
    # ========== ПОПОЛНЕНИЕ БАЛАНСА ==========
    if data == "action_deposit":
        context.user_data["awaiting_custom_amount"] = False
        context.user_data["admin_mode"] = False
        context.user_data["awaiting_target"] = False
        await query.edit_message_text(
            get_text(user_id, "deposit"),
            parse_mode="Markdown",
            reply_markup=await get_deposit_amounts_keyboard(user_id)
        )
        return
    
    if data.startswith("deposit_"):
        if data == "deposit_custom":
            context.user_data["awaiting_custom_amount"] = True
            context.user_data["admin_mode"] = False
            context.user_data["awaiting_target"] = False
            await query.edit_message_text(
                get_text(user_id, "enter_amount"),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(user_id, "btn_back_deposit"), callback_data="action_deposit")]
                ])
            )
            return
        
        amount = float(data.split("_")[1])
        await create_deposit_invoice(update, query, user_id, amount)
        return
    
    # ========== ПОКУПКА УСЛУГИ ==========
    if data == "action_buy_service":
        if user['balance'] < min(p['price'] for p in PACKAGES.values()):
            await query.edit_message_text(
                get_text(user_id, "insufficient_funds", user['balance'], min(p['price'] for p in PACKAGES.values())),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(user_id, "btn_deposit"), callback_data="action_deposit")],
                    [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
                ])
            )
            return
        
        await query.edit_message_text(
            get_text(user_id, "select_package"),
            parse_mode="Markdown",
            reply_markup=await get_packages_keyboard(user_id)
        )
        return
    
    if data.startswith("package_"):
        package_id = data.split("_")[1]
        context.user_data["selected_package"] = package_id
        context.user_data["awaiting_target"] = True
        context.user_data["admin_mode"] = False
        context.user_data["awaiting_custom_amount"] = False
        pkg = PACKAGES[package_id]
        pkg_name = get_package_name(user_id, package_id)
        
        await query.edit_message_text(
            get_text(user_id, "enter_target", 
                    get_text(user_id, "package_info", pkg['emoji'], pkg_name, pkg['price'], 
                            pkg['claims_min'], pkg['claims_max'], pkg['success_rate'])),
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("confirm_"):
        package_id = data.split("_")[1]
        pkg = PACKAGES[package_id]
        pkg_name = get_package_name(user_id, package_id)
        target = context.user_data.get("target")
        
        if not target:
            await query.edit_message_text("❌ Ошибка: цель не указана. Попробуйте снова /start")
            return
        
        user = db.get_user(user_id)
        if not user:
            await query.edit_message_text("❌ Ошибка: пользователь не найден!", reply_markup=await get_main_keyboard(user_id))
            return
            
        if user['balance'] < pkg['price']:
            await query.edit_message_text("❌ Недостаточно средств!", reply_markup=await get_main_keyboard(user_id))
            return
        
        db.update_balance(user_id, pkg['price'], "subtract")
        
        claims_count = random.randint(pkg['claims_min'], pkg['claims_max'])
        success = random.randint(1, 100) <= pkg['success_rate']
        
        db.add_purchase(user_id, pkg_name, target, claims_count, pkg['success_rate'], pkg['price'])
        
        user = db.get_user(user_id)
        
        result_text = get_text(user_id, "purchase_success", 
                              f"{pkg['emoji']} {pkg_name}", target, pkg['price'], 
                              claims_count,
                              get_text(user_id, "success_result") if success else get_text(user_id, "fail_result"),
                              "" if success else "",
                              user['balance'])
        
        await query.edit_message_text(result_text, parse_mode="Markdown")
        
        asyncio.create_task(run_fake_reporting(user_id, target, claims_count, context.bot))
        
        context.user_data["awaiting_target"] = False
        context.user_data["target"] = None
        return
    
    # ========== АДМИН ПАНЕЛЬ ==========
    if data == "admin_users":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text(get_text(user_id, "no_access"))
            return
        
        users = db.get_all_users()
        
        if not users:
            await query.edit_message_text("📊 Нет пользователей в базе данных.")
            return
        
        text = get_text(user_id, "admin_users")
        for u in users[:20]:
            name = u.get('username') or u.get('first_name') or str(u['user_id'])
            text += f"• ID: `{u['user_id']}` | @{name} | 💰 ${u['balance']:.2f} | Язык: {u.get('language', 'ru')}\n"
        
        text += f"\nВсего пользователей: {len(users)}"
        
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_back_admin"), callback_data="admin_back")]
            ])
        )
        return
    
    if data == "admin_stats":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text(get_text(user_id, "no_access"))
            return
        
        users = db.get_all_users()
        total_balance = sum(u['balance'] for u in users)
        total_deposits = sum(u['total_deposits'] for u in users)
        total_spent = sum(u['total_spent'] for u in users)
        
        await query.edit_message_text(
            get_text(user_id, "admin_stats", len(users), total_balance, total_deposits, total_spent,
                    PACKAGES['basic']['price'], PACKAGES['pro']['price'], PACKAGES['vip']['price']),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_back_admin"), callback_data="admin_back")]
            ])
        )
        return
    
    if data == "admin_change_balance":
        if user_id not in ADMIN_IDS:
            await query.edit_message_text(get_text(user_id, "no_access"))
            return
        
        context.user_data["admin_waiting_input"] = True
        context.user_data["admin_mode"] = True
        context.user_data["awaiting_custom_amount"] = False
        context.user_data["awaiting_target"] = False
        
        await query.edit_message_text(
            get_text(user_id, "admin_change_balance"),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_back_admin"), callback_data="admin_back")]
            ])
        )
        return
    
    if data == "admin_back":
        await query.edit_message_text(
            get_text(user_id, "admin_panel"),
            parse_mode="Markdown",
            reply_markup=await get_admin_keyboard(user_id)
        )
        return

async def create_deposit_invoice(update, query, user_id: int, amount: float):
    try:
        invoice = await crypto_client.create_invoice(
            asset="USDT",
            amount=str(amount),
            description=f"Пополнение баланса на ${amount}",
            payload=f"deposit_{user_id}",
            expires_in=1800
        )
        
        invoice_id = invoice["invoice_id"]
        pay_url = invoice["bot_invoice_url"]
        
        db.add_deposit(user_id, invoice_id, amount, "USDT", "pending")
        db.save_deposit_session(user_id, invoice_id, amount, "USDT", 1800)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(user_id, "btn_pay"), url=pay_url)],
            [InlineKeyboardButton(get_text(user_id, "btn_check"), callback_data=f"check_deposit_{invoice_id}")],
            [InlineKeyboardButton(get_text(user_id, "btn_back_deposit"), callback_data="action_deposit")]
        ])
        
        await query.edit_message_text(
            get_text(user_id, "invoice_created", amount, invoice_id),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        await query.edit_message_text(get_text(user_id, "error", str(e)))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    db.get_or_create_user(
        user_id, 
        update.effective_user.username, 
        update.effective_user.first_name, 
        update.effective_user.last_name
    )
    
    # ========== АДМИН РЕЖИМ - ИЗМЕНЕНИЕ БАЛАНСА ==========
    if context.user_data.get("admin_waiting_input"):
        user_input = update.message.text.strip()
        
        if "admin_waiting_amount" not in context.user_data:
            target_user = None
            
            try:
                target_id = int(user_input)
                target_user = db.get_user(target_id)
            except ValueError:
                username = user_input.lstrip('@')
                target_user = db.get_user_by_username(username)
            
            if not target_user:
                await update.message.reply_text(
                    get_text(user_id, "user_not_found_username" if user_input.startswith('@') else "user_not_found", user_input)
                )
                return
            
            context.user_data["admin_target_user_id"] = target_user['user_id']
            context.user_data["admin_waiting_amount"] = True
            
            await update.message.reply_text(
                get_text(user_id, "enter_new_balance", f"@{target_user.get('username', target_user['user_id'])}"),
                parse_mode="Markdown"
            )
        else:
            try:
                new_balance = float(user_input)
                target_user_id = context.user_data.get("admin_target_user_id")
                
                target_user = db.get_user(target_user_id)
                if not target_user:
                    await update.message.reply_text(get_text(user_id, "user_not_found", target_user_id))
                    context.user_data["admin_waiting_input"] = False
                    context.user_data["admin_waiting_amount"] = False
                    return
                
                db.set_balance_direct(target_user_id, new_balance)
                
                await update.message.reply_text(
                    get_text(user_id, "balance_changed", 
                            target_user.get('username') or target_user_id, 
                            target_user_id, 
                            new_balance),
                    parse_mode="Markdown"
                )
                
                try:
                    await context.bot.send_message(
                        target_user_id,
                        get_text(target_user_id, "balance_changed", 
                                "Admin", target_user_id, new_balance),
                        parse_mode="Markdown"
                    )
                except:
                    pass
                
                context.user_data["admin_waiting_input"] = False
                context.user_data["admin_waiting_amount"] = False
                context.user_data["admin_target_user_id"] = None
                
            except ValueError:
                await update.message.reply_text(get_text(user_id, "invalid_number"))
        return
    
    # ========== ПОПОЛНЕНИЕ БАЛАНСА ==========
    if context.user_data.get("awaiting_custom_amount"):
        try:
            amount = float(update.message.text.strip())
            if 1 <= amount <= 500:
                context.user_data["awaiting_custom_amount"] = False
                
                try:
                    invoice = await crypto_client.create_invoice(
                        asset="USDT",
                        amount=str(amount),
                        description=f"Пополнение баланса на ${amount}",
                        payload=f"deposit_{user_id}",
                        expires_in=1800
                    )
                    
                    invoice_id = invoice["invoice_id"]
                    pay_url = invoice["bot_invoice_url"]
                    
                    db.add_deposit(user_id, invoice_id, amount, "USDT", "pending")
                    db.save_deposit_session(user_id, invoice_id, amount, "USDT", 1800)
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(user_id, "btn_pay"), url=pay_url)],
                        [InlineKeyboardButton(get_text(user_id, "btn_check"), callback_data=f"check_deposit_{invoice_id}")],
                        [InlineKeyboardButton(get_text(user_id, "btn_back"), callback_data="action_back_to_main")]
                    ])
                    
                    await update.message.reply_text(
                        get_text(user_id, "invoice_created", amount, invoice_id),
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    await update.message.reply_text(get_text(user_id, "error", str(e)))
            else:
                await update.message.reply_text(get_text(user_id, "invalid_amount"))
        except ValueError:
            await update.message.reply_text(get_text(user_id, "invalid_number"))
        return
    
    # ========== ВВОД ЦЕЛИ ДЛЯ ПОКУПКИ ==========
    if context.user_data.get("awaiting_target"):
        target_text = update.message.text.strip()
        
        target = extract_username(target_text)
        
        if not is_valid_username(target):
            await update.message.reply_text(
                get_text(user_id, "invalid_username"),
                parse_mode="Markdown"
            )
            return
        
        context.user_data["target"] = target
        context.user_data["awaiting_target"] = False
        
        package_id = context.user_data.get("selected_package")
        if package_id:
            pkg = PACKAGES[package_id]
            pkg_name = get_package_name(user_id, package_id)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(get_text(user_id, "btn_confirm"), callback_data=f"confirm_{package_id}")],
                [InlineKeyboardButton(get_text(user_id, "btn_back_packages"), callback_data="action_buy_service")]
            ])
            
            await update.message.reply_text(
                get_text(user_id, "confirm_purchase", f"{pkg['emoji']} {pkg_name}", target, pkg['price']),
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        return

async def run_fake_reporting(user_id: int, target: str, claims_count: int, bot):
    """Имитация процесса - выглядит как реальный бот"""
    import time
    start_time = time.time()
    sent = 0
    
    status_msg = await bot.send_message(
        user_id,
        get_text(user_id, "process_start", target, claims_count, claims_count),
        parse_mode="Markdown"
    )
    
    while sent < claims_count:
        batch = random.randint(15, 25)
        if sent + batch > claims_count:
            batch = claims_count - sent
        sent += batch
        
        progress = int(30 * sent / claims_count)
        progress_bar = "█" * progress + "░" * (30 - progress)
        
        try:
            await status_msg.edit_text(
                get_text(user_id, "process_progress", target, claims_count, sent, claims_count, progress_bar),
                parse_mode="Markdown"
            )
        except:
            pass
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    elapsed_time = int(time.time() - start_time)
    
    await status_msg.edit_text(
        get_text(user_id, "process_complete", target, claims_count, elapsed_time),
        parse_mode="Markdown"
    )

# ==================== ЗАПУСК ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Бот запущен!")
    print("📁 База данных: users.db")
    print("👑 Админ-команда: /admin")
    print(f"👑 Администраторы: {ADMIN_IDS}")
    print("🌐 Поддерживаемые языки: Русский, Українська, English")
    app.run_polling()

if __name__ == "__main__":
    main()