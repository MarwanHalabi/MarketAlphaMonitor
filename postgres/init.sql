-- Market Tracker Database Schema
-- This script initializes the database with required tables and indexes

-- Create database if it doesn't exist (this will be handled by docker-compose)
-- CREATE DATABASE market_tracker;

-- Connect to the database
\c market_tracker;

-- Create prices table
CREATE TABLE IF NOT EXISTS prices (
    symbol TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    o NUMERIC(10, 2) NOT NULL,  -- Open price
    h NUMERIC(10, 2) NOT NULL,  -- High price
    l NUMERIC(10, 2) NOT NULL,  -- Low price
    c NUMERIC(10, 2) NOT NULL,  -- Close price
    v BIGINT NOT NULL,          -- Volume
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(symbol, ts)
);

-- Create indicators table
CREATE TABLE IF NOT EXISTS indicators (
    symbol TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    indicator_type TEXT NOT NULL,  -- 'ema', 'rsi', 'sma', etc.
    value NUMERIC(10, 4) NOT NULL,
    period INTEGER NOT NULL,       -- Period used for calculation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY(symbol, ts, indicator_type, period)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts ON prices(symbol, ts DESC);
CREATE INDEX IF NOT EXISTS idx_prices_ts ON prices(ts DESC);
CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices(symbol);

CREATE INDEX IF NOT EXISTS idx_indicators_symbol_ts ON indicators(symbol, ts DESC);
CREATE INDEX IF NOT EXISTS idx_indicators_type ON indicators(indicator_type);
CREATE INDEX IF NOT EXISTS idx_indicators_symbol_type ON indicators(symbol, indicator_type);
CREATE INDEX IF NOT EXISTS idx_indicators_ts ON indicators(ts DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_prices_updated_at 
    BEFORE UPDATE ON prices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_indicators_updated_at 
    BEFORE UPDATE ON indicators 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for latest prices
CREATE OR REPLACE VIEW latest_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    ts,
    o,
    h,
    l,
    c,
    v,
    created_at,
    updated_at
FROM prices
ORDER BY symbol, ts DESC;

-- Create view for latest indicators
CREATE OR REPLACE VIEW latest_indicators AS
SELECT DISTINCT ON (symbol, indicator_type, period)
    symbol,
    ts,
    indicator_type,
    value,
    period,
    created_at,
    updated_at
FROM indicators
ORDER BY symbol, indicator_type, period, ts DESC;

-- Create materialized view for daily aggregates (optional)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_aggregates AS
SELECT 
    symbol,
    DATE(ts) as date,
    MIN(o) as day_low,
    MAX(h) as day_high,
    FIRST_VALUE(o) OVER (PARTITION BY symbol, DATE(ts) ORDER BY ts) as day_open,
    LAST_VALUE(c) OVER (PARTITION BY symbol, DATE(ts) ORDER BY ts ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as day_close,
    SUM(v) as day_volume,
    COUNT(*) as data_points
FROM prices
GROUP BY symbol, DATE(ts), o, h, c, ts
ORDER BY symbol, date DESC;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_daily_aggregates_symbol_date ON daily_aggregates(symbol, date DESC);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_daily_aggregates()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW daily_aggregates;
END;
$$ LANGUAGE plpgsql;

-- Insert some sample data for testing (optional)
-- This can be removed in production
INSERT INTO prices (symbol, ts, o, h, l, c, v) VALUES 
('AAPL', NOW() - INTERVAL '1 hour', 150.00, 151.00, 149.50, 150.50, 1000000),
('MSFT', NOW() - INTERVAL '1 hour', 300.00, 301.00, 299.50, 300.50, 800000),
('GOOGL', NOW() - INTERVAL '1 hour', 2500.00, 2510.00, 2495.00, 2505.00, 500000)
ON CONFLICT (symbol, ts) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Create a function to get market summary
CREATE OR REPLACE FUNCTION get_market_summary()
RETURNS TABLE (
    symbol TEXT,
    latest_price NUMERIC,
    latest_volume BIGINT,
    price_change NUMERIC,
    price_change_percent NUMERIC,
    last_updated TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_prices AS (
        SELECT DISTINCT ON (symbol)
            symbol,
            c as latest_price,
            v as latest_volume,
            ts as last_updated
        FROM prices
        ORDER BY symbol, ts DESC
    ),
    previous_prices AS (
        SELECT DISTINCT ON (symbol)
            symbol,
            c as previous_price
        FROM prices
        WHERE ts < (SELECT MAX(ts) FROM prices) - INTERVAL '1 minute'
        ORDER BY symbol, ts DESC
    )
    SELECT 
        lp.symbol,
        lp.latest_price,
        lp.latest_volume,
        (lp.latest_price - COALESCE(pp.previous_price, lp.latest_price)) as price_change,
        CASE 
            WHEN COALESCE(pp.previous_price, lp.latest_price) > 0 
            THEN ((lp.latest_price - COALESCE(pp.previous_price, lp.latest_price)) / COALESCE(pp.previous_price, lp.latest_price)) * 100
            ELSE 0
        END as price_change_percent,
        lp.last_updated
    FROM latest_prices lp
    LEFT JOIN previous_prices pp ON lp.symbol = pp.symbol
    ORDER BY lp.symbol;
END;
$$ LANGUAGE plpgsql;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Market Tracker database initialized successfully!';
    RAISE NOTICE 'Tables created: prices, indicators';
    RAISE NOTICE 'Views created: latest_prices, latest_indicators';
    RAISE NOTICE 'Materialized view created: daily_aggregates';
    RAISE NOTICE 'Function created: get_market_summary()';
END $$;
