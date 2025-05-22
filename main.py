import os
from telegram import Update
from telegram.ext import (
    Updater,  # تغییر از Application به Updater
    CommandHandler,
    MessageHandler,
    Filters,  # نه filters
    CallbackContext
)
from pymongo import MongoClient
import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات دیتابیس
MONGO_URI = os.getenv('MONGO_URI')
db_client = MongoClient(MONGO_URI)
db = db_client.get_database()

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(
        f"سلام {user.first_name}!\n\n"
        "این ربات پیام‌های ناشناس ارسال می‌کند.\n"
        "برای ارسال پیام:\n"
        "۱. پیام را فوروارد کنید\n"
        "۲. یا آیدی کاربر + پیام بفرستید\n"
        "مثال: 123456789 سلام"
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        if update.message.forward_from:
            target_user = update.message.forward_from
            message = update.message.text or "پیام رسانه‌ای"
        else:
            parts = update.message.text.split(maxsplit=1)
            if len(parts) < 2:
                update.message.reply_text("⚠️ فرمت اشتباه! مثال: 123456789 سلام")
                return
            target_user = type('', (), {'id': int(parts[0])})  # شبیه‌سازی کاربر
            message = parts[1]

        db.messages.insert_one({
            'sender_id': update.effective_user.id,
            'target_id': target_user.id,
            'message': message,
            'date': datetime.now()
        })

        context.bot.send_message(
            chat_id=target_user.id,
            text=f"📩 پیام ناشناس:\n\n{message}"
        )
        update.message.reply_text("✅ پیام ارسال شد!")
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ خطا در ارسال پیام!")

def main():
    updater = Updater(os.getenv('TELEGRAM_TOKEN'))
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
