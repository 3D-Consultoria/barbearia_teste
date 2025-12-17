import requests
import os

def send_telegram_alert(message, level="info"):
    """
    Envia notificações para o Telegram da 3D Consultoria.
    """
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    topic_id = os.getenv("TELEGRAM_TOPIC_ID") 

    if not token or not chat_id:
        return

    icons = {
        "info": "✅ Sucesso",
        "warning": "⚠️ ATENÇÃO",
        "error": "🚨 FALHA CRÍTICA"
    }
    
    icon = icons.get(level, "ℹ️")
    text = f"*{icon}: Barbearia Teste*\n\n{message}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "message_thread_id": topic_id
    }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")