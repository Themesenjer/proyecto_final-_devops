from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

# Permitir que el Frontend se conecte al Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a la Base de Datos usando Variables de Entorno
def get_db():
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "habit_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "secret"),
        cursor_factory=RealDictCursor
    )
    try:
        yield connection
    finally:
        connection.close()

@app.get("/")
def read_root():
    return {"status": "Backend Operativo para Habit Tracker"}

# Aquí agregaremos los modelos de Pydantic y las rutas de Registro/Login en el siguiente paso