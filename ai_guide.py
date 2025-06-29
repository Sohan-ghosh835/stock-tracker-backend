from fastapi import APIRouter
from db import stocks

ai_guide = APIRouter()

@ai_guide.get("/ai-guide/{symbol:path}")
def ai_insight(symbol: str):
    data = stocks.find_one({"symbol": symbol})
    if not data:
        return {"error": "Stock not found"}
    
    info = data.get("info", {})
    pros = []
    cons = []

    if info.get("trailingPE") and info["trailingPE"] < 20:
        pros.append("Reasonable P/E ratio indicates fair valuation.")
    else:
        cons.append("High P/E ratio might indicate overvaluation.")

    if info.get("ROCE") and info["ROCE"] > 15:
        pros.append("High ROCE suggests efficient capital usage.")
    if info.get("ROE") and info["ROE"] < 10:
        cons.append("Low ROE might indicate weak shareholder returns.")

    if "description" in info and "leader" in info["description"].lower():
        pros.append("The company is described as a market leader.")
    
    return {
        "pros": ", ".join(pros) if pros else "No significant pros identified.",
        "cons": ", ".join(cons) if cons else "No major cons found."
    }
