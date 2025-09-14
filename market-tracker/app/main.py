from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routes import quotes, indicators, health
from app.db import engine, Base

app = FastAPI(
    title="Market Tracker API",
    description="A self-hosted market tracker with real-time data from Yahoo Finance",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(quotes.router, prefix="/api/v1", tags=["quotes"])
app.include_router(indicators.router, prefix="/api/v1", tags=["indicators"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Simple UI page for quick checks"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Market Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
            .url { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 Market Tracker</h1>
            <p>Real-time market data from Yahoo Finance</p>
            
            <h2>API Endpoints</h2>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/api/v1/quotes</span>
                <p>Get latest market quotes</p>
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/api/v1/indicators</span>
                <p>Get technical indicators (EMA, RSI)</p>
            </div>
            <div class="endpoint">
                <span class="method">GET</span> <span class="url">/api/v1/health</span>
                <p>Health check endpoint</p>
            </div>
            
            <h2>External Services</h2>
            <p><a href="http://localhost:3000" target="_blank">Grafana Dashboard</a> - Data visualization</p>
        </div>
    </body>
    </html>
    """
