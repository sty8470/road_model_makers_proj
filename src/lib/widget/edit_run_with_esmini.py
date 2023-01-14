
from asyncio.windows_utils import Popen
import os
import sys
import subprocess
from GUI.opengl_canvas import OpenGLCanvas
import platform

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../src/proj_mgeo_editor_morai_opengl/GUI')))

from lib.common.logger import Logger
from lib.mgeo.class_defs import *

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.Qt import *
class EsminiEditor(QDialog):
    """
    오픈소스 OpenDRIVE 및 OpenSCENARIO 실행 프로그램 esmini의 odrviewer 모듈 연동 클래스
    """
    def __init__(self, odr_viewer_init_path, xodr_init_path, file_io_funcs):
        super().__init__()
        self.canvas = OpenGLCanvas()
        self.odr_viewer_init_path = odr_viewer_init_path
        self.xodr_init_path = xodr_init_path
        self.file_io_funcs = file_io_funcs
        self.odr_viewer_exit_path = ''
        self.xodr_exit_path = ''
        self.initUI()
       
    def initUI(self):
        self.v_widgetLayout = QVBoxLayout()
        self.odrviewer_h_widgetLayout = QHBoxLayout()
        self.xodr_h_widgetLayout = QHBoxLayout()
        
        self.odrviwer_path_label = QLabel('odrviewer path(odrviewer.exe)', self)
        self.odrviewer_path_line_edit = QLineEdit('', self)
        self.odrviewer_path_line_edit.setReadOnly(True)
        self.odrviewer_path_line_edit.setText(self.odr_viewer_init_path)
        self.odrviewer_path_opener_button = QPushButton()
        dir_img_icon = self.style().standardIcon(getattr(QStyle, 'SP_DirIcon'))
        self.odrviewer_path_opener_button.setIcon(dir_img_icon)
        self.odrviewer_path_opener_button.clicked.connect(self.find_odr_viewer_exe_path)
        
        self.v_widgetLayout.addWidget(self.odrviwer_path_label)
        self.odrviewer_h_widgetLayout.addWidget(self.odrviewer_path_line_edit)
        self.odrviewer_h_widgetLayout.addWidget(self.odrviewer_path_opener_button)
        self.v_widgetLayout.addLayout(self.odrviewer_h_widgetLayout)
        
        self.xodr_path_label = QLabel('xodr path', self)
        self.xodr_path_line_edit = QLineEdit('', self)
        self.xodr_path_line_edit.setReadOnly(True)
        self.xodr_path_line_edit.setText(self.xodr_init_path)
        self.xodr_file_opener_button = QPushButton()
        dir_img_icon = self.style().standardIcon(getattr(QStyle, 'SP_DirIcon'))
        self.xodr_file_opener_button.setIcon(dir_img_icon)
        self.xodr_file_opener_button.clicked.connect(self.find_xodr_file_path)
        
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        
        self.v_widgetLayout.addWidget(self.xodr_path_label)
        self.xodr_h_widgetLayout.addWidget(self.xodr_path_line_edit)
        self.xodr_h_widgetLayout.addWidget(self.xodr_file_opener_button)
        self.v_widgetLayout.addLayout(self.xodr_h_widgetLayout)
        self.v_widgetLayout.addWidget(self.buttonbox)
        
        self.setLayout(self.v_widgetLayout) 
        self.setWindowTitle('Run with Esmini')
        self.setFixedSize(300, 150)
        
    def find_odr_viewer_exe_path(self):
        self.odr_viewer_exit_path = QFileDialog.getOpenFileName(self.canvas, caption='Select odrviewer.exe',  directory = self.odr_viewer_init_path, options= QFileDialog.DontUseNativeDialog)[0]
        if self.odr_viewer_exit_path != '':
            self.odrviewer_path_line_edit.setText(self.odr_viewer_exit_path)
        self.odr_viewer_init_path = self.odrviewer_path_line_edit.text()
    
    def find_xodr_file_path(self):
        self.xodr_exit_path = QFileDialog.getOpenFileName(self.canvas, caption='Select a valid OpenDRIVE file',  directory = self.xodr_init_path, options= QFileDialog.DontUseNativeDialog)[0]
        if self.xodr_exit_path != '':
            self.xodr_path_line_edit.setText(self.xodr_exit_path)
        self.xodr_init_path = self.xodr_path_line_edit.text()
    
    def is_empty_input(self):
        if len(self.odrviewer_path_line_edit.text()) == 0 and len(self.xodr_path_line_edit.text()) != 0:
            QMessageBox.warning(self, "Command Error", "Provide a path to esmini odrviewer.exe")
            return True
        if len(self.odrviewer_path_line_edit.text()) != 0 and len(self.xodr_path_line_edit.text()) == 0:
            QMessageBox.warning(self, "Command Error", "Provide a path to OpenDRIVE file")
            return True
        if len(self.odrviewer_path_line_edit.text()) == 0 and len(self.xodr_path_line_edit.text()) == 0:
            QMessageBox.warning(self, "Command Error", "Provide paths to both esmini odrviewer.exe and a valid OpenDRIVE file")
            return True
        return False
        
    def is_valid_odr_viewer_exit_path_check(self):
        if type(self.odr_viewer_exit_path) == tuple and len(self.odr_viewer_exit_path[0]) != 0:
            if self.odr_viewer_exit_path[0].split('.')[0][-9:].lower() != 'odrviewer' and self.odr_viewer_exit_path[0].split('.')[-1] != 'exe':
                QMessageBox.warning(self, "Error", "Provide a path to esmini odrviewer.exe")
            return False
        elif self.odrviewer_path_line_edit.text().split('.')[0][-9:].lower() != 'odrviewer' and len(self.odrviewer_path_line_edit.text()) != 0:
            QMessageBox.warning(self, "Error", "Provide a path to esmini odrviewer.exe")
            return False
        return True
        
    def is_valid_xodr_exit_path_check(self):
        if type(self.xodr_exit_path) == tuple and len(self.xodr_exit_path[0]) != 0: 
            if self.xodr_exit_path[0].split('.')[-1] != 'xodr':
                QMessageBox.warning(self, "Error", "Select a valid OpenDRIVE file")
                return False
        elif 'xodr' not in self.xodr_exit_path.split('.') and len(self.xodr_exit_path) != 0:
            QMessageBox.warning(self, "Error", "Select a valid OpenDRIVE file")
            return False
        return True
        
    def accept(self):
        if self.odr_viewer_exit_path == '':
            self.odr_viewer_exit_path = self.odrviewer_path_line_edit.text()
        if self.xodr_exit_path == '':
            self.xodr_exit_path = self.xodr_path_line_edit.text()
        if not self.is_empty_input() and self.is_valid_odr_viewer_exit_path_check() and self.is_valid_xodr_exit_path_check():
            self.file_io_funcs.update_file_path_config('ODR_VIEWER',self.odrviewer_path_line_edit.text())
            self.file_io_funcs.update_file_path_config('XODR',self.xodr_path_line_edit.text())
            if platform.system().lower()[0] == 'w':
                try:
                    result = Popen('{} --window 800 400 --odr {}'.format(self.odrviewer_path_line_edit.text(), self.xodr_path_line_edit.text(), shell=True, cwd = current_path))
                except subprocess.CalledProcessError as e:
                    Logger.log_info("The Subprocess Error is as following: {}".format(e))
                    result.terminate()
            else:
                Logger.log_info("This function is not supported on Linux system yet")
                
    def showDialog(self):
        Logger.log_trace("Called: Run with Esmini")
        return super().exec_()
        
