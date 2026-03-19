-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Convert ohlcv_candles to hypertable after SQLAlchemy creates it
-- (called after init_db() runs)
-- SELECT create_hypertable('ohlcv_candles', 'time', if_not_exists => TRUE);
