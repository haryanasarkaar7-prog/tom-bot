import logging
import os
import json
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM"
ADMIN_ID = 6169350961 

USERS_FILE = "users_data.json"

def load_data():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"users": {}, "banned": [], "maintenance": False}

def save_data(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def extract_id(text):
    if not text: return None
    match = re.search(r"🆔 ID: (\d+)", text)
    return int(match.group(1)) if match else None

# --- UPDATED STATS COMMAND ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    total_users = len(data["users"])
    banned_users = len(data["banned"])
    
    # List taiyaar karna
    user_list_text = ""
    if data["users"]:
        for uid, info in data["users"].items():
            status = "🚫" if int(uid) in data["banned"] else "✅"
            user_list_text += f"{status} **{info['name']}** | {info['username']} | ID: `{uid}`\n"
    else:
        user_list_text = "No users found yet."

    final_msg = (
        f"📊 **BOT STATISTICS**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: {total_users}\n"
        f"🚫 Banned: {banned_users}\n"
        f"🚧 Maintenance: {'ON' if data.get('maintenance') else 'OFF'}\n\n"
        f"📜 **USER LIST:**\n"
        f"{user_list_text}"
    )
    
    # Telegram message limit check
    if len(final_msg) > 4096:
        await update.message.reply_text(f"📊 Stats: {total_users} users found. List bahut lambi hai, isliye pehle kuch dikha raha hoon:\n\n" + final_msg[:3000], parse_mode='Markdown')
    else:
        await update.message.reply_text(final_msg, parse_mode='Markdown')

# --- BAN COMMAND ---
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ User ke message par reply karke /ban likhein.")
        return
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id:
        if target_id not in data["banned"]:
            data["banned"].append(target_id)
            save_data(data)
            try: await context.bot.send_message(chat_id=target_id, text="🚫 You have been banned.")
            except: pass
        await update.message.reply_text(f"🚫 User {target_id} banned.")

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in data["banned"]: return
    data["users"][str(user.id)] = {"name": user.first_name, "username": f"@{user.username}" if user.username else "No Username"}
    save_data(data)
    await update.message.reply_text("Welcome to Tom Bot! 🤖")

async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in data["banned"]: return

    if user.id == ADMIN_ID:
        if update.message.reply_to_message:
            if update.message.text and update.message.text.startswith("/"): return
            target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
            if target_id:
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Sent!")
        return

    # Auto-register user
    data["users"][str(user.id)] = {"name": user.first_name, "username": f"@{user.username}" if user.username else "No Username"}
    save_data(data)

    header = f"📩 **NEW MESSAGE**\n\n👤 Name: {user.first_name}\n🆔 ID: {user.id}\n⚡ [Chat](tg://user?id={user.id})"
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)

def main():
    PORT = int(os.environ.get('PORT', 8443))
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN, webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    else: app.run_polling()

if __name__ == '__main__':
    main()
