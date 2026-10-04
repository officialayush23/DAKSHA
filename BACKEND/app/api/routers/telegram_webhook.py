# app/api/routers/telegram_webhook.py
"""
Telegram as a full DAKSHA channel.

Linking:  GET /user/telegram/link (signed in) -> https://t.me/<bot>?start=<signed token>
          The bot's /start <token> verifies the HMAC and links the chat to the account.
          (The old flow accepted any raw user UUID, so anyone could bind a chat to any account.)
Chat:     any text from a linked chat goes through the same orchestration graph
          (channel="telegram"), with the same unified context and per-agent memory
          as the web app and the kiosk.
Confirm:  customer approvals come back as inline buttons (approve/decline).
Security: POST /webhooks/telegram requires X-Telegram-Bot-Api-Secret-Token when
          WEBHOOK_SECRET is set (pass the same secret to setWebhook).
"""
import base64
import hashlib
import hmac
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_admin, get_current_user, get_db
from app.integrations import telegram_client as tg

router = APIRouter(tags=["Integrations"])
LINK_TTL_S = 15 * 60


def _key() -> bytes:
    return (settings.SUPABASE_JWT_SECRET + "::telegram-link").encode()


def make_link_token(user_id: str) -> str:
    exp = int(time.time()) + LINK_TTL_S
    raw = uuid.UUID(user_id).bytes + exp.to_bytes(4, "big")
    sig = hmac.new(_key(), raw, hashlib.sha256).digest()[:10]
    return base64.urlsafe_b64encode(raw + sig).decode().rstrip("=")   # 40 chars, Telegram allows 64


def read_link_token(token: str) -> Optional[str]:
    try:
        b = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        raw, sig = b[:20], b[20:]
        if not hmac.compare_digest(sig, hmac.new(_key(), raw, hashlib.sha256).digest()[:10]):
            return None
        if int.from_bytes(raw[16:20], "big") < time.time():
            return None
        return str(uuid.UUID(bytes=raw[:16]))
    except Exception:
        return None


@router.get("/user/telegram/link")
async def telegram_link(user=Depends(get_current_user)):
    me = await tg.get_me()
    bot = me.get("result", {}).get("username")
    if not bot:
        raise HTTPException(503, "Telegram bot unavailable")
    return {"url": f"https://t.me/{bot}?start={make_link_token(str(user.id))}", "expires_in": LINK_TTL_S}


@router.post("/admin/agentic/telegram/set-webhook")
async def telegram_set_webhook(public_base_url: str, admin=Depends(get_current_admin)):
    return await tg.set_webhook(public_base_url.rstrip("/") + "/webhooks/telegram", settings.WEBHOOK_SECRET or None)


def _chat_session_for(db: Session, user_id: str) -> str:
    row = db.execute(text("""SELECT id FROM chat_sessions WHERE user_id = :u AND channel = 'telegram' AND is_active
                             ORDER BY updated_at DESC LIMIT 1"""), {"u": user_id}).first()
    if row:
        return str(row.id)
    from app.services.chat_session_service import create_session
    return str(create_session(db, user_id, "telegram").id)


def _buttons_for(approval: dict):
    if not approval or approval.get("approver") != "customer":
        return None
    aid = approval["approval_id"]
    return [[{"text": "✅ Confirm", "callback_data": f"ok:{aid}"}, {"text": "✖ Cancel", "callback_data": f"no:{aid}"}]]


