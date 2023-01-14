
import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
src_root_path = os.path.normpath(os.path.join(current_path, '../'))
lib_root_path = os.path.normpath(os.path.join(src_root_path, 'lib'))
sys.path.append(current_path)
sys.path.append(src_root_path)
sys.path.append(lib_root_path)

# import platform
# import datetime
# import ctypes
# if platform.system() == "Windows":
#     # 작업 표시줄에 아이콘을 표시하기 위해서 Process App User Model ID 등록
#     myappid = 'morai.mapeditor' # arbitrary string
#     ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# from lib.common.logger import Logger
# import numpy as np
# import json
# import shutil

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtCore import Qt, QMetaObject, QPoint, QSize, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIntValidator
from PyQt5.QtGui import QIcon

from GUI.ui_main import Ui_MainWindow

# from proj_mgeo_editor_morai_opengl.GUI.opengl_canvas import OpenGLCanvas
# from proj_mgeo_editor_morai_opengl.GUI.pyqt5_file_io_funcs import FileIOFuncs

from lib.common.logger import Logger
import traceback
from lib.mgeo.class_defs.mgeo import MGeo

# 이 구문이 있어야 아래 import시 에러 발생X 
sys.path.append(os.path.normpath(os.path.join(lib_root_path, 'open_scenario')))
from lib.openscenario.client.open_scenario_client import OpenScenarioClient
from lib.openscenario.open_scenario_importer import OpenScenarioImporter

from proj_mgeo_editor_license_management.rest_api_manager import *


class PyQTWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setMinimumWidth(300)

        """인증"""
        Logger.log_info("======= Scenario Runner =======")
        inst = RestApiManager.instance()
        while(True):
            Logger.log_info("Please enter user id : ")
            id = input()
            Logger.log_info("Please enter password : ")
            pw = input()
            #result =  inst.sign_in_ex02(id, pw, expected_program_name='osc_support_demo')
            result = inst.sign_in_with_program_name(id, pw, expected_program_name='osc_support_demo')
            if (result.success):
                break
            else:
                Logger.log_error('Failed to sign-in: {}'.format(result.error))

        """메뉴 활성/비활성 설정"""
        self.menu_file = self.findChild(QMenu, 'menuFile')
        self.menurun = self.findChild(QMenu, 'menuRun')
        self.action_start_scenario = self.findChild(QAction, 'actionStart_Scenario')
        self.action_stop_scenario = self.findChild(QAction, 'actionStop_Scenario')
        self.push_button_start = self.findChild(QPushButton, 'pushButton')
        self.push_button_stop = self.findChild(QPushButton, 'pushButton_2')

        self.action_start_scenario.setDisabled(True)
        self.action_stop_scenario.setDisabled(True)
        self.push_button_start.setDisabled(True)
        self.push_button_stop.setDisabled(True)

        """Custom 기능 초기화"""
        self.connect_callback_functions()

        # TODO: OpenSCENARIO Client IP/Port 설정 현재는 고정임 
        self.open_scenario_client = OpenScenarioClient('localhost', '7789')
        # self.open_scenario_client = OpenScenarioClient(
        #     self.file_io_funcs.config['open_scenario_setting']['ip'],
        #     self.file_io_funcs.config['open_scenario_setting']['port']
        # )

        self.open_scenario_importer = None
    

    def connect_callback_functions(self):
        actionLoad_OpenSCENARIO = self.findChild(QAction, 'actionLoad_OpenSCENARIO')
        actionLoad_OpenSCENARIO.setShortcut('Ctrl+L')
        actionLoad_OpenSCENARIO.triggered.connect(self.load_openscenario)

        actionStart_Scenario = self.findChild(QAction, 'actionStart_Scenario')
        actionStart_Scenario.triggered.connect(lambda: self.start_scenario())

        actionStop_Scenario = self.findChild(QAction, 'actionStop_Scenario')
        actionStop_Scenario.triggered.connect(lambda: self.stop_scenario())

        pushButton = self.findChild(QPushButton, 'pushButton')
        pushButton.clicked.connect(lambda: self.start_scenario())

        pushButton = self.findChild(QPushButton, 'pushButton_2')
        pushButton.clicked.connect(lambda: self.stop_scenario())


    def load_openscenario(self):
        try:
            Logger.log_trace('Called: Import OpenScenario')

            # TODO: 현재는 최근 유저가 사용한 path 저장하지 않음
            # init_import_path = self.get_path_from_config('OpenScenario_IMPORT')
            init_import_path = current_path

            input_path = QFileDialog.getOpenFileName(QFileDialog(), 'Select a Open Drive file', 
                        init_import_path, filter='*.xosc;; All File(*)')

            if (input_path == '' or input_path == None or input_path[0] == ''):
                Logger.log_error('invalid input_path (your input: {})'.format(input_path))
                return

            # TODO: 현재는 최근 유저가 사용한 path 저장하지 않음
            # # Update config file (save latest file path)
            # self.update_file_path_config('OpenScenario_IMPORT',
            #     os.path.normpath(os.path.join(input_path[0], '../')))

            # Import OpenScenario
            importer = OpenScenarioImporter(input_path[0])

            # Load MGeo
            mgeo_folder_path = importer.get_mgeo_folder_path()   
            if not mgeo_folder_path:
                Logger.log_error('Import OpenScenario failed. MGeo folder path is empty in OpenScenario file.')
                QMessageBox.critical(self.canvas, "Error", 'Import OpenScenario failed. MGeo folder path is empty in OpenScenario file.')
                return

            Logger.log_info('load MGeo data from: {}'.format(mgeo_folder_path))

            mgeo_planner_map = MGeo.create_instance_from_json(mgeo_folder_path)   
            importer.set_mgeo(mgeo_planner_map)

            # Import OpenScenario
            importer.import_open_scenario() 
            
            # OpenScenario client 객체에 importer 참조 전달
            self.open_scenario_importer = importer

            self.action_start_scenario.setDisabled(False)
            self.action_stop_scenario.setDisabled(True)
            self.push_button_start.setDisabled(False)
            self.push_button_stop.setDisabled(True)

            Logger.log_info('Import OpenScenario data from: {}'.format(input_path[0]))

        except BaseException as e:
            Logger.log_error('Import OpenScenario failed (traceback is down below) \n{}'.format(traceback.format_exc()))

    # start imported scenario
    def start_scenario(self):
        self.open_scenario_client = OpenScenarioClient('localhost', '7789')
        # self.open_scenario_client = OpenScenarioClient(
        #     self.file_io_funcs.config['open_scenario_setting']['ip'],
        #     self.file_io_funcs.config['open_scenario_setting']['port']
        # )

        self.action_start_scenario.setDisabled(True)
        self.action_stop_scenario.setDisabled(False)
        self.push_button_start.setDisabled(True)
        self.push_button_stop.setDisabled(False)

        self.open_scenario_client.set_open_scenario_importer(self.open_scenario_importer)
        self.open_scenario_client.start_scenario()

    def stop_scenario(self):
        self.action_start_scenario.setDisabled(False)
        self.action_stop_scenario.setDisabled(True)
        self.push_button_start.setDisabled(False)
        self.push_button_stop.setDisabled(True)

        self.open_scenario_client.stop_scenario()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    qtWindow = PyQTWindow()  
    qtWindow.show()
    sys.exit(app.exec_())
