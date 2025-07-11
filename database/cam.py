import cv2
import boto3
import os
from datetime import datetime
from dotenv import load_dotenv

# ====== .env 파일 로드 ======
load_dotenv()

# 환경변수에서 불러오기
username = os.getenv('RTSP_USER')
password = os.getenv('RTSP_PASS')
ip_address = os.getenv('RTSP_IP')

aws_access_key_id = os.getenv('AWS_ACCESS_KEY')
aws_secret_access_key = os.getenv('AWS_SECRET_KEY')
bucket_name = os.getenv('S3_BUCKET')

# RTSP 주소 구성
rtsp_url = f'rtsp://{username}:{password}@{ip_address}:554/stream1'

# ====== RTSP 연결 및 캡처 ======
cap = cv2.VideoCapture(rtsp_url)
ret, frame = cap.read()

if ret:
    filename = f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(filename, frame)
    print(f"이미지 저장 완료: {filename}")

    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    s3.upload_file(filename, bucket_name, filename)
    print(f"S3 업로드 성공: {bucket_name}/{filename}")

else:
    print("카메라 연결 실패 또는 프레임 캡처 실패")

cap.release()
