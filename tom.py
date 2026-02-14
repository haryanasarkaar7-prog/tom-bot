import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM" # Apna token yahan dalein
ADMIN_ID = 6169350961 # Apna Telegram ID yahan dalein

# Users ki list (Memory mein save hogi)
all_users = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. Welcome Message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    all_users.add(user_id)
    await update.message.reply_text("Welcome to Tom Bot! 🤖\n\nAap mujhse yahan baat kar sakte hain. Koi rules ya limits nahi hain.")

# 2. Universal Message Handler (Text, Photo, Video, Voice, etc.)
async def handle_incoming_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "No Username"
    
    # Agar Admin Reply kar raha hai (Swipe Reply Logic)
    if user_id == ADMIN_ID:
        if update.message.reply_to_message:
            try:
                # Reply text se User ID nikalna
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
                target_user_id = int(reply_text.split("ID: ")[1].split("\n")[0])
                
                # Admin ka message user ko bhejna
                await update.message.copy(chat_id=target_user_id)
                await update.message.reply_text("✅ Delivered to user.")
            except Exception:
                await update.message.reply_text("❌ Error: User ID nahi mili. Kya aapne sahi message par reply kiya?")
        else:
            await update.message.reply_text("Sir, user ko jawab dene ke liye unke message par 'Swipe/Reply' karein.")
        return

    # Agar User message kar raha hai Admin ko
    all_users.add(user_id)
    info_header = f"📩 NEW MESSAGE\n👤 Name: {name}\n🆔 ID: {user_id}\n🔗 User: {username}\n"
    
    # Pehle user ki info bhejna phir unka content
    await context.bot.send_message(chat_id=ADMIN_ID, text=info_header)
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("Sent! Owner aapko jaldi reply karenge.")

# 3. Broadcast Command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    msg_to_send = " ".join(context.args)
    if not msg_to_send:
        await update.message.reply_text("Usage: /broadcast [message]")
        return

    success, fail = 0, 0
    for user in list(all_users):
        try:
            await context.bot.send_message(chat_id=user, text=f"📢 MESSAGE FROM OWNER:\n\n{msg_to_send}")
            success += 1
        except:
            fail += 1
    
    await update.message.reply_text(f"📊 Broadcast Report:\n✅ Sent: {success}\n❌ Failed: {fail}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    # Sab kuch handle karne ke liye (Text, Photo, Video, Audio, Document)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming_content))

    print("Tom Bot is live with Media Support...")
    app.run_polling()

if __name__ == '__main__':
    main()