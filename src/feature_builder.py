import pandas as pd
import numpy as np
from fastf1.ergast.structure import Driver
from pandas import DataFrame

from database_utils import get_db_engine
from sqlalchemy import text
from track_config import TRACK_TYPES


def big_table():
    engine = get_db_engine()
    raw_laps = pd.read_sql('SELECT * FROM raw_laps', engine)

    # Listy pomocnicze
    sprint_sessions = ['SQ', 'SS']

    #  Czy to weekend sprinterski
    raw_laps['IsSprint'] = raw_laps['SessionType'].isin(sprint_sessions).astype(int)
    # Obliczamy najszybszy czas dla każdego wyścigu/sesji
    raw_laps['MinLapTime'] = raw_laps.groupby(['Year', 'EventName', 'SessionType'])['LapTime'].transform('min')
    raw_laps['SessionRank'] = raw_laps.groupby(['Year', 'EventName', 'SessionType'])['MinLapTime'].rank(method='min')
    raw_laps['DeltaToLeader'] = raw_laps['LapTime'] - raw_laps['MinLapTime']
    # Najpierw szukamy najszybszego czasu wewnątrz każdego zespołu w danej sesji
    raw_laps['MinTeamTime'] = raw_laps.groupby(['Year','EventName','SessionType','TeamName'])['LapTime'].transform('min')
    raw_laps['DeltaToTeammate'] = raw_laps['LapTime'] - raw_laps['MinTeamTime']

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
    raw_laps['TheoDriverBest'] = raw_laps['Best_S1'] + raw_laps['Best_S2'] + raw_laps['Best_S3']
    # najszybsze teoretyczne kółko w danej sesji
    raw_laps['TheoSessionBest'] = raw_laps.groupby(['Year', 'EventName', 'SessionType'])['DriverTheoBest'].transform('min')
    raw_laps['TheoreticalDelta'] = raw_laps['TheoSessionBest'] - raw_laps['TheoDriverBest']

    # obliczanie i implementacja formy w kwalifikacjach
    qualy_history = raw_laps[raw_laps['SessionType'] == 'Q'][['Year', 'EventName', 'Driver', 'SessionRank']].copy()
    qualy_history['RecentQForm'] = qualy_history.groupby('Driver')['SessionRank'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    )
    qualy_history = qualy_history[['Year', 'EventName', 'Driver', 'RecentQForm']]
    raw_laps = pd.merge(raw_laps, qualy_history, on=['Year', 'EventName', 'Driver'], how='left')

    # wynik w kwalifikacjach rok temu


    # delta w kwalifikacjach rok temu


    # punkty kierowcy z ostatnich 3 wyscigow


    # punkty zespołu z ostatnich 3 wyscigow


    # flaga na deszcz w trakcie weekendu


    # średnia temperatura w sesji przed kwalifikacjami (IsSprint == 0 to FP3, IsSprint == 1 oraz Year <= 2023 to FP1, IsSprint == 1 oraz Year >= 2024 to SQ)


    return raw_laps


if __name__ == "__main__":
    tabela = big_table()
    print("Tabela gotowa")