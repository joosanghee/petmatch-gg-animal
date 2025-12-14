import sqlite3
import os
from flask import Flask, render_template, send_from_directory

# 1. HTML과 CSS가 모여있는 'frontend_test' 폴더를 템플릿 및 정적 폴더로 지정합니다.
app = Flask(__name__, 
            template_folder='frontend_test', 
            static_folder='frontend_test')

# --- 데이터베이스 경로 설정 ---
# 현재 파일(app.py)의 위치: .../beckend/
# DB 파일 위치: .../data/processed/animal_data.db

# 1. 현재 파일(app.py)이 있는 폴더 경로 (beckend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 상위 폴더(..)로 올라간 후, 'data/processed' 폴더 안의 DB 파일을 가리킵니다.
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'animal_data.db')

print(f"✅ 최종 확인 DB 경로: {DB_PATH}")

def get_db_connection():
    """DB 연결 및 설정"""
    # 💡 파일 존재 여부 재확인
    if not os.path.exists(DB_PATH):
        print(f"🚨🚨 치명적 오류: DB 파일을 찾을 수 없습니다. 경로를 확인해주세요: {DB_PATH}")
        return None
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 데이터 접근
    return conn

# --- CSS 파일 처리 ---
@app.route('/style.css')
def serve_css():
    return send_from_directory('frontend_test', 'style.css')

# --- 1. 메인 홈 페이지 ---
@app.route('/')
def index():
    conn = get_db_connection()
    latest_animals = []
    
    if conn:
        try:
            # 최신 유기동물 4마리 미리보기
            latest_animals = conn.execute('''
                SELECT * FROM animal_status 
                ORDER BY register_date DESC 
                LIMIT 4
            ''').fetchall()
        except Exception as e:
            # DB 연결은 됐지만, 쿼리 실행(테이블이 없거나 컬럼명 오류) 실패 시
            print(f"❌ DB 쿼리 실행 오류 발생: {e}")
        finally:
            conn.close()

    return render_template('index.html', latest_animals=latest_animals)


# --- 2. 유기동물 목록 페이지 ---
@app.route('/animals')
def animal_list():
    conn = get_db_connection()
    animals = []
    
    if conn:
        try:
            animals = conn.execute('''
                SELECT * FROM animal_status 
                ORDER BY register_date DESC
            ''').fetchall()
        except Exception as e:
            print(f"❌ DB 쿼리 실행 오류 발생: {e}")
        finally:
            conn.close()
            
    return render_template('animals.html', animals=animals)


# --- 3. 병원/약국 목록 페이지 ---
@app.route('/hospital')
def hospital_list():
    conn = get_db_connection()
    entities = []
    
    if conn:
        try:
            query = """
                SELECT hospital_id as id, name, address, phone, '동물병원' as type 
                FROM hospital_final
                UNION ALL
                SELECT pharmacy_id as id, name, address, phone, '동물약국' as type 
                FROM pharmacy_final
                ORDER BY name ASC
            """
            entities = conn.execute(query).fetchall()
        except Exception as e:
            print(f"❌ DB 쿼리 실행 오류 발생: {e}")
        finally:
            conn.close()
            
    return render_template('hospital.html', entities=entities)

# --- 4. 상세 페이지 (임시) ---
@app.route('/detail/<int:id>')
def animal_detail(id):
    return f"<h3>동물 ID {id}번 상세 페이지입니다. (구현 예정)</h3>"


if __name__ == '__main__':
    # 서버 실행
    app.run(debug=True, port=5000)