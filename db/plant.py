from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Annotated, Iterator, Optional

from fastapi.params import Depends
from pandas import DataFrame, read_csv, read_sql_table
from sqlmodel import SQLModel, Session, Field, create_engine

class PlantData(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    signal_value: float
    temperature: float
    humidity: float
    timestamp: datetime
    plant_name: str

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
    with open(Path(Path.cwd(), 'plant_data.db').resolve(), 'r') as f:
        df = read_csv(
            f, parse_dates=['timestamp'], names=PlantData.model_fields.keys(), header=0
        )
    with get_session_generator() as session:
        session.bulk_insert_mappings(PlantData, df.to_dict(orient="records"))
        session.commit()

def fetch_sensor_data(session: AnnotatedSession, table_name: Optional[str] = PlantData.__tablename__, plant_name: Optional[str] = None) -> DataFrame:
    if plant_name:
        df = read_sql_table(table_name, session.bind, chunksize=20000).query(f'plant_name = {plant_name}')
    else:
        df = read_sql_table(table_name, session.bind, chunksize=20000)
    return df