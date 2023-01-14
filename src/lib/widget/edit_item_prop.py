import os
import sys

from logger import Logger

import re
import numpy as np
import ast

from PyQt5.QtWidgets import *

class MGeoPropertyEditor(QDialog):
    """MGeo 데이터 속성을 변경하기 위한 Popup Dialog 정보를 담고 있는 클래스"""

    def __init__(self, data, node_map=None, line_map=None, ts_map=None, tl_map=None, jc_map=None, cw_map=None, scw_map = None, ps_map = None, ego_vehicle=None, vehicle_list=None, pedestrian_list=None, obstacle_list=None, lane_marking_map=None):
        super().__init__()
        self.data = data
        self.node_map = node_map
        self.line_map = line_map
        self.ts_map = ts_map
        self.tl_map = tl_map
        self.jc_map = jc_map
        self.cw_map = cw_map
        self.scw_map = scw_map
        self.ego_vehicle = ego_vehicle
        self.vehicle_list = vehicle_list
        self.pedestrian_list = pedestrian_list
        self.obstacle_list = obstacle_list
        self.lane_marking_map = lane_marking_map

        self.cw_map = ts_map
        self.scw_map = scw_map
        self.ps_map = ps_map

        self.return_value = self.data.text(2)
        self.edit_widget = None
        self.initUI()

    def initUI(self):
        """속성 변경 Dialog 기본 Layout을 설정하고 데이터 타입 별로 다른 Widget을 불러와서 사용한다"""
        data_name = self.data.text(0)
        data_type = self.data.text(1)
        data_value = self.data.text(2)
            
        vbox = QVBoxLayout()

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        
        if self.data.parent() is not None:
            if self.data.parent().text(0) == 'ROADPOLYGON' and data_type != 'string':
                self.edit_widget = ReadList(self.data)
                self.buttonbox = QDialogButtonBox(QDialogButtonBox.Close)
                self.buttonbox.clicked.connect(self.close)

            elif data_type == 'list<float>':
                if data_name in ['speed_offset', 'lane_type_offset']:
                    self.edit_widget = EditFloatList(self.data, 'float')
                elif data_name == 'rot':
                    self.edit_widget = EditRotation(self.data)
                else:
                    self.edit_widget = EditPoint(self.data)
            elif data_type == 'list<int>':
                if 'lane_type' in data_name:
                    self.edit_widget = EditFloatList(self.data, 'int')
                else:
                    model_index_list = list(range(0, 100))
                    self.edit_widget = EditIntList(self.data, model_index_list)
            elif data_type == 'list<string>':
                com_list = self.line_map
                self.edit_widget = EditStringList(self.data)
                if 'junction' in data_name:
                    self.edit_widget = EditStringList(self.data, self.jc_map)
                if 'node' in data_name:
                    self.edit_widget = EditStringList(self.data, self.node_map)
                if 'link' in data_name:
                    self.edit_widget = EditStringList(self.data, self.line_map)
                if 'lane_mark' in data_name:
                    self.edit_widget = EditStringList(self.data, self.lane_marking_map)
                if 'path' in data_name:
                    self.edit_widget = EditStringList(self.data, self.line_map)
                if data_name == 'lane_shape':
                    self.edit_widget = EditStringListList(self.data)
                if data_name == 'lane_color':
                    self.edit_widget = EditStringListList(self.data)
                if data_name in ['ref_lines', 'all_lines', 'signal_id_list', 
                    'synced_signal_id_list', 'ref_traffic_light_list', 'single_crosswalk_list']:
                    self.edit_widget = ReadList(self.data)
                    self.buttonbox = QDialogButtonBox(QDialogButtonBox.Close)
                    self.buttonbox.clicked.connect(self.close)

            elif data_type == 'list<list<float>>':
                self.edit_widget = EditPointList(self.data)

            elif data_type == 'boolean':
                self.edit_widget = EditBoolean(self.data)

            elif data_type == 'list<dict>':
                self.edit_widget = ReadList(self.data)
                self.buttonbox = QDialogButtonBox(QDialogButtonBox.Close)
                self.buttonbox.clicked.connect(self.close)

            elif data_type == 'dict':
                self.edit_widget = ReadDict(self.data)
                self.buttonbox = QDialogButtonBox(QDialogButtonBox.Close)
                self.buttonbox.clicked.connect(self.close)

            else:
                if data_name == 'ref_crosswalk_id':
                    self.edit_widget = EditOneLine(self.data, isReadonly = True)
                    
                elif self.data.text(2).find('[') > -1:
                    self.edit_widget = EditStringList(self.data)
                else:
                    self.edit_widget = EditOneLine(self.data)
            # 일부는 Data Name에 따라 특수한 UI를 사용하는 경우도 있음
            if data_name == 'orientation' or data_name == 'initPositionMode' or data_name == 'pathGenerationMethod' or data_name == 'desiredVelocitiyMode':
                self.edit_widget = EditCombobox(self.data)
        else:
            self.edit_widget = EditOneLine(self.data)

        vbox.addWidget(self.edit_widget)
        vbox.addWidget(self.buttonbox)
        self.setLayout(vbox)

        self.setWindowTitle('Property Editor')
        # self.setGeometry(300, 300, 300, 200)
        # self.show()
        

    def showDialog(self):
        return super().exec_()

    def accept(self):
        return_value = self.edit_widget.accept()
        if return_value is not False:
            self.return_value = return_value
            self.reject()
        else:
            return

    def returnNewAtrri(self):
        data_type = self.data.text(1)
        before_value = self.data.text(2)

        after_value = self.return_value

        if data_type == 'int':
            try:
                after_value = int(self.return_value)
            except:
                after_value = 0

        elif data_type == 'float':
            try:
                after_value = float(self.return_value)
            except:
                after_value = 0

        elif data_type == 'boolean':
            if self.return_value.lower() == 'true':
                after_value = True
            else:
                after_value = False
        elif 'list' in data_type:
            if type(self.return_value) == str:
                after_value = eval(self.return_value)

        # 값을 변경하지 않은 경우에는 원래 값을 리턴한다.
        # (원래 값이 string 이므로 int/float와 타입과 달라서)
        if self.return_value == before_value:
            return before_value

        return after_value

    def closeEvent(self, event):
        self.edit_widget.accept()
        self.reject()
