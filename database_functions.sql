-- SQL functions for advanced festival queries
-- Run these in your Supabase SQL editor

-- Function to get festival averages and statistics
CREATE OR REPLACE FUNCTION get_festival_averages()
RETURNS TABLE (
    avg_price NUMERIC,
    avg_sentiment NUMERIC,
    avg_popularity NUMERIC,
    price_range JSON
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        AVG(price)::NUMERIC,
        AVG(sentiment_score)::NUMERIC,
        AVG(popularity_score)::NUMERIC,
        json_build_object(
            'min', MIN(price),
            'max', MAX(price),
            'median', PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price)
        )::JSON as price_range
    FROM festivals
    WHERE price IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to get top cities by festival count
CREATE OR REPLACE FUNCTION get_top_cities(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    city VARCHAR,
    festival_count BIGINT,
    avg_price NUMERIC,
    avg_sentiment NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.city,
        COUNT(*)::BIGINT as festival_count,
        AVG(f.price)::NUMERIC as avg_price,
        AVG(f.sentiment_score)::NUMERIC as avg_sentiment
    FROM festivals f
    WHERE f.city IS NOT NULL
    GROUP BY f.city
    ORDER BY festival_count DESC, avg_sentiment DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get top categories by festival count
CREATE OR REPLACE FUNCTION get_top_categories(limit_count INTEGER DEFAULT 10)
RETURNS TABLE (
    category VARCHAR,
    festival_count BIGINT,
    avg_price NUMERIC,
    avg_sentiment NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.category,
        COUNT(*)::BIGINT as festival_count,
        AVG(f.price)::NUMERIC as avg_price,
        AVG(f.sentiment_score)::NUMERIC as avg_sentiment
    FROM festivals f
    WHERE f.category IS NOT NULL
    GROUP BY f.category
    ORDER BY festival_count DESC, avg_sentiment DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to search festivals with full-text search
CREATE OR REPLACE FUNCTION search_festivals(search_query TEXT, limit_count INTEGER DEFAULT 50)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    venue VARCHAR,
    city VARCHAR,
    state VARCHAR,
    date TIMESTAMPTZ,
    price NUMERIC,
    url TEXT,
    description TEXT,
    category VARCHAR,
    ai_summary TEXT,
    sentiment_score NUMERIC,
    popularity_score NUMERIC,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    search_rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.*,
        ts_rank(
            to_tsvector('english', COALESCE(f.name, '') || ' ' || COALESCE(f.description, '') || ' ' || COALESCE(f.venue, '')),
            plainto_tsquery('english', search_query)
        ) as search_rank
    FROM festivals f
    WHERE 
        to_tsvector('english', COALESCE(f.name, '') || ' ' || COALESCE(f.description, '') || ' ' || COALESCE(f.venue, '')) @@ plainto_tsquery('english', search_query)
        OR f.name ILIKE '%' || search_query || '%'
        OR f.description ILIKE '%' || search_query || '%'
        OR f.venue ILIKE '%' || search_query || '%'
    ORDER BY search_rank DESC, f.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get festivals by date range
CREATE OR REPLACE FUNCTION get_festivals_by_date_range(
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    venue VARCHAR,
    city VARCHAR,
    state VARCHAR,
    date TIMESTAMPTZ,
    price NUMERIC,
    url TEXT,
    description TEXT,
    category VARCHAR,
    ai_summary TEXT,
    sentiment_score NUMERIC,
    popularity_score NUMERIC,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT f.*
    FROM festivals f
    WHERE f.date BETWEEN start_date AND end_date
    ORDER BY f.date ASC, f.popularity_score DESC NULLS LAST
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get nearby festivals (by city/state)
CREATE OR REPLACE FUNCTION get_nearby_festivals(
    target_city VARCHAR,
    target_state VARCHAR DEFAULT NULL,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    venue VARCHAR,
    city VARCHAR,
    state VARCHAR,
    date TIMESTAMPTZ,
    price NUMERIC,
    url TEXT,
    description TEXT,
    category VARCHAR,
    ai_summary TEXT,
    sentiment_score NUMERIC,
    popularity_score NUMERIC,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    distance_score INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.*,
        CASE 
            WHEN f.city ILIKE target_city AND f.state ILIKE COALESCE(target_state, f.state) THEN 1
            WHEN f.city ILIKE target_city THEN 2
            WHEN f.state ILIKE COALESCE(target_state, f.state) THEN 3
            ELSE 4
        END as distance_score
    FROM festivals f
    WHERE 
        f.city ILIKE target_city 
        OR f.state ILIKE COALESCE(target_state, f.state)
        OR f.city ILIKE '%' || target_city || '%'
    ORDER BY distance_score ASC, f.popularity_score DESC NULLS LAST
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Add full-text search index for better search performance
CREATE INDEX IF NOT EXISTS idx_festivals_search 
ON festivals USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(venue, '')));

-- Add index for date range queries
CREATE INDEX IF NOT EXISTS idx_festivals_date 
ON festivals USING btree (date) TABLESPACE pg_default;

-- Add index for sentiment and popularity scores
CREATE INDEX IF NOT EXISTS idx_festivals_sentiment 
ON festivals USING btree (sentiment_score) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_festivals_popularity 
ON festivals USING btree (popularity_score) TABLESPACE pg_default;

-- Add composite index for location-based queries
CREATE INDEX IF NOT EXISTS idx_festivals_location 
ON festivals USING btree (city, state) TABLESPACE pg_default;

-- Add index for price range queries
CREATE INDEX IF NOT EXISTS idx_festivals_price 
ON festivals USING btree (price) TABLESPACE pg_default;
