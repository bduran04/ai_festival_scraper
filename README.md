# AI-Enhanced Festival Scraper

A modern REST API for festival discovery powered by FastAPI, Supabase, and HuggingFace AI. Features intelligent categorization, sentiment analysis, and smart search capabilities.

## ✨ Features

- **AI-Powered Processing** - Automatic sentiment analysis and categorization using HuggingFace
- **Smart Search** - Find festivals by name, venue, city, or description
- **Rich Data Model** - Comprehensive festival information with AI-enhanced metadata
- **Scalable Architecture** - Built with FastAPI and Supabase PostgreSQL
- **Auto Documentation** - Interactive API docs with Swagger UI
- **CORS Ready** - Frontend integration ready out of the box

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (free tier)
- Git

### 1. Clone & Setup

git clone
cd festival_app

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

### 2. Database Setup

1. **Create Supabase Project**

2. **Run Database Migration**

### 3. Environment Configuration

Create a `.env` file in the project root:

# Supabase Configuration
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY
DATABASE_URL

# HuggingFace API Key for enhanced features in later development
HUGGINGFACE_API_KEY

# App Settings
DEBUG=True

### 4. Run the Application

# Development server with auto-reload
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

The API will be available at:
- **Main API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/festivals` | List festivals with optional filters |
| `POST` | `/api/festivals` | Create new festival (AI processed) |
| `GET` | `/api/festivals/{id}` | Get specific festival by ID |
| `GET` | `/api/search` | Search festivals by text query |
| `GET` | `/api/categories` | List all festival categories |
| `GET` | `/api/stats` | Get application statistics |

### Example Usage

#### Create a Festival
```bash
curl -X POST "http://localhost:8000/api/festivals" \
-H "Content-Type: application/json" \
-d '{
  "name": "Summer Music Festival 2024",
  "venue": "Central Park",
  "city": "New York",
  "state": "NY",
  "price": 75.00,
  "description": "An amazing outdoor music festival featuring top artists from around the world."
}'
```

#### Search Festivals
```bash
curl "http://localhost:8000/api/search?q=music&limit=10"
```

#### Filter by City
```bash
curl "http://localhost:8000/api/festivals?city=New York&limit=20"
```

## 🤖 AI Features

### Automatic Processing
When you create a festival, the AI automatically:

- **📊 Sentiment Analysis** - Analyzes description sentiment (0-1 score)
- **🏷️ Categorization** - Assigns category based on content
- **⭐ Popularity Scoring** - Calculates popularity based on completeness
- **📝 Data Enhancement** - Cleans and standardizes data

### Categories
- `music_festival` - Concerts, music events
- `food_festival` - Culinary events, food markets
- `art_festival` - Art shows, galleries, exhibitions
- `cultural_festival` - Heritage, traditional events
- `outdoor_festival` - Nature, outdoor activities
- `general` - Other events

### Database Configuration

The app uses Supabase PostgreSQL with the following table structure:

- **festivals** - Main festival data with AI-enhanced fields
- Indexes on commonly queried fields (city, category, date)
- Automatic timestamps for created/updated records

### Local Development
python run.py

### Production Deployment

#### Using Railway/Render
1. Connect your GitHub repo
2. Set environment variables in dashboard
3. Deploy automatically

## 🧪 Testing

### Manual Testing
```bash
# Check health
curl http://localhost:8000/

# View API docs
open http://localhost:8000/docs

# Test festival creation
curl -X POST "http://localhost:8000/api/festivals" \
-H "Content-Type: application/json" \
-d '{"name": "Test Festival", "city": "Test City"}'
```

### Sample Data
Use the interactive docs at `/docs` to easily test API endpoints with the built-in Swagger UI.

## 🛠️ Development

### Adding New Features

1. **New API Endpoints** - Add to `app/main.py`
2. **Database Models** - Update `app/models.py`
3. **AI Processing** - Extend `ai/data_processor.py`
4. **Database Schema** - Update Supabase SQL

## 📈 Roadmap

### Planned Features
- [ ] **Advanced Search** - Semantic search with embeddings
- [ ] **Recommendations** - AI-powered festival suggestions
- [ ] **Web Scraping** - Automatic festival data collection
- [ ] **User System** - Authentication and personalization
- [ ] **Caching** - Redis integration for performance
- [ ] **Rate Limiting** - API usage controls

### Performance Optimizations
- [ ] Database query optimization
- [ ] AI model caching
- [ ] Response compression
- [ ] Background task processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
