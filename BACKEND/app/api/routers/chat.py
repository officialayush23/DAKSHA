# app/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
import re
import json
import base64
from typing import Optional, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.models import User
from sqlalchemy.orm import Session

from app.ai.graph import agent_workflow
from app.ai.context_loader import load_context
from app.services.preference_service import refresh_user_preference_summary
from app.services.chat_session_service import (
    create_session,
    get_session,
    list_sessions,
    append_message,
    get_messages,
    get_context_for_llm,
    generate_session_name,
    set_session_name,
    update_rolling_summary,
)

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])


# ── Image similarity search helper ────────────────────────────────────────────
def _image_similarity_search(db: Session, image_url: str, limit: int = 12) -> list[dict]:
    """
    Download the image via the Supabase service-role SDK, generate a Nomic
    vision embedding, run pgvector similarity search against
    product_multimodal_embeddings (modality='image'), and return hydrated
    product card dicts ready for UI rendering.
    """
    from app.services.catalog_semantic_service import search_similar_by_image
    from app.services.pricing_service import resolve_variant_price
    from app.models.models import ProductVariant
    import uuid as _uuid

    from app.models.models import GlobalInventory

    variant_ids = search_similar_by_image(db, image_url, limit=limit * 2)  # fetch extra to account for filtered-out
    if not variant_ids:
        return []

    cards = []
    for vid_str in variant_ids:
        if len(cards) >= limit:
            break
        try:
            vid = _uuid.UUID(vid_str)
            v = db.get(ProductVariant, vid)
            if not v or not v.product:
                continue

            # Only include variants that have inventory assigned (so quick-add works)
            inv = db.get(GlobalInventory, vid)
            available = 0
            if inv:
                available = (inv.total_stock or 0) - (inv.reserved_stock or 0) - (inv.assigned_stock or 0)
            if available <= 0:
                continue

            price = resolve_variant_price(db, v)
            cards.append({
                "variant_id": str(v.id),
                "product_id": str(v.product_id),
                "name":       v.product.name,
                "brand":      v.product.brand,
                "category":   v.product.category,
                "color":      v.color,
                "size":       v.size,
                "image":      v.images[0].image_url if v.images else None,
                **price,
            })
        except Exception:
            continue
    return cards

# ── Image upload endpoint (bypasses Supabase RLS via service-role key) ────────
@router.post("/upload-image")
async def upload_chat_image(
    file: UploadFile = File(...),
    current_user: "User" = Depends(get_current_user),
):
    """Receive an image from the frontend and store it in Supabase Storage
    using the service-role key (which is exempt from RLS).
    Returns { url: string } — the public Supabase URL."""
    from app.services.storage_service import upload_chat_image as _upload

    ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/heic"}
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB

    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=415, detail="Unsupported image type")

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image must be under 10 MB")

    try:
        public_url = _upload(data, file.content_type, file.filename or "image.jpg")
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # None = start a new session
    channel: str = "web"
    image_url: Optional[str] = None    # Supabase public URL for image search

class ChatResponse(BaseModel):
    response: str
    session_id: str
    session_name: Optional[str] = None
    current_agent: Optional[str] = "UnifiedAgent"
    human_takeover: bool = False
    ui_data: Optional[Dict[str, Any]] = None

class NewSessionResponse(BaseModel):
    session_id: str

class SessionListItem(BaseModel):
    session_id: str
    name: Optional[str]
    channel: str
    last_message_at: Optional[str]
    updated_at: str

class ChatMessageItem(BaseModel):
    role: str
    content: str
    ui_data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

class AdminReplyRequest(BaseModel):
    session_id: str
    message: str

# ── One-time checkpointer setup flag ─────────────────────────────────────────
_checkpointer_setup_done = False


