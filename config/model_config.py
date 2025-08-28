"""
Model configuration for Hugging Face models
"""

# Model configurations with specific names and revisions
MODEL_CONFIGS = {
    'sentiment': {
        'model': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
        'revision': 'main',
        'description': 'Twitter RoBERTa for sentiment analysis'
    },
    'sentence_transformer': {
        'model': 'all-MiniLM-L6-v2',
        'revision': 'main',
        'description': 'Sentence transformer for embeddings'
    },
    'classifier': {
        'model': 'facebook/bart-large-mnli',
        'revision': 'main',
        'description': 'BART for zero-shot classification'
    },
    'qa': {
        'model': 'deepset/roberta-base-squad2',
        'revision': 'main',
        'description': 'RoBERTa for question answering'
    },
    'summarizer': {
        'model': 'facebook/bart-large-cnn',
        'revision': 'main',
        'description': 'BART for text summarization'
    }
}

# Alternative model options (you can switch these)
ALTERNATIVE_MODELS = {
    'sentiment': {
        'model': 'nlptown/bert-base-multilingual-uncased-sentiment',
        'revision': 'main',
        'description': 'Multilingual BERT for sentiment'
    },
    'sentence_transformer': {
        'model': 'sentence-transformers/all-mpnet-base-v2',
        'revision': 'main',
        'description': 'MPNet for better embeddings'
    },
    'classifier': {
        'model': 'microsoft/DialoGPT-medium',
        'revision': 'main',
        'description': 'DialoGPT for classification'
    }
}

# Performance settings
PERFORMANCE_CONFIG = {
    'batch_size': 32,
    'max_length': 512,
    'use_gpu': True,
    'device_preference': 'cuda',  # 'cuda', 'cpu', or 'auto'
    'model_cache_dir': './models/cache'
}
