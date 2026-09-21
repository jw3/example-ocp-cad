import math


def polar(center, r, n):
    points = []
    step = 2 * math.pi / n

    for i in range(n):
        angle = step * i
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        points.append((x, y))

    return points
