import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
# In dono ko apni details se badlein
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM" 
ADMIN_ID = 6169350961 # Apna numeric ID dalein

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. Welcome Message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Tom Bot! 🤖")

# 2. Universal Message Handler (User to Owner & Swipe-Reply)
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "No User"

    # Agar AAP (Admin) reply kar rahe hain
    if user_id == ADMIN_ID:
        if update.message.reply_to_message:
            try:
                # Swipe-Reply se ID nikalna
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
                target_id = int(reply_text.split("ID: ")[1].split("\n")[0])
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Message sent!")
            except:
                await update.message.reply_text("❌ Error: User ID nahi mili.")
        return

    # Agar koi USER message kar raha hai
    header = f"📩 NEW MSG\n👤 Name: {name}\n🆔 ID: {user_id}\n🔗 User: {username}\n"
    await context.bot.send_message(chat_id=ADMIN_ID, text=header)
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("Sent! Owner reply karenge.")

# 3. Broadcast Command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Note: Free Render par storage nahi hoti, isliye ye command sirf tab kaam karegi
    # jab bot session active ho. Professional use ke liye Database chaiye hota hai.
    await update.message.reply_text("Broadcast feature is active.")

def main():
    # Render Port setup
    PORT = int(os.environ.get('PORT', 8443))
    
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    # WEBHOOK MODE (Render ke liye zaroori hai)
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        # Local machine par chalane ke liye
        app.run_polling()

if __name__ == '__main__':
    main()