class ReadList(QWidget):
    """데이터가 List type인 read-only Widget 클래스"""
    def __init__(self, data):
        super().__init__()
        self.data = data.text(2)
        self.initUI()
        
    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
        self.item_list = ast.literal_eval(self.data)
        if self.item_list is not None and len(self.item_list) > 0:
            for i in self.item_list:
                self.listWidget.addItem(str(i))
        gridLayout.addWidget(self.listWidget)
        self.setLayout(gridLayout)

    def accept(self):
        return self.data

class ReadDict(QWidget):
    """데이터가 List type인 read-only Widget 클래스"""
    def __init__(self, data):
        super().__init__()
        self.data = data.text(2)
        self.initUI()
        
    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
        self.item_list = ast.literal_eval(self.data)
        if self.item_list is not None and len(self.item_list) > 0:
            for i, region in self.item_list.items():
                self.listWidget.addItem('{} : {}'.format(i, str(region)))
        gridLayout.addWidget(self.listWidget)
        self.setLayout(gridLayout)

    def accept(self):
        return self.data

class EditCombobox(QWidget):
    """데이터가 Combobox type인 데이터의 Widget 클래스"""
    def __init__(self, data):
        super().__init__()
        self.field = data.text(0)
        self.data = data.text(2)
        self.initUI()
        self.new_status = self.data

    def initUI(self):
        
        vbox = QVBoxLayout()
        combo = QComboBox()

        idx = QLabel(self.field)

        if self.field == 'orientation':
            combo.addItem('+')
            combo.addItem('-')
            combo.addItem('horizontal')
            combo.addItem('vertical')
            combo.addItem('none')
        elif self.field == 'initPositionMode':
            combo.addItem('Absolute')
            combo.addItem('Relative')
        elif self.field == 'pathGenerationMethod':            
            combo.addItem('FullRandom')         
            combo.addItem('LinkPath')
            combo.addItem('EndNode')
        elif self.field == 'desiredVelocitiyMode':            
            combo.addItem('Static')         
            combo.addItem('Dynamic')
        else:
            combo.addItem(str(True))
            combo.addItem(str(False))
        combo.setCurrentIndex(combo.findText(self.data))
        combo.activated[str].connect(self.setStatus)

        vbox.addWidget(idx)
        vbox.addWidget(combo)

        self.setLayout(vbox)

    def setStatus(self, data):
        self.new_status = data

    def accept(self):
        # print("Accpet", self.new_status)
        return self.new_status

