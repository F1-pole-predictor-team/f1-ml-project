import pandas as pd
from database_utils import get_db_engine
from track_config import TRACK_TYPES


def big_table():
    engine = get_db_engine()
    raw_laps = pd.read_sql('SELECT * FROM raw_laps', engine)

    # Listy pomocnicze
    sprint_sessions = ['SQ', 'SS']

    #  Czy to weekend sprinterski
    raw_laps['IsSprint'] = raw_laps['SessionType'].isin(sprint_sessions).astype(int)
    raw_laps['IsSprint'] = raw_laps.groupby(['Year', 'EventName'])['IsSprint'].transform('max')

    # najszybszy czas kazdego kierowcy w sesji
    raw_laps['DriverBestLap'] = raw_laps.groupby(['Year', 'EventName', 'SessionType', 'Driver'])['LapTime'].transform('min')

    # Obliczamy najszybszy czas dla każdego wyścigu/sesji
    raw_laps['MinLapTime'] = raw_laps.groupby(['Year', 'EventName', 'SessionType'])['LapTime'].transform('min')
    raw_laps['SessionRank'] = raw_laps.groupby(['Year', 'EventName', 'SessionType'])['DriverBestLap'].rank(method='dense')
    raw_laps['DeltaToLeader'] = raw_laps['DriverBestLap'] - raw_laps['MinLapTime']

    # Najpierw szukamy najszybszego czasu wewnątrz każdego zespołu w danej sesji
    raw_laps['MinTeamTime'] = raw_laps.groupby(['Year','EventName','SessionType','TeamName'])['LapTime'].transform('min')
    raw_laps['DeltaToTeammate'] = raw_laps['DriverBestLap'] - raw_laps['MinTeamTime']

    # mapowanie słownika
    raw_laps['TrackType'] = raw_laps['EventName'].map(TRACK_TYPES)
    # one hot encoding, tworzy kolumny dla kazdego typu toru i wstawia 0 i 1
    raw_laps = pd.get_dummies(raw_laps, columns=['TrackType'], prefix='Track', dtype ='int')

    # najszybsze sektory w danej sesji
    group_driver = ['Year', 'EventName', 'SessionType', 'Driver']
    raw_laps['Best_S1'] = raw_laps.groupby(group_driver)['Sector1Time'].transform('min')
    raw_laps['Best_S2'] = raw_laps.groupby(group_driver)['Sector2Time'].transform('min')
    raw_laps['Best_S3'] = raw_laps.groupby(group_driver)['Sector3Time'].transform('min')
    # najszybsze teoretyczne kółko kierowcy w danej sesji
    raw_laps['DriverTheoBest'] = raw_laps['Best_S1'] + raw_laps['Best_S2'] + raw_laps['Best_S3']
    # najszybsze teoretyczne kółko w danej sesji
    raw_laps['TheoSessionBest'] = raw_laps.groupby(['Year', 'EventName', 'SessionType'])['DriverTheoBest'].transform('min')
    # delta do najszybszego kółka w sesji
    raw_laps['TheoreticalDelta'] = raw_laps['DriverTheoBest'] - raw_laps['TheoSessionBest']

    # sortowanie by najszybsze okrążenia były u góry
    raw_laps = raw_laps.sort_values(['Year', 'EventName', 'Driver', 'SessionType', 'SessionRank'])
    # usunięcie duplikatów = zostają tylko najlepsze okrążenia każdego zawodnika z każdej sesji
    best_laps = raw_laps.drop_duplicates(subset= ['Year', 'EventName', 'Driver', 'SessionType'], keep='first')

    # obliczanie i implementacja formy w kwalifikacjach
    qualy_history = best_laps[best_laps['SessionType'] == 'Q'][['Year', 'EventName', 'Driver', 'SessionRank', 'RoundNumber']].copy()
    qualy_history = qualy_history.sort_values(['Year', 'RoundNumber'])
    qualy_history['RecentQForm'] = qualy_history.groupby('Driver')['SessionRank'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    )
    qualy_history = qualy_history[['Year', 'EventName', 'Driver', 'RecentQForm']]
    best_laps = pd.merge(best_laps, qualy_history, on=['Year', 'EventName', 'Driver'], how='left')

    # pivotowanie tabeli
    pivot_table = best_laps.pivot_table(
        index= ['Driver', 'TeamName', 'Year', 'EventName', 'IsSprint', 'RecentQForm', 'Track_high_aero', 'Track_high_speed', 'Track_street', 'Track_technical'],
        columns= ['SessionType'],
        values= ['SessionRank', 'DeltaToLeader', 'DeltaToTeammate', 'TheoreticalDelta'],
    )
    # spłaszczenie kolumn
    pivot_table.columns = [f'{col[0]}_{col[1]}' for col in pivot_table.columns]
    # reset indexów
    pivot_table = pivot_table.reset_index()


    # wynik w kwalifikacjach rok temu


    # delta w kwalifikacjach rok temu


    # maksymalna prędkość podczas weekendu (speedtrap)


    # punkty kierowcy z ostatnich 3 wyscigow


    # punkty zespołu z ostatnich 3 wyscigow


    # flaga na deszcz w trakcie weekendu


    # średnia temperatura w sesji przed kwalifikacjami (IsSprint == 0 to FP3, IsSprint == 1 oraz Year <= 2023 to FP1, IsSprint == 1 oraz Year >= 2024 to SQ)


    return pivot_table


if __name__ == "__main__":
    tabela = big_table()
    print("Tabela gotowa")

# test skutecznosci = z sprintami i bez

# opcje przewidywania:
# 1. przewidywanie zwycięzcy (target is_pole, procentowe szanse dla kazdego)
# 2. przewidywanie straty do lidera (delty) (target DeltaToLeader_Q, delta dla kazdego)