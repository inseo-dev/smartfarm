import PlantImage from "./PlantImage";
import TargetInfo from "./TargetInfo";
import Graphs from "./Graphs";
import DeviceStatus from "./DeviceStatus";

function ParentComponent() {
  return (
    <div className="flex justify-between">
      <div>
        <PlantImage />
        <TargetInfo />
        <Graphs />
      </div>

      <DeviceStatus />
    </div>
  );
}
export default ParentComponent;
