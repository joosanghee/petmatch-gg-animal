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

CREATE TABLE if not EXISTS protection AS
SELECT 
    발견장소 AS findplace,
    보호소지번주소 AS addr,
	공고고유번호 AS fid,
	공고시작일자 as startdate,
	공고종료일자 as enddate,
	품종 as breed,
	색상 as color,
	나이 as age,
	체중 as weight,
	성별 as sex,
	중성화여부 as neutering,
	특징 as feature,
	보호소명 as proname,
	보호소전화번호 as pronum,
	이미지경로 as photolink
FROM stray_animal_protection_status
WHERE 상태 = '보호중'
ORDER BY addr ASC;
