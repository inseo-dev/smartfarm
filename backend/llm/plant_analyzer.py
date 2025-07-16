import base64
import pymysql
import json
import re
from PIL import Image, ImageEnhance
from openai import OpenAI
import boto3
import os
from dotenv import load_dotenv
from collections import OrderedDict
from typing import Dict, Optional

# ====== .env 로드 및 전역 설정 ======
# 스크립트가 로드될 때 한 번만 실행됩니다.
load_dotenv()

# ✅ AWS 인증 정보 및 클라이언트
aws_access_key_id = os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key = os.getenv("AWS_SECRET_KEY")
bucket_name = os.getenv("S3_BUCKET")
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# ✅ DB 연결 정보
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# ✅ OpenAI 클라이언트 설정
client = OpenAI()

# ✅ 임시 파일 경로
downloaded_image = "downloaded_image.jpg"
resized_image = "resized_image.jpg"


# ====== 헬퍼 함수들 (변경 없음) ======

def crop_resize_brighten(input_path, output_path, size=(512, 512), brightness_factor=1.3):
    """이미지 전처리: 중앙 크롭 → 리사이즈 → 밝기 조절"""
    img = Image.open(input_path).convert("RGB")
    width, height = img.size
    crop_size = min(width, height)
    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    cropped = img.crop((left, top, right, bottom))
    resized = cropped.resize(size, resample=Image.LANCZOS)
    enhancer = ImageEnhance.Brightness(resized)
    brightened = enhancer.enhance(brightness_factor)
    brightened.save(output_path)
    print(f"✅ 이미지 전처리 완료: {output_path}")

def get_latest_avg_by_sensor_60min(sensor_type: str) -> float:
    """센서 타입별 최근 60분간 평균 가져오기"""
    query = """
        SELECT ROUND(AVG(sensor_value), 2) AS avg_value
        FROM (
            SELECT DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:00') AS minute,
                   AVG(sensor_value) AS sensor_value
            FROM sensor_data
            WHERE sensor_type = %s AND timestamp >= NOW() - INTERVAL 1 HOUR
            GROUP BY minute
            ORDER BY minute DESC
            LIMIT 60
        ) AS sub;
    """
    db = pymysql.connect(host=db_host, user=db_user, password=db_password,
                         database=db_name, charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)
    try:
        with db.cursor() as cursor:
            cursor.execute(query, (sensor_type,))
            result = cursor.fetchone()
    finally:
        db.close()
    return result["avg_value"] if result and result["avg_value"] is not None else 0.0

def get_latest_environment() -> Dict[str, float]:
    """현재 환경(온도, 습도, 조도, 토양 습도) 가져오기"""
    return {
        "temp": get_latest_avg_by_sensor_60min("temp"),
        "humidity": get_latest_avg_by_sensor_60min("humidity"),
        "light_intensity": get_latest_avg_by_sensor_60min("light_intensity"),
        "soil_moisture": get_latest_avg_by_sensor_60min("soil_moisture")
    }

def extract_plant_name(gpt_response: str) -> str:
    """GPT 응답에서 식물 이름 추출 및 후처리"""
    match = re.search(r"(감귤나무|레몬나무|바질|고추|토마토|상추|고수|파슬리|오이|가지|딸기|수박)", gpt_response)
    if match:
        return match.group(1)
    fallback = re.findall(r"([가-힣]+)(나무|모종)", gpt_response)
    if fallback:
        return fallback[-1][0] + fallback[-1][1]
    return gpt_response.strip()

def identify_plant(image_path: str) -> str:
    """Step 1. GPT로 식물 이름 추출"""
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    prompt = "이 식물은 어떤 식물로 보이니? 반드시 식물 이름만 한 줄로, 설명 없이 출력해줘. 예시: 바질, 토마토"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    )
    plant_name_raw = response.choices[0].message.content.strip()
    return re.sub(r"[^\uAC00-\uD7A3a-zA-Z0-9\s]", "", plant_name_raw).strip()

