import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";

function Graphs() {
  const tempData = [25, 26, 27]; // 시간대별 온도
  const humiData = [10, 10, 15]; // 습도
  const lux = 13000;

  return (
    <div className="grid grid-cols-3 gap-4">
      <div>
        <h3>온도</h3>
        <LineChart width={250} height={150} data={tempData}>
          <XAxis dataKey="시간" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="온도" stroke="#8884d8" />
        </LineChart>
      </div>

      <div>
        <h3>습도</h3>
        <LineChart width={250} height={150} data={humiData}>
          <XAxis dataKey="시간" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="습도" stroke="#82ca9d" />
        </LineChart>
      </div>

      <div>
        <h3>조도</h3>
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
  );
}

export default Graphs;
