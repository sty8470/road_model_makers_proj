import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from freetype import *
import numpy as np

from lib.common.logger import Logger
from lib.mgeo.class_defs.mgeo_item import MGeoItem

def point_id_list(points, color):
    id_list = glGenLists(1)
    glNewList(id_list, GL_COMPILE)
    glPushMatrix()
    font = GLUT_BITMAP_HELVETICA_12
    for i, item in enumerate(points):
        name = points[item].idx
        point = points[item].point
        glColor3f(color[0], color[1], color[2])
        glRasterPos3f(point[0], point[1] + 0.5, point[2])
        for ch in str(name):
            glutBitmapCharacter(font, ctypes.c_int(ord(ch)))
    glPopMatrix()
    glEndList()

    return id_list

def points_id_list(itemlist, color, data_type):
    id_list = glGenLists(1)
    glNewList(id_list, GL_COMPILE)
    glPushMatrix()
    font = GLUT_BITMAP_HELVETICA_12
    for i, item in enumerate(itemlist):
        name = itemlist[item].idx
        if data_type == MGeoItem.JUNCTION:
            points = itemlist[item].get_jc_node_points()
            if len(points) > 0:
                point = points[0]
            else:
                continue
        elif data_type == MGeoItem.SYNCED_TRAFFIC_LIGHT:
            if itemlist[item].point is None:
                point = itemlist[item].get_synced_signal_points()[0]
            else:
                point = itemlist[item].point[0]
        elif data_type == MGeoItem.INTERSECTION_CONTROLLER:
            point = itemlist[item].point
        else:
            return
        if point is None or len(point) < 1:
            name = None
            continue
        glColor3f(color[0], color[1], color[2])
        glRasterPos3f(point[0], point[1] + 0.5, point[2])
        for ch in str(name):
            glutBitmapCharacter(font, ctypes.c_int(ord(ch)))
    glPopMatrix()
    glEndList()

    return id_list

def line_id_list(lines, color, data_type):
    id_list = glGenLists(1)
    glNewList(id_list, GL_COMPILE)
    glPushMatrix()
    font = GLUT_BITMAP_HELVETICA_12
    for i, key in enumerate(lines):
        if data_type == MGeoItem.LINK:
            name = lines[key].idx
            points = lines[key].points
            p0 = points[0]
            p1 = points[1]
            uv = (p1-p0)/np.linalg.norm(p1-p0)
            try:
                if lines[key].ego_lane is not None:
                    el = int(lines[key].ego_lane)
                    point = p0 + ( uv * el )
                else:
                    point = (p0 + p1) / 2
            except BaseException as e:
                Logger.log_error('Link Id Display Error, ego_lane is None: {}'.format(e))
                return

        elif data_type == MGeoItem.ROAD:
            name = lines[key].road_id
            ref_line = lines[key].ref_line
            if len(ref_line) > 0:
                point = ref_line[0].points[0]
            else:
                # Logger.log_error('Road Id Display Error, ref_line is None')
                if len(lines[key].link_list_not_organized) > 1:
                    point = lines[key].link_list_not_organized[0].points[0]
                    
        elif data_type == MGeoItem.LANE_BOUNDARY:
            name = lines[key].idx
            points = lines[key].points
            p0 = points[0]
            p1 = points[1]
            uv = (p1-p0)/np.linalg.norm(p1-p0)
            point = (p0 + p1) / 2
            
        glColor3f(color[0], color[1], color[2])
        glRasterPos3f(point[0], point[1] + 0.5, point[2])
        for ch in str(name):
            glutBitmapCharacter(font, ctypes.c_int(ord(ch)))
    glPopMatrix()
    glEndList()
    return id_list

def crosswalk_id_list(crosswalks, color, data_type):
    id_list = {}
    font = GLUT_BITMAP_HELVETICA_12
    for i, cw in enumerate(crosswalks):
        if data_type == MGeoItem.CROSSWALK:
            name = crosswalks[cw].idx
            points = crosswalks[cw].points
            p0 = points[0]
            p1 = points[1]
            uv = (p1-p0)/np.linalg.norm(p1-p0)
            try:
                # if lanes[line].ego_lane is not None:
                #     el = int(lanes[line].ego_lane)
                #     point = p0 + ( uv * el )
                # else:
                    point = (p0 + p1) / 2
            except BaseException as e:
                Logger.log_error('Crosswalk Id Display Error, ego_lane is None: {}'.format(e))
                return
        
        i = glGenLists(1)
        glNewList(i, GL_COMPILE)
        glPushMatrix()
        glColor3f(color[0], color[1], color[2])
        glRasterPos3f(point[0], point[1] + 0.5, point[2])
        for ch in str(name):
            glutBitmapCharacter(font, ctypes.c_int(ord(ch)))
        glPopMatrix()
        glEndList()
        id_list[name] = i

    return id_list
