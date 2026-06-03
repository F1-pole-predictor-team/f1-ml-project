from sqlalchemy import create_engine
from pathlib import Path
import fastf1


def get_db_engine():
    project_root = Path(__file__).parent.parent

    db_path = project_root / 'data' / 'f1_db.sqlite'

    engine = create_engine(f"sqlite:///{db_path}")

    return engine

def setup_fastf1_cache():
    project_root = Path(__file__).parent.parent
    cache_path = project_root / 'data' / 'cache'
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(cache_path.as_posix())