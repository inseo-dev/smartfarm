# import os
# import time
# import cv2
# import boto3
# import pymysql
# import logging
# import openai
# import random
# from datetime import datetime
# from dotenv import load_dotenv

# # ====== 설정 ======
# load_dotenv()
# logging.basicConfig(filename="smartfarm.log", level=logging.INFO,
#                     format="%(asctime)s - %(levelname)s - %(message)s")

# # ====== 환경 변수 ======
# RTSP_USER = os.getenv("RTSP_USER")
# RTSP_PASS = os.getenv("RTSP_PASS")
# RTSP_IP = os.getenv("RTSP_IP")
# rtsp_url = f'rtsp://{RTSP_USER}:{RTSP_PASS}@{RTSP_IP}:554/stream1'

# AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
# AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
# S3_BUCKET = os.getenv("S3_BUCKET")

# DB_HOST = os.getenv("DB_HOST")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_NAME = os.getenv("DB_NAME")

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = OPENAI_API_KEY

# # ====== S3 연결 ======
# s3 = boto3.client(
#     's3',
#     aws_access_key_id=AWS_ACCESS_KEY,
#     aws_secret_access_key=AWS_SECRET_KEY
# )

# # ====== 센서 데이터 시뮬레이션 ======


# def insert_sensor_data():
#     conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
#                            database=DB_NAME, charset='utf8mb4')
#     with conn.cursor() as cursor:
#         values = [
#             (1, 'temp', round(random.uniform(22, 30), 1)),
#             (1, 'humidity', round(random.uniform(40, 70), 1)),
#             (2, 'soil', round(random.uniform(20, 50), 1)),
#             (2, 'light', round(random.uniform(8000, 15000), 1))
#         ]
#         for device_id, sensor_type, sensor_value in values:
#             cursor.execute("""
#                 INSERT INTO sensor_data (device_id, sensor_type, sensor_value)
#                 VALUES (%s, %s, %s)
#             """, (device_id, sensor_type, sensor_value))
#     conn.commit()
#     conn.close()
#     logging.info("센서 데이터 저장 완료")


# # ====== 최신 센서값 조회 ======
# def get_latest_sensor_data():
#     conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
#                            database=DB_NAME, charset='utf8mb4')
#     with conn.cursor() as cursor:
#         cursor.execute("""
#             SELECT sensor_type, sensor_value
#             FROM (
#                 SELECT *, ROW_NUMBER() OVER (PARTITION BY sensor_type ORDER BY timestamp DESC) AS rn
#                 FROM sensor_data
#             ) AS ranked
#             WHERE rn = 1
#         """)
#         rows = cursor.fetchall()
#     conn.close()
#     return {row[0]: row[1] for row in rows}


# # ====== OpenAI API 호출 ======
# def analyze_with_openai(sensor_dict, image_url):
#     prompt = f"""
#     스마트팜 센서 데이터:\n{sensor_dict}
#     이미지 주소: {image_url}

#     작물 상태를 분석하고 아래 JSON 형식으로 제어 명령을 생성하세요:
#     {{
#         "heater": true/false,
#         "fan": true/false,
#         "watering": true/false,
#         "light_hours": 숫자
#     }}
#     """

#     response = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     result = response.choices[0].message.content.strip()
#     logging.info("OpenAI 분석 완료")
#     return result


# # ====== 이미지 캡처 + S3 업로드 ======
# def capture_and_upload():
#     cap = cv2.VideoCapture(rtsp_url)
#     time.sleep(1)
#     ret, frame = cap.read()
#     cap.release()

#     if not ret:
#         raise Exception("카메라 캡처 실패")

#     filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
#     cv2.imwrite(filename, frame)
#     s3.upload_file(filename, S3_BUCKET, filename)
#     os.remove(filename)
#     url = f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"
#     logging.info(f"이미지 S3 업로드 완료: {url}")
#     return url


# # ====== DB에 ai_diagnosis 저장 ======
# def save_ai_result(image_url, controls_json):
#     conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
#                            database=DB_NAME, charset='utf8mb4')
#     with conn.cursor() as cursor:
#         sql = """
#             INSERT INTO ai_diagnosis (timestamp, result, recommendations, controls, image_url)
#             VALUES (NOW(), '', '', %s, %s)
#         """
#         cursor.execute(sql, (controls_json, image_url))
#     conn.commit()
#     conn.close()
#     logging.info("AI 진단 결과 저장 완료")


# # ====== 메인 루프 ======
# def run():
#     while True:
#         try:
#             logging.info("=== 자동 실행 시작 ===")
#             insert_sensor_data()
#             sensor = get_latest_sensor_data()
#             image_url = capture_and_upload()
#             controls = analyze_with_openai(sensor, image_url)
#             save_ai_result(image_url, controls)
#             logging.info("✅ 전체 작업 완료\n")

#         except Exception as e:
#             logging.error(f"오류 발생: {e}")

#         time.sleep(600)  # 10분 대기


# if __name__ == "__main__":
#     run()


# import os
# import time
# import cv2
# import boto3
# import pymysql
# import logging
# import random
# from datetime import datetime
# from dotenv import load_dotenv

# # ====== 설정 ======
# load_dotenv()
# logging.basicConfig(filename="smartfarm.log", level=logging.INFO,
#                     format="%(asctime)s - %(levelname)s - %(message)s")

