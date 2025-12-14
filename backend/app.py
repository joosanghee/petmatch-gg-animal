import sqlite3
import os
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__, template_folder='frontend_test', static_folder='frontend_test')
app.secret_key = 'super_secret_key_for_petmatch_prince_minjae'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANIMAL_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'animal_data.db')
USER_DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'user_data.db')

def get_animal_db():
    conn = sqlite3.connect(ANIMAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_db():
    conn = sqlite3.connect(USER_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('is_admin') != 1:
            flash("관리자만 접근할 수 있습니다.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/style.css')
def serve_css(): return send_from_directory('frontend_test', 'style.css')

@app.route('/')
def index():
    conn = get_animal_db()
    items = conn.execute('SELECT * FROM animal_status ORDER BY register_date DESC LIMIT 4').fetchall()
    conn.close()
    return render_template('index.html', latest_animals=items)





@app.route('/animals')
def animal_list():
    conn = get_animal_db()
    animals = []
    region_list = []
    
    # 파라미터 받기
    keyword = request.args.get('keyword', '')
    region = request.args.get('region', '전체')
    species = request.args.get('species', '전체')
    gender = request.args.get('gender', '전체')
    sort = request.args.get('sort', 'newest')
    
    sql = "SELECT * FROM animal_status WHERE 1=1"
    params = []

    if conn:
        try:
            regions_data = conn.execute("SELECT DISTINCT region FROM animal_status WHERE region IS NOT NULL AND region != '' ORDER BY region").fetchall()
            region_list = [row['region'] for row in regions_data]

            # --- 기존 검색 로직 시작 ---
            if keyword:
                sql += " AND (breed LIKE ? OR shelter_name LIKE ?)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            if region != '전체':
                sql += " AND region LIKE ?"
                params.append(f'%{region}%')
            
            if species == '고양이':
                sql += " AND breed LIKE '%고양이%'"
            elif species == '개':
                sql += " AND breed NOT LIKE '%고양이%'"

            if gender == '수컷':
                sql += " AND (gender = 'M' OR gender LIKE '수컷%')"
            elif gender == '암컷':
                sql += " AND (gender = 'F' OR gender LIKE '암컷%')"
            
            if sort == 'oldest':
                sql += " ORDER BY register_date ASC"
            else:
                sql += " ORDER BY register_date DESC"
            
            animals = conn.execute(sql, params).fetchall()
        except Exception as e:
            print(f"검색 오류: {e}")
        finally:
            conn.close()
            

    return render_template('animals.html', animals=animals, 
                           region_list=region_list,
                           curr_keyword=keyword, curr_region=region, 
                           curr_species=species, curr_gender=gender,
                           curr_sort=sort)

# --- 3. 병원/약국 목록  ---
@app.route('/hospital')
def hospital_list():
    conn = get_animal_db()
    entities = []
    region_list = []

    keyword = request.args.get('keyword', '')
    type_filter = request.args.get('type', '전체')
    region_filter = request.args.get('region', '전체')
    
    try:

        r_query = """
            SELECT DISTINCT region FROM hospital_final WHERE region IS NOT NULL AND region != ''
            UNION
            SELECT DISTINCT region FROM pharmacy_final WHERE region IS NOT NULL AND region != ''
            ORDER BY region
        """
        region_rows = conn.execute(r_query).fetchall()
        region_list = [row['region'] for row in region_rows]


        base_query = "SELECT * FROM (SELECT hospital_id as id, name, address, phone, region, '동물병원' as type FROM hospital_final UNION ALL SELECT pharmacy_id as id, name, address, phone, region, '동물약국' as type FROM pharmacy_final) WHERE 1=1"
        params = []
        if keyword:
            base_query += " AND (name LIKE ? OR address LIKE ?)"
            params.extend([f'%{keyword}%', f'%{keyword}%'])
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

    return render_template('hospital.html', entities=entities, 
                           region_list=region_list,
                           curr_keyword=keyword, curr_type=type_filter, curr_region=region_filter)

# --- 4. 보호소 목록  ---
@app.route('/shelter')
def shelter_list():
    conn = get_animal_db()
    shelters = []
    region_list = [] 

    keyword = request.args.get('keyword', '')
    region_filter = request.args.get('region', '전체')
    
    try:
        all_shelters = conn.execute("SELECT address FROM shelter_final WHERE address IS NOT NULL").fetchall()
        temp_regions = set()
        for row in all_shelters:
            addr = row['address'].split()
            if len(addr) >= 2 and addr[0] == '경기도':
                temp_regions.add(addr[1]) # '경기도' 다음 단어 (수원시 등)
            elif len(addr) >= 1:
                temp_regions.add(addr[0])
        
        region_list = sorted(list(temp_regions)) # 가나다순 정렬


        sql = "SELECT * FROM shelter_final WHERE 1=1"
        params = []
        if keyword:
            sql += " AND (name LIKE ? OR address LIKE ?)"
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        if region_filter != '전체':
            sql += " AND address LIKE ?"
            params.append(f'%{region_filter}%')
        sql += " ORDER BY name ASC"
        shelters = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    return render_template('shelter.html', shelters=shelters, 
                           region_list=region_list,
                           curr_keyword=keyword, curr_region=region_filter)

@app.route('/api/animal/<int:id>')
def get_animal_detail(id):
    conn = get_animal_db()
    data = {}
    try:
        row = conn.execute('SELECT * FROM animal_status WHERE animal_id = ?', (id,)).fetchone()
        if row: data = dict(row)
    finally: conn.close()
    return jsonify(data)

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
            session['is_admin'] = user['is_admin']
            flash(f"환영합니다, {user['name']}님!", 'success')
            return redirect(url_for('index'))
        else: flash("로그인 실패", 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name, email, pw = request.form['name'], request.form['email'], request.form['password']
        is_admin = 1 if request.form.get('is_admin') else 0
        hashed = generate_password_hash(pw)
        conn = get_user_db()
        try:
            conn.execute('INSERT INTO users (email, password_hash, name, is_admin) VALUES (?, ?, ?, ?)', (email, hashed, name, is_admin))
            conn.commit()
            flash("가입 완료!", 'success')
            return redirect(url_for('login'))
        except: flash("이미 존재하는 이메일입니다.", 'error')
        finally: conn.close()
    return render_template('signup.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_animal_db()
    animals = conn.execute("SELECT * FROM animal_status ORDER BY register_date").fetchall()
    shelters = conn.execute("SELECT * FROM shelter_final ORDER BY name").fetchall()
    hospitals = conn.execute("SELECT * FROM hospital_final ORDER BY name").fetchall()
    conn.close()
    return render_template('admin.html', animals=animals, shelters=shelters, hospitals=hospitals)

@app.route('/admin/delete/<type>/<int:id>', methods=['POST'])
@admin_required
def delete_item(type, id):
    conn = get_animal_db()
    try:
        if type == 'animal': conn.execute("DELETE FROM animal_status WHERE animal_id = ?", (id,))
        elif type == 'shelter': conn.execute("DELETE FROM shelter_final WHERE shelter_id = ?", (id,))
        elif type == 'hospital': conn.execute("DELETE FROM hospital_final WHERE hospital_id = ?", (id,))
        conn.commit()
    finally: conn.close()
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/add', methods=['POST'])
@admin_required
def add_item():
    t = request.form['item_type']
    conn = get_animal_db()
    try:
        if t == 'animal':
            reg_date = request.form['register_date'].replace('-', '')
            end_date = request.form['register_end_date'].replace('-', '')

            conn.execute("""
                INSERT INTO animal_status 
                (breed, gender, weight, years, region, shelter_name, register_date, register_end_date, image_url) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form['breed'],
                request.form['gender'],
                request.form['weight'],
                request.form['years'],
                request.form['region'],
                request.form['shelter_name'],
                reg_date,
                end_date,
                request.form['image_url']
            ))
            
        elif t == 'shelter':
            conn.execute("INSERT INTO shelter_final (name, phone, address) VALUES (?,?,?)", 
                         (request.form['name'], request.form['phone'], request.form['address']))
            
        elif t == 'hospital':
            conn.execute("INSERT INTO hospital_final (name, phone, address, region, lat, lon) VALUES (?,?,?,?,0,0)", 
                         (request.form['name'], request.form['phone'], request.form['address'], '기타'))
            
        conn.commit()
        flash("성공적으로 추가되었습니다!", 'success')
    except Exception as e:
        flash(f"추가 실패: {e}", 'error')
        print(f"에러: {e}")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)