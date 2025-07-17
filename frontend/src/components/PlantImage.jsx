import axios from "axios";
import React, { useEffect, useState } from "react";

function PlantImage() {
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
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
  }, []);

  if (!aiData) {
    return <p>데이터 로딩 중...</p>;
  }

  return (
    <div className="flex flex-col items-center text-center">
      <img
        src={aiData.image_url}
        alt="작물 사진"
        className="w-[320px] h-auto rounded-xl shadow-md"
        onError={(e) => {
          e.target.src =
            "https://png.pngtree.com/png-vector/20190130/ourmid/pngtree-simple-potted-cartoon-illustration-design-plantflower-potillustrationai-material-png-image_591188.jpg";
        }}
      />
      <p className="text-xl mt-2 font-bold">{aiData.plant_name}</p>
    </div>
  );
}

export default PlantImage;
