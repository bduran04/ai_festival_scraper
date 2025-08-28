import logging
from typing import Dict, List, Optional, Union
import asyncio
import torch
from config.model_config import MODEL_CONFIGS, PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)

class HuggingFaceClient:
    """Enhanced client for Hugging Face models with specific model configurations"""
    
    def __init__(self):
        self.models = {}
        self.device = self._get_device()
        self._init_models()
    
    def _get_device(self):
        """Get the best available device (GPU or CPU)"""
        device_pref = PERFORMANCE_CONFIG['device_preference']
        
        if device_pref == 'cuda' and torch.cuda.is_available():
            device = "cuda"
            logger.info(f"✅ Using GPU: {torch.cuda.get_device_name()}")
        elif device_pref == 'auto':
            if torch.cuda.is_available():
                device = "cuda"
                logger.info(f"✅ Auto-detected GPU: {torch.cuda.get_device_name()}")
            else:
                device = "cpu"
                logger.info("⚠️ Auto-detected CPU (GPU not available)")
        else:
            device = "cpu"
            logger.info("⚠️ Using CPU (as configured)")
        
        return device
    
    def _init_models(self):
        """Initialize models with specific names and revisions from config"""
        try:
            from transformers import pipeline
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"🔄 Initializing models on device: {self.device}")
            
            # Initialize sentiment analysis
            self.models['sentiment'] = pipeline(
                "sentiment-analysis",
                model=MODEL_CONFIGS['sentiment']['model'],
                revision=MODEL_CONFIGS['sentiment']['revision'],
                device=0 if self.device == "cuda" else -1
            )
            logger.info(f"✅ Loaded sentiment model: {MODEL_CONFIGS['sentiment']['model']}")
            
            # Initialize sentence transformer
            self.models['sentence_transformer'] = SentenceTransformer(
                MODEL_CONFIGS['sentence_transformer']['model'],
                device=self.device
            )
            logger.info(f"✅ Loaded sentence transformer: {MODEL_CONFIGS['sentence_transformer']['model']}")
            
            # Initialize zero-shot classifier
            self.models['classifier'] = pipeline(
                "zero-shot-classification",
                model=MODEL_CONFIGS['classifier']['model'],
                revision=MODEL_CONFIGS['classifier']['revision'],
                device=0 if self.device == "cuda" else -1
            )
            logger.info(f"✅ Loaded classifier: {MODEL_CONFIGS['classifier']['model']}")
            
            # Initialize question-answering
            self.models['qa'] = pipeline(
                "question-answering",
                model=MODEL_CONFIGS['qa']['model'],
                revision=MODEL_CONFIGS['qa']['revision'],
                device=0 if self.device == "cuda" else -1
            )
            logger.info(f"✅ Loaded QA model: {MODEL_CONFIGS['qa']['model']}")
            
            # Initialize summarizer
            self.models['summarizer'] = pipeline(
                "summarization",
                model=MODEL_CONFIGS['summarizer']['model'],
                revision=MODEL_CONFIGS['summarizer']['revision'],
                device=0 if self.device == "cuda" else -1
            )
            logger.info(f"✅ Loaded summarizer: {MODEL_CONFIGS['summarizer']['model']}")
            
            logger.info("🎉 All Hugging Face models initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing models: {e}")
            self.models = {}
    
    async def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text"""
        if not text or 'sentiment' not in self.models:
            return {"sentiment": "neutral", "score": 0.5}
        
        try:
            result = self.models['sentiment'](text[:PERFORMANCE_CONFIG['max_length']])
            
            if result and len(result) > 0:
                label = result[0]['label'].lower()
                score = result[0]['score']
                
                # Map labels to sentiment
                if 'positive' in label:
                    return {"sentiment": "positive", "score": score}
                elif 'negative' in label:
                    return {"sentiment": "negative", "score": score}
                else:
                    return {"sentiment": "neutral", "score": score}
            
            return {"sentiment": "neutral", "score": 0.5}
            
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {"sentiment": "neutral", "score": 0.5}
    
    async def classify_category(self, text: str, categories: List[str]) -> Dict:
        """Classify text into categories"""
        if not text or 'classifier' not in self.models:
            return {"category": categories[0] if categories else "general", "score": 0.5}
        
        try:
            result = self.models['classifier'](text, categories)
            
            if result and len(result['labels']) > 0:
                return {
                    "category": result['labels'][0],
                    "score": result['scores'][0]
                }
            
            return {"category": categories[0] if categories else "general", "score": 0.5}
            
        except Exception as e:
            logger.warning(f"Category classification failed: {e}")
            return {"category": categories[0] if categories else "general", "score": 0.5}
    
    async def get_embeddings_batch(self, texts: List[str]) -> Optional:
        """Get embeddings for texts"""
        if not texts or 'sentence_transformer' not in self.models:
            return None
        
        try:
            embeddings = self.models['sentence_transformer'].encode(
                texts, 
                batch_size=PERFORMANCE_CONFIG['batch_size']
            )
            return embeddings
            
        except Exception as e:
            logger.warning(f"Embeddings generation failed: {e}")
            return None
    
    async def extract_info_qa(self, context: str, questions: List[str]) -> Dict:
        """Extract information using question-answering"""
        if not context or 'qa' not in self.models:
            return {}
        
        try:
            results = {}
            for question in questions:
                try:
                    result = self.models['qa'](
                        question=question, 
                        context=context[:PERFORMANCE_CONFIG['max_length']]
                    )
                    results[question] = result['answer']
                except Exception as e:
                    logger.warning(f"QA failed for question '{question}': {e}")
                    results[question] = ""
            
            return results
            
        except Exception as e:
            logger.warning(f"QA extraction failed: {e}")
            return {}
    
    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """Summarize text"""
        if not text or 'summarizer' not in self.models:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        try:
            result = self.models['summarizer'](
                text, 
                max_length=max_length, 
                min_length=20, 
                do_sample=False
            )
            
            if result and len(result) > 0:
                return result[0]['summary_text']
            
            return text[:max_length] + "..." if len(text) > max_length else text
            
        except Exception as e:
            logger.warning(f"Summarization failed: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text

# Global instance
hf_client = HuggingFaceClient()