# # ====== 환경 변수 ======
# RTSP_USER = os.getenv("RTSP_USER")
# RTSP_PASS = os.getenv("RTSP_PASS")
# RTSP_IP = os.getenv("RTSP_IP")
# rtsp_url = f'rtsp://{RTSP_USER}:{RTSP_PASS}@{RTSP_IP}:554/stream1'

# AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
# AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
# S3_BUCKET = os.getenv("S3_BUCKET")

# DB_HOST = os.getenv("DB_HOST")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_NAME = os.getenv("DB_NAME")

# # ====== S3 연결 ======
# s3 = boto3.client(
#     's3',
#     aws_access_key_id=AWS_ACCESS_KEY,
#     aws_secret_access_key=AWS_SECRET_KEY
# )

# # ====== 센서 데이터 시뮬레이션 ======


# def insert_sensor_data():
#     conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
#                            database=DB_NAME, charset='utf8mb4')
#     with conn.cursor() as cursor:
#         values = [
#             (1, 'temp', round(random.uniform(22, 30), 1)),
#             (1, 'humidity', round(random.uniform(40, 70), 1)),
#             (2, 'soil', round(random.uniform(20, 50), 1)),
#             (2, 'light', round(random.uniform(8000, 15000), 1))
#         ]
#         for device_id, sensor_type, sensor_value in values:
#             cursor.execute("""
#                 INSERT INTO sensor_data (device_id, sensor_type, sensor_value)
#                 VALUES (%s, %s, %s)
#             """, (device_id, sensor_type, sensor_value))
#     conn.commit()
#     conn.close()
#     logging.info("센서 데이터 저장 완료")

# # ====== 이미지 캡처 + S3 업로드 ======


# def capture_and_upload():
#     print("카메라 연결 시도 중...")
#     cap = cv2.VideoCapture(rtsp_url)
#     time.sleep(1)
#     print("프레임 읽기 시도 중...")
#     ret, frame = cap.read()
#     print("프레임 읽기 결과:", ret)
#     cap.release()

#     if not ret:
#         raise Exception("카메라 캡처 실패")

#     filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
#     logging.info(f"이미지 저장 중: {filename}")
#     cv2.imwrite(filename, frame)

#     logging.info("S3 업로드 중...")
#     s3.upload_file(filename, S3_BUCKET, filename)

#     logging.info("로컬 파일 삭제")
#     os.remove(filename)

#     url = f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"
#     logging.info(f"이미지 S3 업로드 완료: {url}")
#     return url

# # ====== DB에 ai_diagnosis 저장 (OpenAI 없이) ======


# def save_image_only(image_url):
#     conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
#                            database=DB_NAME, charset='utf8mb4')
#     with conn.cursor() as cursor:
#         sql = """
#             INSERT INTO ai_diagnosis (timestamp, result, recommendations, controls, image_url)
#             VALUES (NOW(), '', '', '{}', %s)
#         """
#         cursor.execute(sql, (image_url,))
#     conn.commit()
#     conn.close()
#     logging.info("이미지 URL만 DB에 저장 완료")

# # ====== 메인 루프 ======


# def run():
#     while True:
#         try:
#             print("실행 시작됨")
#             logging.info("=== 자동 실행 시작 ===")
#             insert_sensor_data()
#             image_url = capture_and_upload()
#             save_image_only(image_url)
#             logging.info("전체 작업 완료 (OpenAI 없이)\n")

#         except Exception as e:
#             logging.error(f"오류 발생: {e}", exc_info=True)

#         time.sleep(60)  # 1분 대기


# if __name__ == "__main__":
#     print("스마트팜 자동 실행 시작")
#     run()


import cv2
import boto3
import os
import time
import pymysql
from datetime import datetime
from dotenv import load_dotenv

# ====== .env 파일 로드 ======
load_dotenv()

# 환경 변수
username = os.getenv('RTSP_USER')
password = os.getenv('RTSP_PASS')
ip_address = os.getenv('RTSP_IP')
aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
aws_secret_access_key = os.getenv('AWS_SECRET_KEY')
bucket_name = os.getenv('S3_BUCKET')

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# RTSP 주소
rtsp_url = f'rtsp://{username}:{password}@{ip_address}:554/stream1'

# S3 클라이언트
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

print("시작: 이미지 촬영 → S3 업로드 → DB 저장")

while True:
    cap = cv2.VideoCapture(rtsp_url)
    ret, frame = cap.read()

    if ret:
        filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(filename, frame)
        print(f"이미지 저장 완료: {filename}")

        try:
            # S3 업로드
            s3.upload_file(filename, bucket_name, filename)
            image_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
            print(f"S3 업로드 성공: {image_url}")

            # DB 연결 및 저장
            conn = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                charset='utf8mb4'
            )
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO ai_diagnosis (timestamp, result, recommendations, controls, image_url)
                VALUES (NOW(), '', '', '{}', %s)
                """
                cursor.execute(sql, (image_url,))
                conn.commit()
                print("DB에 이미지 URL 저장 완료")

            conn.close()
        except Exception as e:
            print(f"오류 발생: {e}")

        # 파일 정리 (옵션)
        # os.remove(filename)

    else:
        print("카메라 연결 실패 또는 프레임 캡처 실패")

    cap.release()
    time.sleep(10)
