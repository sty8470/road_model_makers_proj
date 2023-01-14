import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))

import numpy as np
import json
from pyproj import CRS, Proj
import shutil

from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map, edit_lane_boundary, edit_singlecrosswalk, edit_road_poly, edit_crosswalk, edit_synced_traffic_light, edit_intersection_controller
from lib.mgeo.class_defs.mgeo_map_planner import MgeoMapPlanners
from lib.mgeo.class_defs.mgeo_item import MGeoItem

import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save

from proj_mgeo_editor_morai_opengl.GUI.opengl_canvas import OpenGLCanvas

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.uic.properties import QtCore, QtWidgets
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from PyQt5 import QtGui
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pytest


def file_path():
    input_path = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/test/test_01_kcity'))
    output_path = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/test/test_save'))
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path)
    return input_path, output_path


# 길이비교...
def mgeo_compare_length(mgeo, nodes, links, signs, lights, lanes, lane_nodes, scws, synced, ints, cws, sms, rps, pss):
    return len(mgeo.node_set.nodes) == nodes \
        and len(mgeo.link_set.lines) == links \
        and len(mgeo.sign_set.signals) == signs \
        and len(mgeo.light_set.signals) == lights \
        and len(mgeo.lane_boundary_set.lanes) == lanes \
        and len(mgeo.lane_node_set.nodes) == lane_nodes \
        and len(mgeo.scw_set.data) == scws \
        and len(mgeo.synced_light_set.synced_signals) == synced \
        and len(mgeo.intersection_controller_set.intersection_controllers) == ints \
        and len(mgeo.cw_set.data) == cws \
        and len(mgeo.sm_set.data) == sms \
        and len(mgeo.road_polygon_set.data) == rps \
        and len(mgeo.parking_space_set.data) == pss


# mgeo 불러오기
def test_case_load():
    input_path, output_path = file_path()
    mgeo = MGeo.create_instance_from_json(input_path)
    assert mgeo_compare_length(mgeo, 208, 264, 66, 81, 734, 1474, 57, 25, 7, 25, 235, 1938, 18)



"""
    저장 테스트
"""
# 저장
def funcs_save_mgeo():
    input_path, output_path = file_path()
    mgeo = MGeo.create_instance_from_json(input_path)
    mgeo.to_json(output_path)
    return output_path

    
# 좌표계 이동하고 저장
def funcs_projection_and_save():
    input_path, output_path = file_path()
    mgeo = MGeo.create_instance_from_json(input_path)
    # proj_utm52 = '+proj=utm +zone=52 +ellps=WGS84 +units=m +no_defs'
    proj_5179 = '+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs'
    edit_mgeo_planner_map.change_world_projection(mgeo, proj_5179)
    mgeo.to_json(output_path)
    # 저장한 파일
    # file_count = os.listdir(output_path)
    # 저장한 MGeo의 좌표계
    # new_mgeo = MGeo.create_instance_from_json(output_path)
    # assert len(file_count) == 14 and new_mgeo.global_coordinate_system == proj_5179
    return output_path


# 원점 이동하고 저장
def funcs_origin_and_save():
    input_path, output_path = file_path()
    mgeo = MGeo.create_instance_from_json(input_path)
    # old_origin = np.array([302459.942, 4122635.537, 28.991])
    new_origin = np.array([300000, 4122000, 30])
    edit_mgeo_planner_map.change_origin(mgeo, new_origin, True)
    mgeo.to_json(output_path)
    # file_count = os.listdir(output_path)
    # new_mgeo = MGeo.create_instance_from_json(output_path)
    # assert len(file_count) == 14 and all(new_mgeo.get_origin() == new_origin)
    return output_path


def test_case_save1():
    output_path = funcs_save_mgeo()
    file_count = os.listdir(output_path)
    assert len(file_count) == 14

def test_case_save2():
    # 좌표계 이동하고 저장
    output_path = funcs_projection_and_save()
    file_count = os.listdir(output_path)
    assert len(file_count) == 14

def test_case_save3():
    # 원점 이동하고 저장
    output_path = funcs_origin_and_save()
    file_count = os.listdir(output_path)
    assert len(file_count) == 14




"""
    데이터 자르기 테스트
"""
# 범위 밖의 데이터 자르기
def funcs_trim_hard(input_path, x_range, y_range):
    mgeo = MGeo.create_instance_from_json(input_path)
    edit_mgeo_planner_map.delete_objects_out_of_xy_range(mgeo, x_range, y_range, hard=True)
    return mgeo

def funcs_trim_soft(input_path, x_range, y_range):
    mgeo = MGeo.create_instance_from_json(input_path)
    edit_mgeo_planner_map.delete_objects_out_of_xy_range(mgeo, x_range, y_range, hard=False)
    return mgeo

