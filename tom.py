import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM"
ADMIN_ID = 6169350961  # Aapka ID jo screenshot mein dikha tha

# Temporary Storage (Server restart par ye reset ho jayega)
users_list = set()
banned_users = set()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in banned_users: return
    users_list.add(user_id)
    await update.message.reply_text("Welcome to Tom Bot! 🤖")

# 2. Ban Command (Reply to a message)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if update.message.reply_to_message:
        try:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
            target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
            banned_users.add(target_id)
            await update.message.reply_text(f"🚫 User {target_id} has been BANNED.")
        except:
            await update.message.reply_text("❌ Error: ID nahi mili.")

# 3. Unban Command
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if update.message.reply_to_message:
        try:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
            target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
            if target_id in banned_users:
                banned_users.remove(target_id)
                await update.message.reply_text(f"✅ User {target_id} has been UNBANNED.")
        except:
            await update.message.reply_text("❌ Error: ID nahi mili.")

# 4. Main Message Handler
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in banned_users: return

    name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "No Username"
    user_link = f"tg://user?id={user_id}"

    if user_id == ADMIN_ID:
        if update.message.reply_to_message:
            if update.message.text in ["/ban", "/unban"]: return
            try:
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
                target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Sent!")
            except: pass
        return

    users_list.add(user_id)
    header = (
        f"📩 **NEW MESSAGE**\n\n"
        f"👤 **Name:** {name}\n"
        f"🆔 **ID:** {user_id}\n"
        f"🔗 **User:** {username}\n"
        f"⚡ **Direct Link:** [Open Chat]({user_link})"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("Sent! Owner will reply soon.")

# 5. Broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: return
    count = 0
    for u_id in list(users_list):
        try:
            if u_id not in banned_users:
                await context.bot.send_message(chat_id=u_id, text=f"📢 **BROADCAST**\n\n{msg}", parse_mode='Markdown')
                count += 1
        except: continue
    await update.message.reply_text(f"✅ Broadcast to {count} users done!")

def main():
    PORT = int(os.environ.get('PORT', 8443))
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN,
                        webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    else:
        app.run_polling()

if __name__ == '__main__':
    main()
