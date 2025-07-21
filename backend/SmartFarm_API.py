from flask import Flask, request, Response, jsonify
from datetime import datetime, timezone, timedelta
import pymysql
import json
from flask_cors import CORS

# llm 연동
# import threading
# from llm import plant_analyzer
# diagnosis_delay = 5
# def start_diagnosis():
#     print('start ai diagnosis')
#     plant_analyzer.run_plant_diagnosis()
#     return

def get_connection():
    return pymysql.connect(
        host="database-1.cts2qeeg0ot5.ap-northeast-2.rds.amazonaws.com",
        user="kevin",
        db="smartfarm",
        password="spreatics*",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

app = Flask(__name__)
# 프론트엔드 모든 요청 허용
CORS(app)

# 아두이노에서 DB로 센서 값(Status) 보내기
@app.route('/sensor_data', methods=['POST'])
def sensor_data_input():
    data = request.get_json()

    device_id = data['device_id']
    sensor_data = data['sensor_data']

    if((device_id is None) or (sensor_data is None)):
        return jsonify({"result": "failed", "reason": "There are no required fields."})
    
    conn = get_connection()

    for i, j in sensor_data.items():
        with conn.cursor() as cursor:
            sql = """insert into sensor_data(device_id, sensor_type, sensor_value) 
                    values(%s, %s, %s);"""
            cursor.execute(sql, (device_id, i, j))
            conn.commit()

    with conn.cursor() as cursor:
        sql = """select timestamp
                 from sensor_data
                 order by timestamp desc
                 limit 1;"""
        cursor.execute(sql)
        rows = cursor.fetchall()

        return jsonify({"result": "Success", "timestamp": rows[0]['timestamp']})

# 프론트엔드로 Status 값 보내기
@app.route('/sensor_data')
def get_sensor_data():
    conn = get_connection()

    temp_dict = {}
    light_intensity_dict = {}
    humidity_dict = {}
    soil_moisture_dict = {}

    dict_list = [temp_dict, light_intensity_dict, humidity_dict, soil_moisture_dict]
    cnt = 0

    sensor_type = ['temp', 'light_intensity', 'humidity', 'soil_moisture']
    for i in sensor_type:
        with conn.cursor() as cursor:
            sql = """SELECT 
                        DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:00') AS minute,  -- 타임스탬프를 '분' 단위로 자름
                        round(AVG(sensor_value), 2) AS avg_value                          -- 해당 분의 평균값 계산
                    FROM sensor_data
                    WHERE sensor_type = %s                         -- 센서 타입 필터링
                        AND timestamp >= NOW() - INTERVAL 1 HOUR                -- 최근 1시간 데이터만 선택
                    GROUP BY minute                                           -- '분 단위'로 그룹화
                    ORDER BY minute DESC                                      -- 최근 분부터 정렬
                    LIMIT 60;"""
            cursor.execute(sql, (i, ))
            rows = cursor.fetchall()

            for row in rows:
                ts = row["minute"]
                value = row['avg_value']
                dict_list[cnt][ts] = value

            cnt += 1
            
    return jsonify({ "result": "sended", "data": {"temp": dict_list[0],
                                            "light_intensity": dict_list[1],
                                            "humidity": dict_list[2],
                                            "soil_moisture": dict_list[3]}})

# 프론트엔드로 AI 정보 테이블 보내기
@app.route('/ai_diagnosis')
def get_ai_info():
    conn = get_connection()

    with conn.cursor() as cursor:
        sql = """SELECT * 
                 FROM ai_diagnosis
                 ORDER BY timestamp DESC
                 LIMIT 5;"""
        cursor.execute(sql)
        rows = cursor.fetchall()

        # print(rows[0]['diagnosis_id'])

        return jsonify({"status": "Send Success!!", "diagnosis_id": rows[0]['diagnosis_id'], "plant_name": rows[0]['plant_name'], "timestamp": rows[0]['timestamp'], "result": rows[0]['result'], "recommendations": rows[0]['recommendations'], "controls": json.loads(rows[0]['controls']), "image_url": rows[0]['image_url']})

# GET_Setting(아두이노로 환경변수 설정값 보내기)
@app.route('/control_settings')
def arduino_get_settings():
    conn = get_connection()

    with conn.cursor() as cursor:
        sql = """select controls
                 from ai_diagnosis
                 order by diagnosis_id desc
                 limit 1;"""
        cursor.execute(sql)
        rows = cursor.fetchall()

        controls_data = json.loads(rows[0]['controls'])

        # validate json
        keys = ['temp', 'humidity', 'soil_moisture', 'light_intensity', 'light_time']
        for key in keys:
            if key not in controls_data:
                 return jsonify({"result": "failed", "set_temperature": None, "set_humidity": None, "set_light_intensity": None, "set_soil_moisture": None, "set_start_light": None, "set_end_light": None })


        # temp 평균
        temp_low = controls_data['temp']['from']
        temp_high = controls_data['temp']['to']
        temp_avg = (temp_low + temp_high) / 2
        # humidity 평균
        humidity_low = controls_data['humidity']['from']
        humidity_high = controls_data['humidity']['to']
        humidity_avg = (humidity_low + humidity_high) / 2
        # soil_moisture 평균
        soil_moisture_low = controls_data['soil_moisture']['from']
        soil_moisture_high = controls_data['soil_moisture']['to']
        soil_moisture_avg = (soil_moisture_low + soil_moisture_high) / 2
        # light_intensity 평균
        light_intensity_low = controls_data['light_intensity']['from']
        light_intensity_high = controls_data['light_intensity']['to']
        light_intensity_avg = (light_intensity_low + light_intensity_high) / 2

        return jsonify({"result": "sended", "set_temperature": temp_avg, "set_humidity": humidity_avg, "set_light_intensity": light_intensity_avg, "set_soil_moisture": soil_moisture_avg, "set_start_light": controls_data['light_time']['from'], "set_end_light": controls_data['light_time']['to']})

# POST_Setting(프론트엔드에서 환경변수 설정값 설정하기)
# @app.route('/control_settings', methods=['POST'])
# def frontend_post_settings():
#     data = request.get_json()
    
#     global dumi_set_temperature
#     global dumi_set_light_intensity
#     global dumi_set_humidity
#     global dumi_set_soil_moisture
#     global dumi_set_start_light
#     global dumi_set_end_light

#     dumi_set_temperature = data['set_temperature']
#     dumi_set_light_intensity = data['set_light_intensity']
#     dumi_set_humidity = data['set_humidity']
#     dumi_set_soil_moisture = data['set_soil_moisture']
#     dumi_set_start_light = data['set_start_light']
#     dumi_set_end_light = data['set_end_light']

#     if((dumi_set_temperature > 70) or (dumi_set_light_intensity > 99) or (dumi_set_humidity > 99) or (dumi_set_soil_moisture > 1023)):
#         return jsonify({"result": "failed", "reason": "The input value is out of range."})
    
#     return jsonify({"result": "Success", "set_temperature": dumi_set_temperature, "set_intensity": dumi_set_light_intensity, "set_humidity": dumi_set_humidity, "set_soil_moisture": dumi_set_soil_moisture, "set_start_light": dumi_set_start_light, "set_end_light": dumi_set_end_light})

# Flask 서버에서 아두이노로 현재 시간 보내기(조명 제어를 위한)
@app.route('/time')
def get_current_time():

    # 한국 표준시 정의
    korea_standard_time = timezone(timedelta(hours=9))

    # kst = korea standard time. 현재 kst 시간으로 변환
    current_time_kst = datetime.now(timezone.utc).astimezone(korea_standard_time)

    # 전달 가능한 형식으로 변환
    time_string = current_time_kst.isoformat()

    json_str = json.dumps({"result": "sended", "set_time": time_string})

    return Response(json_str, 200,
                    mimetype="application/json",
                    headers={"Content-Length": str(len(json_str))})

# 재배 품종 변경 시, AI 호출하기
# @app.route('/ai_call')
# def call_ai():

#     print(f'ai diagnosis start after {diagnosis_delay}')
#     timer = threading.Timer(diagnosis_delay, start_diagnosis)
#     timer.start()
#     return jsonify({})

app.run(debug=True, host='0.0.0.0', port=5000)
