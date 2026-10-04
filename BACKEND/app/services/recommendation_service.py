# app/services/recommendation_service.py

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import generate_text_embedding
from app.services.impression_service import log_impressions
from app.models.models import ProductVariant, UserPreferenceSummary
from app.services.pricing_service import resolve_variant_price
from app.services.postrank_service import apply_business_rules

def recommend(
    db: Session,
    user_id: str,
    intent_text: str = None,
    *,
    limit: int = 10,
    seed_variant_id: str = None,
    session_id: str = None,
    feed_type: str = None,
    log: bool = True,
    max_price: float = None,
    category: str = None,
):
    """
    The one recommendation pipeline (feed, agent, Telegram all call this):

      recall  (candidate_service: semantic / collaborative / seed / trending)
      rank    (ranking_service: intent, content-taste and trend scores)
      filter  (sellable stock > 0, optional price/category constraints)
      diversify (postrank_service: max 3 per brand)
      log     (impressions, so clicks and purchases can train the model)

    The query is embedded once and reused by recall and rank.
    """
    from app.models.models import GlobalInventory
    from app.services.candidate_service import generate_candidates
    from app.services.ranking_service import rank_candidates
    from app.services.stock import sellable

    vec = generate_text_embedding(intent_text, task_type="search_query") if intent_text else None
    ids = generate_candidates(db, user_id, intent_text, limit=300, seed_variant_id=seed_variant_id, intent_vec=vec)
    if not ids:
        return []
    ranked = rank_candidates(db, user_id, ids, intent_text, limit=150, intent_vec=vec)

    kept = []
    for r in ranked:
        inv = db.get(GlobalInventory, r["variant_id"])
        if sellable(inv) <= 0:
            continue
        if max_price is not None and r["final_price"] > max_price:
            continue
        if category and category.lower() not in (r.get("category") or "").lower():
            continue
        r["in_stock"] = sellable(inv)
        kept.append(r)
    final = apply_business_rules(kept)[:limit]

    variants = {str(v.id): v for v in db.query(ProductVariant).filter(ProductVariant.id.in_([r["variant_id"] for r in final])).all()} if final else {}
    out = []
    for r in final:
        v = variants.get(str(r["variant_id"]))
        out.append({
            "variant_id": str(r["variant_id"]), "product_id": str(r["product_id"]), "name": r["name"],
            "brand": r["brand"], "category": r["category"], "image": r["image"],
            "color": v.color if v else None, "size": v.size if v else None,
            "base_price": r["base_price"], "final_price": r["final_price"], "price": r["final_price"],
            "offer_name": r.get("offer_name"), "in_stock": r["in_stock"],
            "score": round(float(r["final_score"]), 4), "reason": "recommended",
        })
    if log and out:
        log_impressions(db, user_id, out, feed_type=feed_type or ("search" if intent_text else "home"), session_id=session_id)
    return out


def get_hybrid_recommendations(db: Session, user_id: str, intent_text: str = None, session_id: str = None, limit: int = 20):
    """Backward-compatible wrapper (Telegram, old orchestrator)."""
    return recommend(db, user_id, intent_text, limit=limit, session_id=session_id)


def get_similar_variants(db: Session, variant_id: str, user_id: str = None, limit: int = 10):
    target_vec_sql = text("SELECT embedding FROM product_multimodal_embeddings WHERE product_variant_id = :vid AND modality = 'text' LIMIT 1")
    target_row = db.execute(target_vec_sql, {"vid": variant_id}).first()
    
    if not target_row or not target_row.embedding:
        return []
        
    vector_str = str(target_row.embedding)
    semantic_query = text(f"""
        SELECT pv.id, 1 - (pe.embedding <=> '{vector_str}') as score, 'similar' as reason
        FROM product_variants pv
        JOIN product_multimodal_embeddings pe ON pv.id = pe.product_variant_id
        WHERE pe.modality = 'text' AND pv.active = true AND pv.id != :vid
        ORDER BY pe.embedding <=> '{vector_str}'
        LIMIT :limit
    """)
    
    rows = db.execute(semantic_query, {"vid": variant_id, "limit": limit}).fetchall()
    
    results = []
    for r in rows:
        variant = db.query(ProductVariant).get(r.id)
        if not variant: continue
        price = resolve_variant_price(db, variant)
        results.append({
            "variant_id": variant.id,
            "product_id": variant.product_id,
            "name": variant.product.name,
            "image": variant.images[0].image_url if variant.images else None,
            "base_price": price["base_price"],
            "final_price": price["final_price"],
            "score": float(r.score),
            "reason": r.reason
        })
    return results