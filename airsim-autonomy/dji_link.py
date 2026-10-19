"""Read-only adapter for Mavic Dual Joystick Android 1.0.8 status protocol.

No aircraft command method is exposed. Indoor XY is deliberately unavailable.
"""
import json
import math
import socket
import time


class LinkError(RuntimeError):
    pass


class StatusClient:
    def __init__(self, host, token, port=8865, timeout=1.0):
        if not host or not host.strip():
            raise ValueError('請填入控制器 IP，USB 使用 127.0.0.1')
        if len(token) != 6 or not token.isascii() or not token.isdigit():
            raise ValueError('驗證碼必須為 APP 顯示的六位數字（保留開頭的 0）')
        self.host, self.token, self.port, self.timeout = host.strip(), token, port, timeout

    def read_status(self):
        # Fixed command: callers cannot inject takeoff, mode changes or sticks.
        request = json.dumps({'command': 'status', 'token': self.token}).encode() + b'\n'
        with socket.create_connection((self.host, self.port), self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(request)
            response = bytearray()
            deadline = time.monotonic() + self.timeout
            while len(response) < 65536:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise LinkError('APP 回覆逾時')
                sock.settimeout(remaining)
                data = sock.recv(min(4096, 65536 - len(response)))
                if not data:
                    raise LinkError('APP 提前關閉連線')
                response.extend(data)
                if b'\n' in response:
                    break
            else:
                raise LinkError('APP 回覆超過大小限制')
        try:
            reply = json.loads(response.split(b'\n', 1)[0],
                               parse_constant=lambda value: None)
        except (ValueError, UnicodeError):
            raise LinkError('APP 回覆不是有效 JSON') from None
        if not isinstance(reply, dict) or reply.get('ok') is not True:
            # Do not echo arbitrary server text: it could contain credentials.
            raise LinkError('APP 拒絕讀取；請核對當次驗證碼，錯誤多次需等候 30 秒')
        status = reply.get('status')
        if not isinstance(status, dict):
            raise LinkError('APP 回覆缺少 status')
        return status


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def assess(status, elapsed=0):
    """Conservative display state; never a flight authorization decision."""
    age = status.get('telemetryAgeMs')
    fresh = (status.get('fresh') is True and number(age) and 0 <= age <= 2000
             and number(elapsed) and 0 <= elapsed <= 1.5
             and age + elapsed * 1000 <= 2000)
    simulated = status.get('simulatorActive')
    if not fresh:
        source = 'STALE / 尚無新鮮飛控遙測'
    elif simulated is True:
        source = 'DJI_SIMULATOR / DJI 內建模擬器'
    elif simulated is False:
        source = 'DJI_FLIGHT_CONTROLLER / 非模擬器遙測'
    else:
        source = 'UNKNOWN / 資料來源未確認'
    return {'source': source, 'fresh': fresh,
            'indoor_auto_ready': False, 'outdoor_auto_ready': False,
            'reason': '室內無已校準定位；戶外 GPS 航點橋接尚未實作',
            'position': 'UNKNOWN — 不以 AirSim 或速度積分代替真機 XY'}
