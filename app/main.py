from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import logging

from app.models import FestivalResponse, FestivalListResponse, FestivalCreate
from app.database import supabase_manager
from ai.data_processor import data_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Festival Finder",
    description="AI-Enhanced Festival Discovery",
    version="1.0.0"
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
    logger.info("🚀 Festival App Starting...")
    try:
        # Test Supabase connection
        result = await supabase_manager.get_festivals(limit=1)
        logger.info("✅ Supabase connection successful")
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")

@app.get("/")
async def root():
    return {"message": "Festival Finder API", "status": "running"}

@app.get("/api/festivals", response_model=FestivalListResponse)
async def get_festivals(
    city: Optional[str] = Query(None, description="Filter by city"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get festivals with optional filters"""
    try:
        filters = {}
        if city:
            filters['city'] = city
        if category:
            filters['category'] = category
        
        result = await supabase_manager.get_festivals(limit + offset, filters)
        
        if not result.data:
            return FestivalListResponse(festivals=[], total=0, limit=limit, offset=offset)
        
        # Apply pagination
        festivals = result.data[offset:offset + limit]
        
        # Convert to Pydantic models
        festival_objects = []
        for festival in festivals:
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
        # Convert to dict
        festival_data = festival.dict()
        
        # Process with AI
        processed_data = await data_processor.process_festival(festival_data)
        
        # Save to Supabase
        result = await supabase_manager.create_festival(processed_data)
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create festival")
        
        return FestivalResponse(**result.data[0])
    
    except Exception as e:
        logger.error(f"Error creating festival: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/search")
async def search_festivals(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50)
):
    """Basic text search for festivals"""
    try:
        # Simple text search in Supabase
        query = supabase_manager.client.table("festivals").select("*")
        
        # Search in name, venue, city, and description
        search_filter = f"name.ilike.%{q}%,venue.ilike.%{q}%,city.ilike.%{q}%,description.ilike.%{q}%"
        
        result = query.or_(search_filter).limit(limit).execute()
        
        return {
            "festivals": result.data,
            "query": q,
            "total": len(result.data)
        }
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/categories")
async def get_categories():
    """Get all available categories"""
    try:
        # Get unique categories from database
        result = supabase_manager.client.table("festivals").select("category").execute()
        
        categories = list(set(
            item['category'] for item in result.data 
            if item.get('category')
        ))
        
        return {"categories": sorted(categories)}
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return {"categories": ["music_festival", "food_festival", "art_festival", "general"]}

@app.get("/api/stats")
async def get_stats():
    """Get basic app statistics"""
    try:
        result = await supabase_manager.get_festivals(limit=1000)
        total_festivals = len(result.data)
        
        categories = {}
        for festival in result.data:
            cat = festival.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_festivals": total_festivals,
            "categories": categories,
            "status": "operational"
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"total_festivals": 0, "categories": {}, "status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)