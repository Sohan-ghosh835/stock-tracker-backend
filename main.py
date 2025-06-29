from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import auth
from financials import financials
from analyzer import analyzer
from predictor import predictor

app = FastAPI()
app.include_router(auth)
app.include_router(financials)
app.include_router(analyzer)
app.include_router(predictor)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sohan-ghosh835.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
