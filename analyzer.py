from fastapi import APIRouter
from db import stocks

analyzer = APIRouter()

@analyzer.get("/compare")
def compare_stocks(symbol1: str, symbol2: str):

    s1 = stocks.find_one({"symbol": symbol1})
    s2 = stocks.find_one({"symbol": symbol2})
    if not s1 or not s2:
        return {"error": "Stock data missing"}
    return {
        symbol1: s1["info"],
        symbol2: s2["info"]
    }