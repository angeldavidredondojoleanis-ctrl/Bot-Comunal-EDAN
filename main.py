import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ==========================================
# 1. SERVIDOR WEB FLASK (KEEP-ALIVE PARA RENDER)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot EDAN Comunal activo y operando 24/7"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ==========================================
# 2. CONFIGURACIÓN DE CORREO (SMTP GMAIL)
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "edanbot6@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "hscb okea qezn clpn")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "botedancomunal@gmail.com")


def enviar_correo_alerta(reporte_texto):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Credenciales SMTP no configuradas en las variables de entorno.")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = "🚨 Nuevo Reporte EDAN Comunal Recibido"
        
        cuerpo = f"Se ha registrado un nuevo reporte EDAN a través del bot de Telegram:\n\n{reporte_texto}"
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Correo de alerta SMTP enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# ==========================================
# 3. LÓGICA DE LA CONVERSACIÓN DEL BOT (EDAN)
# ==========================================
MUNICIPIO, VEREDA, FAMILIAS, DANOS = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"¡Hola, {user_name}! Bienvenido al sistema de Evaluación de Daños y Análisis de Necesidades (EDAN) Comunal.\n\n"
        "Usa el comando /reportar para iniciar un nuevo formulario de emergencia."
    )

async def reportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor, ingresa el nombre del **Municipio** o localidad afectada:")
    return MUNICIPIO

async def recibir_municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['municipio'] = update.message.text
    await update.message.reply_text("Perfecto. Ahora ingresa el nombre de la **Vereda** o sector:")
    return VEREDA

async def recibir_vereda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['vereda'] = update.message.text
    await update.message.reply_text("¿Cuántas **familias afectadas** se estiman en la zona? (Ingresa un número):")
    return FAMILIAS

async def recibir_familias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['familias'] = update.message.text
    await update.message.reply_text("Describe brevemente los **daños principales** (ej. viviendas destruidas, vías blocadas, cultivos afectados):")
    return DANOS

async def recibir_danos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['danos'] = update.message.text
    
    # Recopilar consolidado del reporte
    data = context.user_data
    reporte_resumen = (
        f"📍 Municipio: {data.get('municipio')}\n"
        f"🏡 Vereda: {data.get('vereda')}\n"
        f"👥 Familias afectadas: {data.get('familias')}\n"
        f"⚠️ Daños reportados: {data.get('danos')}"
    )
    
    # Disparar envío de correo electrónico
    enviar_correo_alerta(reporte_resumen)
    
    await update.message.reply_text(
        "✅ **¡Reporte EDAN registrado y enviado con éxito!**\n\n"
        "La información ha sido transmitida correctamente al sistema de gestión.\n\n"
        f"{reporte_resumen}"
    )
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Proceso de reporte cancelado.")
    return ConversationHandler.END

# ==========================================
# 4. FUNCIÓN PRINCIPAL DE ARRANQUE
# ==========================================
def main():
    # 1. Encender primero el servidor Flask en segundo plano para abrir el puerto de Render
    keep_alive()
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN no está configurado en las variables de entorno.")
        return

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("reportar", reportar)],
        states={
            MUNICIPIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_municipio)],
            VEREDA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_vereda)],
            FAMILIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_familias)],
            DANOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_danos)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    print("Bot EDAN iniciado correctamente en modo Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
