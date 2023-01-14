"""
MAIN_UI Module
"""

import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
from proj_mgeo_editor_42dot.GUI.ui_layout import Ui_MainWindow

from lib.common.logger import Logger

import json
import shutil

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt, QMetaObject, QPoint, QSize, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QIcon

from GUI.opengl_canvas import OpenGLCanvas
from GUI.pyqt5_file_io_funcs import FileIOFuncs

from GUI.feature_sets_error_fix import ErrorFix
from GUI.feature_sets_odr_conversion import OdrConversion

from lib.widget.display_log import LogWidget
from lib.widget.edit_odr_param import ODREditor
from lib.common.aes_cipher import AESCipher

from proj_mgeo_editor_license_management.editor_ex import LauncherEx, LauncherEx_42dot

# ui_file = os.path.join(current_path, "GUI/ui_layout.ui")
# ui_file = os.path.normpath(ui_file)   
# form_class = uic.loadUiType(ui_file)[0]


class PyQTWindow(QtWidgets.QMainWindow):
# class PyQTWindow(QtWidgets.QMainWindow, form_class):
    """
    PyQTWindow 클래스
    """
    def __init__(self, parent = None):
        # super(PyQTWindow, self).__init__(parent)
        super().__init__()
        # self.setupUi(self)                
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.set_ui(self)
        self.setWindowIcon(QIcon(os.path.join(current_path, 'map.ico')))
        
        self.launcher_ex = LauncherEx_42dot()
        self.launcher_ex.set_qtwindow(self)


    def __init_file_io_funcs(self, canvas):
        """
        File IO 기능만 별도로 모여있는 클래스 생성
        """
        file_io_funcs = FileIOFuncs(self.canvas)
        
        file_path = os.path.join(current_path, 'config_file_io.json')
        config_file_io = None
        
        # 현재 config 파일이 존재하지 않으면 디폴트 파일로부터 생성한다
        if not os.path.exists(file_path):
            default_file = os.path.join(current_path, 'GUI/config_file_io_default.json')
            shutil.copy(default_file, file_path)

        with open(file_path, 'r') as f:
            config_file_io = json.load(f)
        
        if config_file_io is None:
            raise BaseException('Failed to initialize. Cannot find config_file_io.json')

        file_io_funcs.config = config_file_io
        file_io_funcs.config_file_path = file_path
        file_io_funcs.program_root_dir = current_path

        return file_io_funcs


    def __init_error_fix_funcs(self, canvas):
        """
        Error Fix 관련 기능을 제공하는 클래스 생성
        """
        return ErrorFix(canvas)
    

    def __init_odr_conversion_funcs(self, canvas):

        self.odr_param_widget = ODREditor()
        
        file_path = os.path.join(current_path, 'config_odr_param.json')
        config_file_odr_param = None
        
        # 현재 config 파일이 존재하지 않으면 디폴트 파일로부터 생성한다
        if not os.path.exists(file_path):
            default_file = os.path.join(current_path, 'GUI/config_odr_param_default.json')
            shutil.copy(default_file, file_path)

        with open(file_path, 'r') as f:
            config_file_odr_param = json.load(f)
        
        if config_file_odr_param is None:
            raise BaseException('Failed to initialize. Cannot find config_odr_param.json')

        self.odr_param_widget.odr_param = config_file_odr_param
        self.odr_param_widget.config_file_path = current_path
        self.odr_param_widget.program_root_dir = current_path

        self.odr_param_widget.initUI()

        return OdrConversion(canvas)


    def check_user_import_info(self, user_info, action_name):
        """
        User 설정을 보고 Action 을 활성화할지 여부를 결정한다.
        새로운 기능이 추가되었는데 User 설정이 업데이트되지 않아 Key 에 존재하지 않으면 기능을 활성화한다.
        """
        enabled = True
        if user_info['import_actions'].get(action_name) == 0:
            enabled = False
        return enabled


    def set_ui(self, MainWindow):
        """
        Layout Ui와 연결한다
        """

        # OpenGL Canvas 연결
        opengl_layout = self.findChild(QVBoxLayout, "verticalLayout_opengl")

        # User 정보 설정
        user_info_path = os.path.join(current_path, 'User.json')

        aes_cipher = AESCipher()
        # 현재 User 파일이 존재하지 않으면 모라이 정보로 생성한다.
        if not os.path.exists(user_info_path):

            default_user_info_path = os.path.join(current_path, 'GUI/Users/User_42dot.json')
            aes_cipher.encrypt_file(default_user_info_path, user_info_path)

        user_info = aes_cipher.decrypt_file_to_json(user_info_path)
        
        if user_info is None:
            raise BaseException('Failed to initialize. Cannot find User.json')

        # 환경설정 세팅
        file_path = os.path.join(current_path, 'config_canvas.json')        
        config_canvas = None

        # 현재 config 파일이 존재하지 않으면 디폴트 파일로부터 생성한다
        if not os.path.exists(file_path):
            default_file = os.path.join(current_path, 'GUI/config_canvas_default.json')
            shutil.copy(default_file, file_path)
        
        with open(file_path, 'r') as f:
            config_canvas = json.load(f)
        
        if config_canvas is None:
            raise BaseException('Failed to initialize. Cannot find config_canvas.json')

        self.canvas = OpenGLCanvas()
        self.canvas.setFocusPolicy( Qt.ClickFocus )
        self.canvas.setFocus()
        opengl_layout.addWidget(self.canvas)

        self.canvas.setConfig(config_canvas)
        self.canvas.setConfigFilePath(file_path)


        # 별도 기능을 지원하는 클래스 인스턴스 생성
        self.file_io_funcs = self.__init_file_io_funcs(self.canvas)
        self.error_fix_funcs = self.__init_error_fix_funcs(self.canvas)
        self.odr_conversion_funcs = self.__init_odr_conversion_funcs(self.canvas)


        # 로그 저장하는 파일 만들기
        log_file_path = os.path.normpath(os.path.join(current_path, 'log'))
        self.log_msg = Logger.create_instance(log_file_path=log_file_path, log_widget=LogWidget())


        # 회전
        self.slider_x = self.findChild(QtWidgets.QSlider, 'slider_x')
        self.slider_x.valueChanged.connect(self.canvas.setXRotation)
        self.slider_y = self.findChild(QtWidgets.QSlider, 'slider_y')
        self.slider_y.valueChanged.connect(self.canvas.setYRotation)
        self.slider_z = self.findChild(QtWidgets.QSlider, 'slider_z')
        self.slider_z.valueChanged.connect(self.canvas.setZRotation)
        
        # 회전 reset
        self.resetX = self.findChild(QPushButton, 'reset_xRot')
        self.resetX.clicked.connect(lambda:self.canvas.setXRotation(0))
        self.resetY = self.findChild(QPushButton, 'reset_yRot')
        self.resetY.clicked.connect(lambda:self.canvas.setYRotation(0))
        self.resetZ = self.findChild(QPushButton, 'reset_zRot')
        self.resetZ.clicked.connect(lambda:self.canvas.setZRotation(0))
        
        # 회전 edit text
        self.editX = self.findChild(QLineEdit, 'edit_xRot')
        self.editX.setValidator(QIntValidator())
        self.editX.returnPressed.connect(lambda:self.canvas.setXRotation(int(self.editX.text())))

        self.editY = self.findChild(QLineEdit, 'edit_yRot')
        self.editY.setValidator(QIntValidator())
        self.editY.returnPressed.connect(lambda:self.canvas.setYRotation(int(self.editY.text())))

        self.editZ = self.findChild(QLineEdit, 'edit_zRot')
        self.editZ.setValidator(QIntValidator())
        self.editZ.returnPressed.connect(lambda:self.canvas.setZRotation(int(self.editZ.text())))

        slider = [self.slider_x, self.slider_y, self.slider_z]
        rot_eidt = [self.editX, self.editY, self.editZ]
        self.canvas.slider = slider
        self.canvas.rot_eidt = rot_eidt

        # 메뉴 ui 연결
        self.menuFiles = self.findChild(QMenu, 'menuFiles')
        self.menuImport = self.findChild(QMenu, 'menuImport')
        self.menuExport = self.findChild(QMenu, 'menuExport')
        self.menuFind = self.findChild(QMenu, 'menuFind')
        self.menuBasic_Editing = self.findChild(QMenu, 'menuBasic_Editing')
        self.menuCurve_Fitting = self.findChild(QMenu, 'menuCurve_Fitting') 
        self.menuOpenDRIVE_Conversion = self.findChild(QMenu, 'menuOpenDRIVE_Conversion')
        self.menuData_Trimming = self.findChild(QMenu, 'menuData_Trimming')
        self.menuData_Integrity = self.findChild(QMenu, 'menuData_Integrity')
        self.menuMisc = self.findChild(QMenu, 'menuMisc')

        # 처음 시작할 때 (데이터가 없을 때) 다음의 메뉴는 disabled 시킨다
        # 데이터가 정상적으로 로드되면, enable 시킨다
        initiallyDisabledMenu = [
            self.menuExport,
            self.menuFind,
            self.menuBasic_Editing,
            self.menuCurve_Fitting,
            self.menuOpenDRIVE_Conversion,
            self.menuData_Trimming,
            self.menuData_Integrity,
            self.menuMisc 
        ]
        for menu in initiallyDisabledMenu:
            if menu is None:
                raise BaseException('[ERROR] UI is not compatible with this script.')
            menu.setDisabled(True)

        
        main_widget_layout = self.findChild(QHBoxLayout, 'main_widget_layout')

        splitter_main = QSplitter(Qt.Horizontal)

        frame_1 = self.findChild(QFrame, 'frame_1')
        frame_2 = self.findChild(QFrame, 'frame_2')
        frame_3 = self.findChild(QFrame, 'frame_3')

        splitter_main.addWidget(frame_1)
        splitter_main.addWidget(frame_2)
        splitter_main.addWidget(frame_3)

        splitter_log = QSplitter(Qt.Vertical)
        frame_log = self.findChild(QFrame, 'frame_log')
        splitter_log.addWidget(splitter_main)
        splitter_log.addWidget(frame_log)
        splitter_log.setSizes([100, 1])

        main_widget_layout.addWidget(splitter_log)
        
        # Log Widget 연결
        log_layout = self.findChild(QVBoxLayout, "log_widget_layout")
        log_widget = self.log_msg.log_widget
        log_widget.collapsible.splitter = splitter_log
        log_layout.addWidget(log_widget)

        splitter_log.splitterMoved.connect(log_widget.collapsible.lockSplitter)

        # QSplitter를 이용해서 비율 조정하기
        split_data = QSplitter()
        split_data.setOrientation(Qt.Vertical)
        # 1. Mgeo Data
        # 1-1. 어떤 타입의 데이터를 선택할 지 TreeWidget 설정
        self.treeWidget_data = self.findChild(QTreeWidget, 'treeWidget_data')
        self.canvas.tree_data = self.treeWidget_data
        # 메인 데이터 뷰어, MGeo 데이터 타입별 설정
        self.treeWidget_data.setContextMenuPolicy(Qt.CustomContextMenu)

        # 2. Mgeo Style
        self.treeWidget_style = self.findChild(QTreeWidget, 'treeWidget_style')
        # 2-1. Style item
        self.treeWidget_style.setColumnCount(2)
        self.treeWidget_style.setHeaderLabels(["Properties", "Value"])
        self.canvas.tree_style = self.treeWidget_style

        data_layout = self.findChild(QVBoxLayout, 'data_layout')
        
        split_data.addWidget(self.treeWidget_data)
        split_data.addWidget(self.treeWidget_style)
        data_layout.addWidget(split_data)


        # 3. Mgeo Attribute
        self.treeWidget_attr = self.findChild(QTreeWidget, 'treeWidget_attr')
        # 3-1. Attribute item
        self.treeWidget_attr.setColumnCount(3)
        self.treeWidget_attr.setHeaderLabels(["Properties", "Type", "Value"])
        self.canvas.tree_attr = self.treeWidget_attr

        """ ToolBar - Edit 관련 """
        self.btn_toolbar = self.findChild(QtWidgets.QPushButton, 'btn_toolbar')
        
        btn_create_junction = self.findChild(QPushButton, 'btn_create_junction')
        btn_create_junction.setShortcut('Ctrl+J')
        btn_create_junction.clicked.connect(self.canvas.create_junction)

        btn_add_poly3 = self.findChild(QPushButton, 'btn_add_poly3')
        btn_add_poly3.clicked.connect(
            lambda:self.canvas.set_geochange_point('poly3'))

        btn_add_line = self.findChild(QPushButton, 'btn_add_line')
        btn_add_line.clicked.connect(
            lambda:self.canvas.set_geochange_point('line'))

        btn_merge_links = self.findChild(QPushButton, 'btn_merge_links')
        btn_merge_links.clicked.connect(self.canvas.merge_links)

        btn_connect_nodes = self.findChild(QPushButton, 'btn_connect_nodes')
        btn_connect_nodes.clicked.connect(self.canvas.connect_nodes)

        btn_divide_a_link = self.findChild(QPushButton, 'btn_divide_a_link')
        btn_divide_a_link.clicked.connect(self.canvas.divide_a_link_smart)
        


        """ View Buttons """
        rbtn_view_select = self.findChild(QRadioButton, 'rbtn_view_select')
        rbtn_view_trans = self.findChild(QRadioButton, 'rbtn_view_trans')
        rbtn_view_rotate = self.findChild(QRadioButton, 'rbtn_view_rotate')
        
        btn_view_xy = self.findChild(QPushButton, 'btn_view_xy')
        btn_view_yz = self.findChild(QPushButton, 'btn_view_yz')
        btn_view_zx = self.findChild(QPushButton, 'btn_view_zx')

        rbtn_view_select.clicked.connect(lambda:self.canvas.setViewMode('view_select'))
        rbtn_view_trans.clicked.connect(lambda:self.canvas.setViewMode('view_trans'))
        rbtn_view_rotate.clicked.connect(lambda:self.canvas.setViewMode('view_rotate'))

        btn_view_xy.clicked.connect(lambda:self.canvas.setViewMode('view_xy'))
        btn_view_yz.clicked.connect(lambda:self.canvas.setViewMode('view_yz'))
        btn_view_zx.clicked.connect(lambda:self.canvas.setViewMode('view_zx'))



        """ Files """
        action_load_mgeo = self.findChild(QAction, 'action_load_mgeo')
        action_load_mgeo.setShortcut('Ctrl+L')
        action_load_mgeo.triggered.connect(
            lambda:self.file_io_funcs.load_mgeo(initiallyDisabledMenu))

        action_save_mgeo = self.findChild(QAction, 'action_save_mgeo')
        action_save_mgeo.setShortcut('Ctrl+S')
        action_save_mgeo.triggered.connect(
            self.file_io_funcs.save_mgeo)

        action_merge_mgeo = self.findChild(QAction, 'actionMerge_MGeo')
        action_merge_mgeo.setShortcut('Ctrl+M')
        action_merge_mgeo.triggered.connect(
            lambda:self.file_io_funcs.merge_mgeo(initiallyDisabledMenu))

        action_exit = self.findChild(QAction, 'action_exit')
        action_exit.triggered.connect(self.close)



        """ Import & Export """
        action_import_42dot = self.findChild(QAction, 'action_import_42dot')
        action_import_42dot.setShortcut('Ctrl+I')
        action_import_42dot.triggered.connect(
            lambda:self.file_io_funcs.import_42dot(initiallyDisabledMenu, use_legacy=False))


        action_import_42dot_legacy = self.findChild(QAction, 'action_import_42dot_legacy')
        action_import_42dot_legacy.triggered.connect(
            lambda:self.file_io_funcs.import_42dot(initiallyDisabledMenu, use_legacy=True))

        action_export_odr = self.findChild(QAction, 'action_export_odr_2')
        action_export_odr.setShortcut('Ctrl+E')
        action_export_odr.triggered.connect(
            self.file_io_funcs.export_odr)
        


        """ Find """
        actionFind = self.findChild(QAction, 'actionFind')
        actionFind.setShortcut('CTRL+F')

        action_node = self.findChild(QAction, 'action_node')
        action_node.setShortcut('SHIFT+N')

        action_link = self.findChild(QAction, 'action_link')
        action_link.setShortcut('SHIFT+L')
        
        action_ts = self.findChild(QAction, 'action_ts')
        action_ts.setShortcut('SHIFT+S')

        action_tl = self.findChild(QAction, 'action_tl')
        action_tl.setShortcut('SHIFT+T')

        action_jct = self.findChild(QAction, 'action_jct')
        action_jct.setShortcut('SHIFT+J')

        action_road = self.findChild(QAction, 'action_road')
        action_road.setShortcut('SHIFT+R')

        # id 입력할 수 있도록 창 띄우기 
        actionFind.triggered.connect(self.canvas.find_by_mgeo_id)
        
        action_node.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Node'))
        action_link.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Link'))
        action_ts.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Traffic Sign'))
        action_tl.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Traffic Light'))
        action_jct.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Junction'))
        action_road.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Road'))



        """ Basic Edit """
        action_divide_a_link_smart = self.findChild(QAction, 'action_divide_a_link_smart')
        action_divide_a_link_smart.setShortcut('Ctrl+D')
        action_divide_a_link_smart.triggered.connect(
            self.canvas.divide_a_link_smart)

        action_divide_a_link_keep_front = self.findChild(QAction, 'action_divide_a_link_keep_front')
        action_divide_a_link_keep_front.triggered.connect(
            lambda:self.canvas.divide_a_link(keep_front=True))

        action_divide_a_link_keep_rear = self.findChild(QAction, 'action_divide_a_link_keep_rear')
        action_divide_a_link_keep_rear.triggered.connect(
            lambda:self.canvas.divide_a_link(keep_front=False))

        action_merge_links = self.findChild(QAction, 'action_merge_links')
        action_merge_links.triggered.connect(
            self.canvas.merge_links)

        action_connect_nodes = self.findChild(QAction, 'action_connect_nodes')
        action_connect_nodes.triggered.connect(
            self.canvas.connect_nodes)

        action_add_link_point = self.findChild(QAction, 'action_add_link_point')
        action_add_link_point.triggered.connect(
            self.canvas.add_link_point)

        action_set_new_road_id = self.findChild(QAction, 'action_set_new_road_id')
        action_set_new_road_id.triggered.connect(
            lambda:self.canvas.set_new_road_id(
                build_preliminary_road_callback=self.odr_conversion_funcs.create_prelimiary_odr_roads
            ))



        """ Curve Fitting """
        action_edit_link_geometry_add_line = self.findChild(QAction, 'action_add_line')
        action_edit_link_geometry_add_line.setShortcut('Ctrl+1')
        action_edit_link_geometry_add_line.triggered.connect(
            lambda:self.canvas.set_geochange_point('line'))
        
        action_edit_link_geometry_add_poly3 = self.findChild(QAction, 'action_add_poly3')
        action_edit_link_geometry_add_poly3.setShortcut('Ctrl+2')
        action_edit_link_geometry_add_poly3.triggered.connect(
            lambda:self.canvas.set_geochange_point('poly3'))

        action_auto_generate_geometry_points = self.findChild(QAction, 'action_auto_generate_geometry_points')
        action_auto_generate_geometry_points.triggered.connect(
            self.canvas.create_geometry_points_auto)

        action_edit_link_geometry_delete_current_point = self.findChild(QAction, 'action_delete_current_point')
        action_edit_link_geometry_delete_current_point.triggered.connect(
            self.canvas.delete_geochange_point_current)

        action_edit_link_geometry_delete_all_points = self.findChild(QAction, 'action_delete_all_points')
        action_edit_link_geometry_delete_all_points.triggered.connect(
            self.canvas.delete_geochange_point_all)

        action_geometry_points_delete_all_line = self.findChild(QAction, 'action_reset_all_points')
        action_geometry_points_delete_all_line.triggered.connect(
            self.canvas.delete_geometry_points_all_line)

        """ OpenDRIVE Conversion """
        # Junction 생성 기능
        action_create_junction = self.findChild(QAction, 'action_create_junction')
        action_create_junction.triggered.connect(
            self.canvas.create_junction)


        # Road 생성 기능
        action_create_preliminary_odr_roads = self.findChild(QAction, 'action_create_preliminary_odr_roads')
        action_create_preliminary_odr_roads.triggered.connect(
            self.odr_conversion_funcs.create_prelimiary_odr_roads)

        action_create_odr_roads = self.findChild(QAction, 'action_create_odr_roads')
        action_create_odr_roads.setShortcut('Ctrl+R')
        action_create_odr_roads.triggered.connect(
            lambda: self.odr_conversion_funcs.create_odr_roads())


        # Road 클리어 기능
        action_clear_odr_roads = self.findChild(QAction, 'action_clear_odr_roads')
        action_clear_odr_roads.triggered.connect(
            self.odr_conversion_funcs.clear_odr_roads)


        # OpenDRIVE 생성 기능
        action_create_opendrive = self.findChild(QAction, 'action_create_opendrive')
        action_create_opendrive.triggered.connect(
            lambda: self.odr_conversion_funcs.create_complete_odr_data(self.odr_param_widget))

        """ Data Trimming """
        action_delete_Objects_out_of_XY_Range_soft = self.findChild(QAction, 'action_delete_Objects_out_of_XY_Range_soft')
        action_delete_Objects_out_of_XY_Range_soft.triggered.connect(
            lambda:self.canvas.delete_objects_out_of_xy_range(False))

        action_delete_Objects_out_of_XY_Range_hard = self.findChild(QAction, 'action_delete_Objects_out_of_XY_Range_hard')
        action_delete_Objects_out_of_XY_Range_hard.triggered.connect(
            lambda:self.canvas.delete_objects_out_of_xy_range(True))

        action_delete_Objects_inside_this_Screen = self.findChild(QAction, 'action_delete_Objects_inside_this_Screen')
        action_delete_Objects_inside_this_Screen.triggered.connect(
            self.canvas.delete_object_inside_xy_range)


        # 6. Data Integrity
        # Data에러 수정 기능 >> Node 데이터 유무에 따라서 enable/disable 하도록 만들기
        action_find_overlapped_node = self.findChild(QAction, 'action_find_overlapped_node')
        action_repair_overlapped_node = self.findChild(QAction, 'action_repair_overlapped_node')
        action_find_dangling_nodes = self.findChild(QAction, 'action_find_dangling_nodes')
        action_delete_dangling_nodes = self.findChild(QAction, 'action_delete_dangling_nodes')
        action_find_closed_loop_link = self.findChild(QAction, 'action_find_closed_loop_link')
        action_clear = self.findChild(QAction, 'action_clear')

        # find overlapped node는 node 데이터 있으면 enable, repair 후에는 disable ++ overlapped node 데이터 없으면 disable
        action_find_overlapped_node.triggered.connect(
            lambda:self.error_fix_funcs.find_overlapped_node(
                action_repair_overlapped_node, action_clear))

        # repair overlapped node 수행 후에 find overlapped node, repair overlapped node action disable
        action_repair_overlapped_node.triggered.connect(
            lambda:self.error_fix_funcs.repair_overlapped_node(
                action_repair_overlapped_node))
        
        # find dangling node는 node 데이터 있으면 enable, delete 후에는 disable ++ dangling node 데이터 없으면 disable
        action_find_dangling_nodes.triggered.connect(
            lambda:self.error_fix_funcs.find_dangling_nodes(
                action_delete_dangling_nodes, action_clear))
        
        # delete dangling node 수행 후에 find dangling node, delete overlapped node action disable
        action_delete_dangling_nodes.triggered.connect(
            lambda:self.error_fix_funcs.delete_dangling_nodes(
                action_delete_dangling_nodes))

        action_find_closed_loop_link.triggered.connect(
            lambda:self.error_fix_funcs.find_closed_loop_link(action_clear))

        # highlight, overlapped node, dangling node list clear시에 clear action disable
        action_clear.triggered.connect(
            lambda:self.error_fix_funcs.clear_highlight(
                [action_repair_overlapped_node, action_delete_dangling_nodes],  # trigger 이후 disable 되어야하는 기능 
                action_clear)) # trigger 이후 disable 되어야하는 기능

        action_repair_overlapped_node.setDisabled(True)
        action_delete_dangling_nodes.setDisabled(True)
        action_clear.setDisabled(True)


        # 7. Misc
        action_get_position_in_carla = self.findChild(QAction, 'action_get_position_in_carla')
        action_get_position_in_carla.triggered.connect(self.canvas.get_position_in_inlink_point)

        action_change_ids_to_string = self.findChild(QAction, 'action_change_ids_to_string')
        action_change_ids_to_string.triggered.connect(self.canvas.change_all_item_id_to_string)
        
        action_change_node_link_height_to_0 = self.findChild(QAction, 'action_change_node_link_height_to_0')
        action_change_node_link_height_to_0.triggered.connect(self.canvas.change_node_link_height_to_0)


        # position_label에 현재 World 위치 넣으려고
        self.label_range_x = self.findChild(QLabel, 'label_range_x')
        self.label_range_y = self.findChild(QLabel, 'label_range_y')
        self.label_zoom = self.findChild(QLabel, 'label_zoom')
        self.canvas.position_label = [self.label_range_x, self.label_range_y, self.label_zoom]


    def set_menu_disable(self, isActive):        
        # ui menu hide 하는 로직 작성
        # 특정 상황에서 감추고 싶은 메뉴가 있을 때
        print()


    def closeEvent(self, event):
        result = QMessageBox.question(self, "42dot Map Editor", 'Do you really want to close editor?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if result == QMessageBox.Ok:
            event.accept()
            # self.launcher_ex.show_launcher()
        elif result == QMessageBox.Cancel:
            event.ignore()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    qtWindow = PyQTWindow()

    qtWindow.setWindowTitle("42dot Map Editor (v1.5.1)")
    qtWindow.show()
    sys.exit(app.exec_())