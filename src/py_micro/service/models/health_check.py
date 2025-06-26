from modelrepo.models.base import SQLModel
from sqlalchemy import Column, Integer, DateTime
import datetime


class HealthCheck(SQLModel):
    __tablename__ = "health_check"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self) -> str:
        return f"HealthCheck(id={self.id}, timestamp={self.timestamp})"
