from fastapi import APIRouter
from db import stocks
import numpy as np

predictor = APIRouter()

@predictor.get("/predict/{symbol:path}")
def predict_price(symbol: str):
    data = stocks.find_one({"symbol": symbol})
    if not data:
        return {"error": "Stock not found"}
    closes = [d["Close"] for d in data["history"] if d["Close"] > 0]
    prediction = np.mean(closes[-30:])
    return {"predicted_price": round(prediction, 2)}
