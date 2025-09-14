from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.db import get_db
from app.models import Indicator
from pydantic import BaseModel

router = APIRouter()

class IndicatorResponse(BaseModel):
    symbol: str
    timestamp: datetime
    indicator_type: str
    value: float
    period: int

    class Config:
        from_attributes = True

@router.get("/indicators", response_model=List[IndicatorResponse])
async def get_indicators(
    symbol: Optional[str] = Query(None, description="Stock symbol (e.g., AAPL)"),
    indicator_type: Optional[str] = Query(None, description="Type of indicator (ema, rsi)"),
    period: Optional[int] = Query(None, description="Indicator period"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get technical indicators (EMA, RSI, etc.) for specified symbol(s).
    """
    try:
        # Calculate time filter
        time_filter = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(Indicator).filter(Indicator.ts >= time_filter)
        
        if symbol:
            query = query.filter(Indicator.symbol == symbol.upper())
        
        if indicator_type:
            query = query.filter(Indicator.indicator_type == indicator_type.lower())
        
        if period:
            query = query.filter(Indicator.period == period)
        
        indicators = query.order_by(desc(Indicator.ts)).limit(limit).all()
        
        if not indicators:
            raise HTTPException(
                status_code=404, 
                detail=f"No indicators found for the specified criteria"
            )
        
        # Convert database model to response model
        result = []
        for indicator in indicators:
            result.append(IndicatorResponse(
                symbol=indicator.symbol,
                timestamp=indicator.ts,
                indicator_type=indicator.indicator_type,
                value=float(indicator.value),
                period=int(indicator.period)
            ))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving indicators: {str(e)}")

@router.get("/indicators/latest", response_model=List[IndicatorResponse])
async def get_latest_indicators(
    symbol: Optional[str] = Query(None, description="Stock symbol (e.g., AAPL)"),
    indicator_type: Optional[str] = Query(None, description="Type of indicator (ema, rsi)"),
    db: Session = Depends(get_db)
):
    """
    Get the most recent indicator values for each symbol/type combination.
    """
    try:
        query = db.query(Indicator)
        
        if symbol:
            query = query.filter(Indicator.symbol == symbol.upper())
        
        if indicator_type:
            query = query.filter(Indicator.indicator_type == indicator_type.lower())
        
        # Get latest indicator for each symbol/type/period combination
        latest_indicators = []
        
        # Group by symbol, indicator_type, and period to get latest for each
        grouped = {}
        for indicator in query.all():
            key = (indicator.symbol, indicator.indicator_type, indicator.period)
            if key not in grouped or indicator.ts > grouped[key].ts:
                grouped[key] = indicator
        
        for indicator in grouped.values():
            latest_indicators.append(IndicatorResponse(
                symbol=indicator.symbol,
                timestamp=indicator.ts,
                indicator_type=indicator.indicator_type,
                value=float(indicator.value),
                period=int(indicator.period)
            ))
        
        if not latest_indicators:
            raise HTTPException(status_code=404, detail="No latest indicators found")
        
        return latest_indicators
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving latest indicators: {str(e)}")

@router.get("/indicators/available")
async def get_available_indicators(db: Session = Depends(get_db)):
    """
    Get list of available indicator types and periods.
    """
    try:
        indicators = db.query(Indicator.indicator_type, Indicator.period).distinct().all()
        
        result = {}
        for indicator_type, period in indicators:
            if indicator_type not in result:
                result[indicator_type] = []
            result[indicator_type].append(period)
        
        return {
            "available_indicators": result,
            "total_types": len(result)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving available indicators: {str(e)}")
