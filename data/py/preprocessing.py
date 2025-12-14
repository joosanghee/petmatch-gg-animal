import sqlite3
import pandas as pd
import os

# --- 1. 경로 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# CSV 파일 폴더 위치
csv_folder = os.path.join(current_dir, "../csv")      
db_folder = os.path.join(current_dir, "../processed") 
db_path = os.path.join(db_folder, "animal_data.db")

# 로드할 CSV 목록
csv_files = {
    "유기동물보호현황utf8.csv": "stray_animal_protection_status",
    "동물병원현황utf8.csv": "animal_hospital_status",
    "동물약국현황utf8.csv": "animal_pharmacy_status",
    "유기 동물 보호 현황_품종코드.csv": "breed_codes" 
}

# --- 2. CSV를 DB로 로드하는 함수 ---
def load_csv_to_db(conn):
    print("📂 CSV 파일 로드 시작 (보호소 현황은 기존 데이터 유지)...")
    
    if not os.path.exists(csv_folder):
        print(f"⚠️ 경고: CSV 폴더({csv_folder})를 찾을 수 없습니다. 경로를 확인해주세요.")
    
    for file_name, table_name in csv_files.items():
        file_path = os.path.join(csv_folder, file_name)
        
        if not os.path.exists(file_path):
            print(f"  ❌ 파일 없음 (건너뜀): {file_name}")
            continue
            
        try:
            # 인코딩 자동 감지
            try:
                df = pd.read_csv(file_path, encoding='cp949')
            except:
                df = pd.read_csv(file_path, encoding='utf-8')
            
            # DB에 저장
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"  ✅ {table_name} 업데이트 완료 ({len(df)}건)")
        except Exception as e:
            print(f"  ❌ {file_name} 로드 실패: {e}")

# --- 3. 최종 테이블 생성 SQL (품종 매칭 로직 포함) ---
SQL_SCRIPT = """
PRAGMA foreign_keys = ON;

-- 1. 기존 최종 테이블 삭제 (새로 만들기 위해)
DROP TABLE IF EXISTS animal_status;
DROP TABLE IF EXISTS shelter_final;
DROP TABLE IF EXISTS hospital_final;
DROP TABLE IF EXISTS pharmacy_final;

-- 2. 보호소 테이블 (shelter_final)
-- 기존에 로드된 stray_animal_shelter_status 테이블 사용
CREATE TABLE shelter_final (
    shelter_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INTEGER,
    address TEXT,
    phone TEXT
);

INSERT INTO shelter_final (name, capacity, address, phone)
SELECT 업체명, CAST(수용능력수 AS INTEGER), 소재지지번주소, 업체전화번호
FROM stray_animal_shelter_status
ORDER BY 업체명;

-- 3. 동물병원 테이블
CREATE TABLE hospital_final (
    hospital_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    region TEXT,
    lat REAL,
    lon REAL
);
INSERT INTO hospital_final (name, address, phone, region, lat, lon)
SELECT 사업장명, 소재지지번주소, 소재지시설전화번호, 시군명, WGS84위도, WGS84경도
FROM animal_hospital_status WHERE 영업상태명 = '정상' ORDER BY 사업장명;

-- 4. 동물약국 테이블
CREATE TABLE pharmacy_final (
    pharmacy_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    region TEXT,
    lat REAL,
    lon REAL
);
INSERT INTO pharmacy_final (name, address, phone, region, lat, lon)
SELECT 사업장명, 소재지지번주소, 소재지시설전화번호, 시군명, WGS84위도, WGS84경도
FROM animal_pharmacy_status WHERE 영업상태명 = '정상' ORDER BY 사업장명;

-- 5. 유기동물 현황 테이블 (animal_status)
CREATE TABLE animal_status (
    animal_id INTEGER PRIMARY KEY,
    region TEXT,
    register_date TEXT,
    register_end_date TEXT,
    breed TEXT,       -- 웹사이트에 표시될 품종명 (예: 골든 리트리버)
    breed_code TEXT,  -- 원본 품종 코드 (예: 000054) - 필요할까봐 남겨둠
    color TEXT,
    years TEXT,
    weight TEXT,
    gender TEXT,
    image_url TEXT,
    shelter_id INTEGER,
    shelter_name TEXT,
    FOREIGN KEY(shelter_id) REFERENCES shelter_final(shelter_id)
);

INSERT INTO animal_status (
    region, register_date, register_end_date, breed, breed_code, color, years, weight, gender, image_url, shelter_id, shelter_name
)
SELECT
    p.시군명,
    p.공고시작일자,
    p.공고종료일자,
    COALESCE(b.품종명, p.품종) AS breed_final,
    p.품종 AS breed_code_origin,
    p.색상,
    p.나이,
    p.체중,
    p.성별,
    -- 이미지 (썸네일 우선)
    COALESCE(p.썸네일이미지경로, p.이미지경로),
    COALESCE(s_phone.shelter_id, s_name.shelter_id),
    p.보호소명
FROM stray_animal_protection_status p
LEFT JOIN breed_codes b ON CAST(p.품종 AS INTEGER) = CAST(b.품종 AS INTEGER)
LEFT JOIN shelter_final s_phone ON REPLACE(p.보호소전화번호, '-', '') = REPLACE(s_phone.phone, '-', '')
LEFT JOIN shelter_final s_name ON p.보호소명 = s_name.name
WHERE p.상태 = '보호중'
ORDER BY p.공고시작일자 DESC;
"""

def main():
    if not os.path.exists(db_folder):
        os.makedirs(db_folder, exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    print(f"데이터베이스 연결: {db_path}")

    # 1. CSV 로드 (품종 코드 포함)
    load_csv_to_db(conn)
    
    # 2. SQL 실행 (매칭 및 테이블 생성)
    try:
        conn.executescript(SQL_SCRIPT)
        conn.commit()
        print("\n DB 업데이트 완료!")
        
        # 확인
        cursor = conn.cursor()
        cursor.execute("SELECT breed, breed_code FROM animal_status LIMIT 3")
        rows = cursor.fetchall()
        print(f" 변환 결과 예시 (품종명 / 코드): {rows}")
        
    except Exception as e:
        print(f"\n SQL 실행 오류: {e}")
    
    conn.close()

if __name__ == "__main__":
    main()