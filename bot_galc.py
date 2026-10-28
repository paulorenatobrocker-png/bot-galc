import math
import re
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

TOKEN = os.getenv("TOKEN")
SLOT, PORT = range(2)
teclado = [["GALC -> ICX", "FIBRA -> DGO"], ["DGO -> FIBRA"]]
markup = ReplyKeyboardMarkup(teclado, resize_keyboard=True)

def calc_galc(s, p):
    pon = (s * 16 + p - 16)
    si = math.ceil(pon / 24)
    pi = pon - ((si - 1) * 24)
    return pon, si, pi

def calc_fibra(f):
    s = math.ceil(f / 24)
    p = f - ((s - 1) * 24)
    return s, p

def validar(t):
    return int(t) if re.fullmatch(r'\d+', t.strip()) else None

async def start(u,c): await u.message.reply_text("👋 GALC - Escolha:", reply_markup=markup)
async def escolha_galc(u,c):
    c.user_data['modo']='galc'; await u.message.reply_text("Digite o SLOT:"); return SLOT
async def escolha_fibra(u,c):
    c.user_data['modo']='fibra'; await u.message.reply_text("Digite a FIBRA:"); return PORT
async def escolha_dgo(u,c):
    c.user_data['modo']='dgo'; await u.message.reply_text("Digite o SLOT:"); return SLOT
async def receber_slot(update, context):
    v=validar(update.message.text)
    if v is None:
        await update.message.reply_text("Digite o SLOT:"); return SLOT
    context.user_data['slot']=v
    await update.message.reply_text("Digite a PORTA:"); return PORT
async def receber_port(update, context):
    modo=context.user_data['modo']
    v=validar(update.message.text)
    if v is None:
        if modo=='fibra': await update.message.reply_text("Digite a FIBRA:")
        else: await update.message.reply_text("Digite a PORTA:")
        return PORT
    if modo=='fibra':
        s,p=calc_fibra(v); await update.message.reply_text(f"🔄 FIBRA {v}\n➡️ DGO: SLOT {s} PORT {p}", reply_markup=markup); return ConversationHandler.END
    s=context.user_data['slot']; port=v
    if modo=='galc':
        pon,si,pi=calc_galc(s,port); await update.message.reply_text(f"✅ GALC {s}/{port}\n➡️ ICX: SLOT {si} PORT {pi}", reply_markup=markup)
    else:
        fibra=(s-1)*24+port; await update.message.reply_text(f"✅ DGO {s}/{port}\n➡️ FIBRA: {fibra}", reply_markup=markup)
    return ConversationHandler.END

# --- TRUQUE PRA FICAR LIVE DE GRAÇA NO RENDER ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"Bot ON")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# --- FIM DO TRUQUE ---

app=Application.builder().token(TOKEN).build()
conv=ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^GALC -> ICX$"), escolha_galc), MessageHandler(filters.Regex("^FIBRA -> DGO$"), escolha_fibra), MessageHandler(filters.Regex("^DGO -> FIBRA$"), escolha_dgo)],
    states={SLOT:[MessageHandler(filters.TEXT & ~filters.COMMAND, receber_slot)], PORT:[MessageHandler(filters.TEXT & ~filters.COMMAND, receber_port)]},
    fallbacks=[])
app.add_handler(CommandHandler("start", start)); app.add_handler(conv)
app.run_polling()
