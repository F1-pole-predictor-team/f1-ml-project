from fastf1.ergast import Ergast
import fastf1
import pandas as pd
from database_utils import get_db_engine, setup_fastf1_cache
import time



def download_multi_year_standings():
    setup_fastf1_cache()

    ergast = Ergast()
    engine = get_db_engine()

    all_standings_list = []

    for season in [2022, 2023, 2024, 2025]:
        print(f"Pobieranie klasyfikacji dla sezonu {season}")

        schedule = fastf1.get_event_schedule(season)
        total_rounds = schedule['RoundNumber'].max()

        for round_to_check in range(1, total_rounds + 1):
            try:
                standings = ergast.get_driver_standings(season=season, round=round_to_check)

                if not standings.content:
                    continue

                df_standings = standings.content[0]
                cols_to_keep = ['position', 'points', 'wins', 'driverCode']
                df_filtered = df_standings[cols_to_keep].copy()
                    # zmiana nazwy by pasowałą
                df_filtered = df_filtered.rename(columns={'driverCode': 'Driver'})
                df_filtered['season'] = season
                df_filtered['round_after'] = round_to_check

                # 2. Zamiast zapisu do bazy, dorzucamy tabelkę do koszyka
                all_standings_list.append(df_filtered)
                print(f"  Pobrano rundę {round_to_check}/{total_rounds}")

                time.sleep(2)

            except Exception as e:
                print(f" Błąd w rundzie {round_to_check}: {e}")

    print("Łączenie i zapisywanie danych do bazy")

    # 3. Sklejamy wszystkie małe tabelki z koszyka w jedną wielką
    final_df = pd.concat(all_standings_list, ignore_index=True)

    # 4. Zapisujemy wszystko do bazy za jednym razem z replace, żeby wyczyścić ewentualne śmieci
    final_df.to_sql('driver_standings', con=engine, if_exists='replace', index=False)

    print("Wszystkie sezony zrzucone perfekcyjnie")


if __name__ == "__main__":
    download_multi_year_standings()