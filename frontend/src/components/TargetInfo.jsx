import axios from "axios";
import React, { useEffect, useState } from "react";

function TargetInfo() {
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = () => {
      axios
        .get("https://aismartfarm.duckdns.org/api/ai_diagnosis")
        .then((response) => {
          if (response.data.status == "Send Success!!") {
            setAiData(response.data);
          } else {
            setError("데이터를 가져오지 못했습니다.");
          }
        })
        .catch((err) => {
          console.error(err);
          setError("서버 연결에 실패했습니다.");
        });
    };
    // 페이지 로드시 최초 1회 데이터 가져오기
    fetchData();

    // 이후 5초마다 fetchData 반복 실행
    const interval = setInterval(fetchData, 5000); // 5000ms = 5초

    return () => clearInterval(interval);
  }, []);

  if (!aiData) {
    return <p>데이터 로딩 중...</p>;
  }

  return (
    <div className="text-left w-full">
      <h2 className="inline-block bg-gray-400 p-1 rounded border border-gray-400 text-left text-white mb-1">
        권장 재배 환경
      </h2>
      <div className="grid grid-cols-3 gap-5 mb-6 bg-white p-2 rounded border border-black text-2xl font-bold text-center">
        <p>
          권장 온도
          <br />
          <span className="font-normal">
            {aiData.controls.temp.from}~{aiData.controls.temp.to}도
          </span>
        </p>
        <p>
          권장 습도
          <br />
          <span className="font-normal">
            {aiData.controls.humidity.from}~{aiData.controls.humidity.to}%
          </span>
        </p>
        <p>
          권장 토양 습도
          <br />
          <span className="font-normal">
            {aiData.controls.soil_moisture.from}~
            {aiData.controls.soil_moisture.to}%
          </span>
        </p>
        <p>
          권장 조도
          <br />
          <span className="font-normal">
            {aiData.controls.light_intensity.from}~
            {aiData.controls.light_intensity.to} lux
          </span>
        </p>
        <p className="whitespace-nowrap">
          권장 일조 시간
          <br />
          <span className="font-normal">
            {aiData.controls.light_time.from}시 ~{" "}
            {aiData.controls.light_time.to}시
          </span>
        </p>
      </div>

      <h2 className="inline-block bg-gray-400 p-1 rounded border border-gray-400 text-left text-white mb-1">
        AI 분석
      </h2>
      <div className="bg-white p-2 rounded border border-black whitespace-pre-line">
        {aiData.result}
      </div>
    </div>
  );
}

export default TargetInfo;
