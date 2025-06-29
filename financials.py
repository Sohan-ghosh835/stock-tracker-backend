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

        try:
            info = stock.get_info()
        except Exception:
            info = {}

        if not info or not info.get("longName"):
            # Try fallback to Alpha Vantage
            alt_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_KEY}"
            try:
                res = requests.get(alt_url)
                res.raise_for_status()
                alt_info = res.json()

                if "Symbol" not in alt_info:
                    raise HTTPException(status_code=404, detail="No data from Alpha Vantage either")

                data = {
                    "info": {
                        "longName": alt_info.get("Name", symbol.upper()),
                        "sector": alt_info.get("Sector", "Unknown"),
                        "marketCap": int(float(alt_info.get("MarketCapitalization", 0))),
                        "trailingPE": alt_info.get("PERatio", "N/A"),
                        "trailingEps": alt_info.get("EPS", "N/A")
                    },
                    "history": [],
                    "financials": {
                        "balance_sheet": {},
                        "income_stmt": {},
                        "cashflow": {}
                    }
                }

                stocks.update_one({"symbol": symbol}, {"$set": data}, upsert=True)
                return data

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Yahoo Finance and Alpha Vantage both failed: {str(e)}")

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

        history = stock.history(period="5y")
        if history.empty:
            raise HTTPException(status_code=404, detail="No historical data found")

        history_data = history.reset_index().to_dict(orient="records")

        data = {
            "info": {
                "longName": info["longName"],
                "sector": info["sector"],
                "marketCap": info["marketCap"],
                "trailingPE": info["trailingPE"],
                "trailingEps": info["trailingEps"]
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