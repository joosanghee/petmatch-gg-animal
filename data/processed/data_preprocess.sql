CREATE TABLE if not EXISTS hospital AS
SELECT 
    사업장명 AS name,
    소재지시설전화번호 AS tel,
    소재지지번주소 AS addr
FROM animal_hospital_status
WHERE 영업상태명 = '정상'
ORDER BY addr ASC;

CREATE TABLE if not EXISTS pharmacy AS
SELECT 
    사업장명 AS name,
    소재지시설전화번호 AS tel,
    소재지지번주소 AS addr
FROM animal_pharmacy_status
WHERE 영업상태명 = '정상'
ORDER BY addr ASC;

CREATE TABLE if not EXISTS shelter AS
SELECT 
    업체명 AS name,
    업체전화번호 AS tel,
    소재지지번주소 AS addr
FROM stray_animal_shelter_status
ORDER BY addr ASC;

CREATE TABLE IF NOT EXISTS protection AS
SELECT
  "시군명"           AS cityname,
  "접수일자"         AS received_date,
  "발견장소"         AS found_location,
  "상태"             AS animal_status,
  "공고고유번호"     AS notice_id,
  "공고시작일자"     AS notice_start_date,
  "공고종료일자"     AS notice_end_date,
  "품종"             AS breed,
  "색상"             AS color,
  "나이"             AS age,
  "체중"             AS weight,
  "성별"             AS sex,
  "중성화여부"       AS neutered,
  "특징"             AS features,
  "보호소명"         AS shelter_name,
  "보호소전화번호"   AS shelter_tel,
  "보호소도로명주소" AS shelter_addr,
  "관할기관"         AS jurisdiction,
  "이미지경로"       AS image_path
FROM "stray_animal_protection_status"
WHERE 상태 = '보호중'
ORDER BY notice_id, notice_start_date, notice_end_date,shelter_addr;