from datetime import datetime

from sqlmodel import SQLModel, Field

class PlantData(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    signal_value: float
    temperature: float
    humidity: float
    timestamp: datetime
    plant_name: str

class PlantStats(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    plant_name: str
    stat: str
    temperature: float
    humidity: float
    signal_value: float
