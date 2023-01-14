import os
import sys
from typing import DefaultDict

from numpy.lib.twodim_base import diag
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.common.logger import Logger

import numpy as np
import json
from PyQt5.QtWidgets import *
from PyQt5.Qt import *

from pyproj import Proj, Transformer


class EditChangeWorldProjection(QDialog):
    def __init__(self, global_coordinate_system):
        super().__init__()
        self.projectionType = 'proj4'
        self.proj4String = ''
        self.isRetainGlobalPosition = True
        self.initUI()
        self.initializeData(global_coordinate_system)
    
    def initUI(self):
        # self.setGeometry(500, 200, 200, 200)
        
        # old_origin_str = '{:.9f}, {:.9f}, {:.9f}'.format(self.old_origin[0], self.old_origin[1], self.old_origin[2])

        self.rbtn_global = QRadioButton('Retain global position', self)
        self.rbtn_no_global = QRadioButton('Do NOT retain global position', self)
        self.rbtn_global.setChecked(True)

        self.cbType = QComboBox(self)
        self.cbType.addItem('proj4')
        self.cbType.addItem('utm')
        self.cbType.addItem('tmerc_params')
        self.cbType.addItem('undefined')
        self.cbType.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


        lb_type = QLabel('Type :')
        typeLayout = QHBoxLayout()
        typeLayout.addWidget(lb_type)
        typeLayout.addWidget(self.cbType)

        self.lb_help = QLabel('')

        lbValue = QLabel('Value :')
        self.txtValue = QLineEdit()
        

        btn_OK = QPushButton('OK')
        
        textEditLayout = QHBoxLayout()
        textEditLayout.addWidget(lbValue)
        textEditLayout.addWidget(self.txtValue)

        widgetLayout = QVBoxLayout()
        widgetLayout.addWidget(self.rbtn_global)
        widgetLayout.addWidget(self.rbtn_no_global)
        widgetLayout.addSpacing(30)
        widgetLayout.addLayout(typeLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addWidget(self.lb_help)
        widgetLayout.addSpacing(10)
        widgetLayout.addLayout(textEditLayout)
        widgetLayout.addSpacing(10)
        widgetLayout.addWidget(btn_OK)
        self.setLayout(widgetLayout)


        self.rbtn_global.setChecked(True)
        self.txtValue.setToolTip('input full proj4 string')

        self.setWindowTitle('Chnage World Projection')

        # event
        self.rbtn_global.clicked.connect(self.radioButtonClicked)
        self.rbtn_no_global.clicked.connect(self.radioButtonClicked)
        self.cbType.currentIndexChanged.connect(self.cbType_IndexChanged)
        btn_OK.clicked.connect(self.accept)
    

    def initializeData(self, initData):
        result, proj4 =  self.validationProjectionFormat(initData)
        if result:
            self.cbType.setCurrentText('proj4')
            self.txtValue.setText(proj4)
            self.proj4String = proj4 
        
            


    
    def radioButtonClicked(self):
        if self.rbtn_global.isChecked():
            self.isRetainGlobalPosition = True
        else:
            self.isRetainGlobalPosition = False
            
    
    def cbType_IndexChanged(self):
        if self.cbType.currentIndex() == 3:
            QMessageBox.warning(self, "TBD", "TBD")
            self.txtValue.setToolTip('')
        elif self.cbType.currentIndex() == 0: # proj
            self.lb_help.isVisible = True
            # self.lb_help.setText('input full proj4 string')
            self.txtValue.setToolTip('input full proj4 string')
            self.txtValue.setText(self.proj4String)
        
        elif self.cbType.currentIndex() == 1: #utm
            self.lb_help.isVisible = True
            # self.lb_help.setText('input utm zone(zone is between 0 to 60)')
            self.txtValue.setToolTip('input utm zone(zone is between 0 to 60)')
            transformer = Transformer.from_pipeline(self.proj4String)
            if transformer.name == 'utm':
                split_proj = transformer.definition.split(' ')
                zone = split_proj[1].split('=')[1]
                self.txtValue.setText(zone)
            else:
                pass

        elif self.cbType.currentIndex() == 2: #tmerc
            self.lb_help.isVisible = True
            # self.lb_help.setText('format : lat0, long0, k, east, north, spheroid')
            self.txtValue.setToolTip('format : lat0, long0, k, east, north, spheroid')

            transformer = Transformer.from_pipeline(self.proj4String)
            if transformer.name == 'tmerc':
                split_proj = transformer.definition.split(' ')
                value = ''
                for item in split_proj:
                    if item.__contains__('='):
                        itemName = item.split('=')[0]
                        itemValue = item.split('=')[1]
                        
                        if itemName == 'proj' or itemName == 'units' or itemName == 'towgs84':
                            pass
                        else:
                            value = value + itemValue + ','
                
                value = value[:-1]

                self.txtValue.setText(value)
            else:
                split_proj = transformer.definition.split(' ')
                zone = float(split_proj[1].split('=')[1])
                
                porj4_lat_0 = ' +lat_0={}'.format(0)
                porj4_lon_0 = ' +lon_0={}'.format((zone - 0.5) * 6 - 180)
                porj4_k = ' +k={}'.format(0.9996)
                porj4_x_0 = ' +x_0={}'.format(500000)
                porj4_y_0 = ' +y_0={}'.format(0)
                proj4_datum = ' +ellps={}'.format('WGS84')

                proj4_string = '+proj=tmerc'  + porj4_lat_0 + porj4_lon_0 + porj4_k + porj4_x_0 + porj4_y_0 + proj4_datum + ' +units=m +no_defs'
                result, proj4 = self.validationProjectionFormat(proj4_string)
                if result:
                    textValue = '{},{},{},{},{},{}'.format(0,(zone - 0.5) * 6 - 180, 0.9996, 500000, 0,'WGS84')
                    self.txtValue.setText(textValue)
        
        self.projectionType = self.cbType.currentText()



    def accept(self):
        if not self.isRetainGlobalPosition:
            reply = QMessageBox.question(self, "TBD", "TBD", QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                pass # 추후 추가
            else:
                pass # 추후 추가
        
        if self.txtValue.text() == '':
            QMessageBox.warning(self, "Validation Error", "TBD") # 값쓰라고...
      
        
        proj4_string = ''

        if self.projectionType == 'proj4':
            proj4_string = self.txtValue.text()
        elif self.projectionType == 'utm':
            zone = self.txtValue.text()
            if self.validationZone(zone):
                proj4_string = '+proj=utm +zone={} +datum=WGS84 +units=m +no_defs'.format(zone)
            else:
                QMessageBox.warning(self, "Validation Error", "TBD") # zone 범위 및 숫자만 입력가능
        elif self.projectionType == 'tmerc_params':
            value = self.txtValue.text()
            splitArray = value.split(',')
            if splitArray.count != 6:
                QMessageBox.warning(self,'Validation Error', 'TBD') # 포멧확인 ' lat, long, k, x, y, datum' <-순서

            porj4_lat_0 = ' +lat_0={}'.format(splitArray[0])
            porj4_lon_0 = ' +lon_0={}'.format(splitArray[1])
            porj4_k = ' +k={}'.format(splitArray[2])
            porj4_x_0 = ' +x_0={}'.format(splitArray[3])
            porj4_y_0 = ' +y_0={}'.format(splitArray[4])
            proj4_datum = ' +ellps={}'.format(splitArray[5])

            proj4_string = '+proj=tmerc'  + porj4_lat_0 + porj4_lon_0 + porj4_k + porj4_x_0 + porj4_y_0 + proj4_datum + ' +units=m +no_defs'

        # projection string vaidation
        result, proj4 = self.validationProjectionFormat(proj4_string)
        
        if result:
            self.proj4String = proj4
            self.done(1)
        else:
            QMessageBox.warning(self, "Validation Error", "TBD") # 포멧확인하라는 경고메세지
            self.done(0)
        
    
    def close(self):
        self.done(0)
    
    def showDialog(self):
        return super().exec_()
    
    def validationProjectionFormat(self, data):
        try:
            proj4 = Proj(data).srs
            return True, proj4
        except BaseException as e: 
            return False, None
    
    def validationZone(self, data):
        try:
            userInput = int(data)   
            if 0 < userInput <= 61:
                return True

            return False   
        except ValueError:
            return False
    

# TEST
    
# class mainwindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.resize(400,200)
#         global_coord = '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
#         # global_coord = 'proj=utm zone=11 datum=WGS84 units=m no_defs ellps=WGS84 towgs84=0,0,0'



#         dialog = EditChangeWorldProjection(global_coord)
#         dialog.showDialog()


# app = QApplication([])
# main = mainwindow()
# main.show()
# app.exec_()


    
                
            

    
    
