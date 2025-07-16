function DeviceStatus() {
  const deviceStates = {
    히터: true,
    팬: false,
    전구: true,
    급수: false,
  };

  return (
    <div className="flex flex-col gap-4">
      {Object.entries(deviceStates).map(([name, isOn]) => (
        <div
          key={name}
          className={`p-4 rounded text-center font-bold text-xl ${
            isOn ? "bg-pink-300 text-white" : "bg-gray-700 text-gray-300"
          }`}
        >
          {name}
          <br />
          {isOn ? "ON" : "OFF"}
        </div>
      ))}
    </div>
  );
}
export default DeviceStatus;
