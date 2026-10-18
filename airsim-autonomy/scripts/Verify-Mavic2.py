"""Short simulated takeoff/hover/landing check; UE4 must already be running."""
import json
import pathlib
import time
import airsim

root = pathlib.Path(__file__).resolve().parents[1]
out = root / 'artifacts' / 'mavic2'
client = airsim.MultirotorClient(timeout_value=30)
client.confirmConnection()
name = 'MavicSim'
assert name in client.listVehicles()

def state():
    s = client.getMultirotorState(vehicle_name=name)
    p = s.kinematics_estimated.position
    return {'landed': s.landed_state, 'position_ned': [p.x_val, p.y_val, p.z_val]}

report = {'before': state()}
assert report['before']['landed'] == airsim.LandedState.Landed
client.enableApiControl(True, vehicle_name=name)
assert client.armDisarm(True, vehicle_name=name)
try:
    client.takeoffAsync(timeout_sec=20, vehicle_name=name).join()
    client.hoverAsync(vehicle_name=name).join()
    time.sleep(2)
    report['hover'] = state()
    assert report['hover']['landed'] == airsim.LandedState.Flying
    assert report['before']['position_ned'][2] - report['hover']['position_ned'][2] > 0.5
    image = client.simGetImages([airsim.ImageRequest('0', airsim.ImageType.Scene, False, True)], vehicle_name=name)[0]
    assert image.width == 640 and image.height == 480 and image.image_data_uint8
    (out / 'front-camera-hover.png').write_bytes(image.image_data_uint8)
    report['camera'] = {'width': image.width, 'height': image.height}
    client.simRunConsoleCommand('HighResShot 1')
    time.sleep(1)
finally:
    client.landAsync(timeout_sec=30, vehicle_name=name).join()
    report['after'] = state()
    if report['after']['landed'] == airsim.LandedState.Landed:
        client.armDisarm(False, vehicle_name=name)
        client.enableApiControl(False, vehicle_name=name)
    (out / 'flight-check.json').write_text(json.dumps(report, indent=2))
assert report['after']['landed'] == airsim.LandedState.Landed
print(json.dumps(report, indent=2))
