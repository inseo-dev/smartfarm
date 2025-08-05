#include <SoftwareSerial.h>
#include <WiFiEsp.h>
#include <WiFiEspClient.h>    
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <DHT.h>            // DHT 라이브러리 실제 사용을 위해 포함

#define DHTPIN 13    // 온습도 데이터핀
#define DHTTYPE DHT11 // 온습도 센서 타입
DHT dht(DHTPIN, DHTTYPE); // 온습도 객체 생성

// 온도, 전구 시작/끝 초기 세팅
int set_start_light = -1;
int set_end_light = -1;
float set_temperature = -1.0;
float stable_temp = 1.0;  // 설정온도 +/- 1도의 경우 제어 안함
//int my_device_id = 1; //device_id setting

// 핀번호
int light_bulb1 = 11; // 전구 릴레이 제어핀
int heater1 = 10; // 히터 릴레이 제어핀
int EN1 = 5; // 팬1 pwm 제어
int IN1 = 4; // 팬1
int EN2 = 3; // 팬2 pwm 제어
int IN2 = 2; // 팬2

// 시작 시간 설정
float startHour = -1;

// 주기 상수 (in sec)
const unsigned long target_setting_interval = 60;  // 제어환경 가져오기
const unsigned long light_interval = 5; // 조명 제어 주기 
const unsigned long temp_interval = 5;  // 온도 제어 주기
const unsigned long send_interval = 10;

// wifi setting
int WIFI_RX = 6;
int WIFI_TX = 7;
SoftwareSerial espSerial(WIFI_TX, WIFI_RX); // RX, TX
//char ssid[] = "spreatics_eungam_cctv";
//char password[] = "spreatics*";

// http setting
//String server_ip = "43.200.35.210";  // 내 ec2 서버 주소
//int server_port = 5000;  // 내 flask web server 포트 번호
WiFiEspClient client;
//HttpClient http(client, server_ip, server_port);
HttpClient http(client, "13.209.245.226", 5000);

//  설정값 받아오기
void getTargetSettings() { 

  http.get("/control_settings");
  http.skipResponseHeaders();

  StaticJsonDocument<1000> doc;

  // 스트림 파싱 시도
  deserializeJson(doc, http);

  // 파싱 성공 시 JSON 값 추출
  set_temperature = doc["set_temperature"] | set_temperature;
  set_start_light = doc["set_start_light"] | set_start_light;
  set_end_light = doc["set_end_light"] | set_end_light;

  //Serial.print(F("> 설정 온도: ")); Serial.println(set_temperature);
  //Serial.print(F("> 설정 조명 시작시간: ")); Serial.println(set_start_light);
  //Serial.print(F("> 설정 조명 종료시간: ")); Serial.println(set_end_light);
  Serial.print("[TS]");
  Serial.print(set_temperature); Serial.print("/");
  Serial.print(set_start_light); Serial.print("/");
  Serial.println(set_end_light);

  // 연결 정리
  http.stop(); client.stop();
}

// 시간을 받아오는 함수
void getCurrentTime() {
  http.get("/time"); // GET /time 엔드포인트 호출
  http.skipResponseHeaders();

  StaticJsonDocument<500> doc;

  // 스트림 파싱 시도
  DeserializationError error = deserializeJson(doc, http);
  if(error) {
    //Serial.print("시간 설정 실패");
    return;
  }

  // 파싱 성공 시 JSON 값 추출하여 setting_time 업데이트
  String setting_time = doc["set_time"].as<String>(); // String으로 추출
  //Serial.println("> 받아온 시간: " + setting_time);
  
  // 슬라이싱하여 시/분/초 추출
  // setting_time 값 예시 : "2025-07-10T13:15:42.123456+09:00"
  int currentHour = setting_time.substring(11, 13).toInt();
  int currentMinute = setting_time.substring(14, 16).toInt();

  // 시간을 실수형으로 관리하여 변수 하나만 유지 (코드 최소화, 메모리 최소화)
  startHour = currentHour + currentMinute / 60.0;
  //Serial.println("> 시작 시간: " + String(startHour, 2));
  Serial.print("[CT]"); Serial.println(startHour);
  delay(2000);
  
  // 연결 정리
  http.stop(); client.stop();
}

