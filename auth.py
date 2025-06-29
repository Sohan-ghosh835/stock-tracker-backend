from fastapi import APIRouter, HTTPException
from passlib.hash import bcrypt
from db import users
from jose import jwt
import datetime

SECRET_KEY = "secret123"
auth = APIRouter()

@auth.post("/register")
def register(username: str, password: str):
    if users.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="User exists")
    users.insert_one({"username": username, "password": bcrypt.hash(password)})
    return {"message": "Registered"}

@auth.post("/login")
def login(username: str, password: str):
    user = users.find_one({"username": username})
    if not user or not bcrypt.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid")
    payload = {"sub": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)}
    return {"token": jwt.encode(payload, SECRET_KEY, algorithm="HS256")}