import io
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mission import Point, offset, validate, load, ned
from fly import Flight

HOME = (25.0, 121.0)


class Routes(unittest.TestCase):
    def test_ned_axes(self):
        n, e, d = ned(offset(HOME, 12, 20, 10), HOME)
        self.assertAlmostEqual(n, 12, places=5)
        self.assertAlmostEqual(e, 20, places=5)
        self.assertEqual(d, -10)

    def test_valid_route(self):
        self.assertEqual(len(validate([offset(HOME, 5, 0, 10), offset(HOME, 5, 15, 10)], HOME)), 2)

    def test_invalid_values(self):
        for p in [Point(math.nan, 121, 10), Point(25, math.inf, 10), Point(25, 121, math.nan),
                  Point(25, 121, 4), Point(25, 121, 31), Point(91, 121, 10)]:
            with self.subTest(p=p), self.assertRaises(ValueError):
                validate([offset(HOME, 5, 0, 10), p], HOME)

    def test_distance_rules(self):
        cases = [[(31, 0), (35, 0)], [(5, 0), (101, 0)], [(5, 0), (6, 0)],
                 [(5, 0), (90, 0), (-90, 0), (90, 0), (-90, 0)]]
        for pairs in cases:
            with self.subTest(pairs=pairs), self.assertRaises(ValueError):
                validate([offset(HOME, n, e, 10) for n, e in pairs], HOME)

    def test_count(self):
        for count in (1, 21):
            with self.assertRaises(ValueError):
                validate([offset(HOME, i * 2, 0, 10) for i in range(count)], HOME)

    def test_existing_parser_and_fence(self):
        with tempfile.TemporaryDirectory() as tmp:
            route, fence = Path(tmp) / 'route.csv', Path(tmp) / 'fence.json'
            points = [offset(HOME, 5, 0, 10), offset(HOME, 20, 0, 10)]
            route.write_text('\ufeff# test\n' + '\n'.join(f'{p.lat},{p.lon},{p.alt}' for p in points), encoding='utf-8')
            self.assertEqual(len(load(route, HOME)), 2)
            obstacle = offset(HOME, 10, 0, 10)
            fence.write_text(json.dumps({'zones': [{'name': 'wall', 'lat': obstacle.lat, 'lon': obstacle.lon, 'radiusM': 4}]}))
            with self.assertRaises(ValueError):
                load(route, HOME, fences=fence)
            with self.assertRaises(ValueError):
                load(route, HOME, terrain='unused.csv')


class FakeClient:
    def __init__(self):
        self.pos, self.landed, self.api = (0, 0, 0), 0, False
        self.hit, self.stamp, self.fail_move, self.arm_ok = False, 0, False, True
        self.calls = []

    def getMultirotorState(self, **kwargs):
        return NS(kinematics_estimated=NS(position=NS(x_val=self.pos[0], y_val=self.pos[1], z_val=self.pos[2])),
                  landed_state=self.landed, timestamp=1)

    def simGetCollisionInfo(self, **kwargs):
        return NS(has_collided=self.hit, time_stamp=self.stamp)

    def enableApiControl(self, enable, **kwargs):
        self.api = enable
        self.calls.append(('api', enable))

    def isApiControlEnabled(self, **kwargs):
        return self.api

    def armDisarm(self, armed, **kwargs):
        self.calls.append(('arm', armed))
        return self.arm_ok if armed else True

    def takeoffAsync(self, **kwargs):
        self.calls.append(('takeoff',))
        self.pos, self.landed = (0, 0, -2), 1

    def moveToPositionAsync(self, x, y, z, speed, **kwargs):
        if self.fail_move:
            raise RuntimeError('RPC failure')
        self.pos = (x, y, z)

    def landAsync(self, **kwargs):
        self.calls.append(('land',))
        self.landed, self.pos = 0, (0, 0, 0)

    def cancelLastTask(self, **kwargs):
        self.calls.append(('cancel',))

    def hoverAsync(self, **kwargs):
        self.calls.append(('hover',))