def generate_growth_recommendation(plant_name: str, env: Dict) -> str:
    """Step 2. GPT로 재배 환경 분석 및 권장 사항 생성"""
    prompt = f"""
너는 스마트팜을 관리하는 식물학 전문가 AI이다.

분석할 식물: {plant_name}

현재 환경:
- 온도: {env['temp']}°C
- 습도: {env['humidity']}%
- 조도: {env['light_intensity']} lux
- 토양 습도: {env['soil_moisture']}%

아래 형식에 맞춰 출력하라:

1. 식물 정보 및 권장 재배 환경 요약
   - 생장 단계 (한국어 단계명 + 영어 단계명 + 설명 bullet point)
   - 발육 상태 (색상, 형태, 병충해, 결구 진행 상태)
   - 권장 재배 환경 요약

2. 권장 재배 환경 (JSON 형식)
```json
{{
  "temp": {{ "from": 20, "to": 25 }},
  "humidity": {{ "from": 50, "to": 70 }},
  "light_time": {{ "from": 12, "to": 16 }},
  "light_intensity": {{ "from": 15000, "to": 20000 }},
  "soil_moisture": {{ "from": 40, "to": 60 }}
}}
```"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def insert_into_ai_diagnosis(plant_name: str, result: str, controls_json: Dict, image_url: str):
    """분석 결과를 DB에 저장"""
    db = pymysql.connect(host=db_host, user=db_user, password=db_password,
                         database=db_name, charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)
    try:
        with db.cursor() as cursor:
            sql = """
            INSERT INTO ai_diagnosis (plant_name, result, recommendations, controls, image_url)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(sql, (
                plant_name,
                result,
                "",  # recommendations 필드는 비워둠
                json.dumps(controls_json, ensure_ascii=False, sort_keys=False),
                image_url
            ))
            db.commit()
    finally:
        db.close()

# ====== ✅ 메인 실행 함수 ======
def run_plant_diagnosis(s3_object_key: str = "latest_frame.jpg") -> Optional[Dict]:
    """
    S3 이미지를 기반으로 식물 진단 전체 프로세스를 실행하고 결과를 DB에 저장합니다.

    :param s3_object_key: S3 버킷에 있는 이미지의 파일명 (예: 'latest_frame.jpg')
    :return: 성공 시 분석 결과 딕셔너리, 실패 시 None
    """
    try:
        # 1. S3에서 이미지 다운로드
        s3.download_file(bucket_name, s3_object_key, downloaded_image)
        print(f"✅ S3 이미지 다운로드 성공: {s3_object_key}")

        # 2. 이미지 전처리
        crop_resize_brighten(downloaded_image, resized_image, brightness_factor=1.3)

        # 3. 식물 이름 식별
        raw_plant_name = identify_plant(resized_image)
        plant_name = extract_plant_name(raw_plant_name)
        print(f"✅ 추정된 식물 이름: {plant_name}")

        # 4. 현재 환경 데이터 가져오기
        env = get_latest_environment()
        print("✅ 현재 환경 데이터:", env)

        # 5. GPT로 분석 및 권장 사항 생성
        gpt_response = generate_growth_recommendation(plant_name, env)
        print("✅ GPT 응답 생성 완료")

        # 6. GPT 응답 파싱
        try:
            result_section = gpt_response.split("```json")[0].strip()
            json_str = gpt_response.split("```json")[1].split("```")[0]
            controls_json = json.loads(json_str, object_pairs_hook=OrderedDict)
        except (IndexError, json.JSONDecodeError) as e:
            print(f"⚠️ GPT 응답 파싱 오류: {e}. 응답 전체를 저장합니다.")
            result_section = gpt_response
            controls_json = {}

        # 7. S3 이미지 URL 생성 및 DB에 결과 저장
        image_url = f"https://{bucket_name}[.s3.amazonaws.com/](https://.s3.amazonaws.com/){s3_object_key}" # 실제 접근 가능한 URL 형식으로 변경
        insert_into_ai_diagnosis(plant_name, result_section, controls_json, image_url)
        print("✅ DB 저장 완료")
        
        # 8. 임시 이미지 파일 삭제
        if os.path.exists(downloaded_image):
            os.remove(downloaded_image)
        if os.path.exists(resized_image):
            os.remove(resized_image)

        # 9. 성공 시 결과 반환
        return {
            "plant_name": plant_name,
            "result": result_section,
            "controls": controls_json,
            "image_url": image_url
        }

    except Exception as e:
        print(f"❌ 전체 프로세스 중 오류 발생: {e}")
        # 실패 시 임시 파일 정리
        if os.path.exists(downloaded_image):
            os.remove(downloaded_image)
        if os.path.exists(resized_image):
            os.remove(resized_image)
        return None
