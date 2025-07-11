# REST API Spec

## Status
- 아두이노에서 DB로 센서 값(Status) 보내기
    1. Endpoint
        - POST/sensor_data
    2. Request body
        - 이전 버전
            - temperature (float, optional) : 스마트팜 실내 온도
            - light_intensity (float, optional) : 스마트팜 실내 조도
            - humidity (float, optional) : 스마트팜 실내 공기 중 습도
            - soil_moisture (float, optional) : 스마트팜 토양 습도
                
                ```json
                { 
                	"temperature": 24.0,
                	"light_intensity": 240.0,
                	"humidity": 55.00,
                	"soil_moisture": 72.00
                }
                ```
                
        - device_id (int) : 아두이노 장치 id, 필수
        - timestamp (string) : 센서 데이터 수집 시간, 필수
        - sensor_type (string) : 센서 종류, 필수
        - sensor_value (float, optional) : 측정된 센서 값
            
            ```json
            {
            	"device_id": 1,
            	"timestamp": "2025-07-09 10:00:00",
            	"sensor_type": "temp",
            	"sensor_value": 23.1
            }
            ```
            
    3. Description
        - 아두이노A, B가 센서로 온도, 조도, 습도, 토양 습도 값을 읽어서 DB로 보낸다.
        - 아두이노 디바이스에 번호를 부여하여 각 디바이스 별 센서를 통해 값을 읽어오고, timestamp를 기록한다
        - 추후 데이터 사용 시, timestamp를 활용해 일정 시간 단위로 묶어 데이터를 사용한다.
        - 필수 데이터 값들이 들어오지 않으면, 에러를 발생한다.
    4. Response body
        - result (string) : Success, failed
        - device_id (int) : 입력 성공 시, 아두이노 장치 id
        - timestamp (string) : 입력 성공 시, 센서 데이터 수집 시간
        - sensor_type (string) : 입력 성공 시, 센서 종류
        - sensor_value (float, optional) : 입력 성공 시, 측정된 센서 값
        - reason (string) : 입력 실패 시, 실패 원인
        
        ```json
        {
        	"result": "Success",
        	"device_id": 1,
        	"timestamp": "2025-07-09 10:00:00",
        	"sensor_type": "temp",
        	"sensor_value": 23.1
        }
        {
        	"result": "failed",
        	"reason": "There are no required fields."
        }
        ```
        

## Setting(Controller)

- GET_Setting(아두이노로 환경변수 설정값 보내기)
    1. Endpoint
        - GET/control_settings
    2. Request body
        - 없음
    3. Description
        - 아두이노로 설정 스마트팜 온도, 조도, 습도, 토양 습도와 설정값을 보내는 현재시간을 보낸다.
    4. Response body
        - result (string) : sended
        - set_temperature (float) : 설정 내부 온도
        - set_light_intensity (float) : 설정 내부 조도
        - set_humidity (float) : 설정 내부 습도
        - set_soil_moisture (float) : 설정 토양 습도
        - set_start_light (string) : 설정 전구 작동 시작 시간
        - set_end_light (string) : 설정 전구 작동 종료 시간
        
        ```json
        {
        	"result": "sended",
        	"set_temperature": 24.00,
        	"set_light_intensity": 72.00,
        	"set_humidity": 55.00,
        	"set_soil_moisture": 74.00,
        	"set_start_light": "2025-07-10T13:30:00+09:00",
        	"set_end_light": "2025-07-10T18:30:00+09:00"
        }
        ```
        
- POST_Setting(프론트엔드에서 환경변수 설정값 설정하기)
    1. Endpoint
        - POST/control_settings
    2. Request body
        - set_temperature (float, optional) : 설정 내부 온도
        - set_light_intensity (float, optional) : 설정 내부 조도
        - set_humidity (float, optional) : 설정 내부 습도
        - set_soil_moisture (float, optional) : 설정 토양 습도
        - set_start_light (string, optional) : 설정 전구 작동 시작 시간
        - set_end_light (string, optional) : 설정 전구 작동 종료 시간
            
            ```json
            {
            	"set_temperature": 18.00,
            	"set_light_intensity": 57.00,
            	"set_humidity": 77.00,
            	"set_soil_moisture": 128.00,
            	"set_start_light": "2025-07-10T10:30:00+09:00",
            	"set_end_light": "2025-07-10T19:30:00+09:00"
            }
            ```
            
    3. Description
        - 사용자가 스마트팜 내부 환경 변수를 조정할 때 사용되는 API
        - 사용자가 온도, 조도, 습도, 토양습도, 전구 작동 시간을 세팅하면 API를 통해 새롭게 DB에 입력하고, 그 입력에 알맞게 아두이노를 작동시킨다.
        - 세팅한 입력값이 아두이노 센서 아날로그 값 범위를 넘어가면 에러를 발생한다.
    4. Response body
        - result (string) : Success, failed
        - Success_time (string) : 입력 성공 시, 입력 성공 시간
        - reason (string) : 실패 원인
            
            ```json
            {
            	"result": "Success",
            	"Success_time": "2025-07-10T11:30:00+09:00"
            }
            {
            	"result": "failed",
            	"reason": "The input value is out of range."
            }
            ```
            

## Time

- Flask 서버에서 아두이노로 현재 시간 보내기(조명 제어를 위한)
    1. Endpoint
        - GET/time
    2. Request body
        - 없음
    3. Description
        - 아두이노 작동 시간 계산을 위한, 초기 세팅에 필요한 현재 시간을 보낸다.
    4. Responsebody
        - result (string) : sended
        - set_time (string) : 아두이노 초기 기준 세팅 시간
        
        ```json
        {
        	"result": "sended",
        	"set_time": "2025-07-10T13:15:42.123456+09:00"
        }
        ```
        

## AI CALL

- 재배 품종 변경 시, AI 호출하기
    1. Endpoint
        - GET/ai_call
    2. Request body
        - 없음
    3. Description
        - 재배 품종 변경 시, 이미지를 통해 변경 품종을 확인하기 위한 AI를 호출한다.
        - 접속 문제로 AI 호출이 원활하지 않을 시, 에러를 발생한다.
    4. Response body
        - result (string) : called, failed
        - time (string) : 호출 성공 시, 호출 시간
        - reason(string) : 호출 실패 시, 실패 원인
        ```json
       {
        	"result": "called",
        	"predict": ai_instance
        }
        {
        	"result": "failed",
        	"reason": "AI model not loaded."
        }
        ```
