import axios from "axios";
import React, { useEffect, useState } from "react";

function PlantImage() {
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get("http://aismartfarm.duckdns.org/api/ai_diagnosis")
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
    <div className="flex flex-col items-center text-center">
      <img
        src={aiData.image_url}
        alt="작물 사진"
        className="w-64 h-auto"
        onError={(e) => {
          e.target.src =
            "https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcQqG8vMAi185miSPAq-hGkFPQTWFWUpa5vJ1bOdTfh8gdsaTgb6BHUHA4otXHZKq48fXlGdSsPpXsorb-ZzrldnXg"; // 대체 이미지
        }}
      />
      <p className="text-xl mt-2 font-bold">{aiData.plant_name}</p>
    </div>
  );
}

export default PlantImage;
