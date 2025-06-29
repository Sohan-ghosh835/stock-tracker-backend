from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
from db import stocks
import os
from dotenv import load_dotenv

load_dotenv()
ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")

financials = APIRouter()

@financials.get("/stock/{symbol}")
def get_stock_data(symbol: str):
    try:
        stock = yf.Ticker(symbol)
        info = stock.get_info() or {}

        history = stock.history(period="5y")
        if history.empty:
            raise HTTPException(status_code=404, detail="No historical data found")

        history_data = history.reset_index().to_dict(orient="records")

        data = {
            "info": {
                "longName": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "marketCap": info.get("marketCap", 0),
                "trailingPE": info.get("trailingPE", ""),
                "trailingEps": info.get("trailingEps", "")
            },
            "history": history_data,
            "financials": {
                "balance_sheet": stock.balance_sheet.to_dict() if not stock.balance_sheet.empty else {},
                "income_stmt": stock.financials.to_dict() if not stock.financials.empty else {},
                "cashflow": stock.cashflow.to_dict() if not stock.cashflow.empty else {}
            }
        }

        stocks.update_one({"symbol": symbol}, {"$set": data}, upsert=True)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

@financials.get("/alpha/{symbol}")
def get_alpha_data(symbol: str):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if "Symbol" not in data:
            raise HTTPException(status_code=404, detail="No Alpha Vantage data found")
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
