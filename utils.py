import math


def distance(x1, y1, x2, y2):
    """Straight-line distance between two points."""
    return math.hypot(x2 - x1, y2 - y1)


def angle_to(x1, y1, x2, y2):
    """Direction (radians) pointing from point 1 toward point 2.
    math.atan2 turns an x/y offset into an angle."""
    return math.atan2(y2 - y1, x2 - x1)


def angle_difference(from_angle, to_angle):
    """The smallest turn from one angle to another, between -pi and pi.
    The sign says which way to turn; the size is never more than half a
    circle, so players always turn the short way round."""
    diff = (to_angle - from_angle) % (2 * math.pi)  # now 0 .. 2*pi
    if diff > math.pi:
        diff -= 2 * math.pi                         # now -pi .. pi
    return diff
