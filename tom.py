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
                if "maintenance" not in content:
                    content["maintenance"] = False
                return content
        except: pass
    return {"users": {}, "banned": [], "maintenance": False}

def save_data(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- HELPER: Extract ID from Message ---
def extract_id(text):
    if not text: return None
    match = re.search(r"🆔 ID: (\d+)", text)
    return int(match.group(1)) if match else None

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🛠 **Bot Under Maintenance**\nWe are updating the bot. Please try again later.")
        return

    if user.id in data["banned"]:
        await update.message.reply_text("🚫 **Access Denied!**\nYou have been banned from using this bot.")
        return
    
    # Username check: Agar nahi hai toh sirf "None" (No link)
    username_text = f"@{user.username}" if user.username else "None"
    
    data["users"][str(user.id)] = {
        "name": user.first_name, 
        "username": username_text
    }
    save_data(data)
    await update.message.reply_text("Welcome to the TOM Bot! 🤖\n🙌You can send your messages here, and the owner will reply soon.🙌")

async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = True
    save_data(data)
    await update.message.reply_text("🚧 **Maintenance Mode: ON**")

async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = False
    save_data(data)
    await update.message.reply_text("✅ **Maintenance Mode: OFF**")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    total_users = len(data["users"])
    banned_count = len(data["banned"])
    m_status = "ON 🚧" if data.get("maintenance") else "OFF ✅"
    
    user_list_text = ""
    if data["users"]:
        for uid, info in data["users"].items():
            status = "🚫" if int(uid) in data["banned"] else "✅"
            user_list_text += f"{status} **{info['name']}** | {info['username']} | ID: `{uid}`\n"
    else:
        user_list_text = "No users found."

    final_msg = (
        f"📊 **BOT STATISTICS**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: {total_users}\n"
        f"🚫 Banned: {banned_count}\n"
        f"🛠 Maintenance: {m_status}\n\n"
        f"📜 **USER LIST:**\n"
        f"{user_list_text}"
    )
    await update.message.reply_text(final_msg[:4096], parse_mode='Markdown')

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
            try: await context.bot.send_message(chat_id=target_id, text="🚫 You have been banned by the owner.")
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
    msg_to_send = " ".join(context.args)
    if not msg_to_send:
        await update.message.reply_text("Usage: /all [message]")
        return
    
    count = 0
    for uid in list(data["users"].keys()):
        try:
            user_id = int(uid)
            if user_id not in data["banned"]:
                await context.bot.send_message(chat_id=user_id, text=f"📢 **ANNOUNCEMENT**\n\n{msg_to_send}", parse_mode='Markdown')
                count += 1
        except: continue
    await update.message.reply_text(f"✅ Message sent to {count} users.")

# --- MESSAGE HANDLER ---
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🛠 **Maintenance Alert**\nBot is currently under maintenance.")
        return

    if user.id in data["banned"]:
        await update.message.reply_text("❌ **Access Denied!**")
        return

    if user.id == ADMIN_ID:
        if update.message.reply_to_message:
            if update.message.text and update.message.text.startswith("/"): return
            target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
            if target_id:
                await update.message.copy(chat_id=target_id)
                await update.message.reply_text("✅ Sent!")
        return

    # Username check for Admin header
    username_display = f"@{user.username}" if user.username else "None"

    header = f"📩 **NEW MESSAGE**\n\n👤 Name: {user.first_name}\n🆔 ID: {user.id}\n🔗 User: {username_display}\n⚡ [Open Chat](tg://user?id={user.id})"
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("Sent! The owner will reply soon.")

def main():
    PORT = int(os.environ.get('PORT', 8443))
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("all", send_all))
    app.add_handler(CommandHandler("maintenance_on", maintenance_on))
    app.add_handler(CommandHandler("maintenance_off", maintenance_off))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN, 
                        webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    else: app.run_polling()

if __name__ == '__main__':
    main()
