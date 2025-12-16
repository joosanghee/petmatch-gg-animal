# 🐾 PetMatch (펫매치) - 유기동물 입양 정보 플랫폼

> **"가족을 기다리는 친구들을 찾아요"**
>
> PetMatch는 경기도 지역의 유기동물 공고 정보를 실시간으로 제공하고, 가까운 보호소와 동물병원/약국 정보를 쉽고 빠르게 찾을 수 있도록 돕는 웹 플랫폼입니다.


##  Key Features (핵심 기능)

### 1.  유기동물 찾기 (`/animals`)
* **스마트 검색 & 필터**: 지역(시/군), 품종(개/고양이), 성별, 키워드 검색을 통해 원하는 조건의 동물을 빠르게 찾을 수 있습니다.
* **상세 정보 모달(Modal)**: 페이지 이동 없이 팝업창을 통해 사진, 나이, 체중, 특징, 보호소 정보를 즉시 확인할 수 있습니다.
* **데이터 매핑**: 공공데이터의 품종 코드(예: `000054`)를 사용자가 알아보기 쉬운 품종명(예: `골든 리트리버`)으로 자동 변환하여 표시합니다.

### 2.  생활 정보 (`/hospital`, `/shelter`)
* **동물병원/약국 찾기**: 내 주변의 동물병원과 동물약국을 구분하여 검색하고, 네이버 지도와 연동하여 위치를 확인합니다.
* **보호소 정보**: 각 지역 보호소의 연락처, 주소, 수용 가능 정보를 제공합니다.

### 3.  회원 서비스
* **보안 로그인**: `Werkzeug` 보안 라이브러리를 사용하여 비밀번호를 암호화(Hash)하여 안전하게 저장합니다.
* **개인화 UI**: 로그인 시 상단바에 사용자 닉네임이 표시되며, 로그인 상태에 따라 UI가 동적으로 변경됩니다.
* **회원가입**: 누구나 쉽게 이메일과 닉네임으로 가입할 수 있습니다.

<br>

##  Tech Stack (기술 스택)

| 분류 | 기술 스택 |
| :--- | :--- |
| **Backend** | Python 3, **Flask** (Web Framework) |
| **Database** | **SQLite** (Relational DB) |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla), Jinja2 |
| **Data** | 공공데이터포털 CSV (Pandas 전처리) |
| **Tools** | VS Code, Git |

<br>

##  Project Structure (폴더 구조)

```bash
PetMatch/
├── beckend/                  # 백엔드 및 서버 코드
│   ├── app.py                # 메인 Flask 서버 실행 파일
│   ├── create_user_db.py     # 회원 DB 초기화 스크립트
│   ├── update_db.py          # 관심 테이블 추가
│   └── frontend_test/        # 프론트엔드 리소스 (Templates & Static)
│       ├── index.html        # 메인 홈
│       ├── animals.html      # 유기동물 목록 및 상세 팝업
│       ├── hospital.html     # 병원/약국 정보
│       ├── shelter.html      # 보호소 정보
│       ├── login.html        # 로그인 페이지
│       ├── signup.html       # 회원가입 페이지
│       └── style.css         # 전체 스타일시트
├── data/                     # 데이터 저장소
│   ├── csv/                  # 원본 공공데이터 (CSV 파일)
│   ├── processed/            # 가공된 DB 파일 (animal_data.db, user_data.db)
│   └── py/ 
│       ├── cvstodb.py        # (CSV -> DB 변환)
│       └── preprocessing.py  # 데이터 전처리 (CSV -> DB 변환)
└── README.md                 # 프로젝트 설명서
```


## How to run (실행방법)

cd backend -> app.py 실행