class Control(unittest.TestCase):
    def setUp(self):
        self.c, self.log = FakeClient(), io.StringIO()
        self.f = Flight(self.c, 'MavicSim', self.log)

    def test_success_lands_and_releases(self):
        self.f.run([(5, 0, -10), (5, 15, -10)], 1)
        self.assertFalse(self.c.api)
        self.assertIn(('arm', False), self.c.calls)
        self.assertIn('"phase": "complete"', self.log.getvalue())

    def test_takeoff_relative_to_settled_ground(self):
        # Reproduce UE4's +0.91m settled ground and -0.63m takeoff hover.
        self.c.pos = (0, 0, 0.91)
        def takeoff(**kwargs):
            self.c.calls.append(('takeoff',))
            self.c.pos, self.c.landed = (0, 0, -0.63), 1
        self.c.takeoffAsync = takeoff
        ticks = iter(range(1000))
        self.f.clock = lambda: next(ticks)
        self.f.sleep = lambda _: None
        self.f.run([(5, 0, -10), (5, 15, -10)], 1)
        self.assertIn('"phase": "complete"', self.log.getvalue())

    def test_takeoff_does_not_accept_airborne_flag_without_climb(self):
        self.c.pos = (0, 0, -1.5)
        def takeoff(**kwargs):
            self.c.landed = 1  # Already below -1 NED, but has not climbed.
        self.c.takeoffAsync = takeoff
        ticks = iter(range(1000))
        self.f.clock = lambda: next(ticks)
        self.f.sleep = lambda _: None
        with self.assertRaisesRegex(TimeoutError, 'takeoff'):
            self.f.run([(5, 0, -10)], 1)
        self.assertIn(('hover',), self.c.calls)
        self.assertNotIn(('arm', False), self.c.calls)

    def test_rpc_failure_hovers_without_disarming_airborne(self):
        self.c.fail_move = True
        with self.assertRaises(RuntimeError):
            self.f.run([(5, 0, -10), (5, 15, -10)], 1)
        self.assertIn(('hover',), self.c.calls)
        self.assertNotIn(('arm', False), self.c.calls)
        self.assertTrue(self.c.api)
        self.assertNotIn('"phase": "complete"', self.log.getvalue())

    def test_arm_failure_cleans_up_on_ground(self):
        self.c.arm_ok = False
        with self.assertRaises(RuntimeError):
            self.f.run([(5, 0, -10)], 1)
        self.assertNotIn(('takeoff',), self.c.calls)
        self.assertFalse(self.c.api)

    def test_collision_and_geofence(self):
        self.c.hit, self.c.stamp = True, 123
        with self.assertRaisesRegex(RuntimeError, 'Collision'):
            self.f.wait(lambda s: True, 1, 'test')
        self.c.hit, self.c.pos = False, (106, 0, -10)
        with self.assertRaisesRegex(RuntimeError, 'geofence'):
            self.f.wait(lambda s: True, 1, 'test')

    def test_timeout(self):
        ticks = iter([0, 0.5, 2])
        self.f.clock = lambda: next(ticks)
        self.f.sleep = lambda t: None
        with self.assertRaises(TimeoutError):
            self.f.wait(lambda s: False, 1, 'test')

    def test_refuse_airborne_start(self):
        self.c.landed = 1
        with self.assertRaises(RuntimeError):
            self.f.run([(5, 0, -10)], 1)
        self.assertFalse(self.c.calls)

    def test_landing_timeout_does_not_disarm(self):
        self.c.landed, self.c.pos = 1, (0, 0, -3)
        self.c.landAsync = lambda **kwargs: None
        ticks = iter([0, 1, 66])
        self.f.clock = lambda: next(ticks)
        self.f.sleep = lambda t: None
        with self.assertRaises(TimeoutError):
            self.f.land()
        self.assertNotIn(('arm', False), self.c.calls)

    def test_interrupt_requests_hover(self):
        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt()
        self.c.moveToPositionAsync = interrupted
        with self.assertRaises(KeyboardInterrupt):
            self.f.run([(5, 0, -10), (5, 15, -10)], 1)
        self.assertIn(('cancel',), self.c.calls)
        self.assertIn(('hover',), self.c.calls)
        self.assertNotIn(('arm', False), self.c.calls)


if __name__ == '__main__':
    unittest.main()
