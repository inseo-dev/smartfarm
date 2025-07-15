from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta
import pymysql

app = Flask(__name__)

def get_connection():
    return pymysql.connect(
        host='database-1.cts2qeeg0ot5.ap-northeast-2.rds.amazonaws.com',
        user='kevin',
        password='spreatics*',
        db='smartfarm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 🌡 제어 기준값 (프론트에서 설정하거나 기본 제공)
set_temperature = 24.00
set_light_intensity = 72.00
set_humidity = 55.00
set_soil_moisture = 123.00
set_start_light = "2025-07-10T07:00:00+09:00"
set_end_light = "2025-07-10T19:00:00+09:00"

# 1. 아두이노에서 센서 값 POST → DB 저장
@app.route('/sensor_data', methods=['POST'])
def post_sensor_data():
    data = request.get_json()

    device_id = data.get('device_id', 0)
    sensor_type = data.get('sensor_type')
    sensor_value = data.get('sensor_value')
    timestamp = data.get('timestamp')

    if not sensor_type or sensor_value is None:
        return jsonify({"result": "failed", "reason": "Missing required fields"}), 400

    # timestamp 기본값: 현재 시각 (KST)
    if not timestamp:
        timestamp = datetime.now(timezone(timedelta(hours=9))).isoformat()

    # ✅ DB 저장
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO sensor_data (device_id, timestamp, sensor_type, sensor_value)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (device_id, timestamp, sensor_type, sensor_value))
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"result": "failed", "reason": f"DB Error: {e}"}), 500

    return jsonify({
        "result": "Success",
        "device_id": device_id,
        "sensor_type": sensor_type,
        "timestamp": timestamp,
        "sensor_value": sensor_value
    })

# 2. 아두이노에서 설정값 GET
@app.route('/control_settings', methods=['GET'])
def arduino_get_settings():
    return jsonify({
        "result": "sended",
        "set_temperature": set_temperature,
        "set_light_intensity": set_light_intensity,
        "set_humidity": set_humidity,
        "set_soil_moisture": set_soil_moisture,
        "set_start_light": set_start_light,
        "set_end_light": set_end_light
    })

# 3. AI 호출 dummy (미정의 방지용)
@app.route('/ai_call', methods=['POST'])
def call_ai():
    return jsonify({
        "result": "called",
        "predict": "AI 호출 테스트 - 실제 모델 연동 필요"
    })

# 4. 서버 실행
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
