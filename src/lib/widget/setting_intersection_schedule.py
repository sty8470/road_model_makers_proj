from PyQt5.QtCore import pyqtSlot, Qt, QPoint
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QOpenGLWidget
from PyQt5.QtGui import *
from PyQt5.Qt import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import sys
from ast import literal_eval
import itertools
import numpy as np

from proj_mgeo_editor_morai_opengl.GUI.opengl_draw_line import *
from lib.common.polygon_util import calculate_centroid, minimum_bounding_rectangle
from proj_mgeo_editor_morai_opengl.GUI.opengl_draw_point import loadPointList, loadTLList
from proj_mgeo_editor_morai_opengl.GUI.opengl_draw_polygon import load_crosswalk_List
from proj_mgeo_editor_morai_opengl.GUI.load_mgeo_id import *

class DrawIntTLCtrl(QOpenGLWidget):
    def  __init__(self, zoom_factor=None, draw_item=None, mgeo=None, center_point=None):
        super(DrawIntTLCtrl, self).__init__()
        self.draw_item = draw_item
        self.center_point = center_point
        self.mgeo = mgeo
        self.zoom_factor = zoom_factor
        self.select_item = []
        self.select_tl_list = None
        self.select_tl_color = None
        self.zoom = -zoom_factor
        self.lastPos = QPoint()
        self._id = None
        self.cross_walks = {}

        self.red_color = [1, 0, 0] 
        self.yellow_color = [1, 1, 0] 
        self.green_color = [7/255, 112/255, 3/255]
        self.highlight_color = [220/255, 240/255, 0]

        self.projection = glGetDoublev(GL_PROJECTION_MATRIX)
        self.modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)
 
    def initializeGL(self):
        glPolygonMode(GL_FRONT, GL_FILL)
        glPolygonMode(GL_BACK, GL_FILL)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClearDepth(1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
 
    def resizeGL(self, width, height):
        glGetError()
        aspect = width if (height == 0) else width / height
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, aspect, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
 
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glPushMatrix()
        glTranslatef(-self.center_point[0], -self.center_point[1], self.zoom)
        self.projection = glGetDoublev(GL_PROJECTION_MATRIX)
        self.modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.viewport = glGetIntegerv(GL_VIEWPORT)

        if self._id is not None:
            self.highlight_select_item(self._id)

        if self.select_tl_list is not None and self._id is None:
            color = [220/255, 240/255, 0]
            if self.select_tl_color is not None:
                signal_color = self.re_convert_tl(self.select_tl_color)
                if len(signal_color) == 1 and signal_color[0] == 'red':
                    color = self.red_color
                elif len(signal_color) == 1 and signal_color[0] == 'yellow':
                    color = self.yellow_color
                else:
                    color = self.green_color
            else:
                color = self.highlight_color

            for _tl_id in self.select_tl_list:
                self.highlight_select_item(_tl_id, color)
                
        self.draw_mgeo()
        glPopMatrix()
        glFlush()
        self.update()
    
    def wheelEvent(self, event):
        wheel_val = event.angleDelta().y()
        self.setZoom(self.zoom, 0.1 * (wheel_val*10/12))
 
    def setZoom(self, zoom, delta):
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
        self.zoom = zoom + delta 
        
    def mousePressEvent(self, event):
        self.lastPos = event.pos()
        self.makeCurrent()
        if event.buttons() == Qt.LeftButton:
            self.mouseClickWindow(event.x(), event.y())
        self.doneCurrent()
        
    def mouseClickWindow(self, x, y):
        tl_list = self.draw_item
        winX = x
        winY = self.viewport[3] - y
        winZ = glReadPixels(winX, int(winY), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT)
        select_point = gluUnProject(winX, winY, winZ, self.modelview, self.projection, self.viewport)
        
        self._id = self.dist_point_to_point(tl_list.TL_dict, select_point)
            
    def highlight_select_item(self, _id, color=None):
        tl_list = self.draw_item
        if _id is not None:
            if self.select_tl_color is None:
                color = self.highlight_color
            select_item = tl_list.TL_dict[_id]
            self.plot_points([select_item.point], color=color, alpha=1, size=8)
            if select_item.type == 'pedestrian':
                if select_item.ref_crosswalk_id in self.cross_walks:
                    scw_list = self.cross_walks[select_item.ref_crosswalk_id].single_crosswalk_list
                    for scw in scw_list:
                        self.plot_plane(scw.points, color=color, alpha=0.5)
            else:
                for _link in select_item.link_list:
                    self.plot_link_color(_link.points, color=color, alpha=1, width=5, arrow=False)

    def dist_point_to_point(self, items, select_point):
        min_dist = 2
        min_dist_id = None
        self.center_point
        for item in items:
            dist = np.sqrt(sum(((items[item].point[0:2]-select_point[0:2])**2)))
            if min_dist > dist:
                min_dist_id = item
                min_dist = dist
        if min_dist >= 3:
            return
        return min_dist_id

    
    def draw_mgeo(self):
        tl_list = self.draw_item
        draw_link_list = {}
        tl_set = self.mgeo.light_set.signals
        # tl_list.TL_dict
        lines = {}
        nodes = {}
        self.cross_walks = {}
        for tls in tl_list.TL:
            draw_link_list[tls[0]] = []
            for tl in tls:
                if tl_set[tl].type != 'pedestrian':
                    for one_link in tl_set[tl].link_list:
                        if one_link not in draw_link_list[tls[0]]:
                            draw_link_list[tls[0]].append(one_link)
                    # draw_link_list[tl] = tl_set[tl].link_list
                    for i, link_id in enumerate(tl_set[tl].link_id_list):
                        lines[link_id] = tl_set[tl].link_list[i]
                    # break
        _color = 0
        
        # 1. Get all the links close to link that are in one links 
        for link_id, link_obj in list(lines.items()):
            # Get from node --> from link
            for link in link_obj.from_node.from_links:
                lines[link.idx] = link

            for link in link_obj.to_node.to_links:
                lines[link.idx] = link
        
        self.draw_line_list = basicLineList(lines, color=[0, 0, 0], width=1, lane_change=False)
        
        # 2. Nodes
        for link_id, link_obj in list(lines.items()):
            nodes[link_obj.from_node.idx] = link_obj.from_node
            nodes[link_obj.to_node.idx] = link_obj.to_node 

        self.draw_node_list = loadPointList(nodes, color=[0, 0, 0], size=7)

        # 3. Crosswalks
        # if len(self.mgeo.cw_set.data) == 0 or len(self.mgeo.scw_set.data) == 0:
        #     Logger.log_warning('Cannot draw the crosswalk or single crosswalk')
            
        for tl_id, tl_obj in tl_list.TL_dict.items():
            if tl_obj.ref_crosswalk_id == '':
                continue
            else:
                for cw_id, cw_obj in self.mgeo.cw_set.data.items():
                    if tl_obj.ref_crosswalk_id == cw_id:
                        self.cross_walks[cw_id] = cw_obj
        
        cross_walk_color = [0.8, 0.5, 0.7]
        self.cw_draw_list = load_crosswalk_List(self.cross_walks, cross_walk_color, z_axis=-0.1)
        
        # 4. Get all traffic light and pedestrian light
        tl_color = [0.4, 0.4, 1.0]
        ped_tl_color = [0, 0.8, 0.2]
        self.tl_draw_list = loadTLList(tl_list.TL_dict, 
                                       traffic_color=tl_color,
                                       pedestrian_color=ped_tl_color,
                                       size=7)
        
        new_tl_id_list = {}
        new_ped_tl_id_list = {}
        for tl_id, tl_obj in tl_list.TL_dict.items():
            if tl_obj.type == 'car':
                new_tl_id_list[tl_id] = tl_obj
            else:
                new_ped_tl_id_list[tl_id] = tl_obj
        
        self.tl_id_list = point_id_list(new_tl_id_list, color=tl_color)
        self.ped_tl_id_list = point_id_list(new_ped_tl_id_list, color=ped_tl_color)
        self.draw_links()
        self.draw_nodes()
        self.draw_cross_walks()
        self.draw_tls()
        self.draw_tl_id()
        
        # Table Action
        for tl_id, draw_links in draw_link_list.items():
            if len(self.select_item) != len(tl_list.TL):
                continue
            else:
                # 여기 수정하기
                signal_list = self.re_convert_tl(self.select_item[_color])
                related_signal = []
                if len(signal_list) == 1 and signal_list[0] == 'red':
                    color = self.red_color
                elif len(signal_list) == 1 and signal_list[0] == 'yellow':
                    color = self.yellow_color
                else:
                    color = self.green_color
                    related_signal += signal_list
                # 신호등 하이라이트
                signal_list = next((item for item in tl_list.TL if tl_id in item), None)
                if signal_list is not None and len(signal_list) != 0:
                    if color == self.green_color:
                        for signal_id in signal_list:
                            signal_item = self.mgeo.light_set.signals[signal_id]
                            self.plot_points([signal_item.point], color=color, alpha=0.5, size=7)
                for draw_link in draw_links:
                    if len(related_signal) == 0:
                        self.plot_link_color(draw_link.points, color=color, alpha=0.5, width=10, arrow=True)
                    else:
                        if draw_link.related_signal in related_signal:
                            self.plot_link_color(draw_link.points, color=color, alpha=0.5, width=10, arrow=True)

            _color += 1
            
    def draw_nodes(self):
        glPushMatrix()
        glCallList(self.draw_node_list)
        glPopMatrix()
    
    def draw_links(self):
        glPushMatrix()
        glCallList(self.draw_line_list)
        glPopMatrix()

    def draw_cross_walks(self):
        glPushMatrix()
        glCallList(self.cw_draw_list)
        glPopMatrix()
    
    def draw_tls(self):
        glPushMatrix()
        glCallList(self.tl_draw_list)
        glPopMatrix()
        
    def draw_tl_id(self):
        glPushMatrix()
        glCallList(self.tl_id_list)
        glCallList(self.ped_tl_id_list)
        glPopMatrix()
        
    def plot_points(self, points, color=[0, 0, 0], alpha=1, size=1.0):
        glColor4f(color[0], color[1], color[2], alpha)
        glPointSize(size)
        self.paint_points(points)
    
    def plot_link(self, points, color=[0, 0, 0], alpha=1, width=1.0):
        glColor4f(color[0], color[1], color[2], alpha)
        glLineWidth(width)
        self.paint_line(points)

    def plot_plane(self, points, color=[0, 0, 0], alpha=1):
        glColor4f(color[0], color[1], color[2], alpha)
        self.paint_plane(points)
        
    def plot_link_color(self, points, color=[0, 0, 0], alpha=1, width=10.0, arrow=False):
        glColor4f(color[0], color[1], color[2], alpha)
        glLineWidth(width)
        self.paint_line(points, arrow=arrow)
        if arrow is False:
            glPointSize(2)
            self.paint_points(points)

    
    def paint_points(self, points):
        glBegin(GL_POINTS)
        for point in points:
            glVertex3f(point[0], point[1], point[2])
        glEnd()
    
    def paint_line(self, points, arrow=None):
        glBegin(GL_LINES)
        for i in range(len(points)-1):
            glVertex3f(points[i][0], points[i][1], points[i][2])
            glVertex3f(points[i+1][0], points[i+1][1], points[i+1][2])
        glEnd()
        # 하이라이트 라인에 화살표 방향 표시
        if arrow:
            glBegin(GL_TRIANGLES)
            vect = points[-1]-points[-2]
            vect = vect / np.linalg.norm(vect, ord=2)
            pos_vect_ccw = self.rorate_around_z_axis(np.pi/2, vect)*1.5
            pos_vect_cw = self.rorate_around_z_axis(-np.pi/2, vect)*1.5
            up = (points[-1] + pos_vect_ccw).tolist()
            dn = (points[-1] + pos_vect_cw).tolist()

            glVertex3f(points[-1][0]+vect[0]*2, points[-1][1]+vect[1]*2, points[-1][2])
            glVertex3f(up[0], up[1], up[2])
            glVertex3f(dn[0], dn[1], dn[2])
            glEnd()

    def paint_plane(self, points):
        glBegin(GL_POLYGON)
        for i in points:
            glVertex3f(i[0], i[1], i[2])
        glEnd()


    def rorate_around_z_axis(self, angle, point):
        rotation = np.array([
            [np.cos(angle), -np.sin(angle), 0.0],
            [np.sin(angle),  np.cos(angle), 0.0],
            [0.0, 0.0, 1.0]])

        transform_pt = rotation.dot(point)
        return transform_pt


    def re_convert_tl(self, light):
        # traffic_light color
        # R, Y, SG, LG, RG, UTG, ULG, URG, LLG, LRG
        # R_with_Y, Y_with_G, Y_with_GLeft, G_with_GLeft, R_with_GLeft
        # LLG_SG, R_LLG, ULG_URG
        # None, Undefined, Not_detected
        light_list = {
            'R' : ['red'],
            'Y' : ['yellow'],
            'SG' : ['straight', 'left_unprotected', 'right_unprotected'],
            'LG' : ['left', 'left_unprotected', 'uturn_normal'],
            'RG' : ['right', 'right_unprotected'],
            'UTG' : ['uturn'],
            'ULG' : ['upperleft'],
            'URG' : ['upperright'],
            'LLG' : ['lowerleft'],
            'LRG' : ['lowerright'],
            'R_with_Y' : ['red', 'yellow'],
            'Y_with_G' : ['yellow', 'straight', 'left_unprotected', 'right_unprotected'],
            'Y_with_GLeft' : ['yellow', 'left', 'left_unprotected', 'uturn_normal'],
            'G_with_GLeft' : ['straight', 'left', 'left_unprotected',  'right_unprotected', 'uturn_normal'],
            'R_with_GLeft' : ['red', 'left', 'left_unprotected', 'uturn_normal'],
            'LLG_SG' : ['upperleft', 'straight', 'left_unprotected', 'right_unprotected'],
            'R_LLG' : ['red', 'lowerleft'],
            'ULG_URG' : ['upperleft', 'upperright'],
            'Undefined' : ['red']
        }

        return light_list[light]
            

class SettingIntersectionSchedule(QDialog):
    def __init__(self, mgeo, sp):
        super().__init__()
        self.draw_gl = None
        self.mgeo = mgeo
        self.sp = sp
        self._width = 480
        self._height = 360
        self.int_item = mgeo.intersection_controller_set.intersection_controllers[self.sp['id']]
        try:
            self.center_point = calculate_centroid(self.int_item.get_intersection_controller_points())
            rectangle_box = minimum_bounding_rectangle(self.int_item.get_intersection_controller_points())
            self.zoom_factor = self.calculate_zoom_factor(rectangle_box)
        except:
            self.zoom_factor = -50
            
        _idx = self.sp['id']
        if mgeo.intersection_state_list is None:
            mgeo.intersection_state_list = dict()

        self.int_schedule = {'idx' : _idx, 'TLState' : [], 'yelloduration' : [], 'PSState' : []}
        
        if _idx in mgeo.intersection_state_list:
            self.int_schedule['TLState'] = mgeo.intersection_state_list[_idx]['TLState'][:]
            self.int_schedule['yelloduration'] = mgeo.intersection_state_list[_idx]['yelloduration'][:]
            self.int_schedule['PSState'] = mgeo.intersection_state_list[_idx]['PSState'][:]
        self.initUI()



    def initUI(self):
        # traffic_light color
        # R, Y, SG, LG, RG, UTG, ULG, URG, LLG, LRG
        # R_with_Y, Y_with_G, Y_with_GLeft, G_with_GLeft, R_with_GLeft
        # LLG_SG, R_LLG, ULG_URG
        # None, Undefined, Not_detected

        # Set Window Size on OpenGL Widget
        self.draw_gl = DrawIntTLCtrl(zoom_factor=self.zoom_factor, draw_item=self.int_item, mgeo=self.mgeo, center_point=self.center_point)
        self.draw_gl.setMinimumSize(self._width, self._height)
        
        main_layout = QHBoxLayout()

        split_data = QSplitter()
        split_data.setOrientation(Qt.Horizontal)
        split_data.addWidget(self.draw_gl)
        split_data.addWidget(self.set_tl_table_widget())

        main_layout.addWidget(split_data)
        self.setLayout(main_layout)
        # self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Set Intersection State")
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint) | Qt.WindowFlags(Qt.WindowMaximizeButtonHint))
    
    def set_tl_table_widget(self):
        main_widget = QGroupBox('')
        main_widget.setMinimumWidth(600)
        self.tl_table = QTableWidget()
        self.tl_table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.traffic_light_update_table_widget()

        self.tl_table.cellClicked.connect(self.tl_cell_click_highlight_opengl)
        self.tl_table.cellDoubleClicked.connect(self.tl_cell_double_click_update_state)
        self.tl_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Main Layout for main widget
        vbox = QVBoxLayout()
        vbox.addWidget(self.tl_table)

        grid = QGridLayout()
        vbox.addLayout(grid)
        
        append_state = QPushButton("Add State")
        grid.addWidget(append_state, 0, 0)
        delete_state = QPushButton("Delete State")
        grid.addWidget(delete_state, 0, 1)
        # delete_all_state = QPushButton("Delete All State")
        # grid.addWidget(delete_all_state, 0, 2)

        # 보행자 신호등
        self.ps_table = QTableWidget()
        self.ps_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.pedestrian_update_table_widget()
        vbox.addWidget(self.ps_table)

        self.ps_table.cellClicked.connect(self.ps_cell_click_highlight_opengl)
        self.ps_table.cellChanged.connect(self.ps_item_pressed_change_value)

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        vbox.addWidget(self.buttonbox)
        append_state.clicked.connect(self.__append_state)
        delete_state.clicked.connect(self.__delete_state)
        # delete_all_state.clicked.connect(self.__clear_contents)
        main_widget.setLayout(vbox)
        return main_widget


    def traffic_light_update_table_widget(self):

        # default value synced_traffic_light_set count
        column_header = self.int_item.TL
        columncount = len(column_header)
        self.tl_table.setColumnCount(columncount+1)

        for i, ch in enumerate(column_header):
            header_item = QTableWidgetItem(str(ch))
            self.tl_table.setHorizontalHeaderItem(i, header_item)

        duration_item = QTableWidgetItem("duration")
        self.tl_table.setHorizontalHeaderItem(columncount, duration_item)
        self.tl_table.setColumnWidth(columncount, 60)


        if len(self.int_schedule['TLState']) > 0:
            self.tl_table.setRowCount(len(self.int_schedule['TLState']))
            le_state = self.int_schedule['TLState']
            for r, state in enumerate(le_state):
                vheader_item =  QTableWidgetItem('state {}'.format(r))
                self.tl_table.setVerticalHeaderItem(r, vheader_item)
                lightcolor = state['lightcolor']
                for c, color in enumerate(lightcolor):
                    item = QTableWidgetItem(color)
                    if 'G' in color:
                        item.setForeground(QBrush(QColor(0, 128, 19)))
                    elif 'R' in color:
                        item.setForeground(QBrush(Qt.red))
                    self.tl_table.setItem(r, c, item)
                item = QTableWidgetItem(str(state['duration']))
                self.tl_table.setItem(r, columncount, item)
        # else:
        #     self.tl_table.setRowCount(columncount)
        #     for c in range(columncount):
        #         for r in range(columncount):
        #             item = QTableWidgetItem('R')
        #             item.setForeground(QBrush(Qt.red))
        #             self.tl_table.setItem(r, c, item)
        #     for r in range(columncount):
        #         item = QTableWidgetItem('30')
        #         self.tl_table.setItem(r, columncount, item)


    def pedestrian_update_table_widget(self):
        # 보행자 신호등이 연결되어 있지 않으면 pass
        # column_header = self.int_item.TL
        row_header = ['state', 'synced', 'delay', 'on', 'blink']
        self.ps_table.setRowCount(len(row_header))
        # self.ps_table.setColumnCount(len(self.int_item.TL))

        # row_count = self.tl_table.rowCount()
        # self.tl_table.setRowCount(row_count+1)

        for i, ch in enumerate(self.int_item.TL):
            had_ps = next((signal for signal in ch if self.mgeo.light_set.signals[signal].type == 'pedestrian'), False)
            if had_ps:
                col_count = self.ps_table.columnCount()
                self.ps_table.setColumnCount(col_count+1)
                header_item = QTableWidgetItem(str(ch))
                self.ps_table.setHorizontalHeaderItem(col_count, header_item)
        self.ps_table.setVerticalHeaderLabels(row_header)

        ps_state_all = self.int_schedule['PSState']
        if len(ps_state_all) > 0:
            # if 
            for indx, ps_state in enumerate(ps_state_all):
                state, sync, delay_time, on_time, blink_time = ps_state
                # sync -> header에 맞추기
                state_item = QTableWidgetItem(str(state))
                sync_item = QTableWidgetItem(str(sync))
                delay_time_item = QTableWidgetItem(str(delay_time))
                on_time_item = QTableWidgetItem(str(on_time))
                blink_time_item = QTableWidgetItem(str(blink_time))
                self.ps_table.setItem(0, indx, state_item)
                self.ps_table.setItem(1, indx, sync_item)
                self.ps_table.setItem(2, indx, delay_time_item)
                self.ps_table.setItem(3, indx, on_time_item)
                self.ps_table.setItem(4, indx, blink_time_item)
        else:
            for c in range(len(self.int_item.TL)):
                for r in range(len(row_header)):
                    if r == 1:
                        try:
                            item_str = str(self.int_item.TL.index(literal_eval(self.ps_table.horizontalHeaderItem(c).text())))
                        except:
                            item_str = '0'
                        item = QTableWidgetItem(item_str)
                    else:
                        item = QTableWidgetItem('0')
                    self.ps_table.setItem(r, c, item)



    def calculate_zoom_factor(self, rect):
        offset = 20
        x_max = max(rect[np.arange(4)[:, None], 0])
        x_min = min(rect[np.arange(4)[:, None], 0])
        y_max = max(rect[np.arange(4)[:, None], 1])
        y_min = min(rect[np.arange(4)[:, None], 1])
        dist_x = abs(x_max - x_min) + offset
        dist_y = abs(y_max - y_min) + offset
        max_length = dist_x if dist_x >= dist_y else dist_y
        return float(max_length)
    
    def showDialog(self):
        return super().exec_()
    
    def accept(self):
        synced_header = self.tl_table.columnCount()
        synced_state = self.tl_table.rowCount()
        tl_state = self.int_schedule['TLState']
        for state_idx in range(synced_state):
            # 마지막 값은 duration
            if len(tl_state) < state_idx + 1:
                tl_state.append({'duration' : 0, 'lightcolor' : []})
            new_state_light = []
            for synced_ind in range(synced_header-1):
                new_state_light.append(self.tl_table.item(state_idx, synced_ind).text())
            tl_state[state_idx]['lightcolor'] = new_state_light
            try:
                duration_time = int(self.tl_table.item(state_idx, synced_header-1).text())
            except:
                duration_time = 30
            tl_state[state_idx]['duration'] = duration_time
        if len(self.int_schedule['yelloduration']) != len(self.int_item.TL):
            self.int_schedule['yelloduration'] = list([3]*len(self.int_item.TL))
        
        ps_header = self.ps_table.columnCount()
        ps_state = self.ps_table.rowCount()
        new_ps_state = []
        for sync_idx in range(ps_header):
            # 보행자 순서대로 저장
            new_state_light = []
            for state_ind in range(ps_state):
                new_state_light.append(int(self.ps_table.item(state_ind, sync_idx).text()))
            new_ps_state.append(new_state_light)
        self.int_schedule['PSState'] = new_ps_state
        self.mgeo.intersection_state_list[self.sp['id']] = self.int_schedule
        self.done(1)

    def reject(self):
        self.done(0)


    def convert_tl(self, lights):
        # traffic_light color
        # R, Y, SG, LG, RG, UTG, ULG, URG, LLG, LRG
        # R_with_Y, Y_with_G, Y_with_GLeft, G_with_GLeft, R_with_GLeft
        # LLG_SG, R_LLG, ULG_URG
        # None, Undefined, Not_detected
        light_list = {
            'red' : 'R',
            'yellow' : 'Y',
            'straight' : 'SG',
            'left' : 'LG',
            'right' : 'RG',
            'uturn' : 'UTG',
            'upperleft' : 'ULG',
            'upperright' : 'URG',
            'lowerleft' : 'LLG',
            'lowerright' : 'LRG'
        }
        if len(lights) == 1:
            return light_list[lights[0]]
        else:
            if 'red' in lights and 'yellow' in lights:
                return 'R_with_Y'
            elif 'yellow' in lights and 'straight' in lights:
                return 'Y_with_G'
            elif 'yellow' in lights and 'left' in lights:
                return 'Y_with_GLeft'
            elif 'straight' in lights and 'left' in lights:
                return 'G_with_GLeft'
            elif 'red' in lights and 'left' in lights:
                return 'R_with_GLeft'
            elif 'lowerleft' in lights and 'straight' in lights:
                return 'LLG_SG'
            elif 'red' in lights and 'lowerleft' in lights:
                return 'R_LLG'
            elif 'upperleft' in lights and 'upperright' in lights:
                return 'ULG_URG'
            else:
                return None

    @pyqtSlot(int, int)
    def ps_cell_click_highlight_opengl(self, row, col):
        # self.draw_gl.select_item = self.int_schedule['TLState'][row]['lightcolor']
        self.draw_gl.select_item = []
        try:
            str_tl_list = self.ps_table.horizontalHeaderItem(col).text()
            tl_list = literal_eval(str_tl_list)
            self.draw_gl.select_tl_list = tl_list
            self.draw_gl.select_tl_color = None
            self.draw_gl._id = None
        except:
            return

    
    @pyqtSlot(int, int)
    def ps_item_pressed_change_value(self, row, col):
        cell = self.ps_table.currentItem()
        try:
            int(cell.text())
            cell.setText(cell.text())
        except:
            cell.setText('0')

        
    @pyqtSlot(int, int)
    def tl_cell_click_highlight_opengl(self, row, col):
        if col == self.tl_table.columnCount()-1:
            return
        try:
            self.draw_gl.select_item = self.int_schedule['TLState'][row]['lightcolor']
        except:
            select_item = []
            for i in range(self.tl_table.columnCount()-1):
                select_item.append(self.tl_table.item(self.tl_table.currentRow(), i).text())
            self.draw_gl.select_item = select_item

        str_tl_list = self.tl_table.horizontalHeaderItem(col).text()
        tl_list = literal_eval(str_tl_list)
        self.draw_gl.select_tl_list = tl_list
        self.draw_gl.select_tl_color = self.tl_table.currentItem().text()
        self.draw_gl._id = None


    @pyqtSlot(int, int)
    def tl_cell_double_click_update_state(self, row, col):
        cell = self.tl_table.currentItem()

        if col == self.tl_table.columnCount()-1:
            _duration = 0
            try:
                _duration = int(cell.text())
            except:
                pass

            value, okPressed = QInputDialog.getInt(self, 'Duration', 'Enter the duration of the state.', _duration)
            cell.setText(str(value))
            if okPressed and cell is not None:
                self.int_schedule['TLState'][row]['duration'] = value
                self.traffic_light_update_table_widget()
        else:
            # header
            str_tl_list = self.tl_table.horizontalHeaderItem(col).text()
            try:
                self.draw_gl.select_item = self.int_schedule['TLState'][row]['lightcolor']
            except:
                pass
            tl_list = literal_eval(str_tl_list)
            self.draw_gl.select_tl_list = tl_list
            self.draw_gl.select_tl_color = self.tl_table.currentItem().text()
            self.draw_gl._id = None

            light_list = []
            tl_dict = self.int_item.TL_dict
            for idx in tl_list:
                if tl_dict[idx].type != 'car':
                    continue
                if tl_dict[idx].sub_type is None:
                    continue
                if len(light_list) > len(tl_dict[idx].sub_type):
                    continue
                light_list = tl_dict[idx].sub_type

            items = []
            for light in light_list:
                str_light = self.convert_tl([light])
                items.append(str_light)
            # 두개씩 동시에 켜지는 것
            list2 = list((itertools.combinations(light_list, 2)))
            for i in list2:
                str_light = self.convert_tl(i)
                if str_light is not None:
                    items.append(str_light)
            
            items.append('Undefined')
            value, okPressed = QInputDialog.getItem(self, "Get item","RelatedSignal:", items, 0, False)

            if okPressed and cell is not None:
                cell.setText(value)
                try:
                    self.int_schedule['TLState'][row]['lightcolor'][col] = value
                    self.traffic_light_update_table_widget()
                except:
                    pass
            

    # @pyqtSlot()
    # def __clear_contents(self):
    #     self.tl_table.clearContents()
    #     self.int_schedule['TLState'].clear()
    #     self.traffic_light_update_table_widget()

    @pyqtSlot()
    def __append_state(self):
        row_count = self.tl_table.rowCount()
        self.tl_table.setRowCount(row_count+1)
        # {'idx' : self.sp['id'], 'TLState' : [], 'yelloduration' : [], 'PSState' : []}
        base_color_state = ['R']*(self.tl_table.columnCount()-1)
        self.int_schedule['TLState'].append({'duration': 30, 'lightcolor':base_color_state})
        self.traffic_light_update_table_widget()

    @pyqtSlot()
    def __delete_state(self):
        row = self.tl_table.currentRow()
        self.int_schedule['TLState'].pop(row)
        self.tl_table.removeRow(row)
        self.traffic_light_update_table_widget()
