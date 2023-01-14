import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import numpy as np

from lib.common.logger import Logger

def load_triangle_polygon(items, color, alpha=True):
    if alpha :
        color = [color[0], color[1], color[2], 0.3]
    gl_vertex = []
    gl_indices = []
    gl_color = []

    for item in items:
        points = items[item].points
        faces = items[item].faces

        n_len = len(gl_vertex)
        gl_vertex.extend(points)
        gl_color.extend(color*len(points))

        for face in faces :
            gl_indices.append(face[0] + n_len)
            gl_indices.append(face[1] + n_len)
            gl_indices.append(face[2] + n_len)

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_indices = np.array(gl_indices)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    if alpha :
        glColorPointer(4, GL_FLOAT, 0, gl_color)
    else :
        glColorPointer(3, GL_FLOAT, 0, gl_color)

    glDrawElements(GL_TRIANGLES, int(gl_indices.size), GL_UNSIGNED_INT, gl_indices)

    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()
    
    return gl_display_list


def load_polygon_list(items, color):
    gl_vertex = []
    gl_color = []
    gl_size = 10
    
    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)
    glPushMatrix()

    for item in items:
        points = items[item].points
        
        glColor4f(color[0], color[1], color[2], 0.5)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBegin(GL_POLYGON)
        for point in points:
            glVertex3f(point[0], point[1], point[2])
        glEnd()

    glPopMatrix()
    glEndList()

    # gl_vertex = np.array(gl_vertex, dtype = np.float32)
    # gl_color = np.array(gl_color)
    # glEnableClientState(GL_VERTEX_ARRAY)
    # # 포인트별로 x, y, z니까 3개씩 나눈다
    # glVertexPointer(3, GL_FLOAT, 0, gl_vertex)

    # glEnableClientState(GL_COLOR_ARRAY)
    # # 색상별로 r, g, b니까 3개씩 나눈다
    # glColorPointer(3, GL_FLOAT, 0, gl_color)

    # # 포인트별로 x, y, z니까 3개씩 나눈다
    # drawcnt = gl_vertex.size / 3
    # # 사각형(GL_POLYGON) 만들기
    # glDrawElements(GL_POLYGON, int(gl_indices.size), GL_UNSIGNED_INT, gl_indices)
    # glDisableClientState(GL_VERTEX_ARRAY)
    # glDisableClientState(GL_COLOR_ARRAY)

    # glEndList()

    return gl_display_list

def load_polygon_line_list(items, color):
    gl_vertex = []
    gl_color = []
    gl_size = 10
    
    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)
    glPushMatrix()

    for item in items:
        
        points = items[item].all_rect_points
        
        glColor3f(color[0], color[1], color[2])
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glBegin(GL_LINE_LOOP)
        for point in points:
            glVertex3f(point[0], point[1], point[2])
        glEnd()

    glPopMatrix()
    glEndList()

    return gl_display_list

def load_crosswalk_List(items, color, z_axis=0):
    gl_vertex = []
    gl_color = []
    gl_size = 10
    
    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)
    glPushMatrix()

    for item in items:
        #crosswalk
        scw_list = items[item].single_crosswalk_list
        tl_list = items[item].ref_traffic_light_list
        
        for scw in scw_list:
            points = scw.points
            glColor4f(color[0], color[1], color[2], 0.5)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glBegin(GL_POLYGON)
            for point in points:
                glVertex3f(point[0], point[1], point[2]+z_axis)
            glEnd()
        
        for tl in tl_list:
            point = tl.point
            glColor4f(color[0], color[1], color[2], 0.5)
            gl_vertex = np.array(gl_vertex, dtype = np.float32)
            gl_color = np.array(gl_color)


            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
            glEnableClientState(GL_COLOR_ARRAY)
            glColorPointer(3, GL_FLOAT, 0, gl_color)
            drawcnt = gl_vertex.size / 3
            glPointSize(gl_size)
            glDrawArrays(GL_POINTS, 0, int(drawcnt))
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)

    glPopMatrix()
    glEndList()

    return gl_display_list