void setup() {
  Serial.begin(9600);
  espSerial.begin(9600);
  WiFi.init(&espSerial);

  //Serial.println(F("WiFi 연결 중..."));
  //WiFi.begin(ssid, password);
  WiFi.begin("spreatics_eungam_cctv", "spreatics*");
  delay(5000);
  while(WiFi.status()!=WL_CONNECTED){
    delay(500);
  }
  
  /*
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(F("WiFi 연결 성공"));
  } else {
    Serial.println(F("WiFi 연결 실패"));
  }
  */

  dht.begin(); //DHT 센서 초기화
  pinMode(light_bulb1, OUTPUT);
  pinMode(heater1, OUTPUT);
  digitalWrite(light_bulb1, HIGH); //초기 상태: 전구 끄기
  digitalWrite(heater1, HIGH); //초기 상태: 히터 끄기
  pinMode(EN1, OUTPUT);   // 배기팬
  pinMode(IN1, OUTPUT);
  pinMode(EN2, OUTPUT);   // 흡기팬
  pinMode(IN2, OUTPUT);

  delay(2000);

  // 아두이노 시계 초기 세팅
  getCurrentTime();

  // 세팅 초기 설정
  getTargetSettings();

}

// 센서값 보내기
//void PostStatus(int device_id, float temperature, float light_intensity) {
void sendData() {
  StaticJsonDocument<200> json;
  //json["device_id"] = my_device_id;
  json["device_id"] = 1;

  JsonObject sensor_data = json.createNestedObject("sensor_data");
  sensor_data["temp"] = dht.readTemperature();

  int adc = analogRead(A0);
  float lux = exp(0.00921 * adc - 2.302);  // 약식 lux 계산
  //Serial.println(lux);
  sensor_data["light_intensity"] = lux;
  
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

  Serial.print("[SD]"); Serial.println(requestBody);

  http.stop();
  client.stop();
}

void ctrLight(unsigned long currentSec) {
    float currentHour = fmod(startHour + currentSec / 3600.0, 24.0);
    bool lightOn = (currentHour >= set_start_light && currentHour < set_end_light);
    digitalWrite(light_bulb1, lightOn? LOW : HIGH);
    //Serial.println("[조명제어]");
    Serial.print("[CL]");
    Serial.print(set_start_light); Serial.print("/"); 
    Serial.print(set_end_light); Serial.print("/");
    Serial.println(lightOn);
}

void ctrTemp() {

  float current_temp = dht.readTemperature();

  Serial.print("[CT]");
  Serial.print(set_temperature);Serial.print("/");
  Serial.print(current_temp);Serial.print("/");

  if(current_temp > set_temperature + stable_temp){
    //Serial.println(F("> 현재 온도가 높습니다. 팬을 동작시킵니다."));
    Serial.println("F");
    digitalWrite(heater1, HIGH);  // 히터 끄기
    analogWrite(EN1, 80);  // 배기팬 켜기
    digitalWrite(IN1, HIGH);
    analogWrite(EN2, 0);  // 흡기팬 끄기
    digitalWrite(IN2, LOW);    
  }
  else if(current_temp < set_temperature - stable_temp){
    //Serial.println(F("> 현재 온도가 낮습니다. 히터를 동작시킵니다."));
    Serial.println("H");
    digitalWrite(heater1, LOW); // 히터 켜기
    analogWrite(EN1, 0);    // 배기팬 끄기
    digitalWrite(IN1, LOW);
    analogWrite(EN2, 80);    // 흡기팬 켜기
    digitalWrite(IN2, HIGH);
  }
  else {
    //Serial.println(F("> 설정 온도 +/- 1도 범위에 있습니다."));
    Serial.println("-");
    digitalWrite(heater1, HIGH); // 히터 끄기
    analogWrite(EN1, 0);  // 배기팬 끄기
    digitalWrite(IN1, LOW);
    analogWrite(EN2, 0);  // 흡기팬 끄기
    digitalWrite(IN2, LOW);    
  }
}

void loop() {

  Serial.print("[loop]");
  // 시간을 못받아온 경우 다시 시도
  if(startHour == -1) { 
    //Serial.println("[CT] retry");
    getCurrentTime(); delay(1000);
    return;
  }

  if(set_temperature == -1.0) {
    //Serial.println("[TS] retry");
    getTargetSettings(); delay(1000);
    return;
  }

  // 현재 초
  unsigned long currentSec = millis() / 1000;
  Serial.println(currentSec);

  // 0. target setting update
  if(currentSec % target_setting_interval == 0)
    getTargetSettings();

  // 1. 조명 설정하기
  if(currentSec % light_interval == 0)
    ctrLight(currentSec);

  // 2. 히터/팬 켜기
  if(currentSec % temp_interval == 0)
    ctrTemp();

  // 3. 데이터 보내기
  if(currentSec % send_interval == 0)
    sendData();

  delay(1000);
}
