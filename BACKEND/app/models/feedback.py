# app/models/feedback.py


from pydantic import BaseModel


class ReviewCreate(BaseModel):
    product_id: str
    rating: int
    review_text: str
