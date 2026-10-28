import math
import re
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

def extrair_numeros(texto):
    # pega todos os numeros de "1-1-4-12" -> [1,1,4,12]
    return list(map(int, re.findall(r'\d+', texto)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 GALC - Escolha:", reply_markup=markup)

async def escolha_galc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['modo'] = 'galc'
    await update.message.reply_text("Digite o SLOT GALC (pode ser 4 ou 1-1-4-12):")
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
    numeros = extrair_numeros(texto)

    if not numeros:
        await update.message.reply_text("Digite só números! Ex: 4 ou 1-1-4-12")
        return SLOT

    # Se mandou completo tipo 1-1-4-12 ou 4-12
    if len(numeros) >= 2:
        slot = numeros[-2]
        port = numeros[-1]
        context.user_data['slot'] = slot
        
        modo = context.user_data['modo']
        if modo == 'galc':
            pon, slot_icx, port_icx = calc_galc(slot, port)
            await update.message.reply_text(f"✅ GALC {slot}/{port}\n➡️ ICX: SLOT {slot_icx} PORT {port_icx}", reply_markup=markup)
        else:
            fibra = (slot - 1) * 24 + port
            await update.message.reply_text(f"✅ DGO {slot}/{port}\n➡️ FIBRA: {fibra}", reply_markup=markup)
        return ConversationHandler.END

    # Se mandou só o SLOT (ex: 4)
    context.user_data['slot'] = numeros[0]
    await update.message.reply_text("SLOT OK! Agora digite a PORTA:")
    return PORT

async def receber_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modo = context.user_data['modo']
    texto = update.message.text.strip()
    numeros = extrair_numeros(texto)

    if not numeros:
        await update.message.reply_text("Digite só números!")
        return PORT

    if modo == 'fibra':
        fibra = numeros[-1] # pega o ultimo numero
        slot, port = calc_fibra(fibra)
        await update.message.reply_text(f"🔄 FIBRA {fibra}\n➡️ DGO: SLOT {slot} PORT {port}", reply_markup=markup)
        return ConversationHandler.END
    
    # Se no campo da porta mandou de novo "1-1-4-12"
    if len(numeros) >= 2:
        slot = numeros[-2]
        port = numeros[-1]
    else:
        slot = context.user_data['slot']
        port = numeros[0]

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

