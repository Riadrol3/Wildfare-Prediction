from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from datetime import datetime, timezone
from api_endpoints import app as api_router
from models import Location, Prediction, HistoricalData
from database import Base, get_session
import crud
import schemas

app = FastAPI()

app.include_router(api_router)

# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:Riad108515@localhost/Agile_project"  # Replace with your credentials
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
async def get_locations(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await crud.get_all_locations(db, limit=limit, offset=offset)

# Endpoint to create a location
@app.post("/locations/", response_model=schemas.LocationResponse)
async def create_location(location: schemas.LocationCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await crud.create_location(db, location)
        return result
    except crud.CRUDException as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to fetch a single location
@app.get("/locations/{location_id}", response_model=schemas.LocationResponse)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)):
    try:
        location = await crud.get_location(db, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
    except crud.CRUDException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Endpoint to create a prediction
@app.post("/predict/", response_model=schemas.PredictionResponse)
async def predict(input_data: schemas.PredictionCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Validate location existence
        location = await crud.get_location(db, input_data.location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")

        # Fetch and validate historical data
        historical_data = await crud.get_historical_data_by_location(db, input_data.location_id)
        valid_historical_data = [
            data for data in historical_data if data.historical_data and isinstance(data.historical_data, str)
        ]
        historical_risk = "High" if len(valid_historical_data) > 0 and sum(
            1 for data in valid_historical_data if "HIGH" in data.historical_data.upper()
        ) > len(valid_historical_data) / 2 else "Low"

        # Calculate FDI
        fdi = 2 * input_data.temperature - 0.5 * input_data.humidity + 0.3 * input_data.wind_speed - input_data.vegetation_index
        risk_level = "High" if fdi >= 75 else "Moderate" if fdi >= 50 else "Low"

        # Save prediction to the database
        prediction = schemas.PredictionCreate(
            location_id=input_data.location_id,
            risk_level=risk_level,
            date_generated=datetime.now(timezone.utc),
            prediction_type=input_data.prediction_type or "Default",
        )
        return await crud.create_prediction(db, prediction)
    except crud.CRUDException as e:
        raise HTTPException(status_code=400, detail=f"Data issue: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")


# Endpoint to fetch predictions for a location
@app.get("/predictions/{location_id}", response_model=List[schemas.PredictionResponse])
async def get_predictions(location_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    try:
        predictions = await crud.get_predictions_by_location(db, location_id, limit=limit, offset=offset)
        if not predictions:
            raise HTTPException(status_code=404, detail="No predictions found for the location")
        return predictions
    except crud.CRUDException as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/user_predictions/{user_id}", response_model=List[schemas.UserPredictionResponse])
async def get_user_predictions(user_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_predictions_by_user(db, user_id, limit, offset)

@app.post("/user_predictions/", response_model=schemas.UserPredictionResponse)
async def create_user_prediction(user_prediction: schemas.UserPredictionCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user_prediction(db, user_prediction)

@app.get("/user_locations/{user_id}", response_model=List[schemas.UserLocationResponse])
async def get_user_locations(user_id: int, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await crud.get_user_locations_by_user(db, user_id, limit, offset)

@app.post("/user_locations/", response_model=schemas.UserLocationResponse)
async def create_user_location(user_location: schemas.UserLocationCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_user_location(db, user_location)
