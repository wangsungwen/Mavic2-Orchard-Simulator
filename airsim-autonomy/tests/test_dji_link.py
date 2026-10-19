import json
import math
from pathlib import Path
import socket
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dji_link import StatusClient, LinkError, assess


class LinkTests(unittest.TestCase):
    def exchange(self, response):
        server = socket.socket()
        server.bind(('127.0.0.1', 0))
        server.listen(1)
        self.addCleanup(server.close)
        captured = []
        def peer():
            conn, _ = server.accept()
            with conn:
                captured.append(json.loads(conn.makefile('rb').readline()))
                conn.sendall(response)
        worker = threading.Thread(target=peer, daemon=True)
        worker.start()
        client = StatusClient('127.0.0.1', '001234', server.getsockname()[1])
        return client, worker, captured

    def test_only_status_wire_request(self):
        client, worker, captured = self.exchange(b'{"ok":true,"status":{"fresh":true}}\n')
        self.assertEqual(client.read_status(), {'fresh': True})
        worker.join(2)
        self.assertEqual(captured, [{'command':'status', 'token':'001234'}])
        self.assertFalse(hasattr(client, 'request'))

    def test_rejects_errors_without_echoing_token(self):
        client, worker, _ = self.exchange(b'{"ok":false,"error":"001234"}\n')
        with self.assertRaises(LinkError) as error:
            client.read_status()
        self.assertNotIn('001234', str(error.exception))
        worker.join(2)

    def test_bad_or_truncated_protocol(self):
        for reply in [b'bad\n', b'[]\n', b'{"ok":true}\n', b'{"ok":1,"status":{}}\n', b'{}']:
            with self.subTest(reply=reply):
                client, worker, _ = self.exchange(reply)
                with self.assertRaises(LinkError):
                    client.read_status()
                worker.join(2)

    def test_codes(self):
        for code in ['', '12345', '1234567', '１２３４５６', '123 45']:
            with self.assertRaises(ValueError):
                StatusClient('localhost', code)

    def test_never_infers_position_or_navigation_permission(self):
        for sim in (True, False, None):
            result = assess({'fresh':True, 'telemetryAgeMs':100, 'simulatorActive':sim,
                             'ue4Pose':{'northM':123}, 'satellites':30})
            self.assertFalse(result['indoor_auto_ready'])
            self.assertFalse(result['outdoor_auto_ready'])
            self.assertIn('UNKNOWN', result['position'])
        self.assertIn('DJI_SIMULATOR', assess({'fresh':True,'telemetryAgeMs':0,'simulatorActive':True})['source'])
        self.assertIn('DJI_FLIGHT_CONTROLLER', assess({'fresh':True,'telemetryAgeMs':0,'simulatorActive':False})['source'])

    def test_stale_and_invalid_ages(self):
        for age in (-1, 2001, True, '0', None, math.nan, math.inf):
            self.assertFalse(assess({'fresh':True,'telemetryAgeMs':age})['fresh'])
        for elapsed in (-1, 2, math.nan):
            self.assertFalse(assess({'fresh':True,'telemetryAgeMs':0}, elapsed)['fresh'])
        self.assertFalse(assess({'fresh':True,'telemetryAgeMs':1500}, .6)['fresh'])
        self.assertFalse(assess({'fresh':'true','telemetryAgeMs':0})['fresh'])


if __name__ == '__main__':
    unittest.main()
