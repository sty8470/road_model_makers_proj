import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

""" Create New Open Scenario"""
class NewOpenScenarioUI(QDialog):
    def __init__(self, file_io_funcs):
        super().__init__()
        self.map_name = None
        self.mgeo_folder_path = None
        self.file_io_funcs = file_io_funcs
        self.initUI()
        self.show()
        
    def initUI(self):
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.mgeo_map_info(), 0, 0)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        grid_layout.addWidget(self.button_box, 2, 0)
        self.setLayout(grid_layout)
        self.setGeometry(300, 300, 600, 200)
        self.setWindowTitle('Create New OpenSCENARIO')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
        
    def mgeo_map_info(self):
        main_widget = QGroupBox()
        self.map_name_edit = QLineEdit()
        self.mgeo_folder_path_name = QLineEdit()

        # Button to get mgoe_path
        button_widget = QPushButton('Choose')
        button_widget.clicked.connect(self.__open_folder_clicked)
        
        grid_layout  = QGridLayout()
        grid_layout.addWidget(QLabel('Map Name:'), 0, 0)
        grid_layout.addWidget(self.map_name_edit, 0, 1)
        
        grid_layout.addWidget(QLabel('RoadNetwork Path:'), 1, 0)
        grid_layout.addWidget(self.mgeo_folder_path_name, 1, 1)
        grid_layout.addWidget(button_widget, 1, 2)
        
        main_widget.setLayout(grid_layout)
        return main_widget
        
    @pyqtSlot()
    def __open_folder_clicked(self):
        folder_path = self.file_io_funcs.get_existing_directory("Select a folder to load MGeo Data",
                                                                'OpenScenario_NEW')
        if not folder_path:
            return
            
        self.mgeo_folder_path_name.setText(folder_path)
        
    def showDialog(self):
        return super().exec_()
    
    def accept(self):
        # Remove all space --> Prevent to load the map with map name that has the space
        map_name = self.map_name_edit.text().replace(" ", "")
        mgeo_folder_path = self.mgeo_folder_path_name.text()

        if not map_name:
            QMessageBox.warning(self, "Warning", "Please Set the Map Name")
            return
        if not mgeo_folder_path or not os.path.exists(os.path.dirname(mgeo_folder_path)):
            QMessageBox.warning(self, "Warning", "Please Set the Correct MGeo Folder Path")
            return

        #Check if the directory is empty
        if len(os.listdir(mgeo_folder_path)) == 0:
            QMessageBox.warning(self, "Warning", "The directory does not contain MGeo Data")
            return

        self.map_name = map_name
        self.mgeo_folder_path = mgeo_folder_path
        self.done(1)
        
    def reject(self):
        self.map_name = None
        self.mgeo_folder_path = None
        self.done(0)