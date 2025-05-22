import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
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

# اتصال به دیتابیس MongoDB (رایگان در https://www.mongodb.com/atlas)
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://username:password@cluster0.mongodb.net/anon_bot?retryWrites=true&w=majority')
db_client = MongoClient(MONGO_URI)
db = db_client.get_database()

# توکن ربات از متغیر محیطی (در رندر تنظیم می‌شود)
TOKEN = os.getenv('TELEGRAM_TOKEN')

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(
        f"سلام {user.first_name}!\n\n"
        "این ربات برای ارسال پیام‌های ناشناس است.\n"
        "برای ارسال پیام ناشناس به یک کاربر، یکی از روش‌های زیر را استفاده کنید:\n"
        "1. پیام را برای من فوروارد کنید\n"
        "2. آیدی کاربر را همراه با پیام بفرستید (مثال: `123456789 سلام تست`)"
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    if update.message.forward_from:
        # پیام فوروارد شده
        target_user = update.message.forward_from
        sender = update.effective_user
        message = update.message.text or update.message.caption or "پیام رسانه‌ای"
        
        # ذخیره در دیتابیس
        db.messages.insert_one({
            'sender_id': sender.id,
            'target_id': target_user.id,
            'message': message,
            'date': datetime.now(),
            'replied': False
        })
        
        # ارسال پیام
        context.bot.send_message(
            chat_id=target_user.id,
            text=f"📩 پیام ناشناس:\n\n{message}"
        )
        update.message.reply_text("✅ پیام شما به صورت ناشناس ارسال شد!")
    else:
        # پیام معمولی
        text = update.message.text
        if text and len(text.split()) >= 2:
            try:
                target_id = int(text.split()[0])
                message = ' '.join(text.split()[1:])
                sender = update.effective_user
                
                # ذخیره در دیتابیس
                db.messages.insert_one({
                    'sender_id': sender.id,
                    'target_id': target_id,
                    'message': message,
                    'date': datetime.now(),
                    'replied': False
                })
                
                # ارسال پیام
                context.bot.send_message(
                    chat_id=target_id,
                    text=f"📩 پیام ناشناس:\n\n{message}"
                )
                update.message.reply_text("✅ پیام شما به صورت ناشناس ارسال شد!")
            except ValueError:
                update.message.reply_text("⚠️ فرمت پیام اشتباه است. مثال صحیح: `123456789 سلام تست`")

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="خطا در پردازش پیام:", exc_info=context.error)
    if update.effective_message:
        update.effective_message.reply_text("⚠️ خطایی در پردازش پیام شما رخ داد!")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # دستورات
    dispatcher.add_handler(CommandHandler("start", start))
    
    # پردازش پیام‌ها
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # هندلر خطا
    dispatcher.add_error_handler(error_handler)

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()