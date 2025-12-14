import sqlite3
import os
# 👇 여기에 request 를 꼭 추가해야 합니다!
from flask import Flask, render_template, send_from_directory, jsonify, request

# ... (나머지 코드는 그대로 두시면 됩니다)

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
# app.py 의 animal_list 함수 부분을 이걸로 교체하세요!

@app.route('/animals')
def animal_list():
    conn = get_db_connection()
    animals = []
    
    # 1. 프론트엔드에서 보낸 검색 조건 받기 (request.args)
    keyword = request.args.get('keyword', '')  # 검색어
    region = request.args.get('region', '전체')
    species = request.args.get('species', '전체') # 개/고양이
    gender = request.args.get('gender', '전체')
    
    # 2. 기본 SQL 쿼리 작성 (WHERE 1=1은 조건을 계속 붙이기 위한 꼼수입니다)
    sql = "SELECT * FROM animal_status WHERE 1=1"
    params = []

    if conn:
        try:
            # --- 동적 쿼리 조립 시작 ---
            
            # [A] 검색어 (품종이나 보호소 이름에 포함되어 있으면 검색)
            if keyword:
                sql += " AND (breed LIKE ? OR shelter_name LIKE ?)"
                params.append(f'%{keyword}%')
                params.append(f'%{keyword}%')
            
            # [B] 지역 필터 (예: '수원' -> '경기도 수원시...' 매칭)
            if region != '전체':
                sql += " AND region LIKE ?"
                params.append(f'%{region}%')

            # [C] 성별 필터 (DB에는 M/F/Q로 저장되어 있다고 가정)
            if gender == '수컷':
                sql += " AND gender = 'M'"
            elif gender == '암컷':
                sql += " AND gender = 'F'"
            
            # [D] 종 필터 (개/고양이 구분 - 품종명으로 구분)
            if species == '개':
                sql += " AND breed NOT LIKE '%고양이%'"
            elif species == '고양이':
                sql += " AND breed LIKE '%고양이%'"

            # 정렬 및 실행
            sql += " ORDER BY register_date DESC"
            
            print(f"🔍 실행된 SQL: {sql}") # (디버깅용) 터미널에서 확인 가능
            print(f"🔍 파라미터: {params}")

            animals = conn.execute(sql, params).fetchall()
            
        except Exception as e:
            print(f"❌ DB 검색 오류: {e}")
        finally:
            conn.close()
            
    # 3. HTML로 데이터와 현재 검색 조건을 같이 보냄 (그래야 화면에 필터 유지됨)
    return render_template('animals.html', animals=animals, 
                           curr_keyword=keyword, curr_region=region, 
                           curr_species=species, curr_gender=gender)


# --- 3. 병원/약국 목록 페이지 ---
# app.py 의 기존 함수들을 이걸로 덮어쓰세요.

# --- 3. 병원/약국 목록 (검색/필터 적용) ---
@app.route('/hospital')
def hospital_list():
    conn = get_db_connection()
    entities = []
    
    # 1. 필터 조건 받기
    keyword = request.args.get('keyword', '')
    type_filter = request.args.get('type', '전체')
    region_filter = request.args.get('region', '전체')
    
    if conn:
        try:
            # 2. 기본 데이터 (병원 + 약국 합치기)
            # UNION 결과를 서브쿼리(base)로 만들어서 그 뒤에 WHERE를 붙입니다.
            base_query = """
                SELECT * FROM (
                    SELECT hospital_id as id, name, address, phone, region, '동물병원' as type 
                    FROM hospital_final
                    UNION ALL
                    SELECT pharmacy_id as id, name, address, phone, region, '동물약국' as type 
                    FROM pharmacy_final
                ) AS base WHERE 1=1
            """
            params = []

            # 3. 동적 쿼리 조립
            # [A] 검색어 (이름 또는 주소)
            if keyword:
                base_query += " AND (name LIKE ? OR address LIKE ?)"
                params.append(f'%{keyword}%')
                params.append(f'%{keyword}%')
            
            # [B] 구분 (병원 vs 약국)
            if type_filter != '전체':
                base_query += " AND type = ?"
                params.append(type_filter)

            # [C] 지역 필터
            if region_filter != '전체':
                base_query += " AND region LIKE ?"
                params.append(f'%{region_filter}%')
            
            # 정렬
            base_query += " ORDER BY name ASC"
            
            entities = conn.execute(base_query, params).fetchall()
            
        except Exception as e:
            print(f"❌ 병원 검색 오류: {e}")
        finally:
            conn.close()
            
    return render_template('hospital.html', entities=entities,
                           curr_keyword=keyword, curr_type=type_filter, curr_region=region_filter)


# --- 4. 보호소 목록 (검색/필터 적용) ---
@app.route('/shelter')
def shelter_list():
    conn = get_db_connection()
    shelters = []
    
    # 1. 필터 조건 받기
    keyword = request.args.get('keyword', '')
    region_filter = request.args.get('region', '전체')
    
    if conn:
        try:
            sql = "SELECT * FROM shelter_final WHERE 1=1"
            params = []
            
            # [A] 검색어 (이름 or 주소)
            if keyword:
                sql += " AND (name LIKE ? OR address LIKE ?)"
                params.append(f'%{keyword}%')
                params.append(f'%{keyword}%')
                
            # [B] 지역 (주소 기반 검색)
            if region_filter != '전체':
                sql += " AND address LIKE ?"
                params.append(f'%{region_filter}%')
            
            sql += " ORDER BY name ASC"
            
            shelters = conn.execute(sql, params).fetchall()
        except Exception as e:
            print(f"❌ 보호소 검색 오류: {e}")
        finally:
            conn.close()
            
    return render_template('shelter.html', shelters=shelters,
                           curr_keyword=keyword, curr_region=region_filter)

# --- 4. 상세 페이지 (임시) ---
@app.route('/detail/<int:id>')
def animal_detail(id):
    return f"<h3>동물 ID {id}번 상세 페이지입니다. (구현 예정)</h3>"


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/api/animal/<int:id>')
def get_animal_detail(id):
    conn = get_db_connection()
    animal_data = {}
    
    if conn:
        try:
            # 특정 ID의 동물 정보를 가져옵니다.
            row = conn.execute('SELECT * FROM animal_status WHERE animal_id = ?', (id,)).fetchone()
            if row:
                # DB 데이터를 딕셔너리(JSON) 형태로 변환
                animal_data = dict(row)
        except Exception as e:
            print(f"❌상세 정보 조회 오류: {e}")
        finally:
            conn.close()
            
    return jsonify(animal_data)


if __name__ == '__main__':
    # 서버 실행
    app.run(debug=True, port=5000)