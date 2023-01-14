"""
MAIN_UI Module
"""

import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

print(sys.path)
from proj_mgeo_editor_license_management.define import Define
from proj_mgeo_editor_license_management.rest_api_manager import RestApiManager
from proj_mgeo_editor_license_management.editor_ex import LauncherEx

import platform
import datetime
import ctypes
if platform.system() == "Windows":
    # 작업 표시줄에 아이콘을 표시하기 위해서 Process App User Model ID 등록
    myappid = 'morai.mapeditor' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from lib.common.logger import Logger

import numpy as np
import json
import shutil

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *

from GUI.opengl_canvas import OpenGLCanvas
from GUI.pyqt5_file_io_funcs import FileIOFuncs

from GUI.feature_sets_error_fix import ErrorFix
from GUI.feature_sets_odr_conversion import OdrConversion
from GUI.feature_sets_osm_conversion import OsmConversion
from proj_mgeo_editor_morai_opengl.GUI.ui_layout import Ui_MainWindow

from lib.widget.display_log import LogWidget
from lib.widget.edit_odr_param import ODREditor
from lib.widget.edit_run_with_esmini import EsminiEditor
from lib.widget.loading_dialog import LoadingDialog
from lib.widget.start_scenario_dialog import StartScenarioDialog
from lib.widget.batch_scenario_widget import BatchScenarioWidget
# from lib.widget.simulation_result_widget import SimulationResultWidget
from lib.common.aes_cipher import AESCipher

from lib.openscenario.open_scenario_importer import OpenScenarioImporter
from lib.openscenario.client.open_scenario_client import OpenScenarioClient
from lib.openscenario.class_defs.utils_position import convert_to_world_position
from lib.command_manager.command_manager import CommandManager

# ui_file = os.path.join(current_path, "GUI/ui_layout.ui")
# ui_file = os.path.normpath(ui_file)   
# form_class = uic.loadUiType(ui_file)[0]

