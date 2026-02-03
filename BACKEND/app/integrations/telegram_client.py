# app/integrations/telegram_client.py

import os
import httpx

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

async def send_telegram_message(
    chat_id: str,
    text: str,
    buttons: list | None = None,
):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": buttons
        }

    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(
            f"{BASE_URL}/sendMessage",
            json=payload
        )

    return response.json()
