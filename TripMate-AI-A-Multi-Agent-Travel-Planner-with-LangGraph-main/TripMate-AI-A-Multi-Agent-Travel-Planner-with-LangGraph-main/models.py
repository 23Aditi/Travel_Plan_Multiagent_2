from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    thread_id = Column(String, index=True, nullable=True)
    destination = Column(String, nullable=False)
    duration = Column(String, nullable=True)
    budget = Column(String, nullable=True)
    travelers = Column(String, nullable=True)
    prompt = Column(Text, nullable=True)
    plan_data = Column(Text, nullable=False)  # JSON-encoded full dossier and result data
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trips")
