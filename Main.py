import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
PORT = int(os.environ.get("PORT", 10000))

waiting_users = []
active_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Random chat shuru karne ke liye /next dabao.\n"
        "/stop - chat khatam karo\n"
        "/report - partner ko report karo"
    )

async def next_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await update.message.reply_text("Pehle /stop dabao current chat khatam karne ke liye.")
        return
    if user_id in waiting_users:
        await update.message.reply_text("Already wait kar rahe ho... thoda ruko.")
        return
    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await context.bot.send_message(user_id, "✅ Partner mil gaya! Baat karo (identity hidden hai).")
        await context.bot.send_message(partner_id, "✅ Partner mil gaya! Baat karo (identity hidden hai).")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("🔍 Partner dhoonda ja raha hai...")

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("Search cancel ho gaya.")
        return
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(partner_id, "❌ Partner ne chat chhod di. /next dabao naya partner ke liye.")
        await update.message.reply_text("Chat khatam. /next dabao naya partner ke liye.")
    else:
        await update.message.reply_text("Koi active chat nahi hai.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await context.bot.send_message(ADMIN_ID, f"⚠️ Report: User {user_id} ne partner {partner_id} ko report kiya.")
        await update.message.reply_text("Report admin ko bhej diya gaya hai. Dhanyawad.")
    else:
        await update.message.reply_text("Abhi koi active chat nahi hai report karne ke liye.")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await context.bot.send_message(partner_id, update.message.text)
    else:
        await update.message.reply_text("Koi partner nahi hai. /next dabao.")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")
    def log_message(self, format, *args):
        pass

def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("next", next_user))
app.add_handler(CommandHandler("stop", stop_chat))
app.add_handler(CommandHandler("report", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

app.run_polling()
