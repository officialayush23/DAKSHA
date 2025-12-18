from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import supabase
from app.services.ai_service import AIService
from app.core.rbac import require_role

router = APIRouter(prefix="/admin/knowledge", tags=["Admin: Knowledge Base"])

class DocCreate(BaseModel):
    title: str
    content: str
    metadata: dict = {}

@router.post("/")
async def add_knowledge_doc(data: DocCreate, admin = Depends(require_role("catalog_admin"))):
    """
    Add policy/FAQ docs. Automatically embeds content for Vector Search.
    """
    try:
        # 1. Generate Embedding
        embedding = AIService.generate_embedding(f"{data.title}\n{data.content}")
        
        # 2. Insert
        res = supabase.table("knowledge_base").insert({
            "title": data.title,
            "content_chunk": data.content,
            "metadata": data.metadata,
            "embedding": embedding,
            "is_active": True
        }).execute()
        
        return res.data[0]
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/")
async def list_docs():
    return supabase.table("knowledge_base").select("id, title, is_active, created_at").order("created_at", desc=True).execute().data

@router.delete("/{id}")
async def delete_doc(id: str, admin = Depends(require_role("catalog_admin"))):
    supabase.table("knowledge_base").delete().eq("id", id).execute()
    return {"status": "deleted"}