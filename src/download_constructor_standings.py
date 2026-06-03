from fastf1.ergast import Ergast
import fastf1
import pandas as pd
from database_utils import get_db_engine, setup_fastf1_cache
import time


def download_constructor_standings():
    setup_fastf1_cache()

    ergast = Ergast()
    engine = get_db_engine()

    all_standings_list = []

    for season in [2022, 2023, 2024, 2025]:
        print(f"Pobieranie klasyfikacji konstruktorów dla sezonu {season}")

        schedule = fastf1.get_event_schedule(season)
        total_rounds = schedule['RoundNumber'].max()

        for round_to_check in range(1, total_rounds + 1):
            try:
                standings = ergast.get_constructor_standings(season=season, round=round_to_check)

                if not standings.content:
                    continue

                df_standings = standings.content[0]

                cols_to_keep = ['position', 'points', 'wins', 'constructorId']
                df_filtered = df_standings[cols_to_keep].copy()

                # zmiana nazwy by pasowała do reszty
                df_filtered = df_filtered.rename(columns={'constructorId': 'TeamName'})
                df_filtered['season'] = season
                df_filtered['round_after'] = round_to_check

                all_standings_list.append(df_filtered)
                print(f"  Pobrano rundę {round_to_check}/{total_rounds}")

                time.sleep(2)

            except Exception as e:
                print(f" Błąd w rundzie {round_to_check}: {e}")

    print("Sklejanie i zapisywanie do bazy")

    if all_standings_list:
        final_df = pd.concat(all_standings_list, ignore_index=True)
        final_df.to_sql('constructor_standings', con=engine, if_exists='replace', index=False)
        print("Klasyfikacja konstruktorów zapisana!")
    else:
        print("Coś poszło nie tak, koszyk jest pusty.")


if __name__ == "__main__":
    download_constructor_standings()