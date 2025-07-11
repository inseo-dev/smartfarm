import axios from "axios";
import React, { useEffect, useState } from "react";
/*
function TargetInfo() {
  const [temperature, setTemperature] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get("http://127.0.0.1:5000/setting")
      .then((response) => {
        if (response.data.status === "success") {
          setTemperature(response.data.input_temperature);
        } else {
          setError("데이터를 가져오지 못했습니다.");
        }
      })
      .catch((err) => {
        console.error(err);
        setError("서버 연결에 실패했습니다.");
      });
  }, []);

  return (
    <div>
      <h1>설정 온도 보기</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {temperature !== null ? (
        <p>설정된 온도: {temperature}°C</p>
      ) : (
        <p>온도를 불러오는 중...</p>
      )}
    </div>
  );
}

export default TargetInfo;
*/

function TargetInfo() {
  return (
    <div className="bg-green-50 p-4 rounded shadow">
      <div className="flex justify-between mb-2">
        <p>🌡️ 목표 온도: 18~20도</p>
        <p>💧 목표 습도: 50~60%</p>
        <p>💡 목표 조도: 10,000~15,000 lux</p>
      </div>
      <div className="bg-white p-2 rounded border">
        물결 모양의 잎이 중앙으로 오므라들며 결구가 시작된 상태로, 짙은 녹색을
        띠고 생장이 균형 있게 진행 중입니다.
        <strong className="text-green-600">
          병해나 이상 증상 없이 건강한 생장
        </strong>{" "}
        상태를 유지하고 있습니다.
      </div>
    </div>
  );
}

export default TargetInfo;