# 범위 안의 데이터 자르기
def funcs_trim_inside(input_path, x_range, y_range):
    mgeo = MGeo.create_instance_from_json(input_path)
    edit_mgeo_planner_map.delete_object_inside_xy_range(mgeo, x_range, y_range)
    return mgeo


def test_case_trim1():
    input_path, output_path = file_path()
    # East 68, North : 1195, Up : -230
    x_range = [-95, 230]
    y_range = [1100, 1290]
    mgeo = funcs_trim_hard(input_path, x_range, y_range)
    assert mgeo_compare_length(mgeo, 53, 74, 27, 35, 235, 470, 39, 11, 3, 15, 66, 374, 10)

def test_case_trim2():
    input_path, output_path = file_path()
    # East 68, North : 1195, Up : -230
    x_range = [-95, 230]
    y_range = [1100, 1290]
    mgeo = funcs_trim_soft(input_path, x_range, y_range)
    assert mgeo_compare_length(mgeo, 67, 88, 31, 35, 266, 532, 39, 11, 3, 15, 84, 412, 12)

def test_case_trim3():
    input_path, output_path = file_path()
    # East 68, North : 1195, Up : -230
    x_range = [-95, 230]
    y_range = [1100, 1290]
    mgeo = funcs_trim_inside(input_path, x_range, y_range)
    assert mgeo_compare_length(mgeo, 167, 190, 35, 46, 499, 998, 18, 14, 4, 10, 151, 1564, 8)


# 아이디로 찾으면 위치 이동하는지
# def test_case_8_find_id():
#     input_path = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/test_mgeo'))
#     print('opengl_canvas_trans_point_by_id')
#     mgeo_maps_dict = dict()
#     mgeo = MGeo.create_instance_from_json(input_path)
#     mgeo_maps_dict['test'] = mgeo
#     canvas = OpenGLCanvas()
#     canvas.mgeo_maps_dict = mgeo_maps_dict
#     # canvas.resetCamera()
#     find_item = {'key' : 'test', 'type' : MGeoItem.NODE, 'id': 'A119BS010141'}
#     canvas.trans_point_by_id(find_item)
#     trans = np.array([canvas.xTran, canvas.yTran])
#     assert all(canvas.mgeo_maps_dict['test'].node_set.nodes[find_item['id']].point[0:2] == -trans)


    
# def add_merge_mgeo(input_path, output_path):
    
#     mgeo_maps_dict = dict()

#     katri_1_roundabout = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/add_test/katri_1_roundabout'))
#     katri_2_intersection = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/add_test/katri_2_intersection'))
#     katri_3_intersection = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/add_test/katri_3_intersection'))

#     try:
#         print('Add MGeo')
#         mgeo = MGeo.create_instance_from_json(katri_1_roundabout)
#         mgeo_maps_dict['katri_1_roundabout'] = mgeo
#         MgeoMapPlanners(mgeo_maps_dict, mgeo).append_map(katri_2_intersection)
#         MgeoMapPlanners(mgeo_maps_dict, mgeo).append_map(katri_3_intersection)
#         mgeo.to_json(output_path)

#     except BaseException as e:
#         print('add_mgeo failed (traceback is down below) \n{}'.format(e))


# def opengl_canvas_find_by_mgeo_id(input_path, output_path):
#     try:
#         print('opengl_canvas_trans_point_by_id')
#         app = QtWidgets.QApplication(sys.argv)
#         mgeo_maps_dict = dict()
#         mgeo = MGeo.create_instance_from_json(input_path)
#         mgeo_maps_dict['test'] = mgeo
#         canvas = OpenGLCanvas()
#         canvas.mgeo_maps_dict = mgeo_maps_dict
#         # canvas.resetCamera()
#         canvas.mgeo_key = 'test'
#         find_item = {'key' : 'test', 'type' : MGeoItem.NODE, 'id': 'A119BS010141'}
#         canvas.find_by_mgeo_id()
#         print('trans', canvas.xTran, canvas.yTran)
#         print('node_point', canvas.mgeo_maps_dict['test'].node_set.nodes[find_item['id']].point[0:2])

#     except BaseException as e:  
#         print('opengl_canvas_trans_point_by_id failed (traceback is down below) \n{}'.format(e))


if __name__ == '__main__':
    test_case_trim3()
    # input_path = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/mgeo_211105'))
    # output_path = os.path.normpath(os.path.join(current_path, '../../data/mgeo_data/ngii_shp2_kcity-katri/save_test'))
    # trim_mgeo(input_path, output_path)