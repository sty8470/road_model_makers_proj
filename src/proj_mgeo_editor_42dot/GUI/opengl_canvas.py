import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger

import math
import shapefile
import csv
import json
import traceback

import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map
from lib.mgeo.utils import error_fix

from mgeo_odr_converter import MGeoToOdrDataConverter
from xodr_data import OdrData

from lib.widget.display_item_prop import DisplayProp
from lib.widget.display_item_style import DisplayStyle
from lib.widget.edit_autogenerate_geometry_points import EditAutogenerateGeometryPoints

class OpenGLCanvas(QOpenGLWidget):
    """
    QOpenGLWidget 클래스
    """

    xRotationChanged = pyqtSignal(int)
    yRotationChanged = pyqtSignal(int)
    zRotationChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(QOpenGLWidget, self).__init__().__init__(parent)

        # 환경설정
        self.config = None
        self.json_file_path = None

        # 로깅 기능을 제공하는 클래스
        self.logger = None

        # 편집 기능을 제공하는 클래스, MGeo 데이터에 대한 참조 또한 여기서 관리한다
        self.mgeo_planner_map = MGeo()
        self.odr_data = OdrData()

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

        # 시작, 끝 선택하기
        self.marker_start_node = []
        self.marker_end_node = []

        # highlight/error 데이터 id 목록
        self.list_highlight1 = []
        self.list_highlight2 = []
        self.list_error = []

        # view button
        self.view_mode = 'view_trans'

        # draw/delete
        self.draw_node_list = dict()

        # 속성
        self.tree_data = None
        self.tree_style = None
        self.tree_attr = None

        # glPushName hashmap
        self.node_map = dict()
        self.line_map = dict()
        self.tl_map = dict()
        self.ts_map = dict()
        self.jc_map = dict()
        self.road_map = dict()


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


    def initializeGL(self):
        """필요한 OpenGL 리소스 및 상태를 설정한다"""
        # glutInit()에서 에러발생 시
        # 아래 파일 직접 다운로드 해야한다.
        # PyOpenGL-3.1.5-cp37-cp37m-win_amd64.whl
        # PyOpenGL_accelerate-3.1.5-cp37-cp37m-win_amd64.whl
        glutInit()
        # 더블버퍼
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)

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
        
        glTranslate(0, 0, self.zoom)

        # 화면 이동을 회전 후에(오브젝트 회전)
        glRotated(self.xRot, 1.0, 0.0, 0.0)
        glRotated(-self.yRot, 0.0, 1.0, 0.0)
        glRotated(self.zRot, 0.0, 0.0, 1.0)

        glTranslate(self.xTran, self.yTran, self.zTran)

        self.projection = glGetDoublev(GL_PROJECTION_MATRIX)
        self.modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)

        self.drawGL()
        self.update() # 계속 업데이트 시켜줌

    
    def resetCamera(self):
        """현재 데이터 중 첫번째 노드 데이터 위치로 reset한다"""       
        
        indices = self.getNodeSet().nodes.keys()
        first_idx = list(indices)[0]
        node = self.getNodeSet().nodes[first_idx]
         
        # 화면 회전
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
        self.setRotWidget()

        # 화면 줌인/아웃
        self.zoom = -50

        # 화면 이동
        self.xTran = -1 * node.point[0]
        self.yTran = -1 * node.point[1]
    

    def drawGL(self):
        """OpenGL Canvas에 그려야 할 Object를 설정한다"""
        margin = 1.2
        xlim = OpenGLCanvas._add_margin_to_range(self.xlim, margin)
        ylim = OpenGLCanvas._add_margin_to_range(self.ylim, margin)

        # bbox를 이용해서 걸러내자
        self.drawNode(xlim, ylim)
        self.drawLink(xlim, ylim)
        self.drawLinkEditPoint()
        self.drawTL(xlim, ylim)
        self.drawTS(xlim, ylim)
        self.drawJunction(xlim, ylim)
        self.drawRoad(xlim, ylim)

        self.updateXLimYLim()

    # 키보드 이벤트
    def keyPressEvent(self, input_key):
        key = input_key.key()
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        
        if key == Qt.Key_Delete and self.sp['id'] is not None:
            self.delete_item(self.list_sp)

        elif key == Qt.Key_Z: # 첫화면으로 돌아가기
            if len(self.getNodeSet().nodes) > 0:
                self.resetCamera()

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
                    # only shift
                    point_move = -15
                else:
                    point_move = -1
            Logger.log_trace('point_move: {}'.format(point_move))
            self.change_point_in_line(point_move)

        elif key == 16777232: # home
            # 처음 위치 가리키도록 
            self.set_point_in_line(0)

        elif key == 16777233: # end
            # 마지막 위치 가리키도록 
            self.set_point_in_line(-1)

        elif key == 93: # ] for debug mode
            # [DEBUG MODE]
            # NOTE: 여기에 중단점을 적용해서 debug 모드에서 자유롭게 사용한다
            Logger.log_info('Entered Debug Mode') 
            Logger.log_info('Exiting Debug Mode')

        elif key == Qt.Key_T:
            # self.auto_fix_traffic_light_conn_link()
            self.auto_set_junction()


    # 마우스 클릭 이벤트
    def mousePressEvent(self, event):
        self.lastPos = event.pos()
        self.makeCurrent()
        if event.buttons() == Qt.LeftButton:
            self.tree_attr.clear()
            self.mouseClickWindow(event.x(), event.y())
            self.updateMgeoPropWidget(self.sp)
        self.doneCurrent()

    # 마우스 드래그 이벤트
    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        zoom_level = self.getZoomLevel()
        multiplier = zoom_level * 1/20 # 1/20은 zoom_level 1에서의 속도

        # Shift 또는 Alt 누를 때 이동 속도를 현재 속도에서 빠르게/느리게 변경 가능
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers & Qt.ShiftModifier:
            multiplier = multiplier * 2  
        elif modifiers & Qt.AltModifier:
            multiplier = multiplier / 2

        mv_x = dx * multiplier
        mv_y = dy * multiplier
        
        if event.buttons() & Qt.LeftButton and self.view_mode == 'view_rotate':
            self.setXRotation(self.xRot + 0.2 * dy)
            self.setYRotation(self.yRot - 0.2 * dx)
        
        elif event.buttons() & Qt.LeftButton and self.view_mode == 'view_trans':
            self.setXYTranslate(mv_x, mv_y)

        elif event.buttons() & Qt.MidButton:
            self.setXYTranslate(mv_x, mv_y)

        self.lastPos = event.pos()


    # 마우스 휠 이벤트
    def wheelEvent(self, event):
        wheel_val = event.angleDelta().y()
        self.setZoom(self.zoom + 0.1 * wheel_val)


    # 마우스 우클릭 이벤트
    def contextMenuEvent(self, event):
        """마우스 우클릭시 클릭된 포인트 옆에 drop down 메뉴를 표시한다"""
        if self.sp is not None and self.sp['type'] is not None and QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.ControlModifier:
            contextMenu = QMenu(self)
            
            # 참고: 데이터 타입에 따라 기능을 추가하고 싶은 경우
            # if self.sp['type'] == MGeoItem.NODE:
            #     sp_act = contextMenu.addAction("시작점")
            #     sp_act.triggered.connect(self.create_line_task_set_start_point)

            delete_act = contextMenu.addAction("Delete")
            delete_act.setShortcut('Delete')
            delete_act.triggered.connect(lambda:self.delete_item(self.list_sp))
            contextMenu.addSeparator()

            if self.sp['type'] == MGeoItem.ROAD:
                recreate_ref_line = contextMenu.addAction("Move Reference Line")
                recreate_ref_line.triggered.connect(self.recreate_ref_line)

            action = contextMenu.exec_(self.mapToGlobal(event.pos()))


    def setXYTranslate(self, dx, dy):
        """Z축 회전한 후, mouse drag로 이동하기 위해 Z 회전 각도로 구분하여 이동하게 한다""" 
        if -135 <= self.zRot <= -45:
            self.xTran += 0.5 * dy * math.cos(math.radians(self.xRot))
            self.yTran += 0.5 * dx * math.cos(math.radians(self.yRot))
        elif 45 <= self.zRot <= 135:
            self.xTran -= 0.5 * dy * math.cos(math.radians(self.xRot))
            self.yTran -= 0.5 * dx * math.cos(math.radians(self.yRot))
        elif self.zRot > 135 or self.zRot < -135:
            self.xTran -= 0.5 * dx * math.cos(math.radians(self.yRot))
            self.yTran += 0.5 * dy * math.cos(math.radians(self.xRot))
        else:
            self.xTran += 0.5 * dx * math.cos(math.radians(self.yRot))
            self.yTran -= 0.5 * dy * math.cos(math.radians(self.xRot))
        # self.update()


    def setZoom(self, zoom):
        self.zoom = zoom
        # 최대 확대 설정
        if self.zoom > -20:
            self.zoom = -21
        # self.update()


    def getZoomLevel(self):
        """최대 줌일 때, zoom_level이 1이고, 줌을 풀면 (넓은 지역을 보면) zoom_level이 늘어나게 한다"""
        zoom_lim = -21
        return -1 * (self.zoom - zoom_lim) / 12 + 1


    def setRotWidget(self):
        """회전과 관련된 Widget을 설정한다""" 
        self.slider[0].setValue(self.normalizeAngle(self.xRot))
        self.slider[1].setValue(self.normalizeAngle(self.yRot))
        self.slider[2].setValue(self.normalizeAngle(self.zRot))
        self.rot_eidt[0].setText(str(math.floor(self.xRot)))
        self.rot_eidt[1].setText(str(math.floor(self.yRot)))
        self.rot_eidt[2].setText(str(math.floor(self.zRot)))


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


    # mouse select
    def mouseClickWindow(self, x, y):
        """ click된 Widget의 좌표를 OpenGL 좌표로 바꾸어 그 좌표에 그려진 Object List를 불러온다""" 
        glSelectBuffer(512)
        glRenderMode(GL_SELECT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPickMatrix(x, self.viewport[3]-y-1, 10.0, 10.0, self.viewport)
        gluPerspective(45.0, self.viewport[2]/self.viewport[3], 1, -self.zoom*2)
        glMatrixMode(GL_MODELVIEW)
        self.drawGL()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        hits = glRenderMode(GL_RENDER)
        glMatrixMode(GL_MODELVIEW)
        if len(hits) > 0:
            self.processHits(hits)


    # 선택된 아이템 확인
    def processHits(self, hits):
        """Click된 좌표의 Object List 중 check된 MGeo Item을 가져온다"""
        sp_val = None
        sp_type = None
        new_id = None
        for ptr in hits:
            if len(ptr.names) <= 0:
                continue
            if ptr.names[0] == self.bsp:
                continue

            sp_key = str(ptr.names[0])
            select_item = str(sp_key)[0:3]

            if select_item == '100' and self.check_item == MGeoItem.NODE.name:
                sp_val = self.node_map[sp_key]
                sp_type = MGeoItem.NODE
                new_id = ptr.names[0]

            elif select_item == '200' and self.check_item == MGeoItem.LINK.name: 
                sp_val = self.line_map[sp_key]
                sp_type = MGeoItem.LINK
                new_id = ptr.names[0]

            elif select_item == '300' and self.check_item == MGeoItem.TRAFFIC_LIGHT.name: 
                sp_val = self.tl_map[sp_key]
                sp_type = MGeoItem.TRAFFIC_LIGHT
                new_id = ptr.names[0]

            elif select_item == '400' and self.check_item == MGeoItem.TRAFFIC_SIGN.name: 
                sp_val = self.ts_map[sp_key]
                sp_type = MGeoItem.TRAFFIC_SIGN
                new_id = ptr.names[0]

            elif select_item == '500' and self.check_item == MGeoItem.JUNCTION.name: 
                sp_val = self.jc_map[sp_key]
                sp_type = MGeoItem.JUNCTION
                new_id = ptr.names[0]

            elif select_item == '200' and self.check_item == MGeoItem.ROAD.name: 
                if len(self.getRoadSet()) == 0:
                    Logger.log_warning('No Road to select. Create road first. (Preliminary road is okay.)')
                    return

                # Link를 클릭해서 Road를 선택하게 하고 싶을 때
                link_id = self.line_map[sp_key]
                link = self.getLinkSet().lines[link_id]
                road = self.getRoadSet()[link.road_id]
                
                sp_val = road.road_id
                sp_type = MGeoItem.ROAD
                new_id = ptr.names[0]

            elif select_item == '600' and self.check_item == MGeoItem.ROAD.name: 
                sp_val = self.road_map[sp_key]
                sp_type = MGeoItem.ROAD
                new_id = ptr.names[0]

        sp_dict = {'type': sp_type, 'id': sp_val}
        self.bsp = new_id
        self.selectMgeoItem(sp_dict) # 여기서 self.list_sp가 업데이트된다
        self.update_inner_link_point_ptr()

        # find 함수 쓰고 다른 item 선택하거나/빈 화면 선택하면 highlight, find_item에서 제거
        if self.find_item is not None:
            if self.find_item in self.list_highlight1:
                self.list_highlight1.remove(self.find_item)
                self.find_item = None
        

    # 다중 선택 관련 함수
    def selectMgeoItem(self, sp_dict):
        """Ctrl 키와 함께 사용하면 다중 선택 기능을 사용할 수 있도록 한다"""
        self.sp = sp_dict
        if QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.ControlModifier:
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
        
        if self.list_sp[0]['type'] != MGeoItem.LINK:
            # Logger.log_error('change_point_in_line works only when a link is select')
            return

        # 현재 선택된 Link를 받아온다
        idx = self.list_sp[0]['id']
        link = self.getLinkSet().lines[idx]

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


    def change_point_in_line(self, move):
        # 현재 선택된 아이템이 line이고, 하나일때만 동작한다
        if len(self.list_sp) != 1:
            # Logger.log_error('change_point_in_line works only when a link is selected')
            return
        
        if self.list_sp[0]['type'] != MGeoItem.LINK:
            # Logger.log_error('change_point_in_line works only when a link is select')
            return

        # 현재 선택된 Link를 받아온다
        idx = self.list_sp[0]['id']
        link = self.getLinkSet().lines[idx]

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
            # Logger.log_error('set_geochange_point works only when a link is selected')
            return
        
        # 선택된 1개의 item이 Link가 아니면,  inner_link_point_ptr를 reset  
        if self.list_sp[0]['type'] != MGeoItem.LINK:
            self.reset_inner_link_point_ptr()
            # Logger.log_error('set_geochange_point works only when a link is select')
            return

        # 이제 이번에 선택된 대상이 기존 대상과 같은지 확인한다
        # 기존의 링크 정보는 여기에 있다
        current_link = self.inner_link_point_ptr['link']

        # 선택되어있는 링크
        link_id = self.list_sp[0]['id']
        new_link = self.getLinkSet().lines[link_id]

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

            Logger.log_trace('set_geochange_point (link id: {}) (point idx: {}, geometry type: {})'.format(
                point_idx, point_idx, geometry_type))
        
        except BaseException as e:
            Logger.log_error('set_geochange_point failed (traceback is down below) \n{}'.format(traceback.format_exc()))


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
            Logger.log_info('geochange point in {} of link (id = {}) deleted'.format(point_idx, link.idx))
        
        except BaseException as e:
            Logger.log_error('delete_geochange_point_current failed (traceback is down below) \n{}'.format(traceback.format_exc()))


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
            
            Logger.log_info('delete all geochange points of link (id = {})'.format(link.idx))
        
        except BaseException as e:
            Logger.log_error('delete_geochange_point_all failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def delete_geometry_points_all_line(self):
        """모든 link에 대한 모든 geochange point를 삭제한다. 단, point_idx가 0인 첫 geometry 값은 삭제하지 않는다."""
        Logger.log_trace('Called: delete_geometry_points_all_line')
        
        result = QMessageBox.question(self, '42dot Map Editor', 'Do you want to delete all Geometry Points?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

        if result == QMessageBox.Ok:
            
            lines_list = self.getLinkSet().lines

            for line_id in lines_list:
                line = lines_list[line_id]
                try:
                    for i in range(len(line.geometry) - 1):
                        line.geometry.pop()
                except BaseException as e:  
                    Logger.log_error('delete_geochange_point_all failed (traceback below) \n{}'.format(traceback.format_exc()))
            
            Logger.log_info('delete all geochange points of all link')
        
        else:
            Logger.log_info('Cancelled delete all geochange points of all link')


    def recreate_ref_line(self):
        road = self.getRoadSet()[self.sp['id']]
        try:
            road.link_list_not_organized.remove(road.ref_line[0])
            road.find_reference_line()
            road.changed = True
            Logger.log_info('>> Ref line changed - ID: {}'.format(Link.get_id_list_string(road.ref_line)))
        
        except BaseException as e:
            Logger.log_error('Failed to find reference line for road: {}'.format(Link.get_id_list_string(road.ref_line)))


    # OpenGL Widget에 Paint하는 함수
    def plot_text(self, name, point, color=[0, 0, 0], direction=[0, 0, 0]):
        glColor3f(color[0], color[1], color[2])
        font10 = GLUT_BITMAP_HELVETICA_10
        font12 = GLUT_BITMAP_HELVETICA_12
        font18 = GLUT_BITMAP_HELVETICA_18
        font = font10
        offset = abs(self.zoom/100)
        if self.zoom >= -20:
            font = font18
        elif self.zoom < -20 and self.zoom >= -80:
            font = font18
        elif self.zoom < -80 and self.zoom > -120:
            font = font12
        text_point = np.array(point) + (np.array(direction) * offset)
        glRasterPos3f(text_point[0], text_point[1] + offset, text_point[2])

        for ch in str(name):
           glutBitmapCharacter(font, ctypes.c_int(ord(ch)))


    def paint_point(self, name, point, color=[0, 0, 0], size=5.0):
        glInitNames()
        glPushName(name)
        glColor3f(color[0], color[1], color[2])
        glPointSize(size)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBegin(GL_POINTS)
        glVertex3f(point[0], point[1], point[2])
        glEnd()
        glPopName()

    # Geometry 변경 포인트마다 모양이 다른 geochange point 그리기
    def plot_points(self, name, points, color=[0, 0, 0], size=1.0, geometry=None):
        """Link에 속한 Geometry Point별로 다른 도형을 그린다"""
        if geometry is not None and len(geometry) > 0:
            for i in range(len(points)):
                geo = next((item for item in geometry if item['id'] == i), None)
                if geo is not None and i != 0:
                    if geo['method'] == 'poly3':
                        self.paint_triangle(points[i], self.config['STYLE']['LINK']['GEO STYLE']['POLY3 COLOR'], size)
                    elif geo['method'] == 'line':
                            self.paint_rhombus(points[i], self.config['STYLE']['LINK']['GEO STYLE']['LINE COLOR'], size)
                    elif geo['method'] == 'paramPoly3':
                            self.paint_inverted_triangle(points[i], self.config['STYLE']['LINK']['GEO STYLE']['PARAMPOLY3 COLOR'], size)
                else:
                    if self.sp is not None and self.sp['id'] == self.line_map[str(name)]:
                        self.paint_square(points[i], color, size)
        elif geometry is None:
            for i in range(len(points)):
                self.paint_square(points[i], color, size)

    # 일반
    def paint_square(self, point, color, size):
        glColor3f(color[0], color[1], color[2])
        glPointSize(size*3)
        glBegin(GL_POINTS)
        glVertex3f(point[0], point[1], point[2])
        glEnd()

    # 삼각형
    def paint_triangle(self, point, color, size): #▲
        glColor3f(color[0], color[1], color[2])
        glBegin(GL_POLYGON)
        glVertex3f(point[0]-1, point[1]-1, point[2])
        glVertex3f(point[0]+1, point[1]-1, point[2])
        glVertex3f(point[0], point[1]+1, point[2])
        glEnd()

    # 마름모
    def paint_rhombus(self, point, color, size): #◆
        glColor3f(color[0], color[1], color[2])
        glBegin(GL_POLYGON)
        glVertex3f(point[0], point[1]-1, point[2])
        glVertex3f(point[0]-1, point[1], point[2])
        glVertex3f(point[0], point[1]+1, point[2])
        glVertex3f(point[0]+1, point[1], point[2])
        glEnd()

    def paint_inverted_triangle(self, point, color, size): #▼
        glColor3f(color[0], color[1], color[2])
        glBegin(GL_POLYGON)
        glVertex3f(point[0], point[1]-1, point[2])
        glVertex3f(point[0]+1, point[1]+1, point[2])
        glVertex3f(point[0]-1, point[1]+1, point[2])
        glEnd()


    def plot_link(self, name, points, color=[0, 0, 0], width=1.0, geometry=None):
        """Link에 속한 Geometry Point별로 다른 선을 그린다"""
        glInitNames()
        glPushName(name)
        glColor3f(color[0], color[1], color[2])
        glLineWidth(width)
        start_id = 0
        end_id = len(points)

        if (geometry is not None and len(geometry) > 0):
            if len(geometry) == 1:
                start_id = 0
                end_id = len(points)
                line_type = self.config['STYLE']['LINK']['GEO STYLE'][geometry[0]['method'].upper() + ' STYLE']
                self.paint_line(points[start_id:end_id+1], line_type)
            else:
                for i in range(len(geometry)):
                    if i == 0:
                        start_id = 0
                        end_id = geometry[i+1]['id']
                        line_type = self.config['STYLE']['LINK']['GEO STYLE'][geometry[i]['method'].upper() + ' STYLE']
                    elif i == (len(geometry)-1):
                        start_id = geometry[i]['id']
                        end_id = len(points)
                        line_type = self.config['STYLE']['LINK']['GEO STYLE'][geometry[i]['method'].upper() + ' STYLE']
                    else:
                        start_id = geometry[i]['id']
                        end_id = geometry[i+1]['id']
                        line_type = self.config['STYLE']['LINK']['GEO STYLE'][geometry[i]['method'].upper() + ' STYLE']

                    self.paint_line(points[start_id:end_id+1], line_type)
        else:
            self.paint_line(points)
        glPopName()


    def plot_road(self, name, points, color=[0, 0, 0], width=1.0, isRefLine=True):
        glInitNames()
        glPushName(name)
        if isRefLine:            
            glColor4f(color[0], color[1], color[2], 0.6)
        else:
            glColor4f(color[0], color[1], color[2], 0.2)
        glLineWidth(width)
        self.paint_line(points)
        glPopName()


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


    def plot_junction(self, name, points, color=[0, 0, 0], size=5.0):
        glInitNames()
        glPushName(name)
        glColor3f(color[0], color[1], color[2])
        glPointSize(size)
        glBegin(GL_POINTS)
        for i in range(len(points)):
            glVertex3f(points[i][0], points[i][1], points[i][2])
        glEnd()
        glPopName()


    # select 기능을 위해서 Object에 name을 설정한다
    # glPushName()이 int32(2^32)까지 지원하기 때문에
    # 임의로 node는 100+, line은 200+... 로 새로운 name을 적용한다
    # 임의로 정한 name과 원래의 idx값은 hashmap으로 연결한다

    def drawNode(self, xlim, ylim):
        if self.config['STYLE']['NODE']['VIEW']:
            nodes = self.getNodeSet().nodes
            for i, node_id in enumerate(nodes):
                new_id = "100" + str(i)
                self.node_map[new_id] = node_id

                if nodes[node_id].is_out_of_xy_range(xlim, ylim):
                    continue

                if next((item for item in self.list_sp if item['id'] == node_id), False):
                    size = self.config['STYLE']['SELECT']['SIZE']
                    color = self.config['STYLE']['SELECT']['COLOR']

                elif next((item for item in self.marker_start_node if item['id'] == node_id), False):
                    size = self.config['STYLE']['NODE']['START']['SIZE']
                    color = self.config['STYLE']['NODE']['START']['COLOR']

                elif next((item for item in self.marker_end_node if item['id'] == node_id), False):
                    size = self.config['STYLE']['NODE']['END']['SIZE']
                    color = self.config['STYLE']['NODE']['END']['COLOR']

                elif next((item for item in self.list_highlight1 if item['id'] == node_id), False):
                    size = self.config['STYLE']['HIGHLIGHT1']['SIZE']
                    color = self.config['STYLE']['HIGHLIGHT1']['COLOR']

                elif next((item for item in self.list_highlight2 if item['id'] == node_id), False):
                    size = self.config['STYLE']['HIGHLIGHT2']['SIZE']
                    color = self.config['STYLE']['HIGHLIGHT2']['COLOR']

                elif next((item for item in self.list_error if item['id'] == node_id), False):
                    size = self.config['STYLE']['ERROR']['SIZE']
                    color = self.config['STYLE']['ERROR']['COLOR']

                else:
                    size = self.config['STYLE']['NODE']['NORMAL']['SIZE']
                    color = self.config['STYLE']['NODE']['NORMAL']['COLOR']

                nodes[node_id].set_vis_mode_manual_appearance(size, color)
                point = nodes[node_id].point

                self.paint_point(int(new_id), point, color, size)

                if self.config['STYLE']['NODE']['TEXT']:
                    self.plot_text(node_id, point, color)


    def drawLink(self, xlim, ylim):
        if self.config['STYLE']['LINK']['VIEW']:

            lines = self.getLinkSet().lines
            for i, line_id in enumerate(lines):
                new_id = "200" + str(i)
                self.line_map[new_id] = line_id

                if lines[line_id].is_out_of_xy_range(xlim, ylim):
                    continue
                
                if next((item for item in self.list_sp if item['id'] == line_id), False):
                    color = self.config['STYLE']['SELECT']['COLOR']
                    width = self.config['STYLE']['SELECT']['WIDTH']

                elif next((item for item in self.list_highlight1 if item['id'] == line_id), False):
                    color = self.config['STYLE']['HIGHLIGHT1']['COLOR']
                    width = self.config['STYLE']['HIGHLIGHT1']['WIDTH']

                elif next((item for item in self.list_highlight2 if item['id'] == line_id), False):
                    color = self.config['STYLE']['HIGHLIGHT2']['COLOR']
                    width = self.config['STYLE']['HIGHLIGHT2']['WIDTH']

                elif next((item for item in self.list_error if item['id'] == line_id), False):
                    color = self.config['STYLE']['ERROR']['COLOR']
                    width = self.config['STYLE']['ERROR']['WIDTH']

                else:
                    color = self.config['STYLE']['LINK']['NORMAL']['COLOR']
                    width = self.config['STYLE']['LINK']['NORMAL']['WIDTH']

                lines[line_id].set_vis_mode_manual_appearance(width, color)
                points = lines[line_id].points
                geo = lines[line_id].geometry

                if self.config['STYLE']['LINK']['GEO CHANGE']:
                    self.plot_link(int(new_id), points, color, width, geo)
                    self.plot_points(int(new_id), points, color, width, geo)

                elif self.config['STYLE']['LINK']['GEO CHANGE'] == False:
                    self.plot_link(int(new_id), points, color, width)
                    self.plot_points(int(new_id), points, color, width)

                if self.config['STYLE']['LINK']['TEXT']:
                    try:
                        p0 = points[0]
                        p1 = points[1]
                        if lines[line_id].ego_lane is not None:
                            el = int(lines[line_id].ego_lane)
                            uv = (p1-p0)/np.linalg.norm(p1-p0)
                            point = p0 + ( uv * el )
                            self.plot_text(line_id, point, color, uv)
                        else:
                            point = p0
                            self.plot_text(line_id, point, color)


                    except BaseException as e:
                        QMessageBox.warning(self, "Warning", e.args[0])
                        return


    def drawLinkEditPoint(self):
        if self.config['STYLE']['LINK']['VIEW']:

            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                return
            
            # edit point 위치를 받아온다
            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']
            point = link.points[point_idx]

            # 아래 함수로 그려준다 (이 데이터는 선택할 대상이 아니므로 name을 주지 않음)
            color = self.config['STYLE']['SELECT']['COLOR']
            size = self.config['STYLE']['SELECT']['SIZE'] * 1.5 # 1.5 배 큰 값으로 그려준다
            
            glColor3f(color[0], color[1], color[2])
            glPointSize(size)
            glBegin(GL_POINTS)
            glVertex3f(point[0], point[1], point[2])
            glEnd()
        

    def drawTL(self, xlim, ylim):
        if self.config['STYLE']['TRAFFIC_LIGHT']['VIEW']:

            tl_set = self.getTLSet().signals
            for i, tl_id in enumerate(tl_set):
                new_id = "300" + str(i)
                self.tl_map[new_id] = tl_id

                if tl_set[tl_id].is_out_of_xy_range(xlim, ylim):
                    continue

                if next((item for item in self.list_sp if item['id'] == tl_id), False):
                    color = self.config['STYLE']['SELECT']['COLOR']
                    size = self.config['STYLE']['SELECT']['SIZE']

                elif next((item for item in self.list_highlight1 if item['id'] == tl_id), False):
                    color = self.config['STYLE']['HIGHLIGHT1']['COLOR']
                    size = self.config['STYLE']['HIGHLIGHT1']['SIZE']

                elif next((item for item in self.list_highlight2 if item['id'] == tl_id), False):
                    color = self.config['STYLE']['HIGHLIGHT2']['COLOR']
                    size = self.config['STYLE']['HIGHLIGHT2']['SIZE']

                elif next((item for item in self.list_error if item['id'] == tl_id), False):
                    color = self.config['STYLE']['ERROR']['COLOR']
                    size = self.config['STYLE']['ERROR']['SIZE']

                else:
                    color = self.config['STYLE']['TRAFFIC_LIGHT']['NORMAL']['COLOR']
                    size = self.config['STYLE']['TRAFFIC_LIGHT']['NORMAL']['SIZE']

                self.paint_point(int(new_id), tl_set[tl_id].point, color, size)

                if self.config['STYLE']['TRAFFIC_LIGHT']['TEXT']:
                    self.plot_text(tl_id, tl_set[tl_id].point, color)


    def drawTS(self, xlim, ylim):
        if self.config['STYLE']['TRAFFIC_SIGN']['VIEW']:

            ts_set = self.getTSSet().signals
            for i, ts_id in enumerate(ts_set):
                new_id = "400" + str(i)
                self.ts_map[new_id] = ts_id

                if ts_set[ts_id].is_out_of_xy_range(xlim, ylim):
                    continue

                if next((item for item in self.list_sp if item['id'] == ts_id), False):
                    color = self.config['STYLE']['SELECT']['COLOR']
                    size = self.config['STYLE']['SELECT']['SIZE']

                elif next((item for item in self.list_highlight1 if item['id'] == ts_id), False):
                    color = self.config['STYLE']['HIGHLIGHT1']['COLOR']
                    size = self.config['STYLE']['HIGHLIGHT1']['SIZE']

                elif next((item for item in self.list_highlight2 if item['id'] == ts_id), False):
                    color = self.config['STYLE']['HIGHLIGHT2']['COLOR']
                    size = self.config['STYLE']['HIGHLIGHT2']['SIZE']

                elif next((item for item in self.list_error if item['id'] == ts_id), False):
                    color = self.config['STYLE']['ERROR']['COLOR']
                    size = self.config['STYLE']['ERROR']['SIZE']

                else:
                    color = self.config['STYLE']['TRAFFIC_SIGN']['NORMAL']['COLOR']
                    size = self.config['STYLE']['TRAFFIC_SIGN']['NORMAL']['SIZE']

                self.paint_point(int(new_id), ts_set[ts_id].point, color, size)

                if self.config['STYLE']['TRAFFIC_SIGN']['TEXT']:
                    self.plot_text(ts_id, ts_set[ts_id].point, color)


    def drawJunction(self, xlim, ylim):
        if self.config['STYLE']['JUNCTION']['VIEW']:

            junctions = self.getJunctionSet().junctions

            drawing_order = []
            for jid in junctions:
                if next((item for item in self.list_sp if item['id'] == jid), False):
                    drawing_order.insert(0, jid)
                elif next((item for item in self.list_highlight1 if item['id'] == jid), False):
                    drawing_order.insert(0, jid)
                elif next((item for item in self.list_highlight2 if item['id'] == jid), False):
                    drawing_order.insert(0, jid)
                elif next((item for item in self.list_error if item['id'] == jid), False):
                    drawing_order.insert(0, jid)
                else:
                    drawing_order.append(jid)

            for i, jc_id in enumerate(drawing_order):
                new_id = "500" + str(i)
                self.jc_map[new_id] = jc_id
                if next((item for item in self.list_sp if item['id'] == jc_id), False):
                    width = self.config['STYLE']['SELECT']['WIDTH']
                    color = self.config['STYLE']['SELECT']['COLOR']

                elif next((item for item in self.list_highlight1 if item['id'] == jc_id), False):
                    width = self.config['STYLE']['HIGHLIGHT1']['WIDTH']
                    color = self.config['STYLE']['HIGHLIGHT1']['COLOR']

                elif next((item for item in self.list_highlight2 if item['id'] == jc_id), False):
                    width = self.config['STYLE']['HIGHLIGHT2']['WIDTH']
                    color = self.config['STYLE']['HIGHLIGHT2']['COLOR']

                elif next((item for item in self.list_error if item['id'] == jc_id), False):
                    width = self.config['STYLE']['ERROR']['WIDTH']
                    color = self.config['STYLE']['ERROR']['COLOR']

                else:
                    width = self.config['STYLE']['JUNCTION']['NORMAL']['WIDTH']
                    color = self.config['STYLE']['JUNCTION']['NORMAL']['COLOR']

                points = junctions[jc_id].get_jc_node_points()
                if points is None:
                    Logger.log_error('junction (id = {}) has node points'.format(jc_id))
                    continue

                self.plot_junction(int(new_id), points, color, 18)

                if self.config['STYLE']['JUNCTION']['TEXT']:
                    self.plot_text(new_id, points[0], color)

    
    def drawRoad(self, xlim, ylim):
        if self.config['STYLE']['ROAD']['VIEW']:
            roads = self.odr_data.roads
            for i, road_id in enumerate(roads):
                new_id = "600" + str(i)
                self.road_map[new_id] = road_id

                is_selected = False
                if next((item for item in self.list_sp if item['id'] == road_id), False):
                    is_selected = True
                    color = self.config['STYLE']['SELECT']['COLOR']

                elif next((item for item in self.list_highlight1 if item['id'] == road_id), False):
                    is_selected = True
                    color = self.config['STYLE']['HIGHLIGHT1']['COLOR']

                else:
                    color = self.config['STYLE']['ROAD']['NORMAL']['COLOR']

                # width는 공통으로 사용 
                width = self.config['STYLE']['ROAD']['NORMAL']['WIDTH']

                # 모든 Ref Line을 그려서 보여준다
                if len(roads[road_id].ref_line) > 0:
                    for ref_line in roads[road_id].ref_line:
                        ref_line.set_vis_mode_manual_appearance(width, color)
                        points = ref_line.points
                        self.plot_road(int(new_id), points, color, width)

                # 선택된 Road에 대해서는, Road를 구성하는 모든 Link 또한 보여준다
                if is_selected:
                    for link in roads[road_id].link_list_not_organized:
                        points = link.points
                        self.plot_road(int(new_id), points, color, width - 1, False)

                    # 아래는 link_list_not_organized 사용하기 이전에, lane_section에 저장된 정보를 이용하여 plot하던 경우.   
                    # for lane_section in roads[road_id].get_lane_sections():
                    #     for line in lane_section.get_lanes_L():
                    #         line.set_vis_mode_manual_appearance(width, color)
                    #         points = line.points
                    #         self.plot_road(int(new_id), points, color, width - 1, False)
                    #     for line in lane_section.get_lanes_R():
                    #         line.set_vis_mode_manual_appearance(width, color)
                    #         points = line.points
                    #         self.plot_road(int(new_id), points, color, width - 1, False)

                if self.config['STYLE']['ROAD']['TEXT']:
                    if len(roads[road_id].ref_line) > 0:
                        try:
                            p0 = ref_line.points[0]
                            p1 = ref_line.points[1]
                            uv = (p1-p0)/np.linalg.norm(p1-p0)
                            point = p0 + uv
                            self.plot_text(road_id, point, color, uv)

                        except BaseException as e:
                            QMessageBox.warning(self, "Warning", e.args[0])
                            return


    def getNodeSet(self):
        return self.mgeo_planner_map.node_set
    

    def getLinkSet(self):
        return self.mgeo_planner_map.link_set


    def getTSSet(self):
        return self.mgeo_planner_map.sign_set


    def getTLSet(self):
        return self.mgeo_planner_map.light_set


    def getJunctionSet(self):
        return self.mgeo_planner_map.junction_set


    def getRoadSet(self):
        return self.odr_data.roads


    def setMGeoPlannerMap(self, mgeo_planner_map):
        self.mgeo_planner_map = mgeo_planner_map
        self.odr_data = OdrData()


    def setViewMode(self, view_mode):
        if view_mode == 'view_xy':
            self.setXRotation(0)
            self.setYRotation(0)
            self.setZRotation(0)
        elif view_mode == 'view_yz':
            self.setXRotation(0)
            self.setYRotation(-90)
            self.setZRotation(0)
        elif view_mode == 'view_zx':
            self.setXRotation(-90)
            self.setYRotation(0)
            self.setZRotation(0)
        else:
            self.view_mode = view_mode

    # MGeo 속성 Tree Widget 설정
    def updateMgeoPropWidget(self, mgeo):
        """MGeo 속성 Tree Widget의 내용을 현재 선택된 MGeo 속성으로 업데이트한다"""
        self.display_prop.set_prop(self, self.tree_attr, mgeo, self.getRoadSet())

    # [Data_Tree] 1. Mgeo Item ID List 가져오기 (tree_data)
    # MGEO ID 변경되는 경우에 추가
    # 1. import(opengl_user_input_handler에서 set_tree_data연결)
    # 2. 속성 업데이트(아이디 변경)
    # 3. mgeo item 삭제
    # 4. id로 mgeo 아이템 찾기
    def updateMgeoIdWidget(self):
        self.tree_data.clear()
        data_set = { MGeoItem.NODE: self.getNodeSet().nodes, 
                    MGeoItem.LINK: self.getLinkSet().lines, 
                    MGeoItem.TRAFFIC_LIGHT: self.getTLSet().signals, 
                    MGeoItem.TRAFFIC_SIGN: self.getTSSet().signals, 
                    MGeoItem.JUNCTION: self.getJunctionSet().junctions,
                    MGeoItem.ROAD: self.getRoadSet() }

        # 1. 데이터(Mgeo Item) 리스트
        for item in MGeoItem:
            if item not in data_set.keys():
                continue
            
            item_list = QTreeWidgetItem(self.tree_data)
            item_list.setText(0, item.name)
            item_list.setFlags(item_list.flags() | Qt.ItemIsUserCheckable)

            if self.check_item == item.name:
                item_list.setCheckState(0, Qt.Checked)
            else:
                item_list.setCheckState(0, Qt.Unchecked)

            if item not in data_set.keys():
                continue

            for idx in data_set[item]:
                idx_list = QTreeWidgetItem(item_list)
                idx_list.setText(0, "{}".format(idx))


    # [Tree]. import 후 데이터 리스트 불러오기
    def updateTreeWidget(self):
        # data import > set data & style tree list
        self.updateMgeoIdWidget()
        self.display_style.set_widget()

        self.tree_data.itemClicked.connect(self.onItemChanged)
        self.tree_data.itemDoubleClicked.connect(self.mgeoIdDoubleClickEvent)



    # 1-2. 데이터(Mgeo Item) 선택(체크박스 하나만 선택되도록)
    def onItemChanged(self, item, column):
        try:
            MGeoItem[item.text(column)]
            treelist = self.tree_data.invisibleRootItem()
            item_count = treelist.childCount()

            if item.checkState(column) == Qt.Checked:
                self.check_item = item.text(column)
                for it in range(item_count):
                    it_name = treelist.child(it).text(0)
                    if it_name != self.check_item:
                        treelist.child(it).setCheckState(0, Qt.Unchecked)
            if item.checkState(column) == Qt.Unchecked and item.text(column) == self.check_item:
                self.check_item = None
                
        except:
            if item.childCount() == 0:
                self.highlight_mgeo_item(MGeoItem[item.parent().text(0)], item.text(0))
                self.updateMgeoPropWidget(self.find_item)
                

    def setConfig(self, config):
        self.config = config


    def setConfigFilePath(self, file_path):
        self.json_file_path = file_path


    # 아이템 삭제하기
    def delete_item(self, items):
        Logger.log_trace('Called: delete_item')
        try:
            if len(items) == 1:
                result = QMessageBox.question(self, '42dot Map Editor', 
                                    'Delete item\n{} {}'.format(items[0]['type'].name, items[0]['id']), 
                                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            else:
                result = QMessageBox.question(self, '42dot Map Editor', 
                                    'Delete multiple {}s'.format(items[0]['type'].name), 
                                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

            if result == QMessageBox.Ok:
                for item in items:
                    idx = item['id']
                    try:
                        item_type = 'Undefined'
                        if item['type'] == MGeoItem.NODE:
                            node_set = self.getNodeSet()
                            edit_node.delete_node(node_set, node_set.nodes[idx],
                                delete_junction=True, junction_set=self.getJunctionSet())
                            item_type = 'Node'
                        elif item['type'] == MGeoItem.LINK:
                            link_set = self.getLinkSet()
                            edit_link.delete_link(link_set, link_set.lines[idx])
                            item_type = 'Link'
                        elif item['type'] == MGeoItem.TRAFFIC_SIGN:
                            ts_set = self.getTSSet()
                            edit_signal.delete_signal(ts_set, ts_set.signals[idx])
                            item_type = 'TrafficSign'
                        elif item['type'] == MGeoItem.TRAFFIC_LIGHT:
                            tl_set = self.getTLSet()
                            edit_signal.delete_signal(tl_set, tl_set.signals[idx])
                            item_type = 'TrafficLight'
                        elif item['type'] == MGeoItem.JUNCTION: 
                            junction_set = self.getJunctionSet()
                            edit_junction.delete_junction(junction_set, junction_set.junctions[idx])
                            item_type = 'Junction'

                        Logger.log_info('{} (id: {}) deleted.'.format(item_type, idx))
                        
                    except BaseException as e:
                        QMessageBox.warning(self, "Warning", e.args[0])
                    
                # delete attribute widget
                self.sp = {'type': None, 'id': 0}
                self.list_sp.clear()
                self.tree_attr.clear()
                self.updateMgeoIdWidget()
                self.reset_inner_link_point_ptr()

        except BaseException as e:
            Logger.log_error('delete_item failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def create_junction(self):
        Logger.log_trace('Called: create_junction')
        try:
            # 선택된 노드를 받아온다
            nodes_to_create_juction = []
            for sp in self.list_sp:

                # TEMP: 버그 workaround
                if sp['type'] is None:
                    continue

                # 노드 이외 다른 종류의 데이터가 선택되었는지 체크
                if sp['type'] != MGeoItem.NODE:
                    Logger.log_error('Only nodes are allowed to create a junction.')
                    return

                node = self.getNodeSet().nodes[sp['id']]
                nodes_to_create_juction.append(node)

            if len(nodes_to_create_juction) == 0:
                Logger.log_error('There is no selected nodes.')
                return 

            new_junc = edit_junction.create_junction(
                self.getJunctionSet(),
                nodes_to_create_juction)

            self.updateMgeoIdWidget()
            Logger.log_info('Junction (id = {} is created)'.format(new_junc.idx))
        
        except BaseException as e:
            Logger.log_error('create_junction failed (traceback is down below) \n{}'.format(traceback.format_exc()))


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

            # 현재 선택된 아이템이 node이고, 2개일 때만 동작한다.
            if len(self.list_sp) != 2:
                Logger.log_info('Invalid operation: connect_nodes works only when two nodes are selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            for selected_item in self.list_sp:
                if selected_item['type'] != MGeoItem.NODE:
                    Logger.log_info('Invalid operation: connect_nodes works only when two nodes are selected. ({} type data is included)'.format(selected_item['type']))
                    return
            
            # 두 노드가 이미 연결되어있는 노드인지 검색해본다
            start_node = self.getNodeSet().nodes[self.list_sp[0]['id']]
            end_node = self.getNodeSet().nodes[self.list_sp[1]['id']]

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

            self.getLinkSet().append_line(connecting_link, create_new_key=True)

            # 
            Logger.log_info('connecting link (id: {}) created (from node: {} -> to: {})'.format(connecting_link.idx, start_node.idx, end_node.idx))

        except BaseException as e:
            Logger.log_error('connect_nodes failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def merge_links(self):
        Logger.log_trace('Called: merge_links')
        try:
            # REFACTOR(sglee) : refactor this into edit_link or somewhere
            self.temp_workaround_remove_none_item_in_list_sp()

            # 현재 선택된 아이템이 line이고, 2개일 때만 동작한다.
            if len(self.list_sp) != 2:
                Logger.log_info('Invalid operation: merge_links works only when two connected links are selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            for selected_item in self.list_sp:
                if selected_item['type'] != MGeoItem.LINK:
                    Logger.log_info('Invalid operation: merge_links works only when two connected links are selected. ({} type data is included)'.format(selected_item['type']))
                    return

            # 두 링크가 연결되어있는 링크인지 검색해본다
            link0 = self.getLinkSet().lines[self.list_sp[0]['id']]
            link1 = self.getLinkSet().lines[self.list_sp[1]['id']]


            if link1 in link0.get_from_links():
                # link1 -> link0 인 경우
                pre_link = link1
                suc_link = link0

            elif link1 in link0.get_to_links():
                # link0 -> link1 인 경우
                pre_link = link0
                suc_link = link1
                
            else:
                Logger.log_info('Invalid operation: merge_links works only when two connected links are selected. (two links are not connected to each other)')
                return

            # 노드에 연결된 링크 수를 확인하여, 두 링크 이외에 다른 링크가 연결 되어 있는지 확인한다
            node = pre_link.to_node
            if len(node.get_from_links()) != 1 or len(node.get_to_links()) != 1:
                Logger.log_info('Invalid operation: cannot delete node between the two selected links. (another link is connected to the node)')

            if len(node.junctions) != 0:
                Logger.log_info('Invalid operation: cannot delete node that belongs to a junction (node id = {})'.format(node.idx))

            # 이제 노드를 지우고, 두 link를 합치면 된다.
            # 이 때, link0의 property로 link를 구성하게 된다. (link1은 point만 넘겨주고, 삭제하면 된다)

            # 우선 삭제되어야 할 node의 reference를 끊는다
            node.to_links = list()
            node.from_links = list()

            # 일부 link attribute는 보관되거나 수정되어야 하고, 다음과 같이 한다.
            # NOTE: [ASSUMPTION] point는 pre_link의 마지막 point, suc_link의 마지막 point가 겹치므로,
            # suc_link의 첫번째 포인트는 사용하지 않는다
            new_points = np.vstack((pre_link.points, suc_link.points[1:]) )

            # 예를 들어 pre_link point가 10개 였으면,
            # suc_link의 geometry는 9만큼 뒤로 밀려야 함 (suc_link의 첫번째 포인트는 사용하지 않으므로)
            point_idx_offset = len(pre_link.points) - 1

            new_geometry = pre_link.geometry
            for i in range(1, len(suc_link.geometry)):
                geo_change_point = suc_link.geometry[i]
                geo_change_point['id'] += point_idx_offset
                new_geometry.append(geo_change_point)

            link0.set_points(new_points) # 주의: geo_change_point 수정하기 전에 여기를 호출하면 안 된다!
            link0.geometry = new_geometry
            
            # keep 하는 링크의 node reference 변경
            if link0 is pre_link:
                # link0 뒤에 link1이 붙는다
                link0.to_node = link1.to_node
            else:
                # link0 앞에 link1이 붙는다
                link0.from_node = link1.from_node

            edit_link.delete_link(self.getLinkSet(), link1)
            edit_node.delete_node(self.getNodeSet(), node,
                delete_junction=True, junction_set=self.getJunctionSet())

            Logger.log_info('merge_links is done successfully.')
            return

        except BaseException as e:
            Logger.log_error('merge_links failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    
    def __get_total_distance(self, points):
        total_distance = 0
        for i in range(len(points) - 1) :
            vect = points[i+1] - points[i]
            dist_between_each_point_pair = np.linalg.norm(vect, ord=2)
            total_distance += dist_between_each_point_pair
        return total_distance


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
            self.divide_a_link(keep_front)

        except BaseException as e:
            Logger.log_error('divide_a_link_smart failed (traceback is down below) \n{}'.format(traceback.format_exc()))


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

            # 이 위치에 새로운 Node를 생성
            new_node = Node()
            self.getNodeSet().append_node(new_node, create_new_key=True)
            new_node.point = link.points[point_idx]


            """새로운 point 생성하는 부분"""
            # 2개의 points로 분리한다
            new_points_start = link.points[:point_idx+1] # point_idx를 포함해야 하므로
            new_points_end = link.points[point_idx:]


            """Geometry Point 새로 생성하는 부분"""
            # geometry point 또한 분리한다
            new_geometry_start = list()
            new_geometry_end = list()
            for i in range(len(link.geometry)):
                pts = link.geometry[i]
                if pts['id'] < point_idx:
                    new_geometry_start.append(pts)
                else:
                    new_pts = {'id':pts['id'] - point_idx, 'method': pts['method']}
                    new_geometry_end.append(new_pts)

            # new_geometry_end에서 0위치에 아무것도 없는지 확인
            if len(new_geometry_end) == 0:
                new_geometry_end = [{'id': 0, 'method':'poly3'}]
            else:
                # 맨 처음 element의 id는 0 이어야 하는데,
                # 아무것도 없으면, 추가해주면 된다.
                if new_geometry_end[0]['id'] > 0:
                    new_geometry_end = [{'id': 0, 'method':'poly3'}] + new_geometry_end


            # 어떤 링크를 살릴 것인가? 우선 시작점에서의 링크를 살린다고 하면,
            if keep_front:
                # 기존 링크는 to_node를 새로운 노드로 변경해야 함
                prev_to_node = link.to_node # 새 링크에서 이 to_node로 연결할 것이므로 백업
                link.remove_to_node()
                link.set_to_node(new_node)

                # 우선 가리키려는 링크 위 포인트를 0으로 돌려놓는다
                # link.set_points를 호출하면서 링크 내 point 수가 변하므로 오류 발생 가능
                self.set_point_in_line(0)

                # 포인트 변경
                link.set_points(new_points_start)  
                link.geometry = new_geometry_start


                # 새로운 링크 생성
                new_link = Link()
                self.getLinkSet().append_line(new_link, create_new_key=True)

                new_link.set_from_node(new_node)
                new_link.set_to_node(prev_to_node)
                new_link.set_points(new_points_end)
                new_link.geometry = new_geometry_end


            else:
                # 기존 링크는 from_node를 새로운 노드로 변경해야 함
                prev_from_node = link.from_node # 새 링크에서 이 from_node 연결할 것이므로 백업
                link.remove_from_node()
                link.set_from_node(new_node)

                # 우선 가리키려는 링크 위 포인트를 0으로 돌려놓는다
                # link.set_points를 호출하면서 링크 내 point 수가 변하므로 오류 발생 가능
                self.set_point_in_line(0)

                # 포인트 변경
                link.set_points(new_points_end)
                link.geometry = new_geometry_end

                # 새로운 링크 생성
                new_link = Link()
                self.getLinkSet().append_line(new_link, create_new_key=True)

                new_link.set_from_node(prev_from_node)
                new_link.set_to_node(new_node)
                new_link.set_points(new_points_start)
                new_link.geometry = new_geometry_start


            # 그 밖에 공통적으로 copy해도 되는 attribute는 복사한다         
            new_link.max_speed = link.max_speed
            new_link.min_speed = link.min_speed
            new_link.speed_unit = link.speed_unit
            new_link.link_type = link.link_type

            new_link.road_id = link.road_id # 이걸 새로운 값으로 변경해주어야 한다
            new_link.ego_lane = link.ego_lane
            new_link.lane_change_dir = link.lane_change_dir
            new_link.hov = link.hov 

            
            self.updateMgeoIdWidget()
            Logger.log_info('divide_a_link is done successfully')
            return

        except BaseException as e:
            Logger.log_error('divide_a_link failed (traceback is down below) \n{}'.format(traceback.format_exc()))


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

            # 추가할 포인트 위치를 계산한다
            new_point = (link.points[point_idx] + link.points[point_idx + 1]) / 2.0

            # 이 포인트를 새로운 위치에 입력해야 한다
            new_point_list = np.vstack((link.points[:point_idx+1], new_point)) # 현재 포인트를 포함하도록
            new_point_list = np.vstack((new_point_list, link.points[point_idx+1:]))
            link.set_points(new_point_list)

            # geometry point의 경우, 현재 point보다 다음에 있으면 idx를 증가시켜준다
            for i in range(len(link.geometry)):
                pts = link.geometry[i]
                if pts['id'] > point_idx: #
                    link.geometry[i]['id'] += 1 

            self.updateMgeoIdWidget()
            Logger.log_info('add_link_point is done successfully')
            return

        except BaseException as e:
            Logger.log_error('add_link_point failed (traceback is down below) \n{}'.format(traceback.format_exc()))
            

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
                link = self.getLinkSet().lines[selected_item['id']]
                link.road_id = new_road_id
                Logger.log_info('set_new_road_id >> link: {} road_id changed to: {}'.format(link.idx, new_road_id))

            # Preliminary Road를 다시 생성한다.
            Logger.log_trace('set_new_road_id method will call create_prelimiary_odr_roads method automatically.')
            build_preliminary_road_callback()

            self.updateMgeoIdWidget()
            Logger.log_info('set_new_road_id is successfully done.')
            return

        except BaseException as e:
            Logger.log_error('set_new_road_id failed (traceback is down below) \n{}'.format(traceback.format_exc()))
         

    def delete_object_inside_xy_range(self):
        Logger.log_trace('Called: delete_object_inside_xy_range')
        try:
            result = QMessageBox.question(self, "Delete objects", 
                                'Delete objects inside the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]), 
                                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if result == QMessageBox.Ok:
                
                # 핵심 삭제 함수
                edit_mgeo_planner_map.delete_object_inside_xy_range(self.mgeo_planner_map, self.xlim, self.ylim)
                self.odr_data = OdrData() # 원본 MGeo가 변경되었으므로, OdrData는 초기화하여 사용자가 다시 만들게끔한다

                QMessageBox.information(self, "Delete complete", 'Delete objects inside the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]))
            self.updateMgeoIdWidget()
        except BaseException as e:
            Logger.log_error('delete_object_inside_xy_range failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def delete_objects_out_of_xy_range(self, hard):
        Logger.log_trace('Called: delete_objects_out_of_xy_range')
        try:
            result = QMessageBox.question(self, "Delete objects", 
                                'Delete objects out of the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]), 
                                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if result == QMessageBox.Ok:
                
                # 핵심 삭제 함수
                edit_mgeo_planner_map.delete_objects_out_of_xy_range(self.mgeo_planner_map, self.xlim, self.ylim, hard)
                self.odr_data = OdrData() # 원본 MGeo가 변경되었으므로, OdrData는 초기화하여 사용자가 다시 만들게끔한다
                
                QMessageBox.information(self, "Delete complete", 'Delete objects out of the range x = [{}, {}], y = [{}, {}]'.format(self.xlim[0], self.xlim[1], self.ylim[0], self.ylim[1]))
            self.updateMgeoIdWidget()
        except BaseException as e:
            Logger.log_error('delete_objects_out_of_xy_range failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def updateXLimYLim(self):
        """QOpenGLWidget에 그려진 OpenGL의 좌표의 범위를 Widget 아래 Text로 출력한다"""
        
        # OpenGL 좌표를 구하기 위해 Z=0에 투명한 평면의 Object를 그려준다
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_FRONT_AND_BACK)
        glEnable(GL_BLEND)
        glBegin(GL_POLYGON)
        glColor4f(0, 0, 0, 0)
        
        glVertex3f(-10000, -10000, 0)
        glVertex3f(-10000, 10000, 0)
        glVertex3f(10000, 10000, 0)
        glVertex3f(10000, -10000, 0)
        
        glVertex3f(0, -10000, -10000)
        glVertex3f(0, -10000, 10000)
        glVertex3f(0, 10000, 10000)
        glVertex3f(0, 10000, -10000)

        glVertex3f(-10000, 0, -10000)
        glVertex3f(-10000, 0, 10000)
        glVertex3f(10000, 0, 10000)
        glVertex3f(10000, 0, -10000)

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

        self.xlim = [math.floor(right_bottom[0]), math.floor(left_top[0])]
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


    # find 관련 함수
    def mgeoIdDoubleClickEvent(self):
        """Mgeo Id를 더블클릭하면 해당 Item으로 이동한다"""
        if self.find_item is not None:
            self.trans_point_by_id(self.find_item)


    def find_by_mgeo_id(self):
        Logger.log_trace('Called: action_input_mgeo_id')
        find_id, okPressed = QInputDialog.getText(self, "Find", "Enter ID", QLineEdit.Normal, '')

        if okPressed and find_id != '':

            if next((item for item in self.getNodeSet().nodes if item == find_id), False):
                self.highlight_mgeo_item(MGeoItem.NODE, find_id)
                self.trans_point_by_id(self.find_item)
            elif next((item for item in self.getLinkSet().lines if item == find_id), False):
                self.highlight_mgeo_item(MGeoItem.LINK, find_id)
                self.trans_point_by_id(self.find_item)
            elif next((item for item in self.getTSSet().signals if item == find_id), False):
                self.highlight_mgeo_item(MGeoItem.TRAFFIC_SIGN, find_id)
                self.trans_point_by_id(self.find_item)
            elif next((item for item in self.getTLSet().signals if item == find_id), False):
                self.highlight_mgeo_item(MGeoItem.TRAFFIC_LIGHT, find_id)
                self.trans_point_by_id(self.find_item)
            elif next((item for item in self.getJunctionSet().junctions if item == find_id), False):
                self.highlight_mgeo_item(MGeoItem.JUNCTION, find_id)
                self.trans_point_by_id(self.find_item)
            elif next((item for item in self.getRoadSet() if item == find_id), False):
                self.highlight_mgeo_item(MGeoItem.ROAD, find_id)
                self.trans_point_by_id(self.find_item)
            else:
                QMessageBox.warning(self, "Value Error", "Enter the id included in Mgeo.")


    def action_input_mgeo_id(self, item):
        """상단 Menu에서 Mgeo Id를 입력하면 해당 Item을 하이라이트한다"""
        Logger.log_trace('Called: action_input_mgeo_id')
        try:   
            # if self.find_item is not None:
            #     self.list_highlight1.remove(self.find_item)
            if item == 'Node':
                type = MGeoItem.NODE
                map = self.node_map.values()
            elif item == 'Link':
                type = MGeoItem.LINK
                map = self.line_map.values()
            elif item == 'Traffic Sign':
                type = MGeoItem.TRAFFIC_SIGN
                map = self.ts_map.values()
            elif item == 'Traffic Light':
                type = MGeoItem.TRAFFIC_LIGHT
                map = self.tl_map.values()
            elif item == 'Junction':
                type = MGeoItem.JUNCTION
                map = self.jc_map.values()
            elif item == 'Road':
                type = MGeoItem.ROAD
                map = self.road_map.values()

            find_id, okPressed = QInputDialog.getText(self, "Find", "Enter {} ID".format(type.name), QLineEdit.Normal, '')
            if okPressed and find_id != '':
                if find_id in map:
                    self.highlight_mgeo_item(type, find_id)
                    self.trans_point_by_id(self.find_item)
                else:
                    QMessageBox.warning(self, "Value Error", "Enter the id included in {}.".format(type.name))

        except BaseException as e:
            Logger.log_error('action_input_mgeo_id failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def highlight_mgeo_item(self, type, id):
        """Find한 Mgeo 데이터 Highlight 및 속성 Set"""
        if self.find_item is not None:
            if self.find_item in self.list_highlight1:
                self.list_highlight1.remove(self.find_item)
        self.find_item = {'type': type, 'id': id}
        self.list_highlight1.append(self.find_item)
        

    def trans_point_by_id(self, item):
        """Find한 Mgeo 데이터 위치로 이동한다"""
        if item['type'] == MGeoItem.NODE:
            get_point = self.getNodeSet().nodes[item['id']].point
        elif item['type'] == MGeoItem.LINK:
            lines_point = self.getLinkSet().lines[item['id']].points
            get_point = lines_point[round(len(lines_point)/3)]
        elif item['type'] == MGeoItem.TRAFFIC_SIGN:
            get_point = self.getTSSet().signals[item['id']].point
        elif item['type'] == MGeoItem.TRAFFIC_LIGHT:
            get_point = self.getTLSet().signals[item['id']].point
        elif item['type'] == MGeoItem.JUNCTION:
            get_point = self.getJunctionSet().junctions[item['id']].get_jc_node_points()[0]
        elif item['type'] == MGeoItem.ROAD:
            road = self.getRoadSet().get(item['id'])
            
            if len(road.ref_line) > 0:
                # ref line이 설정되어 있으면 ref_line을 기준으로 road를 찾는다
                road_line_point = road.ref_line[0].points
                get_point = road_line_point[round(len(road_line_point)/3)]

            else:
                # ref line이 설정되어 있지 않으면 link_list_not_organized를 바탕으로 계산
                if len(road.link_list_not_organized) == 0:
                    Logger.log_error('Selected road does not contain any link. Cannot visualize this road.')
                    return
                
                road_line_point = road.link_list_not_organized[0].points
                get_point = road_line_point[round(len(road_line_point)/3)]
            
        self.xTran = - get_point[0]
        self.yTran = - get_point[1]
        self.update()

    
    def create_poly3_points_with_uniform_step(self, link, point_step, point_type='paramPoly3', end_condition=1):
        """
        end_condition: 링크의 마지막 포인트에 geometry가 들어가면 안 된다.
        """
        link_points_num = len(link.points)

        # 생성할 포인트 수: 1을 빼는 이유는 이미 시작 위치에 생성된 것이 하나 있기 때문
        num_points_gen = int(np.floor(link_points_num / point_step) - 1)

        # 끝 값에서 에러를 방지하기 위해 다음을 사용
        last_idx = len(link.points) - 1
        

        if point_type == 'poly3':
            link.geometry[0] = {'id': 0, 'method': 'poly3'}
        if point_type == 'paramPoly3':
            link.geometry[0] = {'id': 0, 'method': 'paramPoly3'}
            
        for i in range(num_points_gen):
            # 이번 시점에 추가할 geometry 위치
            point_idx = (i + 1) * point_step # 예: 3, 6, 9, ...

            # 마지막 인덱스가 15라고 하면, 3, 6, 9, 12, 15 << 15는 포함되면 안 된다!
            # end_condition이 디폴트인 1이라고 하면, point_idx가 14일 때까지 허용된다.
            # 즉, 2, 4, 6, ... 14 이런식으로 채워졌을 때, 14가 허용이 되는 것.
            if last_idx - point_idx < end_condition:
                return
            else:
                is_ex = next((item for item in link.geometry if item['id'] == point_idx), None)
                if is_ex is None:
                    link.geometry.append({'id': point_idx, 'method': point_type})
                else:
                    is_ex['method'] = point_type
                # if point_type == 'poly3':
                #     link.geometry.append({'id': point_idx, 'method': 'poly3'})
                # elif point_type == 'paramPoly3':
                #     link.geometry.append({'id': point_idx, 'method': 'paramPoly3'})



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
                Logger.log_info('Point type not selected, create_geometry_points_auto cancelled.')
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
                        self.create_poly3_points_with_uniform_step(link, point_step, point_type=type, end_condition=1)

                Logger.log_info('create_geometry_points_auto completed successfully.')
            elif type == 'paramPoly3':
                # paramPoly3 requires 4 points for each vector
                if len(self.odr_data.roads) < 1:
                    Logger.log_warning('OpenDRIVE Conversion >> Create Roads must be performed before using the auto-generate function')
                    return

                point_step = 4 - slice_offset # paramPoly3 works best with 4 points
                for road_idx, road in self.odr_data.roads.items():
                    for link in road.ref_line:
                        self.create_poly3_points_with_uniform_step(link, point_step, point_type=type)

                Logger.log_info('create_geometry_points_auto completed successfully.')
            else:
                Logger.log_info('Point type not selected, create_geometry_points_auto cancelled.')
                return

        except BaseException as e:
                Logger.log_error('create_geometry_points_auto failed (traceback below) \n{}'.format(traceback.format_exc()))
            
        # geometry_point_dist = 30
        
        # for road_idx, road in self.odr_data.roads.items():
        #     for link in road.ref_line:
        #         total_dist = link.get_total_distance()
                
        #         # 생성할 포인트 수: 1을 빼는 이유는 이미 시작 위치에 생성된 것이 하나 있기 때문
        #         num_points_gen = int(np.floor(total_dist / geometry_point_dist) - 1)

        #         if num_points_gen < 1:
        #             continue

        #         # 얼마 마다 포인트를 생성할 것인가를 결정
        #         point_step = int(np.floor(len(link.points) / num_points_gen))
        #         if point_step <= 2: # point step이 2보다 작으면, 그냥 늘린다
        #             point_step = 3

        #         for i in range(num_points_gen):
        #             point_idx = (i+1) * point_step
                    
        #             # point_step을 마음대로 조절하였고, 끝 값에서 에러를 방지하기 위해
        #             # 다음을 사용한다
        #             last_idx = len(link.points) - 1
        #             if last_idx - point_idx < 2:
        #                 # 원래 break 하면 되는데, break 하면 전체를 종료할것같아서 우선 이렇게 함  
        #                 Logger.log_debug('')
        #             else:
        #                 link.geometry.append( {'id': point_idx, 'method': 'poly3'})


    def change_all_item_id_to_string(self):
        Logger.log_trace('Called: change_all_item_id_to_string')
        try:
            error_fix.change_all_item_id_to_string(self.mgeo_planner_map)
            
            Logger.log_info('change_all_item_id_to_string is done successfully.')
            
        except BaseException as e:
            Logger.log_error('change_all_item_id_to_string failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def change_node_link_height_to_0(self):
        Logger.log_trace('Called: change_node_link_height_to_0')
        try:
            node_set = self.getNodeSet()
            link_set = self.getLinkSet()

            for node in node_set.nodes.values():
                node.point[2] = 0

            for link in link_set.lines.values():
                for point in link.points:
                    point[2] = 0
            
            Logger.log_info('change_node_link_height_to_0 is done successfully.')
            
        except BaseException as e:
            Logger.log_error('change_node_link_height_to_0 failed (traceback is down below) \n{}'.format(traceback.format_exc()))



    def get_position_in_carla_node(self):
        Logger.log_trace('Called: get_get_position_in_carla')
        try:
            # REFACTOR(sglee) : refactor this into edit_link or somewhere
            self.temp_workaround_remove_none_item_in_list_sp()

            # 현재 선택된 아이템이 line이고, 2개일 때만 동작한다.
            if len(self.list_sp) != 1:
                Logger.log_info('Invalid operation: get_get_position_in_carla works only when one node is selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            selected_item = self.list_sp[0]
            if selected_item['type'] != MGeoItem.NODE:
                Logger.log_info('Invalid operation: get_get_position_in_carla works only when one node is selected ({} type data is currently selected)'.format(selected_item['type']))
                return

            node = self.getNodeSet().nodes[self.list_sp[0]['id']]

            Logger.log_info('Node Position: [{:.2f}, {:.2f}, {:.2f}]'.format(node.point[0], node.point[1], node.point[2]))
            return

        except BaseException as e:
            Logger.log_error('get_get_position_in_carla failed (traceback is down below) \n{}'.format(traceback.format_exc()))
    
    
    def get_position_in_carla_link(self):
        Logger.log_trace('Called: get_get_position_in_carla')
        try:
            # REFACTOR(sglee) : refactor this into edit_link or somewhere
            self.temp_workaround_remove_none_item_in_list_sp()

            # 현재 선택된 아이템이 line이고, 2개일 때만 동작한다.
            if len(self.list_sp) != 1:
                Logger.log_info('Invalid operation: get_get_position_in_carla works only when one link is selected (# of selected items: {})'.format(len(self.list_sp)))
                return

            selected_item = self.list_sp[0]
            if selected_item['type'] != MGeoItem.LINK:
                Logger.log_info('Invalid operation: get_get_position_in_carla works only when one link is selected ({} type data is currently selected)'.format(selected_item['type']))
                return

            link = self.getLinkSet().lines[self.list_sp[0]['id']]
            point0 = link.points[0]
            point1 = link.points[1]
            sim_xyz0 = np.array([point0[0], -1 * point0[1], point0[2]])
            sim_xyz1 = np.array([point1[0], -1 * point1[1], point1[2]])
            
            
            vect = sim_xyz1 - sim_xyz0     
            heading = np.arctan2(vect[1], vect[0]) * 180.0 / np.pi

            Logger.log_info('X,Y,Z,Heading: [{:.2f}, {:.2f}, {:.2f}, {:.2f}] (in CARLA)'.format(
                sim_xyz0[0], sim_xyz0[1], sim_xyz0[2], heading))
            return

        except BaseException as e:
            Logger.log_error('get_get_position_in_carla failed (traceback is down below) \n{}'.format(traceback.format_exc()))


    def get_position_in_inlink_point(self):
        Logger.log_trace('Called: get_position_in_inlink_point')
        try:
            # REFACTOR(sglee) : refactor this into edit_link or somewhere
            self.temp_workaround_remove_none_item_in_list_sp()

            # inner_link_point_ptr이 reset 되어 있다면 리턴
            if self.inner_link_point_ptr['link'] is None:
                Logger.log_info('Invalid operation: get_position_in_inlink_point works only when inlink point is selected')
                return

            link = self.inner_link_point_ptr['link']
            point_idx = self.inner_link_point_ptr['point_idx']

            if point_idx + 1 > len(link.points) - 1:
                # 마지막 index 보다 크면 (접근 불가인 경우)
                point0 = link.points[point_idx - 1]
                point1 = link.points[point_idx]
            else:
                point0 = link.points[point_idx]
                point1 = link.points[point_idx + 1]

            sim_xyz0 = np.array([point0[0], -1 * point0[1], point0[2]])
            sim_xyz1 = np.array([point1[0], -1 * point1[1], point1[2]])
            
            vect = sim_xyz1 - sim_xyz0     
            heading = np.arctan2(vect[1], vect[0]) * 180.0 / np.pi

            Logger.log_info('X,Y,Z,Heading: [{:.2f}, {:.2f}, {:.2f}, {:.2f}] (in CARLA)'.format(
                sim_xyz0[0], sim_xyz0[1], sim_xyz0[2], heading))
            return

        except BaseException as e:
            Logger.log_error('get_position_in_inlink_point failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    def auto_fix_traffic_light_conn_link(self):
        tl_set = self.getTLSet().signals
        link_set = self.getLinkSet().lines
        
        for tl in tl_set:
            tl_links = tl_set[tl].link_list
            new_tl_links = []
            new_tl_links_id = []
            for tl_link in tl_links:
                next_links = tl_link.to_node.to_links
                for next_link in next_links:
                    new_tl_links.append(next_link)
                    new_tl_links_id.append(next_link.idx)

            edit_signal.update_signal(tl_set, link_set, tl_set[tl], 'link_id_list', tl_set[tl].link_id_list, new_tl_links_id)
            edit_signal.update_signal(tl_set, link_set, tl_set[tl], 'link_list', tl_set[tl].link_list, new_tl_links)
    # 940      
    def auto_set_junction(self):
        node_set = self.getNodeSet().nodes
        link_set = self.getLinkSet().lines
        road_set = self.getRoadSet()
        junction_set = self.getJunctionSet()

        for road_id in road_set:
            road_object = road_set[road_id]
            if road_id == '786':
                print(786)

            road_start_nodes = road_object.get_frontmost_nodes()
            road_end_nodes = road_object.get_rearmost_nodes()

            
            prev_road = []
            for snode in road_start_nodes:
                sflinks = snode.from_links
                for sfl in sflinks:
                    if sfl.road_id not in prev_road:
                        prev_road.append(sfl.road_id)
            if len(prev_road) > 1:
                self.create_junction_temp_version(junction_set, road_set, prev_road, road_start_nodes)


            next_road = []
            for enode in road_end_nodes:
                etlinks = enode.to_links
                for etl in etlinks:
                    if etl.road_id not in next_road:
                        next_road.append(etl.road_id)
            if len(next_road) > 1:
                self.create_junction_temp_version(junction_set, road_set, next_road, road_end_nodes)


    def create_junction_temp_version(self, junction_set, road_set, road, nodes):

        in_junction_from = []
        in_junction_to = []
        junction_nodes = []

        for road_id in road:
            other_road = road_set[road_id]
            other_road_start_nodes = other_road.get_frontmost_nodes()
            other_road_end_nodes = other_road.get_rearmost_nodes()

            # 기존 정션 검사
            for node in other_road_start_nodes:
                for i in node.junctions:
                    if i not in in_junction_from:
                        in_junction_from.append(i.idx)

                for link in node.to_links:
                    for i in link.to_node.junctions:
                        if i not in in_junction_to:
                            in_junction_to.append(i.idx)
                    

            for node in other_road_end_nodes:
                for i in node.junctions:
                    if i not in in_junction_to:
                        in_junction_to.append(i.idx)

                for link in node.from_links:
                    for i in link.from_node.junctions:
                        if i not in in_junction_from:
                            in_junction_from.append(i.idx)

            # 연결된 정션 있으면
            junction_id = None
            for one_junction in in_junction_from:
                for two_junction in in_junction_to:
                    if one_junction == two_junction:
                        junction_id = one_junction
                        break
            
            # 정션 만들기
            junction_nodes.extend(other_road_start_nodes)
            junction_nodes.extend(other_road_end_nodes)
            
            if junction_id is None:
                jct = Junction()
                for j_node in junction_nodes:
                    jct.add_jc_node(j_node)

                junction_set.append_junction(jct, create_new_key=True)
            else:
                jct = junction_set.junctions[junction_id]
                for j_node in junction_nodes:
                    jct.add_jc_node(j_node)
            
            


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
        # print("Accpet", self.new_idx)
        return self.new_idx