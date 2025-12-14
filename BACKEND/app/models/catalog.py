# app/models/catalog.py
from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
