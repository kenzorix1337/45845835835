from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from fastapi.responses import JSONResponse

app = FastAPI()

# Подключение к базе данных SQLite
def get_db():
    conn = sqlite3.connect('referrals.db')  # Путь к базе данных
    conn.row_factory = sqlite3.Row  # Чтобы можно было работать с результатами как с объектами
    return conn

# Создание таблицы рефералов, если она не существует
def create_table():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                            user_id TEXT PRIMARY KEY,
                            is_referral BOOLEAN)''')
        conn.commit()

# Обработчик для /check_referral/{user_id}, который проверяет наличие user_id в базе данных
@app.get("/check_referral/{user_id}")
def check_referral(user_id: str):
    """Проверяет наличие user_id в базе данных и возвращает статус."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
            existing_user = cursor.fetchone()
        
        if existing_user:
            return {"status": "success", "message": "User found in database"}
        else:
            return {"status": "error", "message": "User not found in database"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Статус сервера
@app.get("/status")
def get_status():
    return {"status": "ok"}

# Создаем таблицу при запуске сервера
create_table()

# Пример добавления нового пользователя в базу
@app.post("/add_referral/")
def add_referral(user_id: str, is_referral: bool):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO referrals (user_id, is_referral) VALUES (?, ?)", (user_id, is_referral))
            conn.commit()
        
        return {"status": "success", "message": "Referral added successfully"}
    
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Пример добавления реферала через GET запрос (как указано в первом сообщении)
@app.get("/callback")
def callback(user_id: str, event_id: str, date: str):
    try:
        # Здесь можно добавить дополнительную логику для проверки или обработки event_id и date
        is_referral = True  # Или другая логика для определения is_referral
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO referrals (user_id, is_referral) VALUES (?, ?)", (user_id, is_referral))
            conn.commit()

        return {"status": "success", "message": "Referral added successfully"}
    
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

