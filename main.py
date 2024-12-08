from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import pytz

from models import Location, Prediction, HistoricalData, EventImpact  # Assuming these models are defined elsewhere
from database import Base, get_session  # Assuming database setup is handled in another module

app = FastAPI()

# Database setup
DATABASE_URL = "postgresql+asyncpg://username:password@localhost/dbname"  # Use environment variables for sensitive data
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to get the database session
async def get_db():
    async with SessionLocal() as session:
        yield session

# Pydantic models for input validation
class PredictionInput(BaseModel):
    location_id: int = Field(..., description="Unique ID for the location")
    temperature: float = Field(..., description="Temperature in Celsius", ge=-50, le=60)
    humidity: float = Field(..., description="Humidity percentage", ge=0, le=100)
    wind_speed: float = Field(..., description="Wind speed in km/h", ge=0)
    vegetation_index: float = Field(..., description="Vegetation index (0 to 1)", ge=0, le=1)

@app.get("/")
def read_root():
    return {"message": "Wildfire Prediction API is running"}

@app.post("/predict/")
async def predict(input_data: PredictionInput, db: AsyncSession = Depends(get_db)):
    try:
        # Extract input data
        location_id = input_data.location_id
        temperature = input_data.temperature
        humidity = input_data.humidity
        wind_speed = input_data.wind_speed
        vegetation_index = input_data.vegetation_index

        # Validate location existence
        stmt = select(Location).where(Location.location_id == location_id)
        location_result = await db.execute(stmt)
        location = location_result.scalar_one_or_none()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        # Fetch historical data for the location
        stmt = select(HistoricalData).where(HistoricalData.location_id == location_id)
        result = await db.execute(stmt)
        historical_data = result.scalars().all()

        # Analyze historical data for risk adjustment (example logic)
        historical_risk = "Unknown"
        if historical_data:
            high_risk_count = sum(1 for data in historical_data if "HIGH" in data.historical_data.upper())
            historical_risk = "High" if high_risk_count > len(historical_data) / 2 else "Low"

        # Enhanced rule-based prediction logic
        risk_score = 0

        if temperature > 35:
            risk_score += 3
        elif temperature > 30:
            risk_score += 2

        if humidity < 30:
            risk_score += 2

        if wind_speed > 20:
            risk_score += 3
        elif wind_speed > 15:
            risk_score += 2

        if vegetation_index < 0.5:
            risk_score += 3
        elif vegetation_index < 0.7:
            risk_score += 2

        # Determine risk level based on score
        if risk_score >= 8:
            risk_level = "High"
        elif risk_score >= 5:
            risk_level = "Moderate"
        else:
            risk_level = "Low"

        # Incorporate historical risk data
        if historical_risk == "High" and risk_level != "High":
            risk_level = "Moderate"  # Adjust based on historical trends

        # Save prediction to the database
        new_prediction = Prediction(
            risk_level=risk_level,
            date_generated=datetime.now(timezone.utc),
            location_id=location_id
        )
        db.add(new_prediction)
        await db.commit()

        # Return the prediction result
        return {
            "location_id": location_id,
            "risk_level": risk_level,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "historical_risk": historical_risk,
            "risk_score": risk_score
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

@app.get("/locations/")
async def get_locations(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Location)
        result = await db.execute(stmt)
        locations = result.scalars().all()
        return [{"location_id": loc.location_id, "region_name": loc.region_name} for loc in locations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching locations: {str(e)}")
