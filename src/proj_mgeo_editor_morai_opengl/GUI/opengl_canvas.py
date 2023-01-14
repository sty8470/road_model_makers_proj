import os
import sys
import time
import datetime as dt
from tkinter.ttk import Treeview
from copy import deepcopy

import math
import csv
import json
import traceback
from freetype import *

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from PyQt5 import QtGui
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.mgeo.class_defs import intersection_controller_set

from lib.mgeo.class_defs.signal import Signal
from lib.mgeo.class_defs.base_point import BasePoint
from lib.mgeo.class_defs.base_line import BaseLine
from lib.mgeo.class_defs.base_plane import BasePlane
from lib.mgeo.class_defs.road_polygon import RoadPolygon
from lib.mgeo.class_defs.intersection_controller_set_builder_rev import IntersectionControllerSetBuilder
from lib.mgeo.class_defs.intersection_state_builder import IntersectionStateBuilder

from lib.openscenario.class_defs.vehicle import Vehicle
from lib.openscenario.class_defs.condition import *
from lib.openscenario.class_defs.utils_position import convert_to_link_position
from lib.openscenario.class_defs.entities import *
from lib.openscenario.class_defs.enumerations import PedestrianCategory
from lib.openscenario.class_defs.environment import *
from lib.openscenario.class_defs.file_header import *
from lib.openscenario.class_defs.misc_object import MiscObject
from lib.openscenario.class_defs.pedestrian import Pedestrian
from lib.openscenario.class_defs.position import *
from lib.openscenario.class_defs.global_action import *
from lib.openscenario.class_defs.private_action import *
from lib.openscenario.class_defs.storyboard_element.act import Act
from lib.openscenario.class_defs.storyboard_element.action import _Action
from lib.openscenario.class_defs.storyboard_element.maneuver import *
from lib.openscenario.class_defs.storyboard_element.maneuver_group import *
from lib.openscenario.class_defs.storyboard_element.storyboard import *
from lib.openscenario.class_defs.add_openscenario_element_struct import ABLE_ADD_ACTION_LIST, ABLE_ADD_CONDITION_LIST, ABLE_ADD_INIT_ACTION_LIST, ADD_ELEMENT_STRUCT, ABLE_ADD_ITEM_LIST
from lib.widget.add_scenario_object import AddEntityInTreeUI, VehicleModelUI, PedestrianModelUI, MiscObjectModelUI
from lib.widget.add_event import AddConditionUI, AddEventUI, AddActionUI, AddInitActionUI
from lib.openscenario.open_scenario_importer import OpenScenarioImporter
from lib.widget.edit_set_max_link_speed import EditSetMaxSpeedLink

from lib.common.logger import Logger
from lib.common.mgeo_rtree import MgeoRTree
from lib.common.polygon_util import minimum_bounding_rectangle, calculate_centroid, calculate_heading

from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.key_maker import KeyMaker

from lib.mgeo.class_defs.mgeo_item import MGeoItem, MGeoItemFlags
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map, edit_lane_boundary, edit_singlecrosswalk, edit_road_poly, edit_crosswalk, edit_synced_traffic_light, edit_intersection_controller, edit_parking_space

from lib.mgeo.utils import error_fix, lane_change_link_creation, mgeo_find, set_link_lane_mark
from lib.mgeo.class_defs.path import Path
from lib.mgeo.path_planning.dijkstra import Dijkstra
from lib.mscenario.class_defs import *
from lib.mscenario.class_defs.mscenario import MScenario
from lib.mscenario.class_defs.mscenario_item import MScenarioItem
from lib.openscenario.class_defs.openscenario_item import ScenarioItem

from lib.widget.display_item_style import DisplayStyle
from lib.widget.display_item_prop import DisplayProp
from lib.widget.edit_tl_type import EditTLType
from lib.widget.edit_change_region_localization import EditChangeRegionLocalization
from lib.widget.edit_geolocation import EditGeolocation
from lib.widget.edit_change_world_projection import EditChangeWorldProjection
from lib.widget.export_csv_widget import ExportCSVWidget
from lib.widget.find_mgeo_item_window import FindMGeoItemWindow
from lib.widget.find_node_window import FindNodeWindow
from lib.widget.find_link_window import FindLinkWindow
from lib.widget.find_traffic_sign_window import FindTrafficSignWindow
from lib.widget.find_traffic_light_window import FindTrafficLightWindow
from lib.widget.find_junction_window import FindJunctionWindow
from lib.widget.find_lane_boundary_window import FindLaneBoundaryWindow
from lib.widget.find_single_crosswalk_window import FindSingleCrosswalkWindow
from lib.widget.find_crosswalk_window import FindCrosswalkWindow
from lib.widget.find_road_polygon_window import FindRoadPolygonWindow
from lib.widget.edit_autogenerate_geometry_points import EditAutogenerateGeometryPoints
from lib.widget.setting_intersection_schedule import SettingIntersectionSchedule
from lib.widget.set_traffic_signal_controller import ViewIntersectionSchedule
from lib.command_manager.concrete_commands import *

from lib.V2X.v2x_exporter import v2xExporter, get_intersection_item

from mgeo_odr_converter import MGeoToOdrDataConverter
from xodr_data import OdrData

from load_mgeo_id import *
from opengl_draw_point import *
from opengl_draw_line import *
from opengl_draw_polygon import *


from lib.opendrive.mesh_utils import vtkPoly, vtkPolyByPoints, vtkTrianglePoly, vtkPoly_to_MeshData, generate_normals

import webbrowser

