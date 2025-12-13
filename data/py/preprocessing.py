import sqlite3
import os
import pandas as pd

# --- 1. 경로 설정 (database/py 폴더 기준) ---
db_name = "animal_data.db"
# 💡 현재 파일(database/py)을 기준으로 DB 파일(database/db) 경로 설정
db_folder = "../processed"
db_path = os.path.join(db_folder, db_name) 

# --- 2. SQL 스크립트 (NULL 최소화 로직 적용) ---
SQL_SCRIPT = """
-- Foreign Key 제약 조건 활성화 (필수)
PRAGMA foreign_keys = ON;

-- 기존 최종 테이블 삭제
DROP TABLE IF EXISTS animal_status;
DROP TABLE IF EXISTS shelter_final;
DROP TABLE IF EXISTS hospital_final;
DROP TABLE IF EXISTS pharmacy_final;

-- 기존 임시 테이블 삭제 (정리 목적)
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS phamercy;
DROP TABLE IF EXISTS shelter;
DROP TABLE IF EXISTS protection;

-- 3. shelter_final 테이블 생성 및 데이터 삽입 (PK 정의)
CREATE TABLE IF NOT EXISTS shelter_final (
    shelter_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INTEGER,
    address TEXT,
    phone TEXT
);

INSERT INTO shelter_final (name, capacity, address, phone)
SELECT
    업체명,
    CAST(수용능력수 AS INTEGER),
    소재지지번주소,
    업체전화번호
FROM stray_animal_shelter_status
ORDER BY 업체명;


-- 4. hospital_final 테이블 생성 및 데이터 삽입 (PK, lat/lon 추가)
CREATE TABLE IF NOT EXISTS hospital_final (
    hospital_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    region TEXT,
    lat REAL,
    lon REAL
);

INSERT INTO hospital_final (name, address, phone, region, lat, lon)
SELECT 
    사업장명,
    소재지지번주소,
    소재지시설전화번호,
    시군명,
    WGS84위도,
    WGS84경도
FROM animal_hospital_status
WHERE 영업상태명 = '정상'
ORDER BY 사업장명;


-- 5. pharmacy_final 테이블 생성 및 데이터 삽입 (PK, lat/lon 추가)
CREATE TABLE IF NOT EXISTS pharmacy_final (
    pharmacy_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    region TEXT,
    lat REAL,
    lon REAL
);

INSERT INTO pharmacy_final (name, address, phone, region, lat, lon)
SELECT 
    사업장명,
    소재지지번주소,
    소재지시설전화번호,
    시군명,
    WGS84위도,
    WGS84경도
FROM animal_pharmacy_status
WHERE 영업상태명 = '정상'
ORDER BY 사업장명;


-- 6. animal_status 테이블 생성 및 데이터 삽입 (PK, FK 정의, 전화번호/이름 JOIN 사용)
CREATE TABLE IF NOT EXISTS animal_status (
    animal_id INTEGER PRIMARY KEY,
    region TEXT,
    register_date TEXT,
    register_end_date TEXT,
    breed TEXT,
    color TEXT,
    years TEXT,
    weight TEXT,
    gender TEXT,
    shelter_id INTEGER, -- FK
    shelter_name TEXT,
    
    FOREIGN KEY(shelter_id) REFERENCES shelter_final(shelter_id)
);

INSERT INTO animal_status (
    region, register_date, register_end_date, breed, color, years, weight, gender, shelter_id, shelter_name
)
-- 💡 전화번호와 이름 두 가지 기준으로 JOIN하여 NULL을 최소화
SELECT
    p.시군명,
    p.공고시작일자,
    p.공고종료일자,
    p.품종,
    p.색상,
    p.나이,
    p.체중,
    p.성별,
    -- COALESCE: 1순위(전화번호 매칭) 실패 시 2순위(이름 매칭) shelter_id 사용
    COALESCE(s_phone.shelter_id, s_name.shelter_id) AS shelter_id,
    p.보호소명
FROM stray_animal_protection_status p
-- 1차 JOIN: 전화번호 기준으로 매칭 시도 (하이픈 제거하여 형식 불일치 보완 시도)
LEFT JOIN shelter_final s_phone 
    ON REPLACE(p.보호소전화번호, '-', '') = REPLACE(s_phone.phone, '-', '')
-- 2차 JOIN: 보호소명 기준으로 매칭 시도
LEFT JOIN shelter_final s_name 
    ON p.보호소명 = s_name.name
WHERE p.상태 = '보호중' 
ORDER BY p.공고시작일자 DESC;
"""

def execute_final_sql(db_path, sql_script):
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"데이터베이스 '{db_path}'에 연결했습니다.")
        
        cursor.executescript(sql_script)
        conn.commit()
        print("\n✅ 모든 SQL 쿼리가 성공적으로 실행되었습니다.")
        
        # NULL 값 재확인 쿼리
        null_count_query = """
        SELECT 
            COUNT(*) AS total_count,
            COUNT(CASE WHEN shelter_id IS NULL THEN 1 END) AS null_shelter_id_count,
            CAST(COUNT(CASE WHEN shelter_id IS NULL THEN 1 END) AS REAL) * 100 / COUNT(*) AS null_percentage
        FROM animal_status;
        """
        null_stats = pd.read_sql_query(null_count_query, conn)
        null_count = null_stats['null_shelter_id_count'][0]
        null_percent = null_stats['null_percentage'][0]
        
        print(f"\n[재실행 후 shelter_id NULL 값 현황]")
        print(f"NULL인 'shelter_id' 개수: {null_count}개")
        print(f"NULL 비율: {null_percent:.2f}%")

    except Exception as e:
        print(f"\n❌ SQL 실행 중 오류 발생: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("데이터베이스 연결 종료.")

# 최종 통합 SQL 스크립트 실행
execute_final_sql(db_path, SQL_SCRIPT)