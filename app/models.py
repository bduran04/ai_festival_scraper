from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class FestivalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Festival name")
    venue: Optional[str] = Field(None, max_length=200, description="Venue name")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State or region")
    date: Optional[datetime] = Field(None, description="Event date and time")
    price: Optional[float] = Field(None, ge=0, le=999999.99, description="Ticket price")
    url: Optional[str] = Field(None, description="Event URL")
    description: Optional[str] = Field(None, description="Event description")
    category: Optional[str] = Field(None, max_length=100, description="Event category")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    sentiment_score: Optional[float] = Field(None, ge=0, le=1, description="Sentiment score (0-1)")
    popularity_score: Optional[float] = Field(None, ge=0, le=1, description="Popularity score (0-1)")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v

    @validator('url')
    def validate_url(cls, v):
        if v and not re.match(r'^https?://', v):
            raise ValueError('URL must start with http:// or https://')
        return v

    @validator('sentiment_score', 'popularity_score')
    def validate_scores(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Score must be between 0 and 1')
        return v

class FestivalCreate(FestivalBase):
    pass

class FestivalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    venue: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    date: Optional[datetime] = None
    price: Optional[float] = Field(None, ge=0, le=999999.99)
    url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    ai_summary: Optional[str] = None
    sentiment_score: Optional[float] = Field(None, ge=0, le=1)
    popularity_score: Optional[float] = Field(None, ge=0, le=1)

class FestivalResponse(FestivalBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FestivalListResponse(BaseModel):
    festivals: List[FestivalResponse]
    total: int
    limit: int
    offset: int

class FestivalSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    city: Optional[str] = Field(None, description="Filter by city")
    state: Optional[str] = Field(None, description="Filter by state")
    category: Optional[str] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    min_sentiment: Optional[float] = Field(None, ge=0, le=1, description="Minimum sentiment score")
    min_popularity: Optional[float] = Field(None, ge=0, le=1, description="Minimum popularity score")
    limit: int = Field(50, ge=1, le=100, description="Number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")

class FestivalStatsResponse(BaseModel):
    total_festivals: int
    total_cities: int
    total_categories: int
    average_price: Optional[float]
    average_sentiment: Optional[float]
    average_popularity: Optional[float]
    price_range: dict
    top_cities: List[dict]
    top_categories: List[dict]