class OpenGLCanvas(QOpenGLWidget):
    """
    QOpenGLWidget 클래스
    """

    xRotationChanged = pyqtSignal(int)
    yRotationChanged = pyqtSignal(int)
    zRotationChanged = pyqtSignal(int)

    checkfps = -1
    timecheck = 0
    beforetime = dt.datetime.now()

    def __init__(self, parent=None):
        super(QOpenGLWidget, self).__init__().__init__(parent)

        self.setMouseTracking(True)

        self._timer = QBasicTimer()          # creating timer
        self._timer.start(1000 / 60, self)   # setting up timer ticks to 60 fps

        # 환경설정
        self.config = None
        self.json_file_path = None

        # 로깅 기능을 제공하는 클래스
        self.logger = None

        # 편집 기능을 제공하는 클래스, MGeo 데이터에 대한 참조 또한 여기서 관리한다
        self.mgeo_planner_map = MGeo()
        
        # Add 한 Mgeo 맵들을 저장하는 dictionary
        self.mgeo_maps_dict = dict()
        self.odr_data = OdrData(mgeo_planner_map=None)

        # MScenario 
        self.mscenario = MScenario()

        #command manager
        self.command_manager = None
        
        # OpenSCENARIO
        self.open_scenario = None
        self.osc_client_triggered = False
        self.path_obj_lst = list()

        # 화면 회전
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0

        # 화면 줌인/아웃
        self.zoom = -50

        # 화면 이동
        self.xTran = 0
        self.yTran = 0
        self.zTran = 0

        self.lastPos = QPoint()

        # 선택하기
        self.bsp = None
        self.sp = None
        self.list_sp = []

        self.check_item = None
        self.clicked_scenario_data = None

        # 시작, 끝 선택하기
        self.marker_start_node = []
        self.marker_end_node = []

        # highlight/error 데이터 id 목록
        self.list_highlight1 = []
        self.list_highlight2 = []
        self.list_highlight3 = []
        self.list_error = []

        # view button
        self.view_mode = 'view_trans'

        # 속성
        self.tree_data = None
        self.tree_style = None
        self.tree_attr = None

        # widget window position convert to opengl position
        self.xlim = [-1, 1]
        self.ylim = [-1, 1]
        self.position_label = None

        # link 내부 point 편집을 위한 ptr
        self.reset_inner_link_point_ptr()

        # id로 찾기
        self.find_item = None

        self.slider = [0, 0, 0]
        self.rot_eidt = [0, 0, 0]
        self.camera_speed_slider = None
        self.camera_speed_edit = None

        self.camera_move_east_edit = None
        self.camera_move_north_edit = None
        self.camera_move_up_edit = None

        # Line안에 포인트 넣기
        self.input_line_points = False
        self.point_list = []

        # display list, id display list 초기화
        self.node_list = dict()
        self.link_list = dict()
        self.link_geo_list = dict()
        self.tl_list = dict()
        self.synced_tl_list = dict()
        self.ic_list = dict()
        self.ts_list = dict()
        self.junction_list = dict()
        self.road_list = dict()
        self.single_crosswalk_list = dict()
        self.crosswalk_list = dict()
        self.road_polygon_list = dict()
        self.sm_list = dict()
        self.parking_space_list = dict()

        self.node_id_list = dict()
        self.link_id_list = dict()
        self.tl_id_list = dict()
        self.synced_tl_id_list = dict()
        self.ic_id_list = dict()
        self.ts_id_list = dict()
        self.junction_id_list = dict()
        self.road_id_list = dict()
        self.sm_id_list = dict()
        self.parking_space_id_list = dict()

        # 210203, 차선/도로 mesh 편집기능 추가
        self.lane_node_list = dict()
        self.lane_node_id_list = dict()
        self.lane_marking_list = dict()
        self.lane_marking_geo_list = dict()
        self.lane_marking_id_list = dict()

        self.display_style = None
        self.display_prop = None

        # 도로 넣기 샘플
        self.road_id_idx = KeyMaker(prefix='4')

        # 횡단보도 색칠하기(210325)
        self.single_crosswalk_list = dict()
        self.crosswalk_list = dict()

        # virtual road/link id (210524)
        self.virtual_road = 0
        self.virtual_link = 0
        self.virtual_lane = 0

        self.camera_speed = 0

        self.control_key_pressed = False

        # start_point와 end_point 설정
        self.start_point_and_end_point = {'start_point':[],'end_point':[]}
        self.scenario_start_point = None
        self.scenario_end_point = None
        self.scenario_stop_point = []
        # 드래그 선택
        self.drag_for_select = False
        self.drag_start = QPoint()
        
        self.mgeo_key = None
        self.mgeo_rtree = dict()
        
    def initializeGL(self):
        """필요한 OpenGL 리소스 및 상태를 설정한다"""
        # glutInit()에서 에러발생 시
        # 아래 파일 직접 다운로드 해야한다.
        # PyOpenGL-3.1.5-cp37-cp37m-win_amd64.whl
        # PyOpenGL_accelerate-3.1.5-cp37-cp37m-win_amd64.whl
        glutInit()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        # Line 모양 변경
        glEnable(GL_LINE_STIPPLE)
        self.display_style = DisplayStyle(self, self.config, self.json_file_path, self.tree_style)
        self.display_prop = DisplayProp()
        self.tree_attr.itemDoubleClicked.connect(self.display_prop.edit_item_prop)

    def resizeGL(self, w, h):
        """이 함수는 Widget의 크기가 조정될 때마다 호출된다"""
        if h == 0:
            h = 1
        ratio =  w / h
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, w, h)
        gluPerspective(45.0, ratio, 0.1, 10000.0)
        # FOV: 45.0, Aspect Ratio: width/height, zNear: 0.1, zFar: 100.0
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """이 함수는 Widget에 Object를 그려야 할 때마다 호출된다"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        
        # Zoom/In Out
        glTranslate(0, 0, self.zoom)

        # 화면 이동을 회전 후에 (오브젝트 회전)
        glRotated(self.xRot, 1.0, 0.0, 0.0)
        glRotated(self.yRot, 0.0, 1.0, 0.0)
        glRotated(self.zRot, 0.0, 0.0, 1.0)

        # TODO(hyjo): self.xTran, self.zTran 값을, xRot, zRot 고려해서 변경하여 입력
        xTranTemp = self.xTran 
        yTranTemp = self.yTran
        zTranTemp = self.zTran

        glTranslate(xTranTemp, yTranTemp, zTranTemp)
          

        self.projection = glGetDoublev(GL_PROJECTION_MATRIX)
        self.modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)


        self.drawGL()
        self.update() # 계속 업데이트

        # diff = dt.datetime.now() - self.beforetime
        # diffsec = diff.microseconds
        # self.timecheck = self.timecheck  + diffsec
        # self.beforetime = dt.datetime.now()

        # self.checkfps = self.checkfps + 1
    
        # if self.timecheck > 600000 : 
        #      Logger.log_trace('time : {}'.format(self.checkfps))
        #      self.checkfps = 0
        #      self.timecheck = 0

        # if  self.checkfps > 120 :
        #     self.checkfps = 0

    def resetCamera(self):
        """현재 데이터 중 첫번째 노드 데이터 위치로 reset한다"""       
        xtran = 0
        ytran = 0
        
        # MGeo Key
        self.mgeo_key = list(self.mgeo_maps_dict.keys())[0]
        
        if len(self.getNodeSet(self.mgeo_key).nodes) > 0:            
            indices = self.getNodeSet(self.mgeo_key).nodes.keys()
            first_idx = list(indices)[0]
            node = self.getNodeSet(self.mgeo_key).nodes[first_idx]            
            xtran = -1 * node.point[0]
            ytran = -1 * node.point[1]

        # 화면 회전
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        self.setRotWidget()
        self.camera_speed = 0 
        self.setCameraSpeedWidget()

        # 화면 줌인/아웃
        self.zoom = -50

        # 화면 이동
        self.xTran = xtran
        self.yTran = ytran
        self.zTran = 0

        self.setCameraMoveWidget()


    def setCameraPositionEast(self, position):
        # 화면 이동
        self.xTran = -1 * position
        self.setCameraMoveWidget()
        
    
    def setCameraPositionNorth(self, position):
        # 화면 이동
        self.yTran = -1 * position
        self.setCameraMoveWidget()
    
    def setCameraPositionUp(self, zoomLevel):
        # 화면 이동
        self.zoom = zoomLevel
        self.setCameraMoveWidget()

    def drawGL(self):
        """OpenGL Canvas에 그려야 할 Object를 설정한다"""
        margin = 1.2
        xlim = OpenGLCanvas._add_margin_to_range(self.xlim, margin)
        ylim = OpenGLCanvas._add_margin_to_range(self.ylim, margin)

        if self.scenario_start_point is not None:
            color = self.config['STYLE']['NODE']['START']['COLOR']
            start_node = self.getNodeSet(self.mgeo_key).nodes[self.scenario_start_point]
            self.plot_point_start_or_end_or_stop(start_node.point, color=color, size=1.0)

        if self.scenario_end_point is not None:
            color = self.config['STYLE']['NODE']['END']['COLOR']
            end_node = self.getNodeSet(self.mgeo_key).nodes[self.scenario_end_point]
            self.plot_point_start_or_end_or_stop(end_node.point, color=color, size=1.0)

        if self.scenario_stop_point !=  []:
            color = self.config['STYLE']['NODE']['STOP']['COLOR']
            for stop_point in self.scenario_stop_point:
                stop_node = self.getNodeSet(self.mgeo_key).nodes[stop_point]
                self.plot_point_start_or_end_or_stop(stop_node.point, color=color, size=1.0)

            
        if len(self.start_point_and_end_point) > 0:
            if self.start_point_and_end_point['start_point'] != []:
                start_node_id = self.start_point_and_end_point['start_point']
                start_node = self.getNodeSet(self.mgeo_key).nodes[start_node_id]
                self.plot_point_start(start_node.point, color=[255, 0, 0], size=1.0)
            if self.start_point_and_end_point['end_point'] != []:
                end_node_id = self.start_point_and_end_point['end_point']
                end_node = self.getNodeSet(self.mgeo_key).nodes[end_node_id]
                self.plot_point_end(end_node.point, color=[0, 0, 255], size=1.0)

        self.drawSelectItem()
        self.drawHL1Item()
        self.drawHL2Item()
        self.drawHL3Item()
        self.drawErrorItem()

        if self.open_scenario is not None:
            self.drawOpenScenario()
        if self.mscenario.ego_vehicle is not None:
            self.drawMScenario()
            
        if self.zoom >= self.config['STYLE']['MAX ID DISPLAY']['SIZE']:
            self.drawMGeoID()
        self.drawMGeo()

        # 드래그 범위 그리기
        if self.drag_for_select:
            self.drag_plot()

        self.updateXLimYLim()

        # style 변경했을 때 MgeoData reload
        if self.display_style.data_update:
            self.updateMapData()
            self.display_style.data_update = False
    
    def smooth_junction_road(self):
        lane_nodes = self.getLaneNodeSet().nodes
        new_point_length = 0.1
        for lane_node_id in lane_nodes:
            clane_node = lane_nodes[lane_node_id]
            to_dir_lane_list = []
            from_dir_lane_list = []
            lane_list = clane_node.to_links + clane_node.from_links
            if len(lane_list) >2:
                if clane_node.to_links != []:
                    to_lane = clane_node.to_links[0] 
                    to_lane_dir = to_lane.points[1] - to_lane.points[0]
                else:
                    from_lane = clane_node.from_links[0]
                    to_lane_dir = from_lane.points[-1] - from_lane.points[-2]
                for lane in lane_list:
                    if lane.from_node == clane_node:
                        to_lane_dir_candidate = lane.points[1] - lane.points[0]
                    else:
                        to_lane_dir_candidate = lane.points[-2] - lane.points[-1]
                    try:
                        if np.dot(to_lane_dir, to_lane_dir_candidate) >0:
                            to_dir_lane_list.append(lane)
                        else:
                            from_dir_lane_list.append(lane)
                    except:
                        pass
            else:
                continue
            
            to_dir_outer_point_list = []
            from_dir_outer_point_list = []
            if to_dir_lane_list != []:
                for to_lane in to_dir_lane_list:                         
                    if to_lane.from_node == clane_node:
                        f_point = to_lane.points[0]
                        sec_point = to_lane.points[1]
                        length = np.linalg.norm(f_point - sec_point)
                        if length == 0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        from_dir_outer_point_list.append(outer_point)
                    
                    else:
                        f_point = to_lane.points[-1]
                        sec_point = to_lane.points[-2]
                        length = np.linalg.norm(f_point - sec_point)
                        if length ==0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        from_dir_outer_point_list.append(outer_point)
                
                try:

                    from_outer_point_calculated = sum(from_dir_outer_point_list)/len(from_dir_outer_point_list)
                except:
                    pass
            if from_dir_lane_list !=[]:

                for from_lane in from_dir_lane_list:
                    if from_lane.to_node == clane_node:
                        f_point = from_lane.points[-1]
                        sec_point = from_lane.points[-2]
                        length = np.linalg.norm(f_point - sec_point)
                        if length ==0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        to_dir_outer_point_list.append(outer_point)
                    else:
                        f_point = from_lane.points[0]
                        sec_point = from_lane.points[1]
                        length = np.linalg.norm(f_point - sec_point)
                        if length ==0:
                            continue
                        outer_point = (sec_point*new_point_length - (new_point_length + length)*f_point)/-length
                        to_dir_outer_point_list.append(outer_point)
                try:
                    to_outer_point_calculated = sum(to_dir_outer_point_list)/len(to_dir_outer_point_list)
                except:
                    pass
            if to_dir_lane_list != []:
                from_link_already = []
                for from_link in from_dir_lane_list:
                    if from_link in clane_node.from_links and from_link not in from_link_already:
                        from_link.points = np.array(list(from_link.points[:-1]) + [from_outer_point_calculated] + [from_link.points[-1]])
                        from_link_already.append(from_link)
                    if from_link in clane_node.to_links and to_link not in from_link_already:
                        from_link.points = np.array([from_link.points[0]] + [from_outer_point_calculated] + list(from_link.points[1:]))
                        from_link_already.append(from_link)
            if from_dir_lane_list !=[]:
                to_link_already =[]
                for to_link in to_dir_lane_list:
                    if to_link in clane_node.from_links and to_link not in to_link_already:
                        to_link.points = np.array(list(to_link.points[:-1]) + [to_outer_point_calculated] + [to_link.points[-1]])
                        to_link_already.append(to_link)
                    if to_link in clane_node.to_links and to_link not in to_link_already:
                        to_link.points = np.array([to_link.points[0]] + [to_outer_point_calculated] + list(to_link.points[1:]))
                        to_link_already.append(to_link)
        print("point append end")


    # 키보드 이벤트
    def keyPressEvent(self, input_key):
        key = input_key.key()
        modifiers = QApplication.keyboardModifiers()

        if key == Qt.Key_Delete and self.sp is not None:
            if self.open_scenario == None:
                self.delete_item(self.list_sp)

        elif key == Qt.Key_Z: # 첫화면으로 돌아가기
            if len(self.getNodeSet(self.mgeo_key).nodes) > 0:
                self.resetCamera()

        # elif key == Qt.Key_Q:
        #     error_fix.find_node_link_connect_point(self.mgeo_planner_map.node_set, self.mgeo_planner_map.link_set)

        # elif key == Qt.Key_U:
        #     lanes = self.getLaneBoundarySet().lanes
        #     for lane_id in lanes:
        #         clane = lanes[lane_id]
        #         if clane.from_node in self.mgeo_planner_map.lane_node_set.nodes.values():
        #             continue
        #         else:
        #             new_node = Node()
        #             new_node.point = clane.points[0]
        #             self.getNodeSet().append_node(new_node, create_new_key=True)
        #             for lane_id in lanes:
        #                 tlane = lanes[lane_id]
        #                 if tlane.points[-1] == new_node.point:
        #                     tlane.to_node = new_node
        #                     continue
        #     print("create new lane node")

        # elif key == Qt.Key_T:
        #     for road in  self.getRoadSet().values():
        #         for lane_mark in road.ref_line[0].lane_mark_left:
        #             if len(lane_mark.points) >2:
        #                 for i in range(len(lane_mark.points)-2):
        #                     first = lane_mark.points[i]
        #                     second = lane_mark.points[i+1]
        #                     third = lane_mark.points[i+2]
        #                     fir_vec = second - first 
        #                     sec_vec = third - second 
        #                     if np.dot(sec_vec, fir_vec) <0:
        #                         print(lane_mark.idx)
        #                         print(i)
                
        #         for link in road.ref_line:
        #             for i in range(len(link.points)-2):
        #                 first = link.points[i]
        #                 second = link.points[i+1]
        #                 third = link.points[i+2]
        #                 fir_vec = second - first 
        #                 sec_vec = third - second 
        #                 if np.dot(sec_vec, fir_vec) <0:
        #                     print(link.idx)
        #                     print(i)
            
        #     lanes= self.getLaneBoundarySet().lanes
        #     for lane_id in lanes:
        #         clane = lanes[lane_id]
        #         if len(clane.points) >2:
        #             for i in range(len(clane.points)-4):
        #                 first = clane.points[i]
        #                 second = clane.points[i+1]
        #                 third = clane.points[i+2]
        #                 fir_vec = second - first 
        #                 sec_vec = third - second 
        #                 if np.dot(sec_vec, fir_vec) <0 and i < len(clane.points)-2:
        #                     clane.points = np.array( clane.points[:i+1]+ clane.points[i+2:])
        #                     print(clane.idx)
        #                 elif np.dot(sec_vec, fir_vec) <0 and i > len(clane.points)-2:
        #                     clane.points = np.array(clane.points[:-2]+ clane.points[-1:])
        #                     print(clane.idx)
        #     print("lnaes point delete end")
            
        #     links = self.getLinkSet().lines
        #     for link in links:
        #         clink = links[link]
        #         if len(clink.points) >2:
        #             for i in range(len(clink.points)-4):
        #                 first = clink.points[i]
        #                 second = clink.points[i+1]
        #                 third = clink.points[i+2]
        #                 fir_vec = second - first 
        #                 sec_vec = third - second 
        #                 if np.dot(sec_vec, fir_vec) <0 and i < len(clink.points)-2:
        #                     clink.points = np.array( clink.points[:i+1]+ clink.points[i+2:])
        #                     print(clink.idx)
        #                 elif np.dot(sec_vec, fir_vec) <0 and i > len(clink.points)-2:
        #                     clink.points = np.array(clink.points[:-2]+ clink.points[-1:])
        #                     print(clink.idx)
        #     print("links point delete end")
        
        
        # elif key == Qt.Key_H:
        #     lanes= self.getLaneBoundarySet().lanes
        #     for lane_id in lanes:
        #         clane = lanes[lane_id]
                
        #         if list(clane.points[-1]) != list(clane.to_node.point):
        #             if len(clane.points) > 2:
                        
        #                 if list(clane.points[-2]) == [clane.to_node.point] or list(clane.points[-3]) == [clane.to_node.point]:
        #                     print(lane_id)
        #                     print(clane.points)
        #                     print(clane.to_node.point)
        #                 #clane.points[-1] = clane.to_node.point
        #                 clane.points = np.array(list(clane.points[:-3]) + [clane.to_node.point])
        #                 #print('clane idx', clane.idx)
                        
        #             else:
        #                 #clane.points[-1] = clane.to_node.point
        #                 clane.points = np.array(list(clane.points[0]) + [clane.to_node.point])
                
                
        #         try:
        #             if list(clane.points[0]) != list(clane.from_node.point):
        #                 if len(clane.points) >2:
        #                     if list(clane.points[2]) == [clane.from_node.point] or list(clane.points[1]) == [clane.from_node.point]:
        #                         print(lane_id)
        #                         print(clane.points)
        #                         print(clane.from_node.point)
        #                     clane.points = np.array([clane.from_node.point] + list(clane.points[3:]))
        #                     #print('clane idx', clane.idx)
                        
        #                 else:
        #                     clane.points = np.array([clane.from_node.point] + list(clane.points[-1]))
        #         except:
        #             pass
           
        #     print("lane bounadry point redefine")
        #     for road in  self.getRoadSet().values():
        #         for lane_mark in road.ref_line[0].lane_mark_left:
        #             if len(lane_mark.points) >2:
        #                 for i in range(len(lane_mark.points)-2):
        #                     first = lane_mark.points[i]
        #                     second = lane_mark.points[i+1]
        #                     third = lane_mark.points[i+2]
        #                     fir_vec = second - first 
        #                     sec_vec = third - second 
        #                     if np.dot(sec_vec, fir_vec) <0:
        #                         print(lane_mark.idx)
        #                         print(i)
                
        #         for link in road.ref_line:
        #             for i in range(len(link.points)-2):
        #                 first = link.points[i]
        #                 second = link.points[i+1]
        #                 third = link.points[i+2]
        #                 fir_vec = second - first 
        #                 sec_vec = third - second 
        #                 if np.dot(sec_vec, fir_vec) <0:
        #                     print(link.idx)
        #                     print(i)
        
        # elif key == Qt.Key_V:
        #     lanes= self.getLaneBoundarySet().lanes
        #     for lane_id in lanes:
        #         clane = lanes[lane_id]
                
        #         if list(clane.points[-1]) != list(clane.to_node.point):
        #             if len(clane.points) > 2:
        #                 clane.points = np.array(list(clane.points[:-2]) + [clane.to_node.point])
        #                 print('clane idx', clane.idx)
        #             else:
        #                 clane.points = np.array(list(clane.points[0]) + [clane.to_node.point])
                
        #         try:
        #             if list(clane.points[0]) != list(clane.from_node.point):
        #                 if len(clane.points) >2:
        #                     clane.points = np.array([clane.from_node.point] + list(clane.points[2:]))
        #                     print('clane idx', clane.idx)
        #                 else:
        #                     clane.points = np.array([clane.from_node.point] + list(clane.points[-1]))
        #         except:
        #             pass
           
        #     print("lane bounadry point redefine")

        # elif key == Qt.Key_R:
        #     Logger.log_trace('Called: smooth_junctoin_road')
        #     self.smooth_junction_road()
            
        # elif key == Qt.Key_J:
        #     links = self.getLinkSet().lines
        #     for link_id in links:
        #         clink  = links[link_id]
        #         if clink.lane_mark_left ==[] or clink.lane_mark_right ==[]:
        #             vector = clink.points
        #             if clink.get_to_links() !=[]:
        #                 to_point = clink.get_to_links()[0].points[1]
        #             else:
        #                 to_point = clink.points[-1]
        #             if clink.get_from_links() !=[]:
        #                 from_point = clink.get_from_links()[0].points[-2]
        #             else:
        #                 from_point = clink.points[0]
        #             test = MGeoToOdrDataConverter()
        #             init_coord, heading, arclength, poly_geo, uv_point, residual, to_slope = \
        #                     test.bezier_geometry_general_boundary_all(vector, to_point, from_point)
                    
        #             if clink.lane_mark_left == []:
        #                 before_rotation_points = []
        #                 point_num = 10
        #                 for i in range(point_num):
        #                     s = arclength*(i/point_num)
        #                     x = 0 
        #                     y = 0
        #                     z = clink.from_node.point[2]
        #                     for t in range(4):
        #                         x += poly_geo[t]*(s**t)
        #                         y += poly_geo[4+t]*(s**t)
        #                     before_rotation_points.append([x,y,z])
        #                 after_translation_points = []
                        

        #                 if clink.get_from_links() !=[]:
        #                     if clink.get_from_links()[-1].lane_mark_left !=[]:
        #                         from_lane_node_point = clink.get_from_links()[-1].lane_mark_left[-1].points[-1]
        #                     else:
        #                         print('no lane node', link_id)
        #                         # from lane node 
        #                         link_vec = (clink.points[1] - clink.points[0])/np.linalg.norm(clink.points[1] - clink.points[0])
        #                         from_lane_node_point = 1.7*(test.coordinate_transform_z(-90, [link_vec]) + clink.points[0])
        #                         from_new_node = Node()
        #                         from_new_node.point = from_lane_node_point[0]
        #                         node_set = self.getLaneNodeSet()
        #                         node_set.append_node(from_new_node, create_new_key=True)
        #                 else:
        #                     print('no lane node', link_id)
        #                     # from lane node 
        #                     link_vec = (clink.points[1] - clink.points[0])/np.linalg.norm(clink.points[1] - clink.points[0])
        #                     from_lane_node_point = 1.7*(test.coordinate_transform_z(-90, [link_vec]) + clink.points[0])
        #                     from_new_node = Node()
        #                     from_new_node.point = from_lane_node_point[0]
        #                     node_set = self.getLaneNodeSet()
        #                     node_set.append_node(from_new_node, create_new_key=True)


        #                 if clink.get_to_links() != []:
        #                     if clink.get_to_links()[-1].lane_mark_left !=[]:
        #                         to_lane_node_point = clink.get_to_links()[-1].lane_mark_left[0].points[0]
        #                     else:
        #                         link_vec = (clink.points[-1] - clink.points[-2])/np.linalg.norm(clink.points[1] - clink.points[0])
        #                         to_lane_node_point = 1.7*(test.coordinate_transform_z(90, [link_vec]) + clink.points[0])
        #                         to_new_node = Node()
        #                         to_new_node.point = to_lane_node_point[0]
        #                         node_set = self.getLaneNodeSet()
        #                         node_set.append_node(to_new_node, create_new_key=True)
        #                 else:
        #                      # to lane node 
        #                     link_vec = (clink.points[-1] - clink.points[-2])/np.linalg.norm(clink.points[1] - clink.points[0])
        #                     to_lane_node_point = 1.7*(test.coordinate_transform_z(90, [link_vec]) + clink.points[0])
        #                     to_new_node = Node()
        #                     to_new_node.point = to_lane_node_point[0]
        #                     node_set = self.getLaneNodeSet()
        #                     node_set.append_node(to_new_node, create_new_key=True)


        #                 rotated_point = test.coordinate_transform_z(-heading, before_rotation_points)
                        
        #                 for point in rotated_point:
        #                     after_translation_points.append(point + from_lane_node_point[0])
                        
                        
        #                 lane_mark_points = np.vstack((np.array(after_translation_points), np.array(to_lane_node_point)))
                           
        #                 self.virtual_lane += 1
        #                 new_lane_id = 'VLM{}'.format(self.virtual_lane)
        #                 new_line = LaneBoundary(idx=new_lane_id)
        #                 new_line.lane_type_def = 'none'

        #                 new_line.set_points(lane_mark_points)
        #                 new_line.set_from_node(from_new_node)
        #                 new_line.set_to_node(to_new_node)
                       
        #                 self.getLaneBoundarySet().append_line(new_line)
                    



        elif key == 16777235: # up
            if modifiers & Qt.ControlModifier:
                if modifiers & Qt.ShiftModifier:
                    # shift + ctrl
                    point_move = 50
                else:
                    # only ctrl
                    point_move = 5
            else:
                if modifiers & Qt.ShiftModifier:
                    # only shift
                    point_move = 15
                else:
                    point_move = 1
            Logger.log_trace('point_move: {}'.format(point_move))
            self.change_point_in_line(point_move)

        elif key == 16777237: # down 
            if modifiers & Qt.ControlModifier:
                if modifiers & Qt.ShiftModifier:
                    # shift + ctrl
                    point_move = -50
                else:
                    # only ctrl
                    point_move = -5
            else:
                if modifiers & Qt.ShiftModifier:
                    # only shift]
                    point_move = -15
                else:
                    point_move = -1
            Logger.log_trace('point_move: {}'.format(point_move))
            self.change_point_in_line(point_move)

        elif key == 93: # ] for debug mode
            # NOTE: 여기에 중단점을 적용해서 debug 모드에서 자유롭게 사용한다
            Logger.log_info('Entered Debug Mode') 
            Logger.log_info('Exiting Debug Mode')

        elif key == Qt.Key_C:
            self.connect_nodes()
    
        elif key == 16777232: # home
            # 처음 위치 가리키도록 
            self.set_point_in_line(0)

        elif key == 16777233: # end
            # 마지막 위치 가리키도록 
            self.set_point_in_line(-1)

        elif key == 16777249:
            self.control_key_pressed = True


        # elif key == Qt.Key_W:
        #     self.point_list = []
        #     self.input_line_points = True
        #     Logger.log_info('start, put points on line')

        # elif key == Qt.Key_E:
        #     self.input_line_points = False
        #     Logger.log_info('end, put points on line')
            
        #     if self.check_item == MGeoItem.LANE_BOUNDARY.name:
        #         self.add_line_points()
        #     elif self.check_item == MGeoItem.LINK.name:
        #         self.add_line_points()
        #     elif self.check_item == MGeoItem.LANE_NODE.name:
        #         self.move_point()


        # elif key == Qt.Key_O:
        #     links = self.getLinkSet().lines
        #     road_id_list = []
        #     for link_id in links:
        #         clink = links[link_id]
        #         if clink.road_id in road_id_list:
                    
        #             continue
                    
        #         for link_id_2 in links:
        #             if  clink.idx != links[link_id_2].idx  \
        #                 and  clink.points[0][0] == links[link_id_2].points[0][0] \
        #                     and  clink.points[1][0] == links[link_id_2].points[1][0]:
        #                 road_id_list.append(links[link_id_2].road_id)
        #                 break
        #     list_sp = [] 
        #     for link_id in links:
        #         if links[link_id].road_id in road_id_list:
        #             sp_dict = {'type': MGeoItem.LINK, 'id': link_id}
        #             list_sp.append(sp_dict)
        #     self.delete_item(list_sp)

        #     for link_id in links:
        #         clink = links[link_id]
        #         if clink.link_type == 'none':
        #             clink.link_type = 'driving'

        # elif key == Qt.Key_L:
        #     nodes = self.getNodeSet().nodes
        #     links = self.getLinkSet().lines
        #     lane_nodes = self.getLaneNodeSet().nodes
        #     lanes = self.getLaneBoundarySet().lanes
        #     for node_id in nodes:
        #         cnode = nodes[node_id]
        #         cnode.from_links = list()
        #         cnode.to_links = list()

        #     for link_id in links:
        #         clink = links[link_id]
        #         clink.from_node = None
        #         clink.to_node = None
        #         start_point = clink.points[0]
        #         end_point = clink.points[-1]
                
        #         dist_threshold = 0.1
        #         min_dist = 0.1
        #         start_node = None
        #         for node_id in nodes:
        #             node_point = nodes[node_id].point
        #             pos_vector = start_point - node_point
        #             start_dist = np.linalg.norm(pos_vector, ord=2)
        #             if start_dist < min_dist:
        #                 min_dist = start_dist
        #                 start_node = nodes[node_id]
        #         if start_node == None:
        #             print('start None', link_id)

        #         min_dist = 0.1
        #         end_node = None
        #         for node_id in nodes:
        #             node_point = nodes[node_id].point
        #             pos_vector = end_point - node_point
        #             end_dist = np.linalg.norm(pos_vector, ord=2)
        #             if end_dist < min_dist:
        #                 min_dist = end_dist
        #                 end_node = nodes[node_id]
        #         if end_node == None:
        #             print('end None', link_id)

        #         if start_node is not None:
        #             clink.set_from_node(start_node)
        #             # clink.from_node.to_links.append(clink)
        #             # Logger.log_info('start_node result: {}'.format(clink.idx))
        #         if end_node is not None:
        #             clink.set_to_node(end_node)
        #             # clink.to_node.add_from_links(clink)
        #             # Logger.log_info('end_node result: {}'.format(clink.idx))
                
        #         if clink.to_node == None:
        #             node_set = self.getNodeSet()
        #             new_node = Node()
        #             new_node.point = clink.points[-1]
        #             node_set.append_node(new_node, create_new_key=True)
        #             clink.set_to_node(new_node)
                
        #         elif clink.from_node == None:
        #             node_set = self.getNodeSet()
        #             new_node = Node()
        #             new_node.point = clink.points[0]
        #             node_set.append_node(new_node, create_new_key=True)
        #             clink.set_from_node(new_node)
            
        #     #  lane boundary
        #     for node_id in lane_nodes:
        #         cnode = lane_nodes[node_id]
        #         cnode.from_links = list()
        #         cnode.to_links = list()

        #     for link_id in lanes:
        #         clink = lanes[link_id]
        #         clink.from_node = None
        #         clink.to_node = None
        #         start_point = clink.points[0]
        #         end_point = clink.points[-1]
                
        #         dist_threshold = 0.1
        #         min_dist = 0.001
        #         start_node = None
        #         for node_id in lane_nodes:
        #             node_point = lane_nodes[node_id].point
        #             pos_vector = start_point - node_point
        #             start_dist = np.linalg.norm(pos_vector, ord=2)
        #             if start_dist < min_dist:
        #                 min_dist = start_dist
        #                 start_node = lane_nodes[node_id]
        #         if start_node == None:
        #             print('start None', link_id)

        #         min_dist = 0.001
        #         end_node = None
        #         for node_id in lane_nodes:
        #             node_point = lane_nodes[node_id].point
        #             pos_vector = end_point - node_point
        #             end_dist = np.linalg.norm(pos_vector, ord=2)
        #             if end_dist < min_dist:
        #                 min_dist = end_dist
        #                 end_node = lane_nodes[node_id]
        #         if end_node == None:
        #             print('end None', link_id)

        #         if start_node is not None:
        #             clink.set_from_node(start_node)
        #             # clink.from_node.to_links.append(clink)
        #             # Logger.log_info('start_node result: {}'.format(clink.idx))
        #         if end_node is not None:
        #             clink.set_to_node(end_node)
        #             # clink.to_node.add_from_links(clink)
        #             # Logger.log_info('end_node result: {}'.format(clink.idx))
                
        #         if clink.to_node == None:
        #             node_set = self.getLaneNodeSet()
        #             new_node = Node()
        #             new_node.point = clink.points[-1]
        #             node_set.append_node(new_node, create_new_key=True)
        #             clink.set_to_node(new_node)
                
        #         elif clink.from_node == None:
        #             node_set = self.getLaneNodeSet()
        #             new_node = Node()
        #             new_node.point = clink.points[0]
        #             node_set.append_node(new_node, create_new_key=True)
        #             clink.set_from_node(new_node)

        #     Logger.log_info('links and nodes are redefined')


        


        # elif key == Qt.Key_M:
        #     #when link has node but set of link.points do not have point of node
        #     links = self.getLinkSet().lines
        #     lanemarks = self.getLaneBoundarySet().lanes
        #     for link_id in links:
        #         clink = links[link_id]
        #         try:
        #             if clink.from_node.point not in clink.points:
        #                 clink.points = np.array([clink.from_node.point] + list(clink.points)) 
        #         except:
        #             pass
        #         try:
        #             if clink.to_node.point not in clink.points:
        #                 clink.points = np.array(list(clink.points) + [clink.to_node.point])
        #         except:
        #             pass
        #     for link_id in lanemarks:
        #         clink = lanemarks[link_id]
        #         try:
        #             if clink.from_node.point not in clink.points:
        #                 clink.points = np.array([clink.from_node.point] + list(clink.points))
        #         except:
        #             pass
        #         try:    
        #             if clink.to_node.point not in clink.points:
        #                 clink.points = np.array(list(clink.points) + [clink.to_node.point])
        #         except:
        #             pass
        #     Logger.log_info('to and from node points are appended')
        
        # elif key == Qt.Key_H:
        #     nodes = self.getNodeSet().nodes
        #     for node_id in nodes:
        #         cnode = nodes[node_id]
        #         if len(cnode.to_links) == 0 or len(cnode.from_links) == 0:
        #             print(cnode.idx, len(cnode.to_links), len(cnode.from_links))
        # both link and lane_ boundary do not have same direction  
        
        # elif key == Qt.Key_I:
        #     links = self.getLinkSet().lines
        #     lanemarks = self.getLaneBoundarySet().lanes
        #     half_width_threshold = 2
        #     for link_id in links:
        #         clink = links[link_id]
        #         if clink.lane_mark_left != [] and clink.lane_mark_right != []:
        #             # Logger.log_info('link id: {} has some other lane boundarys'.format(link_id))
        #             right_first = clink.lane_mark_right[0].points[0]
        #             left_first = clink.lane_mark_left[0].points[0]
        #             link_first = clink.points[0]
        #             link_last = clink.points[-1]
        #             left_vector = link_first - left_first
        #             start_dist_left = np.linalg.norm(left_vector, ord=2)
        #             right_vector = link_first - right_first
        #             start_dist_right = np.linalg.norm(right_vector, ord=2)
        #             link_dir = clink.points[1] - clink.points[0]
        #             if start_dist_left > half_width_threshold:
        #                 clink.lane_mark_left = []
        #                 for lanemark_id in lanemarks:
        #                     clanemark = lanemarks[lanemark_id]
        #                     left_vector = link_first - clanemark.points[0]
        #                     start_dist_left = np.linalg.norm(left_vector, ord=2)
        #                     if start_dist_left < 2 and np.cross(link_dir, left_vector)[-1] >0 :
        #                         clink.lane_mark_left = clink.lane_mark_left + [clanemark]
        #                         break
        #                 if clink.lane_mark_left == []:
        #                     for lanemark_id in lanemarks:
        #                         clanemark = lanemarks[lanemark_id]
        #                         left_vector = link_last - clanemark.points[-1]
        #                         start_dist_left = np.linalg.norm(left_vector, ord=2)
        #                         if start_dist_left < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                             clink.lane_mark_left = clink.lane_mark_left + [clanemark]
        #                 if clink.lane_mark_left == []:
        #                     print(clink)
        #             else:
        #                 continue

                        
        #             if start_dist_right > half_width_threshold:
        #                 clink.lane_mark_right = []
        #                 for lanemark_id in lanemarks:
        #                     clanemark = lanemarks[lanemark_id]
        #                     right_vector = link_first - clanemark.points[0]
        #                     start_dist_right = np.linalg.norm(right_vector, ord=2)
        #                     if start_dist_right < 2 and np.cross(link_dir, right_vector)[-1] >0:
        #                         clink.lane_mark_right = clink.lane_mark_right + [clanemark]
                        
        #                 if clink.lane_mark_right == []:
        #                     for lanemark_id in lanemarks:
        #                         clanemark = lanemarks[lanemark_id]
        #                         left_vector = link_last - clanemark.points[-1]
        #                         start_dist_right = np.linalg.norm(left_vector, ord=2)
        #                         if start_dist_right < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                             clink.lane_mark_right = clink.lane_mark_right + [clanemark]
        #                 if clink.lane_mark_right == []:
        #                     print(clink)

        #         elif clink.lane_mark_left == [] and clink.lane_mark_right != []:
        #             Logger.log_info('link id: {} doesn`t have left lane boundary'.format(link_id))
        #             for lanemark_id in lanemarks:
        #                 clanemark = lanemarks[lanemark_id]
        #                 left_vector = link_first - clanemark.points[0]
        #                 start_dist_left = np.linalg.norm(left_vector, ord=2)
        #                 if start_dist_left < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                     clink.lane_mark_left = clink.lane_mark_left + [clanemark]
                    
        #             if clink.lane_mark_left == []:
        #                 for lanemark_id in lanemarks:
        #                     clanemark = lanemarks[lanemark_id]
        #                     left_vector = link_last - clanemark.points[-1]
        #                     start_dist_left = np.linalg.norm(left_vector, ord=2)
        #                     if start_dist_left < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                         clink.lane_mark_left = clink.lane_mark_left + [clanemark]
        #             if clink.lane_mark_left == []:
        #                 print(clink)


        #         elif clink.lane_mark_right == [] and clink.lane_mark_left != []:
        #             Logger.log_info('link id: {} doesn`t have right lane boundary'.format(link_id))
        #             for lanemark_id in lanemarks:
        #                 clanemark = lanemarks[lanemark_id]
        #                 right_vector = link_first - clanemark.points[0]
        #                 start_dist_right = np.linalg.norm(right_vector, ord=2)
        #                 if start_dist_right < 2 and np.cross(link_dir, right_vector)[-1] >0:
        #                     clink.lane_mark_right = clink.lane_mark_right + [clanemark]
                    
        #             if clink.lane_mark_right == []:
        #                 for lanemark_id in lanemarks:
        #                     clanemark = lanemarks[lanemark_id]
        #                     left_vector = link_last - clanemark.points[-1]
        #                     start_dist_right = np.linalg.norm(left_vector, ord=2)
        #                     if start_dist_right < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                         clink.lane_mark_right = clink.lane_mark_right + [clanemark]
        #             if clink.lane_mark_right == []:
        #                 print(clink)

        #         else:
        #             Logger.log_info('link id: {} doesn`t have any lane boundary'.format(link_id))

        #             for lanemark_id in lanemarks:
        #                 clanemark = lanemarks[lanemark_id]
        #                 left_vector = link_first - clanemark.points[0]
        #                 start_dist_left = np.linalg.norm(left_vector, ord=2)
        #                 if start_dist_left < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                     clink.lane_mark_left = clink.lane_mark_left + [clanemark]
                    
        #             if clink.lane_mark_left == []:
        #                 for lanemark_id in lanemarks:
        #                     clanemark = lanemarks[lanemark_id]
        #                     left_vector = link_last - clanemark.points[-1]
        #                     start_dist_left = np.linalg.norm(left_vector, ord=2)
        #                     if start_dist_left < 2 and np.cross(link_dir, left_vector)[-1] >0:
        #                         clink.lane_mark_left = clink.lane_mark_left + [clanemark]
                    
        #             for lanemark_id in lanemarks:
        #                 clanemark = lanemarks[lanemark_id]
        #                 right_vector = link_first - clanemark.points[0]
        #                 start_dist_right = np.linalg.norm(right_vector, ord=2)
        #                 if start_dist_right < 2 and np.cross(link_dir, right_vector)[-1] >0:
        #                     clink.lane_mark_right = clink.lane_mark_right + [clanemark]
                    
        #             if clink.lane_mark_right == []:
        #                 for lanemark_id in lanemarks:
        #                     clanemark = lanemarks[lanemark_id]
        #                     right_vector = link_last - clanemark.points[-1]
        #                     start_dist_right = np.linalg.norm(right_vector, ord=2)
        #                     if start_dist_right < 2 and np.cross(link_dir, right_vector)[-1] >0:
        #                         clink.lane_mark_right = clink.lane_mark_right + [clanemark]

        # # redefine ego_lane
        # elif key == Qt.Key_Y:
        #     links = self.getLinkSet().lines
        #     for link_id in links:
        #         clink = links[link_id]
        #         clink.ego_lane = -1 
        #     Logger.log_info('ego_lanes are redefined'.format(link_id))

        # #NOTE(chi) lane node add
        # elif key == Qt.Key_P:
        #     lanes = self.getLaneBoundarySet().lanes
        #     lane_nodes = self.getLaneNodeSet().nodes
        #     for lane_id in lanes:
        #         clane = lanes[lane_id]
        #         if clane.from_node is None:
        #             nw_node = Node()
        #             nw_node.point = clane.points[0]
        #             self.getLaneNodeSet().append_node(nw_node, create_new_key=True)
        #             print(lane_id)
        #         else:
        #             if clane.from_node.idx not in lane_nodes:
        #                 nw_node = Node()
        #                 nw_node.point = clane.points[0]
        #                 self.getLaneNodeSet().nodes[clane.from_node.idx] = nw_node
        #                 print(lane_id)
        #         if clane.to_node is None:
        #             nw_node = Node()
        #             nw_node.point = clane.points[-1]
        #             self.getLaneNodeSet().append_node(nw_node, create_new_key=True)
        #             print(lane_id)
        #         else:
        #             if clane.to_node.idx not in lane_nodes:
        #                 nw_node = Node()
        #                 nw_node.point = clane.points[-1]
        #                 self.getLaneNodeSet().nodes[clane.to_node.idx] = nw_node
        #                 print(lane_id)
                        
        # elif key == Qt.Key_T:
            
        #     lanes = self.getLaneBoundarySet().lanes
        #     lane_nodes = self.getLaneNodeSet().nodes
            
        #     road_candidate = []

        #    # if self.list_sp ==[]:
            
        #         #for self.getRoadSet().roads:
                    


        #   #  else:
        #      #   for item in self.list_sp:
        #        #     if item['type'] == MGeoItem.ROAD:





        #     for lane_id in lanes:
        #         clane = lanes[lane_id]
        #         if clane.from_node is None:
        #             nw_node = Node()
        #             nw_node.point = clane.points[0]
        #             self.getLaneNodeSet().append_node(new_node, create_new_key=True)
        #         else:
        #             if clane.from_node.idx not in lane_nodes:
        #                 nw_node = Node()
        #                 nw_node.point = clane.points[0]
        #                 self.getLaneNodeSet().nodes[clane.from_node.idx] = nw_node

                    
        #         if clane.to_node is None:
        #             nw_node = Node()
        #             nw_node.point = clane.points[-1]
        #             self.getLaneNodeSet().append_node(new_node, create_new_key=True)
        #         else:
        #             if clane.to_node.idx not in lane_nodes:
        #                 nw_node = Node()
        #                 nw_node.point = clane.points[-1]
        #                 self.getLaneNodeSet().nodes[clane.to_node.idx] = nw_node
        #         clink.points[0] = clink.from_node.point
        #         clink.points[-1] = clink.to_node.point

        # elif key == Qt.Key_L:
        #     lanes = self.getLaneBoundarySet().lanes
        #     for id, lane in lanes.items():
        #         lane.points[0] = lane.from_node.point
        #         lane.points[-1] = lane.to_node.point
        #         if list(lane.points[0]) == list(lane.points[1]):
        #             if len(lane.points) == 2:
        #                 continue
        #             lane.points[1] = (lane.points[0] + lane.points[2])/2
        #         if list(lane.points[-1]) == list(lane.points[-2]):
        #             if len(lane.points) == 2:
        #                 continue
        #             lane.points[-2] = (lane.points[-1] + lane.points[-3])/2


        
        # elif key == Qt.Key_M:
        #     nodes = self.getNodeSet(self.mgeo_key).nodes
        #     for node in nodes:
        #         to_links = self.getNodeSet(self.mgeo_key).nodes[node].to_links
        #         for i in to_links:
        #             if node != self.getLinkSet(self.mgeo_key).lines[i.idx].from_node.idx:
        #                 sp_dict = {'type': MGeoItem.NODE, 'id': node}
        #                 self.list_highlight2.append(sp_dict)
        #         from_links = self.getNodeSet(self.mgeo_key).nodes[node].from_links
        #         for j in from_links:
        #             if node != self.getLinkSet(self.mgeo_key).lines[j.idx].to_node.idx:
        #                 sp_dict = {'type': MGeoItem.NODE, 'id': node}
        #                 self.list_highlight2.append(sp_dict)

        # link points의 첫번째/마지막 값 이용해서 중간 점 높이(고도) 조절 >> 튀는 값 제거하기 위해
        # elif key == Qt.Key_J:
        #     lines = self.getLinkSet(self.mgeo_key).lines
        #     for i in self.list_sp:
        #         line = i['id']
        #         new_points = []
        #         from_point_z = self.getLinkSet(self.mgeo_key).lines[line].from_node.point[2]
        #         to_point_z = self.getLinkSet(self.mgeo_key).lines[line].to_node.point[2]
        #         lens = len(self.getLinkSet(self.mgeo_key).lines[line].points)
        #         dd = abs((from_point_z - to_point_z)/lens)
        #         for i, pit in enumerate(self.getLinkSet(self.mgeo_key).lines[line].points):
        #             if from_point_z > to_point_z:
        #                 new_point = [pit[0], pit[1], from_point_z - (i*dd)]
        #             else:
        #                 new_point = [pit[0], pit[1], from_point_z + (i*dd)]
        #             new_points.append(new_point)
        #         new_points = np.array(new_points)
        #         edit_link.update_link(lines, self.getNodeSet(self.mgeo_key).nodes, self.getLinkSet(self.mgeo_key).lines[line], 'points', self.getLinkSet(self.mgeo_key).lines[line].points, new_points)
        

    def keyReleaseEvent(self, input_key):
        key = input_key.key()
        modifiers = QApplication.keyboardModifiers()

        if key == 16777249:
            self.control_key_pressed = False
                    
    # 마우스 클릭 
    def mousePressEvent(self, event):
        self.lastPos = event.pos()
        self.makeCurrent()
        self.drag_for_select = False

        # 마우스 좌클릭으로 드래그
        if event.buttons() == Qt.LeftButton:
            self.drag_start = event.pos()
            self.tree_attr.clear()
            self.mouseClickWindow(event.x(), event.y())
            self.updateMgeoPropWidget(self.sp)

        if event.buttons() == Qt.RightButton:
            if self.input_line_points is False:
                winX = event.x()
                winY = self.viewport[3] - event.y()
                winZ = glReadPixels(winX, int(winY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
                select_point = gluUnProject(winX, winY, winZ, self.modelview, self.projection, self.viewport)

                self.point_list = np.array([select_point[0], select_point[1], select_point[2]])

        self.doneCurrent()


    def mouseReleaseEvent(self, event):
        self.drag_for_select = False

    """
    선택된 canvas 위치에서 mgeo 아이템 사이 거리 구하기
    """
    # point - point 사이 거리 구하기 (node, tl, ts 타입)
    def dist_point_to_point(self, items, select_point):
        min_dist = 3
        min_dist_id = None
        # xlim = [select_point[0] - 10, select_point[0] + 10]
        # ylim = [select_point[1] - 10, select_point[1] + 10]
        for item in items:
            if items[item].is_out_of_xy_range(self.xlim, self.ylim):
                continue
            if item == self.bsp:
                continue
            dist = np.sqrt(sum(((items[item].point[0:2]-select_point[0:2])**2)))
            if min_dist > dist:
                min_dist_id = item
                min_dist = dist
        if min_dist >= 3:
            return
        return min_dist_id

    # point - point 사이 거리 구하기 (node, tl, ts 타입)
    def find_min_distance_point_item(self, items, sp_items, select_line):
        min_dist = 3
        min_dist_id = None

        for sp_item in sp_items:
            item = sp_item['id']
            
            if item == self.bsp:
                continue
            if item not in items :
                continue

            dist = self.distance_between_point_and_line(select_line, items[item].point)

            if min_dist > dist:
                min_dist_id = item
                min_dist = dist
        if min_dist >= 3:
            return
        return min_dist_id

    def find_min_distance_points_item(self, items, sp_items, select_line, item_type):
        min_dist = 2
        min_dist_id = None

        for sp_item in sp_items:
            item_id = sp_item['id']
            
            if item_id == self.bsp:
                continue
            if item_id not in items :
                continue

            if item_type == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                points = items[item_id].get_synced_signal_points()
            elif item_type == MGeoItem.INTERSECTION_CONTROLLER:
                points = items[item_id].get_intersection_controller_points()
            elif item_type == MGeoItem.JUNCTION:
                points = items[item_id].get_jc_node_points()
            else:
                points = [items[item_id].point]

            for point in points :
                dist = self.distance_between_point_and_line(select_line, point)

                if min_dist > dist:
                    min_dist_id = item_id
                    min_dist = dist

        if min_dist >= 2:
            return
        return min_dist_id

    def distance_between_point_and_line(self, line, point) :
        line_point_0 = np.array(line[0])
        line_point_1 = np.array(line[1])

        line_vector = line_point_1  - line_point_0
        line_vector_mag = np.linalg.norm(line_vector, ord=2)

        item_point = np.array(point)
        point_to_line_vector = line_point_0 - item_point

        if line_vector_mag == 0 :
            dist = np.sqrt(sum(((item_point[0:2]-line[0][0:2])**2)))
        else :
            dist = np.linalg.norm(np.cross(point_to_line_vector, line_vector), ord=2) / line_vector_mag

        return dist

    def distance_between_line_and_segment(self, line, segment) :
        line_vector = line[1] - line[0]
        seg_vector = segment[1] - segment[0]

        v_cross = np.cross(line_vector, seg_vector)
        v_cross_abs = np.linalg.norm(v_cross, ord=2)
        if v_cross_abs == 0 :
            dist = np.abs(np.linalg.norm(np.cross(line_vector, line[0]-segment[0]), ord=2)) / np.linalg.norm(line_vector, ord=2)
        else :
            dist_0 = self.distance_between_point_and_line(line, segment[0])
            dist_1 = self.distance_between_point_and_line(line, segment[1])
            dist_mid = self.distance_between_point_and_line(line, (segment[0] + segment[1])/2)

            if dist_mid < dist_0 and dist_mid < dist_1 :
                dist = np.abs(np.inner(v_cross, line[0]-segment[0])) / v_cross_abs
            else :
                dist = min(dist_0, dist_1)

        return dist

    def find_min_distance_line_item(self, items, sp_items, select_line):
        min_dist = 3
        min_dist_id = None

        for sp_item in sp_items:
            item = sp_item['id']
            
            if item == self.bsp:
                continue
            if item not in items :
                continue

            item_points = np.array(items[item].points)

            for p_idx in range(len(item_points)-1) :
                point_0 = item_points[p_idx]
                point_1 = item_points[p_idx + 1]

                dist = self.distance_between_line_and_segment(np.array(select_line), np.array([point_0, point_1]))

                if min_dist > dist:
                    min_dist_id = item
                    min_dist = dist

        if min_dist >= 3:
            return
        return min_dist_id

    def find_min_distance_planar_item(self, items, sp_items, select_line, item_type):
        min_dist_z = None
        min_dist_id = None

        for sp_item in sp_items:
            item = sp_item['id']
            
            if item == self.bsp:
                continue
            if item not in items :
                continue

            if item_type == MGeoItem.ROADPOLYGON :
                item_points = np.array(items[item].points)
                item_faces = np.array(items[item].faces)
            else :
                poly_data = vtkPolyByPoints(np.array(items[item].points))
                poly_data = vtkTrianglePoly(poly_data)
                mesh_data = vtkPoly_to_MeshData(poly_data)
                item_points = mesh_data[0]
                item_faces = mesh_data[1]

            select_vector = np.array(select_line[1]) - np.array(select_line[0])
            for face in item_faces : 
                face_point_0 = np.array(item_points[face[0]])
                face_point_1 = np.array(item_points[face[1]])
                face_point_2 = np.array(item_points[face[2]])

                face_normal = np.cross((face_point_2-face_point_1), (face_point_1-face_point_0))
                plane_d = - np.inner(face_normal, face_point_0)
                denominator = np.inner(face_normal, select_vector)
                if denominator == 0 :
                    continue

                intersect_t = -(np.inner(face_normal, np.array(select_line[0])) + plane_d) / denominator
                intersect_point = intersect_t * select_vector + np.array(select_line[0])

                intersect_x = intersect_point[0]
                intersect_y = intersect_point[1]
                intersect_z = intersect_point[2]

                intersect_count = 0
                if min(face_point_0[0], face_point_1[0]) < intersect_x and max(face_point_0[0], face_point_1[0]) > intersect_x :
                    check_y = ((intersect_x - face_point_0[0]) / (face_point_1[0] - face_point_0[0]))*(face_point_1[1] - face_point_0[1]) + face_point_0[1]
                    if check_y < intersect_y :
                        intersect_count += 1

                if min(face_point_1[0], face_point_2[0]) < intersect_x and max(face_point_1[0], face_point_2[0]) > intersect_x :
                    check_y = ((intersect_x - face_point_1[0]) / (face_point_2[0] - face_point_1[0]))*(face_point_2[1] - face_point_1[1]) + face_point_1[1]
                    if check_y < intersect_y :
                        intersect_count += 1

                if min(face_point_2[0], face_point_0[0]) < intersect_x and max(face_point_2[0], face_point_0[0]) > intersect_x :
                    check_y = ((intersect_x - face_point_2[0]) / (face_point_0[0] - face_point_2[0]))*(face_point_0[1] - face_point_2[1]) + face_point_2[1]
                    if check_y < intersect_y :
                        intersect_count += 1

                if intersect_count %2 != 0 :
                    min_dist_id = item
                    #가장 z값이 큰 것을 우선으로
                    if min_dist_z == None or min_dist_z < intersect_z :
                        min_dist_z = intersect_z
                    break
                    
        return min_dist_id

    def find_min_distance_crosswalk_item(self, items, sp_items, select_line):

        min_dist_z = None
        min_dist_id = None

        min_dist_tl = None
        min_dist_tl_id = None

        for sp_item in sp_items:
            item = sp_item['id']
            
            if item == self.bsp:
                continue
            if item not in items :
                continue

            items[item].scw_dic
            items[item].tl_dic

            for tl_id in items[item].tl_dic :
                tl = items[item].tl_dic[tl_id]
                dist = self.distance_between_point_and_line(select_line, tl.point)
                if min_dist_tl == None or min_dist_tl > dist :
                    min_dist_tl = dist
                    min_dist_tl_id = item

            for scw_id in items[item].scw_dic :
                scw = items[item].scw_dic[scw_id]

                poly_data = vtkPolyByPoints(np.array(scw.points))
                poly_data = vtkTrianglePoly(poly_data)
                mesh_data = vtkPoly_to_MeshData(poly_data)
                item_points = mesh_data[0]
                item_faces = mesh_data[1]

                select_vector = np.array(select_line[1]) - np.array(select_line[0])
                for face in item_faces : 
                    face_point_0 = np.array(item_points[face[0]])
                    face_point_1 = np.array(item_points[face[1]])
                    face_point_2 = np.array(item_points[face[2]])

                    face_normal = np.cross((face_point_2-face_point_1), (face_point_1-face_point_0))
                    plane_d = - np.inner(face_normal, face_point_0)
                    denominator = np.inner(face_normal, select_vector)
                    if denominator == 0 :
                        continue

                    intersect_t = -(np.inner(face_normal, np.array(select_line[0])) + plane_d) / denominator
                    intersect_point = intersect_t * select_vector + np.array(select_line[0])

                    intersect_x = intersect_point[0]
                    intersect_y = intersect_point[1]
                    intersect_z = intersect_point[2]

                    intersect_count = 0
                    if min(face_point_0[0], face_point_1[0]) < intersect_x and max(face_point_0[0], face_point_1[0]) > intersect_x :
                        check_y = ((intersect_x - face_point_0[0]) / (face_point_1[0] - face_point_0[0]))*(face_point_1[1] - face_point_0[1]) + face_point_0[1]
                        if check_y < intersect_y :
                            intersect_count += 1

                    if min(face_point_1[0], face_point_2[0]) < intersect_x and max(face_point_1[0], face_point_2[0]) > intersect_x :
                        check_y = ((intersect_x - face_point_1[0]) / (face_point_2[0] - face_point_1[0]))*(face_point_2[1] - face_point_1[1]) + face_point_1[1]
                        if check_y < intersect_y :
                            intersect_count += 1

                    if min(face_point_2[0], face_point_0[0]) < intersect_x and max(face_point_2[0], face_point_0[0]) > intersect_x :
                        check_y = ((intersect_x - face_point_2[0]) / (face_point_0[0] - face_point_2[0]))*(face_point_0[1] - face_point_2[1]) + face_point_2[1]
                        if check_y < intersect_y :
                            intersect_count += 1

                    if intersect_count %2 != 0 :
                        min_dist_id = item
                        if min_dist_z == None or min_dist_z < intersect_z :
                            min_dist_z = intersect_z
                        break
                    
        if min_dist_tl_id is not None and min_dist_id is None :
            return min_dist_tl_id
        else :
            return min_dist_id

    # point - points 사이 거리 구하기 (junction 타입, 아이템 타입 입력해야한다.)
    def dist_point_to_points(self, items, select_point, items_type):
        min_dist = 2
        min_dist_id = None
        for item_id in items:
            to_list = []
            points = []
            if items_type == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                to_list = items[item_id].signal_set.to_list()
                points = items[item_id].get_synced_signal_points()

            elif items_type == MGeoItem.INTERSECTION_CONTROLLER:
                id_list = items[item_id].get_signal_id_list()
                to_list = []
                for idx in id_list:
                    to_list.append(self.getTLSet(self.mgeo_key).signals[idx])
                points = items[item_id].get_intersection_controller_points()

            elif items_type == MGeoItem.JUNCTION:
                to_list = items[item_id].jc_nodes
                points = items[item_id].get_jc_node_points()
            
            else:
                points = [items[item_id].point]

            for item in to_list:
                if item.is_out_of_xy_range(self.xlim, self.ylim):
                    continue
                if item_id == self.bsp:
                    continue

            # if len(to_list) == 0:
            #     points = [items[item_id].point]

            for point in points:
                dist = np.sqrt(sum(((point[0:2]-select_point[0:2])**2)))
                if min_dist > dist:
                    min_dist_id = item_id
                    min_dist = dist
        if min_dist >= 2:
            return
        return min_dist_id

    # point - line 사이 거리 구하기 (link, road 타입)
    def dist_point_to_line(self, items, select_point):
        min_dist = 5
        min_dist_id = None
        # xlim = [select_point[0] - 10, select_point[0] + 10]
        # ylim = [select_point[1] - 10, select_point[1] + 10]

        for item in items:
            if items[item].is_out_of_xy_range(self.xlim, self.ylim):
                continue
            if item == self.bsp:
                continue

            item_points = items[item].points
            for item_point_intdex in  range(len(item_points) - 1):
                A = np.array(item_points[item_point_intdex][0:2])
                B = np.array(item_points[item_point_intdex+1][0:2])
                distance = np.dot(select_point[0:2]-A, B-A)/sum(np.square(B-A))
                if distance < 0:
                    qq = np.sqrt(sum((select_point[0:2]-A)**2))
                elif distance > 1: 
                    qq = np.sqrt(sum((select_point[0:2]-B)**2))
                else:
                    scaleAB = (B-A)*distance
                    perpendicular_point = A + scaleAB
                    perperdicular_p_to_p = select_point[0:2] - perpendicular_point
                    qq = np.sqrt(sum((perperdicular_p_to_p)**2))

                if min_dist > qq:
                    min_dist_id = item
                    min_dist = qq
        if min_dist >= 5:
            return

        return min_dist_id

    def dist_point_to_crosswalk(self, items, select_point):
        min_dist_tl_id = []
        min_dist_scw_id = []
        crosswalk_id = ''
        
        for item in items:
            min_dist_id_1 = self.dist_point_to_line(items[item].scw_dic, select_point)
            min_dist_id_2 = self.dist_point_to_point(items[item].tl_dic, select_point)
            
            if min_dist_id_1 is not None and min_dist_id_1 is not '':
                min_dist_scw_id.append(min_dist_id_1)

            if min_dist_id_2 is not None and min_dist_id_2 is not '':
                min_dist_tl_id.append(min_dist_id_2)
        
        for tl_id in min_dist_tl_id:
            tl = self.getTLSet(self.mgeo_key).signals[tl_id]
            crosswalk_id = tl.ref_crosswalk_id
        
        for scw_id in min_dist_scw_id:
            scw = self.getSingleCrosswalkSet().data[scw_id]
            crosswalk_id = scw.ref_crosswalk_id
        
        if crosswalk_id is not '':
            return crosswalk_id 
        else:
            return

    #mgeo item 삭제 되었을 때 rtree 에서 삭제
    def mgeo_item_deleted(self, mgeo_key, item_type, item_idx) :
        self.mgeo_rtree[mgeo_key].delete(item_type, item_idx)

    #mgeo item 업데이트 되었을 때 rtree 에서 업데이트 / idx 가 위치(point) 가 변경되었을 때 호출
    def mgeo_item_updated(self, mgeo_key, item_type, item_idx, item) :
        self.mgeo_rtree[mgeo_key].update(item_type, item_idx, item)

    #mgeo item 추가 되었을 때 rtree 에 추가
    def mgeo_item_added(self, mgeo_key, item_type, item) :
        self.mgeo_rtree[mgeo_key].insert(item, item_type)
           
    def mouseClickWindow(self, x, y):
        """Click된 좌표의 Object List 중 check된 MGeo Item을 가져온다"""
        self.list_highlight1.clear()

        if self.check_item is None:
            self.sp = None
            self.list_sp.clear()
            return
        winX = x
        winY = self.viewport[3] - y
        winZ = glReadPixels(winX, int(winY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        select_point = gluUnProject(winX, winY, winZ, self.modelview, self.projection, self.viewport)
        near_plane_point = gluUnProject(winX, winY, 0.0, self.modelview, self.projection, self.viewport)
        far_plane_point = gluUnProject(winX, winY, 1.0, self.modelview, self.projection, self.viewport)

        select_line = [near_plane_point, far_plane_point]
        sp_val = None
        sp_type = None
        new_id = None

        if self.input_line_points:
            if type(self.point_list) != list:
                self.point_list = []
            self.point_list.append(select_point)
            return

        select_vector = np.array(select_point) - np.array(near_plane_point)
        select_vector = select_vector / np.linalg.norm(select_vector)

        select_end_point = select_vector * 100 + np.array(select_point)
        select_start_point = -select_vector * 10 + np.array(select_point)

        min_x = min(select_end_point[0], select_start_point[0])
        max_x = max(select_end_point[0], select_start_point[0])
        min_y = min(select_end_point[1], select_start_point[1])
        max_y = max(select_end_point[1], select_start_point[1])
        min_z = min(select_end_point[2], select_start_point[2])
        max_z = max(select_end_point[2], select_start_point[2])

        if max_x - min_x < 10 :
            min_x = (max_x + min_x) / 2 - 5
            max_x = (max_x + min_x) / 2 + 5
        if max_y - min_y < 10 :
            min_y = (max_y + min_y) / 2 - 5
            max_y = (max_y + min_y) / 2 + 5
        if max_z - min_z < 10 :
            min_z = (max_z + min_z) / 2 - 5
            max_z = (max_z + min_z) / 2 + 5
        
        select_bbox = [min_x, min_y, min_z, max_x, max_y, max_z]

        # MGeo 아이템 선택하였을 때
        if self.check_item == MGeoItem.NODE.name:
            if len(self.node_list) == 0:
                return
            sp_type = MGeoItem.NODE
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_point_item(self.getNodeSet(self.mgeo_key).nodes, itsc_list, select_line)

        elif self.check_item == MGeoItem.LINK.name or self.check_item == ScenarioItem.Private or self.check_item == ScenarioItem.RoutingAction or self.check_item == ScenarioItem.AssignRouteAction or self.check_item == ScenarioItem.Entities:
            if len(self.link_list) == 0:
                return
            sp_type = MGeoItem.LINK
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_line_item(self.getLinkSet(self.mgeo_key).lines, itsc_list, select_line)

            # link 선택했을 때 양쪽 차선 같이 하이라이트 되도록
            if sp_val is not None:
                self.list_highlight1.clear()
                current_link = self.getLinkSet(self.mgeo_key).lines[sp_val]
                if current_link.lane_mark_left is not None:
                    for lane_mark in current_link.lane_mark_left:
                        lane_item = {'type': MGeoItem.LANE_BOUNDARY, 'id': lane_mark.idx}
                        self.list_highlight1.append(lane_item)
                if current_link.lane_mark_right is not None:
                    for lane_mark in current_link.lane_mark_right:
                        lane_item = {'type': MGeoItem.LANE_BOUNDARY, 'id': lane_mark.idx}
                        self.list_highlight1.append(lane_item)
                
                self.list_highlight3.clear()
                # current_link = self.getLinkSet(self.mgeo_key).lines[sp_val]
                if current_link.lane_ch_link_left is not None:
                    link_item = {'type': MGeoItem.LINK, 'id': current_link.lane_ch_link_left.idx}
                    self.list_highlight3.append(link_item)
                if current_link.lane_ch_link_right is not None:
                    link_item = {'type': MGeoItem.LINK, 'id': current_link.lane_ch_link_right.idx}
                    self.list_highlight3.append(link_item)
        
        elif self.check_item == MGeoItem.TRAFFIC_LIGHT.name:
            if len(self.tl_list) == 0:
                return
            sp_type = MGeoItem.TRAFFIC_LIGHT
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_point_item(self.getTLSet(self.mgeo_key).signals, itsc_list, select_line)

            if sp_val is not None:
                self.list_highlight1.clear()
                for link in self.getTLSet(self.mgeo_key).signals[sp_val].link_id_list:
                    link_item = {'type': MGeoItem.LINK, 'id': link}
                    self.list_highlight1.append(link_item)

        elif self.check_item == MGeoItem.TRAFFIC_SIGN.name:
            if len(self.ts_list) == 0:
                return
            sp_type = MGeoItem.TRAFFIC_SIGN
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_point_item(self.getTSSet(self.mgeo_key).signals, itsc_list, select_line)

            if sp_val is not None:
                self.list_highlight1.clear()
                for link in self.getTSSet(self.mgeo_key).signals[sp_val].link_id_list:
                    link_item = {'type': MGeoItem.LINK, 'id': link}
                    self.list_highlight1.append(link_item)


        elif self.check_item == MGeoItem.SYNCED_TRAFFIC_LIGHT.name:
            if len(self.synced_tl_list) == 0:
                return
            sp_type = MGeoItem.SYNCED_TRAFFIC_LIGHT
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_points_item(self.getSyncedTLSet(self.mgeo_key).synced_signals, itsc_list, select_line, sp_type)

        elif self.check_item == MGeoItem.INTERSECTION_CONTROLLER.name:
            if len(self.ic_list) == 0:
                return
            sp_type = MGeoItem.INTERSECTION_CONTROLLER
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_points_item(self.getIntersectionControllerSet(self.mgeo_key).intersection_controllers, itsc_list, select_line, sp_type)
    
        elif self.check_item == MGeoItem.JUNCTION.name:
            if len(self.junction_list) == 0:
                return
            sp_type = MGeoItem.JUNCTION
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_points_item(self.getJunctionSet(self.mgeo_key).junctions, itsc_list, select_line, sp_type)

        elif self.check_item == MGeoItem.ROAD.name: 
            if self.road_list is None:
                return
            roads = self.getRoadSet()
            lines = self.getLinkSet(self.mgeo_key).lines
            sp_type = MGeoItem.ROAD
            #TODO : 테스트 하고 적용 결정 필요
            #itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(MGeoItem.LINK, select_bbox)
            #min_dist_id = self.find_min_distance_line_item(self.getLinkSet(self.mgeo_key).lines, itsc_list, select_line)

            min_dist_id = self.dist_point_to_line(self.getLinkSet(self.mgeo_key).lines, select_point)
            if min_dist_id is not None:
                sp_val = lines[min_dist_id].road_id
                if sp_val not in self.getRoadSet().keys():
                    Logger.log_warning('[Road ID Error] id: {}'.format(sp_val))
                    return

        # 차선 데이터 수정을 위해
        elif self.check_item == MGeoItem.LANE_NODE.name:
            if len(self.lane_node_list) == 0:
                return
            sp_type = MGeoItem.LANE_NODE
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_point_item(self.getLaneNodeSet(self.mgeo_key).nodes, itsc_list, select_line)

        elif self.check_item == MGeoItem.LANE_BOUNDARY.name:
            if len(self.lane_marking_list) == 0:
                return
            sp_type = MGeoItem.LANE_BOUNDARY
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_line_item(self.getLaneBoundarySet(self.mgeo_key).lanes, itsc_list, select_line)

        elif self.check_item == MGeoItem.SINGLECROSSWALK.name:
            if len(self.single_crosswalk_list) == 0:
                return
            sp_type = MGeoItem.SINGLECROSSWALK
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_planar_item(self.getSingleCrosswalkSet(self.mgeo_key).data, itsc_list, select_line, sp_type)

        elif self.check_item == MGeoItem.ROADPOLYGON.name:
            if len(self.road_polygon_list) == 0:
                return
            sp_type = MGeoItem.ROADPOLYGON
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_planar_item(self.getRoadPolygonSet(self.mgeo_key).data, itsc_list, select_line, sp_type)

        elif self.check_item == MGeoItem.CROSSWALK.name:
            if len(self.crosswalk_list) == 0:
                return
            sp_type = MGeoItem.CROSSWALK
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_crosswalk_item(self.getCrosswalkSet(self.mgeo_key).data, itsc_list, select_line)

        elif self.check_item == MGeoItem.PARKING_SPACE.name:
            if len(self.parking_space_list) == 0:
                return
            sp_type = MGeoItem.PARKING_SPACE
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_planar_item(self.getParkingSpaceSet(self.mgeo_key).data, itsc_list, select_line, sp_type)

        elif self.check_item == MGeoItem.SURFACE_MARKING.name:
            if len(self.sm_list) == 0:
                return
            sp_type = MGeoItem.SURFACE_MARKING
            itsc_list = self.mgeo_rtree[self.mgeo_key].intersection(sp_type, select_bbox)
            sp_val = self.find_min_distance_planar_item(self.getSurfaceMarkingSet(self.mgeo_key).data, itsc_list, select_line, sp_type)


        # 시나리오 데이터 선택했을 때
        elif self.check_item == MScenarioItem.EGO_VEHICLE.name:
            point_xyz = self.mscenario.ego_vehicle.init_position['pos']
            dist = math.sqrt(pow(point_xyz['x'] - select_point[0], 2) + pow(point_xyz['y'] - select_point[1], 2))
            if dist < 2:
                sp_type = MScenarioItem.EGO_VEHICLE
                sp_val = self.mscenario.ego_vehicle.id

        elif self.check_item == MScenarioItem.SURROUNDING_VEHICLE.name:
            min_dist = 2
            min_dist_id = None
            for vhc in self.mscenario.vehicle_list:
                init_position = vhc.init_position
                if init_position['initPositionMode'] == 'absolute':
                    point_xyz = init_position['pos']
                    dist = math.sqrt(pow(point_xyz['x'] - select_point[0], 2) + pow(point_xyz['y'] - select_point[1], 2))
                    if dist < 2:
                        sp_type = MScenarioItem.SURROUNDING_VEHICLE
                        sp_val = vhc.id

        elif self.check_item == MScenarioItem.PEDESTRIAN.name:
            min_dist = 2
            min_dist_id = None
            for ped in self.mscenario.pedestrian_list:
                init_position = ped.init_position
                point_xyz = init_position['pos']
                dist = math.sqrt(pow(point_xyz['x'] - select_point[0], 2) + pow(point_xyz['y'] - select_point[1], 2))
                if dist < 2:
                    sp_type = MScenarioItem.PEDESTRIAN
                    sp_val = ped.id

        elif self.check_item == MScenarioItem.OBSTACLE.name:
            min_dist = 2
            min_dist_id = None
            for obs in self.mscenario.obstacle_list:
                init_transform = obs.init_transform
                point_xyz = init_transform['pos']
                dist = math.sqrt(pow(point_xyz['x'] - select_point[0], 2) + pow(point_xyz['y'] - select_point[1], 2))
                if dist < 2:
                    sp_type = MScenarioItem.OBSTACLE
                    sp_val = obs.id
                
        sp_dict = {'type': sp_type, 'id': sp_val}
        self.bsp = sp_val
        self.selectMgeoItem(sp_dict) # 여기서 self.list_sp가 업데이트된다
        self.update_inner_link_point_ptr()
        
        # check_convert = True
        
        # if check_convert == True:
        #     mgeo_planner_map = self.mgeo_planner_map

        #     converter = MGeoToOdrDataConverter()
        #     self.odr_data = converter.convert_selected(mgeo_planner_map, self.list_sp)
        #     return self.odr_data

        # find 함수 쓰고 다른 item 선택하거나/빈 화면 선택하면 highlight, find_item에서 제거
        if self.find_item is not None:
            self.list_highlight1.clear()
            self.find_item = None

    # 마우스 드래그 이벤트
    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = -1 * (event.y() - self.lastPos.y())
        # OpenGL에서 +y 방향이 아래쪽이다.
        # 이쪽에선 +y 방향이 위쪽이도록 고려한다.

        zoom_level = self.getZoomLevel()
        multiplier = zoom_level * 1/20 # 1/20은 zoom_level 1에서의 속도

        # Shift 또는 Alt 누를 때 이동 속도를 현재 속도에서 빠르게/느리게 변경 가능
        modifiers = QApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier:
            multiplier = multiplier * 2  
        elif modifiers & Qt.AltModifier:
            multiplier = multiplier / 2
        
        # TODO(hyjo): camera speed min/max 설정 되도록, -10 ~ 10 
        if self.camera_speed != 0:
            if self.camera_speed > 0:
                multiplier = multiplier * self.camera_speed
            elif self.camera_speed < 0:
                multiplier = -multiplier / self.camera_speed
            

        mv_x = dx * multiplier
        mv_y = dy * multiplier

        if event.buttons() & Qt.MiddleButton:
            self.setXYTranslate(mv_x, mv_y, self.zRot)
        elif event.buttons() & Qt.LeftButton:
            # 선택시 드래그로 인식해서 선택해제되는 현상이 있음
            if abs(dx) > 2 and abs(dx) > 2:
                self.drag_for_select = True

        # 마우스로 회전까지 해야할 때의 코드

        # if event.buttons() & Qt.LeftButton and self.view_mode == 'view_rotate':
        #     self.setXRotation(self.xRot + 0.2 * dy)
        #     # self.setYRotation(self.yRot - 0.2 * dx)
        
        # elif event.buttons() & Qt.LeftButton and self.view_mode == 'view_trans':
        #     self.setXYTranslate(mv_x, mv_y, self.zRot)

        self.lastPos = event.pos()
        self.setCameraMoveWidget()


    # 마우스 휠 이벤트
    def wheelEvent(self, event):
        wheel_val = event.angleDelta().y()
        self.setZoom(self.zoom, 0.1 * (wheel_val*10/12))
        self.setCameraMoveWidget()

    # 마우스 우클릭 이벤트
    def contextMenuEvent(self, event):
        """마우스 우클릭시 클릭된 포인트 옆에 drop down 메뉴를 표시한다"""
        contextMenu = QMenu(self)

        if self.sp is not None and self.sp['type'] is not None and QApplication.keyboardModifiers() != Qt.ControlModifier:
            
            # 참고: 데이터 타입에 따라 기능을 추가하고 싶은 경우
            # if self.sp['type'] == MGeoItem.NODE:
            #     sp_act = contextMenu.addAction("시작점")
            #     sp_act.triggered.connect(self.create_line_task_set_start_point)

            # MGeo (Map) Editor 부분
            if self.open_scenario == None:
                delete_act = contextMenu.addAction("Delete")
                delete_act.setShortcut('Delete')
                delete_act.triggered.connect(lambda:self.delete_item(self.list_sp))
                contextMenu.addSeparator()

                if self.sp['type'] == MGeoItem.TRAFFIC_LIGHT:
                    # 5. 신호등 타입 변경
                    edit_traffic_light = contextMenu.addAction("Edit TL")
                    edit_traffic_light.triggered.connect(self.action_edit_traffic_light)
                    # 3. 신호등/표지판에 연관된 link id list 입력하기
                    add_signal_to_link_id = contextMenu.addAction("Set signal(link_id_list)")
                    add_signal_to_link_id.triggered.connect(self.action_input_signal_link_id_list)
                    contextMenu.addSeparator()
                    # 7. Crosswalk 생성
                    add_create_crosswalk = contextMenu.addAction("Create Crosswalk")
                    add_create_crosswalk.triggered.connect(self.action_create_crosswalk) 
                    contextMenu.addSeparator()
                    # 8. Sync Signal Set 생성
                    add_create_sync_light_set = contextMenu.addAction("Create Sync Light Set")
                    add_create_sync_light_set.triggered.connect(self.create_sync_light_set) 
                    contextMenu.addSeparator()
                    # 9. 보행자 신호등 묶기
                    set_pedestrian = contextMenu.addAction("set pedestrian(link_id_list)")
                    set_pedestrian.triggered.connect(self.temp_create_syncTL_IntTL)
                    contextMenu.addSeparator()

                    add_create_intscn_ctlr_set = contextMenu.addAction("Create Intersection Controller Set")
                    add_create_intscn_ctlr_set.triggered.connect(self.action_make_intersecion_tl)

                elif self.sp['type'] == MGeoItem.LINK:
                    # 1. Link에 오른쪽/왼쪽 차선 변경 가능 link 입력하기
                    add_create_lane_change = contextMenu.addAction("Set link(right/left)")
                    add_create_lane_change.triggered.connect(self.add_create_lane_change)
                    # 2. Link에 related_signal 값 입력
                    add_related_signal = contextMenu.addAction("Set link(related_signal)")
                    add_related_signal.triggered.connect(self.add_related_signal_act)
                    contextMenu.addSeparator()
                    # 3. 신호등/표지판에 연관된 link id list 입력하기
                    add_signal_to_link_id = contextMenu.addAction("Set signal(link_id_list)")
                    add_signal_to_link_id.triggered.connect(self.action_input_signal_link_id_list)
                    # 4. Road ID 입력
                    add_road_id = contextMenu.addAction("Set Road ID")
                    add_road_id.triggered.connect(self.action_input_road_id)
                    contextMenu.addSeparator()
                    # 5. Fill points in Links
                    add_fill_points_in_links = contextMenu.addAction("Fill points in links")
                    add_fill_points_in_links.triggered.connect(self.fill_points_in_links)
                    # 6. 마우스 우클릭 링크 방향 반대로
                    reverse_link_points = contextMenu.addAction("Reverse Links Points")
                    reverse_link_points.triggered.connect(self.reverse_link_points)
                    # 7. 링크 양 옆 lane 넣기
                    set_LR_lane_mark = contextMenu.addAction("Set L/R LaneMark")
                    set_LR_lane_mark.triggered.connect(self.set_link_lane_boundary)
                    # 8. divide a Road
                    divide_a_road = contextMenu.addAction("Divide a Road")
                    divide_a_road.triggered.connect(lambda:set_link_lane_mark.cut_link_lane_boundary(self))
                                
                elif self.sp['type'] == MGeoItem.NODE:
                    # 1. node에 on stop node 입력
                    node_on_stop_line_act = contextMenu.addAction("On stop node (True)")
                    node_on_stop_line_act.triggered.connect(lambda:self.set_stop_node(True))
                    node_on_stop_line_act = contextMenu.addAction("On stop node (False)")
                    node_on_stop_line_act.triggered.connect(lambda:self.set_stop_node(False))
                    contextMenu.addSeparator()
                    node = self.getNodeSet(self.mgeo_key).nodes[self.sp['id']]
                    repair_overlapped_node_act = contextMenu.addAction("Repair Overlapped Node")                
                    repair_overlapped_node_act.triggered.connect(lambda:self.repair_overlapped_node(node))
                    contextMenu.addSeparator()
                    # 2. Set start point
                    set_start_point = contextMenu.addAction("Set start point")
                    set_start_point.triggered.connect(self.set_start_point_from_node)
                    # 3. Set stop point
                    set_stop_point = contextMenu.addAction("Set stop point")
                    set_stop_point.triggered.connect(self.set_stop_point_from_node)
                    # 4. Set end point
                    set_end_point = contextMenu.addAction("Set end point")
                    set_end_point.triggered.connect(self.set_end_point_from_node)

                elif self.sp['type'] == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                    # Intersection 생성
                    add_create_intersection = contextMenu.addAction("Create Intersection")
                    add_create_intersection.triggered.connect(self.action_create_intersection)      
                    contextMenu.addSeparator()

                elif self.sp['type'] == MGeoItem.SINGLECROSSWALK:
                    # 7. Crosswalk 생성
                    add_create_crosswalk = contextMenu.addAction("Create Crosswalk")
                    add_create_crosswalk.triggered.connect(self.action_create_crosswalk)      
                    contextMenu.addSeparator()
                
                elif self.sp['type'] == MGeoItem.ROAD:
                    recreate_ref_line = contextMenu.addAction("Move Reference Line")
                    recreate_ref_line.triggered.connect(self.recreate_ref_line)

                elif self.sp['type'] == MGeoItem.LANE_BOUNDARY:
                    # 6. 마우스 우클릭 lane_boundary 방향 반대로
                    reverse_link_points = contextMenu.addAction("Reverse Lanes Points")
                    reverse_link_points.triggered.connect(self.reverse_link_points)
                
                elif self.sp['type'] == MGeoItem.INTERSECTION_CONTROLLER:
                    export_v2xscriptableobject = contextMenu.addAction("Get V2X yaml")
                    export_v2xscriptableobject.triggered.connect(self.action_export_v2x)
                    highlight_v2x_lane = contextMenu.addAction('Highlight V2X Lane')
                    highlight_v2x_lane.triggered.connect(self.action_highlight_v2x_lane)
                
                    contextMenu.addSeparator()
                    setting_intTL_state_widget = contextMenu.addAction("Set IntTL State")
                    setting_intTL_state_widget.triggered.connect(self.setting_intTL_state)

                # point data MGeo 추가하기
                contextMenu.addSeparator() 
                create_mgeo_menu = QMenu("Add MGeo", self)
                create_mgeo_node = create_mgeo_menu.addAction("Add Node")
                create_mgeo_node.triggered.connect(lambda:self.add_new_mgeo_item(MGeoItem.NODE))
                create_mgeo_lane_node = create_mgeo_menu.addAction("Add Lane Node")
                create_mgeo_lane_node.triggered.connect(lambda:self.add_new_mgeo_item(MGeoItem.LANE_NODE))
                create_mgeo_ts = create_mgeo_menu.addAction("Add Sign")
                create_mgeo_ts.triggered.connect(lambda:self.add_new_mgeo_item(MGeoItem.TRAFFIC_SIGN))
                create_mgeo_tl = create_mgeo_menu.addAction("Add Light")
                create_mgeo_tl.triggered.connect(lambda:self.add_new_mgeo_item(MGeoItem.TRAFFIC_LIGHT))
                contextMenu.addMenu(create_mgeo_menu)

                append_mgeo_menu = QMenu("Append MGeo", self)
                append_mgeo_tl = append_mgeo_menu.addAction("Append PsLight")
                append_mgeo_tl.triggered.connect(lambda : self.append_mgeo_item(MGeoItem.SYNCED_TRAFFIC_LIGHT))
                contextMenu.addMenu(append_mgeo_menu)

            else:
                # Scenario Runner Editor 부분
                # OpenScenario 차량 및 Object 배치
                if self.osc_client_triggered == True:
                    return
                
                # View Intersection Controller Phase & its duration
                if self.sp['type'] == MGeoItem.INTERSECTION_CONTROLLER:
                    view_intTL_state_widget = contextMenu.addAction("View Intersection Phase")
                    view_intTL_state_widget.triggered.connect(self.view_intTL_state)

                # Vehicle Placement(Init Position) & Setting its route
                if self.inner_link_point_ptr['link'] is not None:
                    if self.check_item == ScenarioItem.Private:
                        contextMenu.addSeparator()
                        set_start_location = contextMenu.addAction("Set Start Location")
                        set_start_location.triggered.connect(self.set_vehicle_start_location)
                        add_waypoint = contextMenu.addAction("Add Waypoint")
                        add_waypoint.triggered.connect(self.add_waypoint)
                        delete_way_point = contextMenu.addAction("Delete Waypoint")
                        delete_way_point.triggered.connect(self.delete_waypoint)
                    
                    add_scenario_object_menu = QMenu("Add Scenario Objects", self)
                    add_vehicle = add_scenario_object_menu.addAction("Vehicle")
                    add_vehicle.triggered.connect(self.add_vehicle)
                    add_pedestrian = add_scenario_object_menu.addAction("Pedestrian")
                    add_pedestrian.triggered.connect(self.add_pedestrian)
                    add_misc_object = add_scenario_object_menu.addAction("MiscObject")
                    add_misc_object.triggered.connect(self.add_misc_object)
                    contextMenu.addMenu(add_scenario_object_menu)
                elif self.check_item == ScenarioItem.Private:
                    contextMenu.addSeparator()
                    delete_way_point = contextMenu.addAction("Delete Waypoint")
                    delete_way_point.triggered.connect(self.delete_waypoint)
        
        action = contextMenu.exec_(self.mapToGlobal(event.pos()))

    def setting_intTL_state(self):
        settingTL = SettingIntersectionSchedule(self.mgeo_maps_dict[self.mgeo_key], self.sp).showDialog()

        if settingTL > 0:
            Logger.log_info('IntTL state changed - ID: {}'.format(self.sp['id']))
        else:
            Logger.log_info('setting_intTL_state canceled by user.')

    def view_intTL_state(self):
        view_tl = ViewIntersectionSchedule(self.mgeo_maps_dict[self.mgeo_key], self.sp).showDialog()

        if view_tl > 0:
            Logger.log_info('View Intersection Controller Region.')
        else:
            Logger.log_info('view_inTL_state canceled by user.')

    def recreate_ref_line(self):
        road = self.getRoadSet()[self.sp['id']]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
        try:
            road.link_list_not_organized.remove(road.ref_line[0])
            road.find_reference_line()
            road.changed = True
            Logger.log_info('>> Ref line changed - ID: {}'.format(Link.get_id_list_string(road.ref_line)))
        
        except BaseException as e:
            Logger.log_error('Failed to find reference line for road: {}'.format(Link.get_id_list_string(road.ref_line)))
        

    # 1. Link에 오른쪽/왼쪽 차선 변경 가능 link 입력하기
    def add_create_lane_change(self):
        # 중앙선부터 차례대로 다중 선택해서 마우스 우클릭 이벤트를 이용한다.
        # 1 2 3
        # 1 > right : 2
        # 2 > left : 1, right : 3
        # 3 > left : 3
        road_idx = self.road_id_idx.get_new()
        while next((link for link in self.getLinkSet(self.mgeo_key).lines.values() if link.road_id == road_idx), False):
            road_idx = self.road_id_idx.get_new()

        cmd_add_create_lane_change = AddCreateLaneChange(self, self.list_sp)
        self.command_manager.execute(cmd_add_create_lane_change)
                
    # 2. Link에 related_signal 값 입력
    def add_related_signal_act(self):

        # [참고] MORAI 정밀지도 요구 사항
        items = ('straight', 'left', 'left_unprotected', 'right', 'right_unprotected', 'upperleft', 'upperright', 'lowerleft', 'lowerright', 'uturn', 'uturn_normal', 'uturn_misc')

        value, okPressed = QInputDialog.getItem(self, "Get item","RelatedSignal:", items, 0, False)
        if okPressed:
            cmd_add_related_signal = AddRelatedSignal(self, self.list_sp, value)
            self.command_manager.execute(cmd_add_related_signal)
            
    # 3. 신호등/표지판에 연관된 link id list 입력하기(단축키 W)
    def action_input_signal_link_id_list(self):
        cmd_input_signal_link_id_list = InputSignalLinkIdList(self, self.list_sp)
        self.command_manager.execute(cmd_input_signal_link_id_list)

    # 4. node에 on stop node 입력
    def set_stop_node(self, value):
        cmd_set_stop_node = SetStopNode(self, self.list_sp, value)
        self.command_manager.execute(cmd_set_stop_node)
        
    # 5. 신호등 타입 변경
    def action_edit_traffic_light(self):
        signals = self.getTLSet(self.mgeo_key).signals
        signal = signals[self.sp['id']]
        edit_widget = EditTLType(parent=self, signal=signal)
        edit_widget.showDialog()

        if edit_widget.result() > 0:
            new_type = edit_widget.tl_type
            new_sub_type = edit_widget.tl_sub_type
            new_orien = edit_widget.tl_ori

            cmd_edit_traffic_light = EditTrafficLight(self, self.list_sp, new_type, new_sub_type, new_orien)
            self.command_manager.execute(cmd_edit_traffic_light)

    # 6. Road ID 입력
    def action_input_road_id(self):
        # if len(self.list_sp) < 2:
        #     return
        road_idx = self.road_id_idx.get_new()
        while next((link for link in self.getLinkSet(self.mgeo_key).lines.values() if link.road_id == road_idx), False):
            road_idx = self.road_id_idx.get_new()
        node_set = self.getNodeSet(self.mgeo_key).nodes
        link_set = self.getLinkSet(self.mgeo_key).lines
        for i, sp in enumerate(self.list_sp):
            if sp['type'] == MGeoItem.LINK:
                current_link = link_set[self.list_sp[i]['id']]
                edit_link.update_link(link_set, node_set, current_link, 'road_id', '', road_idx)
                Logger.log_info('[Edit item properties] road_id : {}'.format(road_idx))

    # 7. Crosswalk 생성
    def action_create_crosswalk(self):
        try :
            cmd_create_crosswalk = CreateCrossWalk(self, self.list_sp)
            self.command_manager.execute(cmd_create_crosswalk)
        except BaseException as e:
            Logger.log_error('Create Crosswalk failed (traceback below) \n{}'.format(traceback.format_exc()))
    
    def action_delete_crosswalk(self):
        if self.list_sp[0]['type'] == MGeoItem.CROSSWALK:
            cw_id = self.list_sp[0]['id']
            cw_set = self.getCrosswalkSet()
            cw_set.remove_data(cw_set.data[cw_id])
        
        self.updateMapData()
        self.updateMgeoIdWidget()
        self.list_sp.clear()

    
    def find_concave_polygon(self):
        # ㄱ, ㄴ, ㅁ 같이 모양이 다른 횡단보도 찾기
        scws = self.getSingleCrosswalkSet().data
        for scw in scws:
            item = scws[scw]
            # 일단 자전거용 횡단보도에 대해서만
            if item.sign_type == '6':
                compare_points = minimum_bounding_rectangle(item.points)
                dist1 = np.sqrt(sum(((compare_points[0][0:2]-compare_points[1][0:2])**2)))
                dist2 = np.sqrt(sum(((compare_points[0][0:2]-compare_points[-1][0:2])**2)))
                # ㄱ, ㄴ, ㅁ 같이 모양이 다른 것만 자르기 위함
                if dist1 < 10 or dist2 < 10:
                    pass
                else:
                    sp_dict = {'type': MGeoItem.SINGLECROSSWALK, 'id':item.idx}
                    self.list_error.append(sp_dict)

    def repair_concave_polygon(self):
        cmd_repair_concave_polygon = RepairConcavePolygon(self, self.list_error)
        self.command_manager.execute(cmd_repair_concave_polygon)

    def action_export_v2x(self):
        v2xExporter(self.mgeo_planner_map, self.mgeo_key)
    
    def action_highlight_v2x_lane(self):
        # TODO : highlight 하는거 추가
        self.list_highlight2.clear()
        
        if self.list_sp[0]['type'] == MGeoItem.INTERSECTION_CONTROLLER:
            # 현재 선택된 Link를 받아온다
            idx = self.list_sp[0]['id']
            intersection = self.getIntersectionControllerSet(self.mgeo_key).intersection_controllers[idx]
            intersection_info = get_intersection_item(self.mgeo_planner_map,intersection)
            laneSet = intersection_info['laneSet']
            for lane in laneSet:
                matched_links = lane['nodeList']['matchedLinkList']
                for link_idx in matched_links:
                    sp_dict = {'type': MGeoItem.LINK, 'id': link_idx}
                    # link = self.getLinkSet(self.mgeo_key).lines[link_idx]
                    self.list_highlight2.append(sp_dict)
        
        
    def setXYTranslate(self, dx, dy, zRot):
        """Z축 회전한 후, mouse drag로 이동하기 위해 Z 회전 각도로 구분하여 이동하게 한다""" 
        
        # 마우스 움직임을 데이터 움직임에 반영하려면, 현재 회전된 각도의 반대방향으로 돌려준다
        theta_z = -1 * self.zRot * np.pi / 180.0
        theta_y = -1 * self.yRot * np.pi / 180.0
        theta_x = -1 * self.xRot * np.pi / 180.0

        #print("{}, {}, {}".format(self.zRot, self.yRot, self.xRot))

        rotation = np.array([[np.cos(theta_z) * np.cos(theta_y), np.cos(theta_z)*np.sin(theta_y)*np.sin(theta_x) - np.sin(theta_z)*np.cos(theta_x)],\
                            [np.sin(theta_z) * np.cos(theta_y), np.sin(theta_z)*np.sin(theta_y)*np.sin(theta_x) + np.cos(theta_z)*np.cos(theta_x)],\
                            [-np.sin(theta_y), np.cos(theta_y)*np.sin(theta_x)]])

        mv_rotated = np.dot(rotation, np.array([dx, dy]))
        
        # z축으로의 회전이 고려된, 데이터가 이동해야 하는 방향
        mv_x = mv_rotated[0]
        mv_y = mv_rotated[1]
        mv_z = mv_rotated[2]
        #print('mv_x, mv_y, mv_z = [{:4.2f}, {:4.2f}] -> [{:4.2f}, {:4.2f}, {:4.2f}]]'.format(dx, dy, mv_x, mv_y, mv_z))
        
        self.xTran += 0.5 * mv_x
        self.yTran += 0.5 * mv_y
        self.zTran += 0.5 * mv_z


    def setZoom(self, zoom, delta):
        
        # TODO(hyjo): Zoom Mininum 값 제한 풀기
        # 단, 수정님한테 어떤 문제 있었는지는 확인 필요

        # zoom in이 많이 됐으면,
        # delta = delta * 0.2
        # zoom out이 많이 되어있는 상태면
        # delta = delta * 5.0 
        
        if self.zoom > -40 and self.zoom <= -10:
            delta = delta * 0.9 
        elif self.zoom > -10:
            delta = delta * 0.1
        elif self.zoom >= -100 and self.zoom <= -40:
            delta = delta * 1.2
        elif self.zoom < -100 and self.zoom >= -200:
            delta = delta * 5.0
        elif self.zoom < -200:
            delta = delta * 8.0
        else:
            delta = delta * 0.2
           
        # # 최대 확대 설정
        # if self.control_key_pressed:
        #     if self.zoom < -250 and self.zoom >= -80:
        #         self.zoom = self.zoom * 1.2
        #     elif self.zoom > -80:
        #         self.zoom = self.zoom * 1.2
        # else:
        #     if self.zoom > -40 and self.zoom <= -10:
        #         self.zoom = self.zoom -5
            # elif self.zoom > -10:
            #     self.zoom = -10

        self.zoom = zoom + delta 


    def getZoomLevel(self):
        """최대 줌일 때, zoom_level이 1이고, 줌을 풀면 (넓은 지역을 보면) zoom_level이 늘어나게 한다"""
        zoom_lim = -21
        if self.zoom > zoom_lim :
            return 1
        else : 
            return -1 * (self.zoom - zoom_lim) / 12 + 1


    def setRotWidget(self):
        """회전과 관련된 Widget을 설정한다""" 
        self.slider[0].setValue(self.normalizeAngle(self.xRot))
        self.slider[1].setValue(self.normalizeAngle(self.zRot))
        self.rot_eidt[0].setText(str(math.floor(self.xRot)))
        self.rot_eidt[1].setText(str(math.floor(self.zRot)))


    def setXRotation(self, angle):
        self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle
            self.xRotationChanged.emit(angle)
            self.setRotWidget()
            # self.update()


    def setYRotation(self, angle):
        self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle
            self.yRotationChanged.emit(angle)
            self.setRotWidget()
            # self.update()


    def setZRotation(self, angle):
        self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle
            self.zRotationChanged.emit(angle)
            self.setRotWidget()
            # self.update()


    def normalizeAngle(self, angle):
        """회전 각도를 -180 ~ 180 사이로 정규화"""
        while (angle < -180):
            angle += 360
        while (angle > 180):
            angle -= 360
        return angle
    

    def setCameraSpeed(self, speed):
        self.camera_speed = speed
        self.setCameraSpeedWidget()
    
    def setCameraSpeedWidget(self):
        self.camera_speed_slider.setValue(self.camera_speed)
        self.camera_speed_edit.setText(str(math.floor(self.camera_speed)))
    
    def setCameraMoveWidget(self):
        if np.isnan(self.xTran) == False:
            self.camera_move_east_edit.setText(str(math.floor(-1 * self.xTran)))
        if np.isnan(self.yTran) == False:
            self.camera_move_north_edit.setText(str(math.floor(-1 * self.yTran)))
        self.camera_move_up_edit.setText(str(math.floor(self.zoom))) 

    # 다중 선택 관련 함수
    def selectMgeoItem(self, sp_dict):
        """Ctrl 키와 함께 사용하면 다중 선택 기능을 사용할 수 있도록 한다"""
        # mgeo item이 전혀 없는 구간을 선택하면 초기화
        if sp_dict['id'] is None:
            self.sp = None
            # self.list_sp.clear()
            return
        self.sp = sp_dict
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            if len(self.list_sp) > 0 and self.sp in self.list_sp:
                self.list_sp.remove(self.sp)
            else:
                self.list_sp.append(self.sp)
        else:
            self.list_sp.clear()
            self.list_sp.append(self.sp)

    def set_point_in_line(self, point_idx):
        """
        Link 또는 Line 내의 point_idx 포인트를 가리키도록 한다
        """
        if len(self.list_sp) != 1:
            # Logger.log_error('change_point_in_line works only when a link is selected')
            return
        
        if self.list_sp[0]['type'] == MGeoItem.LINK:
            # 현재 선택된 Link를 받아온다
            idx = self.list_sp[0]['id']
            link = self.getLinkSet(self.mgeo_key).lines[idx]

            if point_idx < -1:
                Logger.log_error('set_point_in_line Failed. point_idx is not valid value.')
                return

            if point_idx == -1:
                # 마지막 index 가리키도록
                self.inner_link_point_ptr['point_idx'] = link.get_last_idx()

            elif point_idx > link.get_last_idx():
                self.inner_link_point_ptr['point_idx'] = link.get_last_idx()
            
            else:
                self.inner_link_point_ptr['point_idx'] = point_idx

            Logger.log_trace('set_point_in_line (ptr @ link: {}, point_idx: {} )'.format(
                self.inner_link_point_ptr['link'].idx,
                self.inner_link_point_ptr['point_idx']))

        elif self.list_sp[0]['type'] == MGeoItem.LANE_BOUNDARY:
            idx = self.list_sp[0]['id']
            lane = self.getLaneBoundarySet().lanes[idx]

            if point_idx < -1:
                Logger.log_error('set_point_in_line Failed. point_idx is not valid value.')
                return

            if point_idx == -1:
                # 마지막 index 가리키도록
                self.inner_link_point_ptr['point_idx'] = lane.get_last_idx()

            elif point_idx > lane.get_last_idx():
                self.inner_link_point_ptr['point_idx'] = lane.get_last_idx()
            
            else:
                self.inner_link_point_ptr['point_idx'] = point_idx

            Logger.log_trace('set_point_in_line (ptr @ link: {}, point_idx: {} )'.format(
                self.inner_link_point_ptr['link'].idx,
                self.inner_link_point_ptr['point_idx']))


    def change_point_in_line(self, move):
        # 현재 선택된 아이템이 line이고, 하나일때만 동작한다
        if len(self.list_sp) != 1:
            # Logger.log_error('change_point_in_line works only when a link is selected')
            return
        
        if self.list_sp[0]['type'] == MGeoItem.LINK:
            items = self.getLinkSet(self.mgeo_key).lines
        elif self.list_sp[0]['type'] == MGeoItem.LANE_BOUNDARY:
            items = self.getLaneBoundarySet().lanes
        else:    
            # Logger.log_error('change_point_in_line works only when a link is select')
            return

        # 현재 선택된 Link를 받아온다
        idx = self.list_sp[0]['id']
        link = items[idx]

        # move with limiter
        temp_ptr = self.inner_link_point_ptr['point_idx']
        temp_ptr += move
        if temp_ptr < 0:
            temp_ptr = 0
        if temp_ptr > link.get_last_idx():
            temp_ptr = link.get_last_idx()
        self.inner_link_point_ptr['point_idx'] = temp_ptr

        Logger.log_trace('change_point_in_line (ptr @ link: {}, point_idx: {} )'.format(
            self.inner_link_point_ptr['link'].idx,
            self.inner_link_point_ptr['point_idx']))


    def reset_inner_link_point_ptr(self):
        self.inner_link_point_ptr = {'link':None, 'point_idx':0}


    def update_inner_link_point_ptr(self):
        # 선택된 item이 없거나, 여러개 선택되어있으면, inner_link_point_ptr를 reset 
        if len(self.list_sp) != 1:
            self.reset_inner_link_point_ptr()
            return
        
        # 선택된 1개의 item이 Link가 아니면,  inner_link_point_ptr를 reset  
        if self.list_sp[0]['type'] == MGeoItem.LINK:
            items = self.getLinkSet(self.mgeo_key).lines
        elif self.list_sp[0]['type'] == MGeoItem.LANE_BOUNDARY:
            items = self.getLaneBoundarySet().lanes
        else:
            self.reset_inner_link_point_ptr()
            return

        # 이제 이번에 선택된 대상이 기존 대상과 같은지 확인한다
        # 기존의 링크 정보는 여기에 있다
        current_link = self.inner_link_point_ptr['link']

        # 선택되어있는 링크
        link_id = self.list_sp[0]['id']
        new_link = items[link_id]

        # 기존에 선택되어있든 링크와 현재 선택된 링크가 같으면,
        # 업데이트를 하지 않는다
        if new_link is current_link:
            # Logger.log_trace('update_inner_link_point_ptr: previously selected link selected again.') 
            return

        # 새로운 링크가 선택된 것이면, 해당 링크의 첫번째 point를 가리키도록 초기화한다.
        self.inner_link_point_ptr =\
            {'link':new_link, 'point_idx':0} # index
        # Logger.log_trace('update_inner_link_point_ptr: new link selected (new_link id: {})'.format(new_link.idx))


    def set_geochange_point(self, geometry_type):
        Logger.log_trace('Called: set_geochange_point')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return
        
            # 이 위치에 새로운 geometry point를 입력한다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            # 마지막 위치에는 point 넣을 수 없다
            if point_idx == len(link.points) - 1:
                Logger.log_error('set_geochange_point failed (adding geometry point in the last index is not supported.)')
                return    
            
            # geometry 타입을 설정해준다
            link.add_geometry(point_idx, geometry_type)
            self.updateMgeoPropWidget(self.sp)
            self.updateMapData()
            Logger.log_trace('set_geochange_point (link id: {}) (point idx: {}, geometry type: {})'.format(
                point_idx, point_idx, geometry_type))
        
        except BaseException as e:
            Logger.log_error('set_geochange_point failed (traceback below) \n{}'.format(traceback.format_exc()))


    def delete_geochange_point_current(self):
        """geochange point를 삭제한다. 단, point_idx가 0인 경우는 삭제 불가"""
        Logger.log_trace('Called: delete_geochange_point_current')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return

            # 현재 선택되어 있는 링크와 링크 내 point idx를 받아온다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            if point_idx == 0:
                Logger.log_info('Invalid operation: You cannot delete the very first geometry point.')
                return

            geochange_point_to_delete = None
            for geochange_point in link.geometry:
                # 현재 point_idx에 geochange_point를 찾으면,
                if geochange_point['id'] == point_idx:
                    geochange_point_to_delete = geochange_point

            if geochange_point_to_delete is None:
                # 못 찾은 경우이다
                Logger.log_info('Invalid operation: There is no geochange point here')
                return

            link.geometry.remove(geochange_point_to_delete)
            
            self.updateMapData()
            Logger.log_info('geochange point in {} of link (id = {}) deleted'.format(point_idx, link.idx))
        
        except BaseException as e:
            Logger.log_error('delete_geochange_point_current failed (traceback below) \n{}'.format(traceback.format_exc()))


    def delete_geochange_point_all(self):
        """모든 geochange point를 삭제한다. 단, point_idx가 0인 첫 geometry 값은 삭제하지 않는다"""
        Logger.log_trace('Called: delete_geochange_point_all')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return

            # 현재 선택되어 있는 링크
            link = self.inner_link_point_ptr['link']

            # 첫번째 값을 제외한 나머지 값을 삭제
            for i in range(len(link.geometry) - 1):
                link.geometry.pop()

            self.updateMapData()
            Logger.log_info('delete all geochange points of link (id = {})'.format(link.idx))
        
        except BaseException as e:
            Logger.log_error('delete_geochange_point_all failed (traceback below) \n{}'.format(traceback.format_exc()))

    def delete_geometry_points_all_line(self):
        """모든 link에 대한 모든 geochange point를 삭제한다. 단, point_idx가 0인 첫 geometry 값은 삭제하지 않는다."""
        Logger.log_trace('Called: delete_geometry_points_all_line')
        
        result = QMessageBox.question(self, 'MORAI Map Editor', 'Do you want to delete all Geometry Points?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

        if result == QMessageBox.Ok:

            # link인지 lane_marking에 있는지
            # indices = self.getLinkSet(self.mgeo_key).lines.keys()
            # first_idx = list(indices)[0]
            # first_link = self.getLinkSet(self.mgeo_key).lines[first_idx]
            
            lines_list = [self.getLaneBoundarySet().lanes, self.getLinkSet(self.mgeo_key).lines]

            for lines in lines_list:
                for line_id in lines:
                    line = lines[line_id]
                    try:
                        for i in range(len(line.geometry) - 1):
                            line.geometry.pop()
                    except BaseException as e:  
                        Logger.log_error('delete_geochange_point_all failed (traceback below) \n{}'.format(traceback.format_exc()))
            self.updateMapData()
            Logger.log_info('delete all geochange points of all link')
        
        else:
            Logger.log_info('Cancelled delete all geochange points of all link')


    # OpenGL Widget에 Paint하는 함수
    # (glRasterPos3f 사용하는 방식 - drawText 함수 사용시 사용됨)
    def plot_text(self, name, point, color=[0, 0, 0], direction=[0, 0, 0]):
        glColor3f(color[0], color[1], color[2])
        font10 = GLUT_BITMAP_HELVETICA_10
        font12 = GLUT_BITMAP_HELVETICA_12
        font18 = GLUT_BITMAP_HELVETICA_18
        font24 = GLUT_BITMAP_TIMES_ROMAN_24
        font = GLUT_BITMAP_HELVETICA_12
        offset = abs(self.zoom/100)
        if self.zoom >= -20:
            font = font18
        elif self.zoom < -20 and self.zoom >= -80:
            font = font18
        elif self.zoom < -80 and self.zoom > -120:
            font = font12
        point = [float(point[0]), float(point[1]), float(point[2])]
        text_point = np.array(point) + (np.array(direction) * offset)
        glRasterPos3f(text_point[0], text_point[1] + offset, text_point[2])

        for ch in str(name):
           glutBitmapCharacter(font, ctypes.c_int(ord(ch)))


    # 선택/하이라이트된 MGeo 아이템 오버레이
    def plot_point(self, point, color=[0, 0, 0], size=5.0):
        glColor3f(color[0], color[1], color[2])
        glPointSize(size)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBegin(GL_POINTS)
        glVertex3f(point[0], point[1], point[2])
        glEnd()
    
    def plot_points(self, points, color=[0, 0, 0], size=5.0):
        glColor3f(color[0], color[1], color[2])
        glPointSize(size)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBegin(GL_POINTS)
        for i in points:
            glVertex3f(i[0], i[1], i[2])
        glEnd()
        
    def plot_link(self, points, color=[0, 0, 0], width=1.0, type=None):
        glColor3f(color[0], color[1], color[2])
        glLineWidth(width)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        self.paint_line(points, type)

    def plot_road(self, points, color=[0, 0, 0], width=1.0, isRefLine=True):
        if isRefLine:            
            glColor4f(color[0], color[1], color[2], 0.6)
        else:
            glColor4f(color[0], color[1], color[2], 0.2)
        glLineWidth(width)
        self.paint_line(points)
    
    def plot_plane(self, points, color=[0, 0, 0], size=5.0):
        glColor3f(color[0], color[1], color[2])
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBegin(GL_POLYGON)
        for i in points:
            glVertex3f(i[0], i[1], i[2])
        glEnd()
        glLineWidth(3)
        self.paint_line(points)

    def paint_line(self, points, type=None):
        if type == 'Dot':
            glLineStipple(1, 0xaaaa)
        elif type == 'Dash':
            glLineStipple(1, 0x00ff)
        elif type == 'DashDot':
            glLineStipple(2, 0x1C47) 
        else:
            glLineStipple(1, 0xffff)
        glBegin(GL_LINES)
        for i in range(len(points)-1):
            glVertex3f(points[i][0], points[i][1], points[i][2])
            glVertex3f(points[i+1][0], points[i+1][1], points[i+1][2])
        glEnd()

    def plot_point_start_or_end_or_stop(self, point, color=[0, 0, 0], size=5):
        glColor3f(color[0], color[1], color[2])
        glPointSize(size)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBegin(GL_POLYGON)

        # glVertex3f(point[0] - 0.5, point[1] + 0.8, point[2]) # 1
        # glVertex3f(point[0] - 0.5, point[1] - 0.8, point[2]) # 2
        # glVertex3f(point[0] + 0.5, point[1] + 0.8, point[2]) # 3
        # glVertex3f(point[0] + 0.05, point[1] - 0.8, point[2]) # 3

        glVertex3f(point[0] - 0.05, point[1] - 0.8, point[2]) # 1
        glVertex3f(point[0] + 0.8, point[1] - 1.28, point[2]) # 2
        glVertex3f(point[0] + 0.48, point[1] - 0.48, point[2]) # 3
        glVertex3f(point[0] + 1.28, point[1] + 0.16, point[2]) # 4
        glVertex3f(point[0] + 0.32, point[1] + 0.16, point[2]) # 5
        glVertex3f(point[0] + 0.04, point[1] + 1.0, point[2]) # 6
        glVertex3f(point[0] - 0.32, point[1] + 0.16, point[2]) # 7
        glVertex3f(point[0] - 1.28, point[1] + 0.16, point[2]) # 8
        glVertex3f(point[0] - 0.48, point[1] - 0.48, point[2]) # 9
        glVertex3f(point[0] - 0.8, point[1] - 1.28, point[2]) # 10
        glEnd()

    def drawListDelete(self, mgeo_flags=0xFFFFFFFF):
        if mgeo_flags & MGeoItemFlags.NODE.value != 0 :
            if len(self.node_list) != 0:
                for key in self.node_list:
                    glDeleteLists(self.node_list[key], 1)
            if len(self.node_id_list) != 0:
                for key in self.node_id_list:
                    glDeleteLists(self.node_id_list[key], 1)
            self.node_list = dict()
            self.node_id_list = dict()

        if mgeo_flags & MGeoItemFlags.LINK.value != 0 :
            if len(self.link_list) != 0:
                for key in self.link_list:
                    glDeleteLists(self.link_list[key], 1)
                    
            if len(self.link_geo_list) != 0:
                for key in self.link_geo_list:
                    glDeleteLists(self.link_geo_list[key], 1)
                    
            if len(self.link_id_list) != 0:
                for key in self.link_id_list:
                    glDeleteLists(self.link_id_list[key], 1)
            self.link_list = dict()
            self.link_geo_list = dict()
            self.link_id_list = dict()

        if mgeo_flags & MGeoItemFlags.LANE_NODE.value != 0 :
            if len(self.lane_node_list) != 0:
                for key in self.lane_node_list:
                    glDeleteLists(self.lane_node_list[key], 1)
            if len(self.lane_node_id_list) != 0:
                for key in self.lane_node_id_list:
                    glDeleteLists(self.lane_node_id_list[key], 1)
            self.lane_node_list = dict()
            self.lane_node_id_list = dict()

        if mgeo_flags & MGeoItemFlags.LANE_BOUNDARY.value != 0 :
            if len(self.lane_marking_list) != 0:
                for key in self.lane_marking_list:
                    glDeleteLists(self.lane_marking_list[key], 1)
            if len(self.lane_marking_geo_list) != 0:
                for key in self.lane_marking_geo_list:
                    glDeleteLists(self.lane_marking_geo_list[key], 1)
            if len(self.lane_marking_id_list) != 0:
                for key in self.lane_marking_id_list:
                    glDeleteLists(self.lane_marking_id_list[key], 1)
            self.lane_marking_list = dict()
            self.lane_marking_geo_list = dict()
            self.lane_marking_id_list = dict()

        if mgeo_flags & MGeoItemFlags.TRAFFIC_LIGHT.value != 0 :
            if len(self.tl_list) != 0:
                for key in self.tl_list:
                    glDeleteLists(self.tl_list[key], 1)
            if len(self.tl_id_list) != 0:
                for key in self.tl_id_list: 
                    glDeleteLists(self.tl_id_list[key], 1)
            self.tl_list = dict()
            self.tl_id_list = dict()

        if mgeo_flags & MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value != 0 :
            if len(self.synced_tl_list) != 0:
                for key in self.synced_tl_list:
                    glDeleteLists(self.synced_tl_list[key], 1)                    
            if len(self.synced_tl_id_list) != 0:
                for key in self.synced_tl_id_list:
                    glDeleteLists(self.synced_tl_id_list[key], 1)
            self.synced_tl_list = dict()
            self.synced_tl_id_list = dict()

        if mgeo_flags & MGeoItemFlags.INTERSECTION_CONTROLLER.value != 0 :
            if len(self.ic_list) != 0:
                for key in self.ic_list:
                    glDeleteLists(self.ic_list[key], 1)                    
            if len(self.ic_id_list) != 0:
                for key in self.ic_id_list:
                    glDeleteLists(self.ic_id_list[key], 1)
            self.ic_list = dict()
            self.ic_id_list = dict()

        if mgeo_flags & MGeoItemFlags.TRAFFIC_SIGN.value != 0 :
            if len(self.ts_list) != 0:
                for key in self.ts_list:
                    glDeleteLists(self.ts_list[key], 1)
            if len(self.ts_id_list) != 0:
                for key in self.ts_id_list:
                    glDeleteLists(self.ts_id_list[key], 1)
            self.ts_list = dict()
            self.ts_id_list = dict()

        if mgeo_flags & MGeoItemFlags.JUNCTION.value != 0 :
            if len(self.junction_list) != 0:
                for key in self.junction_list:
                    glDeleteLists(self.junction_list[key], 1)
            if len(self.junction_id_list) != 0:
                for key in self.junction_id_list:
                    glDeleteLists(self.junction_id_list[key], 1)
            self.junction_list = dict()
            self.junction_id_list = dict()

        if mgeo_flags & MGeoItemFlags.ROAD.value != 0 :
            if len(self.road_list) != 0:
                for key in self.road_list:
                    glDeleteLists(self.road_list[key], 1)
            if len(self.road_id_list) != 0:
                for key in self.road_id_list:
                    glDeleteLists(self.road_id_list[key], 1)
            self.road_list = dict()
            self.road_id_list = dict()

        if mgeo_flags & MGeoItemFlags.CROSSWALK.value != 0 :
            if len(self.crosswalk_list) != 0:
                for key in self.crosswalk_list:
                    glDeleteLists(self.crosswalk_list[key], 1)
            self.crosswalk_list = dict()

        if mgeo_flags & MGeoItemFlags.SINGLECROSSWALK.value != 0 :
            if len(self.single_crosswalk_list) != 0:
                for key in self.single_crosswalk_list:
                    glDeleteLists(self.single_crosswalk_list[key], 1)
            self.single_crosswalk_list = dict()

        if mgeo_flags & MGeoItemFlags.ROADPOLYGON.value != 0 :
            if len(self.road_polygon_list) != 0:
                for key in self.road_polygon_list:
                    glDeleteLists(self.road_polygon_list[key], 1)
            self.road_polygon_list = dict()
        # 주차
        if mgeo_flags & MGeoItemFlags.PARKING_SPACE.value != 0 :
            if len(self.parking_space_list) != 0:
                for key in self.parking_space_list:
                    glDeleteLists(self.parking_space_list[key], 1)
            if len(self.parking_space_id_list) != 0:
                for key in self.parking_space_id_list:
                    glDeleteLists(self.parking_space_id_list[key], 1)

            self.parking_space_list = dict()
            self.parking_space_id_list = dict()

        if mgeo_flags & MGeoItemFlags.SURFACE_MARKING.value != 0 :
            if len(self.sm_list) != 0:
                for key in self.sm_list:
                    glDeleteLists(self.sm_list[key], 1)
            if len(self.sm_id_list) != 0:
                for key in self.sm_id_list:
                    glDeleteLists(self.sm_id_list[key], 1)
            self.sm_list = dict()
            self.sm_id_list = dict()


    # 데이터 로드 함수
    def loadNode(self):
        for key in self.mgeo_maps_dict:
            nodes = self.getNodeSet(key).nodes
            if len(nodes) < 1: 
                continue
            size = self.config['STYLE']['NODE']['NORMAL']['SIZE']
            color = self.config['STYLE']['NODE']['NORMAL']['COLOR']
            self.node_list[key] = loadPointList(nodes, color, size)
            self.node_id_list[key] = point_id_list(nodes, color)

    def loadLink(self):
        for key in self.mgeo_maps_dict:
            lines = self.getLinkSet(key).lines
            if len(lines) < 1: 
                continue
            color = self.config['STYLE']['LINK']['NORMAL']['COLOR']
            width = self.config['STYLE']['LINK']['NORMAL']['WIDTH']

            poly3_color = self.config['STYLE']['LINK']['GEO STYLE']['POLY3 COLOR']
            poly3_type = self.config['STYLE']['LINK']['GEO STYLE']['POLY3 STYLE']

            line_color = self.config['STYLE']['LINK']['GEO STYLE']['LINE COLOR']
            line_type = self.config['STYLE']['LINK']['GEO STYLE']['LINE STYLE']

            pp3_color = self.config['STYLE']['LINK']['GEO STYLE']['PARAMPOLY3 COLOR']
            pp3_type = self.config['STYLE']['LINK']['GEO STYLE']['PARAMPOLY3 STYLE']

            style = {'color' : color, 
                    'width' : width,
                    'poly3_color' : poly3_color, 
                    'poly3_type' : poly3_type,
                    'line_color' : line_color, 
                    'line_type' : line_type,
                    'pp3_color' : pp3_color, 
                    'pp3_type' : pp3_type}

            
            lane_change = self.config['STYLE']['LINK']['LANE CHANGE LINK']
            
            self.link_list[key] = basicLineList(lines, color, width, lane_change=lane_change)
            self.link_geo_list[key] = geostyleLineList(lines, style, lane_change=lane_change)
            self.link_id_list[key] = line_id_list(lines, color, MGeoItem.LINK)


    def loadTL(self):
        for key in self.mgeo_maps_dict:
            tl_set = self.getTLSet(key).signals
            if len(tl_set) < 1: 
                continue
            color = self.config['STYLE']['TRAFFIC_LIGHT']['NORMAL']['COLOR']
            pedestrian_light = self.config['STYLE']['PEDESTRIAN_LIGHT']['NORMAL']['COLOR']
            size = self.config['STYLE']['TRAFFIC_LIGHT']['NORMAL']['SIZE']
            self.tl_list[key] = loadTLList(tl_set, color, pedestrian_light, size)
            self.tl_id_list[key] = point_id_list(tl_set, color)

    def loadSyncedTL(self):
        for key in self.mgeo_maps_dict:
            if self.getSyncedTLSet(key) is None:
                continue
            synced_tl_set = self.getSyncedTLSet(key).synced_signals
            if len(synced_tl_set) < 1: 
                continue
            color = self.config['STYLE']['SYNCED_TRAFFIC_LIGHT']['NORMAL']['COLOR']
            size = self.config['STYLE']['SYNCED_TRAFFIC_LIGHT']['NORMAL']['SIZE']
            self.synced_tl_list[key] = loadSyncedTLList(synced_tl_set, color, size)
            self.synced_tl_id_list[key] = points_id_list(synced_tl_set, color, MGeoItem.SYNCED_TRAFFIC_LIGHT)

    def loadIC(self):
        for key in self.mgeo_maps_dict:
            if self.getIntersectionControllerSet(key) is None:
                continue
            ic_set = self.getIntersectionControllerSet(key).intersection_controllers
            if len(ic_set) < 1: 
                continue
            color = self.config['STYLE']['INTERSECTION_CONTROLLER']['NORMAL']['COLOR']
            size = self.config['STYLE']['INTERSECTION_CONTROLLER']['NORMAL']['SIZE']
            self.ic_list[key] = loadICList(ic_set, color, size)
            self.ic_id_list[key] = points_id_list(ic_set, color, MGeoItem.INTERSECTION_CONTROLLER)

    def loadTS(self):
        for key in self.mgeo_maps_dict:
            ts_set = self.getTSSet(key).signals
            if len(ts_set) < 1: 
                continue
            color = self.config['STYLE']['TRAFFIC_SIGN']['NORMAL']['COLOR']
            size = self.config['STYLE']['TRAFFIC_SIGN']['NORMAL']['SIZE']
            self.ts_list[key] = loadPointList(ts_set, color, size)
            self.ts_id_list[key] = point_id_list(ts_set, color)

    def loadJunction(self):
        for key in self.mgeo_maps_dict:
            junction_set = self.getJunctionSet(key).junctions
            if len(junction_set) < 1:
                continue
            width = self.config['STYLE']['JUNCTION']['NORMAL']['WIDTH']
            color = self.config['STYLE']['JUNCTION']['NORMAL']['COLOR']
            self.junction_list[key] = loadJunctionList(junction_set, color, width)
            self.junction_id_list[key] = points_id_list( junction_set, color, MGeoItem.JUNCTION)

    def loadRoad(self):
        for key in self.mgeo_maps_dict:
            roads = self.odr_data.roads
            if len(roads) < 1: 
                return
            width = self.config['STYLE']['ROAD']['NORMAL']['WIDTH']
            color = self.config['STYLE']['ROAD']['NORMAL']['COLOR']
            self.road_list[key] = basicRoadList(roads, color, width)
            self.road_id_list[key] = line_id_list(roads, color, MGeoItem.ROAD)

    def loadRoadPolygon(self):
        for key in self.mgeo_maps_dict:
            road_poly = self.getRoadPolygonSet(key).data
            if len(road_poly) < 1:
                continue
            color = self.config['STYLE']['ROADPOLYGON']['NORMAL']['COLOR']
            self.road_polygon_list[key] = load_triangle_polygon(road_poly, color)
        
    def loadSingleCrosswalk(self):
        for key in self.mgeo_maps_dict:
            cws = self.getSingleCrosswalkSet(key).data
            if len(cws) < 1:
                continue
            width = self.config['STYLE']['SINGLECROSSWALK']['NORMAL']['WIDTH']
            color = self.config['STYLE']['SINGLECROSSWALK']['NORMAL']['COLOR']
            self.single_crosswalk_list[key] = load_polygon_list(cws, color)
            #self.road_id_list = line_id_list(roads, color, MGeoItem.ROAD)
    
    def loadCrosswalk(self):
        for key in self.mgeo_maps_dict:
            cw_set = self.getCrosswalkSet(key).data

            if len(cw_set) < 1:
                continue
            width = self.config['STYLE']['CROSSWALK']['NORMAL']['WIDTH']
            color = self.config['STYLE']['CROSSWALK']['NORMAL']['COLOR']
            
            self.crosswalk_list[key] = load_crosswalk_List(cw_set, color)
    
    # [210510]차선데이터/이름보이는것 추가
    def loadLaneNode(self):
        for key in self.mgeo_maps_dict:
            nodes = self.getLaneNodeSet(key).nodes
            if len(nodes) < 1: 
                continue
            size = self.config['STYLE']['LANE_NODE']['NORMAL']['SIZE']
            color = self.config['STYLE']['LANE_NODE']['NORMAL']['COLOR']
            self.lane_node_list[key] = loadPointList(nodes, color, size)
            self.lane_node_id_list[key] = point_id_list(nodes, color)

    def loadLaneMarking(self):
        for key in self.mgeo_maps_dict:
            laneMarking = self.getLaneBoundarySet(key).lanes
            if len(laneMarking) < 1: 
                continue
            color = self.config['STYLE']['LANE_BOUNDARY']['NORMAL']['COLOR']
            width = self.config['STYLE']['LANE_BOUNDARY']['NORMAL']['WIDTH']

            poly3_color = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE']['POLY3 COLOR']
            poly3_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE']['POLY3 STYLE']

            line_color = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE']['LINE COLOR']
            line_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE']['LINE STYLE']

            pp3_color = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE']['PARAMPOLY3 COLOR']
            pp3_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE']['PARAMPOLY3 STYLE']

            style = {'color' : color, 
                    'width' : width,
                    'poly3_color' : poly3_color, 
                    'poly3_type' : poly3_type,
                    'line_color' : line_color, 
                    'line_type' : line_type,
                    'pp3_color' : pp3_color, 
                    'pp3_type' : pp3_type}

            
            self.lane_marking_list[key] = basicLineList(laneMarking, color, width)
            self.lane_marking_geo_list[key] = geostyleLineList(laneMarking, style)
            self.lane_marking_id_list[key]= line_id_list(laneMarking, color, MGeoItem.LANE_BOUNDARY)
        
    def loadParkingSpace(self):
        for key in self.mgeo_maps_dict:
            ps = self.getParkingSpaceSet(key).data
            if len(ps) < 1:
                continue
            width = self.config['STYLE']['PARKING_SPACE']['NORMAL']['WIDTH']
            color = self.config['STYLE']['PARKING_SPACE']['NORMAL']['COLOR']
            self.parking_space_list[key] = load_polygon_list(ps, color)
            # self.parking_space_id_list = line_id_list(ps, color, MGeoItem.PARKING_SPACE)

    def loadSurfaceMarking(self):
        for key in self.mgeo_maps_dict:
            sms = self.getSurfaceMarkingSet(key).data
            if len(sms) < 1:
                continue
            width = self.config['STYLE']['SURFACE_MARKING']['NORMAL']['WIDTH']
            color = self.config['STYLE']['SURFACE_MARKING']['NORMAL']['COLOR']
            # self.sm_list[key] = load_polygon_list(sms, color)
            # self.sm_id_list = line_id_list(sms, color, MGeoItem.SURFACE_MARKING)
    
    def drawMGeoID(self):
        """
        Opengl에 MGeo 아이디 표시하기
        """
        
        # Node 아이디 표시
        if self.config['STYLE']['NODE']['TEXT']:
            if len(self.node_id_list) != 0:
                glPushMatrix()
                for key in self.node_id_list:
                    glCallLists(self.node_id_list[key])
                glPopMatrix()

        # Link 아이디 표시
        if self.config['STYLE']['LINK']['TEXT']:
            if len(self.link_id_list) != 0:
                glPushMatrix()
                for key in self.link_id_list:
                    glCallLists(self.link_id_list[key])
                glPopMatrix()

        # TL 아이디 표시
        if self.config['STYLE']['TRAFFIC_LIGHT']['TEXT']:
            if len(self.tl_id_list) != 0:
                glPushMatrix()
                for key in self.tl_id_list:
                    glCallLists(self.tl_id_list[key])
                glPopMatrix()

        # SYNCED_TRAFFIC_LIGHT 아이디 표시
        if self.config['STYLE']['SYNCED_TRAFFIC_LIGHT']['TEXT']:
            if len(self.synced_tl_id_list) != 0:
                glPushMatrix()
                for key in self.synced_tl_id_list:
                    glCallLists(self.synced_tl_id_list[key])
                glPopMatrix()

        # INTERSECTION_CONTROLLER 아이디 표시
        if self.config['STYLE']['INTERSECTION_CONTROLLER']['TEXT']:
            if len(self.ic_id_list) != 0:
                glPushMatrix()
                for key in self.ic_id_list:
                    glCallLists(self.ic_id_list[key])
                glPopMatrix()

        # TS 아이디 표시
        if self.config['STYLE']['TRAFFIC_SIGN']['TEXT']:
            if len(self.ts_id_list) != 0:
                glPushMatrix()
                for key in self.ts_id_list:
                    glCallLists(self.ts_id_list[key])
                glPopMatrix()

        # Junction 아이디 표시
        if self.config['STYLE']['JUNCTION']['TEXT']:
            if len(self.junction_id_list) != 0:
                glPushMatrix()
                for key in self.junction_id_list:
                    glCallLists(self.junction_id_list[key])
                glPopMatrix()

        # Road 아이디 표시
        if self.config['STYLE']['ROAD']['TEXT']:
            if len(self.road_id_list) != 0:
                glPushMatrix()
                for key in self.road_id_list:
                    glCallLists(self.road_id_list[key])
                glPopMatrix()

        # if self.config['STYLE']['CROSSWALK']['TEXT']:
        #     if len(self.crosswalk_id_list) != 0:
        #         glPushMatrix()
        #         for key in self.crosswalk_id_list:
        #             glCallLists(self.crosswalk_id_list[key])
        #         glPopMatrix()

        # Lane_marking 아이디 표시
        if self.config['STYLE']['LANE_NODE']['TEXT']:
            if len(self.lane_node_id_list) != 0:
                glPushMatrix()
                for key in self.lane_node_id_list:
                    glCallLists(self.lane_node_id_list[key])
                glPopMatrix()

        if self.config['STYLE']['LANE_BOUNDARY']['TEXT']:
            if len(self.lane_marking_id_list) != 0:
                glPushMatrix()
                for key in self.lane_marking_id_list:
                    glCallLists(self.lane_marking_id_list[key])
                glPopMatrix()


    def drawMScenario(self):  
        """
        Opengl에 MScenario 표시하기
        """     
        if self.config['STYLE']['MScenario']['EGO_VEHICLE']['VIEW'] and self.mscenario.ego_vehicle:
            color = self.config['STYLE']['MScenario']['EGO_VEHICLE']['NORMAL']['COLOR']
            width = self.config['STYLE']['MScenario']['EGO_VEHICLE']['NORMAL']['WIDTH']
            size = self.config['STYLE']['MScenario']['EGO_VEHICLE']['NORMAL']['SIZE']
            self.drawVehicle([self.mscenario.ego_vehicle], color, width, size, 'EGO')

        if self.config['STYLE']['MScenario']['SURROUNDING_VEHICLE']['VIEW'] and len(self.mscenario.vehicle_list) > 0:
            color = self.config['STYLE']['MScenario']['SURROUNDING_VEHICLE']['NORMAL']['COLOR']
            width = self.config['STYLE']['MScenario']['SURROUNDING_VEHICLE']['NORMAL']['WIDTH']
            size = self.config['STYLE']['MScenario']['SURROUNDING_VEHICLE']['NORMAL']['SIZE']
            self.drawVehicle(self.mscenario.vehicle_list, color, width, size, 'SURROUNDING')

        if self.config['STYLE']['MScenario']['OBSTACLE']['VIEW'] and len(self.mscenario.obstacle_list) > 0:
            color = self.config['STYLE']['MScenario']['OBSTACLE']['NORMAL']['COLOR']
            width = self.config['STYLE']['MScenario']['OBSTACLE']['NORMAL']['WIDTH']
            size = self.config['STYLE']['MScenario']['OBSTACLE']['NORMAL']['SIZE']
            self.drawObstacle(self.mscenario.obstacle_list, color, width, size)

        if self.config['STYLE']['MScenario']['PEDESTRIAN']['VIEW'] and len(self.mscenario.pedestrian_list) > 0:
            color = self.config['STYLE']['MScenario']['PEDESTRIAN']['NORMAL']['COLOR']
            width = self.config['STYLE']['MScenario']['PEDESTRIAN']['NORMAL']['WIDTH']
            size = self.config['STYLE']['MScenario']['PEDESTRIAN']['NORMAL']['SIZE']
            self.drawPedestrian(self.mscenario.pedestrian_list, color, width, size)      
    
    def drawMGeo(self):
        """
        Opengl에 MGeo 표시하기
        """
        if self.config['STYLE']['NODE']['VIEW']:
            glPushMatrix()
            for key in self.node_list:
                glCallLists(self.node_list[key])
            glPopMatrix()

        if self.config['STYLE']['LINK']['VIEW']:
            glPushMatrix()
            if self.config['STYLE']['LINK']['GEO CHANGE'] == True:
                for key in self.link_geo_list:
                    glCallLists(self.link_geo_list[key])
            elif self.config['STYLE']['LINK']['GEO CHANGE'] == False:
                for key in self.link_list:
                    glCallLists(self.link_list[key])
            glPopMatrix()

            self.drawLinkEditPoint()
    
        if self.config['STYLE']['TRAFFIC_LIGHT']['VIEW']:
            glPushMatrix()
            for key in self.tl_list:
                glCallList(self.tl_list[key])
            glPopMatrix()

        if self.config['STYLE']['SYNCED_TRAFFIC_LIGHT']['VIEW']:
            glPushMatrix()
            for key in self.synced_tl_list:
                glCallLists(self.synced_tl_list[key])
            glPopMatrix()
            
        if self.config['STYLE']['INTERSECTION_CONTROLLER']['VIEW']:
            glPushMatrix()
            for key in self.ic_list:
                glCallLists(self.ic_list[key])
            glPopMatrix()
            
        if self.config['STYLE']['TRAFFIC_SIGN']['VIEW']:
            glPushMatrix()
            for key in self.ts_list:
                glCallLists(self.ts_list[key])
            glPopMatrix()
            
        if self.config['STYLE']['JUNCTION']['VIEW']:
            glPushMatrix()
            for key in self.junction_list:
                glCallLists(self.junction_list[key])
            glPopMatrix()

        if self.config['STYLE']['ROAD']['VIEW']:
            glPushMatrix()
            for key in self.road_id_list:     
                glCallLists(self.road_list[key])
            glPopMatrix()

        if self.config['STYLE']['CROSSWALK']['VIEW']:
            glPushMatrix()
            for key in self.crosswalk_list:
                glCallLists(self.crosswalk_list[key])
            glPopMatrix()

        if self.config['STYLE']['SINGLECROSSWALK']['VIEW']:
            glPushMatrix()
            for key in self.single_crosswalk_list:
                glCallLists(self.single_crosswalk_list[key])
            glPopMatrix()
            
        # # 21.05.10, lane_boundary 데이터에 geometry 정보 표시되게하기
        if self.config['STYLE']['LANE_NODE']['VIEW']:
            glPushMatrix()
            for key in self.lane_node_list:
                glCallLists(self.lane_node_list[key])
            glPopMatrix()

        if self.config['STYLE']['LANE_BOUNDARY']['VIEW']:
            glPushMatrix()
            if self.config['STYLE']['LANE_BOUNDARY']['GEO CHANGE'] == True:
                for key in self.lane_marking_geo_list:
                    glCallLists(self.lane_marking_geo_list[key])
            elif self.config['STYLE']['LANE_BOUNDARY']['GEO CHANGE'] == False:
                for key in self.lane_marking_list:
                    glCallLists(self.lane_marking_list[key])
            glPopMatrix()
            
        if self.config['STYLE']['ROADPOLYGON']['VIEW']:
            glPushMatrix()
            for key in self.road_polygon_list:
                glCallLists(self.road_polygon_list[key])
            glPopMatrix()

            
        if self.config['STYLE']['PARKING_SPACE']['VIEW']:
            glPushMatrix()
            for key in self.parking_space_list:
                glCallLists(self.parking_space_list[key])
            glPopMatrix()

        if self.config['STYLE']['SURFACE_MARKING']['VIEW']:
            glPushMatrix()
            for key in self.sm_list:
                glCallLists(self.sm_list[key])
            glPopMatrix()
    
    def drawLinkEditPoint(self):
        # inner_link_point_ptr이 reset 되어 있다면 리턴
        if self.inner_link_point_ptr['link'] is None:
            return
        
        # edit point 위치를 받아온다
        link = self.inner_link_point_ptr['link']
        point_idx = self.inner_link_point_ptr['point_idx']
        if point_idx >= len(link.points):
            point_idx = 0
        point = link.points[point_idx]

        # 아래 함수로 그려준다 (이 데이터는 선택할 대상이 아니므로 name을 주지 않음)
        color = self.config['STYLE']['SELECT']['COLOR']
        size = self.config['STYLE']['SELECT']['SIZE']
        
        glColor3f(color[0], color[1], color[2])
        glPointSize(size)
        glBegin(GL_POINTS)
        glVertex3f(point[0], point[1], point[2])
        glEnd()

    # 선택한 아이템 그리기
    def drawSelectItem(self):
        if len(self.list_sp) > 0 :
            color = self.config['STYLE']['SELECT']['COLOR']
            width = self.config['STYLE']['SELECT']['WIDTH']
            size = self.config['STYLE']['SELECT']['SIZE']
            self.itemHighlight(self.list_sp, color, width, size)

    def drawHL1Item(self):
        if len(self.list_highlight1) > 0 :
            color = self.config['STYLE']['HIGHLIGHT1']['COLOR']
            width = self.config['STYLE']['HIGHLIGHT1']['WIDTH']
            size = self.config['STYLE']['HIGHLIGHT1']['SIZE']
            self.itemHighlight(self.list_highlight1, color, width, size)
                                   
    def drawHL2Item(self):
        if len(self.list_highlight2) > 0 :
            color = self.config['STYLE']['HIGHLIGHT2']['COLOR']
            width = self.config['STYLE']['HIGHLIGHT2']['WIDTH']
            size = self.config['STYLE']['HIGHLIGHT2']['SIZE']
            self.itemHighlight(self.list_highlight2, color, width, size)

    def drawHL3Item(self):
        if len(self.list_highlight3) > 0 :
            color = self.config['STYLE']['HIGHLIGHT3']['COLOR']
            width = self.config['STYLE']['HIGHLIGHT3']['WIDTH']
            size = self.config['STYLE']['HIGHLIGHT3']['SIZE']
            self.itemHighlight(self.list_highlight3, color, width, size)

    def drawErrorItem(self):
        if len(self.list_error) > 0 :
            color = self.config['STYLE']['ERROR']['COLOR']
            width = self.config['STYLE']['ERROR']['WIDTH']
            size = self.config['STYLE']['ERROR']['SIZE']
            self.itemHighlight(self.list_error, color, width, size)
            

    def drawVehicle(self, list, color, width, size, type):
        for sp in list:
            points = []
            if sp.init_position.init_position_mode == 'absolute' :                    
                points.append([sp.init_position.position.x, sp.init_position.position.y, sp.init_position.position.z])
            else :
                points.append([sp.init_position.position.x, sp.init_position.position.y, sp.init_position.position.z])
            
            self.plot_points(points, color, size * 1.2)

            point = [sp.init_position.position.x, sp.init_position.position.y, sp.init_position.position.z]
            if type == 'EGO' and self.config['STYLE']['MScenario']['EGO_VEHICLE']['TEXT']:
                self.plot_text('Ego Vehicle', point, self.config['STYLE']['MScenario']['EGO_VEHICLE']['NORMAL']['COLOR'])
            elif type == 'SURROUNDING' and self.config['STYLE']['MScenario']['SURROUNDING_VEHICLE']['TEXT']:
                self.plot_text('Surrounding Vehicle', point, self.config['STYLE']['MScenario']['SURROUNDING_VEHICLE']['NORMAL']['COLOR'])


    def drawObstacle(self, list, color, width, size):
        for sp in list:
            points = []              
            points.append([sp.init_transform.position.x, sp.init_transform.position.y, sp.init_transform.position.z])
            self.plot_points(points, color, size)

            point = [sp.init_transform.position.x, sp.init_transform.position.y, sp.init_transform.position.z]
            if self.config['STYLE']['MScenario']['OBSTACLE']['TEXT']:
                self.plot_text('Obstacle', point, self.config['STYLE']['MScenario']['OBSTACLE']['NORMAL']['COLOR'])


    def drawPedestrian(self, list, color, width, size):
        for sp in list:
            points = []              
            points.append([sp.init_position.position.x, sp.init_position.position.y, sp.init_position.position.z])
            self.plot_points(points, color, size)

            point = [sp.init_position.position.x, sp.init_position.position.y, sp.init_position.position.z]
            if self.config['STYLE']['MScenario']['PEDESTRIAN']['TEXT']:
                self.plot_text('Pedestrian', point, self.config['STYLE']['MScenario']['PEDESTRIAN']['NORMAL']['COLOR'])


    def drawOpenScenarioObject(self, key, position_dict):
        points = []
        for name, world_position in position_dict.items():
            position = [world_position.x, world_position.y, world_position.z]
            points.append(np.array(position))

            if self.config['STYLE']['OpenSCENARIO'][key]['TEXT']:
                self.plot_text(name, position, self.config['STYLE']['OpenSCENARIO'][key]['NORMAL']['COLOR'])
        
        if points:
            color = self.config['STYLE']['OpenSCENARIO'][key]['NORMAL']['COLOR']
            size = self.config['STYLE']['OpenSCENARIO'][key]['NORMAL']['SIZE']
            self.plot_points(points, color, size * 1.2)
   

    def drawOpenScenarioRoute(self, object, color, width, size, type):
        """
        With all waypoints from Route object, draw the EGO / NPC Vehicle's Route
        
        Helper functions: connect_route, connect_dijkstra_route, check_all_links_connected
        """
        
        for key, points in self.open_scenario.gui_object_route.items():
            if object.name == key:
                self.plot_points(points, color, size)
        
    # Draw Open Scenario Item
    def drawOpenScenario(self):
        """
        OpenGL에 OpenScenario 표시하기
        """
        
        for key in ['EGO_VEHICLE', 'NPC_VEHICLE', 'PEDESTRIAN', 'OBSTACLE', 'SPAWN_POINT']:
            if self.config['STYLE']['OpenSCENARIO'][key]['VIEW']:
                self.drawOpenScenarioObject(key, self.open_scenario.gui_object_position_dict[key])

        for object in self.open_scenario.scenario_object_dict.values():
            # TODO: Try to connect catalogreference to vehicles (look at the code below)
            if isinstance(object.entity_object, CatalogReference):
                if object.name == 'Ego':
                    # Ego Route 정보
                    if self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['VIEW']:
                        color = self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['NORMAL']['COLOR']
                        width = self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['NORMAL']['WIDTH']
                        size = self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['NORMAL']['SIZE']
                        self.drawOpenScenarioRoute(object, color, width, size, 'EGO_ROUTE')
                else:
                    # NPC Route 정보
                    if self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['VIEW']:
                        color = self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['NORMAL']['COLOR']
                        width = self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['NORMAL']['WIDTH']
                        size = self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['NORMAL']['SIZE']
                        self.drawOpenScenarioRoute(object, color, width, size, 'NPC_ROUTE')
            
            elif isinstance(object.entity_object, Vehicle):
                if object.name == 'Ego':
                    # Ego Route 정보
                    if self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['VIEW']:
                        color = self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['NORMAL']['COLOR']
                        width = self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['NORMAL']['WIDTH']
                        size = self.config['STYLE']['OpenSCENARIO']['EGO_ROUTE']['NORMAL']['SIZE']
                        self.drawOpenScenarioRoute(object, color, width, size, 'EGO_ROUTE')
                else:
                    # NPC Route 정보
                    if self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['VIEW']:
                        color = self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['NORMAL']['COLOR']
                        width = self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['NORMAL']['WIDTH']
                        size = self.config['STYLE']['OpenSCENARIO']['NPC_ROUTE']['NORMAL']['SIZE']
                        self.drawOpenScenarioRoute(object, color, width, size, 'NPC_ROUTE')
       
            
    def itemHighlight(self, highlight_list, color, width, size):
        #road_polygon 을 한번에 그리기 위해(draw call 줄이기)
        #TODO : 추후에 다른 item도 한번에 그릴 필요가 있을지 검토
        road_poly_dict = dict()
        for sp in highlight_list:
            if sp['id'] is None:
                return

            if sp['type'] == MGeoItem.NODE:
                if sp['id'] in self.getNodeSet(self.mgeo_key).nodes:
                    item = self.getNodeSet(self.mgeo_key).nodes[sp['id']]
                    point = item.point
                    self.plot_point(point, color, size)

            elif sp['type'] == MGeoItem.LINK:
                # merge 했을 때 하이라이트 했던 link가 사라지면 key값이 없어서 에러가 발생함
                if sp['id'] in self.getLinkSet(self.mgeo_key).lines:
                    link = self.getLinkSet(self.mgeo_key).lines[sp['id']]
                    points = link.points
                
                    if self.config['STYLE']['LINK']['GEO CHANGE']:
                        geo = link.geometry
                        if len(geo) == 1:
                            start_id = 0
                            end_id = len(points)
                            line_type = self.config['STYLE']['LINK']['GEO STYLE'][geo[0]['method'].upper() + ' STYLE']
                            self.plot_link(points[start_id:end_id+1], color, width, line_type)
                        else:
                            for i in range(len(geo)):
                                if i == 0:
                                    start_id = 0
                                    end_id = geo[i+1]['id']
                                    line_type = self.config['STYLE']['LINK']['GEO STYLE'][geo[i]['method'].upper() + ' STYLE']
                                elif i == (len(geo)-1):
                                    start_id = geo[i]['id']
                                    end_id = len(points)
                                    line_type = self.config['STYLE']['LINK']['GEO STYLE'][geo[i]['method'].upper() + ' STYLE']
                                else:
                                    start_id = geo[i]['id']
                                    end_id = geo[i+1]['id']
                                line_type = self.config['STYLE']['LINK']['GEO STYLE'][geo[i]['method'].upper() + ' STYLE']
                                self.plot_link(points[start_id:end_id+1], color, width, line_type)
                        self.plot_points(link.points, color, 5)
                    else:
                        self.plot_link(link.points, color, width)
                        self.plot_points(link.points, color, 5)


            elif sp['type'] == MGeoItem.TRAFFIC_SIGN:
                if sp['id'] in self.getTSSet(self.mgeo_key).signals:
                    self.plot_point(self.getTSSet(self.mgeo_key).signals[sp['id']].point, color, size)

            elif sp['type'] == MGeoItem.TRAFFIC_LIGHT:
                if sp['id'] in self.getTLSet(self.mgeo_key).signals:
                    self.plot_point(self.getTLSet(self.mgeo_key).signals[sp['id']].point, color, size)

            elif sp['type'] == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                if sp['id'] in self.getSyncedTLSet().synced_signals:
                    self.plot_points(self.getSyncedTLSet().synced_signals[sp['id']].get_synced_signal_points(), color, size*1.5)
                    # self.plot_point(self.getSyncedTLSet().synced_signals[sp['id']].point, color, size)

            elif sp['type'] == MGeoItem.INTERSECTION_CONTROLLER:
                if sp['id'] in self.getIntersectionControllerSet(self.mgeo_key).intersection_controllers:
                    self.plot_points(self.getIntersectionControllerSet(self.mgeo_key).intersection_controllers[sp['id']].get_intersection_controller_points(), color, size*1.5)
                    self.plot_point(self.getIntersectionControllerSet(self.mgeo_key).intersection_controllers[sp['id']].point, color, size)

            elif sp['type'] == MGeoItem.JUNCTION:
                if sp['id'] in self.getJunctionSet(self.mgeo_key).junctions:
                    self.plot_points(self.getJunctionSet(self.mgeo_key).junctions[sp['id']].get_jc_node_points(), color, size)

            elif sp['type'] == MGeoItem.ROAD:
                if sp['id'] in self.getRoadSet():
                    road = self.getRoadSet()[sp['id']]
                    for link in road.ref_line:
                        self.plot_road(link.points, color, self.config['STYLE']['ROAD']['NORMAL']['WIDTH']*1.2, True)
                    for link in road.link_list_not_organized:
                        self.plot_road(link.points, color, self.config['STYLE']['ROAD']['NORMAL']['WIDTH']*1.2, False)


            # 차선 변경 수정
            elif sp['type'] == MGeoItem.LANE_NODE:
                if sp['id'] in self.getLaneNodeSet().nodes:
                    item = self.getLaneNodeSet().nodes[sp['id']]
                    point = item.point
                    self.plot_point(point, color, size)


            elif sp['type'] == MGeoItem.LANE_BOUNDARY:
                if sp['id'] in self.getLaneBoundarySet().lanes:
                    item = self.getLaneBoundarySet().lanes[sp['id']]
                    points = item.points
                    if self.config['STYLE']['LANE_BOUNDARY']['GEO CHANGE']:
                        geo = item.geometry
                        if len(geo) == 1:
                            start_id = 0
                            end_id = len(points)
                            line_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE'][geo[0]['method'].upper() + ' STYLE']
                            self.plot_link(points[start_id:end_id+1], color, width, line_type)
                        else:
                            for i in range(len(geo)):
                                if i == 0:
                                    start_id = 0
                                    end_id = geo[i+1]['id']
                                    line_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE'][geo[i]['method'].upper() + ' STYLE']
                                elif i == (len(geo)-1):
                                    start_id = geo[i]['id']
                                    end_id = len(points)
                                    line_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE'][geo[i]['method'].upper() + ' STYLE']
                                else:
                                    start_id = geo[i]['id']
                                    end_id = geo[i+1]['id']
                                line_type = self.config['STYLE']['LANE_BOUNDARY']['GEO STYLE'][geo[i]['method'].upper() + ' STYLE']
                                self.plot_link(points[start_id:end_id+1], color, width, line_type)
                        self.plot_points(points, color, 5)
                    else:
                        self.plot_link(points, color, width)
                        self.plot_points(points, color, 5)


            elif sp['type'] == MGeoItem.SINGLECROSSWALK:
                if sp['id'] in self.getSingleCrosswalkSet().data:
                    item = self.getSingleCrosswalkSet().data[sp['id']]
                    points = item.points
                    self.plot_plane(points, color, size)

            elif sp['type'] == MGeoItem.CROSSWALK:
                if sp['id'] in self.getCrosswalkSet().data:
                    item = self.getCrosswalkSet().data[sp['id']]
                    for scw in item.single_crosswalk_list:
                        points = scw.points
                        self.plot_plane(points, color, size)
                    
                    for tl in item.ref_traffic_light_list:
                        point = tl.point
                        self.plot_point(point, color, size)
                        
            elif sp['type'] == MGeoItem.ROADPOLYGON:
                if sp['id'] in self.getRoadPolygonSet().data:
                    item = self.getRoadPolygonSet().data[sp['id']]
                    road_poly_dict[sp['id']] = item
                        
            elif sp['type'] == MGeoItem.PARKING_SPACE:
                if sp['id'] in self.getParkingSpaceSet().data:
                    item = self.getParkingSpaceSet().data[sp['id']]
                    points = item.points
                    self.plot_plane(points, color, size)

            elif sp['type'] == MGeoItem.SURFACE_MARKING:
                if sp['id'] in self.getSurfaceMarkingSet().data:
                    item = self.getSurfaceMarkingSet().data[sp['id']]
                    points = item.points
                    self.plot_plane(points, color, size)


            elif sp['type'] == MScenarioItem.EGO_VEHICLE:
                point_xyz = self.mscenario.ego_vehicle.init_position.position
                point = [point_xyz.x, point_xyz.y, point_xyz.z]
                self.plot_point(point, color, size*1.5)
                # points = []
                # if sp.init_position['absolute']:                    
                #     points.append([sp.init_position['pos']['x'], sp.init_position['pos']['y'], sp.init_position['pos']['z']])
                # elif self.sp.init_position['absolute']:
                #     points.append()
                # self.plot_points(points, color, size*1.5) 

            elif sp['type'] == MScenarioItem.SURROUNDING_VEHICLE:
                vehicle_list = self.mscenario.vehicle_list
                for item in vehicle_list:
                    if str(item.id) == sp['id'] or item.id == sp['id']:
                        point_xyz = item.init_position.position
                        point = [point_xyz.x, point_xyz.y, point_xyz.z]
                        continue
                self.plot_point(point, color, size*1.5)

            elif sp['type'] == MScenarioItem.PEDESTRIAN:
                pedestrian_list = self.mscenario.pedestrian_list
                for item in pedestrian_list:
                    if str(item.id) == sp['id'] or item.id == sp['id']:
                        point_xyz = item.init_position.position
                        point = [point_xyz.x, point_xyz.y, point_xyz.z]
                        continue
                self.plot_point(point, color, size*1.5)
            
            elif sp['type'] == MScenarioItem.OBSTACLE:
                obstacle_list = self.mscenario.obstacle_list
                for item in obstacle_list:
                    if str(item.id) == sp['id'] or item.id == sp['id']:
                        point_xyz = item.init_transform.position
                        point = [point_xyz.x, point_xyz.y, point_xyz.z]
                        continue
                self.plot_point(point, color, size*1.5)

        if len(road_poly_dict) > 0 :
            draw_road_poly = load_triangle_polygon(road_poly_dict, color, False)
            glPushMatrix()
            glCallLists(draw_road_poly)
            glPopMatrix()
                
    def getNodeSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.node_set
        else:
            return self.mgeo_maps_dict[key].node_set

    def getLinkSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.link_set
        else:
            return self.mgeo_maps_dict[key].link_set

    def getLaneBoundarySet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.lane_boundary_set
        else:
            return self.mgeo_maps_dict[key].lane_boundary_set

    def getLaneNodeSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.lane_node_set
        else:
            return self.mgeo_maps_dict[key].lane_node_set

    def getTSSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.sign_set
        else:
            return self.mgeo_maps_dict[key].sign_set

    def getTLSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.light_set
        else:
            return self.mgeo_maps_dict[key].light_set

    def getJunctionSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.junction_set
        else:
            return self.mgeo_maps_dict[key].junction_set

    def getRoadSet(self):
        return self.odr_data.roads

    def getSyncedTLSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.synced_light_set
        else:
            return self.mgeo_maps_dict[key].synced_light_set

    def getIntersectionControllerSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.intersection_controller_set
        else:
            return self.mgeo_maps_dict[key].intersection_controller_set

    def getSurfaceMarkingSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.sm_set
        else:
            return self.mgeo_maps_dict[key].sm_set

    #TODO: CW MGEO TEST
    def getCrosswalkSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.cw_set
        else:
            return self.mgeo_maps_dict[key].cw_set

    def getSingleCrosswalkSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.scw_set
        else:
            return self.mgeo_maps_dict[key].scw_set

    def getRoadPolygonSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.road_polygon_set
        else:
            return self.mgeo_maps_dict[key].road_polygon_set

    def getParkingSpaceSet(self, key=None):
        if key is None:
            return  self.mgeo_planner_map.parking_space_set
        else:
            return self.mgeo_maps_dict[key].parking_space_set
    
    def get_open_scenario(self) -> OpenScenarioImporter:
        return self.open_scenario
    
    def clearDrawData(self):
        """
        Delete Display List
        """
        # 데이터 초기화
        # >> 시나리오 데이터 로드했다가 없는 것 로드하면 시나리오 데이터 남아 있어서, 초기화 시켜줌
        self.clearMGeoData()
        self.mgeo_planner_map = MGeo()
        self.odr_data = OdrData(mgeo_planner_map=None)
        self.mscenario = MScenario()
        self.open_scenario = None


    def setMGeoPlannerMap(self, mgeo_maps_dict):
        # 데이터 claer
        self.clearDrawData()
        self.clearMGeoUI()

        self.mgeo_maps_dict = mgeo_maps_dict
        self.mgeo_key = list(self.mgeo_maps_dict.keys())[0]

        self.mgeo_rtree.clear()
        for key in self.mgeo_maps_dict :
            self.mgeo_rtree[key] = MgeoRTree(self.mgeo_maps_dict[key])
        self.odr_data = OdrData(mgeo_planner_map=None)

    def setMScenario(self, mscenario):
        self.mscenario = mscenario

    def set_open_scenario(self, open_scenario:OpenScenarioImporter):
        self.open_scenario = open_scenario
        
    # Load Display List
    def updateMapData(self, mgeo_flags=0xFFFFFFFF):
        self.drawListDelete(mgeo_flags)
        if mgeo_flags & MGeoItemFlags.NODE.value != 0 :
            self.loadNode()
        if mgeo_flags & MGeoItemFlags.LINK.value != 0 :
            self.loadLink()
        if mgeo_flags & MGeoItemFlags.LANE_NODE.value != 0 :
            self.loadLaneNode()
        if mgeo_flags & MGeoItemFlags.LANE_BOUNDARY.value != 0 :
            self.loadLaneMarking()
        if mgeo_flags & MGeoItemFlags.TRAFFIC_LIGHT.value != 0 :
            self.loadTL()
        if mgeo_flags & MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value != 0 :
            self.loadSyncedTL()
        if mgeo_flags & MGeoItemFlags.INTERSECTION_CONTROLLER.value != 0 :
            self.loadIC()
        if mgeo_flags & MGeoItemFlags.TRAFFIC_SIGN.value != 0 :
            self.loadTS()
        if mgeo_flags & MGeoItemFlags.JUNCTION.value != 0 :
            self.loadJunction()
        if mgeo_flags & MGeoItemFlags.ROAD.value != 0 :
            self.loadRoad()
        if mgeo_flags & MGeoItemFlags.CROSSWALK.value != 0 :
            self.loadCrosswalk()
        if mgeo_flags & MGeoItemFlags.SINGLECROSSWALK.value != 0 :
            self.loadSingleCrosswalk()
        if mgeo_flags & MGeoItemFlags.ROADPOLYGON.value != 0 :
            self.loadRoadPolygon()
        if mgeo_flags & MGeoItemFlags.PARKING_SPACE.value != 0 :
            self.loadParkingSpace()
        if mgeo_flags & MGeoItemFlags.SURFACE_MARKING.value != 0 :
            self.loadSurfaceMarking()

        if self.mgeo_key not in self.mgeo_rtree:
            self.mgeo_rtree[self.mgeo_key] = MgeoRTree(self.mgeo_maps_dict[self.mgeo_key])

    def clearMGeoData(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        self.sp = None
        self.list_sp.clear()
        self.find_item = None
        self.marker_start_node.clear()
        self.marker_end_node.clear()
        self.clearHighlightList()
        # 시나리오 리셋
        self.reset_start_point()
        self.reset_end_point()
        self.reset_stop_point()


    def clearMGeoUI(self):
        self.tree_data.clear()
        self.tree_style.clear()
        self.tree_attr.clear()


    def clearHighlightList(self):
        self.list_highlight1 = []
        self.list_highlight2 = []
        self.list_highlight3 = []
        self.list_error = []


    def setViewMode(self, view_mode):
        if view_mode == 'view_xy':
            self.setXRotation(-45)
            self.setZRotation(90)
        elif view_mode == 'view_yz':
            self.setXRotation(-45)
            self.setZRotation(0)
        elif view_mode == 'view_zx':
            self.setXRotation(-45)
            self.setZRotation(-90)
        elif view_mode == 'south':
            self.setXRotation(-45)
            self.setZRotation(180)
        else:
            self.view_mode = view_mode


    # 신호등/표지판에 heading 값 넣기
    def cal_heading_of_the_traffic_signal(self):
        Logger.log_trace('Called: cal_heading_of_the_traffic_signal')
        tl_set = self.getTLSet().signals
        for _notused, tl in tl_set.items():
            tl.heading = calculate_heading(tl, export_signal=False)
        ts_set = self.getTSSet().signals
        for _notused, ts in ts_set.items():
            ts.heading = calculate_heading(ts, export_signal=False)
        Logger.log_info('cal_heading_of_the_traffic_signal completed successfully.')


    # MGeo 속성 Tree Widget 설정
    def updateMgeoPropWidget(self, item):
        """
        MGeo 속성 Tree Widget의 내용을 현재 선택된 아이템의 속성으로 업데이트한다
        """
        self.display_prop.set_prop(self, self.tree_attr, item, self.getRoadSet())

    def updateMgeoIdWidget(self, mgeo_flags=0xFFFFFFFF):
        """
        Display MGeo/MScenario Item ID List
        """
        self.updateMapData(mgeo_flags)
        self.clearMGeoData()
        self.tree_data.clear()
        
        # 1. 데이터(Mgeo Item) 리스트
        for key in self.mgeo_maps_dict:
            data_set = {
                MGeoItem.NODE: self.getNodeSet(key).nodes,
                MGeoItem.LINK: self.getLinkSet(key).lines,
                MGeoItem.TRAFFIC_LIGHT: self.getTLSet(key).signals,
                MGeoItem.TRAFFIC_SIGN: self.getTSSet(key).signals,
                MGeoItem.JUNCTION: self.getJunctionSet(key).junctions,
                MGeoItem.ROAD: self.getRoadSet(),
                MGeoItem.SYNCED_TRAFFIC_LIGHT: self.getSyncedTLSet(key).synced_signals if self.getSyncedTLSet(key) is not None else None,
                MGeoItem.INTERSECTION_CONTROLLER: self.getIntersectionControllerSet(key).intersection_controllers if self.getIntersectionControllerSet(key) is not None else None,
                MGeoItem.LANE_BOUNDARY: self.getLaneBoundarySet(key).lanes,
                MGeoItem.LANE_NODE: self.getLaneNodeSet(key).nodes,
                MGeoItem.SINGLECROSSWALK: self.getSingleCrosswalkSet(key).data,
                MGeoItem.CROSSWALK: self.getCrosswalkSet(key).data,
                MGeoItem.ROADPOLYGON: self.getRoadPolygonSet(key).data,
                MGeoItem.PARKING_SPACE: self.getParkingSpaceSet(key).data,
                MGeoItem.SURFACE_MARKING: self.getSurfaceMarkingSet(key).data
            }
            mgeoItemList = QTreeWidgetItem(self.tree_data)
            mgeoItemList.setText(0, key)
            for item in MGeoItem:
                if data_set[item] is None:
                    continue
                item_list = QTreeWidgetItem(mgeoItemList)
                item_list.setText(0, item.name)
                for idx in data_set[item]:
                    idx_list = QTreeWidgetItem(item_list)
                    idx_list.setText(0, "{}".format(idx))
            mgeoItemList.setExpanded(True)
        
        # 2. 시나리오 리스트 (MScenario)
        if self.mscenario.ego_vehicle is not None:
            mscenario_data_set = { 
                MScenarioItem.EGO_VEHICLE: [self.mscenario.ego_vehicle],
                MScenarioItem.SURROUNDING_VEHICLE: self.mscenario.vehicle_list,
                MScenarioItem.OBSTACLE: self.mscenario.obstacle_list,
                MScenarioItem.PEDESTRIAN: self.mscenario.pedestrian_list
            }

            mScenarioItemList = QTreeWidgetItem(self.tree_data)
            mScenarioItemList.setText(0, MScenarioItem.__name__)
            for item in MScenarioItem:
                sr_list = QTreeWidgetItem(mScenarioItemList)
                sr_list.setText(0, item.name)
                for data in mscenario_data_set[item]:
                    idx_list = QTreeWidgetItem(sr_list)
                    idx_list.setText(0, "{}".format(data.id))
            mScenarioItemList.setExpanded(True)
        
        # 3. 시나리오 리스트 (OpenScenario)
        if self.open_scenario is not None:
            if self.open_scenario.update_scenario_data() is False:
                Logger.log_warning("OpenSCENARIO file is not valid, cannot draw OpenScenario objects")
            
            ScenarioItem = QTreeWidgetItem(self.tree_data)
            if self.open_scenario.file_path != None:
                root_name = 'OpenSCENARIO - ' + os.path.basename(self.open_scenario.file_path).split('.')[0]
            else:
                root_name = 'OpenSCENARIO - ' + "New Scenario"
            ScenarioItem.setText(0, root_name)
            ScenarioItem.setData(1, Qt.UserRole, self.open_scenario.scenario_definition)
            self.add_openscenario_elements(ScenarioItem, self.open_scenario.scenario_definition)
            ScenarioItem.setExpanded(True)

    def add_openscenario_elements(self, qtree_item, scenario_element):
        if scenario_element is self.clicked_scenario_data:
            parent_item = qtree_item
            while parent_item.parent():
                parent_item.setExpanded(True)
                parent_item = parent_item.parent()
        else:
            qtree_item.setExpanded(False)

        for element in scenario_element.get_child_elements():
            item = QTreeWidgetItem(qtree_item)
            if hasattr(element, 'name') and element.name is not None:
                item.setText(0, type(element).__name__ + ' - ' + element.name)
            else:
                item.setText(0, type(element).__name__)
            item.setData(1, Qt.UserRole, element)
            self.add_openscenario_elements(item, element)

    def updateTreeWidget(self):
        """
        지도 데이터 import 후에 데이터 ID, Style congig 파일에서 값 가져오기
        """
        self.updateMgeoIdWidget()
        self.display_style.set_widget()

        self.tree_data.itemClicked.connect(self.onItemChanged)
        self.tree_data.itemDoubleClicked.connect(self.onIdDoubleClickEvent)
        self.tree_data.customContextMenuRequested.connect(self.onIDRightClickEvent)


    def onItemChanged(self, item, column):
        """
        Select MGeo/MScenario Item
        """
        root_item = item
        mgeo_item = item
        while root_item.parent():
            mgeo_item = root_item
            root_item = root_item.parent()
        mgeo_key = root_item.text(0)
        mgeo_type = mgeo_item.text(0)
        
        try:    # OpenScenario item
            element = item.data(1, Qt.UserRole)
            find_item = { 'key': mgeo_key,
                          'type': ScenarioItem[type(element).__name__],
                          'id': 0, # not used
                          'element': element }
            
            self.check_item = find_item['type']
            self.clicked_scenario_data = find_item['element']
            self.updateMgeoPropWidget(find_item)
            return
        except: 
            pass
        
        if mgeo_key not in self.mgeo_maps_dict:
            return

        self.mgeo_planner_map = self.mgeo_maps_dict[mgeo_key]
        self.check_item = mgeo_type
        self.mgeo_key = mgeo_key


    def setConfig(self, config):
        self.config = config


    def setConfigFilePath(self, file_path):
        self.json_file_path = file_path


    def delete_mgeo(self, key):
        """mgeo_maps_dict 에 있는 선택된 MGeo Map Key 값을 지운다.
        Parameter:
        argument1 (key): MGeo Map Key Value
        Returns: None
        """

        try:
            Logger.log_trace('Called: Target Mgeo Map data : {}'.format(key))
            Logger.log_trace('Called: Delete the Mgeo Mad data : {}'.format(key))

            result = QMessageBox.question(self, 'MORAI Map Editor',
                                        'Delete MGeo : \n{}'.format(key),
                                        QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

            if result == QMessageBox.Ok:
                del self.mgeo_maps_dict[key]
                del self.mgeo_rtree[key]

                if len(self.mgeo_maps_dict) > 0:
                    self.mgeo_key = list(self.mgeo_maps_dict.keys())[0]
                    self.mgeo_planner_map = self.mgeo_maps_dict[self.mgeo_key]
                else:
                    self.mgeo_planner_map = None

                self.updateMgeoIdWidget()

        except BaseException as e:
            Logger.log_error('delete_mgeo failed (traceback below) \n{}'.format(traceback.format_exc()))
    
    # 아이템 삭제하기
    def delete_item(self, items):
        Logger.log_trace('Called: delete_item')
        try:
            if len(items) == 1:
                result = QMessageBox.question(self, 'MORAI Map Editor', 
                                    'Delete item\n{} {}'.format(items[0]['type'].name, items[0]['id']), 
                                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            else:
                result = QMessageBox.question(self, 'MORAI Map Editor', 
                                    'Delete items\n{}'.format(items[0]['type'].name), 
                                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

            if result == QMessageBox.Ok:
                try :
                    delete_cmd = DeleteMgeoItem(self, items)
                    self.command_manager.execute(delete_cmd)
                except BaseException as e:
                    QMessageBox.warning(self, "Warning", e.args[0])
                # mgeo_data update

        except BaseException as e:
            Logger.log_error('delete_item failed (traceback below) \n{}'.format(traceback.format_exc()))

    def add_scenario_element(self, item, param):
        try:
            element:BaseElement = item.data(1, Qt.UserRole)
            element.add_child(param)
            self.clicked_scenario_data = element
            self.updateMgeoIdWidget()
        except ValueError as ve:
            Logger.log_error('Failed to add element: {}'.format(ve))
        except BaseException as be:
            Logger.log_error('add_scenario_elem failed (traceback below) \n{}'.format(traceback.format_exc()))

    def delete_scenario_element(self, item):
        try:
            element = item.data(1, Qt.UserRole)
            Logger.log_trace('Called: Delete the OpenScenario Element: {}'.format(type(element).__name__))
            result = QMessageBox.question(self, 'MORAI Scenario Runner',
                                          'Delete Scenario Element : \n{}'.format(type(element).__name__),
                                        QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if result == QMessageBox.Ok:
                parent_element = item.parent().data(1, Qt.UserRole)
                if parent_element.delete_element(element):
                    self.clicked_scenario_data = parent_element
                else:
                    Logger.log_error("Failed to delete {}".format(type(element).__name__))
                self.updateMgeoIdWidget()
        except BaseException as e:
            Logger.log_error('delete_scenario_elem failed (traceback below) \n{}'.format(traceback.format_exc()))
    
    def repair_overlapped_node(self, act_f_o, act_rpir_o):
        Logger.log_trace('Called: repair_overlapped_node')
        try:
            if len(self.overlapped_node) < 1:
                QMessageBox.warning(self, "Warning", "There are no overlapped nodes to repair.")
                return

            nodes_of_no_use = error_fix.repair_overlapped_node(self.overlapped_node)
            edit_node.delete_nodes(self.getNodeSet(self.mgeo_key), nodes_of_no_use)

            act_rpir_o.setDisabled(True)
            self.updateMgeoIdWidget()
            Logger.log_info('repair_overlapped_node done OK')
        except BaseException as e:
            Logger.log_error('repair_overlapped_node failed (traceback below) \n{}'.format(traceback.format_exc()))


    # 특정 Node에 대한 Repair Overlapped Node 기능
    def repair_overlapped_node(self, node):
            overlapped_node_set = [node, ]
            
            #dist_threshold = 0.1
            dist_threshold, okPressed = QInputDialog.getText(self, "Repair overlapped node", "Input distance threshold value", QLineEdit.Normal, '0.1')

            try:
                dist_threshold = float(dist_threshold)
            except Exception:
                QMessageBox.warning(self.canvas, "Warning", "Input can only be number.")
                return

            for another_idx, another_node in self.getNodeSet(self.mgeo_key).nodes.items():
                # skip_flag 또한 0일 경우에만 확인하면 된다. (현재 노드의 경우 1로 체크가 되었으므로 skip된다)
                if another_idx != node.idx:
                    pos_vector = another_node.point - node.point
                    dist = np.linalg.norm(pos_vector, ord=2)
                    
                    if dist < dist_threshold:
                        overlapped_node_set.append(another_node)

            Logger.log_trace('Called: repair_overlapped_node for ' + node.idx)
            try:
                if len(overlapped_node_set) < 2:
                    QMessageBox.warning(self, "Warning", "There is no overlapped node to repair.")
                    return

                cmd_repair_overlapped_node = RepairOverlappedNode(self, [overlapped_node_set])
                self.command_manager.execute(cmd_repair_overlapped_node)

                Logger.log_info('repair_overlapped_node done OK')
            except BaseException as e:
                Logger.log_error('repair_overlapped_node failed (traceback below) \n{}'.format(traceback.format_exc()))


    def find_dangling_nodes(self, act_f_d, act_del_d, act_clr):
        Logger.log_trace('Called: find_dangling_nodes')
        try:
            if self.getNodeSet(self.mgeo_key) is None or len(self.getNodeSet(self.mgeo_key).nodes) < 1 :
                QMessageBox.warning(self, "Warning", "There is no node data.")
                return

            self.dangling_nodes = error_fix.find_dangling_nodes(self.getNodeSet(self.mgeo_key))
            for node in self.dangling_nodes:
                self.list_error.append({'type': MGeoItem.NODE, 'id': node.idx})

            node_idx_string = '['
            for node in self.dangling_nodes:
                node_idx_string += '{}, '.format(node.idx)
            node_idx_string += ']'
            Logger.log_info('find_dangling_nodes result: {}'.format(node_idx_string))

            # dangling_nodes에 node 유/무에 따라 (delete_dangling_nodes) menu action enable
            if self.dangling_nodes is None or self.dangling_nodes == []:
                QMessageBox.warning(self, "Warning", "There is no dangling node data.")
                act_del_d.setDisabled(True)
                if self.overlapped_node is None or self.overlapped_node == []:
                    act_clr.setDisabled(True)
            else:
                act_del_d.setDisabled(False)
                act_clr.setDisabled(False)
        
        except BaseException as e:
            Logger.log_error('find_dangling_nodes failed (traceback below) \n{}'.format(traceback.format_exc()))


    def delete_dangling_nodes(self, act_f_d, act_del_d):
        Logger.log_trace('Called: delete_dangling_nodes')
        try:
            node_idx_string = '['
            for node in self.dangling_nodes:
                node_idx_string += '{}, '.format(node.idx)
            node_idx_string += ']'

            edit_node.delete_nodes(self.getNodeSet(self.mgeo_key), self.dangling_nodes)
            act_del_d.setDisabled(True)
            self.updateMgeoIdWidget()
            Logger.log_info('dangling nodes ({}) deleted.'.format(node_idx_string))
        
        except BaseException as e:
            Logger.log_error('delete_item failed (traceback below) \n{}'.format(traceback.format_exc()))


    def clear_highlight(self, act_f_o, act_f_d, act_clr, act_rpir_o, act_del_d):
        Logger.log_trace('Called: clear_highlight')
        try:
            self.list_error.clear()
            self.list_highlight1.clear()
            self.list_highlight2.clear()
            self.list_highlight3.clear()
            self.overlapped_node.clear()
            self.dangling_nodes.clear()
            act_f_o.setDisabled(False)
            act_f_d.setDisabled(False)
            act_clr.setDisabled(True)
            act_rpir_o.setDisabled(True)
            act_del_d.setDisabled(True)
            
        except BaseException as e:
            Logger.log_error('clear_highlight failed (traceback below) \n{}'.format(traceback.format_exc()))       


    def create_junction(self):
        Logger.log_trace('Called: create_junction')
        try:
            # 선택된 노드를 받아온다
            nodes_to_create_juction = []
            if len(self.list_sp) ==0:
                self.auto_create_junction()
                return
            for sp in self.list_sp:

                # TEMP: 버그 workaround
                if sp['type'] is None:
                    continue

                # 노드 이외 다른 종류의 데이터가 선택되었는지 체크
                if sp['type'] != MGeoItem.NODE:
                    Logger.log_error('Only nodes are allowed to create a junction.')
                    return

                node = self.getNodeSet(self.mgeo_key).nodes[sp['id']]
                nodes_to_create_juction.append(node)

            if len(nodes_to_create_juction) == 0:
                Logger.log_error('There are no selected nodes.')
                return 

            new_junc = edit_junction.create_junction(
                self.getJunctionSet(self.mgeo_key),
                nodes_to_create_juction)
            self.mgeo_item_added(self.mgeo_key, MGeoItem.JUNCTION, new_junc)

            self.updateMgeoIdWidget()
            Logger.log_info('Junction (id = {}) created'.format(new_junc.idx))
        
        except BaseException as e:
            Logger.log_error('create_junction failed (traceback below) \n{}'.format(traceback.format_exc()))


    def auto_create_junction(self):
        Logger.log_trace('Called: Auto_create_junction')

        jc_candidate_roads = [] 
        
        # this function is running with roads
        if len(self.odr_data.roads) ==0:
            Logger.log_error('Create_Road should be done')
            return
        
        # already_jc_nodes = []
        # for junction in self.getJunctionSet().junctions.values():
        #     already_jc_nodes.append(junction.jc_nodes)
        self.getJunctionSet().junctions = dict()

        for road in self.odr_data.roads.values():
            if len(road.get_to_roads()) > 1:
                jc_candidate_roads.append(road)
        
            elif len(road.get_from_roads()) > 1:
                jc_candidate_roads.append(road)

        end_roads = []
        for i in range(len(jc_candidate_roads)):
            if len(jc_candidate_roads[i].get_to_roads()) >1:
                for end_road_candidate in jc_candidate_roads[i].get_to_roads():
                    if end_road_candidate.get_to_roads() == []:
                        end_roads.append(jc_candidate_roads[i])
            if len(jc_candidate_roads[i].get_from_roads()) >1:
                for end_road_candidate in jc_candidate_roads[i].get_from_roads():
                    if end_road_candidate.get_from_roads() == []:
                        end_roads.append(jc_candidate_roads[i])
        
        for road in end_roads:
            try:
                jc_candidate_roads.remove(road)
            except:
                pass
        
        removed_road = []
        set_of_jc_node_set =[]
        
        for i in range(len(jc_candidate_roads)):
            nodes_to_create_juction = []
            removed_road = list(set(removed_road))
            
            if jc_candidate_roads[i] in removed_road:
                continue
            jc_roads_list = []
            if len(jc_candidate_roads[i].get_to_roads()) >1:
                jc_roads = jc_candidate_roads[i].get_to_roads()
                jc_roads_list.append(jc_roads)
            if len(jc_candidate_roads[i].get_from_roads()) >1: 
                jc_roads = jc_candidate_roads[i].get_from_roads()
                jc_roads_list.append(jc_roads)

            for jc_roads in jc_roads_list:
                temp_jc_roads = []
                nodes_to_create_juction = []
                while True:
                    for road in jc_roads:    
                        try:
                            if len(road.get_to_roads()[0].get_from_roads()) > 1:
                                for road_candidate in road.get_to_roads()[0].get_from_roads():
                                    if road_candidate not in temp_jc_roads:
                                        temp_jc_roads.append(road_candidate)
                                    # removed_road.append(road_candidate.get_to_roads()[0])        
                        except:
                            pass
                        try:
                            if len(road.get_from_roads()[0].get_to_roads()) > 1:
                                for road_candidate in road.get_from_roads()[0].get_to_roads():
                                    if road_candidate not in temp_jc_roads:
                                        temp_jc_roads.append(road_candidate)                    
                                    # removed_road.append(road_candidate.get_from_roads()[0])
                        except:
                            pass
                    temp_jc_roads = list(set(temp_jc_roads))
                    
                    if temp_jc_roads == jc_roads:
                        break
                    else:
                        jc_roads = list(set(temp_jc_roads))
                
                for road in jc_roads:
                    nodes_to_create_juction = nodes_to_create_juction + road.get_to_node_set_in_road() + road.get_from_node_set_in_road()
                    
                    for road_link in road.link_list_not_organized: 
                        if road_link.from_node.from_links == []:
                            nodes_to_create_juction.remove(road_link.from_node)
                            
                            for node in road.get_from_node_set_in_road():
                                if  node.from_links == None:
                                    continue
                                if len(road.get_from_node_set_in_road()) ==1:
                                    road_link.from_node = None
                                    node.add_to_links(road_link)
                                    road_link.set_from_node(node)
                                    #road_link.points.append(node.point)
                                
                                if abs(road_link.ego_lane - node.to_links[0].ego_lane) == 0:
                                    road_link.from_node = None
                                    node.add_to_links(road_link)
                                    road_link.set_from_node(node)
                                    # road_link.points= list(road_link.points) append(node.point)

                                elif abs(road_link.ego_lane - node.to_links[0].ego_lane) == 1:
                                    road_link.from_node = None
                                    node.add_to_links(road_link)
                                    road_link.set_from_node(node)
                                    #road_link.points.append(node.point)
                jc_node_set = list(set(nodes_to_create_juction))
                if jc_node_set in set_of_jc_node_set:
                    continue
                else:
                    set_of_jc_node_set.append(jc_node_set)
                new_junc = edit_junction.create_junction(
                        self.getJunctionSet(self.mgeo_key),
                        jc_node_set)
                self.mgeo_item_added(self.mgeo_key, MGeoItem.JUNCTION, new_junc)
                
                Logger.log_info('Junction (id = {}) created'.format(new_junc.idx))
        
        self.updateMgeoIdWidget()
        Logger.log_trace('Auto_create_junction is done')
        return



        # if len(jc_candidate_roads) == 0:

        #     return 
        # else:
        #     self.auto_create_junction(temp_jc_roads = []\
        #         , jc_candidate_roads = jc_candidate_roads\
        #         , jc_roads = jc_candidate_roads[0].get_to_roads()[0]\
        #             , nodes_to_create_juction = [])

    def temp_workaround_remove_none_item_in_list_sp(self):
        # 버그로 인해 가끔 {'id':0, 'type':None} 이 있곤 함. 이에 대한 workaround
        none_item_found = False

        for selected_item in self.list_sp:
            if selected_item['type'] is None:
                none_item_found = True
                none_item = selected_item

        if none_item_found:
            self.list_sp.remove(none_item)


    def connect_nodes(self):
        Logger.log_trace('Called: connect_nodes')
        try:
            self.temp_workaround_remove_none_item_in_list_sp()

            connect_nodes_cmd = ConnectNode(self, self.list_sp)
            self.command_manager.execute(connect_nodes_cmd)

        except BaseException as e:
            Logger.log_error('connect_nodes failed (traceback below) \n{}'.format(traceback.format_exc()))


    def gen_road_poly(self) :
        Logger.log_trace('Called: gen_road_poly')
        try:
            if len(self.list_sp) < 2:
                Logger.log_info('Invalid operation: gen_road_poly needs more than 2 items (# of selected items: {})'.format(len(self.list_sp)))
                return

            if self.list_sp[0]['type'] != MGeoItem.LANE_BOUNDARY :
                Logger.log_info('Invalid operation: gen_road_poly needs LaneMarking type (Selected type : {})'.format(type(self.list_sp[0])))
                return

            gen_road_poly_cmd = GenerateRoadPoly(self, self.list_sp)
            self.command_manager.execute(gen_road_poly_cmd)
                    
        except BaseException as e:
            Logger.log_error('gen_road_poly failed (traceback is down below) \n{}'.format(traceback.format_exc()))
        return


    def merge_links(self):
        Logger.log_trace('Called: merge_links')
        try:
            if self.sp['type'] == MGeoItem.LINK:
                lines = self.getLinkSet(self.mgeo_key).lines
                line_type = MGeoItem.LINK
            elif self.sp['type'] == MGeoItem.LANE_BOUNDARY:
                lines = self.getLaneBoundarySet(self.mgeo_key).lanes
                line_type = MGeoItem.LANE_BOUNDARY
            else:
                Logger.log_error('Invalid operation: merge_links works only for links or lane_boundary items')
                return

            # REFACTOR(sglee) : refactor this into edit_link or somewhere
            self.temp_workaround_remove_none_item_in_list_sp()

            # 현재 선택된 아이템이 line이고, 2개일 때만 동작한다.
            if len(self.list_sp) != 2:
                Logger.log_info('Invalid operation: merge_links works only when two connected links are selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            for selected_item in self.list_sp:
                if selected_item['type'] != MGeoItem.LINK and selected_item['type'] != MGeoItem.LANE_BOUNDARY:
                    Logger.log_info('Invalid operation: merge_links works only when two connected links are selected. ({} type data is included)'.format(selected_item['type']))
                    return

            # 두 링크가 연결되어있는 링크인지 검색해본다
            link0 = lines[self.list_sp[0]['id']]
            link1 = lines[self.list_sp[1]['id']]
            
            merge_links_cmd = MergeLink(self, line_type, link0, link1)
            self.command_manager.execute(merge_links_cmd)
            self.reset_inner_link_point_ptr()
            return

        except BaseException as e:
            Logger.log_error('merge_links failed (traceback below) \n{}'.format(traceback.format_exc()))


    def divide_a_link_smart(self):
        """
        keep_front값을 자동으로 설정해주는 Helper
        """
        Logger.log_trace('Called: divide_a_link_smart')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return

            # 선택된 link, point idx를 받아온다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            # 시작 위치와 마지막 위치에서는 생성을 할 수 없다
            if point_idx == 0 or point_idx == len(link.points) - 1:
                Logger.log_error('divide_a_link failed (You should select points other than the first or the last point)')
                return 

            
            # 2개의 points로 분리한다
            new_points_start = link.points[:point_idx+1] # point_idx를 포함해야 하므로
            new_points_end = link.points[point_idx:]
            
            dist_start = self.__get_total_distance(new_points_start)
            dist_end = self.__get_total_distance(new_points_end)
            
            if dist_start >= dist_end:
                Logger.log_trace('dist_start: {:.2f}, dist_end: {:.2f} -> keep_front = True'.format(dist_start, dist_end))
                keep_front = True
            else:
                Logger.log_trace('dist_start: {:.2f}, dist_end: {:.2f} -> keep_front = False'.format(dist_start, dist_end))
                keep_front = False
                
            
            if self.sp['type'] == MGeoItem.LANE_BOUNDARY:
                self.divide_a_line(keep_front)
            else:
                self.divide_a_link(keep_front)

            self.updateMgeoIdWidget()

        except BaseException as e:
            Logger.log_error('divide_a_link_smart failed (traceback below) \n{}'.format(traceback.format_exc()))


    def divide_a_line(self, keep_front):
        if self.sp['type'] == MGeoItem.LINK:
            self.divide_a_link(keep_front)
        elif self.sp['type'] == MGeoItem.LANE_BOUNDARY:
            self.divide_a_laneMarking(keep_front)
        else:
            Logger.log_error('This type({}) cannot be divided'.format(self.sp['type']))


    def divide_a_laneMarking(self, keep_front):
        """
        keep_front: True 이면, 기존 링크로서 시작 부분을 유지, False 이면 끝부분을 유지
        None이면 긴 쪽을 유지시킨다
        """
        # TODO(sglee): 여기 구현해야 함!!!
        Logger.log_trace('Called: divide_a_laneMarking')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return

            # 선택된 link, point idx를 받아온다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            # 시작 위치와 마지막 위치에서는 생성을 할 수 없다
            if point_idx == 0 or point_idx == len(link.points) - 1:
                Logger.log_error('divide_a_laneMarking failed (You should select points other than the first or the last point)')
                return 

            divide_link_cmd = DivdeLandBoundary(self, link, point_idx, keep_front)
            self.command_manager.execute(divide_link_cmd)

            self.updateMgeoIdWidget()
            Logger.log_info('divide_a_laneMarking is completed successfully')
            return

        except BaseException as e:
            Logger.log_error('divide_a_laneMarking failed (traceback below) \n{}'.format(traceback.format_exc()))



    def divide_a_link(self, keep_front):
        """
        keep_front: True 이면, 기존 링크로서 시작 부분을 유지, False 이면 끝부분을 유지
        None이면 긴 쪽을 유지시킨다
        """
        # TODO(sglee): 여기 구현해야 함!!!
        Logger.log_trace('Called: divide_a_link')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return

            # 선택된 link, point idx를 받아온다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            # 시작 위치와 마지막 위치에서는 생성을 할 수 없다
            if point_idx == 0 or point_idx == len(link.points) - 1:
                Logger.log_error('divide_a_link failed (You should select points other than the first or the last point)')
                return 

            divide_link_cmd = DivdeLink(self, link, point_idx, keep_front)
            self.command_manager.execute(divide_link_cmd)
            
            Logger.log_info('divide_a_link is done successfully')
            return

        except BaseException as e:
            Logger.log_error('divide_a_link failed (traceback below) \n{}'.format(traceback.format_exc()))


    def add_link_point(self):
        """
        Link 또는 Line 내부의 점을 추가한다. 현재 포인트와 다음 포인트 사이의 중간 위치에 추가한다.
        """
        Logger.log_trace('Called: add_link_point')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return

            # 선택된 link, point idx를 받아온다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            # 마지막 위치에서는 생성을 할 수 없다
            if  point_idx == len(link.points) - 1:
                Logger.log_error('add_link_point failed (You should select points other than the last point)')
                return 

            add_link_pnt_cmd = AddLinkPoint(self, link, point_idx)
            self.command_manager.execute(add_link_pnt_cmd)
            Logger.log_info('add_link_point is done successfully')
            return

        except BaseException as e:
            Logger.log_error('add_link_point failed (traceback below) \n{}'.format(traceback.format_exc()))
            

    def set_new_road_id(self, build_preliminary_road_callback):
        """
        선택된 링크에 새로운 Road ID를 부여한다
        """
        Logger.log_trace('Called: set_new_road_id')
        try:
            self.temp_workaround_remove_none_item_in_list_sp()
            
            # 현재 선택된 아이템이 없으면 동작하지 않는다
            if len(self.list_sp) == 0:
                Logger.log_warning('set_new_road_id failed: set_new_road_id works only when links are selected. (No item is selected)')
                return

            # 선택된 대상이 link인지만 확인한다
            for selected_item in self.list_sp:
                if selected_item['type'] != MGeoItem.LINK:
                    Logger.log_info('set_new_road_id failed: set_new_road_id works only when links are selected. ({} type data is included)'.format(selected_item['type']))
                    return

            # 현재 검색할 수 있는 road set이 없으면 무의미하다
            if len(self.odr_data.roads) == 0:
                Logger.log_error('set_new_road_id failed: Create roads first. (preliminary roads are ok)')
                return

            new_road_id, okPressed = QInputDialog.getText(self, "Set a new Road ID", "Enter ID", QLineEdit.Normal, '')
            if not okPressed:
                Logger.log_info('set_new_road_id is canceled by user.')
                return
                
            Logger.log_trace('set_new_road_id user req: new_road_id: {}'.format(new_road_id))

            if new_road_id in self.odr_data.roads.keys():
                QMessageBox.warning(self, "Error", 'road_id: {} alreay exists.'.format(new_road_id))
                Logger.log_error('set_new_road_id failed: road_id: {} alreay exists.'.format(new_road_id))
                return

            # 이제는 new_road_id가 정말 새로운 road_id 임이 확인되었다.
            # 대상인 Link에 새로운 road_id를 입력하면 된다.
            for selected_item in self.list_sp:
                link = self.getLinkSet(self.mgeo_key).lines[selected_item['id']]
                link.road_id = new_road_id
                Logger.log_info('set_new_road_id >> link: {} road_id changed to: {}'.format(link.idx, new_road_id))

            # Preliminary Road를 다시 생성한다.
            Logger.log_trace('set_new_road_id method will call create_prelimiary_odr_roads method automatically.')
            build_preliminary_road_callback()

            self.updateMgeoIdWidget()
            Logger.log_info('set_new_road_id is completed successfully.')
            return

        except BaseException as e:
            Logger.log_error('set_new_road_id failed (traceback below) \n{}'.format(traceback.format_exc()))
         

    def __get_total_distance(self, points):
        total_distance = 0
        for i in range(len(points) - 1) :
            vect = points[i+1] - points[i]
            dist_between_each_point_pair = np.linalg.norm(vect, ord=2)
            total_distance += dist_between_each_point_pair
        return total_distance


    def connect_links(self):
        Logger.log_trace('Called: connect_links')
        try:
            self.temp_workaround_remove_none_item_in_list_sp()

            # 현재 선택된 아이템이 node이고, 2개일 때만 동작한다.
            if len(self.list_sp) != 2:
                Logger.log_info('Invalid operation: connect_links works only when two nodes are selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            for selected_item in self.list_sp:
                if selected_item['type'] != MGeoItem.NODE:
                    Logger.log_info('Invalid operation: connect_links works only when two nodes are selected. ({} type data is included)'.format(selected_item['type']))
                    return
            
            # 두 노드가 이미 연결되어있는 노드인지 검색해본다
            start_node = self.getNodeSet(self.mgeo_key).nodes[self.list_sp[0]['id']]
            end_node = self.getNodeSet(self.mgeo_key).nodes[self.list_sp[1]['id']]

            if (end_node in start_node.get_to_nodes()) or (end_node in start_node.get_from_nodes()):
                Logger.log_info('Invalid operation: two links are already connected!')
                return

            # 새로운 링크를 생성한다 (attribute는 비어있다)
            connecting_link = Link()
            points = np.vstack((start_node.point,end_node.point))
            connecting_link.set_points(points)

            # 이 라인의 from_node, to_node 설정해주기
            connecting_link.set_from_node(start_node)
            connecting_link.set_to_node(end_node)

            self.getLinkSet(self.mgeo_key).append_line(connecting_link, create_new_key=True)

            # 
            Logger.log_info('connecting link (id: {}) created (from node: {} -> to: {})'.format(connecting_link.idx, start_node.idx, end_node.idx))

        except BaseException as e:
            Logger.log_error('connect_links failed (traceback below) \n{}'.format(traceback.format_exc()))


    def reverse_link_points(self):
        Logger.log_trace('Called: reverse_link_points')
        try:
            # 현재 선택된 아이템이 line이고, 1개 이상일 때만 동작한다.
            if len(self.list_sp) < 1:
                Logger.log_info('Invalid operation: reverse_link_points works only when one more links are selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            for selected_item in self.list_sp:
                if (selected_item['type'] != MGeoItem.LINK and selected_item['type'] != MGeoItem.LANE_BOUNDARY) :
                    Logger.log_info('Invalid operation: reverse_link_points works only when links are selected. ({} type data is included)'.format(selected_item['type']))
                    return

            reverse_link_point_cmd = ReverseLinkPoint(self, self.list_sp)
            self.command_manager.execute(reverse_link_point_cmd)

            return

        except BaseException as e:
            Logger.log_error('reverse_links failed (traceback below) \n{}'.format(traceback.format_exc()))
    
    
    def delete_object_inside_xy_range(self):
        Logger.log_trace('Called: delete_object_inside_xy_range')
        if not (self.xRot == 0 and self.yRot == 0):
            QMessageBox.information(self, "Warning", "View must be in the 'Top-Down' mode (X = 0, Y = 0) to support this feature.")
            return
        try:
            result = QMessageBox.question(self, "Delete objects", 
                                'Delete objects inside the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]), 
                                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if result == QMessageBox.Ok:
                
                # 핵심 삭제 함수
                if len(self.mgeo_maps_dict) == 0:
                    Logger.log_warning('Nothing to delete in the Map Inside')
                else:
                    for key in self.mgeo_maps_dict:
                        self.mgeo_planner_map = self.mgeo_maps_dict[key]
                        edit_mgeo_planner_map.delete_object_inside_xy_range(self.mgeo_planner_map, self.xlim, self.ylim)
                        self.odr_data = OdrData(mgeo_planner_map=None) # 원본 MGeo가 변경되었으므로, OdrData는 초기화하여 사용자가 다시 만들게끔한다
                        self.mgeo_rtree[key] = MgeoRTree(self.mgeo_maps_dict[key])

                    QMessageBox.information(self, "Delete complete", 'Delete objects inside the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]))
            self.updateMgeoIdWidget()
            self.command_manager.clear()
        except BaseException as e:
            Logger.log_error('delete_object_inside_xy_range failed (traceback below) \n{}'.format(traceback.format_exc()))


    def delete_objects_out_of_xy_range(self, hard):
        Logger.log_trace('Called: delete_objects_out_of_xy_range')
        if not (self.xRot == 0 and self.yRot == 0):
            QMessageBox.information(self, "Warning", "View must be in the 'Top-Down' mode (X = 0, Y = 0) to support this feature.")
            return
        try:
            result = QMessageBox.question(self, "Delete objects", 
                                'Delete objects out of the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]), 
                                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if result == QMessageBox.Ok:
                
                if len(self.mgeo_maps_dict) == 0:
                    Logger.log_warning('Nothing to delete in the Map Outside')
                else:
                    for key in self.mgeo_maps_dict:
                        self.mgeo_planner_map = self.mgeo_maps_dict[key]
                        edit_mgeo_planner_map.delete_objects_out_of_xy_range(self.mgeo_planner_map, self.xlim, self.ylim, hard)
                        self.mgeo_rtree[key] = MgeoRTree(self.mgeo_maps_dict[key])
                            
                    QMessageBox.information(self, "Delete complete", 'Delete objects out of the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]))
            self.updateMgeoIdWidget()
            self.command_manager.clear()
            
        except BaseException as e:
            Logger.log_error('delete_objects_out_of_xy_range failed (traceback below) \n{}'.format(traceback.format_exc()))


    def create_odr_roads_and_find_ref_lines(self):    
        Logger.log_trace('Called: create_odr_roads_and_find_ref_lines')
        try: 
            link_set = self.getLinkSet(self.mgeo_key)

            converter = MGeoToOdrDataConverter()
            self.odr_data = converter.create_odr_roads(link_set)
            self.updateMgeoIdWidget()
            return self.odr_data

        except BaseException as e:
            Logger.log_error('create_odr_roads_and_find_ref_lines failed (traceback below) \n{}'.format(traceback.format_exc()))


    def create_complete_odr_data_and_save_as_file(self):
        # try:   
            mgeo_planner_map = self.mgeo_planner_map
            list_sp = self.list_sp
            converter = MGeoToOdrDataConverter()
            self.odr_data = converter.convert(mgeo_planner_map)
            return self.odr_data

        # except BaseException as e:
        #     Logger.log_error('create_complete_odr_data_and_save_as_file failed (traceback below) \n{}'.format(traceback.format_exc()))


    def updateXLimYLim(self):
        """QOpenGLWidget에 그려진 OpenGL의 좌표의 범위를 Widget 아래 Text로 출력한다"""
        
        # OpenGL 좌표를 구하기 위해 Z=0에 투명한 평면의 Object를 그려준다
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_FRONT_AND_BACK)
        glEnable(GL_BLEND)
        glBegin(GL_POLYGON)
        glColor4f(0, 0, 0, 0)
        
        glVertex3f(-10000000, -10000000, 0)
        glVertex3f(-10000000, 10000000, 0)
        glVertex3f(10000000, 10000000, 0)
        glVertex3f(10000000, -10000000, 0)
        
        glVertex3f(0, -10000000, -10000000)
        glVertex3f(0, -10000000, 10000000)
        glVertex3f(0, 10000000, 10000000)
        glVertex3f(0, 10000000, -10000000)

        glVertex3f(-10000000, 0, -10000000)
        glVertex3f(-10000000, 0, 10000000)
        glVertex3f(10000000, 0, 10000000)
        glVertex3f(10000000, 0, -10000000)

        glEnd()
        glFlush()

        # 좌측상단, 우측하단의 Widget 좌표를 OpenGL 좌표로 바꿔준다
        winX_0 = 0
        winY_0 = self.viewport[3] - 1
        winZ_0 = glReadPixels(winX_0, int(winY_0), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        left_top = gluUnProject(winX_0, winY_0, winZ_0, self.modelview, self.projection, self.viewport)

        winX_m = self.viewport[2] - 1
        winY_m = 0
        winZ_m = glReadPixels(winX_m, int(winY_m), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        right_bottom = gluUnProject(winX_m, winY_m, winZ_m, self.modelview, self.projection, self.viewport)

        if np.isnan(right_bottom[0]) == False and np.isnan(left_top[0]) == False:
            self.xlim = [math.floor(right_bottom[0]), math.floor(left_top[0])]
        if np.isnan(right_bottom[1]) == False and np.isnan(left_top[1]) == False:
            self.ylim = [math.floor(right_bottom[1]), math.floor(left_top[1])]
        
        # 오름차순으로 정렬한다
        self.xlim.sort()
        self.ylim.sort()

        self.position_label[0].setText('range x = [{}, {}]'.format(self.xlim[0], self.xlim[1]))
        self.position_label[1].setText('range y = [{}, {}]'.format(self.ylim[0], self.ylim[1]))
        self.position_label[2].setText(str(self.zoom))
        
        
    @staticmethod
    def _add_margin_to_range(lim, margin):
        mid = (lim[1] + lim[0])/2
        dist_from_mid = (lim[1] - lim[0])/2

        new_min = mid - dist_from_mid * margin
        new_max = mid + dist_from_mid * margin
        return (new_min, new_max)


    def onIDRightClickEvent(self, point):
        # Validity Check
        mgeo_index = self.tree_data.indexAt(point)
        if not mgeo_index.isValid():
            return

        # Check whether or not the item is a MGeo-element
        mgeo_item = self.tree_data.itemAt(point)
        root_item = mgeo_item
        while root_item.parent():
            root_item = root_item.parent()
            
        mgeo_key = None
        scenario_key = None
        if root_item.text(0) in self.mgeo_maps_dict:
            mgeo_key = root_item.text(0)
        elif root_item.text(0).split(' ')[0] == "OpenSCENARIO":
            scenario_key = root_item.text(0)
        else: 
            return
        
        if mgeo_key == None and scenario_key == None:
            return
        
        # empty MGeo
        if not self.mgeo_maps_dict:
            return
        
        event_pos = QtGui.QCursor(Qt.PointingHandCursor).pos()
        
        contextMenu = QMenu(self)
        delete_act = contextMenu.addAction("Delete {}".format(mgeo_key))
        delete_act.setShortcut('Delete')
        delete_act.triggered.connect(lambda:self.delete_mgeo(mgeo_key))
        contextMenu.addSeparator()
        
        if mgeo_item.text(0) in self.mgeo_maps_dict.keys():
            action = contextMenu.exec_(event_pos)
        
        if self.osc_client_triggered == True:
            return

        if scenario_key != None:            
            if mgeo_item == None:
                return

            contextMenu_scenario = QMenu(self)
            selected_item_type = ScenarioItem[type(mgeo_item.data(1, Qt.UserRole)).__name__]
            
            # Add element wizard area
            if selected_item_type in ABLE_ADD_ACTION_LIST:
                new_item = contextMenu_scenario.addAction(f"Add Action Wizard")
                new_item.triggered.connect(lambda checked, item=mgeo_item.data(1, Qt.UserRole): self.add_action(item))
                contextMenu_scenario.addSeparator()
            elif selected_item_type in ABLE_ADD_CONDITION_LIST:
                new_item = contextMenu_scenario.addAction(f"Add Condition Wizard")
                new_item.triggered.connect(lambda checked, item=mgeo_item.data(1, Qt.UserRole): self.add_condition(item))
                contextMenu_scenario.addSeparator()
            elif selected_item_type in ABLE_ADD_INIT_ACTION_LIST:
                for action_type in ["Global", "Private", "User Defined"]:
                    new_item = contextMenu_scenario.addAction(f"Add {action_type} Wizard")
                    new_item.triggered.connect(lambda checked, item=mgeo_item.data(1, Qt.UserRole), at=action_type: self.add_init_action(item, at))
                contextMenu_scenario.addSeparator()
            elif selected_item_type == ScenarioItem.Entities:
                new_item = contextMenu_scenario.addAction(f"Add Entity Wizard")
                new_item.triggered.connect(lambda checked: self.add_entity_in_tree())
                contextMenu_scenario.addSeparator()

            # Add element area
            if selected_item_type in ABLE_ADD_ITEM_LIST:
                self.make_add_scenario_element_menu( selected_item_type, 
                                                     contextMenu_scenario, 
                                                     mgeo_item, 
                                                     { "child_types": [] } )

            # Delete element area 
            disable_delete_item_list = [ScenarioItem.ScenarioDefinition, ScenarioItem.FileHeader, ScenarioItem.Catalog, 
                                        ScenarioItem.Entities, ScenarioItem.Storyboard, ScenarioItem.RoadNetwork, 
                                        ScenarioItem.Init, ScenarioItem.InitActions, ScenarioItem.Vehicle, 
                                        ScenarioItem.Pedestrian, ScenarioItem.MiscObject, ScenarioItem.Trigger, ScenarioItem.Actors, 
                                        ScenarioItem.TriggeringEntities, ScenarioItem.SpeedActionTarget, ScenarioItem.TransitionDynamics, 
                                        ScenarioItem.LaneChangeTarget, ScenarioItem.TrafficDefinition, 
                                        ScenarioItem.VehicleCategoryDistribution, ScenarioItem.ControllerDistribution]
            
            if not selected_item_type in disable_delete_item_list:
                delete_scenario_elm = contextMenu_scenario.addAction("Delete {}".format(mgeo_item.text(0)))
                delete_scenario_elm.setShortcut('Delete')
                delete_scenario_elm.triggered.connect(lambda:self.delete_scenario_element(mgeo_item))
                contextMenu_scenario.addSeparator()
            
            action = contextMenu_scenario.exec_(event_pos)
            
        #self.mgeo_planner_map = self.mgeo_maps_dict[mgeo_key]
    
    def make_add_scenario_element_menu(self, selected_item_type, menu:QMenu, mgeo_item, class_list):
        selected_item_info = ADD_ELEMENT_STRUCT[selected_item_type]

        if "pass_to" in selected_item_info:
            selected_item_info = ADD_ELEMENT_STRUCT[selected_item_info["pass_to"]]

        add_elements = selected_item_info["add"] if "add" in selected_item_info else {}
        set_elements = selected_item_info["set"] if "set" in selected_item_info else {}
        xor_elements = selected_item_info["xor"] if "xor" in selected_item_info else {}

        if not add_elements and not xor_elements and not set_elements:
            return False
        else:
            make_list = { "Set": set_elements, "Add": add_elements, "Change": xor_elements, }
        
        for menu_prefix, menu_item in make_list.items():
            class_list["mode"] = menu_prefix
            for attrib_name, childs in menu_item.items():
                for child in childs:
                    child_name = child.name
                    new_menu = QMenu(f"{menu_prefix} {child_name}", self)
                    new_class_list = deepcopy(class_list)
                    new_class_list["child_types"].append(child_name)
                    btn_flag = True
                    if "use_parent_name" not in selected_item_info:
                        new_class_list["target"] = attrib_name
                    if child in ADD_ELEMENT_STRUCT:
                        if "pass_to" in ADD_ELEMENT_STRUCT[child]:
                            new_class_list["child_types"].append(ADD_ELEMENT_STRUCT[child]["pass_to"].name)
                        if "recursive_flag" in ADD_ELEMENT_STRUCT[child]:
                            if self.make_add_scenario_element_menu(child, new_menu, mgeo_item, new_class_list):
                                menu.addMenu(new_menu)
                                btn_flag = False
                    if btn_flag:
                        del new_menu    # resource management
                        new_item = QAction(f"{menu_prefix} {child_name}", self)
                        new_item.triggered.connect(lambda checked, item=mgeo_item, param=new_class_list: self.add_scenario_element(item, param))
                        menu.addAction(new_item)
            menu.addSeparator()

        return True

    # find 관련 함수
    def onIdDoubleClickEvent(self, item, col):
        """Id를 더블클릭하면 해당 Item으로 이동한다"""

        find_id = item.text(0)
        try:    # MGeo item
            # 현재 selected 된 key 값을 가지고 온다.
            find_key = self.mgeo_key
            find_type = MGeoItem[item.parent().text(0)]
            self.highlight_mgeo_item(find_key, find_type, find_id)
            if self.find_item is not None:
                self.trans_point_by_id(self.find_item)
                self.updateMgeoPropWidget(self.find_item)
        except:
            pass
        
        try:    # MScenario item
            find_key = self.mgeo_key
            find_type = MScenarioItem[item.parent().text(0)]
            self.highlight_mgeo_item(find_key, find_type, find_id)
            if self.find_item is not None:
                self.trans_point_by_id(self.find_item)
                self.updateMgeoPropWidget(self.find_item)
        except:
            pass
        
        try:    # OpenScenario item
            find_key = self.mgeo_key
            find_type = ScenarioItem[item.parent().text(0)]
            self.highlight_mgeo_item(find_key, find_type, find_id)
            if self.find_item is not None:
                self.trans_point_by_id(self.find_item)
                self.updateMgeoPropWidget(self.find_item)
        except:
            pass
            
    def find_by_mgeo_id(self):
        Logger.log_trace('Called: find_mgeo_item_by_mgeo_id')
        findMGeoItemWindow = FindMGeoItemWindow()
        
        key = self.mgeo_key
        node_set_lst = self.getNodeSet(self.mgeo_key).nodes
        link_set_lst = self.getLinkSet(self.mgeo_key).lines
        traffic_sign_lst = self.getTSSet(self.mgeo_key).signals
        traffic_light_lst = self.getTLSet(self.mgeo_key).signals
        junction_lst = self.getJunctionSet(self.mgeo_key).junctions
        road_lst = self.getRoadSet()
        lane_marking_lst = self.getLaneBoundarySet(self.mgeo_key).lanes 
        single_crosswalk_lst = self.getSingleCrosswalkSet(self.mgeo_key).data
        crosswalk_lst = self.getCrosswalkSet(self.mgeo_key).data
        
        mgeo_ref_dict = {}
        try: 
            if findMGeoItemWindow.exec_():                    
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in node_set_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    node_set = self.getNodeSet(self.mgeo_key)
                    type = MGeoItem.NODE
                    try:
                        node_to_be_highlighted = mgeo_find.find_node(search_conditions, node_set, is_primitive=True)
                        find_id = node_to_be_highlighted[0]['id']
                        mgeo_ref_dict['name'] = 'node'
                        mgeo_ref_dict['id'] = find_id
                        Logger.log_info('Successfully find the node_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of NODE is typed")
                        return
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in link_set_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    link_set = self.getLinkSet(self.mgeo_key)
                    type = MGeoItem.LINK
                    try:
                        link_to_be_highlighted = mgeo_find.find_link(search_conditions, link_set, is_primitive=True)
                        find_id = link_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'link'
                        mgeo_ref_dict['id'] = find_id
                    except IndexError:
                        Logger.log_info("Invalid index of LINK is typed")
                        return
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in traffic_sign_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    ts_set = self.getTSSet(self.mgeo_key)
                    type = MGeoItem.TRAFFIC_SIGN
                    try:
                        ts_to_be_highlighted = mgeo_find.find_traffic_sign(search_conditions, ts_set, is_primitive=True)
                        find_id = ts_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'traffic_sign'
                        mgeo_ref_dict['id'] = find_id  
                    except IndexError:
                        Logger.log_info("Invalid index of TRAFFIC SIGN is typed")
                        return 
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in traffic_light_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    tl_set = self.getTLSet(self.mgeo_key)
                    type = MGeoItem.TRAFFIC_LIGHT
                    try:
                        tl_to_be_highlighted = mgeo_find.find_traffic_light(search_conditions, tl_set, is_primitive=True)
                        find_id = tl_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'traffic_light'
                        mgeo_ref_dict['id'] = find_id
                    except IndexError:
                        Logger.log_info("Invalid index of TRAFFIC LIGHT is typed")
                        return 
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in junction_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    junction_set = self.getJunctionSet(self.mgeo_key)
                    type = MGeoItem.JUNCTION
                    try:
                        junction_to_be_highlighted = mgeo_find.find_junction(search_conditions, junction_set, is_primitive=True)
                        find_id = junction_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'junction'
                        mgeo_ref_dict['id'] = find_id      
                    except IndexError:
                        Logger.log_info("Invalid index of JUNCTION is typed")
                        return 
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in lane_marking_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    lane_boundary_set = self.getLaneBoundarySet(self.mgeo_key)
                    type = MGeoItem.LANE_BOUNDARY
                    try:
                        lane_boundary_to_be_highlighted = mgeo_find.find_lane_boundary(search_conditions, lane_boundary_set, is_primitive=True)
                        find_id = lane_boundary_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'lane_marking'
                        mgeo_ref_dict['id'] = find_id 
                    except IndexError:
                        Logger.log_info("Invalid index of LANE MARKING is typed")
                        return 
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in single_crosswalk_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    single_crosswalk_set = self.getSingleCrosswalkSet(self.mgeo_key)
                    type = MGeoItem.SINGLECROSSWALK
                    try:
                        single_crosswalk_to_be_highlighted = mgeo_find.find_single_crosswalk(search_conditions, single_crosswalk_set, is_primitive=True)
                        find_id = single_crosswalk_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'single_crosswalk'
                        mgeo_ref_dict['id'] = find_id 
                    except IndexError:
                        Logger.log_info("Invalid index of SINGLE CROSSWALK is typed")
                        return 
                if findMGeoItemWindow.getParameters()['mgeo_item_id']['val'] in crosswalk_lst:
                    search_conditions = findMGeoItemWindow.getParameters()
                    crosswalk_set = self.getCrosswalkSet(self.mgeo_key)
                    type = MGeoItem.CROSSWALK
                    try:
                        crosswalk_to_be_highlighted = mgeo_find.find_crosswalk(search_conditions, crosswalk_set, is_primitive=True)
                        find_id = crosswalk_to_be_highlighted[0]['id'] 
                        mgeo_ref_dict['name'] = 'crosswalk'
                        mgeo_ref_dict['id'] = find_id
                    except IndexError:
                        Logger.log_info("Invalid index of CROSSWALK is typed")
                        return
                                
                else:
                    Logger.log_info("Invalid index of MGEO ITEM is typed")
                    return      
                
                self.highlight_mgeo_item(key, type, find_id)
                self.trans_point_by_id(self.find_item)
                self.updateMgeoPropWidget(self.find_item)
                Logger.log_info('Successfully find the {}_id of {} and highlighted it'.format(mgeo_ref_dict['name'], mgeo_ref_dict['id']))
                
            else:
                Logger.log_info('find cancelled by user')
                return
        
        except BaseException as e:
            Logger.log_error('find_by_mgeo_id failed (traceback below) \n{}'.format(traceback.format_exc()))
        
            
    def action_input_mgeo_id(self, item):
        """상단 Menu에서 Mgeo Id를 입력하면 해당 Item을 하이라이트한다"""
        Logger.log_trace('Called: action_input_mgeo_id')
        try:   
            if item == 'Node':
                findNodeWindow = FindNodeWindow()
                Logger.log_trace("Called: find_node")
                if findNodeWindow.exec_():
                    search_conditions = findNodeWindow.getParameters()
                    node_set = self.getNodeSet(self.mgeo_key)
                    node_to_be_highlighted = mgeo_find.find_node(search_conditions, node_set, is_primitive=False)
                    self.list_highlight1.extend(node_to_be_highlighted)
                    type = MGeoItem.NODE
                    try:
                        find_id = node_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the node_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of NODE is typed")
                        return
                else:
                    Logger.log_info('find_node cancelled by user')
                    return
                
            elif item == 'Link':
                findLinkWindow = FindLinkWindow()
                Logger.log_trace("Called: find_link")
                if findLinkWindow.exec_():
                    search_conditions = findLinkWindow.getParameters()
                    link_set = self.getLinkSet(self.mgeo_key)
                    link_to_be_highlighted = mgeo_find.find_link(search_conditions, link_set, is_primitive=False)
                    self.list_highlight1.extend(link_to_be_highlighted)
                    type = MGeoItem.LINK
                    try:
                        find_id = link_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the link_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of LINK is typed")
                        return
                else:
                    Logger.log_info('find_link cancelled by user')
                    return
                
            elif item == 'Traffic Sign':
                findTSWindow = FindTrafficSignWindow()
                Logger.log_trace("Called: find_traffic_sign")
                if findTSWindow.exec_():
                    search_conditions = findTSWindow.getParameters()
                    ts_set = self.getTSSet(self.mgeo_key)
                    ts_to_be_highlighted = mgeo_find.find_traffic_sign(search_conditions, ts_set, is_primitive=False)
                    self.list_highlight1.extend(ts_to_be_highlighted)
                    type = MGeoItem.TRAFFIC_SIGN
                    try:
                        find_id = ts_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the traffic_sign_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of TRAFFIC SIGN is typed")
                        return        
                else:
                    Logger.log_info('find_traffic_sign cancelled by user')
                    return
                
            elif item == 'Traffic Light':
                findTLWindow = FindTrafficLightWindow()
                Logger.log_trace("Called: find_traffic_light")
                if findTLWindow.exec_():
                    search_conditions = findTLWindow.getParameters()
                    tl_set = self.getTLSet(self.mgeo_key)
                    tl_to_be_highlighted = mgeo_find.find_traffic_light(search_conditions, tl_set, is_primitive=False)
                    self.list_highlight1.extend(tl_to_be_highlighted)
                    type = MGeoItem.TRAFFIC_LIGHT
                    try:
                        find_id = tl_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the traffic_light_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of TRAFFIC LIGHT is typed")
                        return       
                else:
                    Logger.log_info('find_traffic_light cancelled by user')
                    return
                
            elif item == 'Junction':
                findJunctionWindow = FindJunctionWindow()
                Logger.log_trace("Called: find_junction")
                if findJunctionWindow.exec_():
                    search_conditions = findJunctionWindow.getParameters()
                    junction_set = self.getJunctionSet(self.mgeo_key)
                    junction_to_be_highlighted = mgeo_find.find_junction(search_conditions, junction_set, is_primitive=False)
                    self.list_highlight1.extend(junction_to_be_highlighted)
                    type = MGeoItem.JUNCTION
                    try:
                        find_id = junction_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the junction_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of JUNCTION is typed")
                        return     
                else:
                    Logger.log_info('find_junction cancelled by user')
                    return

            elif item == 'Road':
               Logger.log_info ("This function should be supported after \"Creating Road\" function is done.")
               return
               
            elif item == 'Lane Marking':
                findLaneBoundaryWindow = FindLaneBoundaryWindow()
                Logger.log_trace("Called: find_lane_boundary")
                if findLaneBoundaryWindow.exec_():
                    search_conditions = findLaneBoundaryWindow.getParameters()
                    lane_boundary_set = self.getLaneBoundarySet(self.mgeo_key)
                    lane_boundary_to_be_highlighted = mgeo_find.find_lane_boundary(search_conditions, lane_boundary_set, is_primitive=False)
                    self.list_highlight1.extend(lane_boundary_to_be_highlighted)
                    type = MGeoItem.LANE_BOUNDARY
                    try:
                        find_id = lane_boundary_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the lane_marking_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of LANE MARKING is typed")
                        return     
                else:
                    Logger.log_info('find_lane_boundary cancelled by user')
                    return
                
            elif item == 'SingleCrosswalk':
                findSingleCrosswalkWindow = FindSingleCrosswalkWindow()
                Logger.log_trace("Called: find_single_crosswalk")
                if findSingleCrosswalkWindow.exec_():
                    search_conditions = findSingleCrosswalkWindow.getParameters()
                    single_crosswalk_set = self.getSingleCrosswalkSet(self.mgeo_key)
                    single_crosswalk_to_be_highlighted = mgeo_find.find_single_crosswalk(search_conditions, single_crosswalk_set, is_primitive=False)
                    self.list_highlight1.extend(single_crosswalk_to_be_highlighted)
                    type = MGeoItem.SINGLECROSSWALK
                    try:
                        find_id = single_crosswalk_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the single_crosswalk_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of SINGLE CROSSWALK is typed")
                        return     
                else:
                    Logger.log_info('find_single_crosswalk cancelled by user')
                    return
                
            elif item == 'Crosswalk':
                findCrosswalkWindow = FindCrosswalkWindow()
                Logger.log_trace("Called: find_crosswalk")
                if findCrosswalkWindow.exec_():
                    search_conditions = findCrosswalkWindow.getParameters()
                    crosswalk_set = self.getCrosswalkSet(self.mgeo_key)
                    crosswalk_to_be_highlighted = mgeo_find.find_crosswalk(search_conditions, crosswalk_set, is_primitive=False)
                    self.list_highlight1.extend(crosswalk_to_be_highlighted)
                    type = MGeoItem.CROSSWALK
                    try:
                        find_id = crosswalk_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the crosswalk_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of CROSSWALK is typed")
                        return   
                else:
                    Logger.log_info('find_crosswalk cancelled by user')
                    return
            
            elif item == "RoadPolygon":
                findRoadPolygonWindow = FindRoadPolygonWindow()
                Logger.log_trace("Called: find_road_polygon")
                if findRoadPolygonWindow.exec_():
                    search_conditions = findRoadPolygonWindow.getParameters()
                    road_polygon_set = self.getRoadPolygonSet(self.mgeo_key)
                    road_polygon_to_be_highlighted = mgeo_find.find_road_polygon(search_conditions, road_polygon_set, is_primitive=False)
                    self.list_highlight1.extend(road_polygon_to_be_highlighted)
                    type = MGeoItem.ROADPOLYGON
                    try:
                        find_id = road_polygon_to_be_highlighted[0]['id']
                        Logger.log_info('Successfully find the road_polygon_id of {}'.format(find_id))
                    except IndexError:
                        Logger.log_info("Invalid index of ROAD POLYGON is typed")
                        return
                else:
                    Logger.log_info("find_road_polygon cancelled by user")
                    return
            
            self.find_item = {'key': self.mgeo_key,'type':type,'id':find_id}
            self.trans_point_by_id(self.find_item)
           
        except BaseException as e:
            Logger.log_error('action_input_mgeo_id failed (traceback below) \n{}'.format(traceback.format_exc()))


    def highlight_mgeo_item(self, key, type, id):
        
        """Find한 Mgeo 데이터 Highlight 및 속성 Set"""
        if self.find_item is not None:
            self.list_highlight1.clear()
            self.find_item = None
        
        # key 값을 이용해서, type 과 ID 를 찾는다 
        # 'key' : map#, 'type' : NODE, 'id' : A119BS010158
        self.find_item = {'key':key,'type':type,'id':id}
        self.list_highlight1.append(self.find_item)


    def trans_point_by_id(self, item):
        """Find한 Mgeo 데이터 위치로 이동한다"""
        key = item['key']
        
        if item['type'] == MGeoItem.NODE:
            get_point = self.getNodeSet(key).nodes[item['id']].point
        elif item['type'] == MGeoItem.LINK:
            lines_point = self.getLinkSet(key).lines[item['id']].points
            get_point = lines_point[round(len(lines_point)/3)]
        elif item['type'] == MGeoItem.TRAFFIC_SIGN:
            get_point = self.getTSSet(key).signals[item['id']].point
        elif item['type'] == MGeoItem.TRAFFIC_LIGHT:
            get_point = self.getTLSet(key).signals[item['id']].point
        elif item['type'] == MGeoItem.SYNCED_TRAFFIC_LIGHT:
            get_point = self.getSyncedTLSet(key).synced_signals[item['id']].get_synced_signal_points()[0]
        elif item['type'] == MGeoItem.INTERSECTION_CONTROLLER:
            get_point = self.getIntersectionControllerSet(key).intersection_controllers[item['id']].get_intersection_controller_points()[0]
        elif item['type'] == MGeoItem.JUNCTION:
            get_point = self.getJunctionSet(key).junctions[item['id']].get_jc_node_points()[0]
        elif item['type'] == MGeoItem.ROAD:
            # opendrive road_id 값을 int에서 str로 바꾸기
            road_id = item['id']
            if len(self.getRoadSet()[road_id].ref_line) > 0:
                road_line_point = self.getRoadSet()[road_id].ref_line[0].points
            else:
                road_line_point = self.getRoadSet()[road_id].link_list_not_organized[0].points
            get_point = road_line_point[round(len(road_line_point)/3)]

        elif item['type'] == MGeoItem.LANE_NODE:
            get_point = self.getLaneNodeSet(key).nodes[item['id']].point

        elif item['type'] == MGeoItem.LANE_BOUNDARY:
            lines_point = self.getLaneBoundarySet(key).lanes[item['id']].points
            get_point = lines_point[round(len(lines_point)/3)]

        elif item['type'] == MScenarioItem.EGO_VEHICLE:
            point_xyz = self.mscenario.ego_vehicle.init_position.position
            get_point = np.array([point_xyz.x, point_xyz.y, point_xyz.z])

        elif item['type'] == MScenarioItem.SURROUNDING_VEHICLE:
            for vehicle in self.mscenario.vehicle_list:
                if str(vehicle.id) == item['id'] or vehicle.id == item['id']:
                    point_xyz = vehicle.init_position.position
                    get_point = np.array([point_xyz.x, point_xyz.y, point_xyz.z])
                    continue

        elif item['type'] == MScenarioItem.PEDESTRIAN:
            for pedestrian in self.mscenario.pedestrian_list:
                if str(pedestrian.id) == item['id'] or pedestrian.id == item['id']:
                    point_xyz = pedestrian.init_position.position
                    get_point = np.array([point_xyz.x, point_xyz.y, point_xyz.z])
                    continue

        elif item['type'] == MScenarioItem.OBSTACLE:
            for obstacle in self.mscenario.obstacle_list:
                if str(obstacle.id) == item['id'] or obstacle.id == item['id']:
                    point_xyz = obstacle.init_transform.position
                    get_point = np.array([point_xyz.x, point_xyz.y, point_xyz.z])
                    continue
        
        elif item['type'] == MGeoItem.SINGLECROSSWALK:
            # get_point = self.getCrosswalkSet().data[item['id']].points
            get_point = calculate_centroid(self.getSingleCrosswalkSet(key).data[item['id']].points)

        elif item['type'] == MGeoItem.CROSSWALK:
            get_point = self.getCrosswalkSet(key).data[item['id']].cent_point

        elif item['type'] == MGeoItem.ROADPOLYGON:
            get_point = calculate_centroid(self.getRoadPolygonSet(key).data[item['id']].points)

        elif item['type'] == MGeoItem.PARKING_SPACE:
            get_point = self.getParkingSpaceSet(key).data[item['id']].center_point

        elif item['type'] == MGeoItem.SURFACE_MARKING:
            get_point = calculate_centroid(self.getSurfaceMarkingSet(key).data[item['id']].points)


        elif item['type'] == ScenarioItem.Entities:
            for entity in self.open_scenario.scenario_object_dict.values():
                if entity.name in item['id']:
                    get_point = np.array([entity.action_type.position.x, entity.action_type.position.y, entity.action_type.position.z])
                                         
        self.xTran = - get_point[0]
        self.yTran = - get_point[1]

    
    def create_poly3_points_with_uniform_step(self, line, point_step, point_type='paramPoly3', end_condition=1):
        """
        end_condition: 링크의 마지막 포인트에 geometry가 들어가면 안 된다.
        """
        line_points_num = len(line.points)

        # 생성할 포인트 수: 1을 빼는 이유는 이미 시작 위치에 생성된 것이 하나 있기 때문
        num_points_gen = int(np.floor(line_points_num / point_step) - 1)

        # 끝 값에서 에러를 방지하기 위해 다음을 사용
        last_idx = len(line.points) - 1

        if point_type == 'poly3':
            line.geometry[0] = {'id': 0, 'method': 'poly3'}
        if point_type == 'paramPoly3':
            line.geometry[0] = {'id': 0, 'method': 'paramPoly3'}

        for i in range(num_points_gen):
            # 이번 시점에 추가할 geometry 위치
            point_idx = (i + 1) * int(point_step) # 예: 3, 6, 9, ...

            # 마지막 인덱스가 15라고 하면, 3, 6, 9, 12, 15 << 15는 포함되면 안 된다!
            # end_condition이 디폴트인 1이라고 하면, point_idx가 14일 때까지 허용된다.
            # 즉, 2, 4, 6, ... 14 이런식으로 채워졌을 때, 14가 허용이 되는 것.
            if last_idx - point_idx < end_condition:
                return
            else:
                if point_type == 'poly3':
                    if {'id': point_idx, 'method': 'poly3'} not in line.geometry:
                        line.geometry.append({'id': point_idx, 'method': 'poly3'})
                elif point_type == 'paramPoly3':
                    if {'id': point_idx, 'method': 'paramPoly3'} not in line.geometry:
                        line.geometry.append({'id': point_idx, 'method': 'paramPoly3'})


    def create_geometry_points_auto(self):
        """
        [Experimental] 현재 존재하는 모든 링크에 대해, Geometry point를 임의로 생성한다
        """
        Logger.log_trace('Called: create_geometry_points_auto')
        Logger.log_warning('Please note that the autogenerate function is an experimental one.')
        slice_offset = 1

        try: 
            edit_widget = EditAutogenerateGeometryPoints()
            edit_widget.showDialog()

            if edit_widget.result() > 0:
                type = edit_widget.type
                result = edit_widget.value
            else:
                Logger.log_info('Cancelled by user, create_geometry_points_auto cancelled.')
                return

            # OpenDRIVE 형식에 따른 선을 벡터로 분할
            if type == 'poly3':
                num_check = result.isnumeric()
                if num_check is False:
                    # 숫자만 입력하라는 팝업띄우기
                    QMessageBox.warning(self, "Data Type Error", "Only Enter Numeric Values.")
                    return
                if len(self.odr_data.roads) < 1:
                    Logger.log_warning('OpenDRIVE Conversion >> Create Roads must be performed before using the auto-generate function')
                    return
                
                point_step = float(result) - slice_offset
                for road_idx, road in self.odr_data.roads.items():
                    for link in road.ref_line:
                        if len(link.lane_mark_left) == 0:
                            Logger.log_warning('link id = {} is not have lane boundary'.format(link.idx))
                        else:
                            self.create_poly3_points_with_uniform_step(link.lane_mark_left[0], point_step, point_type=type, end_condition=1)
                self.updateMapData()
                Logger.log_info('create_geometry_points_auto completed successfully.')
            
            elif type == 'paramPoly3':
                # delete All geometry points first
                lines_list = [self.getLaneBoundarySet().lanes, self.getLinkSet(self.mgeo_key).lines]

                for lines in lines_list:
                    for line_id in lines:
                        line = lines[line_id]
                        try:
                            for i in range(len(line.geometry) - 1):
                                line.geometry.pop()
                        except BaseException as e:  
                            Logger.log_error('delete_geochange_point_all failed (traceback below) \n{}'.format(traceback.format_exc()))
                # self.updateMapData()
                # paramPoly3 requires 4 points for each vector
                if len(self.odr_data.roads) < 1:
                    Logger.log_warning('OpenDRIVE Conversion >> Create Roads must be performed before using the auto-generate function')
                    return

                point_step = 4 - slice_offset # paramPoly3 works best with 4 points
                for road_idx, road in self.odr_data.roads.items():
                    for link in road.ref_line:
                        # self.create_poly3_points_with_uniform_step(link, point_step, point_type=type)
                        if len(link.lane_mark_left) == 0:
                            Logger.log_warning('link id = {} is not have lane boundary'.format(link.idx))
                            self.create_poly3_points_with_uniform_step(link, point_step, point_type=type)
                        else:
                            self.create_poly3_points_with_uniform_step(link.lane_mark_left[0], point_step, point_type=type)
                self.updateMapData()
                Logger.log_info('create_geometry_points_auto completed successfully.')
            
            else:
                Logger.log_info('Geometry type not selected, create_geometry_points_auto cancelled.')
                return

        except BaseException as e:
                Logger.log_error('create_geometry_points_auto failed (traceback below) \n{}'.format(traceback.format_exc()))
            

    def change_all_item_id_to_string(self):
        Logger.log_trace('Called: change_all_item_id_to_string')
        try:
            error_fix.change_all_item_id_to_string(self.mgeo_planner_map)
            
            Logger.log_info('change_all_item_id_to_string performed successfully.')
            
        except BaseException as e:
            Logger.log_error('change_all_item_id_to_string failed (traceback below) \n{}'.format(traceback.format_exc()))


    def create_lane_change_links(self):
        Logger.log_trace("Called: create_lane_change_links")
        cmd_create_lane_change_link = CreateLaneChangeLinks(self)
        self.command_manager.execute(cmd_create_lane_change_link)
        Logger.log_info("Lane change links created")
        
        # self.update()


    def delete_lane_change_links(self):
        Logger.log_trace('Called: delete_lane_change_links')
        result = QMessageBox.question(self, 'MORAI Map Editor', 
                'Delete Lane Change Links', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

        if result == QMessageBox.Ok:
            cmd_delete_lane_change_links = DeleteLaneChangeLinks(self)
            self.command_manager.execute(cmd_delete_lane_change_links)
            self.reset_inner_link_point_ptr()

    def fill_points_in_all_links(self):
        Logger.log_trace("Called: fill_points_in_all_links")
        step_len = 0.5
        # result, ok = QInputDialog.getText(self, 'Fill points', 'Enter step length', QLineEdit.Normal, '0.5')
        from lib.widget.select_fill_points_window import SelectFillPointsWindow
        select_widget = SelectFillPointsWindow()
        select_widget.showDialog()
        if select_widget.result() > 0:
            points_keep = False
            try:
                result = select_widget.step_length.text()
                if select_widget.no_erasing_points.isChecked():
                    points_keep = True
                step_len = float(result)
            except BaseException as e:
                Logger.log_error('Failed to Filled points in selected links: {}'.format(e))
                return

            if len(self.mgeo_maps_dict) == 0:
                Logger.log_warning(self, "Error", "Please Load the Map")
                return
            else:
                cmd_fill_points_in_all_links = FillPointsInAllLinks(self, step_len, points_keep)
                self.command_manager.execute(cmd_fill_points_in_all_links)
                Logger.log_info("Filled points in selected links")
        else:   
            return

    
    def fill_points_in_links(self):
        Logger.log_trace("Called: fill_points_in_links")
        step_len = 0.5
        # result, ok = QInputDialog.getText(self, 'Fill points', 'Enter step length', QLineEdit.Normal, '0.5')
        from lib.widget.select_fill_points_window import SelectFillPointsWindow
        select_widget = SelectFillPointsWindow()
        select_widget.showDialog()
        if select_widget.result() > 0:
            points_keep = False
            try:
                result = select_widget.step_length.text()
                if select_widget.no_erasing_points.isChecked():
                    points_keep = True
                step_len = float(result)
            except BaseException as e:
                Logger.log_error('Failed to Filled points in selected links: {}'.format(e))
                return

            cmd_fill_points_in_links = FillPointsInLinks(self, self.list_sp, step_len, points_keep)
            self.command_manager.execute(cmd_fill_points_in_links)
            
            Logger.log_info("Filled points in selected links")
        else:   
            return

    def set_link_lane_boundary(self) :
        cmd_set_link_lane_boundary = SetLinkLaneBoundary(self, self.list_sp)
        self.command_manager.execute(cmd_set_link_lane_boundary)
    
    def set_vehicle_start_location(self):
        """Ego 차량 배치 및 경로 재 설정"""
        if self.clicked_scenario_data is None:
            Logger.log_error('Please Select the "Private" Element in Data View')
            return
        
        # Delete existing TeleportAction and RoutingAction
        for p_action in list(self.clicked_scenario_data.actions):
            if isinstance(p_action, TeleportAction):
                self.clicked_scenario_data.actions.remove(p_action)
            elif isinstance(p_action, RoutingAction):
                self.clicked_scenario_data.actions.remove(p_action)
        # Set the vehicle location
        link_id = self.inner_link_point_ptr['link'].idx
        point_idx = self.inner_link_point_ptr['point_idx']
        point = self.inner_link_point_ptr['link'].points[point_idx]

        # Set the vehicle location as LinkPosition
        new_position = LinkPosition({'id': link_id, 'index': str(point_idx)})
        self.clicked_scenario_data.actions.append(TeleportAction(new_position))

        # Set the vehicle location as WorldPosition (kept for further usage)
        # new_position = WorldPosition()
        # new_position.attrib['x'] = str(point[0])
        # new_position.attrib['y'] = str(point[1])
        # new_position.attrib['z'] = str(point[2])
        # new_position.attrib['h'] = str(calc_heading_object(self.open_scenario.mgeo, link_id, point_idx))
        # self.clicked_scenario_data.actions.append(TeleportAction(new_position))

        self.updateMgeoIdWidget()
        
    def add_waypoint(self):
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return

        if self.clicked_scenario_data is None:
            Logger.log_error('Please Select the "Private" Element in Data View')
            return
        
        create_routing_action = True
        link_id = self.inner_link_point_ptr['link'].idx
        point_idx = self.inner_link_point_ptr['point_idx']

        # Add the waypoint to the existing RoutingAction
        for p_action in self.clicked_scenario_data.actions:
            if isinstance(p_action, RoutingAction):
                create_routing_action = False
                position_obj = LinkPosition({'id': link_id, 'index': str(point_idx)})
                waypoint_obj = Waypoint({'routeStrategy': 'shortest'}, position_obj)
                p_action.action.route.waypoints.append(waypoint_obj)
        # Create the RoutingAction
        if create_routing_action:
            teleport_actions = [action for action in self.clicked_scenario_data.actions if isinstance(action, TeleportAction)]
            if teleport_actions:
                init_position = convert_to_link_position(self.open_scenario.mgeo, teleport_actions[0].position, 1)
                init_position_obj = LinkPosition({'id': init_position.id, 'index':str(init_position.index)})
                init_waypoint_obj = Waypoint({'routeStrategy':'shortest'}, init_position_obj)

                stop_position_obj = LinkPosition({'id': link_id, 'index':str(point_idx)})
                stop_waypoint_obj = Waypoint({'routeStrategy':'shortest'}, stop_position_obj)

                entity_name = self.clicked_scenario_data.entity_refs[0] + '_Route'
                route_obj = Route({'name': entity_name, 'closed':'false', 'afterCompletion': 'hide'},
                                    None, [init_waypoint_obj, stop_waypoint_obj])
                assignRouteAction_obj = AssignRouteAction(route_obj)
                routing_action_obj = RoutingAction(assignRouteAction_obj)
                self.clicked_scenario_data.actions.append(routing_action_obj)
            else:
                Logger.log_error("Initial position of the vehicle is not specified")
            
        # TODO: 만약 User 가 link를 여러개 선택해서 Stop 을 만든 다면?
        self.updateMgeoIdWidget()
        
    def delete_waypoint(self):
        if self.clicked_scenario_data is None:
            Logger.log_error('Please Select the "Private" Element in Data View')
            return

        routing_actions = [action for action in self.clicked_scenario_data.actions if isinstance(action, RoutingAction)]
        if routing_actions:
            routing_action = routing_actions[0]
            if len(routing_action.action.route.waypoints) <= 2:
                Logger.log_info("All waypoints are deleted, the routing action would be deleted")
                self.clicked_scenario_data.actions.remove(routing_action)
                self.open_scenario.gui_object_route.clear()
            else:
                routing_action.action.route.waypoints.pop()
            self.updateMgeoIdWidget()
        else:
            Logger.log_error("Waypoint doesn't exist")

    def add_vehicle(self):
        Logger.log_trace("Called: add_vehicle")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario != None:
            VehicleModelUI(self.open_scenario, self.inner_link_point_ptr).showDialog()
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please Create or Load the OpenSCENARIO Data')
        
    def add_pedestrian(self):
        Logger.log_trace("Called: add_pedestrian")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario != None:
            PedestrianModelUI(self.open_scenario, self.inner_link_point_ptr).showDialog()
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please Create or Load the OpenSCENARIO Data')
    
    def add_misc_object(self):
        Logger.log_trace("Called: add_misc_object")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario != None:
            MiscObjectModelUI(self.open_scenario, self.inner_link_point_ptr).showDialog()
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please Create or Load the OpenSCENARIO Data')
    
    def add_entity_in_tree(self):
        Logger.log_trace("Called: add_entity_in_tree")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario != None:
            AddEntityInTreeUI(self.open_scenario, self.inner_link_point_ptr).showDialog()
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please Create or Load the OpenSCENARIO Data')

    def add_event(self):
        Logger.log_trace("Called: add_event")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario != None:
            add_event = AddEventUI(self.open_scenario).showDialog()
            if add_event > 0:
                Logger.log_info("'add_event' was applied by user")
            else:
                Logger.log_info("'add_event' was canceld by user")

            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please Create or Load the OpenSCENARIO Data')    

    def add_action(self, event_element):
        Logger.log_trace("Called: add_action")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario and event_element != None:
            add_action = AddActionUI(self.open_scenario, event_element).showDialog()
            if add_action > 0:
                Logger.log_info("'add_action' was applied by user")
            else:
                Logger.log_info("'add_action' was canceld by user")
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please specify an Element that can add an Action')

    def add_condition(self, condition_group_element):
        Logger.log_trace("Called: add_condition")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario and condition_group_element != None:
            add_condition = AddConditionUI(self.open_scenario, condition_group_element).showDialog()
            if add_condition > 0:
                Logger.log_info("'add_condition' was applied by user")
            else:
                Logger.log_info("'add_condition' was canceld by user")
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please specify an Element that can add a Condition')

    def add_init_action(self, init_action_element, action_type):
        Logger.log_trace("Called: add_init_action")
        if self.osc_client_triggered == True:
            Logger.log_warning('Cannot add or edit while the program is running')
            return
        if self.open_scenario and init_action_element != None:
            add_init_action = AddInitActionUI(self.open_scenario, init_action_element, action_type).showDialog()
            if add_init_action > 0:
                Logger.log_info("'add_init_action' was applied by user")
            else:
                Logger.log_info("'add_init_action' was canceld by user")
            self.updateMgeoIdWidget()
        else:
            Logger.log_error('Please specify an Element that can add an Init Action')

    def change_origin(self):
        Logger.log_trace("Called: change_origin")
        
        #Loaded 된 origin() 을 가지고 온다 기준점
        mgeo_key = list(self.mgeo_maps_dict)[0]
        ref_origin = self.mgeo_maps_dict[mgeo_key].get_origin()
        
        #old_origin = self.mgeo_planner_map.get_origin()
        
        edit_widget = EditGeolocation(ref_origin)
        edit_widget.showDialog()
        
        for i, (key, val) in enumerate(self.mgeo_maps_dict.items()):
            if edit_widget.result() > 0:
                new_value = edit_widget.coordText
                isRetainGloabal = edit_widget.isRetainGlobalPosition
                new_origin = np.array([eval(new_value)[0], eval(new_value)[1], eval(new_value)[2]])
                new_origin_str = '[{:.9f}, {:.9f}, {:.9f}]'.format(new_origin[0], new_origin[1], new_origin[2])
                ref_origin_str = '[{:.9f}, {:.9f}, {:.9f}]'.format(ref_origin[0], ref_origin[1], ref_origin[2])
                self.mgeo_planner_map = self.mgeo_maps_dict[key]
                
                Logger.log_info('Origin of {} will be changed from {} to {}'.format(key, ref_origin_str, new_origin_str))
                edit_mgeo_planner_map.change_origin(self.mgeo_planner_map, new_origin, isRetainGloabal)
                self.mgeo_rtree[mgeo_key] = MgeoRTree(self.mgeo_maps_dict[mgeo_key])

            self.updateMapData()
            self.command_manager.clear()
        Logger.log_info('change_origin finished')

        # new_value, okPressed = QInputDialog.getText(self, "Change Origin", "Enter New Origin", QLineEdit.Normal, str('{}, {}, {}'.format(old_origin[0], old_origin[1], old_origin[2])))
        
        # if okPressed and new_value != '':
        #     new_origin = np.array([eval(new_value)[0], eval(new_value)[1], eval(new_value)[2]])
        #     new_origin_str = '[{:.6f}, {:.6f}, {:.6f}]'.format(new_origin[0], new_origin[1], new_origin[2])
        #     old_origin_str = '[{:.6f}, {:.6f}, {:.6f}]'.format(old_origin[0], old_origin[1], old_origin[2])
        
        #     Logger.log_info('Origin will be changed from {} to {}'.format(old_origin_str, new_origin_str))

        #     edit_mgeo_planner_map.change_origin(self.mgeo_planner_map, new_origin, retain_global_position=True)

        #     self.updateMapData()
        #     Logger.log_info('change_origin finished')
    
    def changeWorldProjection(self):
        Logger.log_trace("Called: change_world_projection")
        # current_projection_info = self.mgeo_planner_map.global_coordinate_system
        mgeo_key = list(self.mgeo_maps_dict)[0]
        current_projection_info = self.mgeo_maps_dict[mgeo_key].global_coordinate_system
        edit_widget = EditChangeWorldProjection(current_projection_info)
        edit_widget.showDialog()

        if edit_widget.result() > 0:
            # edit_mgeo_planner_map.change_world_projection(self.mgeo_planner_map, edit_widget.proj4String)
            edit_mgeo_planner_map.change_world_projection(self.mgeo_maps_dict[mgeo_key], edit_widget.proj4String)
            self.mgeo_rtree[mgeo_key] = MgeoRTree(self.mgeo_maps_dict[mgeo_key])
            self.updateMapData()
            self.command_manager.clear()
            Logger.log_info('change_world_projection finished')

    def show_not_supported_warning(self):
        Logger.log_trace('Called: show_not_supported_warning') 
        QMessageBox.warning(self, "Evaluation Version Notification",
            "Not supported in the evaluation version.\nFull features will be made available in the final release version.")


    def change_region_localization(self):
        Logger.log_trace('Called: change_region_localization') 
        try:
            edit_widget = EditChangeRegionLocalization(self.mgeo_planner_map)
            edit_widget.showDialog()

            for i, (key, val) in enumerate(self.mgeo_maps_dict.items()):
                if edit_widget.result() > 0:
                    current_map = self.mgeo_maps_dict[key]
                    current_map.traffic_dir = edit_widget.traffic_dir
                    current_map.country = edit_widget.country
                    current_map.road_type = edit_widget.road_type
                    current_map.road_type_def = edit_widget.road_type_def

                    Logger.log_info('change_region_localization completed successfully.')
                else:
                    Logger.log_info('change_region_localization cancelled by user')

        except BaseException as e:
            Logger.log_error('change_region_localization failed (traceback below) \n{}'.format(traceback.format_exc()))

        
    def open_user_manual(self, user_manual_url):
        Logger.log_trace('Called: open_user_manual')
        try:
            webbrowser.open(user_manual_url)
            Logger.log_info('The user manual will open in your web browser.')
        except BaseException as e:
            Logger.log_error('open_user_manual failed (traceback below) \n{}'.format(traceback.format_exc()))


    def open_about(self, window_title, page_title, contents):
        Logger.log_trace('Called: open_about')
        # try:
        #     about_dialog = AboutDialog(window_title, page_title, contents)
        # except BaseException as e:
        #     Logger.log_error('open_about failed (traceback below)\n{}'.format(traceback.format_exc()))

    # LaneNode 연결하면 시작/끝 점만 있어서 직선으로 연결됨
    # 도로나 차선 mesh를 만들기 위해서 곡선으로
    # LaneBoundary Line안에 points 를 채워 넣는 함수
    def add_line_points(self):
        if self.input_line_points is False and len(self.point_list) > 0:
            try:
                if self.sp['type'] == MGeoItem.LANE_BOUNDARY:
                    line = self.getLaneBoundarySet().lanes[self.sp['id']]
                else:
                    line = self.getLinkSet(self.mgeo_key).lines[self.sp['id']]
                origin_points = line.points
                new_points = []
                # z0 ---- z1 4
                z0 = origin_points[0][2]
                z1 = origin_points[-1][2]
                new_points.append(origin_points[0])
                for i in range(len(self.point_list)):
                    z = z0 + ((z1-z0)/(len(self.point_list)+1))*(i+1)
                    new_points.append([self.point_list[i][0], self.point_list[i][1], z])
                new_points.append(origin_points[-1])
                line.points = np.array(new_points)
            except:
                pass
            self.point_list.clear()
            self.updateMapData()

    def move_point(self):
        if self.input_line_points is False and len(self.point_list) == 1:
            try:
                node = self.getLaneNodeSet().nodes[self.sp['id']]
                origin_point = node.point
                new_point = np.array([self.point_list[0][0], self.point_list[0][1], node.point[2]])
                node.point = new_point
                from_links = node.from_links
                to_links = node.to_links
                for from_link in from_links:
                    from_link.points[-1] = new_point
                for to_link in to_links:
                    to_link.points[0] = new_point

            except:
                pass
            self.point_list.clear()
            self.updateMapData()

    def add_new_mgeo_item(self, mgeotype):
        Logger.log_trace('Called: add_new_mgeo_item {} '.format(mgeotype))
        
        if len(self.point_list) == 3:
            # 신호등은 road에서 2.5m 정도 위로 추가
            cmd_add_new_mgeo_item = AddNewMgeoItem(self, mgeotype, self.point_list, self.xlim, self.ylim)
            self.command_manager.execute(cmd_add_new_mgeo_item)
            
            self.point_list = []
        else:
            Logger.log_warning('Select only one point to create a {}'.format(mgeotype))

    def append_mgeo_item(self, mgeotype):
        Logger.log_trace('Called: append_mgeo_item {} '.format(mgeotype))

        if len(self.list_sp) > 1:
            signal_set = self.getTLSet(self.mgeo_key)
            synced_light_set = self.getSyncedTLSet(self.mgeo_key)
            cmd_append_ps_lights = EditSyncedTrafficLight(self, synced_light_set)
            self.command_manager.execute(cmd_append_ps_lights)
        else:
            Logger.log_warning('Select more than one traffic light to create a {}'.format(mgeotype))

    def get_simulation_point(self):
        Logger.log_trace('Called: get_simulation_point')
        try:
            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return
        
            # 이 위치에 새로운 geometry point를 입력한다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']
                        
            if point_idx + 1 > len(link.points) - 1:
                # 마지막 index 보다 크면 (접근 불가인 경우)
                pt1 = link.points[point_idx - 1]
                pt2 = link.points[point_idx]
            else:
                pt1 = link.points[point_idx]
                pt2 = link.points[point_idx + 1]
                
            # 시뮬레이터의 좌표계로 변환
            sim_pt1 = np.array([-1 * pt1[0], pt1[2], -1 * pt1[1]])
            sim_pt2 = np.array([-1 * pt2[0], pt2[2], -1 * pt2[1]])

            vect = sim_pt2 - sim_pt1            
            vect2 = [1, 0, 0] # heading 값 계산을 위한 기준 벡터

            if np.linalg.norm(vect, ord=2) < 1e-2: # 두 포인트가 너무 가까우면, 유효하지 않으므로 다른 점을 선택하라고 한다
                Logger.log_error('Distance between the two adjecent points are to small. Choose another point.')
                return

            # 단위벡터 계산
            unit_vector_1 = vect / np.linalg.norm(vect)
            unit_vector_2 = vect2 / np.linalg.norm(vect2)

            heading = np.arctan2(unit_vector_1[0] * unit_vector_2[2] - unit_vector_1[2] * unit_vector_2[0], unit_vector_1[0] * unit_vector_2[0] + unit_vector_1[2] * unit_vector_2[2]) * 180.0 / np.pi

            # 시뮬레이터와 회전 기준축이 다르기 때문에 90을 더해서 값 조정
            sim_heading = heading + 90

            if sim_heading > 360:
                Logger.log_warning('sim_heading > 360 deg. (sim_heading: {:.2f} -> -360 applied)'.format(sim_heading))
                sim_heading -= 360
            
            pitch = 0
            yaw = sim_heading 
            roll = 0
            
            msg_pos = '"pos":{{"x":{:.6f}, "y":{:.6f}, "z":{:.6f}}},'.format(sim_pt1[0], sim_pt1[1], sim_pt1[2])
            msg_rot = '"rot":{{"pitch":{:.6f}, "yaw":{:.6f}, "roll":{:.6f}}}'.format(pitch, yaw, roll)

            Logger.log_info('get_simulation_point string:\n{}\n{}'.format(msg_pos, msg_rot))
        
        except BaseException as e:
            Logger.log_error('get_simulation_point failed (traceback below) \n{}'.format(traceback.format_exc()))


    def open_export_csv_option(self):
        edit_widget = ExportCSVWidget()
        return edit_widget
        # edit_widget.showDialog()
        # if edit_widget.result() > 0:
        #     return edit_widget.isMergeAlldata, edit_widget.isLink, edit_widget.isLaneMarking
        # else:
        #     return None

    # [210705] ngii ver2에 대해 로드 아이디, 링크 - 차선 연결 오류 찾기
    def fix_road_id_assignments(self):
        Logger.log_trace('Called: fix_road_id_assignments')
        try:
            first_link = list(self.mgeo_planner_map.link_set.lines.keys())[0]
            if self.mgeo_planner_map.link_set.lines[first_link].link_type_def == 'ngii_model2':
                link_error = set_link_lane_mark.set_road_id_from_link_change(self)
                for link in link_error:
                    sp_dict = {'type': MGeoItem.LINK, 'id': link}
                    self.list_error.append(sp_dict)
            else:
                QMessageBox.warning(self, "Type Error", "Only available on ngii_model2")
            Logger.log_info('Road ID fix complete')
        except BaseException as e:
            Logger.log_error('fix_road_id_assignments failed (traceback below) \n{}'.format(traceback.format_exc()))


    def find_missing_lane_marking(self):
        Logger.log_trace('Called: find_missing_lane_marking')
        try:
            first_link = list(self.mgeo_planner_map.link_set.lines.keys())[0]
            # if self.mgeo_planner_map.link_set.lines[first_link].link_type_def == 'ngii_model2':
            link_error = set_link_lane_mark.find_error_lane_mark(self)
            for link in link_error:
                sp_dict = {'type': MGeoItem.LINK, 'id': link}
                self.list_error.append(sp_dict)
            # else:
            #     QMessageBox.warning(self, "Type Error", "Only available on ngii_model2")
        except BaseException as e:
            Logger.log_error('find_missing_lane_marking failed (traceback below) \n{}'.format(traceback.format_exc()))


    def create_path_from_selected_links(self):
        Logger.log_trace('Called: create_path_from_selected_links')
        path_obj = Path(id=1)

        # User가 선택한 순서대로, link_path 리스트에 link object들을 추가한다.
        for num_link in range(len(self.list_sp)):
            path_obj.link_path.append(self.getLinkSet(self.mgeo_key).lines[self.list_sp[num_link]['id']])
        
        # User가 제일 처음 선택한 링크의
        # 시작 포인트는 선택한 "첫 번째 노드의 맨 첫 번째 포인트"
        # 마지막 포인트는 선택한 "마지막 노드의 마지막 포인트"
        path_obj.start_point['point'] = self.getLinkSet(self.mgeo_key).lines[self.list_sp[0]['id']].from_node.point
        path_obj.start_point['link'] = self.getLinkSet(self.mgeo_key).lines[self.list_sp[0]['id']]

        path_obj.end_point['point'] = self.getLinkSet(self.mgeo_key).lines[self.list_sp[-1]['id']].to_node.point
        path_obj.end_point['link'] = self.getLinkSet(self.mgeo_key).lines[self.list_sp[-1]['id']]

        #만약 두 링크들끼리 이어져 있으면, self.path_obj을 리턴한다.
        link_connection_validation_count = 0
        for link_idx in range(len(path_obj.link_path)-1):    
            if path_obj.link_path[link_idx] in path_obj.link_path[link_idx+1].get_to_links() or path_obj.link_path[link_idx] in path_obj.link_path[link_idx+1].get_from_links():
                link_connection_validation_count += 1
        
        # link_connection_validation_count가 총 link 숫자보다 1개가 적으면, route을 성공적으로 build 할 수 있다.
        if link_connection_validation_count == len(path_obj.link_path) - 1:
            Logger.log_info('route built successfully')
        
        else:
            Logger.log_error('create_path_from_selected_links failed')
        
        self.path_obj_lst.append(path_obj)

        # 링크들을 이어서 UI 위에서 그려줍니다.
        for link in self.list_sp:
            self.list_highlight2.append(link)
    
    
    def export_path_to_csv(self, output_option, file_name):
        Logger.log_trace('Called: export_path_to_csv')

        if output_option == 'link_list':
            f = open(file_name,"w",newline="")
            writer = csv.writer(f)
            header = ['link_idx','link_from_node','link_to_node']
            writer.writerow(header)
            for path_obj in self.path_obj_lst:
                for link in path_obj.link_path:
                    writer.writerow([link.idx, link.from_node.idx, link.to_node.idx])    
            f.close()

        elif output_option == 'list_point_enu': # output_option = 'point_list
            f = open(file_name,"w",newline="")
            writer = csv.writer(f)
            
            header = ['East','North','Up']
            writer.writerow(header)
            
            # TODO(tyshin): 두 연속된 링크 사이에서 겹치는 vertex는 skip하도록 하기
            for path_obj in self.path_obj_lst:
                for link in path_obj.link_path:
                    for point in link.points:
                        writer.writerow([point[0], point[1], point[2]])
            f.close()
          
        elif output_option == 'list_point_ll': # output_option = 'point_list
            raise NotImplementedError('Not implemented yet')     
    
    
    def set_start_point_from_node(self):
        Logger.log_trace('Called: set_start_point_from_node')
        path_obj = Path(id=2)
        self.scenario_start_point = self.sp['id']
        path_obj.start_point['start_point'] = self.getNodeSet(self.mgeo_key).nodes[self.scenario_start_point].point   
        self.path_obj_lst.append(path_obj)


    def set_end_point_from_node(self):
        Logger.log_trace('Called: set_end_point_from_node')
        path_obj = Path(id=3)
        self.scenario_end_point = self.sp['id']
        path_obj.end_point['end_point'] = self.getNodeSet(self.mgeo_key).nodes[self.scenario_end_point].point
        self.path_obj_lst.append(path_obj)
    
    
    def set_stop_point_from_node(self):
        Logger.log_trace('Called: set_stop_point_from_node')
        path_obj = Path(id=4)
        self.scenario_stop_point.append(self.sp['id'])
        for stop_point in self.scenario_stop_point:
            path_obj.stop_point['stop_point'] = self.getNodeSet(self.mgeo_key).nodes[stop_point].point
            self.path_obj_lst.append(path_obj)


    def create_path_from_start_and_end_point(self):
        Logger.log_trace('Called: create_path_from_start_and_end_point')
        self.reset_path()
        try:
            dijkstra_obj = Dijkstra(self.getNodeSet(self.mgeo_key).nodes, self.getLinkSet(self.mgeo_key).lines)
            result, path = dijkstra_obj.find_shortest_path(self.scenario_start_point, self.scenario_end_point)       
            for link_id in path['link_path']:
                path_obj = Path(id=5)
                sp_dict = {'type': MGeoItem.LINK, 'id': link_id}
                self.list_highlight2.append(sp_dict)
                path_obj.link_path.append(self.getLinkSet(self.mgeo_key).lines[link_id])
                self.path_obj_lst.append(path_obj)
        except BaseException as e:
            Logger.log_error('create_path_from_start_and_end_point failed (traceback below) \n{}'.format(traceback.format_exc()))
    

    def create_path_from_start_and_stop_and_end_point(self):
        Logger.log_trace('Called: create_path_from_start_and_stop_and_end_point')
        self.reset_path()
        try:
            if self.scenario_start_point is not None and self.scenario_end_point is not None:
                # stop_point가 1개인 경우
                if len(self.scenario_stop_point) == 1:
                    start_point = self.scenario_start_point
                    stop_point =  self.scenario_stop_point[0]
                    end_point = self.scenario_end_point

                    dijkstra_obj_from_start_point_to_stop_point = Dijkstra(self.getNodeSet(self.mgeo_key).nodes, self.getLinkSet(self.mgeo_key).lines)
                    result, path_from_start_point_to_stop_point = dijkstra_obj_from_start_point_to_stop_point.find_shortest_path(start_point, stop_point)
                    for link_id in path_from_start_point_to_stop_point['link_path']:
                        path_obj = Path(id=6)
                        sp_dict = {'type': MGeoItem.LINK, 'id': link_id}
                        self.list_highlight2.append(sp_dict)
                        path_obj.link_path.append(self.getLinkSet(self.mgeo_key).lines[link_id])
                        self.path_obj_lst.append(path_obj)
                    dijkstra_obj_from_stop_point_to_end_point = Dijkstra(self.getNodeSet(self.mgeo_key).nodes, self.getLinkSet(self.mgeo_key).lines)
                    result, path_from_stop_point_to_end_point = dijkstra_obj_from_stop_point_to_end_point.find_shortest_path(stop_point, end_point)
                    for link_id in path_from_stop_point_to_end_point['link_path']:
                        path_obj = Path(id=7)
                        sp_dict = {'type': MGeoItem.LINK, 'id': link_id}
                        self.list_highlight2.append(sp_dict)
                        path_obj.link_path.append(self.getLinkSet(self.mgeo_key).lines[link_id])
                        self.path_obj_lst.append(path_obj)
                else:
                    multiple_location_points = []
                    multiple_location_points.append(self.scenario_start_point)
                    multiple_location_points.extend(self.scenario_stop_point)
                    multiple_location_points.append(self.scenario_end_point)

                    for link_num in range(len(self.scenario_stop_point)+1):
                        start_point = multiple_location_points[link_num]
                        end_point = multiple_location_points[link_num + 1]
                        dijkstra_obj = Dijkstra(self.getNodeSet(self.mgeo_key).nodes, self.getLinkSet(self.mgeo_key).lines)
                        result, path = dijkstra_obj.find_shortest_path(start_point, end_point)
                        for link_id in path['link_path']:
                            path_obj = Path(id=8)
                            sp_dict = {'type': MGeoItem.LINK, 'id': link_id}
                            self.list_highlight2.append(sp_dict)
                            path_obj.link_path.append(self.getLinkSet(self.mgeo_key).lines[link_id])
                            self.path_obj_lst.append(path_obj)
        except BaseException as e:
            Logger.log_error('create_path_from_start_and_stop_and_end_point failed (traceback below) \n{}'.format(traceback.format_exc()))
    
    
    def reset_all(self):
        Logger.log_trace('Called: reset_all')
        self.path_obj_lst.clear()
        self.list_sp.clear()
        self.list_highlight2.clear()
        self.scenario_start_point = None
        self.scenario_end_point = None
        self.scenario_stop_point.clear()


    def reset_path(self):
        Logger.log_trace('Called: reset_path')
        self.path_obj_lst.clear()
        self.list_sp.clear()
        self.list_highlight2.clear()

      
    def reset_start_point(self):
        Logger.log_trace('Called: reset_start_point')
        self.scenario_start_point = None

    
    def reset_end_point(self):
        Logger.log_trace('Called: reset_end_point')
        self.scenario_end_point = None


    def reset_stop_point(self):
        Logger.log_trace('Called: reset_stop_point')
        self.scenario_stop_point = []


    def create_sync_light_set(self):
        cmd_create_sync_light_set = CreateSycLightSet(self, self.list_sp)
        self.command_manager.execute(cmd_create_sync_light_set)

    # [sjhan] 교차로 신호등 전체 선택해서
    # Synced Traffic Light Set 이랑 Intersection Controller Set 만드는 함수
    def temp_create_syncTL_IntTL(self):
        cmd_create_syncTL_IntTL = CreateSyncedTLIntTL(self, self.list_sp)
        self.command_manager.execute(cmd_create_syncTL_IntTL)

    def action_create_intersection(self):
        cmd_create_intersection = CreateIntersection(self, self.list_sp)
        self.command_manager.execute(cmd_create_intersection)
        
        self.list_sp.clear()
    
    def action_make_intersecion_tl(self):
        '''
        intscn_tl_data = IntersectionInfo()
        intersection_ctrlr_builder = IntersectionControllerSetBuilder(self.getTLSet(self.mgeo_key), self.getLinkSet(self.mgeo_key), intscn_tl_data)
        intersection_ctrlr_builder.build_synced_signal_set(self.getSyncedTLSet())
        intersection_ctrlr_builder.build_controller(self.getIntersectionControllerSet())
        intersection_state_builder  = IntersectionStateBuilder(self.getIntersectionControllerSet(), intscn_tl_data, self.getLinkSet(self.mgeo_key))
        abnormal_intscn_list, self.mgeo_planner_map.intersection_state_list = intersection_state_builder.build()
        Logger.log_info('Called: action_make_intersection_tl')
        for abnormal in abnormal_intscn_list:
            Logger.log_warning(f'Check Intersection : {abnormal}')
        '''
        #intersection_ctrlr_builder = IntersectionControllerSetBuilder(self.getTLSet(self.mgeo_key))
        #intersection_ctrlr_builder.set_highlight_traffic_lights(self.list_sp)
        cmd_create_syncTL_IntTL = CreateSyncIntscnTLSet(self, self.list_sp)
        self.command_manager.execute(cmd_create_syncTL_IntTL)

        self.updateMapData()
        self.updateMgeoIdWidget()   

    def check_intersection_vicinity(self, act_clr): # change to - check_intersection_vicinity
        Logger.log_trace('Called: check_intersection_vicinity')
        try:
            if self.getLinkSet(self.mgeo_key) is None or len(self.getLinkSet(self.mgeo_key).lines) < 1 :
                QMessageBox.warning(self, "Warning", "There is no link data.")
                return
            self.random_links = error_fix.check_intersection_vicinity(self.getTLSet(self.mgeo_key).signals, self.getLinkSet(self.mgeo_key).lines)
            for link in self.random_links:    
                sp_dict = {'type': MGeoItem.LINK, 'id': link.idx}
                self.list_error.append(sp_dict)
            link_str = '['
            for link in self.random_links:
                link_str += '{}, '.format(link.idx)
            link_str += ']'
            
                # dangling_nodes에 node 유/무에 따라 (delete_dangling_nodes) menu action enable
            if self.random_links is None or self.random_links == []:
                act_clr.setDisabled(True)
            else:
                act_clr.setDisabled(False)
            Logger.log_info('Found wrongly connected links: {}'.format(link_str))
        except BaseException as e:
            Logger.log_error('check_intersection_vicinity failed (traceback below) \n{}'.format(traceback.format_exc()))    

    def set_max_speed_link(self):
        Logger.log_trace('Called: set_max_speed_link')
        try: 
            edit_widget = EditSetMaxSpeedLink(self.mgeo_maps_dict)
            edit_widget.showDialog()

            if edit_widget.result() > 0:
                type = edit_widget.type
                result = edit_widget.value
            else:
                Logger.log_info('value is not entered properly, set_max_speed_link cancelled.')
                return  
            
            if type in ['all_links', 'empty_links']:
                num_check = result.isnumeric()
                if num_check is False:
                    QMessageBox.warning(self, "Data Type Error", "Only Enter Numeric Values.")
                    return
                
                cmd_set_max_speed_link = SetMaxSpeedLink(self, result, type)
                self.command_manager.execute(cmd_set_max_speed_link)

                Logger.log_info('set_max_speed completed successfully.')
            
            else:
                Logger.log_info('the link of max speed to be filled is not selected, set_max_speed_link cancelled.')
                return

        except BaseException as e:
                Logger.log_error('set_max_speed_link failed (traceback below) \n{}'.format(traceback.format_exc()))

    def drag_plot(self):

        if len(self.node_list) == 0:
            return
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_FRONT_AND_BACK)
        glEnable(GL_BLEND)
        glBegin(GL_POLYGON)
        # MS-405 위치에 따라서 드래그 박스가 이상하게 설정됨
        z = 0
        glColor4f(0, 0, 0, 0)
        glVertex3f(self.xlim[0], self.ylim[0], z)
        glVertex3f(self.xlim[0], self.ylim[1], z)
        glVertex3f(self.xlim[1], self.ylim[1], z)
        glVertex3f(self.xlim[1], self.ylim[0], z)
        glEnd()
        #glFlush()

        winX = self.drag_start.x()
        winY = self.viewport[3] - self.drag_start.y()
        winZ = glReadPixels(winX, int(winY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        drag_start = gluUnProject(winX, winY, winZ, self.modelview, self.projection, self.viewport)

        winX = self.lastPos.x()
        winY = self.viewport[3] - self.lastPos.y()
        winZ = glReadPixels(winX, int(winY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        drag_end = gluUnProject(winX, winY, winZ, self.modelview, self.projection, self.viewport)

        left_winX = min(self.drag_start.x(), self.lastPos.x())
        right_winX = max(self.drag_start.x(), self.lastPos.x())
        top_winY = max(self.viewport[3] - self.drag_start.y(), self.viewport[3] - self.lastPos.y())
        bottom_winY = min(self.viewport[3] - self.drag_start.y(), self.viewport[3] - self.lastPos.y())

        #left top
        winX = left_winX
        winY = top_winY

        near_plane_point = gluUnProject(winX, winY, 0.0, self.modelview, self.projection, self.viewport)
        far_plane_point = gluUnProject(winX, winY, 1.0, self.modelview, self.projection, self.viewport)
        point_vector = np.array(far_plane_point) - np.array(near_plane_point)
        point_vector = point_vector / np.linalg.norm(point_vector)
        point_left_top = np.array(near_plane_point) + point_vector
        point_left_top_far = np.array(far_plane_point)
        left_top_segment = [point_left_top_far, point_left_top]

        #left bottom
        winX = left_winX
        winY = bottom_winY

        near_plane_point = gluUnProject(winX, winY, 0.0, self.modelview, self.projection, self.viewport)
        far_plane_point = gluUnProject(winX, winY, 1.0, self.modelview, self.projection, self.viewport)
        point_vector = np.array(far_plane_point) - np.array(near_plane_point)
        point_vector = point_vector / np.linalg.norm(point_vector)
        point_left_bottom = np.array(near_plane_point) + point_vector
        point_left_bottom_far = np.array(far_plane_point)
        left_bottom_segment = [point_left_bottom_far, point_left_bottom]

        #right_bottom
        winX = right_winX
        winY = bottom_winY

        near_plane_point = gluUnProject(winX, winY, 0.0, self.modelview, self.projection, self.viewport)
        far_plane_point = gluUnProject(winX, winY, 1.0, self.modelview, self.projection, self.viewport)
        point_vector = np.array(far_plane_point) - np.array(near_plane_point)
        point_vector = point_vector / np.linalg.norm(point_vector)
        point_right_bottom = np.array(near_plane_point) + point_vector
        point_right_bottom_far = np.array(far_plane_point)
        right_bottom_segment = [point_right_bottom_far, point_right_bottom]

        #right_top
        winX = right_winX
        winY = top_winY

        near_plane_point = gluUnProject(winX, winY, 0.0, self.modelview, self.projection, self.viewport)
        far_plane_point = gluUnProject(winX, winY, 1.0, self.modelview, self.projection, self.viewport)
        point_vector = np.array(far_plane_point) - np.array(near_plane_point)
        point_vector = point_vector / np.linalg.norm(point_vector)
        point_right_top = np.array(near_plane_point) + point_vector
        point_right_top_far = np.array(far_plane_point)
        right_top_segment = [point_right_top_far, point_right_top]

        face_top = [point_right_top, point_right_top_far, point_left_top_far]
        face_top_norm =np.cross((face_top[1] - face_top[0]), (face_top[2] - face_top[0]))
        face_top_const = -np.inner(face_top_norm, face_top[0])
        top_plane = [face_top_norm, face_top_const]

        face_left = [point_left_top, point_left_top_far, point_left_bottom_far]
        face_left_norm =np.cross((face_left[1] - face_left[0]), (face_left[2] - face_left[0]))
        face_left_const = -np.inner(face_left_norm, face_left[0])
        left_plane = [face_left_norm, face_left_const]

        face_bottom = [point_left_bottom, point_left_bottom_far, point_right_bottom_far]
        face_bottom_norm =np.cross((face_bottom[1] - face_bottom[0]), (face_bottom[2] - face_bottom[0]))
        face_bottom_const = -np.inner(face_bottom_norm, face_bottom[0])
        bottom_plane = [face_bottom_norm, face_bottom_const]

        face_right = [point_right_bottom, point_right_bottom_far, point_right_top_far]
        face_right_norm =np.cross((face_right[1] - face_right[0]), (face_right[2] - face_right[0]))
        face_right_const = -np.inner(face_right_norm, face_right[0])
        right_plane = [face_right_norm, face_right_const]

        select_planes = [top_plane, left_plane, bottom_plane, right_plane]
        select_segments = [left_top_segment, left_bottom_segment, right_bottom_segment, right_top_segment]

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_FRONT_AND_BACK)
        glEnable(GL_BLEND)
        glBegin(GL_POLYGON)
        color = self.config['STYLE']['SELECT']['COLOR']
        glColor4f(color[0], color[1], color[2], 0.2)

        glVertex3f(point_left_top[0], point_left_top[1], point_left_top[2])
        glVertex3f(point_left_bottom[0], point_left_bottom[1], point_left_bottom[2])
        glVertex3f(point_right_bottom[0], point_right_bottom[1], point_right_bottom[2])
        glVertex3f(point_right_top[0], point_right_top[1], point_right_top[2])
        glEnd()
        # glFlush()
        glDisable(GL_BLEND)

        xlim = [drag_start[0], drag_end[0]]
        xlim.sort()
        ylim = [drag_start[1], drag_end[1]]
        ylim.sort()

        # Ctrl 누르고 계속 드래그하면 mgeo 선택하는 것 누적
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            self.list_sp = self.list_sp
        else:
            self.list_sp.clear()
        
        key = self.mgeo_key
        if key in self.mgeo_maps_dict:
            if self.check_item == key or self.check_item is None:
                for data_id in MGeoItem:
                    self.drag_select_items(data_id, xlim, ylim)
                
                for data_id in ScenarioItem:
                    self.drag_select_items(data_id, xlim, ylim)
            else:
                if self.check_item in list(MGeoItem.__members__):
                    self.drag_select_items_by_planes(MGeoItem[self.check_item], select_planes, np.array(select_segments))


    def drag_select_items_by_planes(self, item_type, select_planes, select_segments):        

        key = self.mgeo_key
        data_set = { 
            MGeoItem.NODE: self.getNodeSet(key).nodes, 
            MGeoItem.LINK: self.getLinkSet(key).lines, 
            MGeoItem.TRAFFIC_LIGHT: self.getTLSet(key).signals, 
            MGeoItem.TRAFFIC_SIGN: self.getTSSet(key).signals, 
            MGeoItem.JUNCTION: self.getJunctionSet(key).junctions,
            MGeoItem.ROAD: self.getRoadSet(),
            MGeoItem.SYNCED_TRAFFIC_LIGHT: self.getSyncedTLSet(key).synced_signals if self.getSyncedTLSet(key) is not None else None,
            MGeoItem.INTERSECTION_CONTROLLER: self.getIntersectionControllerSet(key).intersection_controllers if self.getIntersectionControllerSet(key) is not None else None,
            MGeoItem.LANE_BOUNDARY: self.getLaneBoundarySet(key).lanes, 
            MGeoItem.LANE_NODE: self.getLaneNodeSet(key).nodes,
            MGeoItem.SINGLECROSSWALK: self.getSingleCrosswalkSet(key).data,
            MGeoItem.CROSSWALK: self.getCrosswalkSet(key).data,
            MGeoItem.ROADPOLYGON: self.getRoadPolygonSet(key).data,
            MGeoItem.PARKING_SPACE: self.getParkingSpaceSet(key).data,
            MGeoItem.SURFACE_MARKING: self.getSurfaceMarkingSet(key).data,
        }

        if item_type not in data_set:
            return

        items = data_set[item_type]
        select_item_type = item_type

        if item_type == MGeoItem.LINK:
            if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                flag_shift = True
                items = data_set[MGeoItem.LINK]
            else:
                flag_shift = False
                items = data_set[MGeoItem.NODE]
                select_item_type = MGeoItem.NODE
        elif item_type == MGeoItem.LANE_BOUNDARY:
            if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                flag_shift = True
                items = data_set[MGeoItem.LANE_BOUNDARY]
            else:
                flag_shift = False
                items = data_set[MGeoItem.LANE_NODE]
                select_item_type = MGeoItem.LANE_NODE


        itsc_list = self.mgeo_rtree[self.mgeo_key].intersection_by_perspective_planes(select_item_type, select_segments, select_planes)

        for sp_item in itsc_list:
            item_id = sp_item['id']
            if item_id not in items :
                continue
            
            # link 또는 lane_mark 선택 시
            if item_type == MGeoItem.LINK or item_type == MGeoItem.LANE_BOUNDARY :
                if flag_shift:
                    if self.is_bbox_item_inside_planes(items[item_id], select_planes) :
                        sp_dict = {'type': item_type, 'id': items[item_id].idx}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                else :
                    if self.is_point_item_inside_planes(items[item_id], select_planes) :
                        for link_item in items[item_id].from_links:
                            sp_dict = {'type': item_type, 'id': link_item.idx}
                            if sp_dict not in self.list_sp:
                                self.list_sp.append(sp_dict)
                        for link_item in items[item_id].to_links:
                            sp_dict = {'type': item_type, 'id': link_item.idx}
                            if sp_dict not in self.list_sp:
                                self.list_sp.append(sp_dict)

            
            elif item_type == MGeoItem.JUNCTION:
                jnodes = items[item_id].jc_nodes
                for jnode in jnodes:
                    if self.is_point_item_inside_planes(jnode, select_planes) :
                        sp_dict = {'type': item_type, 'id': item_id}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                        break
                        
            elif item_type == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                stls = items[item_id].signal_set.to_list()
                for stl in stls:
                    if self.is_point_item_inside_planes(stl, select_planes) :
                        sp_dict = {'type': item_type, 'id': item_id}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                        break
            
            elif item_type == MGeoItem.INTERSECTION_CONTROLLER:
                ics = items[item_id].get_signal_list()
                for ic in ics:
                    if self.is_point_item_inside_planes(ic, select_planes) :
                        sp_dict = {'type': item_type, 'id': item_id}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                        break
                           
            elif item_type == MGeoItem.CROSSWALK:
                for scw_item in items[item_id].single_crosswalk_list:
                    if self.is_bbox_item_inside_planes(scw_item, select_planes) :
                        sp_dict = {'type': item_type, 'id': item_id}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                        break
            
            elif item_type == MGeoItem.ROAD:
                rds = items[item_id]
            
            elif item_type in [MGeoItem.SINGLECROSSWALK, MGeoItem.ROADPOLYGON, MGeoItem.PARKING_SPACE, MGeoItem.SURFACE_MARKING]:
                sp_dict = {'type': item_type, 'id': item_id}
                if sp_dict not in self.list_sp:
                    if self.is_bbox_item_inside_planes(items[item_id], select_planes) :
                        self.list_sp.append(sp_dict)

            elif item_type in [MGeoItem.TRAFFIC_SIGN, MGeoItem.TRAFFIC_LIGHT, MGeoItem.NODE, MGeoItem.LANE_NODE] :
                if self.is_point_item_inside_planes(items[item_id], select_planes) :
                    sp_dict = {'type': item_type, 'id': item_id}
                    if sp_dict not in self.list_sp:
                        self.list_sp.append(sp_dict)
            
        if len(self.list_sp) > 0:
            self.sp = self.list_sp[0]
        else:
            self.sp = {'type': None, 'id': 0}

    def drag_select_items(self, item_type, xlim, ylim):        
        key = self.mgeo_key
        data_set = { 
            MGeoItem.NODE: self.getNodeSet(key).nodes, 
            MGeoItem.LINK: self.getLinkSet(key).lines, 
            MGeoItem.TRAFFIC_LIGHT: self.getTLSet(key).signals, 
            MGeoItem.TRAFFIC_SIGN: self.getTSSet(key).signals, 
            MGeoItem.JUNCTION: self.getJunctionSet(key).junctions,
            MGeoItem.ROAD: self.getRoadSet(),
            MGeoItem.SYNCED_TRAFFIC_LIGHT: self.getSyncedTLSet(key).synced_signals if self.getSyncedTLSet(key) is not None else None,
            MGeoItem.INTERSECTION_CONTROLLER: self.getIntersectionControllerSet(key).intersection_controllers if self.getIntersectionControllerSet(key) is not None else None,
            MGeoItem.LANE_BOUNDARY: self.getLaneBoundarySet(key).lanes, 
            MGeoItem.LANE_NODE: self.getLaneNodeSet(key).nodes,
            MGeoItem.SINGLECROSSWALK: self.getSingleCrosswalkSet(key).data,
            MGeoItem.CROSSWALK: self.getCrosswalkSet(key).data,
            MGeoItem.ROADPOLYGON: self.getRoadPolygonSet(key).data,
            MGeoItem.PARKING_SPACE: self.getParkingSpaceSet(key).data,
            MGeoItem.SURFACE_MARKING: self.getSurfaceMarkingSet(key).data,
        }

        if item_type not in data_set:
            return

        items = data_set[item_type]


        # link 또는 lane_mark 선택 시
        # 그냥 드래그: 드래그 범위 안에 포함된 Node/LaneNode에 연결된 모든 Link/LaneBoundary 아이템 선택
        # shift+드래그 : 드래그 범위 안에 포함된 Line 아이템만 선택하도록 변경
        if item_type == MGeoItem.LINK:
            if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                flag_shift = True
                items = data_set[MGeoItem.LINK]
            else:
                flag_shift = False
                items = data_set[MGeoItem.NODE]
        elif item_type == MGeoItem.LANE_BOUNDARY:
            if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                flag_shift = True
                items = data_set[MGeoItem.LANE_BOUNDARY]
            else:
                flag_shift = False
                items = data_set[MGeoItem.LANE_NODE]
               
        for item_id in items:
            
            # link 또는 lane_mark 선택 시
            if item_type == MGeoItem.LINK or item_type == MGeoItem.LANE_BOUNDARY:
                if flag_shift:
                    if items[item_id].is_completely_included_in_xy_range(xlim, ylim):
                        sp_dict = {'type': item_type, 'id': item_id}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                else:
                    if items[item_id].is_out_of_xy_range(xlim, ylim):
                        continue
                    for link_item in items[item_id].from_links:
                        sp_dict = {'type': item_type, 'id': link_item.idx}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)
                    for link_item in items[item_id].to_links:
                        sp_dict = {'type': item_type, 'id': link_item.idx}
                        if sp_dict not in self.list_sp:
                            self.list_sp.append(sp_dict)

            elif item_type == MGeoItem.JUNCTION:
                jnodes = items[item_id].jc_nodes
                for jnode in jnodes:
                    if jnode.is_out_of_xy_range(xlim, ylim):
                        continue
                    sp_dict = {'type': item_type, 'id': item_id}
                    if sp_dict not in self.list_sp:
                        self.list_sp.append(sp_dict)
                        
            elif item_type == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                stls = items[item_id].signal_set.to_list()
                for stl in stls:
                    if stl.is_out_of_xy_range(xlim, ylim):
                        continue
                    sp_dict = {'type': item_type, 'id': item_id}
                    if sp_dict not in self.list_sp:
                        self.list_sp.append(sp_dict)
                        
            elif item_type == MGeoItem.INTERSECTION_CONTROLLER:
                ics = items[item_id].get_signal_list()
                for ic in ics:
                    if ic.is_out_of_xy_range(xlim, ylim):
                        continue
                    sp_dict = {'type': item_type, 'id': item_id}
                    if sp_dict not in self.list_sp:
                        self.list_sp.append(sp_dict)
                        
            elif item_type == MGeoItem.CROSSWALK:
                for scw_item in items[item_id].single_crosswalk_list:
                    if scw_item.is_out_of_xy_range(xlim, ylim):
                        continue
                    sp_dict = {'type': item_type, 'id': item_id}
                    if sp_dict not in self.list_sp:
                        self.list_sp.append(sp_dict)
            
            elif item_type == MGeoItem.ROAD:
                rds = items[item_id]
            
            else:
                if items[item_id].is_out_of_xy_range(xlim, ylim):
                    continue
                sp_dict = {'type': item_type, 'id': item_id}
                if sp_dict not in self.list_sp:
                    self.list_sp.append(sp_dict)
            
        if len(self.list_sp) > 0:
            self.sp = self.list_sp[0]
        else:
            self.sp = {'type': None, 'id': 0}
    
    #평면의 normal 방향 반대에 위치해 있는지 체크 plane=(N, D) {N dot P + D = 0}
    def is_point_item_inside_planes(self, item, plane_list):
        is_inside = True
        
        for plane in plane_list :
            plane_normal = np.array(plane[0])
            plane_const = np.array(plane[1])

            if np.inner(plane_normal, np.array(item.point)) + plane_const > 0 :
                is_inside = False
                break

        return is_inside

    def is_bbox_item_inside_planes(self, item, plane_list):
        is_inside = False
        bbox_point_list = list()
        bbox_point_list.append([item.bbox_x[0], item.bbox_y[0], item.bbox_z[0]])
        bbox_point_list.append([item.bbox_x[0], item.bbox_y[0], item.bbox_z[1]])
        bbox_point_list.append([item.bbox_x[0], item.bbox_y[1], item.bbox_z[0]])
        bbox_point_list.append([item.bbox_x[0], item.bbox_y[1], item.bbox_z[1]])
        bbox_point_list.append([item.bbox_x[1], item.bbox_y[0], item.bbox_z[0]])
        bbox_point_list.append([item.bbox_x[1], item.bbox_y[0], item.bbox_z[1]])
        bbox_point_list.append([item.bbox_x[1], item.bbox_y[1], item.bbox_z[0]])
        bbox_point_list.append([item.bbox_x[1], item.bbox_y[1], item.bbox_z[1]])

        #모든 포인트가 선택 영역에 있을때 선택되도록...
        for plane in plane_list :
            plane_normal = np.array(plane[0])
            plane_const = np.array(plane[1])

            is_inside = False
            for bbox_point in bbox_point_list :
                if np.inner(plane_normal, np.array(bbox_point)) + plane_const < 0 :
                    is_inside = True
                    break

            if is_inside :
                for point in item.points :
                    if np.inner(plane_normal, np.array(point)) + plane_const > 0 :
                        is_inside = False
                        break

            if not is_inside :
                break
        """
        #포인트 하나라도 선택 영역에 있으면 선택되도록...
        for plane in plane_list :
            plane_normal = np.array(plane[0])
            plane_const = np.array(plane[1])

            is_inside = False
            for bbox_point in bbox_point_list :
                if np.inner(plane_normal, np.array(bbox_point)) + plane_const < 0 :
                    is_inside = True
                    break

            if is_inside :
                break

        if is_inside :
            for point in item.points :
                is_inside = True
                for plane in plane_list :
                    plane_normal = np.array(plane[0])
                    plane_const = np.array(plane[1])
                    
                    if np.inner(plane_normal, np.array(point)) + plane_const > 0 :
                        is_inside = False
                        break
                if is_inside :
                    break
        """
        return is_inside
            
            
class MessageBoxRcvString(QWidget):
    """데이터가 One Line(string, int, float 등)인 데이터의 Widget 클래스"""
    def __init__(self, type_in_string, data_name):
        super().__init__()
        self.type = type_in_string
        self.data = data.text(2)
        self.initUI()
        self.new_idx = None

    def initUI(self):
        idx = QLabel('value : ')
        if self.data is None or self.data == 'None':
            self.idx_edit = QLineEdit()
        else:
            self.idx_edit = QLineEdit(self.data)

        hbox = QHBoxLayout()
        hbox.addWidget(idx)
        hbox.addWidget(self.idx_edit)
        self.idx_edit.textChanged.connect(self.setString)
        self.setLayout(hbox)

    def iscorrect(self, data):
        """새로운 데이터 타입이 변경하고자 하는 데이터 타입과 같은지 확인한다"""
        if 'float' in self.type:
            try:
                float(data)
                return True
            except ValueError:
                return False

        elif 'int' in self.type:
            try:
                int(data)
                return True
            except ValueError:
                return False
        else:
            return True

    def setString(self, text):
        if text != ''  and not self.iscorrect(text):
            QMessageBox.warning(self, "Type Error", "Please check the type")
            self.idx_edit.setText(self.data)

    def accept(self):
        self.new_idx = self.idx_edit.text()
        return self.new_idx

   