class PyQTWindow(QtWidgets.QMainWindow):
    """
    PyQTWindow 클래스
    """
    """
    def __init__(self, parent = None):
        super(PyQTWindow, self).__init__(parent)
        self.setupUi(self)
        self.set_ui(self)
    """
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # OpenSCENARIO related
        self.open_scenario_client = None
        self.open_scenario_importer = None
        self.batch_scenario_widget = None
        self.simulation_result_widget = None
        self.scenario_file_list = []

        self.scheduled_callback_func = None

        # Initialize UI
        self.set_ui(self)                 
        self.setWindowIcon(QIcon(os.path.join(current_path, 'map.ico')))
        # self.initiallyDisabledMenu = []

        self.launcher_ex = LauncherEx()
        self.launcher_ex.set_qtwindow(self)
        
        # self.esmini_init_odr_path = ''
    
    def __init_file_io_funcs(self, canvas, default_config_file):
        """
        File IO 기능만 별도로 모여있는 클래스 생성
        """
        file_io_funcs = FileIOFuncs(self, self.canvas)
        
        file_path = os.path.join(current_path, 'config_file_io.json')
        config_file_io = None
        
        # 현재 config 파일이 존재하지 않으면 디폴트 파일로부터 생성한다
        if not os.path.exists(file_path):
            default_file = os.path.join(current_path, 'GUI/{}'.format(default_config_file))
            shutil.copy(default_file, file_path)

        with open(file_path, 'r') as f:
            config_file_io = json.load(f)
        
        if config_file_io is None:
            raise BaseException('Failed to initialize. Cannot find config_file_io.json')

        file_io_funcs.config = config_file_io
        file_io_funcs.config_file_path = file_path
        file_io_funcs.program_root_dir = current_path
        file_io_funcs.command_manager = self.command_manager

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

    def __init_osm_conversion_funcs(self, canvas):
        return OsmConversion(canvas)

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
        """Layout Ui와 연결한다"""

        # OpenGL Canvas 연결
        opengl_layout = self.findChild(QVBoxLayout, "verticalLayout_opengl")

        # User 정보 설정
        user_info_path = os.path.join(current_path, 'User.json')

        aes_cipher = AESCipher()
        # 현재 User 파일이 존재하지 않으면 모라이 정보로 생성한다.
        if not os.path.exists(user_info_path):

            # default_user_info_path = os.path.join(current_path, 'GUI/Users/User_TomTom.json')
            default_user_info_path = os.path.join(current_path, 'GUI/Users/User_add_on.json')
            aes_cipher.encrypt_file(default_user_info_path, user_info_path)

        user_info = aes_cipher.decrypt_file_to_json(user_info_path)
        
        if user_info is None:
            raise BaseException('Failed to initialize. Cannot find User.json')

        # About 정보 설정
        about_contents = {}
        about_info_path = os.path.join(current_path, 'about.json')
        if os.path.exists(about_info_path):
            with open(about_info_path, 'r') as f:
                about_contents = json.load(f)
                version = user_info['program_name'].split('(')[1]
                version = version[:-1]
                about_contents['Version'] = version
        else:
            about_contents['launch time'] = str(datetime.datetime.now())
            version = user_info['program_name'].split('(')[1]
            version = version[:-1]
            about_contents['version'] = version
        program_name = user_info['program_name']

        # 윈도우 타이틀 설정
        self.setWindowTitle(user_info['program_name'])
        
        # 환경설정 세팅
        file_path = os.path.join(current_path, 'config_canvas.json')        
        config_canvas = None        

        # 현재 config 파일이 존재하지 않으면 디폴트 파일로부터 생성한다
        if not os.path.exists(file_path):
            default_file = os.path.join(current_path, 'GUI/config_canvas_default.json')
            shutil.copy(default_file, file_path)

        #command 관리(UNDO/REDO)
        self.command_manager = CommandManager()
        
        with open(file_path, 'r') as f:
            config_canvas = json.load(f)
        
        if config_canvas is None:
            raise BaseException('Failed to initialize. Cannot find config_canvas.json')

        self.canvas = OpenGLCanvas()
        self.canvas.setFocusPolicy( Qt.ClickFocus )
        self.canvas.setFocus()
        self.canvas.command_manager = self.command_manager
        opengl_layout.addWidget(self.canvas)

        self.canvas.setConfig(config_canvas)
        self.canvas.setConfigFilePath(file_path)

        # 별도 기능을 지원하는 클래스 인스턴스 생성
        self.file_io_funcs = self.__init_file_io_funcs(self.canvas, user_info['config_file_io'])
        
        self.error_fix_funcs = self.__init_error_fix_funcs(self.canvas)
        self.odr_conversion_funcs = self.__init_odr_conversion_funcs(self.canvas)
        self.osm_conversion_funcs = self.__init_osm_conversion_funcs(self.canvas)
        self.esmini_conversion_funcs = self.__init_run_with_esmini_funcs(self.canvas)
        # 로딩 화면 시작/종료를 위한 연결
        self.file_io_funcs.file_io_job_start.connect(self.show_loading)
        self.file_io_funcs.file_io_job_finished.connect(self.close_loading)

        # 회전
        self.slider_x = self.findChild(QtWidgets.QSlider, 'slider_x')
        self.slider_x.valueChanged.connect(self.canvas.setXRotation)
        
        self.slider_z = self.findChild(QtWidgets.QSlider, 'slider_z')
        self.slider_z.valueChanged.connect(self.canvas.setZRotation)
        
        # 회전 reset
        self.resetX = self.findChild(QPushButton, 'reset_xRot')
        self.resetX.clicked.connect(lambda:self.canvas.setXRotation(0))
       
        self.resetZ = self.findChild(QPushButton, 'reset_zRot')
        self.resetZ.clicked.connect(lambda:self.canvas.setZRotation(0))
        
        # 회전 edit text
        self.editX = self.findChild(QLineEdit, 'edit_xRot')
        self.editX.setValidator(QIntValidator())
        self.editX.returnPressed.connect(lambda:self.canvas.setXRotation(int(self.editX.text())))

        self.editZ = self.findChild(QLineEdit, 'edit_zRot')
        self.editZ.setValidator(QIntValidator())
        self.editZ.returnPressed.connect(lambda:self.canvas.setZRotation(int(self.editZ.text())))

        slider = [self.slider_x, self.slider_z]
        rot_eidt = [self.editX, self.editZ]
        self.canvas.slider = slider
        self.canvas.rot_eidt = rot_eidt

        # camera speed
        self.camera_speed_slider = self.findChild(QSlider, 'slider_camera_speed')
        self.camera_speed_slider.valueChanged.connect(self.canvas.setCameraSpeed)

        self.camera_speed_reset = self.findChild(QPushButton, 'reset_camera_speed')
        self.camera_speed_reset.clicked.connect(lambda:self.canvas.setCameraSpeed(0))

        self.camera_speed_edit = self.findChild(QLineEdit, 'edit_camera_speed')
        self.camera_speed_edit.setValidator(QIntValidator())
        self.camera_speed_edit.returnPressed.connect(lambda:self.canvas.setCameraSpeed(int(self.camera_speed_edit.text())))

        cameraSpeedSlider = self.camera_speed_slider
        cameraSpeedEdit = self.camera_speed_edit
        self.canvas.camera_speed_slider = cameraSpeedSlider
        self.canvas.camera_speed_edit = cameraSpeedEdit

        # camera position move
        self.camera_move_east_edit = self.findChild(QLineEdit, 'edit_east')
        self.camera_move_east_edit.setValidator(QIntValidator())
        self.camera_move_east_edit.returnPressed.connect(lambda:self.canvas.setCameraPositionEast(int(self.camera_move_east_edit.text())))

        self.camera_move_north_edit = self.findChild(QLineEdit, 'edit_north')
        self.camera_move_north_edit.setValidator(QIntValidator())
        self.camera_move_north_edit.returnPressed.connect(lambda:self.canvas.setCameraPositionNorth(int(self.camera_move_north_edit.text())))

        self.camera_move_up_edit = self.findChild(QLineEdit, 'edit_up')
        self.camera_move_up_edit.setValidator(QIntValidator())
        self.camera_move_up_edit.returnPressed.connect(lambda:self.canvas.setCameraPositionUp(int(self.camera_move_up_edit.text())))

        self.canvas.camera_move_east_edit = self.camera_move_east_edit
        self.canvas.camera_move_north_edit = self.camera_move_north_edit
        self.canvas.camera_move_up_edit = self.camera_move_up_edit

        # self.camera_move_east_reset = self.findChild(QPushButton, 'reset_east')
        # self.camera_move_east_reset.clicked.connect(lambda:self.canvas.resetCamera())

        # self.camera_move_north_reset = self.findChild(QPushButton, 'reset_north')
        # self.camera_move_north_reset.clicked.connect(lambda:self.canvas.resetCamera())

        self.camera_move_up_reset = self.findChild(QPushButton, 'reset_up')
        self.camera_move_up_reset.clicked.connect(lambda:self.canvas.resetCamera())

        # 메뉴 ui 연결
        self.menu_files = self.findChild(QMenu, 'menuFiles')
        self.menu_import = self.findChild(QMenu, 'menuFileImport')
        self.menu_export = self.findChild(QMenu, 'menuFileExport')
        self.menu_file_export_parent = self.findChild(QMenu, 'menuFileExport')
        self.menu_file_add_mgeo = self.findChild(QAction, 'action_add_mgeo')
        self.menu_find = self.findChild(QMenu, 'menuFind')
        self.menu_edit = self.findChild(QMenu, 'menuEdit')
        self.menu_map_creation = self.findChild(QMenu, 'menuMap_Creation')
        self.menu_xodr = self.findChild(QMenu, 'menuOpenDRIVE_Conversion')
        self.menu_data_trimming = self.findChild(QMenu, 'menuData_Trimming')
        self.menu_data_integrity = self.findChild(QMenu, 'menuData_Integrity')
        self.menu_world_settings = self.findChild(QMenu, 'menuWorld_Settings')
        self.menu_misc = self.findChild(QMenu, 'menuMisc')
        self.menu_osm = self.findChild(QMenu, 'menuLanelet2_Conversion')
        self.menu_scenario = self.findChild(QMenu, 'menuOpenScenario')
        self.simulation_tab_widget = self.findChild(QTabWidget, 'property_simulation_tab')
         
        # 설정에 따라 메뉴바에서 메뉴 삭제
        if 'exclude_menu' in user_info:
            self.menubar = self.findChild(QMenuBar, 'menubar')
            for menu_name in user_info['exclude_menu']:
                self.menubar.removeAction(self.findChild(QMenu, menu_name).menuAction())

        if 'exclude_file_submenu' in user_info:
            for menu_name in user_info['exclude_file_submenu']:
                self.menu_files.removeAction(
                    self.findChild(QMenu, menu_name).menuAction())

        # Edit 메뉴에서 사용하지 않는 메뉴 제거
        if 'exclude_edit_submenu' in user_info:
            for menu_name in user_info['exclude_edit_submenu']:
                self.menu_edit.removeAction(self.findChild(QAction, menu_name))

        # 처음 시작할 때 (데이터가 없을 때) 다음의 메뉴는 disabled 시킨다
        # 데이터가 정상적으로 로드되면, enable 시킨다
        self.initiallyDisabledMenu = [
            self.menu_file_add_mgeo,
            self.menu_file_export_parent,
            self.menu_find,
            self.menu_edit,
            self.menu_xodr,
            self.menu_data_trimming,
            self.menu_data_integrity,
            self.menu_world_settings,
            self.menu_misc,
            self.menu_osm,
            self.menu_map_creation,
            self.menu_scenario
        ]
        for menu in self.initiallyDisabledMenu:
            if menu is None:
                print('[ERROR] UI is not compatible with this script.')
                # raise BaseException('[ERROR] UI is not compatible with this script.')
            else:
                menu.setDisabled(True)
        
        
        # QSplitter를 이용해서 비율 조정하기
        split_data = QSplitter()
        split_data.setOrientation(Qt.Vertical)
        
        
        # 1. Mgeo Data
        # # 1-1. 어떤 타입의 데이터를 선택할 지 TreeWidget 설정
        self.treeWidget_data = self.findChild(QTreeWidget, 'treeWidget_data')
        self.canvas.tree_data = self.treeWidget_data
        
        # # 메인 데이터 뷰어, MGeo 데이터 타입별 설정
        self.treeWidget_data.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # 2. Mgeo Style
        self.treeWidget_style = self.findChild(QTreeWidget, 'treeWidget_style')
        
        # 2-1. Style item
        self.treeWidget_style.setColumnCount(2)
        self.treeWidget_style.setHeaderLabels(["Properties", "Value"])
        self.canvas.tree_style = self.treeWidget_style

        # 3. Mgeo Data Selection
        data_layout = self.findChild(QVBoxLayout, 'data_layout')
        split_data.addWidget(self.treeWidget_data)
        split_data.addWidget(self.treeWidget_style)
        data_layout.addWidget(split_data)

        main_widget_layout = self.findChild(QHBoxLayout, 'main_widget_layout')
        splitter1 = QSplitter(Qt.Horizontal)

        frame_1 = self.findChild(QFrame, 'frame_1')
        frame_2 = self.findChild(QFrame, 'frame_2')
        frame_3 = self.findChild(QFrame, 'frame_3')
        splitter1.addWidget(frame_1)
        splitter1.addWidget(frame_2)
        splitter1.addWidget(frame_3)

        splitter_log = QSplitter(Qt.Vertical)
        frame_log = self.findChild(QFrame, 'frame_log')
        splitter_log.addWidget(splitter1)
        splitter_log.addWidget(frame_log)
        splitter_log.setSizes([10, 0])
        main_widget_layout.addWidget(splitter_log)

        # 로그 저장하는 파일 만들기
        log_file_path = os.path.normpath(os.path.join(current_path, 'log'))
        self.log_msg = Logger.create_instance(log_file_path=log_file_path, log_widget=LogWidget())
        
        # Log Widget 연결
        log_layout = self.findChild(QVBoxLayout, "log_widget_layout")
        log_widget = self.log_msg.log_widget
        log_widget.collapsible.splitter = splitter_log
        log_layout.addWidget(log_widget)
        splitter_log.splitterMoved.connect(log_widget.collapsible.lockSplitter)

        # 3. Mgeo Attribute Tab
        self.treeWidget_attr = self.findChild(QTreeWidget, 'treeWidget_attr')
        # 3-1. Attribute item
        self.treeWidget_attr.setColumnCount(3)
        self.treeWidget_attr.setHeaderLabels(["Properties", "Type", "Value"])
        self.canvas.tree_attr = self.treeWidget_attr
        self.canvas.tree_attr.header().setStretchLastSection(True)

        # 4. Tab Batch Scenario
        btn_load_test_suite = self.findChild(QPushButton, "btn_load_test_suite")
        btn_save_test_suite = self.findChild(QPushButton, "btn_save_test_suite")
        btn_add_batch_scenario = self.findChild(QPushButton, "btn_add_batch_scenario")
        btn_del_batch_scenario = self.findChild(QPushButton, "btn_del_batch_scenario")
        btn_upward_batch_scenario = self.findChild(QPushButton, "btn_upward_batch_scenario")
        btn_downward_batch_scenario = self.findChild(QPushButton, "btn_downward_batch_scenario")
        btn_select_all_batch_scenario = self.findChild(QPushButton, "btn_select_all_batch_scenario")
        table_batch_scenario = self.findChild(QTableWidget, "table_batch_scenario")
        btn_start_batch_scenario = self.findChild(QPushButton, "btn_start_batch_scenario")
        btn_stop_batch_scenario = self.findChild(QPushButton, "btn_stop_batch_scenario")
        btn_skip_batch_scenario = self.findChild(QPushButton, "btn_skip_batch_scenario")
        self.batch_scenario_widget = BatchScenarioWidget(self.file_io_funcs,
                                                   btn_load_test_suite, btn_save_test_suite,
                                                   btn_add_batch_scenario, btn_del_batch_scenario,
                                                   btn_upward_batch_scenario, btn_downward_batch_scenario,
                                                   btn_select_all_batch_scenario,
                                                   btn_start_batch_scenario, btn_stop_batch_scenario,
                                                   btn_skip_batch_scenario,
                                                   table_batch_scenario )
        btn_start_batch_scenario.clicked.connect(lambda:self.start_batch_scenario())
        btn_stop_batch_scenario.clicked.connect(lambda:self.stop_batch_scenario())
        btn_skip_batch_scenario.clicked.connect(lambda:self.stop_scenario())
        self.batch_scenario_widget.context_action_load.triggered.connect(lambda:self.import_scenario_selected_in_batch())
        self.batch_scenario_widget.context_action_run.triggered.connect(lambda:self.start_scenario_selected_in_batch())

        # Simulation Result Tab Widget
        icon_succeeded = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        icon_failed = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        icon_question = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
        text_succeeded = self.findChild(QLabel, "text_succeeded_icon")
        text_succeeded.setPixmap(icon_succeeded.pixmap(QSize(12,12)))
        text_succeeded.setToolTip("number of succeeded tests")
        text_failed = self.findChild(QLabel, "text_failed_icon")
        text_failed.setPixmap(icon_failed.pixmap(QSize(12,12)))
        text_failed.setToolTip("number of failed tests")
        text_none = self.findChild(QLabel, "text_none_icon")
        text_none.setPixmap(icon_question.pixmap(QSize(12,12)))
        text_none.setToolTip("number of not-evaluated tests\nA test wouldn't be evaluated, if Evaluation element is not defined or StopTrigger of Storyboard is triggered.")

        label_total_num = self.findChild(QLabel, "label_total_num")
        label_succeeded = self.findChild(QLabel, "label_succeeded")
        label_failed = self.findChild(QLabel, "label_failed")
        label_none = self.findChild(QLabel, "label_none")
        table_simulation_result_list = self.findChild(QTableWidget, "table_simulation_result_list")
        table_simulation_result = self.findChild(QTableWidget, "table_simulation_result")
        btn_open_log_folder = self.findChild(QPushButton, "btn_open_log_folder")
        btn_simulation_result_clear = self.findChild(QPushButton, "btn_simulation_result_clear")
        progressbar_simulation_result = self.findChild(QProgressBar, "simulation_result_progress_bar")
        # self.simulation_result_widget = SimulationResultWidget(self.file_io_funcs,
        #                                                 label_total_num, label_succeeded, label_failed, label_none,
        #                                                 btn_simulation_result_clear, btn_open_log_folder,
        #                                                 progressbar_simulation_result, table_simulation_result, table_simulation_result_list)

        if 'enable_simulation_tab' in user_info:
            # Only works in PyQT 5.15
            if user_info['enable_simulation_tab'] == "true":
                # Show the simulation tab widget
                for i in range(self.simulation_tab_widget.count()):
                    self.simulation_tab_widget.setTabVisible(i, True)
        else:
            # Hide simulation tab widget, but show the property widget
            for i in range(1, self.simulation_tab_widget.count()):
                self.simulation_tab_widget.setTabVisible(i, False)
        
        """ View Buttons """
        rbtn_view_select = self.findChild(QRadioButton, 'rbtn_view_select')
        rbtn_view_trans = self.findChild(QRadioButton, 'rbtn_view_trans')
        rbtn_view_rotate = self.findChild(QRadioButton, 'rbtn_view_rotate')

        rbtn_view_select.setVisible(False)
        rbtn_view_trans.setVisible(False)
        rbtn_view_rotate.setVisible(False)
        
        btn_view_xy = self.findChild(QPushButton, 'btn_view_xy')
        btn_view_yz = self.findChild(QPushButton, 'btn_view_yz')
        btn_view_zx = self.findChild(QPushButton, 'btn_view_zx')
        btn_view_south = self.findChild(QPushButton, 'btn_view_south')

        rbtn_view_select.clicked.connect(lambda:self.canvas.setViewMode('view_select'))
        rbtn_view_trans.clicked.connect(lambda:self.canvas.setViewMode('view_trans'))
        rbtn_view_rotate.clicked.connect(lambda:self.canvas.setViewMode('view_rotate'))

        btn_view_xy.clicked.connect(lambda:self.canvas.setViewMode('view_xy'))
        btn_view_yz.clicked.connect(lambda:self.canvas.setViewMode('view_yz'))
        btn_view_zx.clicked.connect(lambda:self.canvas.setViewMode('view_zx'))
        btn_view_south.clicked.connect(lambda:self.canvas.setViewMode('south'))

        """ Files """
        action_load_mgeo = self.findChild(QAction, 'action_load_mgeo')
        action_load_mgeo.setShortcut('Ctrl+L')
        action_load_mgeo.triggered.connect(
            lambda:self.file_io_funcs.load_mgeo(self.initiallyDisabledMenu, program_name))
        
        # Add MGeo
        if 'add_mgeo' not in user_info['exclude_file_actions']:   
            self.menu_file_add_mgeo.setShortcut('Ctrl+A')
            self.menu_file_add_mgeo.triggered.connect(
                lambda:self.file_io_funcs.add_mgeo()
            )
        else:
            self.menu_files.removeAction(self.menu_file_add_mgeo)
        
        action_save_mgeo = self.findChild(QAction, 'action_save_mgeo')
        if 'mgeo_save' not in user_info['exclude_file_actions']:     
            action_save_mgeo.setShortcut('Ctrl+S')
            action_save_mgeo.triggered.connect(
                self.file_io_funcs.save_mgeo)
        else:
            self.menu_files.removeAction(action_save_mgeo)

        # MScenario 동작 연결 or 숨기기
        action_load_mscenario = self.findChild(QAction, 'action_load_mscenario')
        action_save_mscenario = self.findChild(QAction, 'action_save_mscenario')
        if 'mscenario' not in user_info['exclude_file_actions']:
            action_load_mscenario.triggered.connect(
                lambda:self.file_io_funcs.load_mscenario(self.initiallyDisabledMenu))
            action_save_mscenario.triggered.connect(
                self.file_io_funcs.save_mscenario)
        else:
            self.menu_files.removeAction(action_load_mscenario)
            self.menu_files.removeAction(action_save_mscenario)
        
        action_exit = self.findChild(QAction, 'action_exit')
        action_exit.triggered.connect(self.close)

        action_merge_mgeo = self.findChild(QAction, 'actionMerge_MGeo')
        if 'merge_mgeo' not in user_info['exclude_file_actions']:
            action_merge_mgeo.triggered.connect(
                lambda:self.file_io_funcs.merge_mgeo(self.initiallyDisabledMenu))
        else:
            self.menu_files.removeAction(action_merge_mgeo)
        

        """ Import & Export """
        action_import_42dot = self.findChild(QAction, 'action_import_42dot')
        if self.check_user_import_info(user_info, '42dot'): 
            action_import_42dot.setShortcut('Ctrl+I')
            action_import_42dot.triggered.connect(
                lambda:self.file_io_funcs.import_42dot(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_42dot)

        action_export_odr = self.findChild(QAction, 'action_export_odr')
        action_export_odr.setShortcut('Ctrl+E')
        action_export_odr.triggered.connect(
            self.file_io_funcs.export_odr)
        
        actionApollo_OpenDRIVE_xml = self.findChild(QAction, 'actionApollo_OpenDRIVE_xml')
        actionApollo_OpenDRIVE_xml.setShortcut('Ctrl+Q')
        actionApollo_OpenDRIVE_xml.triggered.connect(
            self.file_io_funcs.export_apollo)

        action_export_csv = self.findChild(QAction, 'action_export_csv')
        action_export_csv.triggered.connect(
            self.file_io_funcs.export_csv)
                    
        action_export_obj = self.findChild(QAction, 'action_export_obj')
        action_export_obj.triggered.connect(
            self.file_io_funcs.export_obj)
        
        # geojson으로 export
        action_export_geojson = self.findChild(QAction, 'actionGeoJSON_geojson')
        # action_export_odr.setShortcut('Ctrl+E')
        action_export_geojson.triggered.connect(
            self.file_io_funcs.export_geojson)
        
        action_export_path_csv = self.findChild(QAction, 'action_export_path_csv')
        action_export_path_csv.triggered.connect(
            self.file_io_funcs.export_path_csv)
        
        action_export_oicd = self.findChild(QAction, 'actionOICD_oicd')
        if 'oicd' not in user_info['exclude_export_actions']:
            action_export_oicd.triggered.connect(
                self.file_io_funcs.export_oicd)
            
        else:
            self.menu_export.removeAction(action_export_oicd)
        



        # import shp
        # importNGII1Action = self.findChild(QAction, 'actionImport_NGII_Shp_Ver1_Node_Link')
        # if self.check_user_import_info(user_info, 'NGII_Shp_Ver1_Node_Link'): 
        #     importNGII1Action.triggered.connect(lambda:self.file_io_funcs.import_ngii_shp1(self.initiallyDisabledMenu))
        # else:
        #     self.menu_import.removeAction(importNGII1Action)

        importNGII1LaneMarkingAction = self.findChild(QAction, 'actionImport_NGII_Shp_Ver1_Lane_Marking_Data')
        if self.check_user_import_info(user_info, 'NGII_Shp_Ver1_Lane_Marking_Data'): 
            importNGII1LaneMarkingAction.triggered.connect(lambda:self.file_io_funcs.import_ngii_shp1_lane_marking(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(importNGII1LaneMarkingAction)

        # importNGII2Action = self.findChild(QAction, 'actionImport_NGII_Shp_Ver2')
        # if self.check_user_import_info(user_info, 'NGII_Shp_Ver2'): 
        #     importNGII2Action.triggered.connect(lambda:self.file_io_funcs.import_ngii_shp2(self.initiallyDisabledMenu))
        # else:
        #     self.menu_import.removeAction(importNGII2Action)

        importNGII2LaneMarkingAction = self.findChild(QAction, 'actionImport_NGII_Shp_Ver2_Lane_Marking_Data')
        if self.check_user_import_info(user_info, 'NGII_Shp_Ver2_Lane_Marking_Data'): 
            importNGII2LaneMarkingAction.triggered.connect(lambda:self.file_io_funcs.import_ngii_shp2_lane_marking(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(importNGII2LaneMarkingAction)

        action_import_txt = self.findChild(QAction, 'action_import_txt')
        if self.check_user_import_info(user_info, 'txt'):
            action_import_txt.triggered.connect(lambda:self.file_io_funcs.import_txt(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_txt)

        action_import_roadrunner = self.findChild(QAction, 'action_import_roadrunner')
        if self.check_user_import_info(user_info, 'roadrunner'):
            action_import_roadrunner.triggered.connect(lambda:self.file_io_funcs.import_roadrunner_geojson(self.initiallyDisabledMenu, program_name))
        else:
            self.menu_import.removeAction(action_import_roadrunner)
        
        action_import_opendrive = self.findChild(QAction, 'action_import_OpenDRIVE')
        if self.check_user_import_info(user_info, 'opendrive'):
            action_import_opendrive.triggered.connect(lambda:self.file_io_funcs.import_OpenDRIVE(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_opendrive)
        
        action_load_openscenario = self.findChild(QAction, 'action_load_openscenario') 
        if 'openscenario' not in user_info['exclude_file_actions']:     
            action_load_openscenario.triggered.connect(lambda:self.import_scenario())
        else:
            self.menu_files.removeAction(action_load_openscenario)
        
        action_save_openscenario = self.findChild(QAction, 'action_save_openscenario')
        if 'openscenario' not in user_info['exclude_file_actions']:
            action_save_openscenario.triggered.connect(self.file_io_funcs.save_openscenario)
        else:
            self.menu_files.removeAction(action_save_openscenario)
            
        action_create_new_openscenario = self.findChild(QAction, 'action_new_scenario')
        if 'openscenario' not in user_info['exclude_file_actions']:
            action_create_new_openscenario.triggered.connect(lambda:self.create_new_open_scenario())
        else:
            self.menu_files.removeAction(action_create_new_openscenario)

        # Import Lanelet2
        action_import_lanelet2 = self.findChild(QAction, 'action_import_Lanelet2')
        if self.check_user_import_info(user_info, 'lanelet2'):
            action_import_lanelet2.triggered.connect(lambda:self.file_io_funcs.import_Lanelet2(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_lanelet2)

        """ HDMap importer """
        # import stryx
        action_import_stryx = self.findChild(QAction, 'actionImport_Stryx')
        if self.check_user_import_info(user_info, 'Stryx'):
            action_import_stryx.triggered.connect(lambda:self.file_io_funcs.import_stryx(self.initiallyDisabledMenu))     
        else:
            self.menu_import.removeAction(action_import_stryx)

        # import naver
        action_import_naver = self.findChild(QAction, 'actionImport_Naver')
        if self.check_user_import_info(user_info, 'Naver'):
            action_import_naver.triggered.connect(lambda:self.file_io_funcs.import_naver(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_naver)

        # import DeepMap
        action_import_deepmap = self.findChild(QAction, 'actionImport_DeepMap')
        if self.check_user_import_info(user_info, 'DeepMap'):
            action_import_deepmap.triggered.connect(lambda:self.file_io_funcs.import_deepmap(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_deepmap)

        # import TomTom
        action_import_tomtom_avro = self.findChild(QAction, 'actionImport_TomTom_avro')
        if self.check_user_import_info(user_info, 'TomTom_avro'):
            action_import_tomtom_avro.triggered.connect(lambda:self.file_io_funcs.import_tomtom(self.initiallyDisabledMenu, 'avro', program_name))
        else:
            self.menu_import.removeAction(action_import_tomtom_avro)

        action_import_tomtom_shp = self.findChild(QAction, 'actionImport_TomTom_shp')
        if self.check_user_import_info(user_info, 'TomTom_shp'):
            action_import_tomtom_shp.triggered.connect(lambda:self.file_io_funcs.import_tomtom(self.initiallyDisabledMenu, 'shp', program_name))
        else:
            self.menu_import.removeAction(action_import_tomtom_shp)

        action_import_tomtom_geojson = self.findChild(QAction, 'actionImport_TomTom_geojson')
        if self.check_user_import_info(user_info, 'TomTom_geojson'):
            action_import_tomtom_geojson.triggered.connect(lambda:self.file_io_funcs.import_tomtom(self.initiallyDisabledMenu, 'geojson', program_name))
        else:
            self.menu_import.removeAction(action_import_tomtom_geojson)

        # import Civilmaps
        action_import_civilmaps = self.findChild(QAction, 'actionImport_Civilmaps')
        if self.check_user_import_info(user_info, 'Civilmaps'):
            action_import_civilmaps.triggered.connect(lambda:self.file_io_funcs.import_civilmaps(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_civilmaps)
        
        # import Mobiltech
        action_import_Mobiltech = self.findChild(QAction, 'actionImport_Mobiltech')
        if self.check_user_import_info(user_info, 'Mobiltech'):
            action_import_Mobiltech.triggered.connect(lambda:self.file_io_funcs.import_mobiltech(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_Mobiltech)
        
        # import rad-r
        action_import_RAD_R = self.findChild(QAction, 'actionImport_RAD_R')
        if self.check_user_import_info(user_info, 'hyundai'):
            action_import_RAD_R.triggered.connect(lambda:self.file_io_funcs.import_rad_r_data(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_RAD_R)

            
        # import mgeo geojson
        actionImport_MGeo_geojson = self.findChild(QAction, 'actionImport_MGeo_geojson')
        actionImport_MGeo_geojson.triggered.connect(lambda:self.file_io_funcs.import_mgeo_geojson(self.initiallyDisabledMenu))
        

        # import kakaomobility
        action_import_kakaomobility = self.findChild(QAction, 'actionKakaomobility')
        if self.check_user_import_info(user_info, 'Kakaomobility'):
            action_import_kakaomobility.triggered.connect(lambda:self.file_io_funcs.import_kakaomobility(self.initiallyDisabledMenu))
        else:
            self.menu_import.removeAction(action_import_kakaomobility)

        """
        Export Simulation Data
        - Simulation Map Build Data (Lane) > actionExport_Lane_Mesh 하기 전에, action_simplify_lane
        - Simulation Map Build Data (Road) > actionExport_Road_Mesh 한기 전에, action_fill_lane_point
        1. Simulation Map Build Data (All) > actionSimulation_Map_Build_Data_All
        2. Simulation Map Build Data (TS only) > actionSimulation_Map_Build_Data_TS_only
        3. Simulation Map Build Data (TL only) > actionSimulation_Map_Build_Data_TL_only
        4. Simulation Map Build Data (SM only) > actionSimulation_Map_Build_Data_SM_only
        """
        
        # Export Lane Mesh 관련 메뉴(find/fix overlapped node 는 이미 있음)
        action_simplify_lane = self.findChild(QAction, 'action_simplify_lane')
        action_simplify_lane.triggered.connect(self.file_io_funcs.simplify_lane_markings)        
        
        action_fill_lane_point = self.findChild(QAction, 'action_fill_lane_point')
        action_fill_lane_point.triggered.connect(self.file_io_funcs.fill_points_in_lane_markings)        
        
        action_export_Lane_Mesh = self.findChild(QAction, 'actionExport_Lane_Mesh')
        action_export_Road_Mesh = self.findChild(QAction, 'actionExport_Road_Mesh')
        action_export_Structure_Mesh = self.findChild(QAction, 'actionExport_Structure_Mesh')
        export_sim_map_data = self.findChild(QAction, 'actionSimulation_Map_Build_Data_All')
        export_sim_TS_data = self.findChild(QAction, 'actionSimulation_Map_Build_Data_TS_only')
        export_sim_TL_data = self.findChild(QAction, 'actionSimulation_Map_Build_Data_TL_only')
        export_sim_SM_data = self.findChild(QAction, 'actionSimulation_Map_Build_Data_SM_only')

        if 'sim_build_data' not in user_info['exclude_export_actions']:
            action_export_Lane_Mesh.triggered.connect(lambda:self.file_io_funcs.export_sim_data('Lane'))     
            action_export_Road_Mesh.triggered.connect(lambda:self.file_io_funcs.export_sim_data('Road'))      
            action_export_Structure_Mesh.triggered.connect(lambda:self.file_io_funcs.export_sim_data('Structure'))      
            export_sim_map_data.triggered.connect(lambda:self.file_io_funcs.export_sim_data('ALL'))
            export_sim_TS_data.triggered.connect(lambda:self.file_io_funcs.export_sim_data('TS'))
            export_sim_TL_data.triggered.connect(lambda:self.file_io_funcs.export_sim_data('TL'))
            export_sim_SM_data.triggered.connect(lambda:self.file_io_funcs.export_sim_data('SM'))  
        else:
            self.menu_export.removeAction(action_export_Lane_Mesh)
            self.menu_export.removeAction(action_export_Road_Mesh)
            self.menu_export.removeAction(export_sim_map_data)
            self.menu_export.removeAction(export_sim_TS_data)
            self.menu_export.removeAction(export_sim_TL_data)
            self.menu_export.removeAction(export_sim_SM_data)


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

        action_lane_mark = self.findChild(QAction, 'action_lane_mark')
        action_lane_mark.setShortcut('SHIFT+M')
        
        action_find_single_crosswalk = self.findChild(QAction, 'action_find_single_crosswalk')
                
        action_find_crosswalk = self.findChild(QAction, 'action_find_crosswalk')
        action_find_road_polygon = self.findChild(QAction, 'action_find_road_polygon')
        
        # id 입력할 수 있도록 창 띄우기 
        actionFind.triggered.connect(self.canvas.find_by_mgeo_id)
        
        action_node.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Node'))
        action_link.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Link'))
        action_ts.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Traffic Sign'))
        action_tl.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Traffic Light'))
        action_jct.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Junction'))
        action_road.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Road'))
        action_lane_mark.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Lane Marking'))
        action_find_single_crosswalk.triggered.connect(lambda:self.canvas.action_input_mgeo_id('SingleCrosswalk'))
        action_find_crosswalk.triggered.connect(lambda:self.canvas.action_input_mgeo_id('Crosswalk'))
        action_find_road_polygon.triggered.connect(lambda:self.canvas.action_input_mgeo_id('RoadPolygon'))

        """ Basic Edit """
        actionUndo = self.findChild(QAction, 'actionUndo')
        if actionUndo != None:
            actionUndo.setShortcut('Ctrl+Z')
            actionUndo.triggered.connect(self.command_manager.undo)
            #actionUndo.triggered.connect(self.canvas.show_not_supported_warning)

        actionRedo = self.findChild(QAction, 'actionRedo')
        if actionRedo != None:
            actionRedo.setShortcut('Ctrl+Y')
            actionRedo.triggered.connect(self.command_manager.redo)
            #actionRedo.triggered.connect(self.canvas.show_not_supported_warning)

        action_divide_a_link_smart = self.findChild(QAction, 'action_divide_a_link_smart')
        action_divide_a_link_smart.setShortcut('Ctrl+D')
        action_divide_a_link_smart.triggered.connect(
            self.canvas.divide_a_link_smart)

        action_divide_a_link_keep_front = self.findChild(QAction, 'action_divide_a_link_keep_front')
        action_divide_a_link_keep_front.triggered.connect(
            lambda:self.canvas.divide_a_line(keep_front=True))

        action_divide_a_link_keep_rear = self.findChild(QAction, 'action_divide_a_link_keep_rear')
        action_divide_a_link_keep_rear.triggered.connect(
            lambda:self.canvas.divide_a_line(keep_front=False))

        action_merge_links = self.findChild(QAction, 'action_merge_links')
        action_merge_links.triggered.connect(self.canvas.merge_links)

        action_reverse_link_points = self.findChild(QAction, 'action_reverse_link_points')
        action_reverse_link_points.triggered.connect(self.canvas.reverse_link_points)

        action_connect_nodes = self.findChild(QAction, 'action_connect_nodes')
        action_connect_nodes.triggered.connect(self.canvas.connect_nodes)

        action_add_link_point = self.findChild(QAction, 'action_add_link_point')
        action_add_link_point.triggered.connect(
            self.canvas.add_link_point)
        action_add_link_point.setShortcut('Ctrl+Shift+A')

        action_gen_road_poly = self.findChild(QAction, 'action_gen_road_poly')
        action_gen_road_poly.triggered.connect(self.canvas.gen_road_poly)

        action_set_new_road_id = self.findChild(QAction, 'action_set_new_road_id')
        action_set_new_road_id.triggered.connect(
            lambda:self.canvas.set_new_road_id(
                build_preliminary_road_callback=self.odr_conversion_funcs.create_prelimiary_odr_roads
            ))

        """ Scenario Runner Edit"""
        action_add_vehicle = self.findChild(QAction, 'action_add_vehicle')
        action_add_vehicle.triggered.connect(self.canvas.add_vehicle)
        action_add_pedestrian = self.findChild(QAction, 'action_add_pedestrian')
        action_add_pedestrian.triggered.connect(self.canvas.add_pedestrian)
        action_add_misc_object = self.findChild(QAction, 'action_add_misc_object')
        action_add_misc_object.triggered.connect(self.canvas.add_misc_object)
        action_add_event = self.findChild(QAction, 'action_add_event')
        action_add_event.triggered.connect(self.canvas.add_event)
        
        """ Traffic Vehicle """
        # Junction 생성 기능
        action_create_junction = self.findChild(QAction, 'action_create_junction')
        action_create_junction.triggered.connect(
            self.canvas.create_junction)
        
        action_auto_create_junction = self.findChild(QAction, 'action_auto_create_junction')
        action_auto_create_junction.triggered.connect(
            self.canvas.auto_create_junction)

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

        action_geometry_points_delete_all_line = self.findChild(QAction, 'action_delete_all_points_all')
        action_geometry_points_delete_all_line.triggered.connect(
            self.canvas.delete_geometry_points_all_line)

        # 차선변경 링크 만들기
        action_create_lane_change_links = self.findChild(QAction, 'actionCreate_Lane_Change_Links')
        action_create_lane_change_links.triggered.connect(self.canvas.create_lane_change_links)

        action_delete_lane_change_links = self.findChild(QAction, 'actionDelete_Lane_Change_Links')
        action_delete_lane_change_links.triggered.connect(self.canvas.delete_lane_change_links)
        
        action_fill_points_in_all_links = self.findChild(QAction, 'actionFill_Points_in_Links')
        action_fill_points_in_all_links.triggered.connect(self.canvas.fill_points_in_all_links)

        # 신호등, 표지판에 헤딩 넣기
        action_Cal_direction_of_the_traffic_signals = self.findChild(QAction, 'action_Cal_direction_of_the_traffic_signals')
        action_Cal_direction_of_the_traffic_signals.triggered.connect(self.canvas.cal_heading_of_the_traffic_signal)

        """World Settings"""
        actionChange_World_Projection = self.findChild(QAction, 'actionChange_World_Projection')
        actionChange_World_Projection.triggered.connect(self.canvas.changeWorldProjection)
        
        actionChange_World_Origin = self.findChild(QAction, 'actionChange_World_Origin')
        actionChange_World_Origin.triggered.connect(self.canvas.change_origin)

        actionChange_Workspace_Origin = self.findChild(QAction, 'actionChange_Workspace_Origin')
        actionChange_Workspace_Origin.triggered.connect(self.canvas.show_not_supported_warning)

        actionChange_Region_Localization = self.findChild(QAction, 'actionChange_Region_Localization')
        actionChange_Region_Localization.triggered.connect(self.canvas.change_region_localization)

        """ OpenDRIVE Conversion """
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

        # OpenDRIVE 생성 기능 (Legacy)
        action_create_road_objects_legacy = self.findChild(QAction, 'action_create_road_objects_legacy')
        action_create_road_objects_legacy.triggered.connect(
            lambda: self.odr_conversion_funcs.create_odr_roads(legacy=True))

        action_create_opendrive_legacy = self.findChild(QAction, 'action_create_opendrive_legacy')
        action_create_opendrive_legacy.triggered.connect(
            lambda: self.odr_conversion_funcs.create_complete_odr_data(legacy=True))     
        
        # Run with Esmini 생성 기능
        action_run_with_esmini = self.findChild(QAction, 'action_run_with_esmini')            
        action_run_with_esmini.triggered.connect(
            lambda: self.esmini_conversion_funcs.showDialog())

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


        """ Data Integrity """
        # Data에러 수정 기능 >> Node 데이터 유무에 따라서 enable/disable 하도록 만들기
        action_find_overlapped_node = self.findChild(QAction, 'action_find_overlapped_node_')
        action_repair_overlapped_node = self.findChild(QAction, 'action_repair_overlapped_node')
        action_find_dangling_nodes = self.findChild(QAction, 'action_find_dangling_nodes')
        action_delete_dangling_nodes = self.findChild(QAction, 'action_delete_dangling_nodes')
        action_find_end_nodes = self.findChild(QAction, 'action_find_end_nodes')
        action_find_stop_line_nodes = self.findChild(QAction, 'actionFind_Stop_Line_Nodes')
        action_find_dangling_links = self.findChild(QAction, 'action_find_dangling_links')
        action_fix_dangling_links = self.findChild(QAction, 'action_fix_dangling_links')
        action_find_location_error_link = self.findChild(QAction, 'action_find_location_error_link')
        action_find_closed_loop_link = self.findChild(QAction, 'action_find_closed_loop_link')
        action_delete_closed_loop_link = self.findChild(QAction, 'action_delete_closed_loop_link')
        action_find_opposite_direction_link = self.findChild(QAction, 'action_find_opposite_direction_link')
        action_find_duplicated_link = self.findChild(QAction, 'action_find_duplicated_link')
        action_find_lane_change_mismatch = self.findChild(QAction, 'action_find_lane_change_mismatch')
        action_find_empty_related_signal_link = self.findChild(QAction, 'action_find_empty_related_signal_link')
        action_find_short_link = self.findChild(QAction, 'action_find_short_link')
        action_repair_short_link = self.findChild(QAction, 'action_repair_short_link')
        action_fix_signal_road_connection = self.findChild(QAction, 'action_fix_signal_road_connection')
        action_find_intersecting_links = self.findChild(QAction, 'action_find_intersecting_links')
        action_check_intersection_vicinity = self.findChild(QAction,'actionCheck_Intersection_Vicinity')
        action_clear = self.findChild(QAction, 'action_clear')
        
        action_set_max_speed_link = self.findChild(QAction, 'action_set_max_speed_link')

        # find overlapped node는 node 데이터 있으면 enable, repair 후에는 disable ++ overlapped node 데이터 없으면 disable
        action_find_overlapped_node.triggered.connect(
            lambda:self.error_fix_funcs.find_overlapped_node(
                action_repair_overlapped_node, action_clear))

        # repair overlapped node 수행 후에 find overlapped node, repair overlapped node action disable
        action_repair_overlapped_node.triggered.connect(
            lambda:self.error_fix_funcs.repair_overlapped_node(
                action_repair_overlapped_node))
        
        # find short link는 짧은 link 데이터 있을 경우 enable, repair 이후 short link action disable
        action_find_short_link.triggered.connect(
            lambda:self.error_fix_funcs.find_short_link(
                action_repair_short_link, action_clear))
        
        # repair short link 수행 후에 find short link, repair short link action disable
        action_repair_short_link.triggered.connect(
            lambda:self.error_fix_funcs.repair_short_link(
                action_repair_short_link))

        # find dangling node는 node 데이터 있으면 enable, delete 후에는 disable ++ dangling node 데이터 없으면 disable
        action_find_dangling_nodes.triggered.connect(
            lambda:self.error_fix_funcs.find_dangling_nodes(
                action_delete_dangling_nodes, action_clear))
        
        # delete dangling node 수행 후에 find dangling node, delete overlapped node action disable
        action_delete_dangling_nodes.triggered.connect(
            lambda:self.error_fix_funcs.delete_dangling_nodes(
                action_delete_dangling_nodes))

        action_find_end_nodes.triggered.connect(
            lambda:self.error_fix_funcs.find_end_nodes(
                action_clear))

        action_find_stop_line_nodes.triggered.connect(self.error_fix_funcs.highlight_on_stop_line)

        # find dangling link는 link 데이터 있으면 enable, fix 후에는 disable ++ dangling link 데이터 없으면 disable
        action_find_dangling_links.triggered.connect(
            lambda:self.error_fix_funcs.find_dangling_links(
                action_find_dangling_links, action_clear, action_fix_dangling_links))

        action_fix_dangling_links.triggered.connect(
            lambda:self.error_fix_funcs.fix_dangling_links(
                action_fix_dangling_links, action_clear))

        action_find_location_error_link.triggered.connect(
            lambda:self.error_fix_funcs.find_location_error_link(action_find_location_error_link, action_clear))

        action_find_closed_loop_link.triggered.connect(
            lambda:self.error_fix_funcs.find_closed_loop_link(action_clear))

        action_delete_closed_loop_link.triggered.connect(
            lambda:self.error_fix_funcs.delete_closed_loop_link(action_clear))
        
        action_find_opposite_direction_link.triggered.connect(
            lambda:self.error_fix_funcs.find_opposite_direction_link(action_clear))

        action_find_duplicated_link.triggered.connect(
            lambda:self.error_fix_funcs.find_duplicated_link(action_clear))
        
        action_find_lane_change_mismatch.triggered.connect(
            lambda:self.error_fix_funcs.find_mismatch_lane_change())

        action_find_empty_related_signal_link.triggered.connect(
            lambda:self.error_fix_funcs.find_empty_related_signal_link(action_find_empty_related_signal_link, action_clear))

        action_fix_signal_road_connection.triggered.connect(
            lambda:self.error_fix_funcs.fix_signal_road_connection())
        
        # ADD: 11/9/2021 [SHJ]
        action_find_intersecting_links.triggered.connect(
            lambda:self.error_fix_funcs.find_intersecting_links())
        
        # action_check_intersection_vicinity.triggered.connect(self.canvas.check_intersection_vicinity(action_clear))
        action_check_intersection_vicinity.triggered.connect(
            lambda action_clear:self.canvas.check_intersection_vicinity)
        
        action_set_max_speed_link.triggered.connect(self.canvas.set_max_speed_link)

        # highlight, overlapped node, dangling node list clear시에 clear action disable
        action_clear.triggered.connect(
            lambda:self.error_fix_funcs.clear_highlight(
                [action_repair_overlapped_node, action_delete_dangling_nodes],  # trigger 이후 disable 되어야하는 기능 
                action_clear)) # trigger 이후 disable 되어야하는 기능

        actionGet_Simulation_Point = self.findChild(QAction, 'action_get_position_in_carla')
        actionGet_Simulation_Point.triggered.connect(self.canvas.get_simulation_point)
        actionGet_Simulation_Point.setShortcut('Ctrl+G')
        
        action_repair_overlapped_node.setDisabled(True)
        action_delete_dangling_nodes.setDisabled(True)
        action_fix_dangling_links.setDisabled(True)
        action_clear.setDisabled(True)
        
        # singlecrosswalk 자전거 횡단보도 연결 찾기
        action_find_concave_polygon = self.findChild(QAction, 'action_find_concave_polygon')
        action_find_concave_polygon.triggered.connect(self.canvas.find_concave_polygon)
        action_repair_concave_polygon = self.findChild(QAction, 'action_repair_concave_polygon')
        action_repair_concave_polygon.triggered.connect(self.canvas.repair_concave_polygon)

        # tomtom juction error 
        action_find_junction_error = self.findChild(QAction, 'action_find_junction_error')
        action_find_junction_error.triggered.connect(self.error_fix_funcs.find_junction_error)
        action_repair_junction_error_incoming = self.findChild(QAction, 'action_repair_junction_error_incoming')
        action_repair_junction_error_incoming.triggered.connect(self.error_fix_funcs.repair_junction_error_incoming)
        action_repair_junction_error_split = self.findChild(QAction, 'action_repair_junction_error_split')
        action_repair_junction_error_split.triggered.connect(self.error_fix_funcs.repair_junction_error_split)
        
        # 중첩된 라인 찾기.
        action_find_duplicated_lane = self.findChild(QAction, 'action_find_duplicated_lane')
        action_find_duplicated_lane.triggered.connect(lambda:self.error_fix_funcs.find_duplicated_lane())

        # [210705] ngii ver2에 대해 로드 아이디, 링크 - 차선 연결 오류 찾기
        action_fix_road_id_assignments = self.findChild(QAction, 'action_fix_road_id_assignments')
        action_fix_road_id_assignments.triggered.connect(self.canvas.fix_road_id_assignments)

        action_find_missing_Lane_Marking = self.findChild(QAction, 'action_find_missing_Lane_Marking')
        action_find_missing_Lane_Marking.triggered.connect(self.canvas.find_missing_lane_marking)

        # [211027] ngii ver2 신호등 관련 수작업 변경사항 찾기
        action_change_NGII_map_to_MGeo = self.findChild(QAction, 'actionChange_NGII_map_to_MGeo')
        action_change_NGII_map_to_MGeo.triggered.connect(self.error_fix_funcs.change_ngii_to_mgeo)

        action_Make_Intersection_TL = self.findChild(QAction, 'actionMake_Intersection_TL')
        action_Make_Intersection_TL.triggered.connect(self.canvas.action_make_intersecion_tl)

        # 13. Misc
        action_change_ids_to_string = self.findChild(QAction, 'action_change_ids_to_string')
        action_change_ids_to_string.triggered.connect(self.canvas.change_all_item_id_to_string)

        """Help"""
        actionUser_Manual = self.findChild(QAction, 'actionUser_Manual')
        actionUser_Manual.triggered.connect(lambda:self.canvas.open_user_manual(user_info['user_manual_url']))

        actionAbout = self.findChild(QAction, 'actionAbout')
        actionAbout.triggered.connect(lambda:self.canvas.open_about(user_info['program_name'], user_info['program_name'], about_contents))

        """LaneLet Convert"""
        action_convert_lanelet2 = self.findChild(QAction, 'action_convert_lanelet2')
        action_convert_lanelet2.triggered.connect(lambda: self.file_io_funcs.export_osm(self.osm_conversion_funcs))
        
        # OpenScenario 메뉴
        action_start_openscenario = self.findChild(QAction, 'actionStart_Scenario')
        action_stop_openscenario = self.findChild(QAction, 'actionStop_Scenario')

        action_start_openscenario.triggered.connect(lambda: self.start_scenario())
        action_stop_openscenario.triggered.connect(lambda: self.stop_batch_scenario())

        action_start_openscenario.setEnabled(True)
        action_stop_openscenario.setEnabled(False)

        action_create_path_from_selected_links_openscenario = self.findChild(QAction, 'actionCreate_Path_from_Selected_Links')
        action_create_path_from_selected_links_openscenario.triggered.connect(self.canvas.create_path_from_selected_links)

        action_create_path_from_start_end_points_openscenario = self.findChild(QAction, 'actionCreate_Path_from_Start_End_Points')
        action_create_path_from_start_end_points_openscenario.triggered.connect(self.canvas.create_path_from_start_and_end_point)

        action_create_path_from_start_and_stop_and_end_point_openscenario = self.findChild(QAction, 'actionCreate_Path_from_Start_Stop_End_Points')
        action_create_path_from_start_and_stop_and_end_point_openscenario.triggered.connect(self.canvas.create_path_from_start_and_stop_and_end_point)
        
        action_reset_all_openscenario = self.findChild(QAction, 'actionReset_All')
        action_reset_all_openscenario.triggered.connect(self.canvas.reset_all)

        action_reset_path_openscenario = self.findChild(QAction, 'actionReset_Path')
        action_reset_path_openscenario.triggered.connect(self.canvas.reset_path)

        action_reset_start_points = self.findChild(QAction, 'actionReset_Start_Points')
        action_reset_start_points.triggered.connect(self.canvas.reset_start_point)

        action_reset_stop_points = self.findChild(QAction, 'actionReset_Stop_Point')
        action_reset_stop_points.triggered.connect(self.canvas.reset_stop_point)
        
        action_reset_end_points = self.findChild(QAction, 'actionReset_End_Point')
        action_reset_end_points.triggered.connect(self.canvas.reset_end_point)

        # 아직 지원하지 않는 OpenScenario 메뉴 삭제
        if 'exclude_scenario_actions' in user_info:
            for scenario_action in user_info['exclude_scenario_actions']:
               action_openscenario = self.findChild(QAction, scenario_action)
               self.menu_scenario.removeAction(action_openscenario)

        # position_label에 현재 World 위치 넣으려고
        self.label_range_x = self.findChild(QLabel, 'label_range_x')
        self.label_range_y = self.findChild(QLabel, 'label_range_y')
        self.label_zoom = self.findChild(QLabel, 'label_zoom')
        self.canvas.position_label = [self.label_range_x, self.label_range_y, self.label_zoom]        
    
    def closeEvent(self, event):
        result = QMessageBox.question(self, self.windowTitle(), 'Do you really want to close editor?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        if result == QMessageBox.Ok:
            event.accept()            
            # self.session_trhead.cancel()
            # print("session thread kill")
            try:
                self.launcher_ex.show_launcher()
            except:
                pass        # launcher window doesn't exist if the authentication key is valid
        elif result == QMessageBox.Cancel:
            event.ignore()

    def show_loading(self, loading_text):
        self.loading_dialog = LoadingDialog(self, loading_text)
        self.loading_dialog.show_loading()

    def close_loading(self):
        self.loading_dialog.close()

        if self.scheduled_callback_func is not None:
            self.scheduled_callback_func()
            self.scheduled_callback_func = None
            
    def __init_run_with_esmini_funcs(self, canvas):
        odr_viewer_init_path = self.file_io_funcs.get_path_from_config('ODR_VIEWER')
        xodr_init_path = self.file_io_funcs.get_path_from_config('XODR')
        self.esmini_param_widget = EsminiEditor(odr_viewer_init_path, xodr_init_path, self.file_io_funcs)
        return self.esmini_param_widget
    
    def create_new_open_scenario(self):
        self.scheduled_callback_func = self.import_scenario_callback
        self.open_scenario_importer = OpenScenarioImporter()
        self.file_io_funcs.create_new_openscenario(self.open_scenario_importer)

    def set_menu_disable(self, isActive):
        # ui menu hide 하는 로직 작성
        if self.findChild(QMenu, 'menuImport') is not None:
            self.findChild(QMenu, 'menuImport').setDisabled(isActive)

        if self.findChild(QMenu, 'menuFileImport') is not None:
            self.findChild(QMenu, 'menuFileImport').setDisabled(isActive)

        if self.findChild(QAction, 'action_load_mgeo') is not None:
            self.findChild(QAction, 'action_load_mgeo').setDisabled(isActive)

        if self.findChild(QAction, 'action_load_mscenario') is not None:
            self.findChild(QAction, 'action_load_mscenario').setDisabled(isActive)

        if self.findChild(QAction, 'actionMerge_MGeo') is not None:
            self.findChild(QAction, 'actionMerge_MGeo').setDisabled(isActive)
        
        for menu in self.initiallyDisabledMenu:
            if menu is not None:
                menu.setDisabled(isActive)
    
        # actionMerge_MGeo

    # import scenario
    def import_scenario(self, file_path=None):
        self.scheduled_callback_func = self.import_scenario_callback
        self.open_scenario_importer = OpenScenarioImporter()
        self.file_io_funcs.import_OpenScenario(self.open_scenario_importer, file_path)
    
    def import_scenario_callback(self):
        if self.open_scenario_importer.mgeo is None or self.open_scenario_importer.scenario_definition is None:
            return

        # node data 유/무에 따라 (find_overlapped_node, find_dangling_nodes) menu action enable
        if self.open_scenario_importer.mgeo.node_set is None:
            for action in self.initiallyDisabledMenu:
                action.setDisabled(True)
        else:
            for action in self.initiallyDisabledMenu:
                action.setDisabled(False)

        # import 결과 UI에 반영
        self.file_io_funcs.mgeo_planner_map = self.open_scenario_importer.mgeo
        map_name = self.open_scenario_importer.folder_path.split('\\')[-1]
        self.file_io_funcs.mgeo_maps_dict.clear()
        self.file_io_funcs.mgeo_maps_dict[map_name] = self.open_scenario_importer.mgeo
        self.canvas.setMGeoPlannerMap(self.file_io_funcs.mgeo_maps_dict)
        self.canvas.set_open_scenario(self.open_scenario_importer)
        self.canvas.updateTreeWidget()
        # Reset camera position
        try:
            self.canvas.resetCamera()
            ego_obj = self.open_scenario_importer.get_ego_vehicle_object()
            ego_position = convert_to_world_position(self.open_scenario_importer.mgeo, ego_obj.action_type.position)
            self.canvas.setCameraPositionEast(ego_position.x)
            self.canvas.setCameraPositionNorth(ego_position.y)
        except:
            self.canvas.resetCamera()
    
    def import_scenario_selected_in_batch(self):
        scenario_file_path = self.batch_scenario_widget.get_test_scenario_selected()
        if scenario_file_path is None:
            return 
        self.import_scenario(scenario_file_path)
            
    def initialize_openscenario_client(self):
        """set ego cruise mode on/off"""
        start_scenario_dialog = StartScenarioDialog()
        if start_scenario_dialog.showDialog() == 0:
            return False

        if self.open_scenario_client is None:
            self.open_scenario_client = OpenScenarioClient(
                self.file_io_funcs.config['open_scenario_setting']['ip'],
                self.file_io_funcs.config['open_scenario_setting']['port'],
                self )
        self.open_scenario_client.ego_is_cruised_by = start_scenario_dialog.ego_is_cruised_by
        return True

    def set_start_status(self, status:bool):
        # set 'Run' menu status
        action_start_openscenario = self.findChild(QAction, 'actionStart_Scenario')
        action_stop_openscenario = self.findChild(QAction, 'actionStop_Scenario')
        action_start_openscenario.setEnabled(not status)
        action_stop_openscenario.setEnabled(status)
        # set sub-widget status
        self.simulation_result_widget.set_start_status(status)

        # set edit function enable
        self.canvas.osc_client_triggered = status
    
    def start_batch_scenario(self):
        if self.open_scenario_client is not None and self.open_scenario_client.is_start == True:
            QMessageBox.critical(self, 'Error', "Please stop the ongoing simulation.", QMessageBox.Ok)
            return

        # initiate batch simulation
        if not self.batch_scenario_widget.is_start():
            self.scenario_file_list = self.batch_scenario_widget.get_test_scenarios()
            if not self.scenario_file_list:
                return
            else:
                is_stop_trigger_defined = True
                stop_trigger_undefined_file_list = []
                importer = OpenScenarioImporter()
                for file_path in self.scenario_file_list:
                    importer.import_open_scenario(file_path)
                    file_name = os.path.basename(file_path)
                    if importer.scenario_definition is None:
                        QMessageBox.critical(self, 'Error', "Scenario file is not valid: {}".format(file_name), QMessageBox.Ok)
                        return
                    elif not importer.scenario_definition.storyboard.stop_trigger.condition_groups and \
                            not importer.scenario_definition.evaluation.success_condition_groups and \
                            not importer.scenario_definition.evaluation.failure_condition_groups:
                        is_stop_trigger_defined = False
                        stop_trigger_undefined_file_list.append(file_name)
                
                if is_stop_trigger_defined is False:
                    warning_msg = "Below scenarios wouldn't be finished automatically. Start anyway?\n"
                    for file_name in stop_trigger_undefined_file_list:
                        warning_msg = warning_msg + "\n" + file_name
                    ans = QMessageBox.warning(self, 'Warning', warning_msg, QMessageBox.Ok, QMessageBox.Cancel)
                    if ans == QMessageBox.Cancel:
                        return
            # set ego cruise mode on/off
            if self.initialize_openscenario_client() is False:
                return

            # Add file list to result widget
            self.simulation_result_widget.initialize()
            self.simulation_result_widget.update_widget(self.scenario_file_list)

            self.batch_scenario_widget.set_start_status(True)

        if self.scenario_file_list:
            # continue batch simulation
            test_scenario_file = self.scenario_file_list.pop(0)
            self.batch_scenario_widget.set_highlight(test_scenario_file)
            
            self.scheduled_callback_func = self.start_batch_scenario_callback
            self.open_scenario_importer = OpenScenarioImporter()
            self.file_io_funcs.import_OpenScenario(self.open_scenario_importer, test_scenario_file)
        else:
            # end batch simulation
            self.batch_scenario_widget.set_start_status(False)
            self.batch_scenario_widget.set_highlight(None)
            self.set_start_status(False)

    def start_batch_scenario_callback(self):
        if self.open_scenario_importer.update_scenario_data() is False:
            Logger.log_error("Failed to import the scenario, skip to the next scenario")
            self.start_batch_scenario()
            return
        
        self.show_loading("Starting simulation...")
        self.open_scenario_client.set_open_scenario_importer(self.open_scenario_importer)
        self.open_scenario_client.start_scenario()

    def start_scenario(self):
        """
        start open scenario file
        """
        importer:OpenScenarioImporter = self.canvas.get_open_scenario()
        if not importer or not importer.update_scenario_data():
            QMessageBox.critical(self, 'Error', "Failed to start the simulation. Scenario data is not valid.", QMessageBox.Ok)
            return
        # set ego cruise mode on/off
        if self.initialize_openscenario_client() is False:
            return
        
        # clear simulation result widget
        self.simulation_result_widget.initialize()
        
        if importer.file_path is not None:
            self.simulation_result_widget.update_widget([importer.file_path])
        else:
            self.simulation_result_widget.update_widget(None)

        # start simulation
        self.show_loading("Starting simulation...")
        self.open_scenario_client.set_open_scenario_importer(importer)
        self.open_scenario_client.start_scenario()
    
    def start_scenario_selected_in_batch(self):
        if self.open_scenario_client is not None and self.open_scenario_client.is_start == True:
            QMessageBox.critical(self, 'Error', "Please stop the ongoing simulation.", QMessageBox.Ok)
            return

        # get selected scenario
        selected_scenario_filepath = self.batch_scenario_widget.get_test_scenario_selected()
        if selected_scenario_filepath is None:
            return 

        # set ego cruise mode on/off
        if self.initialize_openscenario_client() is False:
            return

        # start batch simulation
        self.batch_scenario_widget.set_start_status(True)
        # Add file list to result widget
        self.scenario_file_list = [selected_scenario_filepath]
        self.simulation_result_widget.initialize()
        self.simulation_result_widget.update_widget(self.scenario_file_list)
        self.start_batch_scenario()

    @pyqtSlot(bool, str)
    def start_scenario_callback(self, result, desc):
        self.close_loading()

        if result is False:
            QMessageBox.critical(self, 'Error', 'Failed to start scenario. Please see the log for details.', QMessageBox.Ok)
            self.stop_scenario()
        else:
            # set scenario menu status
            self.set_start_status(True)

    def stop_batch_scenario(self):
        self.scenario_file_list = []
        self.stop_scenario()

    def stop_scenario(self):
        """stop scenario"""
        if self.open_scenario_client is not None:
            Logger.log_info("Stop scenario")
            self.open_scenario_client.stop_scenario()
        else:
            Logger.log_info("Skipped stop scenario: OpenSCENARIO Client doesn't exist")
    
    @pyqtSlot(bool, str)
    def stop_scenario_callback(self, result, desc):
        if result is False:
            Logger.log_error("Failed to stop scenario. {}".format(desc))

        # Set result
        evaluation_item, event_log = self.open_scenario_client.get_simulation_log()
        
        if evaluation_item:
            self.simulation_result_widget.set_scenario_result(self.open_scenario_client.is_success,
                                                            round(self.open_scenario_client.elapsed_time_sec,2),
                                                            evaluation_item, event_log)
        if self.batch_scenario_widget.is_start():
            self.start_batch_scenario()
        else:
            self.set_start_status(False)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    qtWindow = PyQTWindow()  
    # qtWindow.setWindowIcon(QIcon(os.path.join(current_path, '\\map.ico')))
    #qtWindow.setWindowIcon(QIcon(Define.icon_path))
    qtWindow.show()

    sys.exit(app.exec_())