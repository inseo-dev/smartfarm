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
} from "recharts";
import axios from "axios";
import React, { useEffect, useState } from "react";

function Graphs() {
  const [sensorData, setSensorData] = useState(null);
  const [error, setError] = useState(null);
  const tempData = [
    { 시간: "10:00", 온도: 25 },
    { 시간: "11:00", 온도: 26 },
    { 시간: "12:00", 온도: 27 },
  ]; // 시간대별 온도
  const humiData = [
    { 시간: "10:00", 습도: 55 },
    { 시간: "11:00", 습도: 60 },
    { 시간: "12:00", 습도: 62 },
  ]; // 습도
  const lux = 13000;

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
    <div className="flex justify-center">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <h3 className="text-2xl font-bold">온도</h3>
          <LineChart width={250} height={150} data={tempData}>
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
              }}
            />
            <Tooltip />
            <Line type="monotone" dataKey="온도" stroke="#8884d8" />
          </LineChart>
        </div>

        <div>
          <h3 className="text-2xl font-bold">습도</h3>
          <LineChart width={250} height={150} data={humiData}>
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
                value: "습도",
                position: "insideTopLeft",
                offset: 0,
              }}
            />
            <Tooltip />
            <Line type="monotone" dataKey="습도" stroke="#82ca9d" />
          </LineChart>
        </div>

        <div>
          <h3 className="text-2xl font-bold">조도</h3>
          <PieChart width={200} height={200}>
            <Pie
              data={[
                { name: "lux", value: lux },
                { name: "remain", value: 20000 - lux },
              ]}
              dataKey="value"
              outerRadius={80}
              fill="#8884d8"
              label
            >
              <Cell fill="#eaff6e" />
              <Cell fill="#ccc" />
            </Pie>
          </PieChart>
          <p className="text-center mt-2 text-lg font-bold">{lux} lux</p>
        </div>
      </div>
      <div>
        <h3>센서 정보(벡엔드에서 가져온 정보 연습)</h3>
        {error && <p style={{ color: "red" }}>{error}</p>}
        {sensorData ? (
          <div>
            <p>디바이스 ID: {sensorData.device_id}</p>
            <p>센서 종류: {sensorData.sensor_type}</p>
            <p>센서 값: {sensorData.sensor_value}</p>
            <p>시간: {sensorData.timestamp}</p>
          </div>
        ) : (
          <p>센서 데이터를 불러오는 중...</p>
        )}
      </div>
    </div>
  );
}

export default Graphs;
