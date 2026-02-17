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

# --- DATA MANAGEMENT ---
def load_data():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                content = json.load(f)
                content["banned"] = [int(i) for i in content.get("banned", [])]
                if "users" not in content: content["users"] = {}
                if "maintenance" not in content: content["maintenance"] = False
                return content
        except Exception as e:
            logging.error(f"Error loading JSON: {e}")
    return {"users": {}, "banned": [], "maintenance": False}

def save_data(data_to_save):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving JSON: {e}")

data = load_data()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def extract_id(text):
    if not text: return None
    match = re.search(r"ID:\s*(\d+)", text)
    return int(match.group(1)) if match else None

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    global data
    data = load_data()

    if user.id in data["banned"]:
        await update.message.reply_text("🚫 **Access Denied!**\nYou are banned from using this bot.")
        return

    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🛠 **Maintenance Mode**\nPlease try again later.")
        return
    
    uid_str = str(user.id)
    username_display = f"@{user.username}" if user.username else "None"
    data["users"][uid_str] = {"name": user.first_name, "username": username_display}
    save_data(data)
    await update.message.reply_text("Welcome! TO The TOM Bot 🤖\nSend your message here.✔")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    current_data = load_data()
    user_list = "📜 **User List:**\n"
    for uid, info in current_data["users"].items():
        status = "🚫" if int(uid) in current_data["banned"] else "✅"
        user_list += f"{status} {info['name']} | {info['username']} | ID: `{uid}`\n"
    await update.message.reply_text(user_list[:4096], parse_mode='Markdown')

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to a message with /ban")
        return
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id:
        if target_id not in data["banned"]:
            data["banned"].append(target_id)
            save_data(data)
            try: await context.bot.send_message(chat_id=target_id, text="🚫 You have been banned.")
            except: pass
        await update.message.reply_text(f"🚫 User {target_id} BANNED.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply with /unban")
        return
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id and target_id in data["banned"]:
        data["banned"].remove(target_id)
        save_data(data)
        try: await context.bot.send_message(chat_id=target_id, text="✅ You have been unbanned.")
        except: pass
        await update.message.reply_text(f"✅ User {target_id} UNBANNED.")

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: return
    count = 0
    current_data = load_data()
    for uid in list(current_data["users"].keys()):
        try:
            if int(uid) not in current_data["banned"]:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 **ANNOUNCEMENT**\n\n{msg}")
                count += 1
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users.")

# --- MESSAGE HANDLER ---
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    global data
    data = load_data()

    # REPEATED BAN CHECK (Yahan change kiya hai)
    if user.id in data["banned"] and user.id != ADMIN_ID:
        await update.message.reply_text("🚫 **Access Denied!**\nYou have been banned from using this bot.")
        return

    # Maintenance Check
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🛠 Under Maintenance.")
        return

    if user.id == ADMIN_ID:
        if update.message.reply_to_message:
            if update.message.text and update.message.text.startswith("/"): return
            target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
            if target_id:
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Sent!")
        return

    # Auto-Register & Forward
    uid_str = str(user.id)
    username_disp = f"@{user.username}" if user.username else "None"
    if uid_str not in data["users"]:
        data["users"][uid_str] = {"name": user.first_name, "username": username_disp}
        save_data(data)

    header = f"📩 **NEW MESSAGE**\n\n👤 Name: {user.first_name}\n🆔 ID: {user.id}\n🔗 User: {username_disp}\n⚡ [Chat](tg://user?id={user.id})"
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("Sent! Owner will reply soon.")

def main():
    PORT = int(os.environ.get('PORT', 8443))
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("all", send_all))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN, webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    else: app.run_polling()

if __name__ == '__main__':
    main()
