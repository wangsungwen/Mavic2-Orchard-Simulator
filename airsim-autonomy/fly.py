"""Local AirSim-only mission runner. No DJI transport or Android commands."""
import argparse
import json
import math
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from mission import ROOT, load, offset, coordinate, distance


def xyz(state):
    p = state.kinematics_estimated.position
    return p.x_val, p.y_val, p.z_val


class Flight:
    def __init__(self, client, vehicle, log, landed_value=0, clock=time.monotonic, sleep=time.sleep):
        self.c, self.v, self.log = client, vehicle, log
        self.landed_value, self.clock, self.sleep = landed_value, clock, sleep
        self.collision_stamp = client.simGetCollisionInfo(vehicle_name=vehicle).time_stamp

    def event(self, **values):
        self.log.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), **values}) + "\n")
        self.log.flush()

    def wait(self, predicate, timeout, phase, collision=True):
        deadline = self.clock() + timeout
        while self.clock() < deadline:
            state = self.c.getMultirotorState(vehicle_name=self.v)
            pos = xyz(state)
            hit = self.c.simGetCollisionInfo(vehicle_name=self.v)
            self.event(phase=phase, ned=pos, collision=hit.has_collided, sim_timestamp=state.timestamp)
            if not all(math.isfinite(x) for x in pos):
                raise RuntimeError("Non-finite position")
            if math.hypot(*pos[:2]) > 105 or pos[2] < -32:
                raise RuntimeError("Simulation geofence exceeded")
            if collision and hit.has_collided and hit.time_stamp != self.collision_stamp:
                raise RuntimeError("Collision detected")
            if predicate(state):
                return state
            self.sleep(0.2)
        raise TimeoutError(f"{phase}: timed out after {timeout:.1f}s")

    def move(self, target, speed, phase):
        current = xyz(self.c.getMultirotorState(vehicle_name=self.v))
        timeout = max(20, math.dist(current, target) / speed * 3 + 10)
        self.c.moveToPositionAsync(*target, speed, timeout_sec=timeout, vehicle_name=self.v)
        self.wait(lambda s: math.dist(xyz(s), target) <= 0.75, timeout, phase)

    def land(self):
        self.c.landAsync(timeout_sec=60, vehicle_name=self.v)
        # Ground contact is expected while landing; still log collision data.
        self.wait(lambda s: s.landed_state == self.landed_value, 65, "landing", collision=False)
        if not self.c.armDisarm(False, vehicle_name=self.v):
            raise RuntimeError("Disarm rejected")
        self.c.enableApiControl(False, vehicle_name=self.v)
        self.event(phase="landed")

    def run(self, targets, speed):
        state = self.c.getMultirotorState(vehicle_name=self.v)
        if state.landed_state != self.landed_value or math.dist(xyz(state), (0, 0, 0)) > 2:
            raise RuntimeError(
                f"Start a fresh scene: vehicle must be landed near spawn "
                f"(landed_state={state.landed_state}, NED={xyz(state)}). "
                "Stop and restart the simulator before retrying; an airborne vehicle cannot start a new mission.")
        # SimpleFlight takeoff climbs relative to the current position, while
        # NED zero is established at spawn and can be above the settled ground.
        takeoff_start_z = xyz(state)[2]
        controlled = False
        try:
            self.c.enableApiControl(True, vehicle_name=self.v)
            controlled = True
            if not self.c.isApiControlEnabled(vehicle_name=self.v):
                raise RuntimeError("API control rejected")
            if not self.c.armDisarm(True, vehicle_name=self.v):
                raise RuntimeError("Arming rejected")
            self.event(phase="takeoff-reference", start_ned_z=takeoff_start_z,
                       required_climb_m=1.0)
            self.c.takeoffAsync(timeout_sec=20, vehicle_name=self.v)
            self.wait(lambda s: s.landed_state != self.landed_value
                      and takeoff_start_z - xyz(s)[2] >= 1.0, 25, "takeoff")
            self.move((0, 0, targets[0][2]), speed, "climb")
            for i, target in enumerate(targets, 1):
                print(f"Waypoint {i}/{len(targets)} NED={target}", flush=True)
                self.move(target, speed, f"waypoint-{i}")
            self.move((0, 0, targets[-1][2]), speed, "return")
            self.land()
            self.event(phase="complete")
        except BaseException as exc:
            self.event(phase="failed", error=str(exc))
            if controlled:
                try:
                    self.c.cancelLastTask(vehicle_name=self.v)
                    state = self.c.getMultirotorState(vehicle_name=self.v)
                    if state.landed_state == self.landed_value:
                        self.c.armDisarm(False, vehicle_name=self.v)
                        self.c.enableApiControl(False, vehicle_name=self.v)
                    else:
                        self.c.hoverAsync(vehicle_name=self.v)
                        self.event(phase="hover-requested", note="API control retained; use land command or restart scene")
                except Exception as cleanup:
                    self.event(phase="recovery-failed", error=str(cleanup))
            raise


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["generate", "check", "status", "fly", "land", "image"])
    ap.add_argument("--route", type=Path, default=ROOT / "routes/square.csv")
    ap.add_argument("--settings", type=Path, default=ROOT / "config/settings.json")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--fences", type=Path)
    ap.add_argument("--terrain", type=Path)
    ap.add_argument("--home-elevation", type=float)
    a = ap.parse_args(argv)
    config = json.loads(a.settings.read_text(encoding="utf-8-sig"))
    vehicle_config = config.get("Vehicles", {}).get("MavicSim", {})
    if (config.get("SimMode") != "Multirotor" or config.get("ClockSpeed", 1) != 1
            or config.get("LocalHostIp") != "127.0.0.1" or config.get("ApiServerPort", 41451) != 41451
            or vehicle_config.get("VehicleType") != "SimpleFlight"
            or any(vehicle_config.get(axis, 0) != 0 for axis in ("X", "Y", "Z"))):
        raise ValueError("Use localhost:41451, ClockSpeed=1, MavicSim/SimpleFlight at X/Y/Z=0")
    origin = config["OriginGeopoint"]
    home = (origin["Latitude"], origin["Longitude"])
    if not coordinate(*home) or not math.isfinite(a.speed) or not 0 < a.speed <= 2:
        raise ValueError("Invalid home or speed (0 < speed <= 2 m/s)")
    if a.command == "generate":
        points = [offset(home, n, e, 10) for n, e in [(5, 0), (5, 15), (20, 15), (20, 0)]]
        a.route.parent.mkdir(parents=True, exist_ok=True)
        with a.route.open("x", encoding="utf-8") as out:
            out.write("# AIRSIM SIMULATION ONLY; lat,lon,relative_alt_m\n")
            out.writelines(f"{p.lat:.9f},{p.lon:.9f},{p.alt:.1f}\n" for p in points)
        print(a.route)
        return
    targets = None
    if a.command in ("check", "fly"):
        targets = load(a.route, home, a.fences, a.terrain, a.home_elevation)
        print(json.dumps({"home": home, "ned_waypoints": targets}, indent=2))
        if a.command == "check":
            return
    import airsim
    try:
        with socket.create_connection(("127.0.0.1", 41451), timeout=2):
            pass
    except OSError as error:
        raise RuntimeError("AirSim is not listening on localhost:41451. Run scripts/Start-Simulator.ps1 first.") from error
    c = airsim.MultirotorClient(ip="127.0.0.1", port=41451, timeout_value=10)
    if not c.ping():
        raise RuntimeError("AirSim RPC unavailable")
    vehicle = "MavicSim"
    if vehicle not in c.listVehicles():
        raise RuntimeError("MavicSim missing; launch simulator with supplied settings")
    h = c.getHomeGeoPoint(vehicle_name=vehicle)
    if not coordinate(h.latitude, h.longitude) or distance(*home, h.latitude, h.longitude) > 1:
        raise RuntimeError("Live home differs from settings by >1m; restart scene with matching settings")
    if a.command == "status":
        state = c.getMultirotorState(vehicle_name=vehicle)
        print(json.dumps({"vehicle": vehicle, "home": [h.latitude, h.longitude],
                          "ned": xyz(state), "landed_state": state.landed_state}, indent=2))
        return
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    if a.command == "image":
        data = c.simGetImage("0", airsim.ImageType.Scene, vehicle_name=vehicle)
        if not data:
            raise RuntimeError("Camera returned empty image")
        dest = logs / f"{stamp}.png"
        dest.write_bytes(bytes(data))
        print(dest)
        return
    with (logs / f"{stamp}.jsonl").open("x", encoding="utf-8") as log:
        f = Flight(c, vehicle, log, airsim.LandedState.Landed)
        if a.command == "land":
            c.enableApiControl(True, vehicle_name=vehicle)
            c.cancelLastTask(vehicle_name=vehicle)
            f.land()
        else:
            f.run(targets, a.speed)
    print(f"Completed. Logs: {logs}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted. Only an active flight attempts recovery; check the simulator before using land.", file=sys.stderr)
        sys.exit(130)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
