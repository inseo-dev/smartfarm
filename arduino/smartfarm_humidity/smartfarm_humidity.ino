#include <SoftwareSerial.h>
#include <WiFiEsp.h>
#include <WiFiEspClient.h>
#include <ArduinoHttpClient.h>
#include <ArduinoJson.h>
#include <DHT11.h>

//  WiFi 및 서버 설정
char ssid[] = "spreatics_eungam_cctv";
char password[] = "spreatics*";
char server[] = "13.209.245.226";
int port = 5000;

SoftwareSerial espSerial(3, 4); // RX, TX
//SoftwareSerial espSerial(7, 6); // RX, TX

WiFiEspClient client;
HttpClient http(client, server, port);

//  핀 정의
#define DHTPIN 2
#define SOILPIN A0
#define RELAY_PIN 7
#define MOTOR_IN1 12
#define MOTOR_EN 11
#define BUTTONPIN 10

bool lastButtonState = LOW;
// 장치
DHT11 dht(DHTPIN);
bool isWatering = false;
unsigned long wateringStartTime = 0;
const unsigned long wateringDuration = 500;

//  설정값 (기본값, 서버에서 갱신 예정)
//float set_humidity = 60.0; // 기본 습도 (%)
//float set_soil = 50;        // 기본 토양 습도 (analog)
float set_humidity = -1.0; // 기본 습도 (%)
float set_soil = -1.0;        // 기본 토양 습도 (analog)


// 주기 설정
unsigned long ts_interval = 60000;  // 제어 환경 가져오기, 1분 마다
unsigned long ts_timer = 0;

unsigned long ss_interval = 15000;  // 센서 정보 보내기, 10초 마다
unsigned long ss_timer = 0;

unsigned long humidity_interval = 10000;  // 가습 제어하기, 10초 마다
unsigned long humidity_timer = 0;
unsigned long humidity_duration = 7000;  // 가습 시간, 7초 동안
unsigned long humidity_off_timer = 0;
bool humidity_on = false;

unsigned long soil_interval = 180000;  // 토양 제어하기, 3분 마다
unsigned long soil_timer = 0;
unsigned long soil_duration = 1000; // 급수 시간, 1초 동안
unsigned long soil_off_timer = 0;
bool soil_on = false;

float soil_stable_margin = 2.0;   // 급수의 경우 센싱 delay 고려하여 +/-2% 마진을 설정

// 주기 check 및 update 함수
bool checkTimer(unsigned long interval, unsigned long& timer) {
  unsigned long now = millis();
  if (now >= timer) {
    timer = now + interval;
    return true;
  }
  return false;
}

void connectWiFi() {

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
}

//  초기 설정
void setup() {
  Serial.begin(9600);
  espSerial.begin(9600);
  WiFi.init(&espSerial);

  // 버튼 누를 수 있는 기간 표시
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  pinMode(BUTTONPIN, INPUT);

  // 가습기
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  // 급수기
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_EN, OUTPUT);
  analogWrite(MOTOR_EN, 0);

  connectWiFi();  // wifi 연결
  delay(2000);
  Serial.println(" 시스템 시작");
}

// JSON 파싱 함수 (문자열 → JSON 객체)

bool parseJson(String response, DynamicJsonDocument& doc) {
  response.trim();  // 불필요한 공백 제거
  Serial.println(" JSON 응답 ↓");
  Serial.println(response);

  DeserializationError error = deserializeJson(doc, response);
  if (error) {
    Serial.print(" JSON 파싱 실패: ");
    Serial.println(error.c_str());
    return false;
  }
  return true;
}
//  설정값 받아오기
void getTargetSettings() { 

  http.get("/control_settings");
  http.skipResponseHeaders();

  StaticJsonDocument<1000> doc;

  // 스트림 파싱 시도
  deserializeJson(doc, http);

  // 파싱 성공 시 JSON 값 추출
  set_humidity = doc["set_humidity"] | set_humidity;
  set_soil = doc["set_soil_moisture"] | set_soil;

  Serial.print("[TS] ");
  Serial.println(set_humidity); 

  // 연결 정리
  http.stop(); client.stop();
}