class EditBoolean(QWidget):
    """데이터가 Boolean type인 데이터의 Widget 클래스"""
    def __init__(self, data):
        super().__init__()
        self.field = data.text(0)
        self.data = data.text(2)
        self.initUI()
        self.new_status = self.data

    def initUI(self):
        
        vbox = QVBoxLayout()
        combo = QComboBox()

        idx = QLabel(self.field)

        combo.addItem(str(True))
        combo.addItem(str(False))
        combo.setCurrentIndex(combo.findText(self.data))
        combo.activated[str].connect(self.setStatus)

        vbox.addWidget(idx)
        vbox.addWidget(combo)

        self.setLayout(vbox)

    def setStatus(self, data):
        self.new_status = data

    def accept(self):
        # print("Accpet", self.new_status)
        return self.new_status

class EditOneLine(QWidget):
    """데이터가 One Line(string, int, float 등)인 데이터의 Widget 클래스"""
    def __init__(self, data, isReadonly = False):
        super().__init__()
        self.type = str(data.text(1))
        self.data = data.text(2)
        self.isReadOnly = isReadonly
        self.initUI()
        self.new_idx = None

    def initUI(self):
        idx = QLabel('value : ')
        if self.data is None or self.data == 'None':
            self.idx_edit = QLineEdit()
        else:
            self.idx_edit = QLineEdit(self.data)
        
        if self.isReadOnly:
            self.idx_edit.setReadOnly(True)
        else:
            self.idx_edit.setReadOnly(False)

        hbox = QHBoxLayout()
        hbox.addWidget(idx)
        hbox.addWidget(self.idx_edit)
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

    def accept(self):
        text = self.idx_edit.text()
        if text != ''  and not self.iscorrect(text):
            QMessageBox.warning(self, "Type Error", "Please check the type")
            self.idx_edit.setText(self.data)
            return False
        else:
            self.new_idx = text
            return self.new_idx

class EditPoint(QWidget):
    """데이터가 Point(list<float>)인 데이터의 Widget 클래스"""
    def __init__(self, data):
        super().__init__()
        self.data = data.text(2)
        self.point_edit = eval(self.data)
        self.initUI()

    def initUI(self):
        point = self.point_edit
        vbox = QVBoxLayout()
        x = QLabel('X :')
        y = QLabel('Y :')
        z = QLabel('Z :')
        if self.data is None or self.data == 'None':
            self.x_edit = QLineEdit()
            self.y_edit = QLineEdit()
            self.z_edit = QLineEdit()
        else:
            self.x_edit = QLineEdit(str(point[0]))
            self.y_edit = QLineEdit(str(point[1]))
            self.z_edit = QLineEdit(str(point[2]))
        hbox_x = QHBoxLayout()
        hbox_x.addWidget(x, 1)
        hbox_x.addWidget(self.x_edit, 3.5)
        hbox_y = QHBoxLayout()
        hbox_y.addWidget(y, 1)
        hbox_y.addWidget(self.y_edit, 3.5)
        hbox_z = QHBoxLayout()
        hbox_z.addWidget(z, 1)
        hbox_z.addWidget(self.z_edit, 3.5)
        vbox.addLayout(hbox_x)
        vbox.addLayout(hbox_y)
        vbox.addLayout(hbox_z)
        self.setLayout(vbox)
        x_is_float = self.x_edit.textEdited.connect(lambda:self.setPoint(self.x_edit, str(point[0])))
        y_is_float = self.y_edit.textEdited.connect(lambda:self.setPoint(self.y_edit, str(point[1])))
        z_is_float = self.z_edit.textEdited.connect(lambda:self.setPoint(self.z_edit, str(point[2])))

    def setPoint(self, edit, orignal):
        if edit.text() != '' and not self.isfloat(edit.text()):
            QMessageBox.warning(self, "Type Error", "You must enter float type data")
            edit.setText(orignal)
            

    def isfloat(self, data):
        """새로운 데이터 값이 float형 인지 확인한다"""
        try:
            float(data)
            return True
        except ValueError:
            return False

    def accept(self):
        try:
            self.point_edit = [float(self.x_edit.text()), float(self.y_edit.text()), float(self.z_edit.text())]
        except ValueError:
            QMessageBox.warning(self, "Type Error", "You must enter float type data")
        # print("Accpet", self.point_edit)
        return self.point_edit

