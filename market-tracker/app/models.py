from sqlalchemy import Column, String, DateTime, Numeric, BigInteger, PrimaryKeyConstraint
from sqlalchemy.sql import func
from app.db import Base

class Price(Base):
    __tablename__ = "prices"
    
    symbol = Column(String, nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False)
    o = Column(Numeric(10, 2), nullable=False)  # Open
    h = Column(Numeric(10, 2), nullable=False)  # High
    l = Column(Numeric(10, 2), nullable=False)  # Low
    c = Column(Numeric(10, 2), nullable=False)  # Close
    v = Column(BigInteger, nullable=False)       # Volume
    
    __table_args__ = (
        PrimaryKeyConstraint('symbol', 'ts'),
    )

class Indicator(Base):
    __tablename__ = "indicators"
    
    symbol = Column(String, nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False)
    indicator_type = Column(String, nullable=False)  # 'ema', 'rsi', etc.
    value = Column(Numeric(10, 4), nullable=False)
    period = Column(Numeric(5, 0), nullable=False)  # Period used for calculation
    
    __table_args__ = (
        PrimaryKeyConstraint('symbol', 'ts', 'indicator_type', 'period'),
    )
