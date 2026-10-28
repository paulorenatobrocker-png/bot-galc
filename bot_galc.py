import os
from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot GALC online!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_flask, daemon=True).start()

# DAQUI PRA BAIXO SEU CÓDIGO ANTIGO DO BOT
import math
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

import os
TOKEN = os.getenv("TOKEN")

SLOT, PORT = range(2)

teclado = [["GALC -> ICX", "FIBRA -> DGO"], ["DGO -> FIBRA"]]
markup = ReplyKeyboardMarkup(teclado, resize_keyboard=True)

def calc_galc(slot_galc, port_galc):
    pon = (slot_galc * 16 + port_galc - 16)
    slot_icx = math.ceil(pon / 24)
    port_icx = pon - ((slot_icx - 1) * 24)
    return pon, slot_icx, port_icx

def calc_fibra(fibra):
    slot = math.ceil(fibra / 24)
    port = fibra - ((slot - 1) * 24)
    return slot, port

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 GALC - Escolha:", reply_markup=markup)

async def escolha_galc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['modo'] = 'galc'
    await update.message.reply_text("Digite o SLOT GALC:")
    return SLOT

async def escolha_fibra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['modo'] = 'fibra'
    await update.message.reply_text("Digite a FIBRA:")
    return PORT

async def escolha_dgo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['modo'] = 'dgo'
    await update.message.reply_text("Digite o SLOT DGO:")
    return SLOT

async def receber_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
 texto = update.message.text.strip()
# aceita tanto "4" quanto "1-1-4-12" ou "4-12"
context.user_data['slot'] = texto
try:
    # tenta salvar como número se for só um número
    slot_num = int(texto.split('-')[0])
    context.user_data['slot_num'] = slot_num
except:
    pass
    msg = "SLOT OK! Agora digite a PORTA:"
    await update.message.reply_text(msg)
    return PORT

async def receber_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modo = context.user_data['modo']
    if modo == 'fibra':
        fibra = int(update.message.text)
        slot, port = calc_fibra(fibra)
        await update.message.reply_text(f"🔄 FIBRA {fibra}\n➡️ DGO: SLOT {slot} PORT {port}", reply_markup=markup)
        return ConversationHandler.END
    
    slot = context.user_data['slot']
    port = int(update.message.text)

    if modo == 'galc':
        pon, slot_icx, port_icx = calc_galc(slot, port)
        await update.message.reply_text(f"✅ GALC {slot}/{port}\n➡️ ICX: SLOT {slot_icx} PORT {port_icx}", reply_markup=markup)
    else:
        fibra = (slot - 1) * 24 + port
        await update.message.reply_text(f"✅ DGO {slot}/{port}\n➡️ FIBRA: {fibra}", reply_markup=markup)
    return ConversationHandler.END

app = Application.builder().token(TOKEN).build()
conv = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^GALC -> ICX$"), escolha_galc),
        MessageHandler(filters.Regex("^FIBRA -> DGO$"), escolha_fibra),
        MessageHandler(filters.Regex("^DGO -> FIBRA$"), escolha_dgo),
    ],
    states={
        SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_slot)],
        PORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_port)],
    },
    fallbacks=[],
)
app.add_handler(CommandHandler("start", start))
app.add_handler(conv)
app.run_polling()
