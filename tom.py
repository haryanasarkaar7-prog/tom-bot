import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM"
ADMIN_ID = 6169350961  # Apna numeric ID yahan likhein
MONGO_URL = "mongodb+srv://haryanasarkaar7_db_user:<db_password>@cluster0.1yid7so.mongodb.net/?appName=Cluster0"
# MongoDB Setup
client = MongoClient(MONGO_URL)
db = client['tom_bot_db']
users_col = db['users']
banned_col = db['banned_users']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Functions for DB
def save_user(user_id):
    if not users_col.find_one({"user_id": user_id}):
        users_col.insert_one({"user_id": user_id})

def is_banned(user_id):
    return banned_col.find_one({"user_id": user_id}) is not None

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id): return
    save_user(user_id)
    await update.message.reply_text("Welcome to Tom Bot! 🤖/nHow Mat I Help You Bro ?.")

# 2. Ban Command (Reply to user message)
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if update.message.reply_to_message:
        try:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
            target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
            if not is_banned(target_id):
                banned_col.insert_one({"user_id": target_id})
                await update.message.reply_text(f"🚫 User {target_id} has been BANNED.")
            else:
                await update.message.reply_text("User is already banned.")
        except:
            await update.message.reply_text("❌ Error: Could not find User ID.")

# 3. Unban Command (Reply to user message)
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if update.message.reply_to_message:
        try:
            reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
            target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
            banned_col.delete_one({"user_id": target_id})
            await update.message.reply_text(f"✅ User {target_id} has been UNBANNED.")
        except:
            await update.message.reply_text("❌ Error: Could not find User ID.")

# 4. Main Handler (Message Forwarding + Reply)
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "No Username"
    user_link = f"tg://user?id={user_id}"

    # Check if user is banned
    if is_banned(user_id):
        return

    # Admin Reply Logic
    if user_id == ADMIN_ID:
        if update.message.reply_to_message:
            # Agar reply mein command (/ban, /unban) hai toh forwarding skip karein
            if update.message.text in ["/ban", "/unban"]: return
            try:
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
                target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Sent!")
            except:
                pass
        return

    # User to Admin Forwarding
    save_user(user_id)
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
    users = users_col.find()
    count = 0
    for u in users:
        try:
            if not is_banned(u['user_id']):
                await context.bot.send_message(chat_id=u['user_id'], text=f"📢 **MESSAGE**\n\n{msg}", parse_mode='Markdown')
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





