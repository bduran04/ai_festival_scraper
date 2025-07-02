from transformers import pipeline
import logging
from typing import Dict, List

class BasicHFClient:
    def __init__(self):
        try:
            # Initialize basic models
            self.sentiment_pipeline = pipeline("sentiment-analysis")
            print("✅ Loaded sentiment analysis model")
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            self.sentiment_pipeline = None
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """Basic sentiment analysis"""
        if not self.sentiment_pipeline or not text:
            return {"sentiment": "neutral", "score": 0.5}
        
        try:
            result = self.sentiment_pipeline(text[:512])
            
            if result and len(result) > 0:
                label = result[0]['label'].lower()
                score = result[0]['score']
                
                if label == 'positive':
                    return {"sentiment": "positive", "score": score}
                elif label == 'negative':
                    return {"sentiment": "negative", "score": 1 - score}
                else:
                    return {"sentiment": "neutral", "score": 0.5}
            
            return {"sentiment": "neutral", "score": 0.5}
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "score": 0.5}

# Global instance
hf_client = BasicHFClient()