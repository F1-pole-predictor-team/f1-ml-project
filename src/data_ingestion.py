import fastf1
import pandas as pd
from database_utils import get_db_engine
from pathlib import Path


def test_fastf1_download():
    # Namierzamy główny folder projektu tak samo jak w bazie
    project_root = Path(__file__).parent.parent
    cache_path = project_root / 'data' / 'cache'

    # Tworzymy folder, jeśli go nie ma (używając nowej składni pathlib)
    cache_path.mkdir(parents=True, exist_ok=True)

    # Włączamy cache przekazując ścieżkę jako tekst (as_posix)
    fastf1.Cache.enable_cache(cache_path.as_posix())

    print("Łączenie z serwerami F1...")
    session = fastf1.get_session(2024, 'Bahrain', 'Q')
    session.load()

    laps = session.laps.pick_quicklaps()
    df_laps = laps[['Driver', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife']].copy()

    time_columns = ['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']
    for col in time_columns:
        df_laps[col] = df_laps[col].dt.total_seconds()

    print("Zapisywanie do pliku SQLite...")
    engine = get_db_engine()

    try:
        df_laps.to_sql('raw_laps', con=engine, if_exists='append', index=False)
        print("\n✅ Dane zapisane w głównym folderze data/f1_db.sqlite")
    except Exception as e:
        print(f"❌ Błąd zapisu: {e}")


if __name__ == "__main__":
    test_fastf1_download()