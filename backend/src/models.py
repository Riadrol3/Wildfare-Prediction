#models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from database import Base
from datetime import datetime
import enum

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

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    OFFICER = "OFFICER"
    RESIDENT = "RESIDENT"
    CONSERVATIONIST = "CONSERVATIONIST"
    ANALYST = "ANALYST"

# Location Table
class Location(Base):
    __tablename__ = "location"

    location_id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(255), unique=True, nullable=False, index=True)
    geo_coordinates = Column(String(50), nullable=False, default="0,0")  # Placeholder for real coordinates
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions = relationship("Prediction", back_populates="location", cascade="all, delete-orphan")
    historical_data = relationship("HistoricalData", back_populates="location", cascade="all, delete-orphan")
    satellite_data = relationship("SatelliteData", back_populates="location", cascade="all, delete-orphan")

# Prediction Table
class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, index=True)
    risk_level = Column(ENUM(RiskLevelEnum, name="risk_level_enum"), nullable=False)
    date_generated = Column(DateTime, nullable=False, default=datetime.utcnow)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False)
    prediction_type = Column(String(100), nullable=False, default="Default")

    # Relationships
    location = relationship("Location", back_populates="predictions")
    environmental_conditions = relationship("EnvironmentalCondition", back_populates="prediction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_prediction_location_id", "location_id"),
    )

# Historical Data Table
class HistoricalData(Base):
    __tablename__ = "historical_data"

    historical_id = Column(Integer, primary_key=True, index=True)
    date_occurred = Column(DateTime, nullable=False)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False)
    historical_data = Column(Text, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="historical_data")

# Notification Table
class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    status = Column(ENUM(StatusEnum, name="status_enum"), nullable=False, default=StatusEnum.PENDING.value)
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

    # Constraints
    __table_args__ = (
        CheckConstraint("temperature BETWEEN -50 AND 60", name="check_temperature_range"),
        CheckConstraint("wind_speed >= 0", name="check_wind_speed_non_negative"),
    )

    # Relationships
    prediction = relationship("Prediction", back_populates="environmental_conditions")
    satellite_data = relationship("SatelliteData", back_populates="environmental_conditions")

# Satellite Data Table
class SatelliteData(Base):
    __tablename__ = "satellite_data"

    satellite_id = Column(Integer, primary_key=True, index=True)
    captured_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    location_id = Column(Integer, ForeignKey("location.location_id", ondelete="CASCADE"), nullable=False)
    map_layer_details = Column(Text, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="satellite_data")
    environmental_conditions = relationship("EnvironmentalCondition", back_populates="satellite_data", cascade="all, delete-orphan")

# User Table
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(ENUM(RoleEnum, name="role_enum"), nullable=False)
    user_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
