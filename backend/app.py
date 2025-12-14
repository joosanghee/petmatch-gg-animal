import sqlite3
import os
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='frontend_test', static_folder='frontend_test')
app.secret_key = 'super_secret_key_for_petmatch_prince_minjae'

# --- 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANIMAL_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'animal_data.db')
USER_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'user_data.db')

# --- DB 연결 함수 ---
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

# --- 헬퍼 함수: 현재 로그인한 유저의 찜 목록(ID 리스트) 가져오기 ---
def get_user_favorites():
    if 'user_id' not in session: return []
    conn = get_user_db()
    favs = []
    if conn:
        rows = conn.execute('SELECT animal_id FROM favorites WHERE user_id = ?', (session['user_id'],)).fetchall()
        favs = [row['animal_id'] for row in rows]
        conn.close()
    return favs

# --- 라우트 ---

@app.route('/style.css')
def serve_css():
    return send_from_directory('frontend_test', 'style.css')

@app.route('/')
def index():
    conn = get_animal_db()
    latest_animals = []
    if conn:
        latest_animals = conn.execute('SELECT * FROM animal_status ORDER BY register_date DESC LIMIT 4').fetchall()
        conn.close()
    
    # 찜한 상태 표시를 위해 내 찜 목록 가져오기
    fav_ids = get_user_favorites()
    
    return render_template('index.html', latest_animals=latest_animals, fav_ids=fav_ids)

@app.route('/animals')
def animal_list():
    conn = get_animal_db()
    animals = []
    keyword = request.args.get('keyword', '')
    region = request.args.get('region', '전체')
    species = request.args.get('species', '전체')
    gender = request.args.get('gender', '전체')
    
    sql = "SELECT * FROM animal_status WHERE 1=1"
    params = []

    if conn:
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
        conn.close()
            
    fav_ids = get_user_favorites()
    return render_template('animals.html', animals=animals, 
                           curr_keyword=keyword, curr_region=region, 
                           curr_species=species, curr_gender=gender,
                           fav_ids=fav_ids)

# ⭐️ [신규] 좋아요 토글 (API)
@app.route('/api/favorite/<int:animal_id>', methods=['POST'])
def toggle_favorite(animal_id):
    if 'user_id' not in session:
        return jsonify({'status': 'fail', 'message': '로그인이 필요합니다.'}), 401

    conn = get_user_db()
    user_id = session['user_id']
    
    # 이미 찜했는지 확인
    exists = conn.execute('SELECT 1 FROM favorites WHERE user_id=? AND animal_id=?', (user_id, animal_id)).fetchone()
    
    if exists:
        # 있으면 삭제 (취소)
        conn.execute('DELETE FROM favorites WHERE user_id=? AND animal_id=?', (user_id, animal_id))
        action = 'removed'
    else:
        # 없으면 추가 (찜)
        conn.execute('INSERT INTO favorites (user_id, animal_id) VALUES (?, ?)', (user_id, animal_id))
        action = 'added'
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'action': action})

# ⭐️ [신규] 마이페이지 (내가 찜한 동물들)
@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        flash("로그인이 필요한 페이지입니다.", 'error')
        return redirect(url_for('login'))
        
    # 1. 유저 DB에서 찜한 ID들 가져오기
    fav_ids = get_user_favorites()
    
    # 2. 동물 DB에서 해당 ID들의 상세 정보 가져오기
    fav_animals = []
    if fav_ids:
        conn = get_animal_db()
        # "SELECT * FROM ... WHERE animal_id IN (1, 3, 5)" 형태로 쿼리 생성
        placeholders = ','.join('?' for _ in fav_ids)
        sql = f"SELECT * FROM animal_status WHERE animal_id IN ({placeholders})"
        fav_animals = conn.execute(sql, fav_ids).fetchall()
        conn.close()
        
    return render_template('mypage.html', animals=fav_animals, user_name=session['user_name'])

# --- (기존 병원, 보호소, 로그인 등 코드는 그대로 유지) ---
@app.route('/hospital')
def hospital_list():
    conn = get_animal_db()
    entities = []
    keyword = request.args.get('keyword', '')
    type_filter = request.args.get('type', '전체')
    region_filter = request.args.get('region', '전체')
    
    if conn:
        base_query = """SELECT * FROM (
            SELECT hospital_id as id, name, address, phone, region, '동물병원' as type FROM hospital_final
            UNION ALL
            SELECT pharmacy_id as id, name, address, phone, region, '동물약국' as type FROM pharmacy_final
        ) AS base WHERE 1=1"""
        params = []
        if keyword:
            base_query += " AND (name LIKE ? OR address LIKE ?)"
            params.append(f'%{keyword}%'); params.append(f'%{keyword}%')
        if type_filter != '전체':
            base_query += " AND type = ?"; params.append(type_filter)
        if region_filter != '전체':
            base_query += " AND region LIKE ?"; params.append(f'%{region_filter}%')
        base_query += " ORDER BY name ASC"
        entities = conn.execute(base_query, params).fetchall()
        conn.close()
    return render_template('hospital.html', entities=entities, curr_keyword=keyword, curr_type=type_filter, curr_region=region_filter)

@app.route('/shelter')
def shelter_list():
    conn = get_animal_db()
    shelters = []
    keyword = request.args.get('keyword', '')
    region_filter = request.args.get('region', '전체')
    if conn:
        sql = "SELECT * FROM shelter_final WHERE 1=1"
        params = []
        if keyword:
            sql += " AND (name LIKE ? OR address LIKE ?)"
            params.append(f'%{keyword}%'); params.append(f'%{keyword}%')
        if region_filter != '전체':
            sql += " AND address LIKE ?"; params.append(f'%{region_filter}%')
        sql += " ORDER BY name ASC"
        shelters = conn.execute(sql, params).fetchall()
        conn.close()
    return render_template('shelter.html', shelters=shelters, curr_keyword=keyword, curr_region=region_filter)

@app.route('/api/animal/<int:id>')
def get_animal_detail(id):
    conn = get_animal_db()
    animal_data = {}
    if conn:
        row = conn.execute('SELECT * FROM animal_status WHERE animal_id = ?', (id,)).fetchone()
        if row: animal_data = dict(row)
        conn.close()
    return jsonify(animal_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_user_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash(f"환영합니다, {user['name']}님!", 'success')
            return redirect(url_for('index'))
        else:
            flash("이메일 또는 비밀번호가 올바르지 않습니다.", 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        conn = get_user_db()
        try:
            conn.execute('INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)', (email, hashed_pw, name))
            conn.commit()
            flash("회원가입 완료! 로그인해주세요.", 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("이미 등록된 이메일입니다.", 'error')
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("로그아웃 되었습니다.", 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)