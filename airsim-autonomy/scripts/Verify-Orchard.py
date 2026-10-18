"""Run against Start-Orchard.cmd: motion, RGB and short clear-pad flight checks."""
import json
import argparse
import math
import pathlib
import time
import airsim

parser = argparse.ArgumentParser()
parser.add_argument('--scene-only', action='store_true', help='Check animation/alignment and RGB without flying.')
args = parser.parse_args()

OUT = pathlib.Path(__file__).resolve().parents[1] / 'artifacts' / 'orchard'
OUT.mkdir(parents=True, exist_ok=True)
client = airsim.MultirotorClient(timeout_value=30)
client.confirmConnection()
NAME = 'MavicSim'
assert NAME in client.listVehicles()
monkeys = client.simListSceneObjects('.*[Mm]acaque.*')
assert len(monkeys) == 4, monkeys

def position(name):
    p = client.simGetObjectPose(name).position
    assert all(math.isfinite(v) for v in (p.x_val, p.y_val, p.z_val))
    return [p.x_val, p.y_val, p.z_val]

before = {m: position(m) for m in monkeys}
time.sleep(6)
after = {m: position(m) for m in monkeys}
distances = {m: math.dist(before[m], after[m]) for m in monkeys}
assert all(d > 0.1 for d in distances.values()), distances
report = {'macaques': monkeys, 'movement_m_over_6s': distances}
ground_errors = {}
for m, (x, y, z) in after.items():
    # Convert global NED back to original UE map coordinates (PlayerStart).
    ue_x, ue_y, ue_z = x * 100 - 3600, y * 100, 45 - z * 100
    uphill = max(0, ue_x + 2500)
    ground = uphill * .16 + min(uphill / 1500, 1) * 45 * math.sin(ue_x / 1100) * math.cos(ue_y / 1400)
    ground_errors[m] = abs(ue_z - ground - 3) / 100
    assert -2200 < ue_x < 3000 and abs(ue_y) < 3000, (m, ue_x, ue_y)
    assert ground_errors[m] < .05, (m, ground_errors[m])
report['ground_alignment_error_m'] = ground_errors

def capture(filename):
    frame = client.simGetImages([airsim.ImageRequest('0', airsim.ImageType.Scene, False, True)], vehicle_name=NAME)[0]
    assert frame.width == 640 and frame.height == 480 and frame.image_data_uint8
    (OUT / filename).write_bytes(frame.image_data_uint8)

# Camera-only overview; the aircraft stays on the pad.
client.simSetCameraPose('0', airsim.Pose(airsim.Vector3r(-9, -12, -27), airsim.to_quaternion(-0.40, 0, 0.25)), vehicle_name=NAME)
time.sleep(2)
capture('orchard-overview.png')
p = client.simGetObjectPose(monkeys[0]).position
client.simSetCameraPose('0', airsim.Pose(airsim.Vector3r(p.x_val-3, p.y_val-2, p.z_val-1.6), airsim.to_quaternion(-.25, 0, .6)), vehicle_name=NAME)
time.sleep(.5)
capture('macaque-prototype.png')
client.simSetCameraPose('0', airsim.Pose(airsim.Vector3r(.12, 0, -.01), airsim.to_quaternion(0, 0, 0)), vehicle_name=NAME)
if args.scene_only:
    (OUT / 'scene-check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0)

state = client.getMultirotorState(vehicle_name=NAME)
assert state.landed_state == airsim.LandedState.Landed
initial_z = state.kinematics_estimated.position.z_val
client.enableApiControl(True, vehicle_name=NAME)
assert client.armDisarm(True, vehicle_name=NAME)
try:
    client.takeoffAsync(timeout_sec=20, vehicle_name=NAME).join()
    client.moveToZAsync(-5, 1, timeout_sec=20, vehicle_name=NAME).join()
    client.hoverAsync(vehicle_name=NAME).join()
    state = client.getMultirotorState(vehicle_name=NAME)
    report['hover_z_ned_m'] = state.kinematics_estimated.position.z_val
    assert state.landed_state == airsim.LandedState.Flying
    assert initial_z - report['hover_z_ned_m'] > 3
    report['takeoff_hover_passed'] = True
    capture('orchard-drone-camera.png')
finally:
    client.landAsync(timeout_sec=30, vehicle_name=NAME).join()
    state = client.getMultirotorState(vehicle_name=NAME)
    report['landed'] = state.landed_state == airsim.LandedState.Landed
    collision = client.simGetCollisionInfo(vehicle_name=NAME)
    report['ground_contact'] = collision.has_collided
    report['contact_object'] = collision.object_name
    report['final_speed_m_s'] = state.kinematics_estimated.linear_velocity.get_length()
    report['landing_flag_limitation'] = None if report['landed'] else 'Existing SimpleFlight landing-state issue; contact is not a passed landing check.'
    if report['landed']:
        client.armDisarm(False, vehicle_name=NAME)
        client.enableApiControl(False, vehicle_name=NAME)
    (OUT / 'runtime-check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
assert report['landed']
print(json.dumps(report, indent=2))
