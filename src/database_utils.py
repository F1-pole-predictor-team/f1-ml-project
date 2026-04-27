from sqlalchemy import create_engine
from pathlib import Path
import fastf1


def get_db_engine():
    # __file__ to ścieżka do tego skryptu (src/database_utils.py)
    # .parent to folder src/
    # .parent.parent to główny folder projektu (f1-ml-project)
    project_root = Path(__file__).parent.parent

    # Sklejamy ścieżkę do pliku sqlite w głównym folderze data
    db_path = project_root / 'data' / 'f1_db.sqlite'

    # Tworzymy połączenie
    engine = create_engine(f"sqlite:///{db_path}")

    return engine

def setup_fastf1_cache():
    project_root = Path(__file__).parent.parent
    cache_path = project_root / 'data' / 'cache'
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path.as_posix())