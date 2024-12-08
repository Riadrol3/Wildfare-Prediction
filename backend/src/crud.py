from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from models import (
    Location,
    Prediction,
    HistoricalData,
    Notification,
    EnvironmentalCondition,
    SatelliteData,
    User,
)
from schemas import (
    LocationCreate,
    LocationResponse,
    PredictionCreate,
    PredictionResponse,
    HistoricalDataCreate,
    HistoricalDataResponse,
    NotificationCreate,
    NotificationResponse,
    EnvironmentalConditionCreate,
    EnvironmentalConditionResponse,
    SatelliteDataCreate,
    SatelliteDataResponse,
    UserCreate,
    UserResponse,
)

def to_response(model, schema):
    """Utility function to convert a model instance to a Pydantic response schema."""
    return schema.from_orm(model) if model else None

# Location CRUD operations
async def get_location(db: AsyncSession, location_id: int) -> Optional[LocationResponse]:
    try:
        result = await db.execute(
            select(Location).where(Location.location_id == location_id).options(joinedload(Location.predictions))
        )
        location = result.scalar_one_or_none()
        return to_response(location, LocationResponse) if location else None
    except SQLAlchemyError as e:
        raise ValueError(f"Error fetching location: {str(e)}")

async def create_location(db: AsyncSession, location: LocationCreate) -> LocationResponse:
    try:
        new_location = Location(**location.dict())
        db.add(new_location)
        await db.commit()
        await db.refresh(new_location)
        return to_response(new_location, LocationResponse)
    except SQLAlchemyError as e:
        raise ValueError(f"Error creating location: {str(e)}")

async def get_all_locations(db: AsyncSession) -> List[LocationResponse]:
    try:
        result = await db.execute(select(Location))
        locations = result.scalars().all()
        return [to_response(location, LocationResponse) for location in locations]
    except SQLAlchemyError as e:
        raise ValueError(f"Error fetching locations: {str(e)}")

# Prediction CRUD operations
async def create_prediction(db: AsyncSession, prediction: PredictionCreate) -> PredictionResponse:
    try:
        # Ensure location exists
        result = await db.execute(select(Location).where(Location.location_id == prediction.location_id))
        location = result.scalar_one_or_none()
        if not location:
            raise ValueError("Location does not exist")

        new_prediction = Prediction(**prediction.dict())
        db.add(new_prediction)
        await db.commit()
        await db.refresh(new_prediction)
        return to_response(new_prediction, PredictionResponse)
    except SQLAlchemyError as e:
        raise ValueError(f"Error creating prediction: {str(e)}")

async def get_prediction(db: AsyncSession, prediction_id: int) -> Optional[PredictionResponse]:
    try:
        result = await db.execute(
            select(Prediction).where(Prediction.prediction_id == prediction_id).options(joinedload(Prediction.environmental_conditions))
        )
        prediction = result.scalar_one_or_none()
        return to_response(prediction, PredictionResponse) if prediction else None
    except SQLAlchemyError as e:
        raise ValueError(f"Error fetching prediction: {str(e)}")

# Historical Data CRUD operations
async def create_historical_data(db: AsyncSession, data: HistoricalDataCreate) -> HistoricalDataResponse:
    try:
        new_data = HistoricalData(**data.dict())
        db.add(new_data)
        await db.commit()
        await db.refresh(new_data)
        return to_response(new_data, HistoricalDataResponse)
    except SQLAlchemyError as e:
        raise ValueError(f"Error creating historical data: {str(e)}")

# Notification CRUD operations
async def create_notification(db: AsyncSession, notification: NotificationCreate) -> NotificationResponse:
    try:
        # Ensure user exists
        result = await db.execute(select(User).where(User.user_id == notification.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User does not exist")

        new_notification = Notification(**notification.dict())
        db.add(new_notification)
        await db.commit()
        await db.refresh(new_notification)
        return to_response(new_notification, NotificationResponse)
    except SQLAlchemyError as e:
        raise ValueError(f"Error creating notification: {str(e)}")

async def get_notifications_by_user(db: AsyncSession, user_id: int) -> List[NotificationResponse]:
    try:
        result = await db.execute(select(Notification).where(Notification.user_id == user_id))
        notifications = result.scalars().all()
        return [to_response(notification, NotificationResponse) for notification in notifications]
    except SQLAlchemyError as e:
        raise ValueError(f"Error fetching notifications: {str(e)}")

# Satellite Data CRUD operations
async def create_satellite_data(db: AsyncSession, data: SatelliteDataCreate) -> SatelliteDataResponse:
    try:
        new_data = SatelliteData(**data.dict())
        db.add(new_data)
        await db.commit()
        await db.refresh(new_data)
        return to_response(new_data, SatelliteDataResponse)
    except SQLAlchemyError as e:
        raise ValueError(f"Error creating satellite data: {str(e)}")
