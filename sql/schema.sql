CREATE TABLE IF NOT EXISTS raw_laps ( --tworzy tabele jezeli nie istnieje
    Driver TEXT, --nazwa kolumny i typ
    LapTime FLOAT,
    S1_time FLOAT,
    S2_time FLOAT,
    S3_time FLOAT,
    Compound TEXT,
    Tyre_life FLOAT,
    Event_type TEXT,
    Event_name TEXT
);