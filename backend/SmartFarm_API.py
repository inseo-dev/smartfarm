from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta
import pymysql
from flask_cors import CORS

# 가정 AI 라이브러리 파일
# from ai_model_lib import AIModel

# AI 모델 로딩
# try:
#     ai_instance = AIModel()
# except Exception as e:
#     print(f"AI 모델 로딩 실패: {e}")
#     ai_instance = None

# def get_connection():
#     return pymysql.connect(
#         host=
#         user=
#         password=
#         db=
#         charset='utf8mb4',
#         cursorclass=pymysql.cursors.DictCursor
#     )

# get settings용 변수
set_temperature = 24.00
set_light_intensity = 72.00
set_humidity = 55.00
set_soil_moisture = 123.00
set_start_light = "2025-07-10T13:30:00+09:00"
set_end_light = "2025-07-10T18:30:00+09:00"

# 아두이노 -> DB POST 용 변수
dumi_device_id = 128
dumi_timestamp = "24시간"
dumi_sensor_type = "ice"
dumi_sensor_value = 752.00

# 프론트엔드 -> DB POST 용 변수
dumi_set_temperature = 350
dumi_set_light_intensity = 270
dumi_set_humidity = 485.00
dumi_set_soil_moisture = 27.08
dumi_set_start_light = "dayday"
dumi_set_end_light = "daybyday "

app = Flask(__name__)
# 프론트엔드 모든 요청 허용
CORS(app)

# 아두이노에서 DB로 센서 값(Status) 보내기
@app.route('/sensor_data', methods=['POST'])
def sensor_data_input():
    data = request.get_json()

    global dumi_device_id
    global dumi_timestamp
    global dumi_sensor_type
    global dumi_sensor_value

    dumi_device_id = data['device_id']
    dumi_timestamp = data['timestamp']
    dumi_sensor_type = data['sensor_type']
    dumi_sensor_value = data['sensor_value']

    if((dumi_device_id is None) or (dumi_timestamp is None) or (dumi_sensor_type is None)):
        return jsonify({"result": "failed", "reason": "There are no required fields."})
    
    return jsonify({"result": "Success", "device_id": dumi_device_id, "timestamp": dumi_timestamp, "sensor_type": dumi_sensor_type, "sensor_value": dumi_sensor_value})

# 프론트엔드로 Status 값 보내기
@app.route('/sensor_data')
def get_sensor_data():
    return jsonify({"result": "sended", "device_id": dumi_device_id, "timestamp": dumi_timestamp, "sensor_type": dumi_sensor_type, "sensor_value": dumi_sensor_value})

# GET_Setting(아두이노로 환경변수 설정값 보내기)
@app.route('/control_settings')
def arduino_get_settings():
    return jsonify({"result": "sended", "set_temperature": set_temperature, "set_light_intensity": set_light_intensity, "set_humidity": set_humidity, "set_soil_moisture": set_soil_moisture, "set_start_light": set_start_light, "set_end_light": set_end_light})

# POST_Setting(프론트엔드에서 환경변수 설정값 설정하기)
@app.route('/control_settings', methods=['POST'])
def frontend_post_settings():
    data = request.get_json()
    
    global dumi_set_temperature
    global dumi_set_light_intensity
    global dumi_set_humidity
    global dumi_set_soil_moisture
    global dumi_set_start_light
    global dumi_set_end_light

    dumi_set_temperature = data['set_temperature']
    dumi_set_light_intensity = data['set_light_intensity']
    dumi_set_humidity = data['set_humidity']
    dumi_set_soil_moisture = data['set_soil_moisture']
    dumi_set_start_light = data['set_start_light']
    dumi_set_end_light = data['set_end_light']

    if((dumi_set_temperature > 70) or (dumi_set_light_intensity > 99) or (dumi_set_humidity > 99) or (dumi_set_soil_moisture > 1023)):
        return jsonify({"result": "failed", "reason": "The input value is out of range."})
    
    return jsonify({"result": "Success", "set_temperature": dumi_set_temperature, "set_intensity": dumi_set_light_intensity, "set_humidity": dumi_set_humidity, "set_soil_moisture": dumi_set_soil_moisture, "set_start_light": dumi_set_start_light, "set_end_light": dumi_set_end_light})

# Flask 서버에서 아두이노로 현재 시간 보내기(조명 제어를 위한)
@app.route('/time')
def get_current_time():

    # 한국 표준시 정의
    korea_standard_time = timezone(timedelta(hours=9))

    # kst = korea standard time. 현재 kst 시간으로 변환
    current_time_kst = datetime.now(timezone.utc).astimezone(korea_standard_time)

    # 전달 가능한 형식으로 변환
    time_string = current_time_kst.isoformat()

    return jsonify({"result": "sended", "set_time": time_string})

# 재배 품종 변경 시, AI 호출하기
# @app.route('/ai_call')
# def call_ai():
#     if ai_instance is None:
#         return jsonify({"return": "failed", "reason": "AI model not loaded"})

#     return jsonify({"result": "called", "predict": ai_instance})

app.run(debug=True, host='0.0.0.0', port=5000)
