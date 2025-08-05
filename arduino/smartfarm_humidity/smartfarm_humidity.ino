// 📦 라이브러리 포함
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

SoftwareSerial espSerial(2, 3); // RX, TX
WiFiEspClient client;
HttpClient http(client, server, port);

//  핀 정의
#define DHTPIN 4
#define SOILPIN A0
#define RELAY_PIN 7
#define MOTOR_IN1 12
#define MOTOR_IN2 13
#define MOTOR_EN 11
#define BUTTONPIN 10
#define LEDPIN 9  // 버튼 가능 표시용 LED

bool lastButtonState = LOW;
// 장치
DHT11 dht(DHTPIN);
bool isWatering = false;
unsigned long wateringStartTime = 0;
const unsigned long wateringDuration = 500;

//  설정값 (기본값, 서버에서 갱신 예정)
float set_humidity = 60.0; // 기본 습도 (%)
float set_soil = 50;        // 기본 토양 습도 (analog)

//  초기 설정
void setup() {
  Serial.begin(9600);
  espSerial.begin(9600);
  WiFi.init(&espSerial);
  pinMode(LEDPIN, OUTPUT);
  digitalWrite(LEDPIN, LOW);

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(MOTOR_EN, OUTPUT);
  pinMode(BUTTONPIN, INPUT);
  digitalWrite(RELAY_PIN, LOW);
  analogWrite(MOTOR_EN, 0);

  Serial.print(" WiFi 연결 중...");
  WiFi.begin(ssid, password);
  delay(5000);
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" 연결됨");
  } else {
    Serial.println(" 연결 실패");
  }

  getTargetSettings(); // 서버에서 초기 설정값 받아오기
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
void getTargetSettings() {  http.get("/control_settings");

  // 헤더를 넘기고 본문 스트림 준비
  http.skipResponseHeaders();  

  // 메모리 충분히 확보 (필요시 늘리세요)
  DynamicJsonDocument doc(2048);  

  // 스트림 파싱 시도
  DeserializationError error = deserializeJson(doc, http);

  if (error) {
    Serial.print("❌ JSON 파싱 실패: ");
    Serial.println(error.c_str());
    http.stop(); 
    client.stop();
    return;
  }

  // 파싱 성공 시 JSON 값 추출
  set_humidity = doc["set_humidity"] | set_humidity;
  set_soil = doc["set_soil_moisture"] | set_soil;

  Serial.print("  설정 습도: "); Serial.print(set_humidity);
  Serial.print("  설정 토양습도: "); Serial.println(set_soil);

  // 연결 정리
  http.stop();  
  client.stop();
}



// 제어 함수
void controlActuators(float humidity, int soil) {
  if (!isnan(humidity) && humidity < set_humidity) {
    Serial.println(" 가습기 ON");
    digitalWrite(RELAY_PIN, HIGH);
    delay(7000);
    digitalWrite(RELAY_PIN, LOW);
  }

  if (!isWatering && soil < set_soil) {
    Serial.println(" 급수 시작");
    digitalWrite(MOTOR_IN1, HIGH);
    digitalWrite(MOTOR_IN2, LOW);
    analogWrite(MOTOR_EN, 75);
    wateringStartTime = millis();
    isWatering = true;
  }
}

//  급수기 자동 종료
void handleWatering() {
  if (isWatering && millis() - wateringStartTime >= wateringDuration) {
    Serial.println(" 급수 종료");
    digitalWrite(MOTOR_IN1, LOW);
    digitalWrite(MOTOR_IN2, LOW);
    digitalWrite(MOTOR_EN, LOW);
    isWatering = false;
  }
}

void sendStatus(const char* type, int value) {
  WiFiEspClient sendClient;
  HttpClient sendHttp(sendClient, server, port);

  StaticJsonDocument<150> doc;
  doc["device_id"] = 2;

  JsonObject sensor_data = doc.createNestedObject("sensor_data");
  if (strcmp(type, "humidity") == 0) {
    sensor_data["humidity"] = value;
  } else if (strcmp(type, "soil_moisture") == 0) {
    sensor_data["soil_moisture"] = value;
  }

  Serial.print(" 전송 JSON: ");
  serializeJson(doc, Serial);
  Serial.println();

  sendHttp.beginRequest();
  sendHttp.post("/sensor_data");
  sendHttp.sendHeader("Content-Type", "application/json");
  sendHttp.sendHeader("Connection", "close");
  sendHttp.sendHeader("Content-Length", measureJson(doc));
  sendHttp.beginBody();
  serializeJson(doc, sendHttp);  // ← 안정적으로 직접 스트림에 씀
  sendHttp.endRequest();

  sendHttp.stop();
  sendClient.stop();
}


void callAI() {
  Serial.println("버튼 출력 성공");
  http.get("/ai_call");
  Serial.println("ai 호출 성공");
  http.stop();
}

void loop() {

  getTargetSettings();
  float humidity = dht.readHumidity();
  int soilRaw = analogRead(SOILPIN);
  int soilPercent = map(soilRaw, 1023, 0, 0, 100); 

  Serial.print(" 습도: "); Serial.print(humidity);
  Serial.print(" /  토양: "); Serial.print(soilPercent); Serial.println("%");

  controlActuators(humidity, soilPercent);
  handleWatering();

  sendStatus("humidity", (int)humidity);
  sendStatus("soil_moisture", soilPercent);

  digitalWrite(LEDPIN, HIGH);
  unsigned long startTime = millis();
  bool buttonHandled = false;

  while (millis() - startTime < 5000) {
    handleWatering();
    bool currentButtonState = digitalRead(BUTTONPIN);
    if (!buttonHandled && currentButtonState == HIGH && lastButtonState == LOW) {
      delay(20);  // 디바운싱
      callAI();
      digitalWrite(LEDPIN, LOW);  // 버튼 사용 종료
      buttonHandled = true;
    }
    lastButtonState = currentButtonState;


    delay(10);  // CPU 잠시 쉬게
  }

  digitalWrite(LEDPIN, LOW);  // 시간 초과 시 LED OFF


}

