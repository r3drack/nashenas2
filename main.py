import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import logging
from pymongo import MongoClient
from datetime import datetime

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# اتصال به دیتابیس
MONGO_URI = os.getenv('MONGO_URI')
db_client = MongoClient(MONGO_URI)
db = db_client.get_database()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"سلام {user.first_name}!\n\n"
        "ربات پیام‌های ناشناس\n\n"
        "برای ارسال پیام ناشناس:\n"
        "1. پیام را فوروارد کنید\n"
        "2. یا آیدی کاربر + پیام را بفرستید\n"
        "مثال: 123456789 سلام چطوری؟"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.forward_from:
        # پیام فوروارد شده
        target_user = update.message.forward_from
        sender = update.effective_user
        message = update.message.text or update.message.caption or "پیام رسانه‌ای"
        
        db.messages.insert_one({
            'sender_id': sender.id,
            'target_id': target_user.id,
            'message': message,
            'date': datetime.now(),
            'replied': False
        })
        
        try:
            await context.bot.send_message(
                chat_id=target_user.id,
                text=f"📩 پیام ناشناس:\n\n{message}"
            )
            await update.message.reply_text("✅ پیام ارسال شد!")
        except Exception as e:
            await update.message.reply_text("❌ ارسال پیام ناموفق بود!")
            logger.error(f"Error sending message: {e}")

    else:
        # پیام معمولی
        text = update.message.text
        if text and len(text.split()) >= 2:
            try:
                target_id = int(text.split()[0])
                message = ' '.join(text.split()[1:])
                sender = update.effective_user
                
                db.messages.insert_one({
                    'sender_id': sender.id,
                    'target_id': target_id,
                    'message': message,
                    'date': datetime.now(),
                    'replied': False
                })
                
                try:
                    await context.bot.send_message(
                        chat_id=target_id,
                        text=f"📩 پیام ناشناس:\n\n{message}"
                    )
                    await update.message.reply_text("✅ پیام ارسال شد!")
                except Exception as e:
                    await update.message.reply_text("❌ ارسال پیام ناموفق بود!")
                    logger.error(f"Error sending message: {e}")

            except ValueError:
                await update.message.reply_text("⚠️ فرمت اشتباه! مثال صحیح:\n123456789 سلام")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="خطا:", exc_info=context.error)
    if update.effective_message:
        await update.effective_message.reply_text("⚠️ خطایی رخ داد!")

def main() -> None:
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

    # دستورات
    application.add_handler(CommandHandler("start", start))
    
    # پردازش پیام‌ها
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # هندلر خطا
    application.add_error_handler(error_handler)

    # اجرای ربات
    application.run_polling()

if __name__ == '__main__':
    main()
