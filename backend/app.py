import sqlite3
import os
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash # 암호화 도구

app = Flask(__name__, 
            template_folder='frontend_test', 
            static_folder='frontend_test')

# 🔐 세션을 위한 시크릿 키 (보안상 랜덤 문자열 사용)
app.secret_key = 'super_secret_key_for_petmatch_prince_minjae'

# --- 데이터베이스 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANIMAL_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'animal_data.db')
USER_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'user_data.db') # 회원 DB 경로

# --- DB 연결 함수들 ---
def get_animal_db():
    if not os.path.exists(ANIMAL_DB_PATH): return None
    conn = sqlite3.connect(ANIMAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_db():
    if not os.path.exists(USER_DB_PATH): return None
    conn = sqlite3.connect(USER_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- CSS 파일 처리 ---
@app.route('/style.css')
def serve_css():
    return send_from_directory('frontend_test', 'style.css')

# --- 라우트 ---

@app.route('/')
def index():
    conn = get_animal_db()
    latest_animals = []
    if conn:
        try:
            latest_animals = conn.execute('SELECT * FROM animal_status ORDER BY register_date DESC LIMIT 4').fetchall()
        finally:
            conn.close()
    return render_template('index.html', latest_animals=latest_animals)

@app.route('/animals')
def animal_list():
    conn = get_animal_db()
    animals = []
    
    # 필터 파라미터 받기
    keyword = request.args.get('keyword', '')
    region = request.args.get('region', '전체')
    species = request.args.get('species', '전체')
    gender = request.args.get('gender', '전체')
    
    sql = "SELECT * FROM animal_status WHERE 1=1"
    params = []

    if conn:
        try:
            if keyword:
                sql += " AND (breed LIKE ? OR shelter_name LIKE ?)"
                params.append(f'%{keyword}%'); params.append(f'%{keyword}%')
            if region != '전체':
                sql += " AND region LIKE ?"
                params.append(f'%{region}%')
            if gender == '수컷': sql += " AND gender = 'M'"
            elif gender == '암컷': sql += " AND gender = 'F'"
            if species == '개': sql += " AND breed NOT LIKE '%고양이%'"
            elif species == '고양이': sql += " AND breed LIKE '%고양이%'"
            
            sql += " ORDER BY register_date DESC"
            animals = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
            
    return render_template('animals.html', animals=animals, 
                           curr_keyword=keyword, curr_region=region, 
                           curr_species=species, curr_gender=gender)

@app.route('/hospital')
def hospital_list():
    conn = get_animal_db()
    entities = []
    keyword = request.args.get('keyword', '')
    type_filter = request.args.get('type', '전체')
    region_filter = request.args.get('region', '전체')
    
    if conn:
        try:
            base_query = """
                SELECT * FROM (
                    SELECT hospital_id as id, name, address, phone, region, '동물병원' as type FROM hospital_final
                    UNION ALL
                    SELECT pharmacy_id as id, name, address, phone, region, '동물약국' as type FROM pharmacy_final
                ) AS base WHERE 1=1
            """
            params = []
            if keyword:
                base_query += " AND (name LIKE ? OR address LIKE ?)"
                params.append(f'%{keyword}%'); params.append(f'%{keyword}%')
            if type_filter != '전체':
                base_query += " AND type = ?"
                params.append(type_filter)
            if region_filter != '전체':
                base_query += " AND region LIKE ?"
                params.append(f'%{region_filter}%')
            
            base_query += " ORDER BY name ASC"
            entities = conn.execute(base_query, params).fetchall()
        finally:
            conn.close()
    return render_template('hospital.html', entities=entities, curr_keyword=keyword, curr_type=type_filter, curr_region=region_filter)

@app.route('/shelter')
def shelter_list():
    conn = get_animal_db()
    shelters = []
    keyword = request.args.get('keyword', '')
    region_filter = request.args.get('region', '전체')
    
    if conn:
        try:
            sql = "SELECT * FROM shelter_final WHERE 1=1"
            params = []
            if keyword:
                sql += " AND (name LIKE ? OR address LIKE ?)"
                params.append(f'%{keyword}%'); params.append(f'%{keyword}%')
            if region_filter != '전체':
                sql += " AND address LIKE ?"
                params.append(f'%{region_filter}%')
            sql += " ORDER BY name ASC"
            shelters = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    return render_template('shelter.html', shelters=shelters, curr_keyword=keyword, curr_region=region_filter)

@app.route('/api/animal/<int:id>')
def get_animal_detail(id):
    conn = get_animal_db()
    animal_data = {}
    if conn:
        try:
            row = conn.execute('SELECT * FROM animal_status WHERE animal_id = ?', (id,)).fetchone()
            if row: animal_data = dict(row)
        finally:
            conn.close()
    return jsonify(animal_data)

# ----------------------------------------------------
# 🔐 [신규] 로그인 & 회원가입 기능
# ----------------------------------------------------

# 1. 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_user_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        # 비밀번호 확인 (해시 비교)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f"환영합니다, {user['name']}님!", 'success')
            return redirect(url_for('index'))
        else:
            flash("이메일 또는 비밀번호가 올바르지 않습니다.", 'error')
            
    return render_template('login.html')

# 2. 회원가입
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # 비밀번호 암호화
        hashed_pw = generate_password_hash(password)
        
        conn = get_user_db()
        try:
            conn.execute('INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)', 
                         (email, hashed_pw, name))
            conn.commit()
            flash("회원가입이 완료되었습니다! 로그인해주세요.", 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("이미 등록된 이메일입니다.", 'error')
        finally:
            conn.close()
            
    return render_template('signup.html')

# 3. 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    flash("로그아웃 되었습니다.", 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)