class EditPointList(QWidget):
    """데이터가 Point(list<float>)로 이루어진 List 데이터의 Widget 클래스"""

    def __init__(self, data):
        super().__init__()
        self.data = data.text(2)
        self.point_edit = None
        self.item_list = []
        self.initUI()

    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
            
        self.item_list = eval(self.data)
        if len(self.item_list) > 0:
            for i in eval(self.data):
                self.listWidget.addItem(str(i))

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self.action_add)

        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self.action_remove)

        btn_edit = QPushButton("Edit")
        btn_edit.clicked.connect(self.action_edit)

        btn_up = QPushButton("Move Up")
        btn_up.clicked.connect(self.action_up)

        btn_down = QPushButton("Move Down")
        btn_down.clicked.connect(self.action_down)

        gridLayout.addWidget(self.listWidget, 0, 0, 4, 1)
        gridLayout.addWidget(btn_add, 0, 1, 1, 1)
        gridLayout.addWidget(btn_remove, 1, 1, 1, 1)
        gridLayout.addWidget(btn_edit, 2, 1, 1, 1)
        gridLayout.addWidget(btn_up, 3, 1, 1, 1)
        gridLayout.addWidget(btn_down, 4, 1, 1, 1)

        # self.listWidget.itemSelectionChanged.connect(self.action_selected)

        self.setLayout(gridLayout)

    def addeditUI(self, point=None):
        self.msg = QDialog()
        self.pit = []
        popup = QVBoxLayout()
        qbtnbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.point_edit = point

        qx = QLabel('X :')
        self.qx_edit = QLineEdit()
        qy = QLabel('Y :')
        self.qy_edit = QLineEdit()
        qz = QLabel('Z :')
        self.qz_edit = QLineEdit()

        if point is not None:
            self.pit = eval(point)
            
            self.qx_edit = QLineEdit(str(self.pit[0]))
            self.qy_edit = QLineEdit(str(self.pit[1]))
            self.qz_edit = QLineEdit(str(self.pit[2]))

        qhbox_x = QHBoxLayout()
        qhbox_x.addWidget(qx, 1)
        qhbox_x.addWidget(self.qx_edit, 3.5)

        qhbox_y = QHBoxLayout()
        qhbox_y.addWidget(qy, 1)
        qhbox_y.addWidget(self.qy_edit, 3.5)

        qhbox_z = QHBoxLayout()
        qhbox_z.addWidget(qz, 1)
        qhbox_z.addWidget(self.qz_edit, 3.5)

        if self.pit is not None and self.pit != []:
            x_is_float = self.qx_edit.textEdited.connect(lambda:self.setPoint(self.qx_edit, str(self.pit[0])))
            y_is_float = self.qy_edit.textEdited.connect(lambda:self.setPoint(self.qy_edit, str(self.pit[1])))
            z_is_float = self.qz_edit.textEdited.connect(lambda:self.setPoint(self.qz_edit, str(self.pit[2])))

        popup.addLayout(qhbox_x)
        popup.addLayout(qhbox_y)
        popup.addLayout(qhbox_z)

        popup.addWidget(qbtnbox)
        
        qbtnbox.accepted.connect(self.addList)
        qbtnbox.rejected.connect(self.msg.reject)

        self.msg.setLayout(popup)
        self.msg.exec_()
    
    def addList(self):
        try:
            self.point_edit = [float(self.qx_edit.text()), float(self.qy_edit.text()), float(self.qz_edit.text())]
        except ValueError:
            QMessageBox.warning(self, "Type Error", "You must enter float type data")
        self.msg.reject()

    def setPoint(self, edit, orignal):
        if edit.text() != '' and not self.isfloat(edit.text()):
            QMessageBox.warning(self, "Type Error", "You must enter float type data")
            edit.setText(orignal)

    def action_add(self):
        self.addeditUI()
        if self.point_edit is not None:
            self.listWidget.addItem(str(self.point_edit))

    def action_edit(self):
        current_item = self.listWidget.currentIndex()
        self.addeditUI(current_item.data())
        self.listWidget.currentItem().setText(str(self.point_edit))


    def action_remove(self):
        # NOTE https://morai.atlassian.net/browse/MS-52
        # point 2개 남으면 삭제 X
        if self.listWidget.count() > 2:
            current_item = self.listWidget.currentIndex()
            self.listWidget.takeItem(current_item.row())
        else:
            QMessageBox.warning(self, "Type Error", "At least 2 points are required")

    def action_up(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow - 1, currentItem)
        self.listWidget.setCurrentRow(currentRow - 1)


    def action_down(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow + 1, currentItem)
        self.listWidget.setCurrentRow(currentRow + 1)


    def isfloat(self, data):
        try:
            float(data)
            return True
        except ValueError:
            return False

    def accept(self):
        return_array = []
        for i in range(self.listWidget.count()):
            return_array.append(eval(self.listWidget.item(i).text()))
        # print(return_array)
        self.item_list = return_array
        return return_array
        

