import sqlite3
import os

# 1. 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'user_data.db')

# 2. 즐겨찾기 테이블 생성 SQL
SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    animal_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, animal_id) -- 중복 찜하기 방지
);
"""

def update_db():
    if not os.path.exists(USER_DB_PATH):
        print("❌ 오류: user_data.db 파일이 없습니다. create_user_db.py를 먼저 실행했는지 확인하세요.")
        return

    try:
        conn = sqlite3.connect(USER_DB_PATH)
        conn.execute(SQL_SCHEMA)
        conn.commit()
        conn.close()
        print(f"✅ 즐겨찾기 테이블 추가 완료!")
    except Exception as e:
        print(f"❌ 테이블 추가 실패: {e}")

if __name__ == "__main__":
    update_db()