import matplotlib.pyplot as plt
import numpy as np
import math

def GetLanePlane(p1, p2, width):
    x1, y1, z1 = p1[0], p1[1], p1[2]
    x2, y2, z2 = p2[0], p2[1], p2[2]

    m = (y2 - y1) / (x2 - x1)
    r = width / 2
    a = x1 * x1 - (m * m * r * r) / (m * m + 1)
    ax = (2 * x1 + math.sqrt(4 * x1 * x1 - 4 * a)) / 2
    bx = (2 * x1 - math.sqrt(4 * x1 * x1 - 4 * a)) / 2
    ay = (-1 / m) * ax + y1 + x1 / m
    by = (-1 / m) * bx + y1 + x1 / m

    s1 = np.array([ax, ay, z1])
    s2 = np.array([bx, by, z1])
    e1 = np.array([ax + (x2 - x1), ay + (y2 - y1), z2])
    e2 = np.array([bx + (x2 - x1), by + (y2 - y1), z2])

    return s1, s2, e1, e2


def draw_point(p1, str_text, text_left=False):
    plt.gca().plot(p1[0], p1[1], marker='D', color='b')
    
    if text_left:
        text_pos_offset = -0.2
    else:
        text_pos_offset = 0.2
    plt.gca().text(p1[0]+text_pos_offset, p1[1], str_text)


def draw_lane_plane(s1, s2, e1, e2):
    lane_plane = np.vstack([s1, e1, e2, s2, s1])
    plt.plot(lane_plane[:,0], lane_plane[:,1],
        linestyle='-',
        linewidth=1)

    draw_point(s1, 's1')
    draw_point(s2, 's2')
    draw_point(e1, 'e1')
    draw_point(e2, 'e2', False)


plt.figure()

p1 = np.array([5,5,0])
p2 = np.array([10,10,0])
width = 2**(1.5)
lane_line = np.vstack([p1, p2])


plt.plot(lane_line[:,0], lane_line[:,1],
    linestyle='--',
    linewidth=1,
    color='k',
    marker='o')
plt.gca().text(p1[0]+0.2, p1[1], 'p1')
plt.gca().text(p2[0]+0.2, p2[1], 'p2')


s1, s2, e1, e2 = GetLanePlane(p1, p2, width)
draw_lane_plane(s1, s2, e1, e2)


plt.gca().axis('equal')
plt.show()