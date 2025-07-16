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

# ====== .env 로드 ======
load_dotenv()

# ✅ AWS 인증 정보
aws_access_key_id = os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key = os.getenv("AWS_SECRET_KEY")
bucket_name = os.getenv("S3_BUCKET")
object_key = "latest_frame.jpg"
downloaded_image = "downloaded_image.jpg"
resized_image = "resized_image.jpg"

# ✅ DB 연결 정보
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

# ✅ OpenAI 클라이언트 설정
client = OpenAI()  # OPENAI_API_KEY는 .env에 있어야 함

# ✅ 이미지 전처리: 중앙 크롭 → 리사이즈 → 밝기 조절
def crop_resize_brighten(input_path, output_path, size=(512, 512), brightness_factor=1.3):
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
    print(f"✅ 중앙 크롭 → 리사이즈 → 밝기조절 완료: {output_path}")

# ✅ 센서 타입별 최근 60분간 평균 가져오기
def get_latest_avg_by_sensor_60min(sensor_type):
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
    with db.cursor() as cursor:
        cursor.execute(query, (sensor_type,))
        result = cursor.fetchone()
    db.close()
    return result["avg_value"] if result and result["avg_value"] is not None else 0.0

# ✅ 현재 환경 가져오기
def get_latest_environment():
    return {
        "temp": get_latest_avg_by_sensor_60min("temp"),
        "humidity": get_latest_avg_by_sensor_60min("humidity"),
        "light_intensity": get_latest_avg_by_sensor_60min("light_intensity"),
        "soil_moisture": get_latest_avg_by_sensor_60min("soil_moisture")
    }

# ✅ 식물이름 후처리 함수
def extract_plant_name(gpt_response: str) -> str:
    match = re.search(r"(감귤나무|레몬나무|바질|고추|토마토|상추|고수|파슬리|오이|가지|딸기|수박)", gpt_response)
    if match:
        return match.group(1)
    fallback = re.findall(r"([가-힣]+)(나무|모종)", gpt_response)
    if fallback:
        return fallback[-1][0] + fallback[-1][1]
    return gpt_response.strip()

# ✅ Step 1. GPT로 식물이름 추출
def identify_plant(image_path):
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    prompt = """
이 식물은 어떤 식물로 보이니?

- 반드시 식물 이름만 한 줄로 출력해줘
- 예시: 바질, 토마토, 로즈마리, 레몬 나무 묘목
- 설명, 문장 형태 없이 식물 이름만 출력해줘
""".strip()

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
    plant_name = re.sub(r"[^\uAC00-\uD7A3a-zA-Z0-9\s]", "", plant_name_raw).strip()
    return plant_name

# ✅ Step 2. GPT로 재배 환경 분석
def generate_growth_recommendation(plant_name, env):
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
  "temp": {{ "from": x, "to": x }},
  "humidity": {{ "from": x, "to": x }},
  "light_time": {{ "from": x, "to": x }}, 
  "light_intensity": {{ "from": x, "to": x }},
  "soil_moisture": {{ "from": x, "to": x }}
}}
```"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ✅ 결과 저장
def insert_into_ai_diagnosis(plant_name, result, controls_json, image_url):
    db = pymysql.connect(host=db_host, user=db_user, password=db_password,
                         database=db_name, charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)
    with db.cursor() as cursor:
        sql = """
        INSERT INTO ai_diagnosis (plant_name, result, recommendations, controls, image_url)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(sql, (
            plant_name,
            result,
            "",
            json.dumps(controls_json, ensure_ascii=False, sort_keys=False),  # ✅ 순서 유지
            image_url
        ))
        db.commit()
    db.close()

# ✅ 실행부
if __name__ == "__main__":
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        s3.download_file(bucket_name, object_key, downloaded_image)
        print(f"✅ 이미지 다운로드 성공: {downloaded_image}")
    except Exception as e:
        print(f"❌ 이미지 다운로드 실패: {e}")
        exit()

    crop_resize_brighten(downloaded_image, resized_image, brightness_factor=1.3)

    raw_plant_name = identify_plant(resized_image)
    plant_name = extract_plant_name(raw_plant_name)
    print(f"✅ 추정된 식물이름: {plant_name}")

    env = get_latest_environment()
    print("✅ 현재 환경 데이터:", env)

    gpt_response = generate_growth_recommendation(plant_name, env)
    print("✅ GPT 권장 재배 환경 응답:\n", gpt_response)

    try:
        json_str = gpt_response.split("```json")[1].split("```")[0]
        controls_json = json.loads(json_str, object_pairs_hook=OrderedDict)  # ✅ 순서 유지
    except Exception as e:
        print("⚠️ JSON 파싱 오류:", e)
        controls_json = {}

    result_section = gpt_response.split("```json")[0].strip()

    insert_into_ai_diagnosis(
        plant_name,
        result_section,
        controls_json,
        f"(private s3) {object_key}"
    )
    print("✅ DB 저장 완료")
