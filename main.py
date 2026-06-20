import os
import json
import asyncio
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")

PUNTOS = {
    "#desayuno": 5,
    "#comida": 5,
    "#cena": 5,
    "#entreno": 10,
    "#retodiario": 10,
    "#peso": 10,
    "#motivacion": 5,
}

def conectar_sheets():
    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    cliente = gspread.authorize(creds)
    return cliente.open_by_key(SHEET_ID)

def buscar_participante(hoja, telegram_id):
    datos = hoja.get_all_records()
    for i, fila in enumerate(datos, start=2):
        if str(fila.get("telegram_id")) == str(telegram_id):
            return i, fila
    return None, None

def sumar_puntos(usuario_id, username, nombre, accion, puntos):
    libro = conectar_sheets()
    participantes = libro.worksheet("Participantes")
    registros = libro.worksheet("Registros")

    fila_num, participante = buscar_participante(participantes, usuario_id)

    if participante:
        puntos_actuales = int(participante.get("puntos_totales", 0))
        nuevo_total = puntos_actuales + puntos
        participantes.update_cell(fila_num, 4, nuevo_total)
    else:
        nuevo_total = puntos
        participantes.append_row([usuario_id, username, nombre, nuevo_total])

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    registros.append_row([fecha, usuario_id, username, nombre, accion, puntos])

    return nuevo_total

async def hola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot Reto Verano MSLIFE FIT funcionando correctamente.")

async def mispuntos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    libro = conectar_sheets()
    participantes = libro.worksheet("Participantes")

    fila_num, participante = buscar_participante(participantes, user.id)

    if not participante:
        await update.message.reply_text("Todavía no tienes puntos registrados.")
        return

    await update.message.reply_text(
        f"🏅 {user.first_name}, tienes {participante.get('puntos_totales', 0)} puntos."
    )

async def detectar_puntos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    texto = update.message.text.lower()
    user = update.effective_user

    puntos_sumados = 0
    acciones_detectadas = []

    for accion, puntos in PUNTOS.items():
        if accion in texto:
            puntos_sumados += puntos
            acciones_detectadas.append(accion)

    if puntos_sumados == 0:
        return

    username = f"@{user.username}" if user.username else ""
    nombre = user.full_name

    nuevo_total = sumar_puntos(
        user.id,
        username,
        nombre,
        ", ".join(acciones_detectadas),
        puntos_sumados
    )

    await update.message.reply_text(
        f"✅ {nombre} ha sumado {puntos_sumados} puntos.\n"
        f"Acción: {', '.join(acciones_detectadas)}\n"
        f"🏆 Total actual: {nuevo_total} puntos."
    )

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    libro = conectar_sheets()
    participantes = libro.worksheet("Participantes")
    datos = participantes.get_all_records()

    if not datos:
        await update.message.reply_text("Todavía no hay participantes con puntos.")
        return

    datos_ordenados = sorted(
        datos,
        key=lambda x: int(x.get("puntos_totales", 0)),
        reverse=True
    )

    mensaje = "🏆 Ranking Reto Verano MSLIFE FIT\n\n"

    for i, fila in enumerate(datos_ordenados[:10], start=1):
        nombre = fila.get("nombre", "Sin nombre")
        puntos = fila.get("puntos_totales", 0)
        mensaje += f"{i}. {nombre} - {puntos} puntos\n"

    await update.message.reply_text(mensaje)

async def main():
    def main():
    if not TOKEN:
        raise RuntimeError("Falta BOT_TOKEN")
    if not SHEET_ID:
        raise RuntimeError("Falta SHEET_ID")
    if not GOOGLE_CREDENTIALS:
        raise RuntimeError("Falta GOOGLE_CREDENTIALS")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("hola", hola))
    app.add_handler(CommandHandler("mispuntos", mispuntos))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detectar_puntos))

    print("Bot iniciado correctamente...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
