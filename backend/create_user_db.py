import sqlite3
import os

# 1. 저장 경로 설정 (기존 동물 DB와 같은 data/processed 폴더에 저장)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, '..', 'data', 'processed')
DB_PATH = os.path.join(DB_FOLDER, 'user_data.db')

# 폴더가 없으면 생성
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# 2. 회원 테이블 생성 SQL
# 비밀번호는 해시(암호화)된 문자열로 저장됩니다.
SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def create_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(SQL_SCHEMA)
        conn.commit()
        conn.close()
        print(f"회원 DB 생성 완료!\n📂 경로: {DB_PATH}")
    except Exception as e:
        print(f"DB 생성 실패: {e}")

if __name__ == "__main__":
    create_db()