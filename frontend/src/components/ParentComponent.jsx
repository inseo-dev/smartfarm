import PlantImage from "./PlantImage";
import TargetInfo from "./TargetInfo";
import Graphs from "./Graphs";
import DeviceStatus from "./DeviceStatus";

function ParentComponent() {
  return (
    <div className="flex flex-col items-center w-full gap-8">
      <div className="flex justify-center items-start gap-12">
        <PlantImage />
        <TargetInfo />
      </div>
      <div className="w-full flex justify-center">
        <Graphs />
      </div>
      {/* <DeviceStatus /> */}
    </div>
  );
}
export default ParentComponent;
