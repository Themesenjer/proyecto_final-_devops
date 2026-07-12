from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = FastAPI(title="Habit Tracker API")

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ESTO CONFIGURA EL CANDADO EN SWAGGER AUTOMÁTICAMENTE
security_scheme = HTTPBearer()

# Modelos de datos
class UserAuth(BaseModel):
    email: str
    password: str

class HabitCreate(BaseModel):
    name: str

class HabitUpdate(BaseModel):
    completed: bool

# Inicialización de la Base de Datos
def init_db():
    time.sleep(2)
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "habit_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "secret_password_2026")
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(150) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Tablas verificadas en PostgreSQL.")
    except Exception as e:
        print(f"Error de conexión DB: {e}")

@app.on_event("startup")
def startup_event():
    init_db()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "habit_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "secret_password_2026"),
        cursor_factory=RealDictCursor
    )

# --- ENDPOINTS ---

@app.get("/")
def root():
    return {"status": "Backend Operativo"}

@app.post("/auth/register")
def register(user: UserAuth):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (user.email, user.password))
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Usuario registrado"}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="El correo ya existe")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
def login(user: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (user.email, user.password))
    db_user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    return {"token": db_user["email"]}

# USAMOS DEPENDS PARA EXTRAER EL TOKEN DE MANERA ESTÁNDAR
@app.get("/habits")
def get_habits(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    email = credentials.credentials # Aquí FastAPI ya limpió el "Bearer " de adelante
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT h.* FROM habits h JOIN users u ON h.user_id = u.id WHERE u.email = %s", (email,))
    habits = cursor.fetchall()
    cursor.close()
    conn.close()
    return habits

@app.post("/habits")
def create_habit(habit: HabitCreate, credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    email = credentials.credentials
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    u = cursor.fetchone()
    
    cursor.execute("INSERT INTO habits (name, user_id) VALUES (%s, %s)", (habit.name, u["id"]))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "Creado"}

@app.patch("/habits/{id}")
def update_habit(id: int, habit: HabitUpdate, credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE habits SET completed = %s WHERE id = %s", (habit.completed, id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "Actualizado"}

@app.delete("/habits/{id}")
def delete_habit(id: int, credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habits WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "Eliminado"}