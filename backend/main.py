# backend/main.py
# from fastapi import FastAPI
from backend.core.database import Base, engine

# app = FastAPI()

# Automatically create all tables in the database
Base.metadata.create_all(bind=engine)

# @app.get("/")
# def read_root():
#     return {"message": "Hello, world!"}
