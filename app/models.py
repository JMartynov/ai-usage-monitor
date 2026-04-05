from sqlalchemy import Column, Integer, String, DateTime, Text, Float
import datetime
import uuid
from .database import Base

class RequestLog(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    model = Column(String, index=True)
    prompt = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error = Column(String, nullable=True)
