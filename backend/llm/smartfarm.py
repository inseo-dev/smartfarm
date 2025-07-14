import base64
import requests
import pymysql
import json
from PIL import Image
from io import BytesIO
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ✅ 공통: 센서 타입별 최근 1분 평균 가져오기
def get_latest_avg_by_sensor(sensor_type):
    db = pymysql.connect(
        host='database-1.cts2qeeg0ot5.ap-northeast-2.rds.amazonaws.com',
        user='kevin',
        password='spreatics*',
        database='smartfarm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    with db.cursor() as cursor:
        sql = """
            SELECT 
              AVG(sensor_value) AS avg_value
            FROM sensor_data
            WHERE sensor_type = %s
              AND timestamp >= NOW() - INTERVAL 1 MINUTE;
        """
        cursor.execute(sql, (sensor_type,))
        result = cursor.fetchone()
    db.close()
    return result["avg_value"] if result and result["avg_value"] is not None else 0.0


# ✅ 현재 환경 가져오기
def get_latest_environment():
    return {
        "temperature": get_latest_avg_by_sensor("temp"),
        "humidity": get_latest_avg_by_sensor("humidity"),
        "light_intensity": get_latest_avg_by_sensor("light_intensity"),
        "soil_moisture": get_latest_avg_by_sensor("soil_moisture")
    }


# ✅ 프롬프트 생성
def create_prompt_dynamic(env):
    return f"""
너는 스마트팜을 관리하는 식물학 전문가 AI이다.

첨부된 이미지와 아래 환경 데이터를 기반으로 재배 환경을 분석하라:
이미지는 현재 식물 사진이고, 생장 단계도 고려해서 재배 환경 결과를 알려줘

현재 환경:
- 온도: {env['temperature']}°C
- 습도: {env['humidity']}%
- 조도: {env['light']} lux
- 토양 습도: {env['soil_moisture']}%

아래 형식에 맞춰 결과를 출력하라:

1. 식물이름  
- 식물 이름을 한글로 한 줄 출력

2. 식물 정보 및 권장 재배 환경 요약  
   - 생장 단계 (한국어 단계명 + 영어 단계명 + 설명 bullet point)
   - 발육 상태 (색상, 형태, 병충해, 결구 진행 상태)
   - 권장 재배 환경 요약

3. 권장 재배 환경 (JSON 형식)  
- 아래 형식으로 JSON만 출력  
- 각 항목의 값은 float형 숫자를 가진 "from", "to" 딕셔너리여야 한다

```json
{{
  "온도": {{ "from": 20.0, "to": 25.0 }},
  "습도": {{ "from": 50.0, "to": 70.0 }},
  "일조 시간": {{ "from": 10.0, "to": 14.0 }},
  "조도": {{ "from": 6000.0, "to": 9000.0 }},
  "토양 습도": {{ "from": 30.0, "to": 50.0 }}
}}

식물 정보 및 권장 재배 환경 요약은 일반 설명 형태로 요약,
그 다음에 재배 환경 요약은 JSON 형식으로 5가지 속성을 키로 넣어서 반환
""".strip()


# ✅ 이미지 다운로드 및 리사이즈
def download_and_resize_image(image_url, output_path, size=(256, 256)):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img_resized = img.resize(size)
        img_resized.save(output_path)
    except Exception as e:
        print(f"❌ 이미지 다운로드 또는 저장 실패: {e}")


# ✅ GPT-4o 분석
def analyze_plant_image(image_path, prompt_text):
    model = ChatOpenAI(model="gpt-4o")
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    )
    return model.invoke([message]).content


# ✅ 분석 결과 DB에 저장
def insert_into_ai_diagnosis(plant_name, result, recommendations, controls_json, image_url):
    db = pymysql.connect(
        host='database-1.cts2qeeg0ot5.ap-northeast-2.rds.amazonaws.com',
        user='kevin',
        password='spreatics*',
        database='smartfarm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    with db.cursor() as cursor:
        sql = """
        INSERT INTO ai_diagnosis (plant_name, result, recommendations, controls, image_url)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(sql, (
            plant_name,
            result,
            recommendations,
            json.dumps(controls_json, ensure_ascii=False),
            image_url
        ))
        db.commit()
    db.close()


# ✅ 실행부
if __name__ == "__main__":
    image_url = "https://re2-smartfarm.s3.amazonaws.com/latest_frame.jpg"
    resized_image = "resized_image.jpg"

    # 1. 실시간 환경 정보 가져오기
    env = get_latest_environment()

    # 2. 프롬프트 생성
    prompt = create_prompt_dynamic(env)

    # 3. 이미지 다운로드 및 리사이즈
    download_and_resize_image(image_url, resized_image)

    # 4. GPT 분석
    gpt_response = analyze_plant_image(resized_image, prompt)
    print("✅ GPT 응답:\n", gpt_response)

    # 5. 결과 파싱
    lines = gpt_response.strip().split("\n")
    plant_name = lines[0].strip()  # 1줄 요약 식물이름

    # JSON 추출
    try:
        json_str = gpt_response.split("```json")[1].split("```")[0]
        controls_json = json.loads(json_str)
    except Exception as e:
        print("⚠️ JSON 파싱 오류:", e)
        print("⚠️ 응답 내용:\n", gpt_response)
        controls_json = {}

    # 설명 전체 (식물이름 제외 + JSON 제외 부분)
    result_section = gpt_response.split("```json")[0]
    result = "\n".join(result_section.split("\n")[1:]).strip()

    # recommendations는 빈 문자열로 처리
    recommendations = ""

    # 6. DB 저장
    insert_into_ai_diagnosis(plant_name, result, recommendations, controls_json, image_url)

    print("✅ DB 저장 완료!")
