import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, SessionLocal
from models import User, Location, Prediction
from sqlalchemy.orm import Session

test_client = TestClient(app)

# Create a test database for the duration of tests
Base.metadata.create_all(bind=engine)

# Dependency override for test database
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides["get_db"] = override_get_db

# Fixture for creating a test session
@pytest.fixture(scope="function")
def db_session():
    session = SessionLocal()
    yield session
    session.close()

# Helper function for creating test data
def create_test_user(db: Session):
    user = User(user_name="Test User", email="testuser@example.com", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_location(db: Session):
    location = Location(region_name="Test Region", fake_coordinates="123.456,789.012")
    db.add(location)
    db.commit()
    db.refresh(location)
    return location

def create_test_prediction(db: Session, location_id: int):
    prediction = Prediction(risk_level="HIGH", location_id=location_id, prediction_type="test")
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction

# Test cases

def test_create_user(db_session):
    response = test_client.post(
        "/users",
        json={"user_name": "Test User", "email": "testuser@example.com", "role": "admin"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"

def test_get_user(db_session):
    test_user = create_test_user(db_session)
    response = test_client.get(f"/users/{test_user.user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email

def test_create_location(db_session):
    response = test_client.post(
        "/locations",
        json={"region_name": "Test Region", "fake_coordinates": "123.456,789.012"}
    )
    assert response.status_code == 200
    assert response.json()["region_name"] == "Test Region"

def test_get_location(db_session):
    test_location = create_test_location(db_session)
    response = test_client.get(f"/locations/{test_location.location_id}")
    assert response.status_code == 200
    assert response.json()["region_name"] == test_location.region_name

def test_create_prediction(db_session):
    test_location = create_test_location(db_session)
    response = test_client.post(
        "/predictions",
        json={"risk_level": "HIGH", "location_id": test_location.location_id, "prediction_type": "test"}
    )
    assert response.status_code == 200
    assert response.json()["risk_level"] == "HIGH"

def test_get_prediction(db_session):
    test_location = create_test_location(db_session)
    test_prediction = create_test_prediction(db_session, test_location.location_id)
    response = test_client.get(f"/predictions/{test_prediction.prediction_id}")
    assert response.status_code == 200
    assert response.json()["risk_level"] == "HIGH"
