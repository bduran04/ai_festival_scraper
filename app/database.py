import os
from supabase import create_client, Client
from typing import Dict, List, Optional

class SupabaseManager:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
    
    async def get_festivals(self, limit: int = 50, filters: Dict = None):
        """Get festivals with optional filters"""
        query = self.client.table("festivals").select("*")
        
        if filters:
            if filters.get("city"):
                query = query.ilike("city", f"%{filters['city']}%")
            if filters.get("category"):
                query = query.eq("category", filters["category"])
        
        return query.limit(limit).order("created_at", desc=True).execute()
    
    async def create_festival(self, festival_data: Dict):
        """Create a new festival"""
        return self.client.table("festivals").insert(festival_data).execute()
    
    async def get_festival_by_id(self, festival_id: int):
        """Get festival by ID"""
        return self.client.table("festivals").select("*").eq("id", festival_id).execute()

# Global instance
supabase_manager = SupabaseManager()