import {
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
  }, []);

  const tempData = sensorData
    ? Object.entries(sensorData.data.temp).map(([time, value]) => ({
        시간: time.slice(11, 16),
        온도: value,
      }))
    : [];
  /*
  const tempData = [
    { 시간: "10:00", 온도: 15 },
    { 시간: "10:01", 온도: 18 },
    { 시간: "10:02", 온도: 23 },
    { 시간: "10:03", 온도: 28 },
    { 시간: "10:04", 온도: 30 },
  ];
  */
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
  const lightData = [
    { 시간: "00:00", 조도: 0 },
    { 시간: "01:00", 조도: 0 },
    { 시간: "02:00", 조도: 0 },
    { 시간: "03:00", 조도: 0 },
    { 시간: "04:00", 조도: 0 },
    { 시간: "05:00", 조도: 1200 },
    { 시간: "06:00", 조도: 1200 },
    { 시간: "07:00", 조도: 1200 },
    { 시간: "08:00", 조도: 1200 },
    { 시간: "09:00", 조도: 1200 },
    { 시간: "10:00", 조도: 1200 },
    { 시간: "11:00", 조도: 1200 },
    { 시간: "12:00", 조도: 1200 },
    { 시간: "13:00", 조도: 1200 },
    { 시간: "14:00", 조도: 1200 },
    { 시간: "15:00", 조도: 1200 },
    { 시간: "16:00", 조도: 1200 },
    { 시간: "17:00", 조도: 1200 },
    { 시간: "18:00", 조도: 1200 },
    { 시간: "19:00", 조도: 0 },
    { 시간: "20:00", 조도: 0 },
    { 시간: "21:00", 조도: 0 },
    { 시간: "22:00", 조도: 0 },
    { 시간: "23:00", 조도: 0 },
  ];
  const sunlightHours = lightData.filter((d) => d.조도 > 0).length; // 태양 떠 있는 시간

  // 조도
  const lux = 1200;

  // 파이 차트에 시간 추가
  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    index,
  }) => {
    const RADIAN = Math.PI / 180;
    // 파이 조각의 중심에서 라벨 위치 계산
    const radius = innerRadius + (outerRadius - innerRadius) * 1.1;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    // index가 0이면 빛 나는 시간 끝 (ex: 05), 1이면 빛 없는 시간 끝 (ex: 18)
    const labels = ["05", "18"];

    return (
      <text
        x={x}
        y={y}
        fill="#333"
        textAnchor={x > cx ? "start" : "end"}
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {labels[index]}
      </text>
    );
  };

  if (!aiData) {
    return <p>데이터 로딩 중...</p>;
  }

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-screen-xl grid grid-cols-4 gap-4 ">
        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 온도</span>
            <div className="w-12 h-4 bg-[#a48eea]/70 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold  mb-4 pl-10">온도</h3>
          <LineChart
            width={300}
            height={200}
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
              fillOpacity={0.7}
            />
          </LineChart>
        </div>

        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 습도</span>
            <div className="w-12 h-4 bg-[#a48eea]/70 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold mb-4 pl-10">습도</h3>
          <LineChart
            width={300}
            height={200}
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
              fillOpacity={0.7}
            />
          </LineChart>
        </div>
        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">목표 토양 습도</span>
            <div className="w-12 h-4 bg-[#a48eea]/70 rounded-sm"></div>
          </div>
          <h3 className="text-2xl font-bold mb-4 pl-10">토양 습도</h3>
          <LineChart
            width={300}
            height={200}
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
              fillOpacity={0.7}
            />
          </LineChart>
        </div>
        <div>
          <div className="flex items-center gap-2 pl-10 mb-2">
            <span className="text-sm font-bold">일조 시간</span>
            <div className="w-12 h-4 bg-[#eaff6e] rounded-sm"></div>
          </div>
          <div className="flex flex-col items-center">
            <h3 className="text-2xl font-bold mb-4 ">조도 및 일조 시간</h3>
            <PieChart
              width={200}
              height={200}
              margin={{ top: 30, right: 20, bottom: 20, left: 40 }}
            >
              <Pie
                data={[
                  { name: "lux", value: sunlightHours },
                  { name: "remain", value: 24 - sunlightHours },
                ]}
                dataKey="value"
                outerRadius={80}
                fill="#8884d8"
                label={renderCustomizedLabel}
              >
                <Cell fill="#eaff6e" />
                <Cell fill="#ccc" />
              </Pie>
            </PieChart>
            <p className="text-center mt-2 text-lg font-bold">{lux} lux</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Graphs;
