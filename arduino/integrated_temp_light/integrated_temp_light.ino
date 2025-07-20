#include <SoftwareSerial.h>
#include <WiFiEsp.h>
#include <WiFiEspClient.h>    
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <DHT.h>            // DHT 라이브러리 실제 사용을 위해 포함

#define DHTPIN 9    // 온습도 데이터핀
#define DHTTYPE DHT11 // 온습도 센서 타입
DHT dht(DHTPIN, DHTTYPE); // 온습도 객체 생성

// 온도, 전구 시작/끝 초기 세팅
int set_start_light = 0;
int set_end_light = 0;
float set_temperature = 0.0;
int my_device_id = 1; //device_id setting

int light_bulb1 = 10; // 전구 릴레이 제어핀
int heater1 = 12; // 히터 릴레이 제어핀
int IN1 = 2; // 팬 1
int IN2 = 3; // 팬 2
int EN1 = 5; // 팬 pwm 제어

// String 형태의 전역 변수 setting_time 선언
String setting_time = "";
bool timeValid = false, targetValid = false;   // 전역 플래그 추가 ─ 시간세팅 수신 성공 여부

// setting_time 슬라이싱 한 시/분/초 값
int currentHour = 0;
int currentMinute = 0;
int currentSecond = 0;

// 이전 시간 업데이트 시점을 기록할 변수 (밀리초)
unsigned long previousMillis = 0;
unsigned long lightTimer = 0;
unsigned long tempTimer = 0;
bool lightState = false;
const unsigned long interval = 1000; // 1초 간격
const unsigned long light_interval = 1800000UL; // 30분 간격
const unsigned long temp_interval = 10000;

// wifi setting
int WIFI_RX = 6;
int WIFI_TX = 7;
SoftwareSerial espSerial(WIFI_TX, WIFI_RX); // RX, TX
char ssid[] = "spreatics_eungam_cctv";
char password[] = "spreatics*";

// http setting
String server_ip = "43.200.35.210";  // 내 ec2 서버 주소
int server_port = 5000;  // 내 flask web server 포트 번호
WiFiEspClient client;
HttpClient http(client, server_ip, server_port);

//  설정값 받아오기
void getTargetSettings() { 
  http.get("/control_settings");
  http.skipResponseHeaders();

  StaticJsonDocument<384> doc;

  // 스트림 파싱 시도
  DeserializationError error = deserializeJson(doc, http);

  if (error) {
    targetValid = false;
    Serial.print(F("❌ JSON 파싱 실패: "));
    Serial.println(error.c_str());
    http.stop(); client.stop();
    delay(2000);
    return;
  }

  // 파싱 성공 시 JSON 값 추출
  set_temperature = doc["set_temperature"] | set_temperature;
  set_start_light = doc["set_start_light"] | set_start_light;
  set_end_light = doc["set_end_light"] | set_end_light;

  Serial.print(F("  설정 온도: ")); Serial.println(set_temperature);
  Serial.print(F(" / 설정 조명 시작시간: ")); Serial.println(set_start_light);
  Serial.print(F(" / 설정 조명 종료시간: ")); Serial.println(set_end_light);

  targetValid = true;
  // 연결 정리
  http.stop();  
  client.stop();
}

// 시간을 받아오는 함수
void getCurrentTime() {
  http.get("/time"); // GET /time 엔드포인트 호출
  http.skipResponseHeaders();

  StaticJsonDocument<384> doc;

  // 스트림 파싱 시도
  DeserializationError error = deserializeJson(doc, http);

  if (error) {
    timeValid = false;
    Serial.print(F("❌ JSON 파싱 실패: "));
    Serial.println(error.c_str());
    http.stop(); client.stop();
    delay(2000);
    return;
  }

  // 파싱 성공 시 JSON 값 추출하여 setting_time 업데이트
  setting_time = doc["set_time"].as<String>(); // String으로 추출
  Serial.print(F("받아온 시간: "));
  Serial.println(setting_time);
  
  // 슬라이싱하여 시/분/초 추출
  // setting_time 값 예시 : "2025-07-10T13:15:42.123456+09:00"
  currentHour = setting_time.substring(11, 13).toInt();
  currentMinute = setting_time.substring(14, 16).toInt();
  currentSecond = setting_time.substring(17, 19).toInt();

  Serial.print(F("초기 설정 시간: "));
  Serial.print(currentHour);
  Serial.print(F("시 "));
  Serial.print(currentMinute);
  Serial.print(F("분 "));
  Serial.print(currentSecond);
  Serial.println(F("초"));

  timeValid = true;
  // 연결 정리
  http.stop();
  client.stop();
}

