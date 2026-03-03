import requests
import os

print("Test mesajı gönderiliyor")

requests.post(
    f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
    data={
        "chat_id": os.environ["TELEGRAM_CHAT_ID"],
        "text": "🔥 TEST MESAJI - Sistem çalışıyor"
    }
)
