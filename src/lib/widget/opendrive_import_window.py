import os
import sys

from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger

import numpy as np
#import json
from PyQt5.QtWidgets import *
from PyQt5.Qt import *

class OpenDriveImportWindow(QDialog):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()
        

    def initUI(self):
        self.setModal = True
        self.setWindowTitle('OpenDrive Import Configuration')

        self.rbLeftHandTraffic = QRadioButton('Left Hand Traffic')
        self.rbRightHandTraffic = QRadioButton('Right Hand Traffic')

        self.cbGenerateMesh = QCheckBox('Generate Road Polygon')
        self.cbUnionJunction = QCheckBox('Union Junction Mesh')
        self.cbCleanlink = QCheckBox('Clean Link and Vertices')
        self.cbProjectLM = QCheckBox('Project Lanemarking mesh on road')
        
        if self.config is not None:
            self.txtVertexDistance = QLineEdit(self.config['vertex_distance'], self)
            self.txtSidewalkHeight = QLineEdit(self.config['sidewalk_height'], self)
            self.txtLaneMarkingHeight = QLineEdit(self.config['lanemarking_height'], self)
            self.txtZTolerance = QLineEdit(self.config['z_tolerance'], self)

            if self.config['traffic_direction'] == "right" :
                self.rbRightHandTraffic.setChecked(True)
            else :
                self.rbLeftHandTraffic.setChecked(True)

            if self.config['union_junction'] == "True" :
                self.cbUnionJunction.setChecked(True)
            else :
                self.cbUnionJunction.setChecked(False)

            if self.config['generate_mesh'] == "True" :
                self.cbGenerateMesh.setChecked(True)
            else :
                self.cbGenerateMesh.setChecked(False)

            if self.config['clean_link'] == "True" :
                self.cbCleanlink.setChecked(True)
            else :
                self.cbCleanlink.setChecked(False)

            if 'project_lm' in self.config :
                if self.config['project_lm'] == "True" :
                    self.cbProjectLM.setChecked(True)
                else :
                    self.cbProjectLM.setChecked(False)
            else :
                self.cbProjectLM.setChecked(False)
        else:
            self.txtVertexDistance = QLineEdit('2.0', self)
            self.txtSidewalkHeight = QLineEdit('0.15', self)
            self.txtLaneMarkingHeight = QLineEdit('0.03', self)
            self.txtZTolerance = QLineEdit('0.1', self)
            self.rbRightHandTraffic.setChecked(True)
        
        self.txtVertexDistance.setMaxLength(20)
        self.txtVertexDistance.setMaximumWidth(120)

        self.txtSidewalkHeight.setMaxLength(20)
        self.txtSidewalkHeight.setMaximumWidth(120)
        
        self.txtZTolerance.setMaxLength(20)
        self.txtZTolerance.setMaximumWidth(120)

        self.txtLaneMarkingHeight.setMaxLength(20)
        self.txtLaneMarkingHeight.setMaximumWidth(100)
            
        self.btnOk = QPushButton('OK', self)
        self.btnOk.clicked.connect(self.onOkButtonClicked) 
        
        self.lbVertexDistance = QLabel('& Vertex Distance : ')
        self.lbVertexDistance.setBuddy(self.txtVertexDistance)

        self.lbSidewalkHeight = QLabel('& Sidewalk Height : ')
        self.lbSidewalkHeight.setBuddy(self.txtSidewalkHeight)

        self.lbLaneMarkingHeight = QLabel('& Lanemarking Height : ')
        self.lbLaneMarkingHeight.setBuddy(self.txtLaneMarkingHeight)

        self.lbZTolerance = QLabel('& Z-Tolerance : ')
        self.lbZTolerance.setBuddy(self.txtZTolerance)

        self.gbGeneral = QGroupBox('General')
        GeneralGroupBoxLayout = QGridLayout()
        GeneralGroupBoxLayout.addWidget(self.lbVertexDistance, 0, 0)
        GeneralGroupBoxLayout.addWidget(self.txtVertexDistance, 0 ,1, QtCore.Qt.AlignmentFlag.AlignLeft)
        GeneralGroupBoxLayout.addWidget(self.lbSidewalkHeight, 1, 0)
        GeneralGroupBoxLayout.addWidget(self.txtSidewalkHeight, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        GeneralGroupBoxLayout.addWidget(self.lbZTolerance, 2, 0)
        GeneralGroupBoxLayout.addWidget(self.txtZTolerance, 2, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        GeneralGroupBoxLayout.setColumnStretch(0, 0)
        GeneralGroupBoxLayout.setColumnStretch(1, 1)
        self.gbGeneral.setLayout(GeneralGroupBoxLayout)

        self.gbMesh = QGroupBox('Mesh')
        MeshGroupBoxLayout = QGridLayout()
        MeshGroupBoxLayout.addWidget(self.cbGenerateMesh, 0, 0, 1, 2)
        MeshGroupBoxLayout.addWidget(self.cbUnionJunction, 1, 0, 1, 2)
        MeshGroupBoxLayout.addWidget(self.cbCleanlink, 2, 0, 1, 2)
        MeshGroupBoxLayout.addWidget(self.cbProjectLM, 3, 0, 1, 2)
        MeshGroupBoxLayout.addWidget(self.lbLaneMarkingHeight, 4, 0)
        MeshGroupBoxLayout.addWidget(self.txtLaneMarkingHeight, 4, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        MeshGroupBoxLayout.setColumnStretch(0, 0)
        MeshGroupBoxLayout.setColumnStretch(1, 1)
        self.gbMesh.setLayout(MeshGroupBoxLayout)

        self.gbTrafficDirection = QGroupBox('Traffic Direction')
        TDGroupBoxLayout = QGridLayout()
        TDGroupBoxLayout.addWidget(self.rbLeftHandTraffic, 0, 0)
        TDGroupBoxLayout.addWidget(self.rbRightHandTraffic, 0, 1)
        self.gbTrafficDirection.setLayout(TDGroupBoxLayout)

        gridLayout = QGridLayout()
        gridLayout.addWidget(self.gbGeneral, 0, 0)
        gridLayout.addWidget(self.gbMesh, 1, 0)
        gridLayout.addWidget(self.gbTrafficDirection, 2, 0)
        gridLayout.addWidget(self.btnOk, 3, 0)

        self.setLayout(gridLayout)
    
    def onOkButtonClicked(self):
        chk_vertex_distance = self.isFloat(self.txtVertexDistance.text()) == True
        chk_sidewalk_height = self.isFloat(self.txtSidewalkHeight.text()) == True
        chk_lanemarking_height = self.isFloat(self.txtLaneMarkingHeight.text()) == True
        chk_z_tolerance = self.isFloat(self.txtZTolerance.text()) == True
        if chk_vertex_distance and chk_sidewalk_height and chk_z_tolerance and chk_lanemarking_height :
            self.accept()
        else :
            QMessageBox.warning(self, "Type Error", "Please check the type")

    def getParameters(self):
        vertex_distance = float(self.txtVertexDistance.text()) if self.isFloat(self.txtVertexDistance.text()) == True else None
        sidewalk_height = float(self.txtSidewalkHeight.text()) if self.isFloat(self.txtSidewalkHeight.text()) == True else None
        lanemarking_height = float(self.txtLaneMarkingHeight.text()) if self.isFloat(self.txtLaneMarkingHeight.text()) == True else None
        z_tolerance = float(self.txtZTolerance.text()) if self.isFloat(self.txtZTolerance.text()) == True else None
        traffic_direction = "left" if self.rbLeftHandTraffic.isChecked() else "right"
        generate_mesh = True if self.cbGenerateMesh.isChecked() else False
        union_junction = True if self.cbUnionJunction.isChecked() else False
        clean_link = True if self.cbCleanlink.isChecked() else False
        project_lm = True if self.cbProjectLM.isChecked() else False

        return vertex_distance, sidewalk_height, z_tolerance, traffic_direction, lanemarking_height, union_junction, clean_link, generate_mesh, project_lm
   
    def showDialog(self):
        return super().exec_()


    def isFloat(self, value):
        if value != '':
            try:
                float(value)
                return True
            except:
                #QMessageBox.warning(self, "Type Error", "Please check the type")
                return False


if __name__ == '__main__':
    pass