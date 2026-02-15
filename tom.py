import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
# Inhe apni details se zaroor badlein
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM" 
ADMIN_ID = 6169350961  # Apna numeric ID yahan likhein

# Logging taaki error ka pata chale
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Tom Bot! 🤖")

# 2. Main Message Handler (Fix for Webhook & Direct Link)
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "No Username"
    
    # Direct Chat Link (Permanent ID based)
    user_link = f"tg://user?id={user_id}"

    # Agar Admin (Aap) Reply kar rahe hain
    if user_id == ADMIN_ID:
        if update.message.reply_to_message:
            try:
                # Header se ID extract karna
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
                target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
                
                # Admin ka message user ko copy karke bhejna
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Message sent!")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: User ID nahi mili ya format galat hai.")
        else:
            await update.message.reply_text("Sir, reply dene ke liye user ke message par 'Swipe-Reply' karein.")
        return

    # Agar User message kar raha hai (Admin ko detail bhejna)
    header = (
        f"📩 **NEW MESSAGE RECEIVED**\n\n"
        f"👤 **Name:** {name}\n"
        f"🆔 **ID:** {user_id}\n"
        f"🔗 **User:** {username}\n"
        f"⚡ **Direct Link:** [Open Chat]({user_link})"
    )
    
    # Admin ko header aur message bhejna
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("Sent! Owner aapko jaldi reply karenge.")

# 3. Broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Broadcast feature ready (Sessions based).")

def main():
    # Render Port Fix
    PORT = int(os.environ.get('PORT', 8443))
    
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    # WEBHOOK CONFIGURATION (Fixed for Render)
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    
    if RENDER_URL:
        # Jab Render par ho tab ye chalega
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        # Jab apne laptop/PC par test karein
        app.run_polling()

if __name__ == '__main__':
    main()
