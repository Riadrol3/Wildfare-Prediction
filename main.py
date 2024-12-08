from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Wildfire Prediction API is running"}

@app.post("/predict/")
def predict(input_data: dict):
    try:
        temperature = input_data.get("temperature")
        humidity = input_data.get("humidity")
        wind_speed = input_data.get("wind_speed")
        vegetation_index = input_data.get("vegetation_index")

        if temperature > 35 and humidity < 30 and wind_speed > 20 and vegetation_index < 0.5:
            return {"prediction": "High Risk"}
        elif temperature > 30 or wind_speed > 15:
            return {"prediction": "Moderate Risk"}
        else:
            return {"prediction": "Low Risk"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
