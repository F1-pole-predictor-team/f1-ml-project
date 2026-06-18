import numpy as np
import pandas as pd
from database_utils import get_db_engine
from dicts import TEAM_NAME_MAP, TRACK_TYPES


def big_table():
    """Pobiera surowe dane o okrążeniach z bazy SQL, przetwarza je,

    generuje zaawansowane cechy (features) i agreguje do postaci szerokiej
    tabeli analitycznej (Pivot Table) gotowej pod modelowanie ML.
    """
    engine = get_db_engine()
    raw_laps = pd.read_sql("SELECT * FROM raw_laps", engine)

    # Sesje powiązane z formatem sprinterskim
    sprint_sessions = ["SQ", "SS"]

    # --- 1. IDENTYFIKACJA FORMATU WEEKENDU ---
    # Oznaczamy pojedyncze sesje sprinterskie, a potem rozciągamy flagę 'max'
    # na cały Event (wyścig), aby każdy wiersz z danego weekendu wiedział,
    # że to weekend sprinterski.
    raw_laps["IsSprint"] = (
        raw_laps["SessionType"].isin(sprint_sessions).astype(int)
    )
    raw_laps["IsSprint"] = raw_laps.groupby(["Year", "EventName"])[
        "IsSprint"
    ].transform("max")

    # --- 2. OBLICZANIE PODSTAWOWYCH CZASÓW I RANG ---
    # Najlepsze osobiste okrążenie każdego kierowcy w danej sesji
    raw_laps["DriverBestLap"] = raw_laps.groupby(
        ["Year", "EventName", "SessionType", "Driver"]
    )["LapTime"].transform("min")

    # Absolutnie najszybsze okrążenie sesji (czas lidera)
    raw_laps["MinLapTime"] = raw_laps.groupby(
        ["Year", "EventName", "SessionType"]
    )["LapTime"].transform("min")

    # Ranking kierowców w sesji od 1 do 20 na podstawie ich życiówek
    raw_laps["SessionRank"] = raw_laps.groupby(
        ["Year", "EventName", "SessionType"]
    )["DriverBestLap"].rank(method="dense")

    # Strata czasowa kierowcy do lidera sesji
    raw_laps["DeltaToLeader"] = (
            raw_laps["DriverBestLap"] - raw_laps["MinLapTime"]
    )

    #  POJEDYNEK W WEWNĄTRZZESPOŁOWY
    # Najszybszy czas wewnątrz każdego zespołu w danej sesji
    raw_laps["MinTeamTime"] = raw_laps.groupby(
        ["Year", "EventName", "SessionType", "TeamName"]
    )["LapTime"].transform("min")

    # Strata kierowcy do jego kolegi z zespołu
    raw_laps["DeltaToTeammate"] = (
            raw_laps["DriverBestLap"] - raw_laps["MinTeamTime"]
    )

    # KONFIGURACJA I TYPY TORÓW (One-Hot Encoding)
    # Mapowanie charakterystyki toru ze słownika i zamiana na kolumny 0/1
    raw_laps["TrackType"] = raw_laps["EventName"].map(TRACK_TYPES)
    raw_laps = pd.get_dummies(
        raw_laps, columns=["TrackType"], prefix="Track", dtype="int"
    )

    # TEORETYCZNE OKRĄŻENIE (Ideal Pace)
    # Wyciągamy najlepsze pojedyncze sektory kierowcy z całej sesji
    group_driver = ["Year", "EventName", "SessionType", "Driver"]
    raw_laps["Best_S1"] = raw_laps.groupby(group_driver)[
        "Sector1Time"

    ].transform("min")
    raw_laps["Best_S2"] = raw_laps.groupby(group_driver)[
        "Sector2Time"
    ].transform("min")
    raw_laps["Best_S3"] = raw_laps.groupby(group_driver)[
        "Sector3Time"
    ].transform("min")

    # Teoretyczne najlepsze kółko kierowcy (suma jego najlepszych sektorów)
    raw_laps["DriverTheoBest"] = (
            raw_laps["Best_S1"] + raw_laps["Best_S2"] + raw_laps["Best_S3"]
    )

    # Teoretyczne najlepsze kółko całej sesji (składak absolutnych rekordów)
    raw_laps["TheoSessionBest"] = raw_laps.groupby(
        ["Year", "EventName", "SessionType"]
    )["DriverTheoBest"].transform("min")

    # Delta pokazująca, jak blisko idealnego kółka złożył swój przejazd kierowca
    raw_laps["TheoreticalDelta"] = (
            raw_laps["DriverTheoBest"] - raw_laps["TheoSessionBest"]
    )

    #MAKSYMALNA PRĘDKOŚĆ (Speedtrap Pace)
    # Wyciągamy najwyższą prędkość osiągniętą przez kierowcę na punkcie pomiarowym
    raw_laps["MaxSpeedST"] = raw_laps.groupby(["Year", "EventName", "Driver"])[
        "SpeedST"
    ].transform("max")

    # --- 7. HISTORIA I MOMENTUM PUNKTOWE
    def add_clean_round(df):
        """Generuje ciągłą, chronologiczną sekwencję rund (1, 2, 3...) dla

        każdego sezonu niezależnie, eliminując dziury po odwołanych GP.
        """
        races = (
            df[["season", "round_after"]]
            .drop_duplicates()
            .sort_values(["season", "round_after"])
            .copy()
        )
        races["CleanRound"] = races.groupby("season").cumcount() + 1
        return df.merge(races, on=["season", "round_after"], how="left")

    # Tworzymy czystą sekwencję rund dla tabeli głównej
    races_raw = (
        raw_laps[["Year", "RoundNumber"]]
        .drop_duplicates()
        .sort_values(["Year", "RoundNumber"])
        .copy()
    )
    races_raw["CleanRound"] = races_raw.groupby("Year").cumcount() + 1
    raw_laps = raw_laps.merge(races_raw, on=["Year", "RoundNumber"], how="left")

    # Odkumulowanie i wyliczenie punktów kierowcy z 3 ostatnich wyścigów
    driver_st = pd.read_sql(
        "SELECT season, round_after, Driver, points FROM driver_standings",
        engine,
    )
    driver_st["points"] = pd.to_numeric(driver_st["points"])
    driver_st = driver_st.sort_values(by=["season", "round_after"])
    driver_st["points_in_round"] = (
        driver_st.groupby(["season", "Driver"])["points"]
        .diff()
        .fillna(driver_st["points"])
    )
    driver_st["driver_points_last_3"] = (
        driver_st.groupby(["season", 'Driver'])["points_in_round"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).sum())
    )

    driver_st = add_clean_round(driver_st)
    driver_st["Year"] = driver_st["season"]
    driver_st["NextCleanRound"] = driver_st["CleanRound"] + 1

    # Merge punktów kierowcy (Stan po rundzie X pasuje jako wejście do rundy X+1)
    raw_laps = raw_laps.merge(
        driver_st[["Year", "NextCleanRound", "Driver", "driver_points_last_3"]],
        left_on=["Year", "CleanRound", "Driver"],
        right_on=["Year", "NextCleanRound", "Driver"],
        how="left",
    ).drop(columns=["NextCleanRound"])
    raw_laps["driver_points_last_3"] = raw_laps["driver_points_last_3"].fillna(
        0
    )

    # Odkumulowanie i wyliczenie punktów zespołu z 3 ostatnich wyścigów
    constructor_st = pd.read_sql(
        "SELECT season, round_after, TeamName, points FROM constructor_standings",
        engine,
    )
    constructor_st["points"] = pd.to_numeric(constructor_st['points'])
    constructor_st = constructor_st.sort_values(by=["season", "round_after"])
    constructor_st["points_in_round"] = (
        constructor_st.groupby(["season", "TeamName"])["points"]
        .diff()
        .fillna(constructor_st["points"])
    )
    constructor_st["team_points_last_3"] = (
        constructor_st.groupby(["season", "TeamName"])["points_in_round"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).sum())
    )

    constructor_st = add_clean_round(constructor_st)
    constructor_st["Year"] = constructor_st["season"]
    constructor_st["NextCleanRound"] = constructor_st["CleanRound"] + 1

    # Mapowanie nazw zespołów z FastF1 na małe slugi z bazy SQL
    raw_laps["TeamSlug"] = raw_laps["TeamName"].map(TEAM_NAME_MAP)
    constructor_st = constructor_st.rename(columns={"TeamName": "TeamSlug"})

    # Merge punktów konstruktorow
    raw_laps = raw_laps.merge(
        constructor_st[
            ["Year", "NextCleanRound", "TeamSlug", "team_points_last_3"]
        ],
        left_on=["Year", "CleanRound", "TeamSlug"],
        right_on=["Year", "NextCleanRound", "TeamSlug"],
        how="left",
    ).drop(columns=["NextCleanRound"])
    raw_laps["team_points_last_3"] = raw_laps["team_points_last_3"].fillna(0)

    #  WARUNKI ATMOSFERYCZNE
    # Flaga deszczu: Jeśli w jakiejkolwiek minucie weekendu Rainfall > 0 -> 1, else 0
    raw_laps["WeekendRainFlag"] = (
        raw_laps.groupby(["Year", "EventName"])["Rainfall"]
        .transform(lambda x: (x > 0).max().astype(int))
    )

    # Średnia temperatura toru z ostatniej sesji bezpośrednio przed głównymi kwalifikacjami
    mask_fp3 = (raw_laps["IsSprint"] == 0) & (raw_laps["SessionType"] == "FP3")
    mask_fp1_old = (
            (raw_laps["IsSprint"] == 1)
            & (raw_laps["Year"] <= 2023)
            & (raw_laps["SessionType"] == "FP1")
    )
    mask_sq_new = (
            (raw_laps["IsSprint"] == 1)
            & (raw_laps["Year"] >= 2024)
            & (raw_laps["SessionType"] == "SQ")
    )

    pre_quali_sessions = raw_laps[mask_fp3 | mask_fp1_old | mask_sq_new]
    avg_temp_df = (
        pre_quali_sessions.groupby(["Year", "EventName"])["TrackTemp"]
        .mean()
        .reset_index()
    )
    avg_temp_df = avg_temp_df.rename(columns={"TrackTemp": "AvgPreQualiTemp"})

    raw_laps = raw_laps.merge(avg_temp_df, on=["Year", "EventName"], how='left')
    raw_laps["AvgPreQualiTemp"] = raw_laps["AvgPreQualiTemp"].fillna(
        raw_laps.groupby(["Year", "EventName"])["TrackTemp"].transform("mean")
    )

    #  CZYSZCZENIE DUPLIKATÓW
    # Sortujemy, aby na samej górze były absolutnie najlepsze czasy sesji
    raw_laps = raw_laps.sort_values(
        ["Year", "EventName", "Driver", "SessionType", "SessionRank"]
    )
    # Zostawiamy tylko jeden, najszybszy wiersz dla każdego kierowcy z danej sesji
    best_laps = raw_laps.drop_duplicates(
        subset=["Year", "EventName", "Driver", "SessionType"], keep="first"
    ).copy()

    #  MOMENTUM KWALIFIKACYJNE (Recent Q Form)
    # Wyciągamy historyczne pozycje wyłącznie z kwalifikacji (Q) do obliczenia średniej
    qualy_history = best_laps[best_laps["SessionType"] == "Q"][
        ["Year", "EventName", "Driver", "SessionRank", "RoundNumber"]
    ].copy()
    qualy_history = qualy_history.sort_values(["Year", "RoundNumber"])
    qualy_history["RecentQForm"] = qualy_history.groupby("Driver")[
        "SessionRank"
    ].transform(lambda x: x.shift(1).rolling(window=3, min_periods=1).mean())
    qualy_history = qualy_history[["Year", "EventName", "Driver", "RecentQForm"]]

    best_laps = pd.merge(
        best_laps, qualy_history, on=["Year", "EventName", "Driver"], how="left"
    )

    #AGREGACJA DO STRUKTURY SZEROKIEJ (Pivot Table)
    track_cols = [
        col for col in best_laps.columns if str(col).startswith("Track_")
    ]

    # Budujemy pancerny, stały indeks (lewa ściana tabeli)
    pivot_index = [
                      "Driver", "TeamName", "Year", "EventName", "IsSprint", "RecentQForm",
                      "driver_points_last_3", "team_points_last_3", "WeekendRainFlag",
                      "AvgPreQualiTemp", "MaxSpeedST"
                  ] + track_cols

    # Obracamy tabelę tak, aby każda sesja (FP1, FP2...) dostała własne kolumny dla metryk czasowych
    pivot_table = best_laps.pivot_table(
        index=pivot_index,
        columns=["SessionType"],
        values=[
            "SessionRank", "DeltaToLeader", "DeltaToTeammate", "TheoreticalDelta"
        ],
    )

    # Spłaszczamy dwupoziomowe nagłówki kolumn (np. ('SessionRank', 'Q') -> 'SessionRank_Q')
    pivot_table.columns = [f"{col[0]}_{col[1]}" for col in pivot_table.columns]
    pivot_table = pivot_table.reset_index()

    #Wyniki z poprzedniego roku
    # Wyciągamy czysty wynik z kwalifikacji zeszłego roku i przesuwamy oś czasu o +1
    q_last_year = best_laps[best_laps["SessionType"] == "Q"][
        ["Year", "EventName", "Driver", "SessionRank", "DeltaToLeader"]
    ].copy()
    q_last_year["Year"] = q_last_year["Year"] + 1
    q_last_year = q_last_year.rename(
        columns={
            "SessionRank": "Q_Rank_LastYear",
            "DeltaToLeader": "Q_Delta_LastYear",
        }
    )

    # Doklejamy zeszłoroczne osiągi do bieżącego wiersza
    pivot_table = pd.merge(
        pivot_table, q_last_year, on=["Year", "EventName", "Driver"], how="left"
    )

    return pivot_table


if __name__ == "__main__":
    tabela = big_table()
    print(tabela.head())
    print("Tabela gotowa!")