void readSensor(int& humidity, int& soilPercent) {
  humidity = dht.readHumidity();
  int soilRaw = analogRead(SOILPIN);
  soilPercent = map(soilRaw, 1023, 0, 0, 100); 
}

// 제어 함수
void controlHumidity() {

  int humidity = dht.readHumidity();
  unsigned long now = millis();

  if (humidity < set_humidity) { 
    Serial.print("[가습기]"); Serial.print(humidity); Serial.print("/"); 
    Serial.print(set_humidity); Serial.println("/ON");
    digitalWrite(RELAY_PIN, HIGH);
    humidity_on = true;
    humidity_off_timer = now + humidity_duration;
  }
}

void controlSoil() {

  int soilRaw = analogRead(SOILPIN);
  int soil = map(soilRaw, 1023, 0, 0, 100); 
  unsigned long now = millis();

  if (soil < (set_soil - soil_stable_margin)) {
    Serial.print("[급수]"); Serial.print(soil); Serial.print("/"); 
    Serial.print(set_soil); Serial.println("/ON");
    digitalWrite(MOTOR_IN1, HIGH);
    analogWrite(MOTOR_EN, 75);
    soil_on = true;
    soil_off_timer = now + soil_duration;
  }
}

// 가습기 종료
void checkHumidityOffTimer() {
  if (!humidity_on) return;
  unsigned long now = millis();
  if (now >= humidity_off_timer) {
    Serial.println("[가습기]stop");
    digitalWrite(RELAY_PIN, LOW);
    humidity_on = false;
  }
}

//  급수기 종료
void checkSoilOffTimer() {
  if (!soil_on) return;
  unsigned long now = millis();
  if (now >= soil_off_timer) {
    Serial.println("[급수]stop");
    digitalWrite(MOTOR_IN1, LOW);
    digitalWrite(MOTOR_EN, 0);
    soil_on = false;
  }
}

void sendStatus() {
  StaticJsonDocument<150> doc;
  doc["device_id"] = 2;

  JsonObject sensor_data = doc.createNestedObject("sensor_data");

  int humidity, soilPercent;
  readSensor(humidity, soilPercent);
  sensor_data["humidity"] = humidity;
  sensor_data["soil_moisture"] = soilPercent;

  String requestBody;
  serializeJson(doc, requestBody);

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


void callAI() {
  Serial.println("[CA]");
  //http.get("/ai_call");
  //http.stop(); client.stop();
}


unsigned long lastPrintTime = 0;

void loop() {

  // 초단위로 처리할 작업들
  unsigned long now = millis();
  if (now - lastPrintTime >= 1000) {

    // debug용 상태 출력
    Serial.print("[loop]"); Serial.print(now / 1000); Serial.print("/");
    Serial.println(WiFi.status());

    // Wifi 연결 확인
    if (WiFi.status() != WL_CONNECTED)
      connectWiFi();
    lastPrintTime = now;
  }

  // 제어환경 못받아온 경우 즉시 다시 시도
  if(set_humidity == -1.0) {
    getTargetSettings(); delay(1000);
    return;
  }

  // 1. target setting 가져오기 (제어 환경 주기인 1분마다 실행됨)
  if (checkTimer(ts_interval, ts_timer)) {
    digitalWrite(LED_BUILTIN, LOW);
    getTargetSettings();
    digitalWrite(LED_BUILTIN, HIGH);
  }

  // 2. 가습 제어
  if (checkTimer(humidity_interval, humidity_timer)) controlHumidity();
  checkHumidityOffTimer();

  // 3. 토양 제어
  if (checkTimer(soil_interval, soil_timer)) controlSoil();
  checkSoilOffTimer();

  // 4. 데이터 서버로 전송
  if (checkTimer(ss_interval, ss_timer)) {
    digitalWrite(LED_BUILTIN, LOW);
    sendStatus();
    digitalWrite(LED_BUILTIN, HIGH);
  }

  // 5. AI 호출 버튼 처리
  bool currentButtonState = digitalRead(BUTTONPIN);
  if (currentButtonState == HIGH && lastButtonState == LOW) callAI();
  lastButtonState = currentButtonState;

  delay(10);  // CPU 잠시 쉬게
}

