import axios from "axios";
import React, { useEffect, useState } from "react";

function TargetInfo() {
  const [sensorData, setSensorData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get("http://43.200.35.210:5000/sensor_data")
      .then((response) => {
        if (response.data.result === "sended") {
          setSensorData(response.data);
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
    <div className="text-left">
      <h2 className="inline-block bg-gray-400 p-1 rounded border border-gray-400 text-left text-white mb-1">
        권장 재배 환경
      </h2>
      <div className="flex justify-between mb-2 bg-white p-2 rounded border border-black text-2xl font-bold text-center">
        <p>
          목표 온도
          <br />
          <span className="font-normal">18~20도</span>
        </p>
        <p>
          목표 습도
          <br />
          <span className="font-normal">50~60%</span>
        </p>
        <p>
          목표 조도
          <br />
          <span className="font-normal">10,000~15,000 lux</span>
        </p>
        <p>
          목표 일조량 시간(1일 기준)
          <br />
          <span className="font-normal">12~16시간</span>
        </p>
      </div>

      <h2 className="inline-block bg-gray-400 p-1 rounded border border-gray-400 text-left text-white mb-1">
        AI 분석
      </h2>
      <div className="bg-white p-2 rounded border border-black">
        물결 모양의 잎이 중앙으로 오므라들며 결구가 시작된 상태로, 짙은 녹색을
        띠고 생장이 균형 있게 진행 중입니다.&nbsp;
        <strong>병해나 이상 증상 없이 건강한 생장</strong>
        상태를 유지하고 있습니다.
      </div>
    </div>
  );
}

export default TargetInfo;
