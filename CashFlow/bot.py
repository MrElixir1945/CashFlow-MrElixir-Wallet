import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import threading
import time

# --- KONFIGURASI ---
TOKEN = 'your_api_token'
PUBLIC_URL = 'Your_domain_from_tailsclae_or_anywhere' 

# --- SECURITY: HANYA ID INI YANG BOLEH PAKAI ---
ALLOWED_USER_ID = YourID # <--- GANTI DENGAN ID TELEGRAM KAMU (ANGKA)

bot = telebot.TeleBot(TOKEN)

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  type TEXT, 
                  amount INTEGER, 
                  description TEXT, 
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- HELPER ---
def format_rupiah(value):
    return f"Rp {value:,.0f}".replace(",", ".")

def get_saldo(user_id):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("SELECT sum(amount) FROM transactions WHERE user_id=? AND type='IN'", (user_id,))
    res_in = c.fetchone()[0] or 0
    c.execute("SELECT sum(amount) FROM transactions WHERE user_id=? AND type='OUT'", (user_id,))
    res_out = c.fetchone()[0] or 0
    conn.close()
    return res_in - res_out

def safe_delete(chat_id, message_id):
    try: bot.delete_message(chat_id, message_id)
    except: pass

def delete_later(chat_id, message_id, delay=3):
    def run():
        time.sleep(delay)
        safe_delete(chat_id, message_id)
    threading.Thread(target=run).start()

# --- MIDDLEWARE CHECK ---
def is_allowed(user_id):
    return str(user_id) == str(ALLOWED_USER_ID)

# --- MENU UTAMA ---
def show_main_menu(chat_id, message_id=None):
    saldo = get_saldo(chat_id)
    text = f"💳 **Mr Elixir Wallet**\n\nSaldo Saat Ini:\n🔥 *{format_rupiah(saldo)}*"
    
    markup = InlineKeyboardMarkup()
    btn_in = InlineKeyboardButton("Pemasukan 📥", callback_data="input_in")
    btn_out = InlineKeyboardButton("Pengeluaran 📤", callback_data="input_out")
    # Link Dashboard dengan UID
    btn_dash = InlineKeyboardButton("📊 Buka Dashboard", url=f"{PUBLIC_URL}/dashboard?uid={chat_id}")
    
    markup.row(btn_in, btn_out)
    markup.row(btn_dash)

    if message_id:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        except: bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_allowed(message.chat.id):
        bot.send_message(message.chat.id, "⛔ **Akses Ditolak!** Bot ini khusus Owner.")
        return
    show_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    if not is_allowed(user_id): return
    
    if call.data in ["input_in", "input_out"]:
        tipe = "IN" if call.data == "input_in" else "OUT"
        lbl = "📥 PEMASUKAN" if tipe == "IN" else "📤 PENGELUARAN"
        msg = bot.send_message(user_id, f"{lbl}\n\nFormat: `Nominal : Keterangan`\nContoh: `50.000 : Makan`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_transaction, tipe, call.message.message_id, msg.message_id)

    elif call.data == "back_menu":
        show_main_menu(user_id, call.message.message_id)

def process_transaction(message, trans_type, main_menu_id, prompt_msg_id):
    user_id = message.chat.id
    safe_delete(user_id, message.message_id)
    safe_delete(user_id, prompt_msg_id)

    try:
        if ":" not in message.text: raise ValueError
        parts = message.text.split(":", 1)
        amt_str = parts[0].strip().replace(".", "").replace(",", "").replace("Rp", "").replace("rp", "")
        if not amt_str.isdigit(): raise ValueError
        amount = int(amt_str)
        desc = parts[1].strip()

        conn = sqlite3.connect('finance.db')
        conn.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (?, ?, ?, ?)", (user_id, trans_type, amount, desc))
        conn.commit()
        conn.close()

        show_main_menu(user_id, main_menu_id)
        msg = bot.send_message(user_id, f"✅ Sukses: {format_rupiah(amount)} - {desc}")
        delete_later(user_id, msg.message_id, 3)

    except:
        msg = bot.send_message(user_id, "❌ **Format Salah!**\nContoh: `50.000 : Makan`", parse_mode="Markdown")
        delete_later(user_id, msg.message_id, 3)
        show_main_menu(user_id, main_menu_id)

print("Badawi Wallet Bot Started...")
bot.infinity_polling()
