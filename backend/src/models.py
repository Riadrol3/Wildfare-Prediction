
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from database import Base
import enum
from datetime import datetime

# Enums for specific fields
class RiskLevelEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ImpactLevelEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class StatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

# Location Table
class Location(Base):
    __tablename__ = "location"

    location_id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(255), unique=True, nullable=False)
    fake_coordinates = Column(String(50))

    # Relationships
    predictions = relationship("Prediction", back_populates="location", cascade="all, delete")
    historical_data = relationship("HistoricalData", back_populates="location", cascade="all, delete")


# Prediction Table
class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, index=True)
    risk_level = Column(ENUM(RiskLevelEnum), nullable=False)
    date_generated = Column(DateTime, nullable=False, default=datetime.utcnow)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False)

    # Relationships
    location = relationship("Location", back_populates="predictions")
    environmental_conditions = relationship("EnvironmentalCondition", back_populates="prediction", cascade="all, delete")


# Historical Data Table
class HistoricalData(Base):
    __tablename__ = "historical_data"

    historical_id = Column(Integer, primary_key=True, index=True)
    date_occurred = Column(DateTime, nullable=False)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False)
    historical_data = Column(Text)

    # Relationships
    location = relationship("Location", back_populates="historical_data")


# Notifications Table
class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    status = Column(ENUM(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    message_content = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")


# Environmental Conditions Table
class EnvironmentalCondition(Base):
    __tablename__ = "environmental_conditions"

    environmental_conditions_id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    satellite_id = Column(Integer, ForeignKey("satellite_data.satellite_id", ondelete="CASCADE"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id", ondelete="CASCADE"), nullable=False)

    # Relationships
    prediction = relationship("Prediction", back_populates="environmental_conditions")
    satellite_data = relationship("SatelliteData", back_populates="environmental_conditions")


# Satellite Data Table
class SatelliteData(Base):
    __tablename__ = "satellite_data"

    satellite_id = Column(Integer, primary_key=True, index=True)
    captured_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False)
    map_layer_details = Column(Text)

    # Relationships
    location = relationship("Location")
    environmental_conditions = relationship("EnvironmentalCondition", back_populates="satellite_data", cascade="all, delete")


# User Table
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    user_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
