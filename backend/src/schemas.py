from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Enums for specific fields
class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class StatusEnum(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

# Base Schema for common fields
class LocationBase(BaseModel):
    region_name: str = Field(..., max_length=255)
    fake_coordinates: Optional[str] = None  # Placeholder for future real coordinates

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    location_id: int

    class Config:
        orm_mode = True

class PredictionBase(BaseModel):
    risk_level: RiskLevelEnum
    date_generated: datetime = Field(default_factory=datetime.utcnow)
    location_id: int

class PredictionCreate(PredictionBase):
    pass

class PredictionResponse(PredictionBase):
    prediction_id: int

    class Config:
        orm_mode = True

class HistoricalDataBase(BaseModel):
    date_occurred: datetime
    location_id: int
    historical_data: str

class HistoricalDataCreate(HistoricalDataBase):
    pass

class HistoricalDataResponse(HistoricalDataBase):
    historical_id: int

    class Config:
        orm_mode = True

class NotificationBase(BaseModel):
    user_id: int
    status: StatusEnum = StatusEnum.PENDING
    message_content: str = Field(..., max_length=255)

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    notification_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class EnvironmentalConditionBase(BaseModel):
    temperature: float = Field(..., ge=-50, le=60)  # Adding realistic range validation
    wind_speed: float = Field(..., ge=0)  # Wind speed cannot be negative
    satellite_id: int
    prediction_id: int

class EnvironmentalConditionCreate(EnvironmentalConditionBase):
    pass

class EnvironmentalConditionResponse(EnvironmentalConditionBase):
    environmental_conditions_id: int

    class Config:
        orm_mode = True

class SatelliteDataBase(BaseModel):
    captured_date: datetime = Field(default_factory=datetime.utcnow)
    location_id: int
    map_layer_details: Optional[str] = None

class SatelliteDataCreate(SatelliteDataBase):
    pass

class SatelliteDataResponse(SatelliteDataBase):
    satellite_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: EmailStr
    role: str = Field(..., max_length=50)
    user_name: str = Field(..., max_length=100)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Enhanced responses for lists and nested relationships
class LocationWithPredictionsResponse(LocationResponse):
    predictions: List[PredictionResponse] = []

    class Config:
        orm_mode = True

class UserWithNotificationsResponse(UserResponse):
    notifications: List[NotificationResponse] = []

    class Config:
        orm_mode = True

class PredictionWithEnvironmentalConditionsResponse(PredictionResponse):
    environmental_conditions: List[EnvironmentalConditionResponse] = []

    class Config:
        orm_mode = True
