import sqlite3
import os

# 저장 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, '..', 'data', 'processed')
DB_PATH = os.path.join(DB_FOLDER, 'user_data.db')

if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

#  'is_admin' 컬럼이 추가
SQL_SCHEMA = """
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0, 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def create_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SQL_SCHEMA)
        conn.commit()
        conn.close()
        print(f"(관리자 기능 포함) 회원 DB 생성 완료!\n 경로: {DB_PATH}")
    except Exception as e:
        print(f" DB 생성 실패: {e}")

if __name__ == "__main__":
    create_db()