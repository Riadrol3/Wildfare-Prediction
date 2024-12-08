import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware
import logging

from models import Location, Prediction, HistoricalData
from database import Base, get_session
import crud
import schemas

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wildfire-prediction")

# App instance
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production (e.g., ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/db")
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to get the database session
async def get_db():
    async with SessionLocal() as session:
        yield session

# Ensure tables are created during startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Wildfire Prediction API is running"}

# Endpoint to get all locations
@app.get("/locations/", response_model=List[schemas.LocationResponse])
async def get_locations(db: AsyncSession = Depends(get_db)):
    try:
        return await crud.get_all_locations(db)
    except Exception as e:
        logger.error(f"Error fetching locations: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to create a location
@app.post("/locations/", response_model=schemas.LocationResponse)
async def create_location(location: schemas.LocationCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await crud.create_location(db, location)
        return result
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=400, detail="Location creation failed")

# Endpoint to fetch a single location
@app.get("/locations/{location_id}", response_model=schemas.LocationResponse)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)):
    try:
        location = await crud.get_location(db, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
    except Exception as e:
        logger.error(f"Error fetching location {location_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to create a prediction
@app.post("/predict/", response_model=schemas.PredictionResponse)
async def predict(input_data: schemas.PredictionCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Validate location existence
        location = await crud.get_location(db, input_data.location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        # Fetch historical data for the location
        historical_data = await crud.get_historical_data_by_location(db, input_data.location_id)
        historical_risk = "Unknown"
        if historical_data:
            high_risk_count = sum(1 for data in historical_data if "HIGH" in data.historical_data.upper())
            historical_risk = "High" if high_risk_count > len(historical_data) / 2 else "Low"

        # Validate input ranges using Pydantic schemas
        if not (0 <= input_data.temperature <= 60):
            raise HTTPException(status_code=400, detail="Temperature out of range")
        if not (0 <= input_data.humidity <= 100):
            raise HTTPException(status_code=400, detail="Humidity out of range")
        if not (0 <= input_data.wind_speed <= 150):
            raise HTTPException(status_code=400, detail="Wind speed out of range")

        # Prediction logic
        risk_score = 0
        if input_data.temperature > 35:
            risk_score += 3
        elif input_data.temperature > 30:
            risk_score += 2

        if input_data.humidity < 30:
            risk_score += 2

        if input_data.wind_speed > 20:
            risk_score += 3
        elif input_data.wind_speed > 15:
            risk_score += 2

        if input_data.vegetation_index < 0.5:
            risk_score += 3
        elif input_data.vegetation_index < 0.7:
            risk_score += 2

        # Determine risk level
        if risk_score >= 8:
            risk_level = "High"
        elif risk_score >= 5:
            risk_level = "Moderate"
        else:
            risk_level = "Low"

        # Incorporate historical risk
        if historical_risk == "High" and risk_level != "High":
            risk_level = "Moderate"

        # Save prediction to the database
        prediction = schemas.PredictionCreate(
            location_id=input_data.location_id,
            risk_level=risk_level,
            date_generated=datetime.now(timezone.utc),
        )
        new_prediction = await crud.create_prediction(db, prediction)
        return new_prediction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Endpoint to fetch predictions for a location
@app.get("/predictions/{location_id}", response_model=List[schemas.PredictionResponse])
async def get_predictions(location_id: int, db: AsyncSession = Depends(get_db)):
    try:
        predictions = await crud.get_predictions_by_location(db, location_id)
        if not predictions:
            raise HTTPException(status_code=404, detail="No predictions found for the location")
        return predictions
    except Exception as e:
        logger.error(f"Error fetching predictions for location {location_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
