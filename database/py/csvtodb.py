import pandas as pd
import sqlite3
import re
import os

# --- 경로 및 파일 설정 ---
csv_folder = "../csv" # CSV 파일이 있는 폴더 (database/csv)
db_folder = "../db"   # DB 파일이 저장될 폴더 (database/db)
db_name = "animal_data.db"
db_path = os.path.join(db_folder, db_name) 

files = {
    "유기동물보호현황utf8.csv": "stray_animal_protection_status",
    "유기동물보호시설현황utf8.csv": "stray_animal_shelter_status",
    "동물병원현황utf8.csv": "animal_hospital_status",
    "동물약국현황utf8.csv": "animal_pharmacy_status"
}

# --- 보조 함수 ---

def clean_column_name(col):
    col = re.sub(r'[()\s\/\-\.]+', '_', col.strip())
    col = re.sub(r'_+', '_', col)
    col = re.sub(r'(^_|_$)', '', col)
    return col.lower()

# --- 메인 함수: 인코딩 재시도 로직 추가 ---

def create_animal_data_db_with_fallback(files, db_path, csv_folder, db_folder):
    os.makedirs(db_folder, exist_ok=True)
    
    # 기존 DB 파일이 있다면 삭제하고 새로 생성하여 이전의 부분적인 저장 내용을 초기화합니다.
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"기존 DB 파일 '{db_name}'을 삭제하고 새로 시작합니다.")
        
    conn = sqlite3.connect(db_path)
    print(f"데이터베이스 연결 시도: '{db_path}'")

    for file_name, table_name in files.items():
        file_path = os.path.join(csv_folder, file_name)
        
        try:
            # 1차 시도:  'euc-kr' 인코딩

            df = pd.read_csv(file_path, encoding='utf-8')
            used_encoding = 'utf-8'

            # 컬럼명 정리
            df.columns = [clean_column_name(col) for col in df.columns]

            # 데이터베이스에 저장
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f" '{table_name}' 테이블로 성공적으로 저장되었습니다. (인코딩: {used_encoding})")
        
        except FileNotFoundError:
            print(f" 파일 찾기 오류: '{file_path}' 경로에 파일이 없습니다.")
        except UnicodeDecodeError:
            print(f"최종 인코딩 오류: '{file_name}'은 'euc-kr'과 'utf-8' 모두로 디코딩할 수 없습니다. 다른 인코딩을 확인해주세요.")
        except Exception as e:
            print(f"'{file_name}' 처리 중 알 수 없는 오류 발생: {e}")

    conn.close()
    print("\n작업 완료: 데이터베이스 연결이 종료되었습니다.")

# --- 실행 부분 ---
create_animal_data_db_with_fallback(files, db_path, csv_folder, db_folder)