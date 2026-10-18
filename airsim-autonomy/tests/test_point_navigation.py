import math
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from point_navigation import Navigator, target_from_command


def state(n=0, e=0, z=.919, landed=0):
    return SimpleNamespace(landed_state=landed, kinematics_estimated=SimpleNamespace(
        position=SimpleNamespace(x_val=n, y_val=e, z_val=z)))


class PointNavigationTests(unittest.TestCase):
    def test_height_relative_to_settled_body(self):
        self.assertEqual(target_from_command(dict(north=2, east=3, height=2), .919), (2, 3, -1.081))

    def test_invalid_targets(self):
        for data in [dict(north=math.nan, east=0, height=2), dict(north=21, east=0, height=2),
                     dict(north=0, east=0, height=0), dict(north=True, east=0, height=2)]:
            with self.assertRaises(ValueError):
                target_from_command(data, .919)

    def make_nav(self):
        c = Mock()
        c.getMultirotorState.return_value = state()
        c.simGetCollisionInfo.return_value = SimpleNamespace(time_stamp=1, has_collided=False)
        return c, Navigator(c, Mock())

    def test_full_sequence_and_no_automatic_land(self):
        c, nav = self.make_nav()
        nav.command(dict(action='go', north=3, east=2, height=2))
        self.assertEqual(nav.phase, 'takeoff')
        c.getMultirotorState.return_value = state(z=-.6, landed=1)
        nav.tick()
        self.assertEqual(nav.phase, 'height')
        c.getMultirotorState.return_value = state(z=-1.081, landed=1)
        nav.tick()
        self.assertEqual(nav.phase, 'moving')
        c.getMultirotorState.return_value = state(n=3, e=2, z=-1.081, landed=1)
        nav.tick()
        self.assertEqual(nav.phase, 'idle')
        c.hoverAsync.assert_called_once()
        c.landAsync.assert_not_called()

    def test_busy_does_not_replace_target(self):
        c, nav = self.make_nav()
        nav.command(dict(action='go', north=3, east=2, height=2))
        nav.command(dict(action='go', north=9, east=9, height=3))
        self.assertEqual(nav.target[:2], (3, 2))
        c.takeoffAsync.assert_called_once()

    def test_stop_in_air_never_disarms(self):
        c, nav = self.make_nav()
        nav.controlled = True
        c.getMultirotorState.return_value = state(z=-1, landed=1)
        nav.command(dict(action='stop'))
        c.cancelLastTask.assert_called_once()
        c.hoverAsync.assert_called_once()
        c.armDisarm.assert_not_called()

    def test_collision_is_detected(self):
        c, nav = self.make_nav()
        nav.command(dict(action='go', north=3, east=2, height=2))
        c.simGetCollisionInfo.return_value = SimpleNamespace(time_stamp=2, has_collided=True)
        with self.assertRaisesRegex(RuntimeError, 'Collision'):
            nav.tick()


if __name__ == '__main__':
    unittest.main()
