from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
from db import stocks
import os
from dotenv import load_dotenv

load_dotenv()
ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")

financials = APIRouter()

@financials.get("/stock")
def get_stock_data(symbol: str):


    try:
        stock = yf.Ticker(symbol)

        try:
            info = stock.get_info()
        except Exception:
            info = {}

        if not info.get("longName"):
            info["longName"] = symbol.upper()
        if not info.get("sector"):
            info["sector"] = "Unknown"
        if not info.get("marketCap"):
            info["marketCap"] = 0
        if not info.get("trailingPE"):
            info["trailingPE"] = "N/A"
        if not info.get("trailingEps"):
            info["trailingEps"] = "N/A"

        if not info.get("currentPrice"):
            info["currentPrice"] = info.get("previousClose", 0)
        if not info.get("dayHigh"):
            info["dayHigh"] = info.get("fiftyTwoWeekHigh", 0)
        if not info.get("dayLow"):
            info["dayLow"] = info.get("fiftyTwoWeekLow", 0)
        if not info.get("bookValue"):
            info["bookValue"] = "N/A"
        if not info.get("dividendYield"):
            info["dividendYield"] = "N/A"
        if not info.get("returnOnEquity"):
            info["returnOnEquity"] = "N/A"
        if not info.get("returnOnAssets"):
            info["returnOnAssets"] = "N/A"
        if not info.get("faceValue"):
            info["faceValue"] = "N/A"
        if not info.get("longBusinessSummary"):
            info["longBusinessSummary"] = "No description available."

        history = stock.history(period="5y")
        if history.empty:
            alpha_fallback = fetch_alpha_vantage(symbol)
            if not alpha_fallback:
                raise HTTPException(status_code=404, detail="No data found from Yahoo or Alpha Vantage")
            return alpha_fallback

        history_data = history.reset_index().to_dict(orient="records")

        data = {
            "info": {
                "longName": info["longName"],
                "sector": info["sector"],
                "marketCap": info["marketCap"],
                "trailingPE": info["trailingPE"],
                "trailingEps": info["trailingEps"],
                "currentPrice": info["currentPrice"],
                "high": info["dayHigh"],
                "low": info["dayLow"],
                "bookValue": info["bookValue"],
                "dividendYield": info["dividendYield"],
                "ROCE": info["returnOnAssets"],
                "ROE": info["returnOnEquity"],
                "faceValue": info["faceValue"],
                "description": info["longBusinessSummary"]
            },
            "history": history_data,
            "financials": {
                "balance_sheet": stock.balance_sheet.to_dict() if hasattr(stock, "balance_sheet") and not stock.balance_sheet.empty else {},
                "income_stmt": stock.financials.to_dict() if hasattr(stock, "financials") and not stock.financials.empty else {},
                "cashflow": stock.cashflow.to_dict() if hasattr(stock, "cashflow") and not stock.cashflow.empty else {}
            }
        }

        stocks.update_one({"symbol": symbol}, {"$set": data}, upsert=True)
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

def fetch_alpha_vantage(symbol):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if "Symbol" not in data:
            return None

        return {
            "info": {
                "longName": data.get("Name", symbol.upper()),
                "sector": data.get("Sector", "N/A"),
                "marketCap": float(data.get("MarketCapitalization", 0)),
                "trailingPE": data.get("PERatio", "N/A"),
                "trailingEps": data.get("EPS", "N/A"),
                "currentPrice": data.get("PreviousClose", "N/A"),
                "high": data.get("52WeekHigh", "N/A"),
                "low": data.get("52WeekLow", "N/A"),
                "bookValue": data.get("BookValue", "N/A"),
                "dividendYield": data.get("DividendYield", "N/A"),
                "ROCE": data.get("ReturnOnAssetsTTM", "N/A"),
                "ROE": data.get("ReturnOnEquityTTM", "N/A"),
                "faceValue": data.get("SharesOutstanding", "N/A"),
                "description": data.get("Description", "No description available.")
            },
            "history": [],
            "financials": {}
        }
    except Exception:
        return None

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