# ── Image inlining helper ─────────────────────────────────────────────────────
async def _inline_image(url: str) -> str:
    """
    Download a Supabase storage image and return a base64 data URL
    (data:<mime>;base64,...) so Gemini always receives raw image bytes.

    Uses the Supabase service-role SDK client (.download()) instead of raw
    HTTP — this bypasses any bucket-level RLS and avoids the 400 that Supabase
    returns when auth headers are sent to a /object/public/ endpoint.
    """
    import mimetypes
    from app.services.storage_service import supabase as _sb_admin

    # Only handle Supabase storage URLs we know how to parse
    _MARKER = "/storage/v1/object/public/"
    if _MARKER not in url:
        # Not a recognisable Supabase storage URL — return as-is
        return url

    try:
        # Extract bucket + file path from the URL
        # URL shape: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
        tail = url.split(_MARKER, 1)[1]          # "user_uploaded_image/chat_xxx.png"
        bucket, _, file_path = tail.partition("/")
        file_path = file_path.split("?")[0]       # strip any query params

        # SDK download uses the service-role key — no HTTP-level auth needed
        file_bytes = _sb_admin.storage.from_(bucket).download(file_path)

        # Infer MIME type from file extension
        mime, _ = mimetypes.guess_type(file_path)
        if not mime or mime in ("application/json", "text/html", "text/plain"):
            mime = "image/jpeg"

        b64 = base64.b64encode(file_bytes).decode()
        print(f"[IMAGE INLINE] Inlined {bucket}/{file_path} as {mime} ({len(file_bytes)} bytes)")
        return f"data:{mime};base64,{b64}"

    except Exception as exc:
        print(f"[IMAGE INLINE] SDK download failed for {url}: {exc}")
        return url  # last-resort fall-back

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/sessions/new", response_model=NewSessionResponse)
def new_chat_session(
    channel: str = "web",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session (called when user clicks 'New Chat')."""
    session = create_session(db, str(current_user.id), channel)
    return NewSessionResponse(session_id=str(session.id))


@router.get("/sessions", response_model=List[SessionListItem])
def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all chat sessions for the user (newest first)."""
    sessions = list_sessions(db, str(current_user.id))
    return [
        SessionListItem(
            session_id=str(s.id),
            name=s.name,
            channel=s.channel,
            last_message_at=s.last_message_at.isoformat() if s.last_message_at else None,
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageItem])
def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Load the message history for a specific chat session."""
    chat_session = get_session(db, session_id, str(current_user.id))
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = get_messages(db, session_id)
    return [
        ChatMessageItem(
            role=m.role,
            content=m.content,
            ui_data=m.ui_data,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in msgs
        if m.role in ("user", "assistant")   # skip raw tool messages
    ]


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    global _checkpointer_setup_done
    try:
        user_id_str = str(current_user.id)

        # ── 1. Resolve or create session ──────────────────────────────────────
        if request.session_id:
            chat_session = get_session(db, request.session_id, user_id_str)
            if not chat_session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            chat_session = create_session(db, user_id_str, request.channel)

        session_id_str = str(chat_session.id)

        # ── 2. Persist user message ───────────────────────────────────────────
        append_message(db, session_id_str, "user", request.message)

        # ── 3a. IMAGE SEARCH — short-circuit: skip LangGraph entirely ───────────
        # When the user uploads an image we generate a Nomic vision embedding
        # and run pgvector similarity search against product image embeddings.
        # This is faster, more accurate, and avoids Gemini vision entirely.
        if request.image_url:
            cards = _image_similarity_search(db, request.image_url)
            if cards:
                ui_data = {"type": "products", "products": cards}
                response_text = (
                    f"Here are {len(cards)} visually similar products I found based on your image:"
                    if not request.message or request.message.strip() in ("", "Image search")
                    else f"Based on your image, here are the most visually similar products:"
                )
            else:
                ui_data = None
                response_text = "I couldn't find any visually similar products. Could you describe what you're looking for?"

            append_message(db, session_id_str, "assistant", response_text, ui_data=ui_data)

            is_first_message = chat_session.name is None
            if is_first_message:
                background_tasks.add_task(_name_session_async, db, session_id_str, request.message or "Image search")
            background_tasks.add_task(refresh_user_preference_summary, user_id_str, session_id_str)

            print(f"\n{'='*50}\n📷 IMAGE SEARCH: found {len(cards)} similar products\n{'='*50}\n")
            return ChatResponse(
                response=response_text,
                session_id=session_id_str,
                session_name=chat_session.name,
                current_agent="ImageSearch",
                human_takeover=False,
                ui_data=ui_data,
            )

        # ── 3b. Build context for text agent ─────────────────────────────────
        context = load_context(db, user_id_str, session_id_str)
        ctx_data = get_context_for_llm(db, session_id_str)

        # Build summary context string for the agent
        summary_context = context.get("user_summary", "")
        if ctx_data.get("summary"):
            summary_context += f"\n\nConversation summary so far:\n{ctx_data['summary']}"

        human_msg = HumanMessage(content=request.message)

        input_state = {
            "messages": [human_msg],
            "user_id": user_id_str,
            "session_id": session_id_str,
            "channel": request.channel,
            "order_mode": "online",
            "user_summary": summary_context,
            "conversation_summary": ctx_data.get("summary"),
        }

        config = {"configurable": {"thread_id": session_id_str}}

        # ── 4. Run LangGraph ──────────────────────────────────────────────────
        lg_url = settings.LANGGRAPH_DB_URL or settings.DATABASE_URL
        async with AsyncPostgresSaver.from_conn_string(lg_url, pipeline=False) as checkpointer:
            if not _checkpointer_setup_done:
                await checkpointer.setup()
                _checkpointer_setup_done = True

            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            final_state = await app_graph.ainvoke(input_state, config)

        # ── 5. Extract response ───────────────────────────────────────────────
        last_msg = final_state["messages"][-1]
        is_human_takeover = final_state.get("pending_human_input", False)
        active_agent = final_state.get("current_agent", "UnifiedAgent")

        response_text = (
            last_msg.content if isinstance(last_msg, AIMessage)
            else "I'm processing your request..."
        )

        # Extract UI JSON payload
        ui_data = None
        match = re.search(r'<UI_DATA>(.*?)</UI_DATA>', response_text, re.DOTALL)
        if match:
            try:
                ui_data = json.loads(match.group(1))
                response_text = response_text.replace(match.group(0), "").strip()
            except Exception as parse_error:
                print(f"⚠️ JSON Parse Error: {parse_error}")

        # ── 6. Persist assistant message (with ui_data so history re-renders cards)
        append_message(db, session_id_str, "assistant", response_text, ui_data=ui_data)

        # ── 7. Background: name session after first message, refresh taste profile
        is_first_message = chat_session.name is None
        if is_first_message:
            background_tasks.add_task(
                _name_session_async, db, session_id_str, request.message
            )

        background_tasks.add_task(
            refresh_user_preference_summary,
            user_id_str,
            session_id_str,
        )

        print(f"\n{'='*50}\n🤖 AGENT: {active_agent}\n💬 {response_text[:200]}\n{'='*50}\n")

        return ChatResponse(
            response=response_text,
            session_id=session_id_str,
            session_name=chat_session.name,
            current_agent=active_agent,
            human_takeover=is_human_takeover,
            ui_data=ui_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _name_session_async(db: Session, session_id: str, first_message: str):
    """Background task: generate and save AI session name."""
    try:
        name = generate_session_name(first_message)
        set_session_name(db, session_id, name)
    except Exception as e:
        print(f"[SESSION NAMING ERROR]: {e}")


@router.post("/admin-reply")
async def admin_chat_resume(
    request: AdminReplyRequest,
    current_admin: User = Depends(get_current_user),
):
    """Injects admin message into the thread and resets human handoff."""
    config = {"configurable": {"thread_id": request.session_id}}
    try:
        lg_url = settings.LANGGRAPH_DB_URL or settings.DATABASE_URL
        async with AsyncPostgresSaver.from_conn_string(lg_url, pipeline=False) as checkpointer:
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            state_update = {
                "messages": [AIMessage(content=f"👨‍💻 [Support Admin]: {request.message}")],
                "pending_human_input": False,
                "failure_count": 0,
            }
            await app_graph.ainvoke(state_update, config)
        return {"status": "Message injected to thread successfully."}
    except Exception as e:
        print(f"[ADMIN REPLY ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))