class EditRotation(QWidget):
    """데이터가 Rotation(list<float>)인 데이터의 Widget 클래스"""
    def __init__(self, data):
        super().__init__()
        self.data = data.text(2)
        self.point_edit = eval(self.data)
        self.initUI()

    def initUI(self):
        point = self.point_edit
        vbox = QVBoxLayout()
        x = QLabel('Pitch :')
        y = QLabel('Yaw :')
        z = QLabel('Roll :')
        
        self.x_edit = QLineEdit(str(point[0]))
        self.y_edit = QLineEdit(str(point[1]))
        self.z_edit = QLineEdit(str(point[2]))

        hbox_x = QHBoxLayout()
        hbox_x.addWidget(x, 1)
        hbox_x.addWidget(self.x_edit, 3.5)
        hbox_y = QHBoxLayout()
        hbox_y.addWidget(y, 1)
        hbox_y.addWidget(self.y_edit, 3.5)
        hbox_z = QHBoxLayout()
        hbox_z.addWidget(z, 1)
        hbox_z.addWidget(self.z_edit, 3.5)
        vbox.addLayout(hbox_x)
        vbox.addLayout(hbox_y)
        vbox.addLayout(hbox_z)
        self.setLayout(vbox)
        x_is_float = self.x_edit.textEdited.connect(lambda:self.setPoint(self.x_edit, str(point[0])))
        y_is_float = self.y_edit.textEdited.connect(lambda:self.setPoint(self.y_edit, str(point[1])))
        z_is_float = self.z_edit.textEdited.connect(lambda:self.setPoint(self.z_edit, str(point[2])))

    def setPoint(self, edit, orignal):
        if edit.text() != '' and not self.isfloat(edit.text()):
            QMessageBox.warning(self, "Type Error", "You must enter float type data")
            edit.setText(orignal)
            

    def isfloat(self, data):
        """새로운 데이터 값이 float형 인지 확인한다"""
        try:
            float(data)
            return True
        except ValueError:
            return False

    def accept(self):
        try:
            self.point_edit = [float(self.x_edit.text()), float(self.y_edit.text()), float(self.z_edit.text())]
        except ValueError:
            QMessageBox.warning(self, "Type Error", "You must enter float type data")
        # print("Accpet", self.point_edit)
        return self.point_edit


