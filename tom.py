import logging
import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM"
ADMIN_ID = 6169350961 

# Database File
USERS_FILE = "users_data.json"

def load_data():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "banned": [], "maintenance": False}

def save_data(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- MAINTENANCE COMMANDS ---
async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = True
    save_data(data)
    await update.message.reply_text("🚧 **Maintenance Mode ON:** Ab users ko maintenance ka message jayega.")

async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = False
    save_data(data)
    await update.message.reply_text("✅ **Maintenance Mode OFF:** Bot ab normal kaam kar raha hai.")

# --- OTHER COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ **Bot Under Maintenance:** Hum kuch naya update kar rahe hain, thodi der baad koshish karein.")
        return
    if user.id in data["banned"]:
        await update.message.reply_text("🚫 You Are Banned nikal bkl .")
        return
    data["users"][str(user.id)] = {"name": user.first_name, "username": f"@{user.username}"}
    save_data(data)
    await update.message.reply_text("Welcome to Tom Bot! 🤖")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = "👥 **Users List:**\n"
    for uid, info in data["users"].items():
        text += f"👤 {info['name']} | {info['username']} | `{uid}`\n"
    await update.message.reply_text(text[:4096], parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    m_status = "ON 🚧" if data.get("maintenance") else "OFF ✅"
    await update.message.reply_text(f"📊 **Stats:**\nUsers: {len(data['users'])}\nBanned: {len(data['banned'])}\nMaintenance: {m_status}")

# --- MESSAGE HANDLER ---
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Maintenance Check
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🛠 **Maintenance Alert:** Bot abhi maintenance mein hai. Owner abhi kaam kar rahe hain. Jaldi wapas aayenge!")
        return

    if user.id in data["banned"]:
        await update.message.reply_text("❌ YOU ARE BANNED, NIKAL bkl.")
        return

    if user.id == ADMIN_ID:
        if update.message.reply_to_message:
            if update.message.text and update.message.text.startswith("/"): return
            try:
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
                target_id = int(reply_text.split("🆔 ID: ")[1].split("\n")[0])
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Sent!")
            except: pass
        return

    header = f"📩 **NEW MESSAGE**\n\n👤 Name: {user.first_name}\n🆔 ID: {user.id}\n⚡ [Chat](tg://user?id={user.id})"
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)

def main():
    PORT = int(os.environ.get('PORT', 8443))
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("maintenance_on", maintenance_on))
    app.add_handler(CommandHandler("maintenance_off", maintenance_off))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN, webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    else: app.run_polling()

if __name__ == '__main__':
    main()
