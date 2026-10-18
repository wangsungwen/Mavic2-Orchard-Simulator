"""Validate a relocated orchard bundle via its command mailbox, not desktop input."""
import argparse
import json
import math
from pathlib import Path
import socket
import subprocess
import time
import airsim

ap = argparse.ArgumentParser()
ap.add_argument('bundle', type=Path)
a = ap.parse_args()
root = a.bundle.resolve()
out = Path(__file__).resolve().parents[1] / 'artifacts/orchard-portable-check'
out.mkdir(parents=True, exist_ok=True)
try:
    with socket.create_connection(('127.0.0.1', 41451), timeout=.3):
        raise SystemExit('Existing simulator: close it first')
except (ConnectionRefusedError, socket.timeout):
    pass
process = subprocess.Popen([str(root/'Controller/Mavic2Navigation.exe'), '--scene', 'Orchard',
    '--simulator', str(root/'Simulator/Blocks/Binaries/Win64/Blocks.exe')], cwd=str(root))
client = airsim.MultirotorClient(timeout_value=5)
connected = False
report = {'bundle': str(root), 'method': 'packaged controller + mailbox; no UI click injection'}
try:
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(('127.0.0.1', 41451), timeout=.3):
                break
        except OSError:
            if process.poll() is not None:
                raise RuntimeError('Packaged controller exited')
            time.sleep(.3)
    else:
        raise TimeoutError('Simulator startup')
    connected = True
    client.confirmConnection()
    session = max((root/'Controller/logs').glob('point-*'), key=lambda p:p.stat().st_mtime)
    events = session/'events.jsonl'
    def wait_for(text, timeout=45):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            content = events.read_text(encoding='utf-8') if events.exists() else ''
            if 'STOPPED:' in content:
                raise RuntimeError(content)
            if text in content:
                return
            time.sleep(.2)
        raise TimeoutError(text)
    wait_for('READY')
    names = client.simListSceneObjects('.*[Mm]acaque.*')
    assert len(names) == 4, names
    def pos(name):
        p = client.simGetObjectPose(name).position
        return (p.x_val, p.y_val, p.z_val)
    initial = {n:pos(n) for n in names}
    time.sleep(6)
    report['macaque_movement_m'] = {n:math.dist(initial[n], pos(n)) for n in names}
    assert all(v>.1 for v in report['macaque_movement_m'].values())
    client.simSetCameraPose('0', airsim.Pose(airsim.Vector3r(-9,-12,-27), airsim.to_quaternion(-.4,0,.25)), vehicle_name='MavicSim')
    time.sleep(.5)
    data = client.simGetImage('0', airsim.ImageType.Scene, vehicle_name='MavicSim')
    assert data
    (out/'overview.png').write_bytes(data)
    client.simSetCameraPose('0', airsim.Pose(airsim.Vector3r(.12,0,-.01), airsim.to_quaternion(0,0,0)), vehicle_name='MavicSim')
    def command(seq, action, **fields):
        temp = session/'validation.tmp'
        temp.write_text(json.dumps(dict(sequence=seq, action=action, **fields)), encoding='utf-8')
        temp.replace(session/'command.json')
    command(1,'go',north=2,east=2,height=3)
    wait_for('ARRIVED')
    p = client.getMultirotorState(vehicle_name='MavicSim').kinematics_estimated.position
    report['arrived_ned'] = [p.x_val,p.y_val,p.z_val]
    command(2,'go',north=2,east=-3,height=3)
    time.sleep(2)
    command(3,'stop')
    wait_for('CANCELLED')
    time.sleep(3)
    report['stop_speed_m_s'] = client.getMultirotorState(vehicle_name='MavicSim').kinematics_estimated.linear_velocity.get_length()
    assert report['stop_speed_m_s'] < .2
    report['passed'] = True
    (out/'events.jsonl').write_text(events.read_text(encoding='utf-8'), encoding='utf-8')
finally:
    (out/'result.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    if connected:
        client.simRunConsoleCommand('quit')
print(json.dumps(report, indent=2, ensure_ascii=False))