class EditStringList(QWidget):

    """데이터 타입이 문자열 List인 데이터의 Widget 클래스"""

    def __init__(self, data, com_list=None):
        super().__init__()
        self.data = data.text(2)
        self.com_list = com_list
        self.item_list = []
        self.initUI()

    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
        self.item_list = ast.literal_eval(self.data)
        if len(self.item_list) > 0:
            for i in self.item_list:
                self.listWidget.addItem(str(i))

        btn_add = QPushButton("Add")
        btn_remove = QPushButton("Remove")
        btn_edit = QPushButton("Edit")
        btn_up = QPushButton("Move Up")
        btn_down = QPushButton("Move Down")

        btn_add.clicked.connect(self.action_add)
        btn_remove.clicked.connect(self.action_remove)
        btn_edit.clicked.connect(self.action_edit)
        btn_up.clicked.connect(self.action_up)
        btn_down.clicked.connect(self.action_down)

        gridLayout.addWidget(self.listWidget, 0, 0, 4, 1)
        gridLayout.addWidget(btn_add, 0, 1, 1, 1)
        gridLayout.addWidget(btn_remove, 1, 1, 1, 1)
        gridLayout.addWidget(btn_edit, 2, 1, 1, 1)
        gridLayout.addWidget(btn_up, 3, 1, 1, 1)
        gridLayout.addWidget(btn_down, 4, 1, 1, 1)

        self.setLayout(gridLayout)

    def action_add(self):
        # List에 존재 여부 확인
        itemsTextList =  [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Add to list", QLineEdit.Normal, '')
        if okPressed and new_idx != '':
            if self.com_list is None:
                 self.listWidget.addItem(new_idx)
            else:
                if new_idx in itemsTextList:
                    QMessageBox.warning(self, "Value Error", "Already in the list!")
                elif new_idx not in self.com_list:
                    QMessageBox.warning(self, "Value Error", "Enter the id included in the list.")
                else:
                    self.listWidget.addItem(new_idx)

    def action_edit(self):
        itemsTextList =  [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        current_item = self.listWidget.currentIndex()
        if current_item is not None:
            new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Edit Data", QLineEdit.Normal, current_item.data())
            if okPressed and new_idx != '':
                if self.com_list is None:
                    self.listWidget.currentItem().setText(str(new_idx))
                else:
                    if new_idx in itemsTextList:
                        QMessageBox.warning(self, "Value Error", "Already in the list!")
                    elif new_idx not in self.com_list:
                        QMessageBox.warning(self, "Value Error", "Enter the id included in the list.")
                    else:
                        self.listWidget.currentItem().setText(str(new_idx))

    def action_remove(self):
        current_item = self.listWidget.currentIndex()
        self.listWidget.takeItem(current_item.row())

    def action_up(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow - 1, currentItem)
        self.listWidget.setCurrentRow(currentRow - 1)


    def action_down(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow + 1, currentItem)
        self.listWidget.setCurrentRow(currentRow + 1)

    def accept(self):
        return_array = []
        for i in range(self.listWidget.count()):
            return_array.append(self.listWidget.item(i).text())
            
        self.item_list = return_array
        return return_array

class EditStringListList(QWidget):

    def __init__(self, data):
        super().__init__()
        self.data = data.text(2)
        self.item_list = []
        self.initUI()

    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
        self.item_list = ast.literal_eval(self.data)
        if len(self.item_list) > 0:
            for i in self.item_list:
                self.listWidget.addItem(str(i))

        btn_add = QPushButton("Add")
        btn_remove = QPushButton("Remove")
        btn_edit = QPushButton("Edit")
        btn_up = QPushButton("Move Up")
        btn_down = QPushButton("Move Down")

        btn_add.clicked.connect(self.action_add)
        btn_remove.clicked.connect(self.action_remove)
        btn_edit.clicked.connect(self.action_edit)
        btn_up.clicked.connect(self.action_up)
        btn_down.clicked.connect(self.action_down)

        gridLayout.addWidget(self.listWidget, 0, 0, 4, 1)
        gridLayout.addWidget(btn_add, 0, 1, 1, 1)
        gridLayout.addWidget(btn_remove, 1, 1, 1, 1)
        gridLayout.addWidget(btn_edit, 2, 1, 1, 1)
        gridLayout.addWidget(btn_up, 3, 1, 1, 1)
        gridLayout.addWidget(btn_down, 4, 1, 1, 1)

        self.setLayout(gridLayout)

    def action_add(self):
        itemsTextList =  [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Add to list", QLineEdit.Normal, '')
        if okPressed and new_idx != '':
            self.listWidget.addItem(self.inputTextToList(new_idx))

    def action_edit(self):
        itemsTextList =  [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        current_item = self.listWidget.currentIndex()
        if current_item is not None:
            try:
                current_val = ','.join(ast.literal_eval(current_item.data()))
            except:
                current_val = current_item.data()

            new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Edit Data", QLineEdit.Normal, current_val)
            if okPressed and new_idx != '':
                self.listWidget.currentItem().setText(self.inputTextToList(new_idx))

    def action_remove(self):
        current_item = self.listWidget.currentIndex()
        self.listWidget.takeItem(current_item.row())

    def action_up(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow - 1, currentItem)
        self.listWidget.setCurrentRow(currentRow - 1)


    def action_down(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow + 1, currentItem)
        self.listWidget.setCurrentRow(currentRow + 1)


    def inputTextToList(self, input_text):
        return_array = []
        if ', ' in input_text:
            text_array = input_text.split(', ')
            for i in text_array:
                return_array.append(i)
        elif ' ' in input_text:
            text_array = input_text.split(' ')
            for i in text_array:
                return_array.append(i)
        elif ',' in input_text:
            text_array = input_text.split(',')
            for i in text_array:
                return_array.append(i)
        else:
            return_array.append(input_text)
        return " ".join(return_array)


    def accept(self):
        return_array = []
        for i in range(self.listWidget.count()):
            try:
                input_array = ast.literal_eval(self.listWidget.item(i).text())
            except:
                input_array = self.listWidget.item(i).text()
            return_array.append(input_array)
        self.item_list = return_array
        return return_array


class EditIntList(QWidget):

    """데이터 타입이 문자열 List인 데이터의 Widget 클래스"""

    def __init__(self, data, com_list):
        super().__init__()
        self.data = data.text(2)
        self.com_list = com_list
        self.item_list = []
        self.initUI()

    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
        try:
            data = int(self.data)
            self.item_list = [data]
        except:
            self.item_list = ast.literal_eval(self.data)
            
        if len(self.item_list) > 0:
            for i in self.item_list:
                self.listWidget.addItem(str(i))

        btn_add = QPushButton("Add")
        btn_remove = QPushButton("Remove")
        btn_edit = QPushButton("Edit")
        btn_up = QPushButton("Move Up")
        btn_down = QPushButton("Move Down")

        btn_add.clicked.connect(self.action_add)
        btn_remove.clicked.connect(self.action_remove)
        btn_edit.clicked.connect(self.action_edit)
        btn_up.clicked.connect(self.action_up)
        btn_down.clicked.connect(self.action_down)

        gridLayout.addWidget(self.listWidget, 0, 0, 4, 1)
        gridLayout.addWidget(btn_add, 0, 1, 1, 1)
        gridLayout.addWidget(btn_remove, 1, 1, 1, 1)
        gridLayout.addWidget(btn_edit, 2, 1, 1, 1)
        gridLayout.addWidget(btn_up, 3, 1, 1, 1)
        gridLayout.addWidget(btn_down, 4, 1, 1, 1)

        self.setLayout(gridLayout)

    def action_add(self):
        # List에 존재 여부 확인
        itemsTextList =  [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Add to list", QLineEdit.Normal, '')
        new_idx = int(new_idx)
        if okPressed:
            if new_idx in itemsTextList:
                QMessageBox.warning(self, "Value Error", "Already in the list!")
            elif new_idx not in self.com_list:
                QMessageBox.warning(self, "Value Error", "Enter the id included in the list.")
            else:
                self.listWidget.addItem(str(new_idx))

    def action_edit(self):
        itemsTextList =  [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        current_item = self.listWidget.currentIndex()
        if current_item is not None:
            new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Edit Data", QLineEdit.Normal, current_item.data())
            new_idx = int(new_idx)
            if okPressed:
                if new_idx in itemsTextList:
                    QMessageBox.warning(self, "Value Error", "Already in the list!")
                elif new_idx not in self.com_list:
                    QMessageBox.warning(self, "Value Error", "Enter the id included in the list.")
                else:
                    self.listWidget.currentItem().setText(str(new_idx))

    def action_remove(self):
        current_item = self.listWidget.currentIndex()
        self.listWidget.takeItem(current_item.row())

    def action_up(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow - 1, currentItem)
        self.listWidget.setCurrentRow(currentRow - 1)


    def action_down(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow + 1, currentItem)
        self.listWidget.setCurrentRow(currentRow + 1)

    def accept(self):
        return_array = []
        for i in range(self.listWidget.count()):
            return_array.append(self.listWidget.item(i).text())
            
        self.item_list = return_array
        return return_array



class EditFloatList(QWidget):
    """데이터 타입이 Float List인 데이터의 Widget 클래스"""
    def __init__(self, data, date_type):
        super().__init__()
        self.data = data.text(2)
        self.item_list = []
        self.date_type = date_type
        self.initUI()

    def initUI(self):
        gridLayout = QGridLayout()
        self.listWidget = QListWidget()
        try:
            data = float(self.data)
            self.item_list = [data]
        except:
            self.item_list = ast.literal_eval(self.data)
            
        if len(self.item_list) > 0:
            for i in self.item_list:
                self.listWidget.addItem(str(i))

        btn_add = QPushButton("Add")
        btn_remove = QPushButton("Remove")
        btn_edit = QPushButton("Edit")
        btn_up = QPushButton("Move Up")
        btn_down = QPushButton("Move Down")

        btn_add.clicked.connect(self.action_add)
        btn_remove.clicked.connect(self.action_remove)
        btn_edit.clicked.connect(self.action_edit)
        btn_up.clicked.connect(self.action_up)
        btn_down.clicked.connect(self.action_down)

        gridLayout.addWidget(self.listWidget, 0, 0, 4, 1)
        gridLayout.addWidget(btn_add, 0, 1, 1, 1)
        gridLayout.addWidget(btn_remove, 1, 1, 1, 1)
        gridLayout.addWidget(btn_edit, 2, 1, 1, 1)
        gridLayout.addWidget(btn_up, 3, 1, 1, 1)
        gridLayout.addWidget(btn_down, 4, 1, 1, 1)

        self.setLayout(gridLayout)

    def action_add(self):
        # float
        new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Add to list", QLineEdit.Normal, '')
        if okPressed:
            if self.date_type == 'int' and self.isint(new_idx):
                self.listWidget.addItem(str(new_idx))
            elif self.date_type == 'float' and self.isfloat(new_idx):
                self.listWidget.addItem(str(new_idx))
            else:
                QMessageBox.warning(self, "Type Error", "You must enter float type data.")

    def action_edit(self):
        current_item = self.listWidget.currentIndex()
        if current_item is not None:
            new_idx, okPressed = QInputDialog.getText(self, "Mgeo Attribute", "Edit Data", QLineEdit.Normal, current_item.data())
            if okPressed:
                if self.date_type == 'int' and self.isint(new_idx):
                    self.listWidget.currentItem().setText(str(new_idx))
                elif self.date_type == 'float' and self.isfloat(new_idx):
                    self.listWidget.currentItem().setText(str(new_idx))
                else:
                    QMessageBox.warning(self, "Type Error", "You must enter float type data.")

    def action_remove(self):
        current_item = self.listWidget.currentIndex()
        self.listWidget.takeItem(current_item.row())

    def action_up(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow - 1, currentItem)
        self.listWidget.setCurrentRow(currentRow - 1)

    def action_down(self):
        current_item = self.listWidget.currentIndex()
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.takeItem(currentRow)
        self.listWidget.insertItem(currentRow + 1, currentItem)
        self.listWidget.setCurrentRow(currentRow + 1)

    def isfloat(self, data):
        """새로운 데이터 값이 float형 인지 확인한다"""
        try:
            float(data)
            return True
        except ValueError:
            return False

    def isint(self, data):
        """새로운 데이터 값이 int 인지 확인한다"""
        try:
            int(data)
            return True
        except ValueError:
            return False

    def accept(self):
        return_array = []
        for i in range(self.listWidget.count()):
            if self.date_type == 'int' and self.isint(new_idx):
                input_num = int(self.listWidget.item(i).text())
            elif self.date_type == 'float' and self.isfloat(new_idx):
                input_num = float(self.listWidget.item(i).text())
            return_array.append(input_num)
        self.item_list = return_array
        return return_array


    def accept(self):
        return_array = []
        for i in range(self.listWidget.count()):
            try:
                input_array = ast.literal_eval(self.listWidget.item(i).text())
            except:
                input_array = self.listWidget.item(i).text()
            return_array.append(input_array)
        self.item_list = return_array
        return return_array