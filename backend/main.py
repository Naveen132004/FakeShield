"""
main.py
=======
FastAPI backend for Fake News Detection & Credibility Scoring Platform.

Endpoints:
  POST /api/predict       - Analyze text
  POST /api/predict-url   - Analyze URL
  GET  /api/monitor       - Real-time news monitoring
  GET  /api/history       - Get analysis history
  GET  /api/dashboard     - Get dashboard stats
  GET  /api/health        - Health check

Run:
  uvicorn main:app --reload --port 8000
"""

import os
import sys
import time
import uuid
import traceback
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from schemas import (
    TextPredictionRequest, URLPredictionRequest,
    PredictionResponse, URLPredictionResponse,
    HistoryResponse, DashboardStats, MonitorResponse,
    HealthResponse, ErrorResponse, NewsArticle
)
from ml_service import ml_service
from scraper import extract_article
from database import db

# Add blockchain and geo-analytics to path
BLOCKCHAIN_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blockchain")
GEO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "geo-analytics")
for d in [BLOCKCHAIN_DIR, GEO_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

from blockchain import blockchain_service
from geo_analytics import extract_countries, SAMPLE_HEATMAP_DATA

# ─── App Initialization ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered fake news detection with credibility scoring",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Track startup time for uptime
START_TIME = time.time()

# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Startup Event ───────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Load ML model on startup."""
    print(f"\n[Startup] {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Resolve model paths relative to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.normpath(os.path.join(backend_dir, settings.MODEL_PATH))
    preprocessor_path = os.path.normpath(os.path.join(backend_dir, settings.PREPROCESSOR_PATH))
    
    print(f"[Startup] Loading model from: {model_path}")
    print(f"[Startup] Loading preprocessor from: {preprocessor_path}")
    
    try:
        ml_service.initialize(model_path, preprocessor_path)
        print("[Startup] ML model loaded successfully!")
    except Exception as e:
        print(f"[Startup] WARNING: Could not load ML model: {e}")
        print("[Startup] API will start but predictions will fail.")


# ─── Global Exception Handler ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions gracefully."""
    print(f"[Error] Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health and model status."""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        model_loaded=ml_service.is_loaded,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


# ─── Text Prediction ─────────────────────────────────────────────────────────
@app.post("/api/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_text(request: TextPredictionRequest):
    """
    Analyze news text and predict if it's fake or real.
    
    Returns prediction label, confidence percentage, 
    credibility score, and suspicious word analysis.
    """
    if not ml_service.is_loaded:
        raise HTTPException(status_code=503, detail="ML model not loaded")
    
    try:
        result = ml_service.predict(request.text)
        
        # Save to history
        result["source_text"] = request.text
        await db.save_analysis(result)
        
        # Build response
        return PredictionResponse(
            prediction=result["prediction"],
            confidence=result["confidence"],
            credibility_score=result["credibility_score"],
            credibility_level=result["credibility_level"],
            credibility_color=result.get("credibility_color", "#6b7280"),
            fake_probability=result["fake_probability"],
            real_probability=result["real_probability"],
            suspicious_words=result.get("suspicious_words", []),
            text_length=result.get("text_length", len(request.text)),
            analyzed_at=result.get("analyzed_at", datetime.utcnow().isoformat()),
            analysis_id=result.get("analysis_id"),
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ─── URL Prediction ──────────────────────────────────────────────────────────
@app.post("/api/predict-url", response_model=URLPredictionResponse, tags=["Prediction"])
async def predict_url(request: URLPredictionRequest):
    """
    Scrape article from URL and analyze for fake news.
    
    Extracts article text using BeautifulSoup, then runs
    the same prediction pipeline.
    """
    if not ml_service.is_loaded:
        raise HTTPException(status_code=503, detail="ML model not loaded")
    
    # Extract article content
    try:
        article = extract_article(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraping failed: {str(e)}")
    
    if not article.get("text") or len(article["text"]) < 20:
        raise HTTPException(
            status_code=422,
            detail="Could not extract sufficient text from the URL"
        )
    
    # Run prediction
    try:
        result = ml_service.predict(article["text"], source_url=request.url)
        
        # Save to history
        result["source_text"] = article["text"]
        await db.save_analysis(result)
        
        return URLPredictionResponse(
            prediction=result["prediction"],
            confidence=result["confidence"],
            credibility_score=result["credibility_score"],
            credibility_level=result["credibility_level"],
            credibility_color=result.get("credibility_color", "#6b7280"),
            fake_probability=result["fake_probability"],
            real_probability=result["real_probability"],
            suspicious_words=result.get("suspicious_words", []),
            text_length=result.get("text_length", len(article["text"])),
            source_url=request.url,
            analyzed_at=result.get("analyzed_at", datetime.utcnow().isoformat()),
            analysis_id=result.get("analysis_id"),
            extracted_title=article.get("title"),
            extracted_text_length=len(article["text"]),
            source_domain=article.get("domain"),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ─── News Monitoring ─────────────────────────────────────────────────────────
@app.get("/api/monitor", response_model=MonitorResponse, tags=["Monitoring"])
async def monitor_news(
    query: str = Query("latest news", description="Search query for news"),
    limit: int = Query(10, ge=1, le=50, description="Number of articles"),
):
    """
    Fetch and analyze real-time news articles.
    
    Uses News API to fetch articles, then analyzes each one.
    Falls back to sample data if no API key is configured.
    """
    articles = []
    fake_count = 0
    real_count = 0
    
    # Try to fetch from News API
    if settings.NEWS_API_KEY:
        try:
            import requests
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "pageSize": limit,
                "sortBy": "publishedAt",
                "apiKey": settings.NEWS_API_KEY,
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                for art in data.get("articles", []):
                    text = f"{art.get('title', '')} {art.get('description', '')}"
                    if text.strip() and ml_service.is_loaded:
                        pred = ml_service.predict(text)
                        articles.append(NewsArticle(
                            title=art.get("title", ""),
                            description=art.get("description"),
                            url=art.get("url", ""),
                            source=art.get("source", {}).get("name", "Unknown"),
                            published_at=art.get("publishedAt"),
                            prediction=pred["prediction"],
                            confidence=pred["confidence"],
                            credibility_score=pred["credibility_score"],
                        ))
                        if pred["prediction"] == "FAKE":
                            fake_count += 1
                        else:
                            real_count += 1
        except Exception as e:
            print(f"[Monitor] News API error: {e}")
    
    # Fallback: provide sample data if no API key or API failed
    if not articles:
        sample_articles = [
            {"title": "Global Climate Summit Reaches Historic Agreement", 
             "desc": "World leaders announced a landmark deal to reduce emissions by 50% by 2035, according to the United Nations.",
             "source": "Reuters", "url": "https://reuters.com/example"},
            {"title": "New Study Confirms Benefits of Mediterranean Diet", 
             "desc": "Researchers at Harvard published findings in The Lancet showing improved cardiovascular outcomes.",
             "source": "BBC News", "url": "https://bbc.com/example"},
            {"title": "SHOCKING: Government Hiding Secret Weather Control Program!", 
             "desc": "Leaked documents reveal the truth about chemtrails! Share before they delete this!",
             "source": "TruthBuzz", "url": "https://truthbuzz.example"},
            {"title": "Tech Giant Announces AI Safety Initiative", 
             "desc": "The company released its annual transparency report citing data from independent auditors.",
             "source": "AP News", "url": "https://apnews.com/example"},
            {"title": "EXPOSED: Vaccines Contain Mind-Control Microchips!", 
             "desc": "A renegade scientist was silenced after revealing the truth about what big pharma is hiding!",
             "source": "WakeUpPeople", "url": "https://wakeup.example"},
        ]
        
        for art in sample_articles:
            text = f"{art['title']} {art['desc']}"
            if ml_service.is_loaded:
                pred = ml_service.predict(text)
                articles.append(NewsArticle(
                    title=art["title"],
                    description=art["desc"],
                    url=art["url"],
                    source=art["source"],
                    prediction=pred["prediction"],
                    confidence=pred["confidence"],
                    credibility_score=pred["credibility_score"],
                ))
                if pred["prediction"] == "FAKE":
                    fake_count += 1
                else:
                    real_count += 1
    
    return MonitorResponse(
        articles=articles,
        analyzed_count=len(articles),
        fake_count=fake_count,
        real_count=real_count,
    )


# ─── History ──────────────────────────────────────────────────────────────────
@app.get("/api/history", response_model=HistoryResponse, tags=["History"])
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get analysis history."""
    result = await db.get_history(limit=limit, offset=offset)
    return HistoryResponse(**result)


# ─── Dashboard ────────────────────────────────────────────────────────────────
@app.get("/api/dashboard", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard():
    """Get dashboard statistics."""
    stats = await db.get_stats()
    return DashboardStats(**stats)


# ─── Blockchain Endpoints ─────────────────────────────────────────────────────
@app.post("/api/blockchain/verify", tags=["Blockchain"])
async def blockchain_verify(request: TextPredictionRequest):
    """Create a blockchain verification record for a prediction."""
    if not ml_service.is_loaded:
        raise HTTPException(status_code=503, detail="ML model not loaded")
    
    result = ml_service.predict(request.text)
    record = blockchain_service.create_verification_record(request.text, result)
    
    return {
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "credibility_score": result["credibility_score"],
        "blockchain": record,
    }


@app.get("/api/blockchain/info", tags=["Blockchain"])
async def blockchain_info():
    """Get blockchain status and info."""
    return blockchain_service.get_chain_info()


@app.get("/api/blockchain/blocks", tags=["Blockchain"])
async def blockchain_blocks(n: int = Query(10, ge=1, le=50)):
    """Get recent blockchain blocks."""
    return blockchain_service.get_recent_blocks(n)


# ─── Geo-Analytics Endpoints ──────────────────────────────────────────────────
@app.get("/api/heatmap", tags=["Geo-Analytics"])
async def get_heatmap():
    """Get world heatmap data for fake news distribution."""
    # Use sample data for demo; in production, aggregate from DB
    return SAMPLE_HEATMAP_DATA


@app.post("/api/extract-countries", tags=["Geo-Analytics"])
async def extract_countries_from_text(request: TextPredictionRequest):
    """Extract country mentions from text."""
    countries = extract_countries(request.text)
    return {"countries": countries, "total": len(countries)}


# ─── Root ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    """API welcome page."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
