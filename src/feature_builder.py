import pandas as pd
import numpy as np
from database_utils import get_db_engine
from sqlalchemy import text


def big_table():
    engine = get_db_engine()
    raw_laps = pd.read_sql('SELECT * FROM raw_laps', engine)

    # Listy pomocnicze
    qualy_sessions = ['Q', 'SQ', 'SS']
    sprint_sessions = ['SQ', 'SS']

    # 1. Czy to są jakiekolwiek kwalifikacje?
    raw_laps['IsQualifying'] = raw_laps['SessionType'].isin(qualy_sessions).astype(int)
    raw_laps['IsSprint'] = raw_laps['SessionType'].isin(sprint_sessions).astype(int)

    conditions = [
        (raw_laps['SessionType']== 'Q'),
        (raw_laps['SessionType'].isin(sprint_sessions))
    ]
    choices = [1.0, 0.9]      # nadaje wagi wszystkim wierszom na raz
    raw_laps['SessionWeight'] = np.select(conditions, choices, default=0.6)
