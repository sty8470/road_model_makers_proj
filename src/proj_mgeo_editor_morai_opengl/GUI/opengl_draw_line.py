import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)


from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import numpy as np

from lib.common.logger import Logger


def basicLineList(items, color, width, lane_change=True, road=False):
    gl_vertex = []
    gl_indices = []
    gl_color = []
    gl_width = width

    for i, item_id in enumerate(items):
        if lane_change == False:
            if items[item_id].lazy_point_init:
                continue
        points = items[item_id].points
        pushline(points, color, gl_vertex, gl_indices, gl_color)

    return makeDisplayLineList(gl_vertex, gl_indices, gl_color, gl_width, linetype=None, road=False)


def geostyleLineList(items, style, lane_change=True, road=False):
    # poly3
    gl_vertex_poly3_line = []
    gl_vertex_poly3_shp = []
    gl_indices_poly3 = []
    gl_color_poly3_line = []
    gl_color_poly3_shp = []
    # line
    gl_vertex_line_line = []
    gl_vertex_line_shp = []
    gl_indices_line = []
    gl_color_line_line = []
    gl_color_line_shp = []
    # paramPoly3
    gl_vertex_pp3_line = []
    gl_vertex_pp3_shp = []
    gl_indices_pp3 = []
    gl_color_pp3_line = []
    gl_color_pp3_shp = []

    gl_width = style['width']
    color = style['color']
    poly3_color = style['poly3_color']
    poly3_type = style['poly3_type']
    line_color = style['line_color']
    line_type = style['line_type']
    pp3_color = style['pp3_color']
    pp3_type = style['pp3_type']



    for i, item_id in enumerate(items):
        if lane_change == False:
            if items[item_id].lazy_point_init:
                continue
            
        points = items[item_id].points
        geo = items[item_id].geometry

        if len(geo) == 1:
            if geo[0]['method'] == 'poly3':
                pushline(points, color, gl_vertex_poly3_line, gl_indices_poly3, gl_color_poly3_line)
            elif geo[0]['method'] == 'line':
                pushline(points, color, gl_vertex_line_line, gl_indices_line, gl_color_line_line)
            elif geo[0]['method'] == 'paramPoly3':
                pushline(points, color, gl_vertex_pp3_line, gl_indices_pp3, gl_color_pp3_line)
        else:
            for i in range(len(geo)):
                if i == 0:
                    start_id = 0
                    end_id = geo[i+1]['id']
                elif i == (len(geo)-1):
                    start_id = geo[i]['id']
                    end_id = len(points)
                else:
                    start_id = geo[i]['id']
                    end_id = geo[i+1]['id']
                
                if geo[i]['method'] == 'poly3':
                    pushline(points[start_id:end_id+1], color, gl_vertex_poly3_line, gl_indices_poly3, gl_color_poly3_line)
                    if start_id != 0:
                        pushtriangle(points[start_id], poly3_color, gl_vertex_poly3_shp, gl_color_poly3_shp)
                
                elif geo[i]['method'] == 'line':
                    pushline(points[start_id:end_id+1], color, gl_vertex_line_line, gl_indices_line, gl_color_line_line)
                    if start_id != 0:
                        pushrhombus(points[start_id], line_color, gl_vertex_line_shp, gl_color_line_shp)
                
                elif geo[i]['method'] == 'paramPoly3':
                    pushline(points[start_id:end_id+1], color, gl_vertex_pp3_line, gl_indices_pp3, gl_color_pp3_line)
                    if start_id != 0:
                        pushinvertriangle(points[start_id], pp3_color, gl_vertex_pp3_shp, gl_color_pp3_shp)


    pline_list = makeDisplayLineList(gl_vertex_poly3_line, gl_indices_poly3, gl_color_poly3_line, gl_width, linetype=poly3_type, road=False)
    lline_list = makeDisplayLineList(gl_vertex_line_line, gl_indices_line, gl_color_line_line, gl_width, linetype=line_type, road=False)
    pp3line_list = makeDisplayLineList(gl_vertex_pp3_line, gl_indices_pp3, gl_color_pp3_line, gl_width, linetype=pp3_type, road=False)

    pshp_list = makeDisplayShpList(gl_vertex_poly3_shp, gl_color_poly3_shp, gl_width*3, GL_TRIANGLES)
    lshp_list = makeDisplayShpList(gl_vertex_line_shp, gl_color_line_shp, gl_width*3, GL_QUADS)
    pp3shp_list = makeDisplayShpList(gl_vertex_pp3_shp, gl_color_pp3_shp, gl_width*3, GL_TRIANGLES)

    new_display_list = glGenLists(1)
    glNewList(new_display_list, GL_COMPILE)
    glPushMatrix()
    glCallLists(pline_list)
    glCallLists(lline_list)
    glCallLists(pp3line_list)
    glCallLists(pshp_list)
    glCallLists(lshp_list)
    glCallLists(pp3shp_list)
    glPopMatrix()
    glEndList()

    # display_list = [pline_list, lline_list, pshp_list, lshp_list]

    return new_display_list
    