void setup() {
  Serial.begin(9600);
  espSerial.begin(9600);
  WiFi.init(&espSerial);

  Serial.println(F("WiFi 연결 중..."));
  WiFi.begin(ssid, password);
  delay(5000);
  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(F("WiFi 연결 성공"));
  } else {
    Serial.println(F("WiFi 연결 실패"));
  }
  delay(2000);
  dht.begin(); //DHT 센서 초기화
  pinMode(light_bulb1, OUTPUT);
  pinMode(heater1, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(EN1, OUTPUT);
  // 세팅 전구 작동 시간 초기 설정
  getTargetSettings();
  // 아두이노 시계 초기 세팅
  getCurrentTime();

  digitalWrite(light_bulb1, HIGH); //초기 상태: 전구 끄기 (릴레이 모듈에 따라 HIGH/LOW 다를 수 있음)
  digitalWrite(heater1, HIGH); //초기 상태: 히터 끄기 (릴레이 모듈에 따라 HIGH/LOW 다를 수 있음)
  digitalWrite(IN1, LOW); // 팬도 초기에 멈춰있는 상태로 시작
  digitalWrite(IN2, LOW);
  analogWrite(EN1, 0);
}

// DB로 센서값 보내기
void PostStatus(int device_id, float temperature, float light_intensity) {
  StaticJsonDocument<200> json;
  json["device_id"] = device_id;

  JsonObject sensor_data = json.createNestedObject("sensor_data");
  sensor_data["temp"] = temperature;
  sensor_data["light_intensity"] = light_intensity;

  String requestBody;
  serializeJson(json, requestBody);

  // http post 호출
  http.beginRequest();
  http.post("/sensor_data");
  http.sendHeader("Content-Type", "application/json");
  http.sendHeader("Content-Length", requestBody.length());
  http.beginBody();
  http.print(requestBody);
  http.endRequest();

  http.stop();
  client.stop();
}

void loop() {
  if(!timeValid) getCurrentTime();
  if(!targetValid) getTargetSettings();
  if(!(timeValid && targetValid)) return;

  unsigned long currentMillis = millis(); // millis()는 아두이노가 시작된 이후의 시간을 밀리초로 반환한 함수.
  if (currentMillis - previousMillis >= interval){
    previousMillis = currentMillis; // 이전 시간 업데이트

    // 1초 증가
    currentSecond++;

    // 60초가 되면 1분 증가
    if(currentSecond >= 60){
      currentSecond = 0;
      currentMinute++;

      // 60분이 되면 시 증가, 분 초기화
      if(currentMinute >= 60){
        currentMinute = 0;
        currentHour++;

        // 24시가 되면 0시로 초기화
        if(currentHour >= 24){
          currentHour = 0;
        }
      }
    }
  }

  if(currentMillis - lightTimer >= light_interval){
    lightTimer = currentMillis;

    bool shouldLightOn = (currentHour >= set_start_light && currentHour < set_end_light);

    if(shouldLightOn != lightState){
      lightState = shouldLightOn;
      digitalWrite(light_bulb1, lightState? LOW : HIGH); // LOW = ON
      Serial.println(lightState ? F("-> 일광시간: 전구 ON") : F("-> 소등시간: 전구 OFF"));
    }
  }

  // 온도_조도 보내기 & 히터/팬 켜기
  if(currentMillis - tempTimer >= temp_interval){
    tempTimer = currentMillis;

    float current_temp = dht.readTemperature();
    if (isnan(current_temp)) {
      Serial.println(F("DHT센서 값을 읽어오지 못했습니다!"));
      return;
    }
    float current_light_intensity = 0.0;

    PostStatus(my_device_id, current_temp, current_light_intensity);

    if(current_temp > set_temperature){
      Serial.println(F("현재 온도가 높습니다. 팬을 동작시킵니다."));
      digitalWrite(heater1, HIGH);
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      analogWrite(EN1, 150);  
    }
    else if(current_temp < set_temperature){
      Serial.println(F("현재 온도가 낮습니다. 히터를 동작시킵니다."));
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);
      analogWrite(EN1, 0);
      digitalWrite(heater1, LOW); // 히터 켜기
    }
  }
}
