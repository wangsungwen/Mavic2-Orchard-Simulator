"""UE4 mouse targets -> localhost AirSim only. Never connects to DJI."""
import argparse
import json
import math
from pathlib import Path
import socket
import subprocess
import time
import uuid
import sys

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
VEHICLE = "MavicSim"


def position(state):
    p = state.kinematics_estimated.position
    return p.x_val, p.y_val, p.z_val


def target_from_command(command, ground_z):
    values = [command[key] for key in ("north", "east", "height")]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError("Target must contain finite numbers")
    n, e, height = values
    if math.hypot(n, e) > 20 or not 1 <= height <= 10:
        raise ValueError("Target outside limit: radius 20 m, height 1..10 m")
    return n, e, ground_z - height


class Navigator:
    def __init__(self, client, report, clock=time.monotonic):
        self.c, self.report, self.clock = client, report, clock
        state = client.getMultirotorState(vehicle_name=VEHICLE)
        if state.landed_state != 0 or math.dist(position(state), (0, 0, 0)) > 2:
            raise RuntimeError("Start a fresh scene, landed near spawn")
        self.ground_z = position(state)[2]
        self.phase = "idle"
        self.controlled = False
        self.collision = client.simGetCollisionInfo(vehicle_name=VEHICLE).time_stamp
        self.report("READY: select XY, set height, press Enter. No automatic landing.")

    def stop(self, reason):
        self.phase = "idle"
        if self.controlled:
            self.c.cancelLastTask(vehicle_name=VEHICLE)
            state = self.c.getMultirotorState(vehicle_name=VEHICLE)
            if state.landed_state != 0:
                self.c.hoverAsync(vehicle_name=VEHICLE)
            else:
                self.c.armDisarm(False, vehicle_name=VEHICLE)
        self.report(reason)

    def command(self, command):
        if command.get("action") == "stop":
            self.stop("CANCELLED: hover requested; check scene")
            return
        if command.get("action") != "go":
            raise ValueError("Unknown action")
        if self.phase != "idle":
            self.report("BUSY: target ignored. X to stop first.")
            return
        self.target = target_from_command(command, self.ground_z)
        state = self.c.getMultirotorState(vehicle_name=VEHICLE)
        self.c.enableApiControl(True, vehicle_name=VEHICLE)
        self.controlled = True
        if not self.c.isApiControlEnabled(vehicle_name=VEHICLE):
            raise RuntimeError("API control rejected")
        if state.landed_state == 0:
            if not self.c.armDisarm(True, vehicle_name=VEHICLE):
                raise RuntimeError("Arming rejected")
            self.start_z = position(state)[2]
            self.c.takeoffAsync(timeout_sec=20, vehicle_name=VEHICLE)
            self.phase, self.deadline = "takeoff", self.clock() + 25
            self.report("TAKEOFF: climbing relative to starting position")
        else:
            self.climb(state)

    def move(self, target, phase):
        current = position(self.c.getMultirotorState(vehicle_name=VEHICLE))
        timeout = max(20, math.dist(current, target) / .5 * 3 + 10)
        self.c.moveToPositionAsync(*target, .5, timeout_sec=timeout, vehicle_name=VEHICLE)
        self.phase, self.deadline, self.segment = phase, self.clock() + timeout, target
        self.report(f"{phase.upper()}: N={target[0]:.2f} E={target[1]:.2f} D={target[2]:.2f}; speed 0.5 m/s")

    def climb(self, state):
        n, e, _ = position(state)
        self.move((n, e, self.target[2]), "height")

    def tick(self):
        if self.phase == "idle":
            return
        state = self.c.getMultirotorState(vehicle_name=VEHICLE)
        p = position(state)
        hit = self.c.simGetCollisionInfo(vehicle_name=VEHICLE)
        if not all(math.isfinite(v) for v in p) or math.hypot(*p[:2]) > 22 or p[2] < self.ground_z - 12:
            raise RuntimeError("Position invalid or simulation boundary exceeded")
        if hit.has_collided and hit.time_stamp != self.collision:
            raise RuntimeError("Collision detected; no automatic obstacle avoidance")
        if self.clock() > self.deadline:
            raise TimeoutError(f"{self.phase} timed out")
        if self.phase == "takeoff":
            if state.landed_state != 0 and self.start_z - p[2] >= 1:
                self.climb(state)
        elif math.dist(p, self.segment) <= .75:
            if self.phase == "height":
                self.move(self.target, "moving")
            else:
                self.c.hoverAsync(vehicle_name=VEHICLE)
                self.phase = "idle"
                self.report("ARRIVED within 0.75 m: hover requested. Select next target or X.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, default=Path("C:/Program Files/Epic Games/UE_4.27/Engine/Binaries/Win64/UE4Editor.exe"))
    parser.add_argument("--simulator", type=Path, help="Packaged game executable; no UE4 editor required")
    parser.add_argument("--scene", choices=("Blocks", "Orchard"), default="Blocks")
    parser.add_argument("--self-test", action="store_true", help="Check bundled runtime without launching or controlling a scene")
    args = parser.parse_args()
    if args.self_test:
        import airsim
        import numpy
        print("Runtime OK; AirSim import OK; numpy " + numpy.__version__)
        print("Bundle root: " + str(ROOT))
        return
    try:
        with socket.create_connection(("127.0.0.1", 41451), timeout=.5):
            raise RuntimeError("Close the existing UE4 / AirSim scene first (port 41451 in use)")
    except (ConnectionRefusedError, socket.timeout):
        pass
    config_path = ROOT / "config/settings-mavic2.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    vehicle = config["Vehicles"][VEHICLE]
    if (config.get("LocalHostIp") != "127.0.0.1" or config.get("ApiServerPort", 41451) != 41451
            or config.get("SimMode") != "Multirotor" or config.get("ClockSpeed", 1) != 1
            or vehicle.get("VehicleType") != "SimpleFlight"
            or any(vehicle.get(k, 0) != 0 for k in ("X", "Y", "Z"))):
        raise ValueError("Requires local SimpleFlight MavicSim, clock=1, spawn=0")
    session = ROOT / "logs" / ("point-" + uuid.uuid4().hex)
    session.mkdir(parents=True)
    mailbox = session / "command.json"
    status = Path(str(mailbox) + ".status")

    def report(message):
        print(message, flush=True)
        temp = Path(str(status) + ".tmp")
        temp.write_text(message, encoding="utf-8")
        for attempt in range(10):
            try:
                temp.replace(status)
                break
            except PermissionError:
                time.sleep(.01)  # UE may hold a read handle for one frame.
        with (session / "events.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps({"time": time.time(), "message": message}) + "\n")

    project = ROOT / "vendor/AirSim/Unreal/Environments/Blocks/Blocks.uproject"
    if args.simulator:
        executable = args.simulator.resolve()
        launch = [str(executable)]
        launch_cwd = executable.parent
    else:
        launch = [str(args.engine), str(project), "-game"]
        launch_cwd = project.parent
    if args.scene == "Orchard":
        launch.append("/Game/Orchard/Maps/Orchard_Hillside")
    proc = subprocess.Popen(launch + ["-windowed", "-ResX=1280", "-ResY=720",
        "-nosplash", f"-settings={config_path}", "-PointNavigation", f"-NavMailbox={mailbox}"], cwd=str(launch_cwd))
    import airsim
    client = airsim.MultirotorClient(ip="127.0.0.1", port=41451, timeout_value=3)
    nav = None
    try:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline and proc.poll() is None:
            try:
                with socket.create_connection(("127.0.0.1", 41451), timeout=.3):
                    break
            except OSError:
                time.sleep(.3)
        else:
            raise RuntimeError("UE4 did not start AirSim within 90 seconds")
        client.confirmConnection()
        if VEHICLE not in client.listVehicles():
            raise RuntimeError("MavicSim missing")
        time.sleep(2)  # Allow the body to settle before capturing the height datum.
        nav = Navigator(client, report)
        sequence = 0
        while proc.poll() is None:
            try:
                if mailbox.exists():
                    command = json.loads(mailbox.read_text(encoding="utf-8-sig"))
                    new_sequence = command.get("sequence", 0)
                    if isinstance(new_sequence, int) and new_sequence > sequence:
                        sequence = new_sequence
                        report("COMMAND: " + json.dumps(command))
                        nav.command(command)
                nav.tick()
            except (ValueError, TimeoutError, RuntimeError) as exc:
                nav.stop("STOPPED: " + str(exc))
            time.sleep(.1)
    finally:
        if nav and proc.poll() is None:
            nav.stop("Bridge stopped: hover requested; restart bridge and scene for another session")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
    except Exception as error:
        raise SystemExit(str(error))
