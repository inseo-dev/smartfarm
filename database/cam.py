# import cv2
# import boto3
# import datetime
# import time
# import os

# # AWS 설정
# AWS_ACCESS_KEY = "사용자 id"
# AWS_SECRET_KEY = "비밀번호"
# S3_BUCKET = "s3저장소이름"

# # 카메라 주소 (RTSP)
# RTSP_URL = "rtsp://admin:123456@192.168.1.100:554/h264Preview_01_main"

# # AWS 연결
# s3 = boto3.client('s3',
#                   aws_access_key_id=AWS_ACCESS_KEY,
#                   aws_secret_access_key=AWS_SECRET_KEY
#                   )

# # 캡처 함수


# def capture_and_upload():
#     cap = cv2.VideoCapture(RTSP_URL)
#     ret, frame = cap.read()
#     if ret:
#         now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         filename = f"{plant_id}image_{now}.jpg"
#         cv2.imwrite(filename, frame)
#         print(f"{filename} 저장 완료")

#         # S3 업로드
#         s3.upload_file(filename, S3_BUCKET, f"reolink/{filename}")
#         print(f"{filename} → S3 업로드 완료")

#         os.remove(filename)
#     else:
#         print("카메라 캡처 실패")
#     cap.release()


# # 10분마다 실행
# while True:
#     capture_and_upload()
#     time.sleep(600)  # 600초 = 10분


import cv2

# === 사용자 정보 입력 ===
username = 'spreatics'           # 설정한 사용자명
password = 'smartfarm'       # 설정한 비밀번호
ip_address = '192.168.1.184'     # 카메라 IP (정적 IP로 설정한 값)

# === RTSP 스트림 URL 구성 ===
rtsp_url = f'rtsp://{username}:{password}@{ip_address}:554/stream1'

# === 카메라 연결 ===
cap = cv2.VideoCapture(rtsp_url)

# === 연결 확인 및 프레임 캡처 ===
ret, frame = cap.read()

if ret:
    cv2.imwrite('snapshot.jpg', frame)
    print('✅ 프레임 캡처 성공! → snapshot.jpg 로 저장됨')
else:
    print('❌ 스트림 연결 실패 또는 프레임 수신 실패')

cap.release()
