import os
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
import logging

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(
        f"سلام {user.first_name}!\n\n"
        "این ربات پیام‌های ناشناس ارسال می‌کند.\n\n"
        "دستورات:\n"
        "1. پیام را فوروارد کنید\n"
        "2. یا آیدی کاربر + پیام بفرستید\n"
        "مثال: 123456789 سلام"
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        if update.message.forward_from:
            # پیام فوروارد شده
            target_user = update.message.forward_from
            message = update.message.text or "پیام رسانه‌ای"
        else:
            # پیام معمولی
            text = update.message.text
            if not text or len(text.split()) < 2:
                update.message.reply_text("⚠️ فرمت اشتباه! مثال: 123456789 سلام")
                return
                
            target_id = int(text.split()[0])
            message = ' '.join(text.split()[1:])
            target_user = type('', (), {'id': target_id})  # ساخت شیء کاربر موقت

        # ارسال پیام
        context.bot.send_message(
            chat_id=target_user.id,
            text=f"📩 پیام ناشناس:\n\n{message}"
        )
        update.message.reply_text("✅ پیام ارسال شد!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("❌ خطا در ارسال پیام!")

def main():
    # دریافت توکن از متغیر محیطی
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        logger.error("لطفا TELEGRAM_TOKEN را تنظیم کنید!")
        return

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # ثبت هندلرها
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # شروع ربات
    updater.start_polling()
    logger.info("ربات شروع به کار کرد...")
    updater.idle()

if __name__ == '__main__':
    main()
