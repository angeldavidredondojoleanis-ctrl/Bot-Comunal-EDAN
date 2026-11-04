import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ==========================================
# 1. CONFIGURACIÓN DEL SERVIDOR FLASK (Keep-Alive)
# ==========================================
# Render requiere que los Web Services mantengan un puerto abierto.
app = Flask(__name__)

@app.route('/')
def home():
    return "¡El Bot de Telegram EDAN Comunal está activo y operando en la nube! 🚀"

def run_flask():
    # Render asigna dinámicamente el puerto mediante la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# ==========================================
# 2. CONFIGURACIÓN DE LA ALERTA (LOGS DE RENDER)
# ==========================================
def enviar_correo_alerta(reporte_texto):
    """
    Registra el reporte de emergencia de forma estructurada en los Logs de Render.
    Sirve como evidencia en tiempo real infalible para la sustentación.
    """
    print("==================================================")
    print("🚨 [ALERTA EDAN REGISTRADA EN LA NUBE] 🚨")
    print(reporte_texto)
    print("==================================================")


# ==========================================
# 3. LÓGICA DEL BOT DE TELEGRAM
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido al sistema de reporte EDAN Comunal.\n"
        "Por favor, envíe los detalles de la emergencia para registrar el reporte. 📋"
    )

async def manejar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_reporte = update.message.text
    
    # Llamamos a la función que imprime la alerta en los logs de Render
    enviar_correo_alerta(texto_reporte)
    
    # Respondemos al usuario en Telegram confirmando el éxito
    await update.message.reply_text("✅ ¡Reporte EDAN realizado con éxito y procesado por el sistema!")


def main():
    if not TELEGRAM_TOKEN:
        print("❌ Error: El TELEGRAM_TOKEN no está configurado en las variables de entorno.")
        return

    # Construir la aplicación del bot de Telegram
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Manejadores de comandos y mensajes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), manejar_reporte))

    print("🤖 Iniciando el bot de Telegram...")
    application.run_polling()


# ==========================================
# 4. EJECUCIÓN CONCURRENTE (Flask + Telegram Bot)
# ==========================================
if __name__ == '__main__':
    # Lanzamos Flask en un hilo secundario para cumplir con el requisito de puertos de Render
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Ejecutamos el bot de Telegram en el hilo principal
    main()