@router.post("/webhooks/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db),
                           x_telegram_bot_api_secret_token: Optional[str] = Header(default=None)):
    if settings.WEBHOOK_SECRET and x_telegram_bot_api_secret_token != settings.WEBHOOK_SECRET:
        raise HTTPException(401, "bad secret")
    data = await request.json()
    from app.agentic.runtime import resume, run_turn
    from app.services.chat_session_service import append_message

    # inline-button decisions
    if "callback_query" in data:
        cq = data["callback_query"]
        chat_id = str(cq["message"]["chat"]["id"])
        link = db.execute(text("SELECT user_id FROM telegram_users WHERE chat_id = :c"), {"c": chat_id}).first()
        kind, _, aid = (cq.get("data") or "").partition(":")
        row = db.execute(text("SELECT * FROM agent_approvals WHERE id = :a"), {"a": aid}).mappings().first()
        if not link or not row or str(row["user_id"]) != str(link.user_id) or row["status"] != "pending":
            await tg.answer_callback(cq["id"], "This request has expired.")
            return {"ok": True}
        await tg.answer_callback(cq["id"], "Got it")
        out = await resume(thread_id=row["thread_id"], approval_id=aid, approved=(kind == "ok"), by=str(link.user_id))
        append_message(db, row["thread_id"], "assistant", out["reply"], ui_data={"_agentic": {"plan": out.get("plan")}})
        await tg.send_telegram_message(chat_id, out["reply"] or "Done.", _buttons_for(out.get("approval")))
        return {"ok": True}

    msg = data.get("message") or {}
    if not msg.get("text"):
        return {"ok": True}
    chat_id = str(msg["chat"]["id"])
    txt = msg["text"].strip()

    if txt.startswith("/start"):
        parts = txt.split(maxsplit=1)
        uid = read_link_token(parts[1]) if len(parts) == 2 else None
        if not uid:
            await tg.send_telegram_message(chat_id, "👋 Open DAKSHA → Profile → Connect Telegram to link this chat.")
            return {"ok": True}
        db.execute(text("""INSERT INTO telegram_users (user_id, chat_id, username, opt_in) VALUES (:u, :c, :n, true)
                           ON CONFLICT (user_id) DO UPDATE SET chat_id = EXCLUDED.chat_id, username = EXCLUDED.username, opt_in = true"""),
                   {"u": uid, "c": chat_id, "n": msg["chat"].get("username")})
        db.commit()
        await tg.send_telegram_message(chat_id, "✅ Linked! Ask me anything: find an outfit, track an order, start a return.")
        return {"ok": True}

    link = db.execute(text("SELECT user_id FROM telegram_users WHERE chat_id = :c AND opt_in"), {"c": chat_id}).first()
    if not link:
        await tg.send_telegram_message(chat_id, "Please link your account first: DAKSHA app → Profile → Connect Telegram.")
        return {"ok": True}
    if txt in ("/stop", "/unlink"):
        db.execute(text("UPDATE telegram_users SET opt_in = false WHERE chat_id = :c"), {"c": chat_id})
        db.commit()
        await tg.send_telegram_message(chat_id, "Unlinked. You won't get messages here any more.")
        return {"ok": True}

    uid = str(link.user_id)
    sid = _chat_session_for(db, uid)
    append_message(db, sid, "user", txt)
    h = db.execute(text("""SELECT id FROM agent_handoffs WHERE chat_session_id = :s AND status IN ('open','in_progress')"""),
                   {"s": sid}).first()
    if h:
        from app.api.routers.websocket_handoff import relay_customer_message
        await relay_customer_message(db, str(h.id), sid, txt)
        return {"ok": True}
    try:
        out = await run_turn(thread_id=sid, user_id=uid, session_id=sid, message=txt, channel="telegram")
    except Exception as e:
        await tg.send_telegram_message(chat_id, "Sorry, I'm having trouble right now. Please try again shortly.")
        return {"ok": True, "error": str(e)[:200]}
    reply = out["reply"] or "Done."
    ui = out.get("ui") or {}
    if ui.get("type") == "products":
        reply += "\n\n" + "\n".join(f"• {p['name']} ({p.get('color') or ''} {p.get('size') or ''}) ₹{p['price']:.0f}"
                                     for p in ui.get("products", [])[:6])
    append_message(db, sid, "assistant", reply, ui_data={**ui, "_agentic": {"plan": out.get("plan"), "approval": out.get("approval")}})
    await tg.send_telegram_message(chat_id, reply, _buttons_for(out.get("approval")))
    return {"ok": True}
