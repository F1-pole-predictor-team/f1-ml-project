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
    session_type TEXT #dodaje bo musimy widziec odzielnie FP1 FP2 itd. zeby dalo sie je odroznic
    TrackTemp FLOAT); #od tej kolumny w dol najwaniejsze kolumny z pogoda
    TrackTemp FLOAT,
    AirTemp FLOAT,
    Humidity FLOAT,
    Pressure FLOAT,
    WindSpeed FLOAT,
    WindDirection FLOAT,
    Rainfall BOOLEAN
