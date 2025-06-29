from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.hash import bcrypt
from jose import jwt
from db import users
import datetime

SECRET_KEY = "secret123"
auth = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str

@auth.post("/register")
def register(data: LoginRequest):
    if users.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="User exists")
    users.insert_one({
        "username": data.username,
        "password": bcrypt.hash(data.password)
    })
    return {"message": "Registered"}

@auth.post("/login")
def login(data: LoginRequest):
    user = users.find_one({"username": data.username})
    if not user or not bcrypt.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    payload = {
        "sub": data.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"token": token}
