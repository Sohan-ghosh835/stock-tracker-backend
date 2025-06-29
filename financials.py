from fastapi import APIRouter
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
    stock = yf.Ticker(symbol)
    info = stock.info
    history = stock.history(period="5y").reset_index().to_dict(orient="records")
    data = {
        "info": info,
        "history": history,
        "financials": {
            "balance_sheet": stock.balance_sheet.to_dict(),
            "income_stmt": stock.financials.to_dict(),
            "cashflow": stock.cashflow.to_dict()
        }
    }
    stocks.update_one({"symbol": symbol}, {"$set": data}, upsert=True)
    return data

@financials.get("/alpha/{symbol}")
def get_alpha_data(symbol: str):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"
    res = requests.get(url)
    return res.json()
