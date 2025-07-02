from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FestivalBase(BaseModel):
    name: str
    venue: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    date: Optional[datetime] = None
    price: Optional[float] = None
    description: Optional[str] = None
    url: Optional[str] = None

class FestivalCreate(FestivalBase):
    pass

class FestivalResponse(FestivalBase):
    id: int
    category: Optional[str] = None
    ai_summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    popularity_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FestivalListResponse(BaseModel):
    festivals: List[FestivalResponse]
    total: int
    limit: int
    offset: int