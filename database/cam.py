# import cv2
# import boto3
# import os
# from datetime import datetime
# from dotenv import load_dotenv

# # ====== .env 파일 로드 ======
# load_dotenv()

# # 환경변수에서 불러오기
# username = os.getenv('RTSP_USER')
# password = os.getenv('RTSP_PASS')
# ip_address = os.getenv('RTSP_IP')

# aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
# aws_secret_access_key = os.getenv('AWS_SECRET_KEY')
# bucket_name = os.getenv('S3_BUCKET')

# # RTSP 주소 구성
# rtsp_url = f'rtsp://{username}:{password}@{ip_address}:554/stream1'

# # ====== RTSP 연결 및 캡처 ======
# cap = cv2.VideoCapture(rtsp_url)
# ret, frame = cap.read()

# if ret:
#     filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
#     cv2.imwrite(filename, frame)
#     print(f"이미지 저장 완료: {filename}")

#     s3 = boto3.client(
#         's3',
#         aws_access_key_id=aws_access_key_id,
#         aws_secret_access_key=aws_secret_access_key
#     )

#     s3.upload_file(filename, bucket_name, filename)
#     print(f"S3 업로드 성공: {bucket_name}/{filename}")

# else:
#     print("카메라 연결 실패 또는 프레임 캡처 실패")

# cap.release()

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

print("📸 시작: 이미지 촬영 → S3 업로드 → DB 저장")

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
