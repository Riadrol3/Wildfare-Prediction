from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import logging
from models import (
    Location,
    Prediction,
    HistoricalData,
    Notification,
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
    SatelliteDataCreate,
    SatelliteDataResponse,
)

# Configure logger
logger = logging.getLogger("wildfire_crud")
logging.basicConfig(level=logging.INFO)

class CRUDException(Exception):
    """Custom exception for CRUD operations"""
    pass

def to_response(model, schema):
    """Utility function to convert a model instance to a Pydantic response schema."""
    return schema.from_orm(model) if model else None

MAX_LIMIT = 1000  # Upper limit for pagination

# Location CRUD operations
async def get_all_locations(db: AsyncSession, limit: int = 100, offset: int = 0) -> List[LocationResponse]:
    if limit > MAX_LIMIT:
        raise CRUDException(f"Limit cannot exceed {MAX_LIMIT}")
    try:
        result = await db.execute(select(Location).order_by(Location.region_name).offset(offset).limit(limit))
        locations = result.scalars().all()
        return [to_response(location, LocationResponse) for location in locations]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise CRUDException(f"Error fetching locations: {str(e)}")

async def create_location(db: AsyncSession, location: LocationCreate) -> LocationResponse:
    try:
        # Check for duplicate region_name
        existing = await db.execute(select(Location).where(Location.region_name == location.region_name))
        if existing.scalar_one_or_none():
            raise CRUDException("Region name already exists")

        new_location = Location(**location.dict())
        db.add(new_location)
        await db.commit()
        await db.refresh(new_location)
        return to_response(new_location, LocationResponse)
    except SQLAlchemyError as e:
        logger.error(f"Error creating location: {str(e)}")
        await db.rollback()
        raise CRUDException(f"Error creating location: {str(e)}")

async def get_location(db: AsyncSession, location_id: int) -> Optional[LocationResponse]:
    try:
        result = await db.execute(select(Location).where(Location.location_id == location_id))
        location = result.scalar_one_or_none()
        return to_response(location, LocationResponse) if location else None
    except SQLAlchemyError as e:
        logger.error(f"Error fetching location: {str(e)}")
        raise CRUDException(f"Error fetching location: {str(e)}")

# Prediction CRUD operations
async def create_prediction(db: AsyncSession, prediction: PredictionCreate) -> PredictionResponse:
    try:
        # Ensure location exists
        location = await db.execute(select(Location).where(Location.location_id == prediction.location_id))
        if not location.scalar_one_or_none():
            raise CRUDException("Location does not exist")

        # Calculate FDI and risk level
        fdi = (
            2 * prediction.temperature
            - 0.5 * prediction.humidity
            + 0.3 * prediction.wind_speed
            - prediction.vegetation_index
        )
        risk_level = "High" if fdi >= 75 else "Moderate" if fdi >= 50 else "Low"

        new_prediction = Prediction(
            location_id=prediction.location_id,
            risk_level=risk_level,
            date_generated=datetime.now(timezone.utc),
            prediction_type=prediction.prediction_type or "Default",
        )
        db.add(new_prediction)
        await db.commit()
        await db.refresh(new_prediction)
        return to_response(new_prediction, PredictionResponse)
    except SQLAlchemyError as e:
        logger.error(f"Error creating prediction: {str(e)}")
        await db.rollback()
        raise CRUDException(f"Error creating prediction: {str(e)}")

async def get_predictions_by_location(db: AsyncSession, location_id: int, limit: int = 100, offset: int = 0) -> List[PredictionResponse]:
    if limit > MAX_LIMIT:
        raise CRUDException(f"Limit cannot exceed {MAX_LIMIT}")
    try:
        result = await db.execute(
            select(Prediction)
            .where(Prediction.location_id == location_id)
            .order_by(Prediction.date_generated.desc())
            .offset(offset)
            .limit(limit)
        )
        predictions = result.scalars().all()
        return [to_response(prediction, PredictionResponse) for prediction in predictions]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching predictions for location: {str(e)}")
        raise CRUDException(f"Error fetching predictions for location: {str(e)}")

# Historical Data CRUD operations
async def get_historical_data_by_location(db: AsyncSession, location_id: int) -> List[HistoricalDataResponse]:
    try:
        result = await db.execute(
            select(HistoricalData).where(HistoricalData.location_id == location_id).order_by(HistoricalData.date_occurred)
        )
        historical_data = result.scalars().all()
        return [to_response(data, HistoricalDataResponse) for data in historical_data]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        raise CRUDException(f"Error fetching historical data: {str(e)}")

# Add this at the bottom of `crud.py`

# User Prediction CRUD
async def get_user_predictions_by_user(db: AsyncSession, user_id: int, limit: int = 100, offset: int = 0):
    try:
        result = await db.execute(
            select(UserPrediction).where(UserPrediction.user_id == user_id).offset(offset).limit(limit)
        )
        user_predictions = result.scalars().all()
        return [to_response(up, UserPredictionResponse) for up in user_predictions]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user predictions: {str(e)}")
        raise CRUDException(f"Error fetching user predictions: {str(e)}")

async def create_user_prediction(db: AsyncSession, user_prediction: UserPredictionCreate):
    try:
        new_user_prediction = UserPrediction(**user_prediction.dict())
        db.add(new_user_prediction)
        await db.commit()
        await db.refresh(new_user_prediction)
        return to_response(new_user_prediction, UserPredictionResponse)
    except SQLAlchemyError as e:
        logger.error(f"Error creating user prediction: {str(e)}")
        await db.rollback()
        raise CRUDException(f"Error creating user prediction: {str(e)}")

# User Location CRUD
async def get_user_locations_by_user(db: AsyncSession, user_id: int, limit: int = 100, offset: int = 0):
    try:
        result = await db.execute(
            select(UserLocation).where(UserLocation.user_id == user_id).offset(offset).limit(limit)
        )
        user_locations = result.scalars().all()
        return [to_response(ul, UserLocationResponse) for ul in user_locations]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user locations: {str(e)}")
        raise CRUDException(f"Error fetching user locations: {str(e)}")

async def create_user_location(db: AsyncSession, user_location: UserLocationCreate):
    try:
        new_user_location = UserLocation(**user_location.dict())
        db.add(new_user_location)
        await db.commit()
        await db.refresh(new_user_location)
        return to_response(new_user_location, UserLocationResponse)
    except SQLAlchemyError as e:
        logger.error(f"Error creating user location: {str(e)}")
        await db.rollback()
        raise CRUDException(f"Error creating user location: {str(e)}")
