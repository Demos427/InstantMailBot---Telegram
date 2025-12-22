import os
import logging
import json
import asyncio
import aiohttp
import random
import string
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    JobQueue,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

class JsonManager:
    def __init__(self):
        self.file_accounts = "comptes.json"
        self.file_messages = "messages.json"
        self._init_files()

    def _init_files(self):
        if not os.path.exists(self.file_accounts):
            with open(self.file_accounts, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)
        if not os.path.exists(self.file_messages):
            with open(self.file_messages, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)

    def _read_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_json(self, filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_account(self, user_id, email, service, auth_data):
        accounts = self._read_json(self.file_accounts)
        new_account = {
            "user_id": user_id,
            "email": email,
            "service": service,
            "auth_data": auth_data,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        accounts.append(new_account)
        self._write_json(self.file_accounts, accounts)

    def get_user_accounts(self, user_id, only_active=False):
        accounts = self._read_json(self.file_accounts)
        if only_active:
            return [acc for acc in accounts if acc['user_id'] == user_id and acc['is_active']]
        return [acc for acc in accounts if acc['user_id'] == user_id]

    def stop_account(self, user_id, email):
        accounts = self._read_json(self.file_accounts)
        found = False
        for acc in accounts:
            if acc['user_id'] == user_id and acc['email'] == email:
                acc['is_active'] = False
                found = True
        self._write_json(self.file_accounts, accounts)
        return found

    def delete_account_data(self, user_id, email):
        accounts = self._read_json(self.file_accounts)
        accounts = [acc for acc in accounts if not (acc['user_id'] == user_id and acc['email'] == email)]
        self._write_json(self.file_accounts, accounts)

        messages = self._read_json(self.file_messages)
        messages = [msg for msg in messages if msg['email_address'] != email]
        self._write_json(self.file_messages, messages)
        return True

    def save_message(self, email_address, sender, subject, body):
        messages = self._read_json(self.file_messages)
        for msg in messages:
            if (msg['email_address'] == email_address and 
                msg['subject'] == subject and 
                msg['body'] == body):
                return False 

        msg_id = int(datetime.now().timestamp() * 1000)
        
        new_message = {
            "id": msg_id,
            "email_address": email_address,
            "sender": sender,
            "subject": subject,
            "body": body,
            "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        messages.insert(0, new_message)
        self._write_json(self.file_messages, messages)
        return True

    def get_messages_by_email(self, email_address):
        messages = self._read_json(self.file_messages)
        return [msg for msg in messages if msg['email_address'] == email_address]

    def get_message_by_id(self, msg_id):
        messages = self._read_json(self.file_messages)
        for msg in messages:
            if msg.get('id') == int(msg_id):
                return msg
        return None

db = JsonManager()

class EmailService:
    async def create_account(self): raise NotImplementedError
    async def get_messages(self, auth_data): raise NotImplementedError

class GuerrillaMailService(EmailService):
    BASE_URL = "https://api.guerrillamail.com/ajax.php"
    async def create_account(self):
        async with aiohttp.ClientSession(headers=HEADERS_API) as session:
            params = {"f": "get_email_address"}
            async with session.get(self.BASE_URL, params=params) as resp:
                data = await resp.json()
                return {"email": data['email_addr'], "sid_token": data['sid_token']}
    async def get_messages(self, auth_data):
        async with aiohttp.ClientSession(headers=HEADERS_API) as session:
            params = {"f": "check_email", "seq": "0", "sid_token": auth_data['sid_token']}
            async with session.get(self.BASE_URL, params=params) as resp:
                data = await resp.json()
                return [{
                    "sender": msg.get('mail_from'),
                    "subject": msg.get('mail_subject'),
                    "body": msg.get('mail_excerpt', '') + "..."
                } for msg in data.get('list', [])]

class MailTmService(EmailService):
    BASE_URL = "https://api.mail.tm"
    async def create_account(self):
        async with aiohttp.ClientSession(headers=HEADERS_API) as session:
            username = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
            async with session.get(f"{self.BASE_URL}/domains") as resp:
                data = await resp.json()
                if isinstance(data, list): domain = data[0]['domain']
                elif 'hydra:member' in data: domain = data['hydra:member'][0]['domain']
                else: raise Exception("Format Mail.tm inconnu")
            email = f"{username}@{domain}"
            async with session.post(f"{self.BASE_URL}/accounts", json={"address": email, "password": password}) as resp:
                if resp.status != 201: raise Exception("Échec création compte")
            async with session.post(f"{self.BASE_URL}/token", json={"address": email, "password": password}) as resp:
                token = (await resp.json())['token']
            return {"email": email, "token": token}
    async def get_messages(self, auth_data):
        auth_header = HEADERS_API.copy()
        auth_header["Authorization"] = f"Bearer {auth_data['token']}"
        async with aiohttp.ClientSession(headers=auth_header) as session:
            async with session.get(f"{self.BASE_URL}/messages") as resp:
                if resp.status != 200: return []
                data = await resp.json()
                msgs = data if isinstance(data, list) else data.get('hydra:member', [])
                return [{
                    "sender": msg.get('from', {}).get('address', 'Inconnu'),
                    "subject": msg.get('subject', 'Sans sujet'),
                    "body": msg.get('intro', '')
                } for msg in msgs]

SERVICES = {"guerrilla": GuerrillaMailService(), "mailtm": MailTmService()}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🦍 Guerrilla", callback_data="svc_guerrilla"), 
         InlineKeyboardButton("🛡️ Mail.tm", callback_data="svc_mailtm")],
        [InlineKeyboardButton("🛑 Arrêter", callback_data="menu_stop"),
         InlineKeyboardButton("🗑️ Supprimer", callback_data="menu_delete")],
        [InlineKeyboardButton("📂 Explorer Historique", callback_data="hist_menu")]
    ]
    text = "🤖 **TempMailBot**\nBienvenue. Que voulez-vous faire ?"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📚 **Aide**\n`/start` : Menu\n`/stop` : Pause\n`/delete` : Supprimer\n`/history` : Lire les mails"
    await update.message.reply_text(text, parse_mode="Markdown")

async def history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    all_accounts = db.get_user_accounts(user_id, only_active=False)
    
    if not all_accounts:
        msg = "📭 Aucun compte créé."
        if update.callback_query: await update.callback_query.edit_message_text(msg)
        else: await update.message.reply_text(msg)
        return

    keyboard = []
    for acc in all_accounts:
        msgs = db.get_messages_by_email(acc['email'])
        count = len(msgs)
        keyboard.append([InlineKeyboardButton(f"📂 {acc['email']} ({count})", callback_data=f"hlist_{acc['email']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Menu Principal", callback_data="start")])
    text = "📂 **Historique**\nChoisissez une adresse pour voir ses messages :"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def history_list(update: Update, context: ContextTypes.DEFAULT_TYPE, email):
    msgs = db.get_messages_by_email(email)
    
    if not msgs:
        text = f"📭 **Boîte vide** : `{email}`"
        keyboard = [[InlineKeyboardButton("🔙 Retour Comptes", callback_data="hist_menu")]]
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    keyboard = []
    for msg in msgs[:10]:
        btn_text = f"📩 {msg['subject'][:30]}..." if msg['subject'] else "📩 Sans sujet"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"hread_{msg['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Retour Comptes", callback_data="hist_menu")])
    
    text = f"📂 **Messages pour :** `{email}`\nCliquez sur un message pour le lire en entier."
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def history_read(update: Update, context: ContextTypes.DEFAULT_TYPE, msg_id):
    msg = db.get_message_by_id(msg_id)
    
    if not msg:
        await update.callback_query.answer("Message introuvable ou supprimé.", show_alert=True)
        return

    keyboard = [[InlineKeyboardButton("🔙 Retour Liste", callback_data=f"hlist_{msg['email_address']}")]]
    
    text = (
        f"📨 **Lecture du Message**\n\n"
        f"📅 **Reçu le :** {msg['received_at']}\n"
        f"👤 **De :** `{msg['sender']}`\n"
        f"📝 **Sujet :** {msg['subject']}\n"
        f"{'—'*20}\n\n"
        f"{msg['body']}"
    )
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n[...Message tronqué par Telegram...]"

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def stop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    active = db.get_user_accounts(user_id, only_active=True)
    if not active:
        await update.callback_query.edit_message_text("🛑 Rien à arrêter.")
        return
    keyboard = [[InlineKeyboardButton(f"🛑 {acc['email']}", callback_data=f"stop_{acc['email']}")] for acc in active]
    keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="start")])
    await update.callback_query.edit_message_text("🛑 **Stop Surveillance** :", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    all_acc = db.get_user_accounts(user_id)
    if not all_acc:
        await update.callback_query.edit_message_text("🗑️ Rien à supprimer.")
        return
    keyboard = [[InlineKeyboardButton(f"🗑️ {acc['email']}", callback_data=f"del_{acc['email']}")] for acc in all_acc]
    keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="start")])
    await update.callback_query.edit_message_text("⚠️ **Suppression Totale** :", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def check_mail_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.chat_id
    service = SERVICES.get(job.data['service_name'])
    email = job.data['email']
    try:
        messages = await service.get_messages(job.data['auth_data'])
        for msg in messages:
            if db.save_message(email, msg['sender'], msg['subject'], msg['body']):
                text = (f"📨 **Nouveau Mail !**\n📬 `{email}`\n👤 `{msg['sender']}`\n📝 {msg['subject']}\n\n"
                        f"Aller dans /history pour lire le contenu complet.")
                await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Check error {email}: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start": await start(update, context); return
    if data == "menu_stop": await stop_menu(update, context); return
    if data == "menu_delete": await delete_menu(update, context); return
    
    if data == "hist_menu": await history_menu(update, context); return
    if data.startswith("hlist_"): 
        await history_list(update, context, data.split("hlist_")[1])
        return
    if data.startswith("hread_"): 
        await history_read(update, context, data.split("hread_")[1])
        return

    if data.startswith("stop_"):
        email = data.split("stop_")[1]
        for job in context.job_queue.get_jobs_by_name(f"{update.effective_user.id}_{email}"): job.schedule_removal()
        db.stop_account(update.effective_user.id, email)
        await query.edit_message_text(f"🛑 Arrêté : `{email}`", parse_mode="Markdown")
        return

    if data.startswith("del_"):
        email = data.split("del_")[1]
        for job in context.job_queue.get_jobs_by_name(f"{update.effective_user.id}_{email}"): job.schedule_removal()
        db.delete_account_data(update.effective_user.id, email)
        await query.edit_message_text(f"🗑️ Supprimé : `{email}`", parse_mode="Markdown")
        return

    if data.startswith("svc_"):
        svc = data.split("_")[1]
        await query.edit_message_text("⚙️ Création...")
        try:
            auth = await SERVICES[svc].create_account()
            email = auth['email']
            uid = update.effective_user.id
            db.add_account(uid, email, svc, auth)
            context.job_queue.run_repeating(check_mail_job, 15, first=1, chat_id=uid, name=f"{uid}_{email}", data={'service_name': svc, 'auth_data': auth, 'email': email})
            await query.edit_message_text(f"✅ **Créé** : `{email}`", parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(f"❌ Erreur : {e}")

async def post_init(app: Application):
    with open("comptes.json", 'r') as f: all_accs = json.load(f)
    for acc in all_accs:
        if acc.get('is_active'):
            app.job_queue.run_repeating(check_mail_job, 15, first=10, chat_id=acc['user_id'], name=f"{acc['user_id']}_{acc['email']}", data={'service_name': acc['service'], 'auth_data': acc['auth_data'], 'email': acc['email']})

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler(["start", "history"], start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot en ligne.")
    app.run_polling()

if __name__ == "__main__":
    main()