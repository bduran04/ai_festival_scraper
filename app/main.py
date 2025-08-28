from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging

from app.models import (
    FestivalResponse, FestivalListResponse, FestivalCreate, FestivalUpdate,
    FestivalSearchRequest, FestivalStatsResponse
)
from app.database import supabase_manager
from ai.data_processor import data_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Festival Scraper",
    description="AI-Enhanced Festival Discovery with Sentiment Analysis and Smart Recommendations",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Festival App Starting...")
    try:
        # Test Supabase connection
        result = await supabase_manager.get_festivals(limit=1)
        logger.info("✅ Supabase connection successful")
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")

@app.get("/")
async def root():
    return {
        "message": "AI Festival Scraper API", 
        "status": "running",
        "version": "2.0.0",
        "features": [
            "AI-powered sentiment analysis",
            "Smart festival categorization",
            "Popularity scoring",
            "Advanced search and filtering",
            "Festival statistics and insights"
        ]
    }

@app.get("/api/festivals", response_model=FestivalListResponse)
async def get_festivals(
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_sentiment: Optional[float] = Query(None, ge=0, le=1, description="Minimum sentiment score"),
    min_popularity: Optional[float] = Query(None, ge=0, le=1, description="Minimum popularity score"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get festivals with advanced filtering"""
    try:
        filters = {}
        if city:
            filters['city'] = city
        if state:
            filters['state'] = state
        if category:
            filters['category'] = category
        if min_price is not None:
            filters['min_price'] = min_price
        if max_price is not None:
            filters['max_price'] = max_price
        if min_sentiment is not None:
            filters['min_sentiment'] = min_sentiment
        if min_popularity is not None:
            filters['min_popularity'] = min_popularity
        
        result = await supabase_manager.get_festivals(limit, filters, offset)
        
        if not result.data:
            return FestivalListResponse(festivals=[], total=0, limit=limit, offset=offset)
        
        # Convert to Pydantic models
        festival_objects = []
        for festival in result.data:
            try:
                festival_obj = FestivalResponse(**festival)
                festival_objects.append(festival_obj)
            except Exception as e:
                logger.warning(f"Skipping invalid festival data: {e}")
                continue
        
        return FestivalListResponse(
            festivals=festival_objects,
            total=len(result.data),
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Error getting festivals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/festivals/{festival_id}", response_model=FestivalResponse)
async def get_festival(festival_id: int):
    """Get a specific festival by ID"""
    try:
        result = await supabase_manager.get_festival_by_id(festival_id)
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Festival not found")
        
        return FestivalResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting festival {festival_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/festivals", response_model=FestivalResponse)
async def create_festival(festival: FestivalCreate):
    """Create a new festival with AI processing"""
    try:
        # Process festival data with AI
        processed_data = await data_processor.process_festival(festival.dict())
        
        # Create festival in database
        result = await supabase_manager.create_festival(processed_data)
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create festival")
        
        return FestivalResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating festival: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/api/festivals/{festival_id}", response_model=FestivalResponse)
async def update_festival(festival_id: int, festival: FestivalUpdate):
    """Update a festival"""
    try:
        # Get existing festival
        existing = await supabase_manager.get_festival_by_id(festival_id)
        if not existing.data:
            raise HTTPException(status_code=404, detail="Festival not found")
        
        # Update only provided fields
        update_data = festival.dict(exclude_unset=True)
        
        # Re-process with AI if description or name changed
        if 'description' in update_data or 'name' in update_data:
            existing_data = existing.data[0]
            existing_data.update(update_data)
            processed_data = await data_processor.process_festival(existing_data)
            update_data.update({
                'ai_summary': processed_data.get('ai_summary'),
                'sentiment_score': processed_data.get('sentiment_score'),
                'popularity_score': processed_data.get('popularity_score'),
                'category': processed_data.get('category')
            })
        
        result = await supabase_manager.update_festival(festival_id, update_data)
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update festival")
        
        return FestivalResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating festival {festival_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/festivals/{festival_id}")
async def delete_festival(festival_id: int):
    """Delete a festival"""
    try:
        result = await supabase_manager.delete_festival(festival_id)
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Festival not found")
        
        return {"message": "Festival deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting festival {festival_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/festivals/search", response_model=FestivalListResponse)
async def search_festivals(search_request: FestivalSearchRequest):
    """Advanced search with multiple parameters"""
    try:
        search_params = search_request.dict()
        result = await supabase_manager.search_festivals(search_params)
        
        if not result.data:
            return FestivalListResponse(
                festivals=[], 
                total=0, 
                limit=search_request.limit, 
                offset=search_request.offset
            )
        
        # Convert to Pydantic models
        festival_objects = []
        for festival in result.data:
            try:
                festival_obj = FestivalResponse(**festival)
                festival_objects.append(festival_obj)
            except Exception as e:
                logger.warning(f"Skipping invalid festival data: {e}")
                continue
        
        return FestivalListResponse(
            festivals=festival_objects,
            total=len(result.data),
            limit=search_request.limit,
            offset=search_request.offset
        )
    
    except Exception as e:
        logger.error(f"Error searching festivals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/festivals/stats", response_model=FestivalStatsResponse)
async def get_festival_stats():
    """Get festival statistics and insights"""
    try:
        stats = await supabase_manager.get_festival_stats()
        return FestivalStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Error getting festival stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/festivals/popular", response_model=FestivalListResponse)
async def get_popular_festivals(
    min_popularity: float = Query(0.7, ge=0, le=1, description="Minimum popularity score"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get festivals with high popularity scores"""
    try:
        result = await supabase_manager.get_popular_festivals(min_popularity, limit)
        
        if not result.data:
            return FestivalListResponse(festivals=[], total=0, limit=limit, offset=0)
        
        festival_objects = [FestivalResponse(**festival) for festival in result.data]
        
        return FestivalListResponse(
            festivals=festival_objects,
            total=len(result.data),
            limit=limit,
            offset=0
        )
    
    except Exception as e:
        logger.error(f"Error getting popular festivals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/festivals/positive", response_model=FestivalListResponse)
async def get_positive_sentiment_festivals(
    min_sentiment: float = Query(0.7, ge=0, le=1, description="Minimum sentiment score"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get festivals with positive sentiment"""
    try:
        result = await supabase_manager.get_positive_sentiment_festivals(min_sentiment, limit)
        
        if not result.data:
            return FestivalListResponse(festivals=[], total=0, limit=limit, offset=0)
        
        festival_objects = [FestivalResponse(**festival) for festival in result.data]
        
        return FestivalListResponse(
            festivals=festival_objects,
            total=len(result.data),
            limit=limit,
            offset=0
        )
    
    except Exception as e:
        logger.error(f"Error getting positive sentiment festivals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/festivals/category/{category}", response_model=FestivalListResponse)
async def get_festivals_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get festivals by category"""
    try:
        result = await supabase_manager.get_festivals_by_category(category, limit)
        
        if not result.data:
            return FestivalListResponse(festivals=[], total=0, limit=limit, offset=offset)
        
        festival_objects = [FestivalResponse(**festival) for festival in result.data]
        
        return FestivalListResponse(
            festivals=festival_objects,
            total=len(result.data),
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Error getting festivals by category {category}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)