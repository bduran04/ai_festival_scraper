from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class BasicDataProcessor:
    def __init__(self):
        self.categories = [
            "music_festival", "food_festival", "art_festival", 
            "cultural_festival", "outdoor_festival", "general"
        ]
        self.hf_client = None
        self._init_hf_client()
    
    def _init_hf_client(self):
        """Initialize Hugging Face client safely"""
        try:
            from ai.hf_client import hf_client
            self.hf_client = hf_client
            logger.info("✅ Hugging Face client initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Hugging Face client not available: {e}")
            self.hf_client = None
    
    async def process_festival(self, festival_data: Dict) -> Dict:
        """Basic festival processing"""
        processed = festival_data.copy()
        
        # Basic category assignment
        processed['category'] = self._assign_category(festival_data)
        
        # Basic sentiment analysis (if HF client available)
        text = festival_data.get('description', festival_data.get('name', ''))
        if text and self.hf_client:
            try:
                sentiment = await self.hf_client.analyze_sentiment(text)
                processed['sentiment_score'] = sentiment['score']
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                processed['sentiment_score'] = 0.5
        else:
            processed['sentiment_score'] = 0.5
        
        # Basic popularity score
        processed['popularity_score'] = self._calculate_popularity(festival_data)
        
        return processed
    
    def _assign_category(self, festival: Dict) -> str:
        """Basic category assignment based on keywords"""
        text = f"{festival.get('name', '')} {festival.get('description', '')}".lower()
        
        if any(word in text for word in ['music', 'concert', 'band', 'singer']):
            return 'music_festival'
        elif any(word in text for word in ['food', 'culinary', 'taste', 'chef']):
            return 'food_festival'
        elif any(word in text for word in ['art', 'gallery', 'artist', 'painting']):
            return 'art_festival'
        elif any(word in text for word in ['cultural', 'heritage', 'tradition']):
            return 'cultural_festival'
        elif any(word in text for word in ['outdoor', 'park', 'nature']):
            return 'outdoor_festival'
        else:
            return 'general'
    
    def _calculate_popularity(self, festival: Dict) -> float:
        """Basic popularity calculation"""
        score = 0.5
        
        # Has description
        if festival.get('description') and len(festival['description']) > 50:
            score += 0.2
        
        # Has venue
        if festival.get('venue'):
            score += 0.1
        
        # Has price info
        if festival.get('price') is not None:
            score += 0.1
            # Free events boost
            if festival['price'] == 0:
                score += 0.1
        
        return min(score, 1.0)

# Global instance
data_processor = BasicDataProcessor()