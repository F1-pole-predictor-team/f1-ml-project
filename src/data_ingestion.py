import time
import fastf1
import pandas as pd
from database_utils import get_db_engine
from pathlib import Path
from sqlalchemy import text


def download_all_20242025sessions():
    project_root = Path(__file__).parent.parent
    cache_path = project_root / 'data' / 'cache'
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path.as_posix())

    print("Resetowanie tabeli raw_laps w bazie danych...")
    engine = get_db_engine()
    with engine.connect() as con:
        con.execute(text("DROP TABLE IF EXISTS raw_laps"))
        con.commit()

    seasons = [2024, 2025]
    for year in seasons:
        print("Pobieranie kalendarza na sezon 2024 oraz 2025...")
        schedule = fastf1.get_event_schedule(year)
        races = schedule[schedule['RoundNumber'] > 0]

        # Pobiera Fp1,2,3 i Q zamiast tylko Q
        sessions_to_get = ['FP1', 'FP2', 'FP3', 'Q']
        for index, row in races.iterrows():
            event_name = row['EventName']
            print(f"\n--- Przetwarzanie weekendu: {year} - {event_name} ---")

            for session_type in sessions_to_get:
                try:
                    print(f"  -> Pobieranie sesji: {session_type}...")
                    session = fastf1.get_session(year, event_name, session_type)
                    session.load()

                    laps = session.laps.pick_quicklaps()
                    dane_pogodowe = laps.get_weather_data() #dodajemy pogode do okrazen
                    if laps.empty:
                        print(f"  Brak szybkich okrążeń dla {event_name} w sesji {session_type}. Pomijam.")
                        continue

                    df_laps = laps[
                        ['Driver', 'LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife']].copy()
                     # Dodanie event_name i danych pogodowych do tabeli
                    df_laps['EventName'] = event_name
                    df_laps['SessionType'] = session_type
                    df_laps['TrackTemp'] = dane_pogodowe['TrackTemp'].values
                    df_laps['Humidity'] = dane_pogodowe['Humidity'].values
                    df_laps['AirTemp'] = dane_pogodowe['AirTemp'].values
                    df_laps['WindSpeed'] = dane_pogodowe['WindSpeed'].values
                    df_laps['WindDirection'] = dane_pogodowe['WindDirection'].values
                    df_laps['Rainfall'] = dane_pogodowe['Rainfall'].values
                    time_columns = ['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']
                    for col in time_columns:
                        df_laps[col] = df_laps[col].dt.total_seconds()

                    df_laps.to_sql('raw_laps', con=engine, if_exists='append', index=False)
                    print(f" Zapisano sesję {session_type} do bazy.")

                    #  Usypiamy skrypt na 2 sekundy, żeby nie dostać bana od API (limit 500 zapytań)
                    time.sleep(2)

                except Exception as e:
                    print(f"   Błąd (pomijam tę sesję): {e}")

    print("\n🏆 Pobieranie danych z całego sezonu (Treningi + Kwale) zakończone!")


if __name__ == "__main__":
    download_all_20242025sessions()