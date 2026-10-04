# app/integrations/telegram_client.py
import httpx

from app.core.config import settings


def _base() -> str:
    tok = (settings.TELEGRAM_TOKEN or "").strip().strip('"')
    if not tok:
        raise RuntimeError("TELEGRAM_TOKEN is not set")
    return f"https://api.telegram.org/bot{tok}"


async def send_telegram_message(chat_id: str, text: str, buttons: list | None = None, parse_mode: str | None = "Markdown"):
    payload = {"chat_id": chat_id, "text": text[:4000]}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{_base()}/sendMessage", json=payload)
        data = r.json()
        if not data.get("ok") and parse_mode:
            # Markdown can fail on model text with stray *_[ characters; retry as plain text
            payload.pop("parse_mode", None)
            data = (await client.post(f"{_base()}/sendMessage", json=payload)).json()
    return data


async def answer_callback(callback_id: str, text: str = ""):
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{_base()}/answerCallbackQuery", json={"callback_query_id": callback_id, "text": text[:180]})


async def set_webhook(url: str, secret: str | None = None):
    body = {"url": url, "allowed_updates": ["message", "callback_query"]}
    if secret:
        body["secret_token"] = secret
    async with httpx.AsyncClient(timeout=10) as client:
        return (await client.post(f"{_base()}/setWebhook", json=body)).json()


async def get_me():
    async with httpx.AsyncClient(timeout=10) as client:
        return (await client.get(f"{_base()}/getMe")).json()
