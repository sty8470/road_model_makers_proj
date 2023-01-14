import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import numpy as np

from lib.common.logger import Logger


def loadPointList(items, color, size):
    gl_vertex = []
    gl_color = []
    gl_size = size

    for i, item_id in enumerate(items):
        point = items[item_id].point
        gl_vertex.extend(point)
        gl_color.extend(color)

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointer(3, GL_FLOAT, 0, gl_color)
    drawcnt = gl_vertex.size / 3
    glPointSize(gl_size)
    glDrawArrays(GL_POINTS, 0, int(drawcnt))
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()

    return gl_display_list

def loadJunctionList(items, color, size):
    gl_vertex = []
    gl_color = []
    gl_size = size

    for i, item_id in enumerate(items):
        points = items[item_id].get_jc_node_points()
        if points is None:
            Logger.log_error('junction (id = {}) has node points'.format(jc_id))
            continue
        gl_vertex.extend(points)
        gl_color.extend(color*len(points))

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointer(3, GL_FLOAT, 0, gl_color)
    drawcnt = gl_vertex.size / 3
    glPointSize(gl_size)
    glDrawArrays(GL_POINTS, 0, int(drawcnt))
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()

    return gl_display_list

def loadSyncedTLList(items, color, size):
    gl_vertex = []
    gl_color = []
    gl_size = size

    for i, item_id in enumerate(items):
        points = items[item_id].get_synced_signal_points()
        if points is None:
            Logger.log_error('synced_signal (id = {}) has no points'.format(items[item_id].idx))
            continue
        gl_vertex.extend(points)
        gl_color.extend(color*len(points))

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointer(3, GL_FLOAT, 0, gl_color)
    drawcnt = gl_vertex.size / 3
    glPointSize(gl_size)
    glDrawArrays(GL_POINTS, 0, int(drawcnt))
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()

    return gl_display_list


def loadICList(items, color, size):
    gl_vertex = []
    gl_color = []
    gl_size = size

    for i, item_id in enumerate(items):
        points = items[item_id].get_intersection_controller_points()
        if points is None:
            Logger.log_error('intersection_controller (id = {}) has no points'.format(items[item_id].idx))
            continue
        gl_vertex.extend(points)
        gl_color.extend(color*len(points))

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointer(3, GL_FLOAT, 0, gl_color)
    drawcnt = gl_vertex.size / 3
    glPointSize(gl_size)
    glDrawArrays(GL_POINTS, 0, int(drawcnt))
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()

    return gl_display_list

def loadTLList(items, traffic_color, pedestrian_color, size):
    gl_vertex = []
    gl_color = []
    gl_size = size

    for i, item_id in enumerate(items):
        point = items[item_id].point
        gl_vertex.extend(point)
        if items[item_id].IsPedestrianSign() == True or items[item_id].type == 'pedestrian':
            gl_color.extend(pedestrian_color)
        else:
            gl_color.extend(traffic_color)

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointer(3, GL_FLOAT, 0, gl_color)
    drawcnt = gl_vertex.size / 3
    glPointSize(gl_size)
    glDrawArrays(GL_POINTS, 0, int(drawcnt))
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()
    
    return gl_display_list