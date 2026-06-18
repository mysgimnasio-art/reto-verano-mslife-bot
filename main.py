import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def hola(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot Reto Verano MSLIFE FIT funcionando correctamente.")

async def main():
    if not TOKEN:
        raise RuntimeError("Falta la variable BOT_TOKEN en Render")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("hola", hola))

    print("Bot iniciado correctamente...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
