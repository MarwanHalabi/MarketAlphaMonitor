from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.db import get_db
from app.models import Price
from pydantic import BaseModel

router = APIRouter()

class QuoteResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    class Config:
        from_attributes = True

    def model_dump(self, *args, **kwargs):
        """Compatibility shim so tests can call model_dump under Pydantic v1."""
        return self.dict(*args, **kwargs)

@router.get("/quotes", response_model=List[QuoteResponse])
async def get_quotes(
    symbol: Optional[str] = Query(None, description="Stock symbol (e.g., AAPL)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get latest market quotes for specified symbol(s).
    If no symbol is provided, returns quotes for all available symbols.
    """
    try:
        # Calculate time filter
        time_filter = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(Price).filter(Price.ts >= time_filter)
        
        if symbol:
            query = query.filter(Price.symbol == symbol.upper())
        
        quotes = query.order_by(desc(Price.ts)).limit(limit).all()
        
        if not quotes:
            raise HTTPException(
                status_code=404, 
                detail=f"No quotes found for symbol: {symbol}" if symbol else "No quotes found"
            )
        
        # Convert database model to response model
        result = []
        for quote in quotes:
            result.append(QuoteResponse(
                symbol=quote.symbol,
                timestamp=quote.ts,
                open=float(quote.o),
                high=float(quote.h),
                low=float(quote.l),
                close=float(quote.c),
                volume=int(quote.v)
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving quotes: {str(e)}")

@router.get("/quotes/latest", response_model=List[QuoteResponse])
async def get_latest_quotes(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    db: Session = Depends(get_db)
):
    """
    Get the most recent quote for each symbol.
    """
    try:
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            query = db.query(Price).filter(Price.symbol.in_(symbol_list))
        else:
            # Get all unique symbols first
            unique_symbols = db.query(Price.symbol).distinct().all()
            symbol_list = [s[0] for s in unique_symbols]
            query = db.query(Price).filter(Price.symbol.in_(symbol_list))
        
        # Get latest quote for each symbol
        latest_quotes = []
        for symbol in symbol_list:
            latest = query.filter(Price.symbol == symbol).order_by(desc(Price.ts)).first()
            if latest:
                latest_quotes.append(QuoteResponse(
                    symbol=latest.symbol,
                    timestamp=latest.ts,
                    open=float(latest.o),
                    high=float(latest.h),
                    low=float(latest.l),
                    close=float(latest.c),
                    volume=int(latest.v)
                ))
        
        if not latest_quotes:
            raise HTTPException(status_code=404, detail="No latest quotes found")
        
        return latest_quotes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving latest quotes: {str(e)}")