def pushline(points, color, gl_vertex, gl_indices, gl_color):
    n_len = len(gl_vertex)
    gl_vertex.extend(points)
    for index_i in range(len(points)-1):
        n_index = [n_len + index_i, n_len + index_i + 1]
        gl_indices.extend(n_index)
    gl_color.extend(color*len(points))

def pushinvertriangle(point, color, gl_vertex, gl_color):
    gl_vertex.extend([point[0]-1, point[1]+1, point[2]])
    gl_vertex.extend([point[0]+1, point[1]+1, point[2]])
    gl_vertex.extend([point[0], point[1]-1, point[2]])
    gl_color.extend(color*3)

def pushtriangle(point, color, gl_vertex, gl_color):
    gl_vertex.extend([point[0]-1, point[1]-1, point[2]])
    gl_vertex.extend([point[0]+1, point[1]-1, point[2]])
    gl_vertex.extend([point[0], point[1]+1, point[2]])
    gl_color.extend(color*3)

def pushrhombus(point, color, gl_vertex, gl_color):
    gl_vertex.extend([point[0], point[1]-1, point[2]])
    gl_vertex.extend([point[0]-1, point[1], point[2]])
    gl_vertex.extend([point[0], point[1]+1, point[2]])
    gl_vertex.extend([point[0]+1, point[1], point[2]])
    gl_color.extend(color*4)

def makeDisplayLineList(gl_vertex, gl_indices, gl_color, gl_width, linetype=None, road=False):
    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_indices = np.array(gl_indices)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    if road:
        glColorPointer(4, GL_FLOAT, 0, gl_color) # 도로 반투명 설정하려면 4로 해야함
    else:
        glColorPointer(3, GL_FLOAT, 0, gl_color)
        glPointSize(gl_width*3)
        glDrawArrays(GL_POINTS, 0, int(gl_vertex.size / 3))

    glLineWidth(gl_width)
    if linetype == 'Dot':
        glLineStipple(1, 0xaaaa)
    elif linetype == 'Dash':
        glLineStipple(1, 0x00ff)
    elif linetype == 'DashDot':
        glLineStipple(1, 0x7272) 
    else:
        glLineStipple(1, 0xffff)
    glLineWidth(gl_width)
    glDrawElements(GL_LINES, int(gl_indices.size), GL_UNSIGNED_INT, gl_indices)
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()

    return gl_display_list

def makeDisplayShpList(gl_vertex, gl_color, gl_size, shptype):

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
    glDrawArrays(shptype, 0, int(drawcnt))
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()

    return gl_display_list

def basicRoadList(items, color, width, road=False):
    color = [color[0], color[1], color[2], 0.5]
    gl_vertex = []
    gl_indices = []
    gl_color = []
    gl_width = width*1.2

    for i, item_id in enumerate(items):
        ref_line = items[item_id].ref_line
        if len(ref_line) == 0:
            for line in items[item_id].link_list_not_organized:
                points = line.points
                n_len = len(gl_vertex)
                gl_vertex.extend(points)
                for index_i in range(len(points)-1):
                    n_index = [n_len + index_i, n_len + index_i + 1]
                    gl_indices.extend(n_index)
                gl_color.extend(color*len(points))
            
        for line in ref_line:
            points = line.points
            n_len = len(gl_vertex)
            gl_vertex.extend(points)
            for index_i in range(len(points)-1):
                n_index = [n_len + index_i, n_len + index_i + 1]
                gl_indices.extend(n_index)
            gl_color.extend(color*len(points))

    gl_vertex = np.array(gl_vertex, dtype = np.float32)
    gl_indices = np.array(gl_indices)
    gl_color = np.array(gl_color)

    gl_display_list = glGenLists(1)
    glNewList(gl_display_list, GL_COMPILE)

    glEnableClientState(GL_VERTEX_ARRAY)
    glVertexPointer(3, GL_FLOAT, 0, gl_vertex)
    glEnableClientState(GL_COLOR_ARRAY)
    glColorPointer(4, GL_FLOAT, 0, gl_color)
    glLineWidth(gl_width)
    glLineStipple(1, 0xffff)
    glDrawElements(GL_LINES, int(gl_indices.size), GL_UNSIGNED_INT, gl_indices)
    glDisableClientState(GL_VERTEX_ARRAY)
    glDisableClientState(GL_COLOR_ARRAY)

    glEndList()
    
    return gl_display_list

    




