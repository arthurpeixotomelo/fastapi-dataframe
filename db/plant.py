from pathlib import Path
from functools import lru_cache
from contextlib import contextmanager
from typing import Annotated, Iterator, Optional

from fastapi.params import Depends
from sqlmodel import SQLModel, Session, create_engine
from pandas import DataFrame, read_csv, read_sql_table

from .models import PlantData, PlantStats

engine = create_engine(
    f'sqlite:///db/plant_data.db', connect_args={'check_same_thread': False}, 
    pool_pre_ping=True, execution_options={'stream_results': True}
)

LocalSession = Session(engine)

def get_session() -> Iterator[Session]:
    with LocalSession as session:
        yield session

get_session_generator = contextmanager(get_session)

AnnotatedSession = Annotated[Session, Depends(get_session)]

def create_database_metadata():
    SQLModel.metadata.create_all(engine)

def create_database_file():
    create_database_metadata()
    with open(Path(Path.cwd(), 'db', 'plant_data.csv').resolve(), 'r') as f:
        df = read_csv(
            f, parse_dates=['timestamp'], names=PlantData.model_fields.keys(), header=0
        )
        stats = (
            df.groupby('plant_name').describe(include=['float']).unstack().reset_index()
            .rename(columns={'level_0': 'Tipo', 'level_1': 'stat', 0: 'Value'})
            .pivot(index=['plant_name', 'stat'], columns='Tipo', values='Value').reset_index()
            .where(lambda x: x['stat'] != 'count').dropna()
            .assign(
                **{
                    'signal_value': lambda x: x['signal_value'].round(3),
                    'temperature': lambda x: x['temperature'].round(3),
                    'humidity': lambda x: x['humidity'].round(2)
                }
            )
        )
    with get_session_generator() as session:
        session.bulk_insert_mappings(PlantData, df.to_dict(orient="records"))
        session.bulk_insert_mappings(PlantStats, stats.to_dict(orient="records"))
        session.commit()

def fetch_sensor_data(session: AnnotatedSession, plant_name: Optional[str] = None, chunksize: Optional[int] = None) -> Iterator[DataFrame]:
    for chunk in read_sql_table(PlantData.__tablename__, session.bind, chunksize=chunksize):
        if plant_name:
            chunk = chunk[chunk['plant_name'].values == plant_name.title()] 
        chunk.to_json(
            orient='records', lines=True, date_format='iso', date_unit='s', 
            compression={'method': 'gzip', 'compresslevel': 1, 'mtime': 1}
        )
    yield chunk

@lru_cache
def fetch_stats(session: AnnotatedSession, plant_name: Optional[str] = None) -> DataFrame:
    if plant_name:
        df = read_sql_table(PlantStats.__tablename__, session.bind)
        df = df[df['plant_name'].values == plant_name.title()]
    else:
        df = read_sql_table(PlantStats.__tablename__, session.bind)
    return df