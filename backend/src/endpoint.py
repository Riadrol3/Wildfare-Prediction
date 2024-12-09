from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import enum

# Database setup
DATABASE_URL = "postgresql://username:password@localhost/db_name"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enum definitions
class RiskLevelEnum(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

# Models
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Location(Base):
    __tablename__ = "location"
    location_id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, unique=True, nullable=False)
    fake_coordinates = Column(String, nullable=True)

class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id = Column(Integer, primary_key=True, index=True)
    risk_level = Column(Enum(RiskLevelEnum), nullable=False)
    date_generated = Column(DateTime, default=func.now())
    location_id = Column(Integer, ForeignKey("location.location_id"), nullable=False)
    prediction_type = Column(String, nullable=True)

# FastAPI setup
app = FastAPI()

# Dependency for session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users")
def create_user(user: User, db: Session = Depends(get_db)):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.get("/predictions/{prediction_id}")
def read_prediction(prediction_id: int, db: Session = Depends(get_db)):
    prediction = db.query(Prediction).filter(Prediction.prediction_id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction

@app.post("/predictions")
def create_prediction(prediction: Prediction, db: Session = Depends(get_db)):
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction

@app.get("/locations/{location_id}")
def read_location(location_id: int, db: Session = Depends(get_db)):
    location = db.query(Location).filter(Location.location_id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@app.post("/locations")
def create_location(location: Location, db: Session = Depends(get_db)):
    db.add(location)
    db.commit()
    db.refresh(location)
    return location

# Run migrations if needed
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
