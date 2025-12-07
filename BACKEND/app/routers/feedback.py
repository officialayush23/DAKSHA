from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.schemas import ReviewCreate
from app.database import supabase

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("/submit")
async def submit_review(review: ReviewCreate, user_id: str = Depends(get_current_user_id)):
    # TODO: hook AIService for sentiment/tags
    sentiment_score = 0.8
    tags = ["good_quality", "fast_shipping"]

    res = (
        supabase.table("product_reviews")
        .insert(
            {
                "user_id": user_id,
                "product_id": review.product_id,
                "rating": review.rating,
                "review_text": review.review_text,
                "sentiment_score": sentiment_score,
                "tags": tags,
            }
        )
        .execute()
    )

    return {"status": "submitted", "id": res.data[0]["id"]}
