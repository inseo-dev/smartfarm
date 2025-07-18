import cv2
import boto3
import os
import time
import pymysql
from datetime import datetime
from dotenv import load_dotenv

# ====== .env 파일 로드 ======
load_dotenv()

# 환경 변수 로드
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

# RTSP URL 생성
rtsp_url = f'rtsp://{username}:{password}@{ip_address}:554/stream1'

# 디버깅 출력
print(f"[디버깅] RTSP URL: {rtsp_url}")
print("[DEBUG] username:", username)
print("[DEBUG] ip_address:", ip_address)
print("[DEBUG] S3 bucket:", bucket_name)
print("[DEBUG] DB Host:", db_host)

# S3 클라이언트 초기화
s3 = boto3.client(
    's3',
    region_name='ap-northeast-2',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

print("시작: 이미지 촬영 → S3 업로드 → DB 저장")

# 반복 실행
while True:
    frame = None
    ret = False

    # 최대 12번까지 프레임 캡처 시도
    for attempt in range(12):
        cap = cv2.VideoCapture(rtsp_url)
        time.sleep(1)  # 연결 직후 잠시 대기
        ret, frame = cap.read()
        cap.release()

        if ret and frame is not None:
            print(f"[성공] {attempt+1}번째 시도에서 프레임 캡처 성공")
            break
        else:
            print(f"[{attempt+1}번째 시도] 프레임 캡처 실패 → 10초 후 재시도")
            time.sleep(10)

    if ret and frame is not None:
        print("프레임 캡처 성공:", frame.shape)

        filename = "latest_frame.jpg"
        cv2.imwrite(filename, frame)
        print(f"이미지 저장 완료: {filename}")

        try:
            # S3 업로드
            s3.upload_file(
                filename,
                bucket_name,
                filename,
                ExtraArgs={
                    'CacheControl': 'no-cache, no-store, must-revalidate'
                }
            )
            image_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': filename},
                ExpiresIn=3600 * 24
            )
            print(f"S3 업로드 성공: {image_url}")

        except Exception as e:
            print(f"[오류] S3 업로드 또는 DB 저장 실패: {e}")

        # 원한다면 파일 삭제
        # os.remove(filename)

    else:
        print("[실패] 모든 시도에서 프레임 캡처 실패. 다음 주기까지 대기")

    time.sleep(10)  # 다음 촬영까지 대기
