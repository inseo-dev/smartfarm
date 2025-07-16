import axios from "axios";
import React, { useEffect, useState } from "react";

function TargetInfo() {
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get("http://43.200.35.210:5000/ai_diagnosis")
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
  }, []);

  if (!aiData) {
    return <p>데이터 로딩 중...</p>;
  }

  return (
    <div className="text-left">
      <h2 className="inline-block bg-gray-400 p-1 rounded border border-gray-400 text-left text-white mb-1">
        권장 재배 환경
      </h2>
      <div className="grid grid-cols-3 gap-5 mb-6 bg-white p-2 rounded border border-black text-2xl font-bold text-center">
        <p>
          권장 온도
          <br />
          <span className="font-normal">
            {aiData.controls["온도"].from}~{aiData.controls["온도"].to}도
          </span>
        </p>
        <p>
          권장 습도
          <br />
          <span className="font-normal">
            {aiData.controls["습도"].from}~{aiData.controls["습도"].to}%
          </span>
        </p>
        <p>
          권장 토양 습도
          <br />
          <span className="font-normal">
            {aiData.controls["토양 습도"].from}~
            {aiData.controls["토양 습도"].to}%
          </span>
        </p>
        <p>
          권장 조도
          <br />
          <span className="font-normal">
            {aiData.controls["조도"].from}~{aiData.controls["조도"].to} lux
          </span>
        </p>
        <p className="whitespace-nowrap">
          권장 일조 시간(1일 기준)
          <br />
          <span className="font-normal">
            {aiData.controls["일조 시간"].from}~
            {aiData.controls["일조 시간"].to}
            시간
          </span>
        </p>
      </div>

      <h2 className="inline-block bg-gray-400 p-1 rounded border border-gray-400 text-left text-white mb-1">
        AI 분석
      </h2>
      <div className="bg-white p-2 rounded border border-black">
        {aiData.result}
      </div>
    </div>
  );
}

export default TargetInfo;
