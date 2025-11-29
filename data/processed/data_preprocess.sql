CREATE TABLE if not EXISTS hospital AS
SELECT 
    사업장명 AS name,
    소재지시설전화번호 AS tel,
    소재지지번주소 AS addr
FROM animal_hospital_status
WHERE 영업상태명 = '정상'
ORDER BY addr ASC;

CREATE TABLE if not EXISTS phamercy AS
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