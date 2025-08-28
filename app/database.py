import os
from supabase import create_client, Client
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
    
    async def get_festivals(self, limit: int = 50, filters: Dict = None, offset: int = 0):
        """Get festivals with optional filters"""
        query = self.client.table("festivals").select("*")
        
        if filters:
            # Text-based filters
            if filters.get("city"):
                query = query.ilike("city", f"%{filters['city']}%")
            if filters.get("state"):
                query = query.ilike("state", f"%{filters['state']}%")
            if filters.get("category"):
                query = query.eq("category", filters["category"])
            if filters.get("venue"):
                query = query.ilike("venue", f"%{filters['venue']}%")
            
            # Price filters
            if filters.get("min_price") is not None:
                query = query.gte("price", filters["min_price"])
            if filters.get("max_price") is not None:
                query = query.lte("price", filters["max_price"])
            
            # Date filters
            if filters.get("start_date"):
                query = query.gte("date", filters["start_date"].isoformat())
            if filters.get("end_date"):
                query = query.lte("date", filters["end_date"].isoformat())
            
            # Score filters
            if filters.get("min_sentiment") is not None:
                query = query.gte("sentiment_score", filters["min_sentiment"])
            if filters.get("min_popularity") is not None:
                query = query.gte("popularity_score", filters["min_popularity"])
            
            # Text search
            if filters.get("query"):
                search_query = filters["query"]
                query = query.or_(f"name.ilike.%{search_query}%,description.ilike.%{search_query}%")
        
        return query.range(offset, offset + limit - 1).order("created_at", desc=True).execute()
    
    async def get_festival_by_id(self, festival_id: int):
        """Get festival by ID"""
        return self.client.table("festivals").select("*").eq("id", festival_id).execute()
    
    async def create_festival(self, festival_data: Dict):
        """Create a new festival"""
        # Convert datetime objects to strings
        processed_data = {}
        for key, value in festival_data.items():
            if isinstance(value, datetime):
                processed_data[key] = value.isoformat()
            else:
                processed_data[key] = value
        
        # Add timestamps
        processed_data["created_at"] = datetime.utcnow().isoformat()
        processed_data["updated_at"] = datetime.utcnow().isoformat()
        
        return self.client.table("festivals").insert(processed_data).execute()
    
    async def update_festival(self, festival_id: int, festival_data: Dict):
        """Update a festival"""
        # Convert datetime objects to strings
        processed_data = {}
        for key, value in festival_data.items():
            if isinstance(value, datetime):
                processed_data[key] = value.isoformat()
            else:
                processed_data[key] = value
        
        processed_data["updated_at"] = datetime.utcnow().isoformat()
        
        return self.client.table("festivals").update(processed_data).eq("id", festival_id).execute()
    
    async def delete_festival(self, festival_id: int):
        """Delete a festival"""
        return self.client.table("festivals").delete().eq("id", festival_id).execute()
    
    async def get_festival_stats(self):
        """Get festival statistics"""
        try:
            # Get basic counts
            total_result = self.client.table("festivals").select("id", count="exact").execute()
            total_festivals = total_result.count if total_result.count is not None else 0
            
            # Get unique cities and categories
            cities_result = self.client.table("festivals").select("city").not_.is_("city", "null").execute()
            categories_result = self.client.table("festivals").select("category").not_.is_("category", "null").execute()
            
            unique_cities = len(set(item["city"] for item in cities_result.data if item["city"]))
            unique_categories = len(set(item["category"] for item in categories_result.data if item["category"]))
            
            # Get averages
            avg_result = self.client.rpc("get_festival_averages").execute()
            averages = avg_result.data[0] if avg_result.data else {}
            
            # Get top cities
            top_cities_result = self.client.rpc("get_top_cities").execute()
            top_cities = top_cities_result.data if top_cities_result.data else []
            
            # Get top categories
            top_categories_result = self.client.rpc("get_top_categories").execute()
            top_categories = top_categories_result.data if top_categories_result.data else []
            
            return {
                "total_festivals": total_festivals,
                "total_cities": unique_cities,
                "total_categories": unique_categories,
                "average_price": averages.get("avg_price"),
                "average_sentiment": averages.get("avg_sentiment"),
                "average_popularity": averages.get("avg_popularity"),
                "price_range": averages.get("price_range", {}),
                "top_cities": top_cities,
                "top_categories": top_categories
            }
            
        except Exception as e:
            logger.error(f"Error getting festival stats: {e}")
            return {
                "total_festivals": 0,
                "total_cities": 0,
                "total_categories": 0,
                "average_price": None,
                "average_sentiment": None,
                "average_popularity": None,
                "price_range": {},
                "top_cities": [],
                "top_categories": []
            }
    
    async def search_festivals(self, search_params: Dict):
        """Advanced search with multiple parameters"""
        return await self.get_festivals(
            limit=search_params.get("limit", 50),
            offset=search_params.get("offset", 0),
            filters=search_params
        )
    
    async def get_festivals_by_date_range(self, start_date: datetime, end_date: datetime, limit: int = 50):
        """Get festivals within a date range"""
        filters = {
            "start_date": start_date,
            "end_date": end_date
        }
        return await self.get_festivals(limit=limit, filters=filters)
    
    async def get_festivals_by_location(self, city: str = None, state: str = None, limit: int = 50):
        """Get festivals by location"""
        filters = {}
        if city:
            filters["city"] = city
        if state:
            filters["state"] = state
        
        return await self.get_festivals(limit=limit, filters=filters)
    
    async def get_festivals_by_category(self, category: str, limit: int = 50):
        """Get festivals by category"""
        filters = {"category": category}
        return await self.get_festivals(limit=limit, filters=filters)
    
    async def get_popular_festivals(self, min_popularity: float = 0.7, limit: int = 50):
        """Get festivals with high popularity scores"""
        filters = {"min_popularity": min_popularity}
        return await self.get_festivals(limit=limit, filters=filters)
    
    async def get_positive_sentiment_festivals(self, min_sentiment: float = 0.7, limit: int = 50):
        """Get festivals with positive sentiment"""
        filters = {"min_sentiment": min_sentiment}
        return await self.get_festivals(limit=limit, filters=filters)

# Global instance
supabase_manager = SupabaseManager()