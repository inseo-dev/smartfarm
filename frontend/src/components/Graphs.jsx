import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  ReferenceArea,
  Label,
} from "recharts";
import axios from "axios";
import React, { useEffect, useState } from "react";

function Graphs() {
  const [sensorData, setSensorData] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = () => {
      axios
        .get("https://aismartfarm.duckdns.org/api/sensor_data")
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

  // 시간대별 온도
  const tempData = sensorData
    ? Object.entries(sensorData.data.temp).map(([time, value]) => ({
        시간: time.slice(11, 16),
        온도: value,
      }))
    : [];

  // 시간대별 습도
  const humiData = sensorData
    ? Object.entries(sensorData.data.humidity).map(([time, value]) => ({
        시간: time.slice(11, 16),
        습도: value,
      }))
    : [];
  // 시간대별 토양수분
  const soilData = sensorData
    ? Object.entries(sensorData.data.soil_moisture).map(([time, value]) => ({
        시간: time.slice(11, 16),
        토양습도: value,
      }))
    : [];
  //시간대별 일조 시간
  const lightData = sensorData
    ? Object.entries(sensorData.data.light_intensity).map(([time, value]) => ({
        시간: time.slice(11, 16),
        조도: value,
      }))
    : [];

  if (!aiData) {
    return <p>데이터 로딩 중...</p>;
  }

  return (
    <div className="w-full px-4">
      <div className="w-full max-w-screen-xl grid grid-cols-2 gap-6 ">
        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 온도</span>
            <div className="w-12 h-4 bg-[#a48eea]/30 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold  mb-4 pl-10">온도</h3>
          <div className="flex flex-col items-center">
            <LineChart
              width={450}
              height={300}
              data={tempData}
              margin={{ top: 30, right: 20, bottom: 20, left: 40 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="#ccc"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="시간"
                label={{
                  value: "시간",
                  position: "insideBottomRight",
                  offset: -5,
                }}
              />
              <YAxis
                domain={[0, aiData.controls.temp.to + 10]}
                label={{
                  value: "온도",
                  position: "insideTopLeft",
                  offset: 0,
                  dy: -20,
                }}
              />
              <Tooltip />
              <Line type="monotone" dataKey="온도" stroke="#8884d8" />
              <ReferenceArea
                y1={aiData.controls.temp.from}
                y2={aiData.controls.temp.to}
                strokeOpacity={0.3}
                fill="#a48eea"
                fillOpacity={0.3}
              />
            </LineChart>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 습도</span>
            <div className="w-12 h-4 bg-[#a48eea]/30 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold mb-4 pl-10">습도</h3>
          <div className="flex flex-col items-center">
            <LineChart
              width={450}
              height={300}
              data={humiData}
              margin={{ top: 30, right: 20, bottom: 20, left: 40 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="#ccc"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="시간"
                label={{
                  value: "시간",
                  position: "insideBottomRight",
                  offset: -5,
                }}
              />
              <YAxis
                domain={[0, 100]}
                label={{
                  value: "습도",
                  position: "insideTopLeft",
                  offset: 0,
                  dy: -20,
                }}
              />
              <Tooltip />
              <Line type="monotone" dataKey="습도" stroke="#82ca9d" />
              <ReferenceArea
                y1={aiData.controls.humidity.from}
                y2={aiData.controls.humidity.to}
                strokeOpacity={0.3}
                fill="#a48eea"
                fillOpacity={0.3}
              />
            </LineChart>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 토양 습도</span>
            <div className="w-12 h-4 bg-[#a48eea]/30 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold mb-4 pl-10">토양 습도</h3>
          <div className="flex flex-col items-center">
            <LineChart
              width={450}
              height={300}
              data={soilData}
              margin={{ top: 30, right: 20, bottom: 20, left: 40 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="#ccc"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="시간"
                label={{
                  value: "시간",
                  position: "insideBottomRight",
                  offset: -5,
                }}
              />
              <YAxis
                domain={[0, 100]}
                label={{
                  value: "토양습도",
                  position: "insideTopLeft",
                  offset: 0,
                  dy: -20,
                }}
              />
              <Tooltip />
              <Line type="monotone" dataKey="토양습도" stroke="#82ca9d" />
              <ReferenceArea
                y1={aiData.controls.soil_moisture.from}
                y2={aiData.controls.soil_moisture.to}
                strokeOpacity={0.3}
                fill="#a48eea"
                fillOpacity={0.3}
              />
            </LineChart>
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 조도</span>
            <div className="w-12 h-4 bg-[#a48eea]/30 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold mb-4 pl-10">조도</h3>
          <div className="flex flex-col items-center">
            <LineChart
              width={450}
              height={300}
              data={lightData}
              margin={{ top: 30, right: 20, bottom: 20, left: 40 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="#ccc"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="시간"
                label={{
                  value: "시간",
                  position: "insideBottomRight",
                  offset: -5,
                }}
              />
              <YAxis
                domain={[0, aiData.controls.light_intensity.to]}
                label={{
                  value: "조도",
                  position: "insideTopLeft",
                  offset: 0,
                  dy: -20,
                }}
              />
              <Tooltip />
              <Line type="monotone" dataKey="조도" stroke="#82ca9d" />
              <ReferenceArea
                y1={aiData.controls.light_intensity.from}
                y2={aiData.controls.light_intensity.to}
                strokeOpacity={0.3}
                fill="#a48eea"
                fillOpacity={0.3}
              />
            </LineChart>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Graphs;
