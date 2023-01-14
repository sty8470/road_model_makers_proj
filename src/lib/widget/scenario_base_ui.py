from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from math import pi

import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.openscenario.class_defs.condition import *
from lib.openscenario.class_defs.environment import Environment
from lib.openscenario.class_defs.enumerations import *
from lib.openscenario.class_defs.environment import *
from lib.openscenario.class_defs.parameter import ParameterAddValueRule, ParameterMultiplyByValueRule, VariableAddValueRule
from lib.openscenario.class_defs.exceptions import InvalidSelectionError
from lib.openscenario.class_defs.position import *
from lib.openscenario.class_defs.global_action import *
from lib.openscenario.class_defs.private_action import *
from lib.openscenario.class_defs.user_defined_action import *
from lib.openscenario.class_defs.utils import truncate, clean_empty
from lib.widget.set_traffic_signal_controller import *

POSITION_LIST = ['World Position', 'Link Position', 'RelativeObjectPosition', 'RelativeWorldPosition']
BOOLEAN_TYPE_LIST = ['true', 'false']
BOOLEAN_TYPE_LIST_W_NONE = ['', 'true', 'false']

###  Utility Function ###
def isVisibleWidget(widget):
        if not widget.visibleRegion().isEmpty():
            return True
        return False        
'''Debugging Tool for pyqt5'''
class Debugger(QTextBrowser):
    def __init__(self, parent=None):
        super(Debugger, self).__init__(parent)
        self.setMaximumWidth(240)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setReadOnly(True)

    def write(self, text):
        self.append("• " + text)

class FileWidget(QWidget):
    def __init__(self):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.file_path_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def file_path_info(self):
        main_widget = QWidget()
        self.filePath = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('FilePath:', self.filePath)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'filepath':self.filePath.text()})
    
    def get_data(self):
        return FilePath(clean_empty({'filepath':self.filePath.text()}))

class WorldPositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        main_layout = QGridLayout()
        self.position = position
        self._link = None
        self._index = None
        if self.position != None:
            self._link = self.position['link']
            self._index = self.position['point_idx']
        
        default_validator = QDoubleValidator(decimals=14, notation=QDoubleValidator.StandardNotation)
        self.x = QLineEdit()
        self.x.setValidator(default_validator)
        self.y = QLineEdit()
        self.y.setValidator(default_validator)
        self.z = QLineEdit()
        self.z.setValidator(default_validator)
        self.h = QLineEdit()
        self.h.setValidator(default_validator)
        self.r = QLineEdit()
        self.r.setValidator(default_validator)
        self.p = QLineEdit()
        self.p.setValidator(default_validator)
        
        if self._link != None and self._index != None:
            point_x, point_y, point_z = self._link.points[self._index]
            self.x.setText(str(truncate(point_x, 3)))
            self.y.setText(str(truncate(point_y, 3)))
            self.z.setText(str(truncate(point_z, 3)))
        main_layout.setContentsMargins(0, 0, 0 ,0)
        main_layout.addWidget(QLabel('x(m)'), 0, 0)
        main_layout.addWidget(self.x, 0, 1)
        main_layout.addWidget(QLabel('y(m)'), 0, 2)
        main_layout.addWidget(self.y, 0, 3)

        main_layout.addWidget(QLabel('z(m)'), 0, 4)
        main_layout.addWidget(self.z, 0, 5)

        main_layout.addWidget(QLabel('h(deg)'),0, 6)
        main_layout.addWidget(self.h ,0,7)

        main_layout.addWidget(QLabel('p(deg)'), 0, 8)
        main_layout.addWidget(self.p, 0, 9)

        main_layout.addWidget(QLabel('r(deg)'), 0, 10)
        main_layout.addWidget(self.r, 0, 11)
        main_layout.setRowStretch(main_layout.rowCount(), 1)
        main_layout.setColumnStretch(main_layout.columnCount(), 1)
        main_layout.setSpacing(5)
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
    
    def get_elements(self):
        return clean_empty({'x':self.x.text(), 'y':self.y.text(), 'z':self.z.text(), 'h':self.h.text(), 'r':self.r.text(), 'p':self.p.text()})
    
    def get_data(self):
        attrib = clean_empty({'x':self.x.text(), 'y':self.y.text(), 'z':self.z.text(), 'h':self.h.text(), 'r':self.r.text(), 'p':self.p.text()})
        return WorldPosition(attrib)

class OrientationWidget(QWidget):
    def __init__(self):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.orientation_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def orientation_info(self):
        main_widget = QWidget()
        main_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        default_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.h = QLineEdit()
        self.h.setValidator(default_validator)
        self.p = QLineEdit()
        self.p.setValidator(default_validator)
        self.r = QLineEdit()
        self.r.setValidator(default_validator)
        type_list = ['absolute', 'relative']
        self.type_combo_box = QComboBox()
        self.type_combo_box.addItems(type_list)
        self.type_combo_box.setToolTip('Relative or absolute definition. Missing type value is interpreted as absolute.')
        
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QLabel('ReferenceContext'))
        hbox.addWidget(self.type_combo_box)
        hbox.addWidget(QLabel('h(deg)'))
        hbox.addWidget(self.h)
        hbox.addWidget(QLabel('p(deg)'))
        hbox.addWidget(self.p)
        hbox.addWidget(QLabel('r(deg)'))
        hbox.addWidget(self.r)
        main_widget.setLayout(hbox)
        return main_widget

    def get_elements(self):
        return clean_empty({'h':self.h.text(), 'p':self.p.text(), 'r':self.r.text(), 'type':self.type_combo_box.currentText()})

    def get_data(self):
        attrib = clean_empty({'h':self.h.text(), 'p':self.p.text(), 'r':self.r.text(), 'type':self.type_combo_box.currentText()})
        return Orientation(attrib)
    
class RelativeWorldPositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.relative_world_position(), 0, 0)
        self.position = position
        self._link = None
        self._index = None
        if self.position != None:
            self._link = self.position['link']
            self._index = self.position['point_idx']
        self.set_default_orientation_info_widget()
        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(grid_layout)
    
    def relative_world_position(self):
        main_widget = QWidget()
        main_widget.setContentsMargins(0, 0, 0, 0)
        default_validator = QDoubleValidator(decimals=14, notation=QDoubleValidator.StandardNotation)
        self.dx = QLineEdit()
        self.dx.setValidator(default_validator)
        self.dy = QLineEdit()
        self.dy.setValidator(default_validator)
        self.dz = QLineEdit()
        self.dz.setValidator(default_validator)
        self.entityRef = QLineEdit()

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(QLabel('EntityRef'), 0, 0)
        grid_layout.addWidget(self.entityRef, 0, 1)
        grid_layout.addWidget(QLabel('dx(m)'), 0, 2)
        grid_layout.addWidget(self.dx, 0, 3)
        grid_layout.addWidget(QLabel('dy(m)'), 0, 4)
        grid_layout.addWidget(self.dy, 0, 5)
        grid_layout.addWidget(QLabel('dz(m)'), 0, 6)
        grid_layout.addWidget(self.dz, 0, 7)
        grid_layout.setRowStretch(grid_layout.rowCount(), 1)
        grid_layout.setColumnStretch(grid_layout.columnCount(), 1)

        self.checkbox = QCheckBox()
        orientation_label = QLabel('Orientation')
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(orientation_label)
        self.checkbox.stateChanged.connect(self.update_orientation_info)
        
        self.orientation_vbox = QVBoxLayout()
        self.orientation_widget = OrientationWidget()
        self.orientation_vbox.addWidget(self.orientation_widget)

        form_layout = QFormLayout()
        form_layout.addRow(container, self.checkbox)

        vbox = QVBoxLayout()
        vbox.addLayout(grid_layout)
        vbox.addLayout(form_layout)
        vbox.addLayout(self.orientation_vbox)

        main_widget.setLayout(vbox)
        return main_widget
    
    def set_default_orientation_info_widget(self):
        self.hide_all_widgets()
        self.orientation_widget.setVisible(False)
    
    def update_orientation_info(self, state):
        self.hide_all_widgets()
        if state == Qt.Checked:
            self.orientation_widget.show()
        else:
            self.orientation_widget.hide()

    def hide_all_widgets(self):
        for i in range(0, self.orientation_vbox.count()):
            self.orientation_vbox.itemAt(i).widget().hide()

    def get_orientation_info_elements(self):
        if self.checkbox.isChecked():
            return self.orientation_widget.get_elements()
        else:
            return None
    
    def get_orientation_info_data(self):
        if self.checkbox.isChecked():
            return self.orientation_widget.get_data()
        else:
            return None

    def get_elements(self):
        return clean_empty({'dx':self.dx.text(), 'dy':self.dy.text(), 'dz':self.dz.text(), 
                            'entityRef':self.entityRef.text(), 'Orientation':self.get_orientation_info_elements()})
    
    def get_data(self):
        attrib = clean_empty({'dx':self.dx.text(), 'dy':self.dy.text(), 'dz':self.dz.text(),
                              'entityRef':self.entityRef.text()})
        return RelativeWorldPosition(attrib, self.get_orientation_info_data())
    
class RoadPositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        main_layout = QFormLayout()
        self.position = position
        
        default_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.roadid = QLineEdit()
        self.s = QLineEdit()
        self.s.setValidator(default_validator)
        self.t = QLineEdit()
        self.t.setValidator(default_validator)
        self.orientation_widget = OrientationWidget()
        main_layout.addRow('roadId:', self.roadid)
        main_layout.addRow('s(m):', self.s)
        main_layout.addRow('t(m):', self.t)
        main_layout.addRow('Orientation:', self.orientation_widget)
    
    def get_elements(self):
        attrib = clean_empty({'roadId':self.roadid.text(), 's':self.s.text(), 't':self.t.text(), 'Orientation':self.orientation_widget.get_elements()})
        return attrib

    def get_data(self):
        attrib = clean_empty({'roadId':self.roadid.text(), 's':self.s.text(), 't':self.t.text()})
        orientation = self.orientation_widget.get_data()
        return RoadPosition(attrib, orientation)

class RelativeRoadPositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        main_layout = QFormLayout()
        self.position = position
        
        default_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.ds = QLineEdit()
        self.ds.setValidator(default_validator)
        self.dt = QLineEdit()
        self.dt.setValidator(default_validator)
        self.entityRef = QLineEdit()
        self.orientation_widget = OrientationWidget()
        main_layout.addRow('entityRef:', self.entityRef)
        main_layout.addRow('ds(m):', self.ds)
        main_layout.addRow('dt(m):', self.dt)
        main_layout.addRow('Orientation:', self.orientation_widget)
        self.setLayout(main_layout)
        
    def get_elements(self):
        return clean_empty({'ds':self.ds.text(), 'dt':self.dt.text(), 
                            'entityRef':self.entityRef.text(), 'Orientation':self.orientation_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'ds':self.ds.text(), 'dt':self.dt.text(), 'entityRef':self.entityRef.text()})
        return RelativeRoadPosition(attrib, self.orientation_widget.get_data())

class LanePositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        main_layout = QFormLayout()
        self.position = position
        
        default_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.laneId = QLineEdit()
        self.offset = QLineEdit()
        self.offset.setValidator(default_validator)
        self.roadId = QLineEdit()
        self.s = QLineEdit()
        self.orientation_widget = OrientationWidget()
        main_layout.addRow('LaneId:', self.laneId)
        main_layout.addRow('Offset(m):', self.offset)
        main_layout.addRow('RoadId:', self.roadId)
        main_layout.addRow('s(m):', self.s)
        main_layout.addRow('Orientation:', self.orientation_widget)
        self.setLayout(main_layout)
    
    def get_elements(self):
        return clean_empty({'laneId':self.laneId.text(), 'offset':self.offset.text(), 'roadId':self.roadId.text(),
                              's':self.s.text(), 'Orientation':self.orientation_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'laneId':self.laneId.text(), 'offset':self.offset.text(), 'roadId':self.roadId.text(),
                              's':self.s.text()})
        return LanePosition(attrib, self.orientation_widget.get_data())
    
class RelativeLanePositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        main_layout = QFormLayout()
        self.position = position
        double_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.dLane = QLineEdit()
        self.dLane.setValidator(QIntValidator(bottom=0))
        self.ds = QLineEdit()
        self.ds.setValidator(double_validator)
        self.dsLane = QLineEdit()
        self.dsLane.setValidator(double_validator)
        self.entityRef = QLineEdit()
        self.offset = QLineEdit()
        self.offset.setValidator(double_validator)
        self.orientation_widget = OrientationWidget()
        
        main_layout.addRow('DLane:', self.dLane)
        main_layout.addRow('Ds(m):', self.ds)
        main_layout.addRow('DsLane(m):', self.dsLane)
        main_layout.addRow('EntityRef:', self.entityRef)
        main_layout.addRow('Offset(m):', self.offset)
        main_layout.addRow('Orientation:', self.orientation_widget)
        self.setLayout(main_layout)
    
    def get_elements(self):
        return clean_empty({'dLane':self.dLane.text(), 'ds':self.ds.text(), 'dsLane':self.dsLane.text(), 
                            'entityRef':self.entityRef.text(), 'offset':self.offset.text(), 
                            'Orientation':self.orientation_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'dLane':self.dLane.text(), 'ds':self.ds.text(), 'dsLane':self.dsLane.text(), 
                            'entityRef':self.entityRef.text(), 'offset':self.offset.text()})
        return RelativeLanePosition(attrib, self.orientation_widget.get_data())
    
class RoutePositionWidget(QWidget):
    def __init__(self, position=None):
        pass
    
class GeoPositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        self.position = position
        
        main_layout = QFormLayout()
        self.altitude = QLineEdit()
        self.latitudeDeg = QLineEdit()
        self.longitudeDeg = QLineEdit()
        self.orientation_widget = OrientationWidget()
        main_layout.addRow('Altitudie(m)', self.altitude)
        main_layout.addRow('LatitudeDeg(deg):', self.latitudeDeg)
        main_layout.addRow('LongitudeDeg(deg):', self.longitudeDeg)
        main_layout.addRow('Orientation:', self.orientation_widget)
        self.setLayout(main_layout)
    
    def get_element(self):
        return clean_empty({'altitude':self.altitude.text(), 'latitudeDeg':self.latitudeDeg.text(),
                            'longitudeDeg':self.longitudeDeg.text(), 'Orientation':self.orientation_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'altitude':self.altitude.text(), 'latitudeDeg':self.latitudeDeg.text(),
                            'longitudeDeg':self.longitudeDeg.text()})
        return GeoPosition(attrib, self.orientation_widget.get_data())
        
class TrajectoryPositionWidget(QWidget):
    def __init__(self, position=None):
        pass

class LinkPositionWidget(QWidget):
    def __init__(self, position=None):
        super().__init__()
        self.position = position
        self._link = None
        self._index = None
        
        if self.position != None:
            self._link = self.position['link']
            self._index = self.position['point_idx']
        
        main_layout = QGridLayout()
        self.link_id = QLineEdit()
        self.index = QLineEdit()
        self.index.setValidator(QIntValidator(bottom=0))
        
        if self._link != None and self._index != None:
            link = self._link.idx
            index = self._index
            self.link_id.setText(str(link))
            self.index.setText(str(index))
        
        main_layout.addWidget(QLabel('Link ID'), 0, 0)
        main_layout.addWidget(self.link_id, 0, 1)
        main_layout.addWidget(QLabel('Index'), 0, 2)
        main_layout.addWidget(self.index, 0, 3)
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setRowStretch(main_layout.rowCount(), 1)
        self.setLayout(main_layout)

    def get_elements(self):
        return clean_empty({'id': self.link_id.text(), 'index':self.index.text()})

    def get_data(self):
        attrib = clean_empty({'id': self.link_id.text(), 'index':self.index.text()})
        return LinkPosition(attrib)

class RelativeObjectPositionWidget(QWidget):
    def __init__(self):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.relative_object_position(), 0, 0)
        self.set_default_orientation_info_widget()
        self.setLayout(grid_layout)
    
    def relative_object_position(self):
        main_widget = QWidget()
        main_widget.setContentsMargins(0, 0, 0, 0)
        default_validator = QDoubleValidator(decimals=14, notation=QDoubleValidator.StandardNotation)
        self.dx = QLineEdit()
        self.dx.setValidator(default_validator)
        self.dy = QLineEdit()
        self.dy.setValidator(default_validator)
        self.dz = QLineEdit()
        self.dz.setValidator(default_validator)
        self.entityRef = QLineEdit()
        
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(QLabel('EntityRef'), 0, 0)
        grid_layout.addWidget(self.entityRef, 0, 1)
        grid_layout.addWidget(QLabel('dx(m)'), 0, 2)
        grid_layout.addWidget(self.dx, 0, 3)
        grid_layout.addWidget(QLabel('dy(m)'), 0, 4)
        grid_layout.addWidget(self.dy, 0, 5)
        grid_layout.addWidget(QLabel('dz(m)'), 0, 6)
        grid_layout.addWidget(self.dz, 0, 7)
        grid_layout.setRowStretch(grid_layout.rowCount(), 1)
        grid_layout.setColumnStretch(grid_layout.columnCount(), 1)

        self.checkbox = QCheckBox()
        orientation_label = QLabel('Orientation')
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(orientation_label)
        self.checkbox.stateChanged.connect(self.update_orientation_info)
        
        self.orientation_vbox = QVBoxLayout()
        self.orientation_widget = OrientationWidget()
        self.orientation_vbox.addWidget(self.orientation_widget)

        form_layout = QFormLayout()
        form_layout.addRow(container, self.checkbox)

        vbox = QVBoxLayout()
        vbox.addLayout(grid_layout)
        vbox.addLayout(form_layout)
        vbox.addLayout(self.orientation_vbox)

        main_widget.setLayout(vbox)
        return main_widget

    def set_default_orientation_info_widget(self):
        self.hide_all_widgets()
        self.orientation_widget.setVisible(False)
    
    def update_orientation_info(self, state):
        self.hide_all_widgets()
        if state == Qt.Checked:
            self.orientation_widget.show()
        else:
            self.orientation_widget.hide()

    def hide_all_widgets(self):
        for i in range(0, self.orientation_vbox.count()):
            self.orientation_vbox.itemAt(i).widget().hide()

    def get_orientation_info_elements(self):
        if self.checkbox.isChecked():
            return self.orientation_widget.get_elements()
        else:
            return None
    
    def get_orientation_info_data(self):
        if self.checkbox.isChecked():
            return self.orientation_widget.get_data()
        else:
            return None

    def get_elements(self):
        return clean_empty({'dx':self.dx.text(), 'dy':self.dy.text(), 
                            'dz':self.dz.text(), 'entityRef':self.entityRef.text(),
                            'orientation':self.get_orientation_info_elements()})
    
    def get_data(self):
        attrib = clean_empty({'dx':self.dx.text(), 'dy':self.dy.text(), 'dz':self.dz.text(), 'entityRef':self.entityRef.text()})
        return RelativeObjectPosition(attrib, self.get_orientation_info_data())
        
class ValueConstraintWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.value = QLineEdit()
        self.value.setToolTip('A constant value, parameter or parameter expression')
        form_layout = QFormLayout()
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('value:', self.value)
        self.setLayout(form_layout)
        
    def find_current_text(self):
         return self.rule_combo_box.currentText()
     
    def get_data(self):
        return
    
class ValueConstraintGroupWidget(QWidget):
    def __init__(self, constraint_group_dict, parent=None):
        super().__init__(parent)
        self.constraint_group_dict = constraint_group_dict
        self.value_constraint_group = []
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        value_constraint_widget = ValueConstraintWidget()
        self.main_layout.insertWidget(0, value_constraint_widget)
        self.value_constraint_group.append(value_constraint_widget)
        self.button_layout = self.make_button_layout()
        self.main_layout.addLayout(self.button_layout, -1)
        self.setLayout(self.main_layout)
        
    def make_button_layout(self):
        grid_layout = QGridLayout()
        self.add_value_constraint_btn = QPushButton("add value constraint")
        self.add_value_constraint_btn.clicked.connect(self.add_value_constraint_widget)
        self.delete_value_constraint_btn = QPushButton("delete value constraint")
        self.delete_value_constraint_btn.clicked.connect(self.delete_value_constraint_widget)
        grid_layout.addWidget(self.add_value_constraint_btn, 0, 0)
        grid_layout.addWidget(self.delete_value_constraint_btn, 0, 1)
        return grid_layout

    @pyqtSlot()
    def add_value_constraint_widget(self):
        new_value_constraint_widget = ValueConstraintWidget()
        index = self.main_layout.count()-1
        self.main_layout.insertWidget(index, new_value_constraint_widget)
        self.value_constraint_group.append(new_value_constraint_widget)
    
    @pyqtSlot()
    def delete_value_constraint_widget(self):
        index = self.main_layout.count()-2
        if index < 1:
            QMessageBox.warning(self, 'Warning', 'Cannot delete the value constraint')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.value_constraint_group.pop()
        
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
    
    def get_data(self):
        return
        
class ParameterDeclarationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        parameter_type_list = [str(parameter_type.name) for parameter_type in ParameterType]
        self.name = QLineEdit()
        self.name.setToolTip('Name of the parameter')
        self.parameter_type_combo_box = QComboBox()
        self.parameter_type_combo_box.addItems(parameter_type_list)
        self.parameter_type_combo_box.setToolTip('Type of the parameter.')
        self.value = QLineEdit()
        self.value.setToolTip('Value of the parameter as its default value.')
        
        constraint_group_dict = {}
        self.constraint_group_widget = ValueConstraintGroupWidget(constraint_group_dict)
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('ParameterType:', self.parameter_type_combo_box)
        form_layout.addRow('Value:', self.value)
        form_layout.addRow('ConstraintGroups:', self.constraint_group_widget)
        self.setLayout(form_layout)
        
    def get_data(self):
        return 

class SunWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.sun_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def sun_info(self):
        main_widget = QWidget()
        self.azimuth = QLineEdit()
        self.azimuth.setValidator(QDoubleValidator(bottom=0, top=2*pi, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.azimuth.setPlaceholderText('Range: [0..2PI]')
        self.elevation = QLineEdit()
        self.elevation.setValidator(QDoubleValidator(bottom=-pi, top=pi, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.elevation.setPlaceholderText('Range: [-PI..PI]')
        self.illuminance = QLineEdit()
        self.illuminance.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.illuminance.setPlaceholderText('Range: [0..inf]')
        
        form_layout = QFormLayout()
        form_layout.addRow('Azimuth(rad):',self.azimuth)
        form_layout.addRow('Elevation(rad):',self.elevation)
        form_layout.addRow('Illuminance(lux)',self.illuminance)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'azimuth':self.azimuth.text(),'elevation':self.elevation.text(),'illuminance':self.illuminance.text()})
    
    def get_data(self):
        attrib = clean_empty({'azimuth':self.azimuth.text(),'elevation':self.elevation.text(),'illuminance':self.illuminance.text()})
        return Sun(attrib)

class FogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.fog_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def fog_info(self):
        main_widget = QWidget()
        self.visualRange = QLineEdit()
        self.visualRange.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.visualRange.setPlaceholderText('Range: [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('VisualRange(m):',self.visualRange)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'visualRange':self.visualRange.text()})
    
    def get_data(self):
        attrib = clean_empty({'visualRange':self.visualRange.text()})
        return Fog(attrib)
 
class PrecipitationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.precipitation_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def precipitation_info(self):
        main_widget = QWidget()
        precipitation_type_list = [str(percipitation.name) for percipitation in PrecipitationType]
        self.precipitationIntensity = QLineEdit()
        self.precipitationIntensity.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.precipitationIntensity.setPlaceholderText('Range: [0..inf]')
        self.precipitation_type_combo_box = QComboBox()
        self.precipitation_type_combo_box.addItems(precipitation_type_list)
        
        form_layout = QFormLayout()
        form_layout.addRow('PrecipitationIntensity(mm/h):',self.precipitationIntensity)
        form_layout.addRow('PrecipitationType:',self.precipitation_type_combo_box)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def find_current_text(self):
        return self.precipitation_type_combo_box.currentText()
    
    def get_elements(self):
        return clean_empty({'precipitationIntensity':self.precipitationIntensity.text(),
                              'precipitationType':self.find_current_text()})
    
    def get_data(self):
        attrib = clean_empty({'precipitationIntensity':self.precipitationIntensity.text(),
                              'precipitationType':self.find_current_text()})
        return Precipitation(attrib)

class Windwidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.wind_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def wind_info(self):
        main_widget = QWidget()
        self.direction = QLineEdit()
        self.direction.setValidator(QDoubleValidator(bottom=0, top=2*pi, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.direction.setPlaceholderText('Range [0..2PI]')
        self.speed = QLineEdit()
        self.speed.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.speed.setPlaceholderText('Range [0..inf]')
        
        form_layout = QFormLayout()
        form_layout.addRow('Direction(rad):',self.direction)
        form_layout.addRow('Speed(m/s):',self.speed)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'direction':self.direction.text(),'speed':self.speed.text()})
    
    def get_data(self):
        attrib = clean_empty({'direction':self.direction.text(),'speed':self.speed.text()})
        return Wind(attrib)

class TimeOfDayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.time_of_day_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def time_of_day_info(self):
        main_widget = QWidget()
        self.dateTime = QDateTimeEdit()
        self.animation_combo_box = QComboBox()
        self.animation_combo_box.addItems(BOOLEAN_TYPE_LIST)
        form_layout = QFormLayout()
        form_layout.addRow('Animation:', self.animation_combo_box)
        form_layout.addRow('DateTime:', self.dateTime)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'animation':self.animation_combo_box.currentText(),
                            'dateTime':self.dateTime.dateTime().toString(Qt.ISODate)})
    
    def get_data(self):
        attrib = clean_empty({'animation':self.animation_combo_box.currentText(),
                              'dateTime':self.dateTime.dateTime().toString(Qt.ISODate)})
        return TimeOfDay(attrib)

class DomeImageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.dome_image_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def dome_image_info(self):
        main_widget = QWidget()
        self.azimuthOffset = QLineEdit()
        self.azimuthOffset.setValidator(QDoubleValidator(bottom=0, top=2*pi, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.azimuthOffset.setPlaceholderText('Range: [0..2PI]')
        self.domeFile = FileWidget()
        form_layout = QFormLayout()
        form_layout.addRow('AzimuthOffset(degree):', self.azimuthOffset)
        form_layout.addRow('DomeFile:', self.domeFile)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'azimuthOffset':self.azimuthOffset.text(), 'domeFile':self.domeFile.get_elements})
    
    def get_data(self):
        attrib = clean_empty({'azimuthOffset':self.azimuthOffset.text()})
        return DomeImage(attrib, self.domeFile.get_data())

class WeatherWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.weather_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def weather_info(self):
        main_widget = QWidget()
        fractionalCloudCover_list = [str(fractionalCloudCover.name) for fractionalCloudCover in FractionalCloudCover]
        
        self.atmosphericPressure = QLineEdit()
        self.atmosphericPressure.setValidator(QDoubleValidator(bottom=80000, top=120000, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.atmosphericPressure.setPlaceholderText('Range: [80000...120000]')
        self.fractionalCloudCover_combo_box = QComboBox()
        self.fractionalCloudCover_combo_box.addItems(fractionalCloudCover_list)
        
        self.sun = SunWidget()
        self.fog = FogWidget()
        self.precipitation = PrecipitationWidget()
        self.wind = Windwidget()
        self.domeImage = DomeImageWidget()
        self.temperature = QLineEdit()
        self.temperature.setValidator(QDoubleValidator(bottom=170, top=340, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.temperature.setPlaceholderText('Range: [170...340]')
        form_layout = QFormLayout()
        form_layout.addRow('AtmosphericPressure(Pa):', self.atmosphericPressure)
        form_layout.addRow('FractionalCloudCover:', self.fractionalCloudCover_combo_box)
        form_layout.addRow('Temperature(K):', self.temperature)
        form_layout.addRow('Sun:', self.sun)
        form_layout.addRow('Fog:', self.fog)
        form_layout.addRow('Precipitation:', self.precipitation)
        form_layout.addRow('Wind:',self.wind)
        form_layout.addRow('DomeImage:', self.domeImage)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'atmosphericPressure':self.atmosphericPressure.text(),
                            'fractionalCloudCover':self.fractionalCloudCover_combo_box.currentText(),
                            'temperature':self.temperature.text(),
                            'sun':self.sun.get_elements(),
                            'fog':self.fog.get_elements(),
                            'precipitation':self.precipitation.get_elements(),
                            'wind':self.wind.get_elements(),
                            'domeImage':self.domeImage.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({
            'atmosphericPressure':self.atmosphericPressure.text(),
            'fractionalCloudCover':self.fractionalCloudCover_combo_box.currentText(),
            'temperature':self.temperature.text()})
        
        return Weather(attrib,
                       sun=self.sun.get_data(),
                       fog=self.fog.get_data(),
                       precipitation=self.precipitation.get_data(),
                       wind=self.wind.get_data(),
                       dome_image=self.domeImage.get_data())

class RoadConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.road_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def road_condition_info(self):
        main_widget = QWidget()
        self.frictionScaleFactor = QLineEdit()
        self.frictionScaleFactor.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.frictionScaleFactor.setPlaceholderText('Range [0..inf]')
        wetness_type_list = [str(wetness.name) for wetness in Wetness]
        self.wetness_combo_box = QComboBox()
        self.wetness_combo_box.addItems(wetness_type_list)
        
        form_layout = QFormLayout()
        form_layout.addRow('FrictionScaleFactor:', self.frictionScaleFactor)
        form_layout.addRow('Wetness:', self.wetness_combo_box)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'frictionScaleFactor':self.frictionScaleFactor.text(), 
                            'wetness':self.wetness_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'frictionScaleFactor':self.frictionScaleFactor.text(),
                              'wetness':self.wetness_combo_box.currentText()})
        return RoadCondition(attrib)
    
# Action
class EnvironmentActionWidget(QWidget):
    def __init__(self):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.environment_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def environment_info(self):
        groupbox = QGroupBox('Environment')
        vbox = QVBoxLayout()
        self.environment_name = QLineEdit()
        self.environment_name.setFixedWidth(300)
        self.timeofday = TimeOfDayWidget()
        self.weather = WeatherWidget()
        self.roadcondition = RoadConditionWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.environment_name)
        form_layout.addRow('TimeOfDay:', self.timeofday)
        form_layout.addRow('Weather:',  self.weather)
        form_layout.addRow('Roadcondition:', self.roadcondition)
        
        vbox.addLayout(form_layout)
        groupbox.setLayout(vbox)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'name':self.environment_name.text(), 
                'timeofday':self.timeofday.get_elements(),
                'weather':self.weather.get_elements(),
                'roadcondition':self.roadcondition.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.environment_name.text()})
        return EnvironmentAction(Environment(attrib,
                           None,
                           timeofday=self.timeofday.get_data(),
                           weather=self.weather.get_data(),
                           roadcondition=self.roadcondition.get_data()))
        
class AddEntityActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        form_layout = QFormLayout()
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        self.setLayout(form_layout)

    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    # def set_default_position_widget(self):

    # def hide_position_widgets(self):
    #     for i in range(self.)

    def get_elements(self):
        return {'position':self.get_position_elements()}
    
    def get_data(self):
        return AddEntityAction(position=self.get_position_data())

class EntityActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.entity_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def entity_action_info(self):
        groupbox = QGroupBox('EntityAction')
        entity_action_list = ['addEntityAction', 'deleteEntityAction']
        self.entity_action_combo_box = QComboBox()
        self.entity_action_combo_box.addItems(entity_action_list)
        self.entity_action_combo_box.activated[str].connect(self.update_action)
        
        self.entity_ref = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('EntityRef:', self.entity_ref)
        form_layout.addRow('EntityAction:', self.entity_action_combo_box)
        
        self.hbox = QHBoxLayout()
        self.add_entity_action = AddEntityActionWidget()
        self.hbox.addWidget(self.add_entity_action)
        
        form_layout.addWidget(self.add_entity_action)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def hide_widgets(self):
        for i in range(4, self.hbox.count()):
            self.hbox.itemAt(i).widget().hide()    

    def update_action(self, choice):
        self.hide_widgets()
        if choice == 'addEntityAction':
            self.add_entity_action.show()
        else:
            self.add_entity_action.hide()
    
    def get_elements(self):
        if self.entity_action_combo_box.currentText() == 'addEntityAction':
            return clean_empty({'entityRef':self.entity_ref.text(), 'addEntityAction':self.add_entity_action.get_elements()})
        else:
            return clean_empty({'entityRef':self.entity_ref.text(), 'deleteEntityAction':self.add_entity_action.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entity_ref.text()})
        if self.entity_action_combo_box.currentText() == 'addEntityAction':
            return EntityAction(attrib, self.add_entity_action.get_data(), None)
        else:
            return EntityAction(attrib, None, DeleteEntityAction())
        
class ParameterSetActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.parameter_set_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def parameter_set_action_info(self):
        main_widget = QWidget()
        form_layout = QFormLayout()
        self.value = QLineEdit()
        self.value.setToolTip('The new value for the parameter')
        form_layout.addRow('Value:',self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        return ParameterSetAction(attrib)

class ParameterModifyActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.parameter_modify_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def parameter_modify_action_info(self):
        main_widget = QWidget()
        modify_action_list = ['addValue', 'multiplyByValue']
        self.modify_rule_combo_box = QComboBox()
        self.modify_rule_combo_box.addItems(modify_action_list)
        
        form_layout = QFormLayout()
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [-inf..inf]')
        self.value.setToolTip('Either adding a value to a parameter or multiply the parameter by a value')
        form_layout.addRow('ModifyRule:', self.modify_rule_combo_box)
        form_layout.addRow('Value:', self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        if self.modify_rule_combo_box.currentText() == 'addValue':
            return clean_empty({'modifyRule':self.modify_rule_combo_box.currentText(), 'value':self.value.text()})
        else:
            return clean_empty({'modifyRule':self.modify_rule_combo_box.currentText(), 'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        add_value, multiply_value = None, None
        if self.modify_rule_combo_box.currentText() == 'addValue':
            add_value = ParameterAddValueRule(attrib)
        else:
            multiply_value = ParameterMultiplyByValueRule(attrib)
        return ParameterModifyRule(add_value, multiply_value)

# ! PrameterActionWidget is deprecated on OSC 1.2 !
class ParameterActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.parameter_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def parameter_action_info(self):
        groupbox = QGroupBox('ParameterAction')
        parameter_action_type_list = ['setAction', 'modifyAction']
        self.parameter_action_combo_box = QComboBox()
        self.parameter_action_combo_box.addItems(parameter_action_type_list)
        self.parameter_action_combo_box.activated[str].connect(self.update_action)
        
        self.parameter_ref = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('ParameterRef:', self.parameter_ref)
        form_layout.addRow('Action Type:', self.parameter_action_combo_box)
        
        self.parameter_action = QStackedWidget()
        self.parameter_set_action = ParameterSetActionWidget()
        self.parameter_modify_action = ParameterModifyActionWidget()
        self.parameter_action.addWidget(self.parameter_set_action)
        self.parameter_action.addWidget(self.parameter_modify_action)
        form_layout.addWidget(self.parameter_action)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def update_action(self, choice):
        if choice == 'setAction':
            self.parameter_action.setCurrentWidget(self.parameter_set_action)
        else:
            self.parameter_action.setCurrentWidget(self.parameter_modify_action)
    
    def get_elements(self):
        if self.parameter_action_combo_box.currentText() == 'setAction':
            return clean_empty({'parameterRef':self.parameter_ref.text(), 
                    'setAction':self.parameter_set_action.get_elements()})
        else:
            return clean_empty({'parameterRef':self.parameter_ref.text(), 
                    'modifyAction':self.parameter_modify_action.get_elements()})
                
    def get_data(self):
        attrib = clean_empty({'parameterRef':self.parameter_ref.text()})
        if self.parameter_action_combo_box.currentText() == 'setAction':
            return ParameterAction(attrib,
                                   set_param_action=self.parameter_set_action.get_data(), 
                                   modify_param_action=None)
        else:
            return ParameterAction(attrib,
                                   set_param_action=None,
                                   modify_param_action=self.parameter_modify_action.get_data())

class VariableSetActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.variable_set_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def variable_set_action_info(self):
        main_widget = QWidget()
        form_layout = QFormLayout()
        self.value = QLineEdit()
        self.value.setToolTip('The new value for the variable')
        form_layout.addRow('Value:',self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        return VariableSetAction(attrib)

class VariableModifyActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.variable_modify_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def variable_modify_action_info(self):
        main_widget = QWidget()
        modify_action_list = ['addValue', 'multiplyByValue']
        self.modify_rule_combo_box = QComboBox()
        self.modify_rule_combo_box.addItems(modify_action_list)
        
        form_layout = QFormLayout()
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [-inf..inf]')
        self.value.setToolTip('Either adding a value to a parameter or multiply the variable by a value')
        form_layout.addRow('ModifyRule:', self.modify_rule_combo_box)
        form_layout.addRow('Value:', self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        if self.modify_rule_combo_box.currentText() == 'addValue':
            return clean_empty({'modifyRule':self.modify_rule_combo_box.currentText(), 'value':self.value.text()})
        else:
            return clean_empty({'modifyRule':self.modify_rule_combo_box.currentText(), 'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        if self.modify_rule_combo_box.currentText() == 'addValue':
            return VariableModifyAction(VariableModifyRule(VariableAddValueRule(attrib), None))
        else:
            return VariableModifyAction(VariableModifyRule(None, VariableMultiplyByValueRule(attrib)))

class VariableActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.variable_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def variable_action_info(self):
        groupbox = QGroupBox('VariableAction')
        variable_action_type_list = ['setAction', 'modifyAction']
        self.variable_action_combo_box = QComboBox()
        self.variable_action_combo_box.addItems(variable_action_type_list)
        self.variable_action_combo_box.activated[str].connect(self.update_action)
        
        self.variable_ref = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('VariableRef:', self.variable_ref)
        form_layout.addRow('Action Type:', self.variable_action_combo_box)
        
        self.variable_action = QStackedWidget()
        self.variable_set_action = VariableSetActionWidget()
        self.variable_modify_action = VariableModifyActionWidget()
        self.variable_action.addWidget(self.variable_set_action)
        self.variable_action.addWidget(self.variable_modify_action)
        form_layout.addWidget(self.variable_action)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def update_action(self, choice):
        if choice == 'setAction':
            self.variable_action.setCurrentWidget(self.variable_set_action)
        else:
            self.variable_action.setCurrentWidget(self.variable_modify_action)
    
    def get_elements(self):
        if self.variable_action_combo_box.currentText() == 'setAction':
            return clean_empty({'variableRef':self.variable_ref.text(), 
                    'setAction':self.variable_set_action.get_elements()})
        else:
            return clean_empty({'variableRef':self.variable_ref.text(), 
                    'modifyAction':self.variable_modify_action.get_elements()})
                
    def get_data(self):
        attrib = clean_empty({'variableRef':self.variable_ref.text()})
        if self.variable_action_combo_box.currentText() == 'setAction':
            return VariableAction(attrib,
                                   variable_set_action=self.variable_set_action.get_data(), 
                                   variable_modify_action=None)
        else:
            return VariableAction(attrib,
                                   variable_set_action=None,
                                   variable_modify_action=self.variable_modify_action.get_data())

class TrafficSignalStateListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.traffic_signal_state_widget_list = []
        self.initUI()
        
    def initUI(self):
        self.main_layout = QVBoxLayout()
        traffic_signal_state_widget = TrafficSignalStateWidget()
        self.main_layout.insertWidget(0, traffic_signal_state_widget)
        self.traffic_signal_state_widget_list.append(traffic_signal_state_widget)
        self.setLayout(self.main_layout)
    
    def add_tss_widget(self):
        new_tss_widget = TrafficSignalStateWidget()
        index = self.main_layout.count()
        self.main_layout.insertWidget(index, new_tss_widget)
        self.traffic_signal_state_widget_list.append(new_tss_widget)
    
    def delete_tss_widget(self):
        index = self.main_layout.count()-1
        if index < 1:
            pass
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.traffic_signal_state_widget_list.pop()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
    
    def get_elements(self):
        return [widget.get_elements() for widget in self.traffic_signal_state_widget_list]
    
    def get_data(self):
        return [widget.get_data() for widget in self.traffic_signal_state_widget_list]

class TrafficSignalStateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        self.state = QLineEdit()
        self.trafficSignalID = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('State:', self.state)
        form_layout.addRow('TrafficSignalId:', self.trafficSignalID)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'state':self.state.text(),'trafficSignalId':self.trafficSignalID.text()})
    
    def get_data(self):
        attrib = clean_empty({'trafficSignalId':self.trafficSignalID.text(), 'state':self.state.text()})
        return TrafficSignalState(attrib)

class PhaseListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase_widget_list = []
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        phase_widget = PhaseWidget()
        self.main_layout.insertWidget(0, phase_widget)
        self.phase_widget_list.append(phase_widget)
        self.button_layout = self.make_button_layout()
        self.main_layout.addLayout(self.button_layout, -1)
        self.setLayout(self.main_layout)

    def make_button_layout(self):
        grid_layout = QGridLayout()
        self.add_phase_btn = QPushButton("add phase")
        self.add_phase_btn.clicked.connect(self.add_phase_widget)
        self.delete_phase_btn = QPushButton("delete phase")
        self.delete_phase_btn.clicked.connect(self.delete_phase_widget)
        
        self.add_traffic_signal_state_btn = QPushButton("add traffic signal state")
        self.add_traffic_signal_state_btn.clicked.connect(self.add_traffic_signal_state)
        self.delete_traffic_signal_state_btn = QPushButton("delete traffic signal state")
        self.delete_traffic_signal_state_btn.clicked.connect(self.delete_traffic_signal_state)

        grid_layout.addWidget(self.add_traffic_signal_state_btn, 0, 0)
        grid_layout.addWidget(self.delete_traffic_signal_state_btn, 0, 1)
        grid_layout.addWidget(self.add_phase_btn, 1, 0)
        grid_layout.addWidget(self.delete_phase_btn, 1, 1)
        return grid_layout

    @pyqtSlot()
    def add_phase_widget(self):
        num_tss = len(self.phase_widget_list[0].traffic_signal_state_widget.traffic_signal_state_widget_list)
        new_phase_widget = PhaseWidget()
        index = self.main_layout.count()-1
        
        if num_tss > 1:
            for i in range(1, num_tss):
                new_phase_widget.traffic_signal_state_widget.add_tss_widget()
            self.main_layout.insertWidget(index, new_phase_widget)
            self.phase_widget_list.append(new_phase_widget)
        else:
            self.main_layout.insertWidget(index, new_phase_widget)
            self.phase_widget_list.append(new_phase_widget)

    @pyqtSlot()
    def delete_phase_widget(self):
        index = self.main_layout.count()-2
        if index < 1:
            QMessageBox.warning(self, 'Warning', 'Cannot delete the phase')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.phase_widget_list.pop()
    
    @pyqtSlot()
    def add_traffic_signal_state(self):
        if len(self.phase_widget_list) == 1:
            self.phase_widget_list[0].traffic_signal_state_widget.add_tss_widget()
        else:
            for widget in self.phase_widget_list:
                widget.traffic_signal_state_widget.add_tss_widget()
    
    @pyqtSlot()
    def delete_traffic_signal_state(self):
        num_tss = len(self.phase_widget_list[0].traffic_signal_state_widget.traffic_signal_state_widget_list)
        if num_tss <= 1:
            QMessageBox.warning(self, 'Warning', 'Cannot delete the traffic signal state')
        
        if len(self.phase_widget_list) == 1:
            self.phase_widget_list[0].traffic_signal_state_widget.delete_tss_widget()
        else:
            for widget in self.phase_widget_list:
                widget.traffic_signal_state_widget.delete_tss_widget()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None

    def get_elements(self):
        return [widget.get_elements() for widget in self.phase_widget_list]
    
    def get_data(self):
        return [widget.get_data() for widget in self.phase_widget_list]
            
class PhaseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        self.duration = QLineEdit()
        self.duration.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.name = QLineEdit()
        self.traffic_signal_state_widget = TrafficSignalStateListWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('Duration(s):', self.duration)
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('TrafficSignalState:', self.traffic_signal_state_widget)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'duration':self.duration.text(),'name':self.name.text(),
                            'trafficSignalState':self.traffic_signal_state_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'duration':self.duration.text(),'name':self.name.text()})
        return Phase(attrib, traffic_signal_states=self.traffic_signal_state_widget.get_data())

class TrafficSignalControllerActionWidget(QWidget):
    def __init__(self, parent=None, mgeo=None):
        super().__init__(parent)
        self.mgeo = mgeo
        self.phase = QLineEdit()
        self.phase.setToolTip('Targeted phase of the signal controller')

        intersection_controller_id_list = []
        if len(self.mgeo.intersection_controller_set.intersection_controllers) != 0:
            intersection_controller_id_list = self.mgeo.intersection_controller_set.intersection_controllers.keys()
        self.intersection_controller_id = QComboBox()
        self.intersection_controller_id.addItems(intersection_controller_id_list)
        self.intersection_controller_id.setToolTip('ID of the intersection controller in MGeo.')
        self.intersection_controller_id.activated[str].connect(self.update_intersection_controller_widget)
        
        information = QLabel()

        self.setting_intersection_schedule_widget = None
        if len(self.mgeo.intersection_controller_set.intersection_controllers) != 0:
            self.setting_intersection_schedule_widget = SettingIntersectionSchedule(self.mgeo, self.intersection_controller_id.currentText())
        form_layout = QFormLayout()
        form_layout.addRow('StartingPhase:',self.phase)
        form_layout.addRow('IntersectionControllerId:',self.intersection_controller_id)
        
        main_layout = QVBoxLayout()
        hbox = QHBoxLayout()
        if self.setting_intersection_schedule_widget is not None:
            hbox.addWidget(self.setting_intersection_schedule_widget)
            main_layout.addLayout(form_layout)
            main_layout.addLayout(hbox)
        else:
            information.setText('※ The intersection_controller data is empty')
            form_layout.addRow(information)
            main_layout.addLayout(form_layout)
        self.setLayout(main_layout)
    
    def update_intersection_controller_widget(self, choice):
        self.setting_intersection_schedule_widget.update_widget(choice)

    def get_elements(self):
        if self.intersection_controller_id.currentText()  != "":
            return clean_empty({'StartingPhase':self.phase.text(),'IntersectionControllerId':self.intersection_controller_id.currentText()})
        else:
            return None
    
    def get_data(self):
        if self.intersection_controller_id.currentText() != "":
            attrib = clean_empty({'phase':self.phase.text(),'trafficSignalControllerRef':self.intersection_controller_id.currentText()})
            data = self.setting_intersection_schedule_widget.get_data()
            return TrafficSignalAction(TrafficSignalControllerAction(attrib, phases=data), None)
        else:
            return TrafficSignalAction(None, None)

class TrafficSignalStateActionWidget(QWidget):
    def __init__(self, parent=None, mgeo=None):
        super().__init__(parent)
        self.mgeo = mgeo
        tl_list = list(self.mgeo.light_set.signals.keys())
        self.name = QComboBox()
        self.name.addItems(tl_list)
        self.state = QLineEdit()
        self.impulse_combo_box = QComboBox()
        self.impulse_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.impulse_combo_box.setToolTip('true: return to the phase cycle, false: keep the given signal state')
        self.setSibling_comb_box = QComboBox()
        self.setSibling_comb_box.addItems(BOOLEAN_TYPE_LIST)
        self.setSibling_comb_box.setToolTip('true: change all synced signals, false: change this signal only')
        form_layout = QFormLayout()
        form_layout.addRow('Name:',self.name)
        form_layout.addRow('State:',self.state)
        form_layout.addRow('Impulse:', self.impulse_combo_box)
        form_layout.addRow('setSibling', self.setSibling_comb_box)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'name':self.name.currentText(),
                'state':self.state.text(),
                'impulse':self.impulse_combo_box.currentText(),
                'setSibling':self.setSibling_comb_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.currentText(),'state':self.state.text(), 
                             'impulse':self.impulse_combo_box.currentText(),
                             'setSibling':self.setSibling_comb_box.currentText()})
        return TrafficSignalAction(None, TrafficSignalStateAction(attrib))

class InfrastructureActionWidget(QWidget):
    def __init__(self, parent=None, mgeo=None):
        super().__init__(parent)
        self.mgeo = mgeo
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_signal_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traffic_signal_action_info(self):
        groupbox = QGroupBox('TrafficSignalAction')
        traffic_signal_action_list = ['trafficSignalControllerAction','trafficSignalStateAction']
        self.traffic_signal_action_combo_box = QComboBox()
        self.traffic_signal_action_combo_box.addItems(traffic_signal_action_list)
        self.traffic_signal_action_combo_box.activated[str].connect(self.update_action)
        
        self.traffic_signal_action_widget = QStackedWidget()
        self.traffic_signal_controller_action_widget = TrafficSignalControllerActionWidget(mgeo=self.mgeo)
        self.traffic_signal_state_action_widget = TrafficSignalStateActionWidget(mgeo=self.mgeo)
        self.traffic_signal_action_widget.addWidget(self.traffic_signal_controller_action_widget)
        self.traffic_signal_action_widget.addWidget(self.traffic_signal_state_action_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.traffic_signal_action_combo_box)
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.traffic_signal_action_widget)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        groupbox.setLayout(vbox)
        return groupbox

    def update_action(self, choice):
        if choice == 'trafficSignalControllerAction':
            self.traffic_signal_action_widget.setCurrentWidget(self.traffic_signal_controller_action_widget)
        elif choice == 'trafficSignalStateAction':
            self.traffic_signal_action_widget.setCurrentWidget(self.traffic_signal_state_action_widget)
    
    def get_elements(self):
        if self.traffic_signal_action_combo_box.currentText() == 'trafficSignalControllerAction':
            return self.traffic_signal_controller_action_widget.get_elements()
        else:
            return self.traffic_signal_state_action_widget.get_elements()
    
    def get_data(self):
        if self.traffic_signal_action_combo_box.currentText() == 'trafficSignalControllerAction':
            return InfrastructureAction(action=self.traffic_signal_controller_action_widget.get_data())
        else:
            return InfrastructureAction(action=self.traffic_signal_state_action_widget.get_data())

class VehicleCategoryDistributionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.vehicle_category_distribution_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def vehicle_category_distribution_info(self):
        main_widget = QWidget()
        vehicle_category_list = [str(vehicle.name) for vehicle in VehicleCategory]
        self.category_combo_box = QComboBox()
        self.category_combo_box.addItems(vehicle_category_list)
        
        self.weight = QLineEdit()
        self.weight.setValidator(QDoubleValidator(bottom=0, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.weight.setPlaceholderText('Range [0..1]')

        self.model = QLineEdit()
        self.model.setPlaceholderText("If specified, 'Category' would be ignored.")
        
        form_layout = QFormLayout()
        form_layout.addRow('Model:',self.model)
        form_layout.addRow('Category:',self.category_combo_box)
        form_layout.addRow('Weight:',self.weight)
        main_widget.setLayout(form_layout)
        return main_widget

    def find_current_text(self):
        return self.category_combo_box.currentText()
    
    def get_elements(self):
        return clean_empty({'model':self.model.text(), 'category':self.find_current_text(),'weight':self.weight.text()})
    
    def get_data(self):
        ret_list = []
        attrib = clean_empty({'model':self.model.text(), 'category':self.find_current_text(), 'weight':self.weight.text()})
        ret_list.append(VehicleCategoryDistributionEntry(attrib))
        return ret_list

class ControllerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.controller_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def controller_info(self):
        main_widget = QWidget()
        self.name = QLineEdit()
        controller_type_list = [str(controller_type.name) for controller_type in ControllerType]
        controller_type_list.insert(0, "")
        self.controller_type_combo_box = QComboBox()
        self.controller_type_combo_box.addItems(controller_type_list)
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('ControllerType:', self.controller_type_combo_box)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 'controllerType':self.controller_type_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 'controllerType':self.controller_type_combo_box.currentText()})
        return Controller(attrib, None, Properties())
    
class ControllerDistributionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.controller_distribution_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def controller_distribution_info(self):
        main_widget = QWidget()
        self.weight = QLineEdit()
        self.weight.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.weight.setPlaceholderText('Range [0..inf]')
        self.controller = ControllerWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('Weight:',self.weight)
        form_layout.addRow('Controller:', self.controller)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'weight':self.weight.text(),'controller':self.controller.get_elements()})

    def get_data(self):
        ret_list = []
        attrib = clean_empty({'weight':self.weight.text()})
        ret_list.append(ControllerDistributionEntry(attrib, controller=self.controller.get_data()))
        return ret_list

class VehicleRoleDistributionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.vehicle_role_distribution_info(), 0, 0)
        self.setLayout(grid_layout)

    def vehicle_role_distribution_info(self):
        main_widget = QWidget()
        role_list = [str(role.name) for role in Role]
        self.role_combo_box = QComboBox()
        self.role_combo_box.addItems(role_list)
        self.weight = QLineEdit()
        self.weight.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.weight.setPlaceholderText('Range [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('Role:', self.role_combo_box)
        form_layout.addRow('Weight:', self.weight)
        main_widget.setLayout(form_layout)
    
    def get_elements(self):
        return {'role':self.role_combo_box.currentText(), 'weight':self.weight.text()}
    
    def get_data(self):
        attrib = {'role':self.role_combo_box.currentText(), 'weight':self.weight.text()}
        return VehicleRoleDistributionEntry(attrib)


class TrafficDefinitionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_definition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traffic_definition_info(self):
        main_widget = QWidget()
        self.name = QLineEdit()
        self.vehicle_category_distribution_widget = VehicleCategoryDistributionWidget()
        # Controller distribution is currently not supported
        # self.controller_distribution_widget = ControllerDistributionWidget()
        # self.vehicle_role_distribution_widget = VehicleRoleDistributionWidget()

        form_layout = QFormLayout()
        form_layout.addRow('Name:',self.name)
        form_layout.addRow('VehicleCategoryDistributionEntry:',self.vehicle_category_distribution_widget)
        # form_layout.addRow('ControllerDistributionEntry:',self.controller_distribution_widget)
        # form_layout.addRow('VehicleRoleDistributionEntry:', self.vehicle_role_distribution_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        # return clean_empty({'name':self.name.text(), 
        #         'vehicleCategoryDistributionEntry':self.vehicle_category_distribution_widget.get_elements(),
        #         'controllerDistributionEntry':self.controller_distribution_widget.get_elements(),
        #         'vehicleRoleDistributionEntry':self.vehicle_role_distribution_widget.get_elements()})
        return clean_empty({'name':self.name.text(), 
                'vehicleCategoryDistributionEntry':self.vehicle_category_distribution_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text()})
        # return TrafficDefinition(attrib, vehicle_distributions=self.vehicle_category_distribution_widget.get_data(),
        #                          vehicle_role_distributions=self.vehicle_role_distribution_widget.get_data(),
        #                          controller_distributions=self.controller_distribution_widget.get_data())
        return TrafficDefinition(attrib, vehicle_distributions=self.vehicle_category_distribution_widget.get_data())

class TrafficSourceActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_source_action_info(), 0, 0)
        self.set_default_speed_action_target_widget()
        self.setLayout(grid_layout)
        self.setFixedWidth(760)
    
    def traffic_source_action_info(self):
        main_widget = QWidget()
        self.radius = QLineEdit()

        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        self.radius.setValidator(nonnegative_validator)
        self.radius.setPlaceholderText('Range [0..inf]')
        self.rate = QLineEdit()
        self.rate.setValidator(nonnegative_validator)
        self.rate.setPlaceholderText('Range [0..inf]')
        self.rate.setToolTip('Rate on which vehicles appear at the source location (vehicles/s). It would be ignored when ‘Period’ is defined')
        self.count = QLineEdit()
        self.count.setValidator(QIntValidator(bottom=0))
        self.count.setPlaceholderText('Range [0..inf]')
        self.count.setToolTip('Maximum spawn vehicles (default: a million)')
        
        self.period = QLineEdit()
        self.period.setValidator(nonnegative_validator)
        self.period.setPlaceholderText('Range [0..inf]')
        self.period.setToolTip('Period on which vehicles appear at the source location (sec). (default: 1 sec)')
        self.periodRange = QLineEdit()
        self.periodRange.setValidator(nonnegative_validator)
        self.periodRange.setToolTip('Range of the period')
        self.periodRange.setPlaceholderText('Range [0..inf]')
        
        self.offset = QLineEdit()
        self.offset.setValidator(QDoubleValidator(bottom=-1, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.offset.setToolTip('Signed number the vehicle should respect as an offset from the center of the current lane. [-1..1]')
        self.offsetRange = QLineEdit()
        self.offsetRange.setValidator(QDoubleValidator(bottom=0, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.offsetRange.setToolTip('Range of the offset')
        
        self.closed_loop_combo_box = QComboBox()
        self.closed_loop_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.closed_loop_combo_box.setToolTip('True: spawned vehicles would come back to the spawn location. False: vehicles would be disappear at their target location.')
        
        self.discretionaryLaneChange_combo_box = QComboBox()
        self.discretionaryLaneChange_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.discretionaryLaneChange_combo_box.setToolTip('True: a spawned vehicle would change its lane randomly. False: the vehicle would keep its initial lane.')
         
        # self.velocity = QLineEdit()
        # self.velocity.setValidator(nonnegative_validator)
        # self.velocity.setPlaceholderText('Range [0..inf]')
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
                
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        # 지금은 Link Position 과 WorldPosition 만 보여줄수 있게끔 되어있다.
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        speed_action_target_list = ['relativeTargetSpeed', 'absoluteTargetSpeed']
        self.init_speed_combo_box = QComboBox()
        self.init_speed_combo_box.addItems(speed_action_target_list)
        self.init_speed_combo_box.activated[str].connect(self.update_init_target_speed)
        
        self.desired_speed_combo_box = QComboBox()
        self.desired_speed_combo_box.addItems(speed_action_target_list)
        self.desired_speed_combo_box.activated[str].connect(self.update_desired_target_speed)

        self.init_speed_layout = QVBoxLayout()
        self.init_relative_target_speed_widget = RelativeTargetSpeedWidget()
        self.init_absolute_target_speed_widget = AbsoluteTargetSpeedWidget()
        self.init_speed_layout.addWidget(self.init_relative_target_speed_widget)
        self.init_speed_layout.addWidget(self.init_absolute_target_speed_widget)
        
        self.desired_speed_layout = QVBoxLayout()
        self.desired_relative_target_speed_widget = RelativeTargetSpeedWidget()
        self.desired_absolute_target_speed_widget = AbsoluteTargetSpeedWidget()
        self.desired_speed_layout.addWidget(self.desired_relative_target_speed_widget)
        self.desired_speed_layout.addWidget(self.desired_absolute_target_speed_widget)
        
        self.waypoint = WaypointWidget()
        self.traffic_definition_widget = TrafficDefinitionWidget()
        
        vbox = QVBoxLayout()
        form_layout0 = QFormLayout()
        form_layout0.addRow('Radius (m):',self.radius)
        # form_layout0.addRow('Starting Velocity (m/s):',self.velocity)
        form_layout0.addRow('Number of Vehicles:', self.count)
        form_layout0.addRow('Rate (vehicles/s):',self.rate)
        form_layout0.addRow('Period (s):', self.period)
        form_layout0.addRow('Period Range:', self.periodRange)
        form_layout0.addRow('Lane Offset:', self.offset)
        form_layout0.addRow('Lane Offset Range:', self.offsetRange)
        form_layout0.addRow('Closed Loop:', self.closed_loop_combo_box)
        form_layout0.addRow('Discretionary Lane Change:', self.discretionaryLaneChange_combo_box)
        form_layout0.addRow('Position:', self.position_type_combo_box)
        form_layout0.addWidget(self.position_widget)
        vbox.addLayout(form_layout0)
        
        form_layout1 = QFormLayout()
        form_layout1.addRow('InitSpeed:', self.init_speed_combo_box)
        vbox.addLayout(form_layout1)
        vbox.addLayout(self.init_speed_layout)
        
        #form_layout.addRow(self.init_speed_layout)
        form_layout2 = QFormLayout()
        form_layout2.addRow('DesiredSpeed:', self.desired_speed_combo_box)
        vbox.addLayout(form_layout2)
        vbox.addLayout(self.desired_speed_layout)

        form_layout3 = QFormLayout()
        form_layout3.addRow('Waypoint:', self.waypoint)
        form_layout3.addRow('TrafficDefinition:', self.traffic_definition_widget)
        vbox.addLayout(form_layout3)
        main_widget.setLayout(vbox)
        return main_widget
        
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)

    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
        
    def update_init_target_speed(self, choice):
        self.hide_init_speed_action_target_widget()
        if choice == 'relativeTargetSpeed':
            self.init_relative_target_speed_widget.setVisible(True)
        elif choice == 'absoluteTargetSpeed': #absoluteTargetSpeed
            self.init_absolute_target_speed_widget.setVisible(True)
        else:
            self.hide_init_speed_action_target_widget()
    
    def update_desired_target_speed(self, choice):
        self.hide_desired_speed_action_target_widget()
        if choice == 'relativeTargetSpeed':
            self.desired_relative_target_speed_widget.setVisible(True)
        elif choice == 'absoluteTargetSpeed': #absoluteTargetSpeed
            self.desired_absolute_target_speed_widget.setVisible(True)
        else:
            self.hide_desired_speed_action_target_widget()
    
    def set_default_speed_action_target_widget(self):
        self.hide_all_speed_action_target_widgets()
        self.init_relative_target_speed_widget.setVisible(True)
        self.desired_relative_target_speed_widget.setVisible(True)
    
    def hide_init_speed_action_target_widget(self):
        for i in range(self.init_speed_layout.count()):
            self.init_speed_layout.itemAt(i).widget().setVisible(False)
    
    def hide_desired_speed_action_target_widget(self):
        for i in range(self.desired_speed_layout.count()):
            self.desired_speed_layout.itemAt(i).widget().setVisible(False)
    
    # ERROR HANDLING
    def hide_all_speed_action_target_widgets(self):
        for i in range(self.init_speed_layout.count()):
            self.init_speed_layout.itemAt(i).widget().setVisible(False)
        
        for i in range(self.desired_speed_layout.count()):
            self.desired_speed_layout.itemAt(i).widget().setVisible(False)
    
    def get_init_speed_target_elements(self):
        if self.init_speed_combo_box.currentText() == 'relativeTargetSpeed':
            return self.init_relative_target_speed_widget.get_elements()
        else:
            return self.init_absolute_target_speed_widget.get_elements()
    
    def get_desired_speed_target_elements(self):
        if self.desired_speed_combo_box.currentText() == 'relativeTargetSpeed':
            return self.desired_relative_target_speed_widget.get_elements()
        else:
            return self.desired_absolute_target_speed_widget.get_elements()
    
    def get_init_speed_target_data(self):
        if self.init_speed_combo_box.currentText() == 'relativeTargetSpeed':
            return SpeedActionTarget(speed_type=self.init_relative_target_speed_widget.get_data())
        else:
            return SpeedActionTarget(speed_type=self.init_absolute_target_speed_widget.get_data())
    
    def get_desired_speed_target_data(self):
        if self.desired_speed_combo_box.currentText() == 'relativeTargetSpeed':
            return SpeedActionTarget(speed_type=self.desired_relative_target_speed_widget.get_data())
        else:
            return SpeedActionTarget(speed_type=self.desired_absolute_target_speed_widget.get_data())
    
    def get_elements(self):
        return clean_empty({'radius':self.radius.text(), 'velocity': self.velocity.text(), 'count': self.count.text(),
                            'rate': self.rate.text(), 'period': self.period.text(), 'periodRange': self.periodRange.text(),
                            'offset': self.offset.text(), 'offsetRange': self.offsetRange.text(), 
                            'closedLoop': self.closed_loop_combo_box.currentText(),
                            'discretionaryLaneChange': self.discretionaryLaneChange_combo_box.currentText(),
                            'position':self.get_position_elements(), 
                            'initSpeed':{'type':self.init_speed_combo_box.currentText(), 'value':self.get_init_speed_target_elements()},
                            'desiredSpeed':{'type':self.desired_speed_combo_box.currentText(), 'value':self.get_desired_speed_target_elements()}, 
                            'waypoint':self.waypoint.get_elements(),
                            'trafficDefinition':self.traffic_definition_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'radius':self.radius.text(), 'velocity':'', 'count': self.count.text(),
                              'rate': self.rate.text(), 'period': self.period.text(), 'periodRange': self.periodRange.text(),
                              'offset': self.offset.text(), 'offsetRange': self.offsetRange.text(), 
                              'closedLoop': self.closed_loop_combo_box.currentText(),
                              'discretionaryLaneChange': self.discretionaryLaneChange_combo_box.currentText()})
        
        return TrafficSourceAction(attrib, position=self.get_position_data(), init_speed=self.get_init_speed_target_data(),
                                   desired_speed=self.get_desired_speed_target_data(), waypoint=self.waypoint.get_data(),
                                   traffic_definition=self.traffic_definition_widget.get_data())

class PedestrianSourceActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.pedestrian_source_action_info(), 0, 0)
        self.setLayout(grid_layout)
        self.setFixedWidth(760)
    
    def pedestrian_source_action_info(self):
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        main_widget = QWidget()
        self.radius = QLineEdit()
        self.radius.setValidator(nonnegative_validator)
        self.radius.setPlaceholderText('Range [0..inf]')
        self.radius.setToolTip('Radius of spawn area')
        self.count = QLineEdit()
        self.count.setValidator(QIntValidator(bottom=0))
        self.count.setPlaceholderText('Range [0..inf]')
        self.count.setToolTip('Maximum spawn pedestrians (default: a million)')
        self.period = QLineEdit()
        self.period.setValidator(nonnegative_validator)
        self.period.setPlaceholderText('Range [0...inf]')
        self.period.setToolTip('Period on which pedestrians appear at the source location (sec). (default: 1 sec)')
        
        mode_list = ['once', 'closedLoop', 'repeat', 'loop', 'newPath', 'stand']
        self.mode_combo_box = QComboBox()
        self.mode_combo_box.addItems(mode_list)
        pedestrian_type = ['random', 'man1_ai', 'man2_ai', 'man3_ai', 'man5_ai', 'man6_ai', 'man7_ai', 'man8_ai', 'woman4_ai',
                   'woman5_ai', 'woman6_ai']
        self.pedestrian_type_combo_box = QComboBox()
        self.pedestrian_type_combo_box.addItems(pedestrian_type)
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
                
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        # 지금은 Link Position 과 WorldPosition 만 보여줄수 있게끔 되어있다.
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        self.waypoint = WaypointWidget()

        vbox = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.addRow('Radius(m):', self.radius)
        form_layout.addRow('Count:', self.count)
        form_layout.addRow('Period(s):', self.period)
        form_layout.addRow('Mode:', self.mode_combo_box)
        form_layout.addRow('PedestrianType:', self.pedestrian_type_combo_box)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        vbox.addLayout(form_layout)
        
        form_layout1 = QFormLayout()
        form_layout1.addRow('Waypoint:', self.waypoint)
        vbox.addLayout(form_layout1)
        main_widget.setLayout(vbox)
        return main_widget
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)

    def get_elements(self):
        return clean_empty({'radius':self.radius.text(),'count':self.count.text(),'period':self.period.text(),
                            'mode':self.mode_combo_box.currentText(), 
                            'pedestrianType':self.pedestrian_type_combo_box.currentText(),
                            'position':self.get_position_elements(),
                            'waypoint':self.waypoint.get_elements()
                            })
    
    def get_data(self):
        attrib = clean_empty({'radius':self.radius.text(), 'count':self.count.text(), 'period':self.period.text(),
                             'mode':self.mode_combo_box.currentText(), 
                             'pedestrianType': self.pedestrian_type_combo_box.currentText()})
        return PedestrianSourceAction(attrib, position=self.get_position_data(),
                                      waypoint=self.waypoint.get_data())
    
class TrafficSinkActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_sink_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traffic_sink_action_info(self):
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        main_widget = QWidget()
        self.radius = QLineEdit()
        self.radius.setValidator(nonnegative_validator)
        self.rate = QLineEdit()
        self.rate.setValidator(nonnegative_validator)
        self.rate.setPlaceholderText('Range [0..inf]')
        self.rate.setToolTip('If omitted, rate is interpreted as "inf"')
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        self.traffic_definition_widget = TrafficDefinitionWidget()
        form_layout = QFormLayout()
        form_layout.addRow('Radius(m):',self.radius)
        form_layout.addRow('Rate(vehicles/s):',self.rate)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        form_layout.addRow('TrafficDefinition:',self.traffic_definition_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
    
    def get_elements(self):
        return clean_empty({'radius':self.radius.text(),
                            'rate':self.rate.text(),
                            'position':self.get_position_elements(),
                            'trafficDefinition':self.traffic_definition_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'radius':self.radius.text(),'rate':self.rate.text()})
        return TrafficSinkAction(attrib, 
                                 position=self.get_position_data(), 
                                 traffic_definition=self.traffic_definition_widget.get_data())

class CentralSwarmObjectWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entityRef = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('EntityRef:', self.entityRef)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'entityRef':self.entityRef.text()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entityRef.text()})
        return CentralSwarmObject(attrib)

class RangeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.range_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def range_info(self):
        main_widget = QWidget()
        default_double_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.lower_limit = QLineEdit()
        self.lower_limit.setValidator(default_double_validator)
        self.lower_limit.setPlaceholderText('Range [-inf..inf]')
        self.upper_limit = QLineEdit()
        self.upper_limit.setValidator(default_double_validator)
        self.upper_limit.setPlaceholderText('Range [-inf..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('LowerLimit:', self.lower_limit)
        form_layout.addRow('UpperLimit:', self.upper_limit)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return {'lowerLimit':self.lower_limit.text(), 'upperLimit':self.upper_limit.text()}
    
    def get_data(self):
        attrib = {'lowerLimit':self.lower_limit.text(), 'upperLimit':self.upper_limit.text()}
        return Range(attrib)

class DirectionOfTravelDistributionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.direction_of_travel_distribution_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def direction_of_travel_distribution_info(self):
        main_widget = QWidget()
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        self.opposite = QLineEdit()
        self.opposite.setValidator(nonnegative_validator)
        self.opposite.setPlaceholderText('Range [0..inf]')
        self.same = QLineEdit()
        self.same.setValidator(nonnegative_validator)
        self.same.setPlaceholderText('Range [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('Opposite:', self.opposite)
        form_layout.addRow('Same:', self.same)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return {'opposite':self.opposite.text(), 'same':self.same.text()}
    
    def get_data(self):
        attrib = {'opposite':self.opposite.text(), 'same':self.same.text()}
        return DirectionOfTravelDistribution(attrib)

class TrafficSwarmActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_swarm_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traffic_swarm_action_info(self):
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        main_widget = QWidget()
        self.innerRadius = QLineEdit()
        self.innerRadius.setValidator(nonnegative_validator)
        self.innerRadius.setPlaceholderText('Range [0..inf]')
        self.innerRadius.setToolTip('Radius of the inner circular area around central entity')
        self.numberOfVehicles = QLineEdit()
        self.numberOfVehicles.setValidator(nonnegative_validator)
        self.numberOfVehicles.setPlaceholderText('Range [0..inf]')
        self.numberOfVehicles.setToolTip('The maximum number of vehicles')
        self.offset = QLineEdit()
        self.offset.setValidator(nonnegative_validator)
        self.offset.setPlaceholderText('Range [0..inf]')
        self.offset.setToolTip('Offset in longitudinal direction related to the x-axis of the central entity')
        self.semiMajorAxis = QLineEdit()
        self.semiMajorAxis.setValidator(nonnegative_validator)
        self.semiMajorAxis.setPlaceholderText('Range [0..inf]')
        self.semiMajorAxis.setToolTip('Shape of the swarm traffic distribution area is given as an ellipsis around a central entity')
        self.semiMinorAxis = QLineEdit()
        self.semiMinorAxis.setValidator(nonnegative_validator)
        self.semiMinorAxis.setPlaceholderText('Range [0..inf]')
        self.central_swarm_object_widget = CentralSwarmObjectWidget()
        self.traffic_definition_widget = TrafficDefinitionWidget()
        self.range_widget = RangeWidget()
        self.direction_of_travel_distribution_widget = DirectionOfTravelDistributionWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('InnerRadius(m):', self.innerRadius)
        form_layout.addRow('NumberOfVehicles:', self.numberOfVehicles)
        form_layout.addRow('Offset(m):', self.offset)
        form_layout.addRow('SemiMajorAxis(m):', self.semiMajorAxis)
        form_layout.addRow('SemiMinorAxis(m):', self.semiMinorAxis)
        form_layout.addRow('InitialSpeedRange(m/s):', self.range_widget)
        form_layout.addRow(self.central_swarm_object_widget)
        form_layout.addRow('TrafficDefinition:', self.traffic_definition_widget)
        form_layout.addRow('DirectionOfTravelDistribution:', self.direction_of_travel_distribution_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'innerRadius':self.innerRadius.text(),
                            'numberOfVehicles':self.numberOfVehicles.text(),
                            'offset':self.offset.text(),
                            'semiMajorAxis':self.semiMajorAxis.text(),
                            'semiMinorAxis':self.semiMinorAxis.text(),
                            'centralObject':self.central_swarm_object_widget.get_elements(),
                            'trafficDefinition':self.traffic_definition_widget.get_elements(),
                            'initialSpeedRange':self.range_widget.get_elements(),
                            'directionOfTravelDistribution':self.direction_of_travel_distribution_widget.get_elements()
                            })
    
    def get_data(self):
        attrib = clean_empty({'innerRadius': self.innerRadius.text(),
                              'numberOfVehicles': self.numberOfVehicles.text(),
                              'offset':self.offset.text(), 
                              'semiMajorAxis':self.semiMajorAxis.text(), 
                              'semiMinorAxis':self.semiMinorAxis.text()})
        return TrafficSwarmAction(attrib, 
                                  central_object=self.central_swarm_object_widget.get_data(),
                                  traffic_definition=self.traffic_definition_widget.get_data(),
                                  initialSpeedRange=self.range_widget.get_data(),
                                  directionOfTravelDistribution=self.direction_of_travel_distribution_widget.get_data()
                                  )

class TrafficActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_action_info(), 0, 0)
        self.set_default_traffic_action_widget()
        self.setLayout(grid_layout)
    
    def traffic_action_info(self):
        main_widget = QWidget()
        self.traffic_name = QLineEdit()
        traffic_action_list = ['trafficSourceAction','trafficSinkAction','trafficSwarmAction','trafficStopAction', 'pedestrianSourceAction']
        self.traffic_action_combo_box = QComboBox()
        self.traffic_action_combo_box.addItems(traffic_action_list)
        self.traffic_action_combo_box.activated[str].connect(self.update_action)
        
        self.traffic_action_layout = QVBoxLayout()
        self.traffic_source_action_widget = TrafficSourceActionWidget()
        self.traffic_sink_action_widget = TrafficSinkActionWidget()
        self.traffic_swarm_action_widget = TrafficSwarmActionWidget()
        self.pedestrian_source_action_widget = PedestrianSourceActionWidget()
        self.traffic_action_layout.addWidget(self.traffic_source_action_widget)
        self.traffic_action_layout.addWidget(self.traffic_sink_action_widget)
        self.traffic_action_layout.addWidget(self.traffic_swarm_action_widget)
        self.traffic_action_layout.addWidget(self.pedestrian_source_action_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('TrafficName:',self.traffic_name)
        form_layout.addRow('TrafficAction:',self.traffic_action_combo_box)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(self.traffic_action_layout)
        vbox.addStretch()
        main_widget.setLayout(vbox)
        return main_widget

    def update_action(self, choice):
        self.hide_all_traffic_action_widgets()
        if choice == 'trafficSourceAction':
            self.traffic_source_action_widget.setVisible(True)
        elif choice == 'trafficSinkAction':
            self.traffic_sink_action_widget.setVisible(True)
        elif choice == 'trafficSwarmAction':
            self.traffic_swarm_action_widget.setVisible(True)
        elif choice == 'pedestrianSourceAction':
            self.pedestrian_source_action_widget.setVisible(True)
        else:
            self.hide_all_traffic_action_widgets()

    def set_default_traffic_action_widget(self):
        self.hide_all_traffic_action_widgets()
        self.traffic_source_action_widget.setVisible(True)
    
    def hide_all_traffic_action_widgets(self):
        for i in range(self.traffic_action_layout.count()):
            self.traffic_action_layout.itemAt(i).widget().setVisible(False)
    
    def get_elements(self):
        if self.traffic_action_combo_box.currentText() == 'trafficSourceAction':
            return clean_empty({'name':self.traffic_name, 'value':self.traffic_source_action_widget.get_elements()})
        elif self.traffic_action_combo_box.currentText() == 'trafficSinkAction':
            return clean_empty({'name':self.traffic_name, 'value':self.traffic_sink_action_widget.get_elements()})
        elif self.traffic_action_combo_box.currentText() == 'trafficSwarmAction':
            return clean_empty({'name':self.traffic_name, 'value':self.traffic_swarm_action_widget.get_elements()})
        elif self.traffic_action_combo_box.currentText() == 'pedestrianSourceAction':
            return clean_empty({'name':self.traffic_name, 'value':self.pedestrian_source_action_widget.get_elements()})
        elif self.traffic_action_combo_box.currentText() == 'trafficStopAction':
            return {}
    
    def get_current_visible_action_widget(self):
        for i in range(self.traffic_action_layout.count()):
            widget = self.traffic_action_layout.itemAt(i).widget()
            if isVisibleWidget(widget):
                return widget
    
    def get_data(self):
        attrib = clean_empty({'trafficName':self.traffic_name.text()})
        if self.traffic_action_combo_box.currentText() == 'trafficSourceAction':
            return TrafficAction(attrib, action=self.traffic_source_action_widget.get_data())
        elif self.traffic_action_combo_box.currentText() == 'trafficSinkAction':
            return TrafficAction(attrib, action=self.traffic_sink_action_widget.get_data())
        elif self.traffic_action_combo_box.currentText() == 'trafficSwarmAction':
            return TrafficAction(attrib, action=self.traffic_swarm_action_widget.get_data())
        elif self.traffic_action_combo_box.currentText() == 'pedestrianSourceAction':
            return TrafficAction(attrib, self.pedestrian_source_action_widget.get_data())
        elif self.traffic_action_combo_box.currentText() == 'trafficStopAction':
            return TrafficAction(attrib, action=TrafficStopAction())

class TransitionDynamicsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.transition_dynamic_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def transition_dynamic_info(self):
        main_widget = QWidget()
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        self.value.setToolTip('Rate(Unit: delta/s), Time(Unit: s), Distance(Unit:m)')
        dynamic_dimension_list = [str(dimension.name) for dimension in DynamicsDimension]
        dynamic_shape_list = [str(shape.name) for shape in DynamicsShape]
        self.dynamics_dimension_combo_box = QComboBox()
        self.dynamics_dimension_combo_box.addItems(dynamic_dimension_list)
        self.dynamics_shape_combo_box = QComboBox()
        self.dynamics_shape_combo_box.addItems(dynamic_shape_list)
        
        form_layout = QFormLayout()
        form_layout.addRow('DynamicsDimension:', self.dynamics_dimension_combo_box)
        form_layout.addRow('DynamicsShape:', self.dynamics_shape_combo_box)
        form_layout.addRow('Value:', self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'dynamicsDimension': self.dynamics_dimension_combo_box.currentText(), 
                            'dynamicsShape':self.dynamics_shape_combo_box.currentText(),
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'dynamicsDimension': self.dynamics_dimension_combo_box.currentText(), 
                              'dynamicsShape':self.dynamics_shape_combo_box.currentText(),
                              'value':self.value.text()})
        return TransitionDynamics(attrib)
    
class RelativeTargetSpeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_target_speed_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def relative_target_speed_info(self):
        main_widget = QWidget()
        self.continuous_combo_box = QComboBox()
        self.continuous_combo_box.addItems(BOOLEAN_TYPE_LIST)
        speed_target_value_type_list = [str(val_type.name) for val_type in SpeedTargetValueType]
        self.speed_target_value_type_combo_box = QComboBox()
        self.speed_target_value_type_combo_box.addItems(speed_target_value_type_list)
        self.entity_ref = QLineEdit()
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        self.value.setToolTip('This value is either given as a delta or as a factor')
        type_list = [str(val_type.name) for val_type in VelocityType]
        self.type_combo_box = QComboBox()
        self.type_combo_box.addItems(type_list)
        self.type_combo_box.activated[str].connect(self.update_type)
        self.range = QLineEdit()
        self.range.setToolTip('Range of the Speed - link_type: [0..1] or custom_type: [0..inf]')
        self.range.setPlaceholderText('Range [0..1]')
        form_layout = QFormLayout()
        form_layout.addRow('Continuous:',  self.continuous_combo_box)
        form_layout.addRow('EntityRef:', self.entity_ref)
        form_layout.addRow('SpeedTargetValueType:', self.speed_target_value_type_combo_box)
        form_layout.addRow('Value(m/s):', self.value)
        form_layout.addRow('Type:', self.type_combo_box)
        form_layout.addRow('Range:', self.range)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def update_type(self, text):
        if text == 'link':
            self.range.setPlaceholderText('Range [0..1]')
        else:
            self.range.setPlaceholderText('Range [0..inf]')
    
    def get_elements(self):
        return clean_empty({'continuous':self.continuous_combo_box.currentText(), 
                            'entityRef':self.entity_ref.text(),
                            'speedTargetValueType':self.speed_target_value_type_combo_box.currentText(), 
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'continuous':self.continuous_combo_box.currentText(), 
                              'entityRef':self.entity_ref.text(),
                              'speedTargetValueType':self.speed_target_value_type_combo_box.currentText(), 
                              'value':self.value.text(),
                              'type':self.type_combo_box.currentText(),
                              'range':self.range.text()})
        return RelativeTargetSpeed(attrib)
    
class AbsoluteTargetSpeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.absolute_target_speed_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def absolute_target_speed_info(self):
        main_widget = QWidget()
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        type_list = [str(val_type.name) for val_type in VelocityType]
        self.type_combo_box = QComboBox()
        self.type_combo_box.addItems(type_list)
        self.type_combo_box.activated[str].connect(self.update_type)
        self.range = QLineEdit()
        self.range.setPlaceholderText('Range [0..1]')
        self.range.setToolTip('Range of the Speed - link_type: [0..1] or custom_type: [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('Value(m/s):', self.value)
        form_layout.addRow('Type:', self.type_combo_box)
        form_layout.addRow('Range:', self.range)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def update_type(self, text):
        if text == 'link':
            self.range.setPlaceholderText('Range [0..1]')
        else:
            self.range.setPlaceholderText('Range [0..inf]')
    
    def get_elements(self):
        return clean_empty({'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text(),
                              'type':self.type_combo_box.currentText(),
                              'range':self.range.text()})
        return AbsoluteTargetSpeed(attrib)
    
class SpeedActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.speed_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def speed_action_info(self):
        groupbox = QGroupBox('SpeedAction')
        self.speed_action_dynamics_widget = TransitionDynamicsWidget()
        speed_action_target_list = ['relativeTargetSpeed', 'absoluteTargetSpeed']
        self.speed_action_target_combo_box = QComboBox()
        self.speed_action_target_combo_box.addItems(speed_action_target_list)
        self.speed_action_target_combo_box.activated[str].connect(self.update_target_speed)
        
        self.speed_action_target_widget = QStackedWidget()
        self.relative_target_speed_widget = RelativeTargetSpeedWidget()
        self.absolute_target_speed_widget = AbsoluteTargetSpeedWidget()
        self.speed_action_target_widget.addWidget(self.relative_target_speed_widget)
        self.speed_action_target_widget.addWidget(self.absolute_target_speed_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('SpeedActionDynamics:', self.speed_action_dynamics_widget)
        form_layout.addRow('SpeedActionTarget:',self.speed_action_target_combo_box)
        form_layout.addWidget(self.speed_action_target_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_speed_target_elements(self):
        if self.speed_action_target_combo_box.currentText() == 'relativeTargetSpeed':
            return self.relative_target_speed_widget.get_elements()
        else:
            return self.absolute_target_speed_widget.get_elements()
    
    def get_speed_target_data(self):
        if self.speed_action_target_combo_box.currentText() == 'relativeTargetSpeed':
            return SpeedActionTarget(speed_type=self.relative_target_speed_widget.get_data())
        else:
            return SpeedActionTarget(speed_type=self.absolute_target_speed_widget.get_data())
    
    def update_target_speed(self, choice):
        if choice == 'relativeTargetSpeed':
            self.speed_action_target_widget.setCurrentWidget(self.relative_target_speed_widget)
        else: #absoluteTargetSpeed
            self.speed_action_target_widget.setCurrentWidget(self.absolute_target_speed_widget)
    
    def get_elements(self):
        return clean_empty({'speedActionTarget':self.get_speed_target_elements(), 
                            'transitionDynamics':self.speed_action_dynamics_widget.get_elements()})
    
    def get_data(self):
        return SpeedAction(target=self.get_speed_target_data(),
                           transition_dynamics=self.speed_action_dynamics_widget.get_data())

class DynamicConstraintsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.dynamic_constraints_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def dynamic_constraints_info(self):
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        main_widget = QWidget()
        self.maxAcceleration = QLineEdit()
        self.maxAcceleration.setValidator(nonnegative_validator)
        self.maxAcceleration.setPlaceholderText('Range [0..inf]')
        self.maxAcceleration.setToolTip('Maximum acceleration the distance controller is allowed to use for keeping the distance')
        self.maxAccelerationRate = QLineEdit()
        self.maxAccelerationRate.setValidator(nonnegative_validator)
        self.maxAccelerationRate.setPlaceholderText('Range [0..inf]')
        self.maxAccelerationRate.setToolTip('Maximum acceleration rate the distance controller is allowed to use for keeping the distance')
        self.maxDeceleration = QLineEdit()
        self.maxDeceleration.setValidator(nonnegative_validator)
        self.maxDeceleration.setPlaceholderText('Range [0..inf]')
        self.maxAcceleration.setToolTip('Maximum deceleration the distance controller is allowed to use for keeping the distance')
        self.maxDecelerationRate = QLineEdit()
        self.maxDecelerationRate.setValidator(nonnegative_validator)
        self.maxDecelerationRate.setPlaceholderText('Range [0..inf]')
        self.maxDecelerationRate.setToolTip('Maximum deceleration the distance controller is allowed to use for keeping the distance')
        self.maxSpeed = QLineEdit()
        self.maxSpeed.setValidator(nonnegative_validator)
        self.maxSpeed.setPlaceholderText('Range [0..inf]')
        
        form_layout = QFormLayout()
        form_layout.addRow('MaxAcceleration(m/s\u00b2):', self.maxAcceleration)
        form_layout.addRow('MaxAccelerationRate(m/s\u00b2):', self.maxAccelerationRate)
        form_layout.addRow('MaxDeceleration(m/s\u00b2):', self.maxDeceleration)
        form_layout.addRow('MaxDecelerationRate(m/s\u00b2):', self.maxDecelerationRate)
        form_layout.addRow('MaxSpeed(m/s):', self.maxSpeed)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'maxAcceleration':self.maxAcceleration.text(),
                            'maxAccelerationRate':self.maxAccelerationRate.text(),
                            'maxDeceleration':self.maxDeceleration.text(),
                            'maxDecelerationRate':self.maxDecelerationRate.text(),
                            'maxSpeed':self.maxSpeed.text()})
    
    def get_data(self):
        attrib = clean_empty({'maxAcceleration':self.maxAcceleration.text(),
                              'maxAccelerationRate':self.maxAccelerationRate.text(),
                              'maxDeceleration':self.maxDeceleration.text(),
                              'maxDecelerationRate':self.maxDecelerationRate.text(),
                              'maxSpeed':self.maxSpeed.text()})
        return DynamicConstraints(attrib)

class LongitudinalDistanceActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.longitudinaldistance_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def longitudinaldistance_action_info(self):
        groupbox = QGroupBox('LongitudinalDistanceAction')
        self.continuous_combo_box = QComboBox()
        self.continuous_combo_box.addItems(BOOLEAN_TYPE_LIST)
        coordinate_system_list = [str(coordinate.name) for coordinate in CoordinateSystem]
        self.coordinate_system_combo_box = QComboBox()
        self.coordinate_system_combo_box.addItems(coordinate_system_list)
        longitudinal_displacement_list = ['any','trailingReferencedEntity','leadingReferencedEntity']	
        self.longitudinal_displacement_combo_box = QComboBox()
        self.longitudinal_displacement_combo_box.addItems(longitudinal_displacement_list)

        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        self.distance = QLineEdit()
        self.distance.textChanged[str].connect(self.disable_time_gap_line)
        self.distance.setValidator(nonnegative_validator)
        self.distance.setPlaceholderText('Range [0..inf]')
        self.entity_ref = QLineEdit()
        
        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.freespace_combo_box.setToolTip('True: Distance is measured using the distance between closest bounding box points False False: Reference point distance is used')
        self.timegap = QLineEdit()
        self.timegap.textChanged[str].connect(self.disable_distance_line)
        self.timegap.setValidator(nonnegative_validator)
        self.timegap.setPlaceholderText('Range [0..inf]')
        self.dynamic_constraints = DynamicConstraintsWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('Continuous:', self.continuous_combo_box)
        form_layout.addRow('CoordinateSystem:', self.coordinate_system_combo_box)
        form_layout.addRow('Displacement:', self.longitudinal_displacement_combo_box)
        form_layout.addRow('Distance(m):', self.distance)
        form_layout.addRow('EntityRef:', self.entity_ref)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('TimeGap(s):', self.timegap)
        form_layout.addRow('DynamicConstraints:', self.dynamic_constraints)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def disable_time_gap_line(self, text):
        if text == '':
            self.timegap.setDisabled(False)
        else:
            self.timegap.setDisabled(True)
            
    def disable_distance_line(self, text):
        if text == '':
            self.distance.setDisabled(False)
        else:
            self.distance.setDisabled(True)
    
    def get_elements(self):
        if self.distance.isEnabled():
            return clean_empty({'continuous':self.continuous_combo_box.currentText(),
                                'entityRef':self.entity_ref.text(),
                                'freespace':self.freespace_combo_box.currentText(),
                                'distance':self.distance.text(),
                                'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                                'displacement':self.longitudinal_displacement_combo_box.currentText(),
                                'dynamicConstraints':self.dynamic_constraints.get_elements()})
        else:
            return clean_empty({'continuous':self.continuous_combo_box.currentText(),
                                'entityRef':self.entity_ref.text(),
                                'freespace':self.freespace_combo_box.currentText(),
                                'timeGap':self.timegap.text(),
                                'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                                'displacement':self.longitudinal_displacement_combo_box.currentText(),
                                'dynamicConstraints':self.dynamic_constraints.get_elements()})
    
    def get_data(self):
        if self.distance.isEnabled():
            attrib = clean_empty({'continuous':self.continuous_combo_box.currentText(),
                                'entityRef':self.entity_ref.text(),
                                'freespace':self.freespace_combo_box.currentText(),
                                'distance':self.distance.text(),
                                'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                                'displacement':self.longitudinal_displacement_combo_box.currentText()})
            return LongitudinalDistanceAction(attrib, dynamic_constraint=self.dynamic_constraints.get_data())
        else:
            attrib = clean_empty({'continuous':self.continuous_combo_box.currentText(),
                                'entityRef':self.entity_ref.text(),
                                'freespace':self.freespace_combo_box.currentText(),
                                'timeGap':self.timegap.text(),
                                'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                                'displacement':self.longitudinal_displacement_combo_box.currentText()})
            return LongitudinalDistanceAction(attrib, dynamic_constraint=self.dynamic_constraints.get_data())

class SpeedProfileEntryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        self.speed = QLineEdit()
        self.speed.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.speed.setPlaceholderText('Range [-inf..inf]')
        self.time = QLineEdit()
        self.time.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.time.setPlaceholderText('Range [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('Speed(m/s):', self.speed)
        form_layout.addRow('Time(s):', self.time)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'speed':self.speed.text(), 'time':self.time.text()})
    
    def get_data(self):
        attrib = clean_empty({'speed':self.speed.text(), 'time':self.time.text()})
        return SpeedProfileEntry(attrib)

class SpeedProfileEntriesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.speed_profile_entries = []
        self.initUI()
        
    def initUI(self):
        self.main_layout = QVBoxLayout()
        speed_profile_entry_widget = SpeedProfileEntryWidget()
        self.main_layout.insertWidget(0, speed_profile_entry_widget)
        self.speed_profile_entries.append(speed_profile_entry_widget)
        self.button_layout = self.make_button_layout()
        self.main_layout.addLayout(self.button_layout, -1)
        self.setLayout(self.main_layout)
        
    def make_button_layout(self):
        grid_layout = QGridLayout()
        self.add_entity_ref_btn = QPushButton("add speed profile entry")
        self.add_entity_ref_btn.clicked.connect(self.add_speed_profile_entry_widget)
        self.delete_entity_ref_btn = QPushButton('delete speed profile entry')
        self.delete_entity_ref_btn.clicked.connect(self.delete_speed_profile_entry_widget)
        grid_layout.addWidget(self.add_entity_ref_btn, 0, 0)
        grid_layout.addWidget(self.delete_entity_ref_btn, 0, 1)
        return grid_layout
    
    @pyqtSlot()
    def add_speed_profile_entry_widget(self):
        new_entity_ref_widget = SpeedProfileEntryWidget()
        index = self.main_layout.count() - 1
        self.main_layout.insertWidget(index, new_entity_ref_widget, 1)
        self.speed_profile_entries.append(new_entity_ref_widget)
    
    @pyqtSlot()
    def delete_speed_profile_entry_widget(self):
        index = self.main_layout.count() - 2
        if index < 1:
            QMessageBox.warning(self, 'Warning', 'There is nothing to delete')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.speed_profile_entries.pop()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
    
    def get_elements(self):
        return [widget.get_elements() for widget in self.speed_profile_entries]
    
    def get_data(self):
        return [widget.get_data() for widget in self.speed_profile_entries]

class SpeedProfileActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.speed_profile_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def speed_profile_action_info(self):
        groupbox = QGroupBox('SpeedProfileAction')
        self.entityRef = QLineEdit()
        following_mode_list = [str(following_mode.name) for following_mode in FollowingMode]
        self.following_mode_combo_box = QComboBox()
        self.following_mode_combo_box.addItems(following_mode_list)
        self.dynamic_constraints = DynamicConstraintsWidget()
        self.speed_profile_entry = SpeedProfileEntriesWidget()
        form_layout = QFormLayout()
        form_layout.addRow('EntityRef:', self.entityRef)
        form_layout.addRow('FollowingMode:', self.following_mode_combo_box)
        form_layout.addRow('DynamicConstraints:', self.dynamic_constraints)
        form_layout.addRow('SpeedProfileEntry:', self.speed_profile_entry)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'entityRef':self.entityRef.text(), 
                            'followingMode':self.following_mode_combo_box.currentText(),
                            'dynamicConstraints':self.dynamic_constraints.get_elements(),
                            'speedProfileEntry':self.speed_profile_entry.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entityRef.text(), 
                             'followingMode':self.following_mode_combo_box.currentText()})
        return SpeedProfileAction(attrib, self.dynamic_constraints.get_data(), self.speed_profile_entry.get_data())
        
class LongitudinalActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.longitudinal_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def longitudinal_action_info(self):
        groupbox = QGroupBox('LongitduinalAction')
        action_type_list = ['speedAction', 'longitudinalDistanceAction', 'speedProfileAction']
        self.longitudinal_action_type_combo_box = QComboBox()
        self.longitudinal_action_type_combo_box.addItems(action_type_list)
        self.longitudinal_action_type_combo_box.activated[str].connect(self.update_action)
        
        self.longitudinal_action_widget = QStackedWidget()
        self.speed_action_widget = SpeedActionWidget()
        self.longitudinal_distance_action_widget = LongitudinalDistanceActionWidget()
        self.speed_profile_action_widget = SpeedProfileActionWidget()
        self.longitudinal_action_widget.addWidget(self.speed_action_widget)
        self.longitudinal_action_widget.addWidget(self.longitudinal_distance_action_widget)
        self.longitudinal_action_widget.addWidget(self.speed_profile_action_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.longitudinal_action_type_combo_box)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.longitudinal_action_widget)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        groupbox.setLayout(vbox)
        return groupbox
                
    def update_action(self, choice):
        if choice == 'speedAction':
            self.longitudinal_action_widget.setCurrentWidget(self.speed_action_widget)
        elif choice == 'longitudinalDistanceAction':
            self.longitudinal_action_widget.setCurrentWidget(self.longitudinal_distance_action_widget)
        elif choice == 'speedProfileAction':
            self.longitudinal_action_widget.setCurrentWidget(self.speed_profile_action_widget)
        else:
            raise InvalidSelectionError("{} not in longitudinalAction category".format(choice))
    
    def get_elements(self):
        if self.longitudinal_action_type_combo_box.currentText() == 'speedAction':
            return {'action':self.speed_action_widget.get_elements()}
        elif self.longitudinal_action_type_combo_box.currentText() == 'longitudinalDistanceAction':
            return {'action':self.longitudinal_distance_action_widget.get_elements()}
        elif self.longitudinal_action_type_combo_box.currentText() == 'speedProfileAction':
            return {'action':self.speed_profile_action_widget.get_elements()}
        else:
            raise ValueError('Failed to get elements: {}', self.longitudinal_action_type_combo_box.currentText())
    
    def get_data(self):
        if self.longitudinal_action_type_combo_box.currentText() == 'speedAction':
            return LongitudinalAction(action=self.speed_action_widget.get_data())
        elif self.longitudinal_action_type_combo_box.currentText() == 'longitudinalDistanceAction':
            return LongitudinalAction(action=self.longitudinal_distance_action_widget.get_data())
        elif self.longitudinal_action_type_combo_box.currentText() == 'speedProfileAction':
            return LongitudinalAction(action=self.speed_profile_action_widget.get_data())
        else:
            raise ValueError('Failed to get data: {}', self.longitudinal_action_type_combo_box.currentText())

class RelativeTargetLaneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_target_lane_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def relative_target_lane_info(self):
        main_widget = QWidget()
        self.value = QLineEdit()
        self.value.setValidator(QIntValidator())
        self.value.setPlaceholderText('Signed number of lanes')
        self.entityRef = QLineEdit()
        
        form_layout = QFormLayout()
        form_layout.addRow('Value:', self.value)
        form_layout.addRow('EntityRef:', self.entityRef)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'entityRef':self.entityRef.text(), 'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entityRef.text(), 'value':self.value.text()})
        return RelativeTargetLane(attrib)
        
class AbsoluteTargetLaneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.absolute_target_lane_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def absolute_target_lane_info(self):
        main_widget = QWidget()
        self.value = QLineEdit()
        self.value.setPlaceholderText('Number (ID) fo the target lane')
        form_layout = QFormLayout()
        form_layout.addRow('Value:', self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        return AbsoluteTargetLane(attrib)

class LaneChangeActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.lane_change_action_info(), 0 , 0)
        self.setLayout(grid_layout)
    
    def lane_change_action_info(self):
        groupbox = QGroupBox('LaneChangeAction')
        self.target_lane_off_set = QLineEdit()
        self.target_lane_off_set.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.target_lane_off_set.setPlaceholderText('Lane offset')
        self.target_lane_off_set.setToolTip('Lane offset to be reached at the target lane, Missing value is interpreted as 0')
        self.lane_change_action_dynamics = TransitionDynamicsWidget()
        
        lane_change_target_list = ['relativeTargetLane', 'absoluteTargetLane'] 
        self.lane_change_target_combo_box = QComboBox()
        self.lane_change_target_combo_box.addItems(lane_change_target_list)
        self.lane_change_target_combo_box.activated[str].connect(self.update_target_lane)
        self.lane_change_target_widget = QStackedWidget()
        self.relative_target_lane_widget = RelativeTargetLaneWidget()
        self.absolute_target_lane_widget = AbsoluteTargetLaneWidget()
        self.lane_change_target_widget.addWidget(self.relative_target_lane_widget)
        self.lane_change_target_widget.addWidget(self.absolute_target_lane_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('TargetLaneOffset(m):', self.target_lane_off_set)
        form_layout.addRow('LaneChangeActionDynamics:', self.lane_change_action_dynamics)
        form_layout.addRow('LaneChangeTarget:', self.lane_change_target_combo_box)
        form_layout.addWidget(self.lane_change_target_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def update_target_lane(self, choice):
        if choice == 'relativeTargetLane':
            self.lane_change_target_widget.setCurrentWidget(self.relative_target_lane_widget)
        elif self.lane_change_target_combo_box.currentText() == 'absoluteTargetLane':
            self.lane_change_target_widget.setCurrentWidget(self.absolute_target_lane_widget)
        else:
            raise InvalidSelectionError("{} not in laneChangeTarget category".format(self.lane_change_target_combo_box.currentText()))

    def get_lane_change_target_elements(self):
        if self.lane_change_target_combo_box.currentText() == 'relativeTargetLane':
            return self.relative_target_lane_widget.get_elements()
        elif self.lane_change_target_combo_box.currentText() == 'absoluteTargetLane':
            return self.absolute_target_lane_widget.get_elements()
        else:
            raise ValueError('Failed to get element: {}', self.lane_change_target_combo_box.currentText())
    
    def get_lane_change_target_data(self):
        if self.lane_change_target_combo_box.currentText() == 'relativeTargetLane':
            return LaneChangeTarget(self.relative_target_lane_widget.get_data())
        elif self.lane_change_target_combo_box.currentText() == 'absoluteTargetLane':
            return LaneChangeTarget(self.absolute_target_lane_widget.get_data())
        else:
            raise ValueError('Failed to get data: {}', self.lane_change_target_combo_box.currentText())

    def get_elements(self):
        return clean_empty({'targetLaneOffset':self.target_lane_off_set.text(),
                            'dynamics':self.lane_change_action_dynamics.get_elements(),
                            'target':self.get_lane_change_target_elements()})
    
    def get_data(self):
        attrib = clean_empty({'targetLaneOffset':self.target_lane_off_set.text()})
        return LaneChangeAction(attrib, 
                                transition_dynamics=self.lane_change_action_dynamics.get_data(),
                                target=self.get_lane_change_target_data())

class LaneOffsetActionDynamicsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.lane_offset_action_dynamics_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def lane_offset_action_dynamics_info(self):
        main_widget = QWidget()
        dynamic_shape_list = [str(shape.name) for shape in DynamicsShape]
        self.dynamics_shape_combo_box = QComboBox()
        self.dynamics_shape_combo_box.addItems(dynamic_shape_list)
        self.maxLateralAcc = QLineEdit()
        self.maxLateralAcc.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.maxLateralAcc.setPlaceholderText('Range [0..inf]')
        
        form_layout = QFormLayout()
        form_layout.addRow('DynamicsShape:', self.dynamics_shape_combo_box)
        form_layout.addRow('MaxLateralAcc(m/s\u00b2)', self.maxLateralAcc)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'dynamicsShape':self.dynamics_shape_combo_box.currentText(),
                            'maxLateralAcc':self.maxLateralAcc.text()})
    
    def get_data(self):
        attrib = clean_empty({'dynamicsShape':self.dynamics_shape_combo_box.currentText(),'maxLateralAcc':self.maxLateralAcc.text()})
        return LaneOffsetActionDynamics(attrib)

class LaneOffSetActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.lane_offset_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def lane_offset_action_info(self):
        groupbox = QGroupBox('LaneOffsetAction')
        lane_offset_target_list = ['relativeTargetLaneOffset', 'absoluteTargetLaneOffset'] 
        self.continuous_combo_box = QComboBox()
        self.continuous_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.lane_offset_action_dynamics_widget = LaneOffsetActionDynamicsWidget()
        self.lane_offset_target_combo_box = QComboBox()
        self.lane_offset_target_combo_box.addItems(lane_offset_target_list)
        self.lane_offset_target_combo_box.activated[str].connect(self.update_target_offset)
        self.lane_offset_target_widget = QStackedWidget()
        self.relative_target_lane_offset_widget=RelativeTargetLaneOffsetWidget()
        self.absolute_target_lane_offset_widget=AbsoluteTargetLaneOffsetWidget()
        self.lane_offset_target_widget.addWidget(self.relative_target_lane_offset_widget)
        self.lane_offset_target_widget.addWidget(self.absolute_target_lane_offset_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('Continuous', self.continuous_combo_box)
        form_layout.addRow('LaneOffsetActionDynamics', self.lane_offset_action_dynamics_widget)
        form_layout.addRow('LaneOffsetTarget:', self.lane_offset_target_combo_box)
        form_layout.addWidget(self.lane_offset_target_widget)
        groupbox.setLayout(form_layout)
        return groupbox
        
    def update_target_offset(self, choice):
        if choice == 'relativeTargetLaneOffset':
            self.lane_offset_target_widget.setCurrentWidget(self.relative_target_lane_offset_widget)
        elif choice == 'absoluteTargetLaneOffset':
            self.lane_offset_target_widget.setCurrentWidget(self.absolute_target_lane_offset_widget)
        else:
             raise InvalidSelectionError("{} not in longitudinal category".format(choice))
    
    def get_lane_change_target_elements(self):
        if self.lane_offset_target_combo_box.currentText() == 'relativeTargetLaneOffset':
            return self.relative_target_lane_offset_widget.get_elements()
        elif self.lane_offset_target_combo_box.currentText() == 'absoluteTargetLaneOffset':
            return self.absolute_target_lane_offset_widget.get_elements()
        else:
            raise ValueError('Failed to get data: {}', self.lane_offset_target_combo_box.currentText())
    
    def get_lane_change_target_data(self):
        if self.lane_offset_target_combo_box.currentText() == 'relativeTargetLaneOffset':
            return LaneOffsetTarget(self.relative_target_lane_offset_widget.get_data())
        elif self.lane_offset_target_combo_box.currentText() == 'absoluteTargetLaneOffset':
            return LaneOffsetTarget(self.absolute_target_lane_offset_widget.get_data())
        else:
            raise ValueError('Failed to get data: {}', self.lane_offset_target_combo_box.currentText())
    
    def get_elements(self):
        return clean_empty({'continuous':self.continuous_combo_box.currentText(),
                            'dynamics':self.lane_offset_action_dynamics_widget.get_elements(),
                            'target':self.get_lane_change_target_elements()})
    
    def get_data(self):
        attrib = clean_empty({'continuous':self.continuous_combo_box.currentText()})
        return LaneOffsetAction(attrib,
                                dynamics=self.lane_offset_action_dynamics_widget.get_data(),
                                target=self.get_lane_change_target_data())

class RelativeTargetLaneOffsetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_target_lane_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def relative_target_lane_info(self):
        main_widget = QWidget()
        self.value = QLineEdit()
        self.value.setValidator(QIntValidator())
        self.value.setPlaceholderText('Signed number of lanes')
        self.entityRef = QLineEdit()
        
        form_layout = QFormLayout()
        form_layout.addRow('Value:', self.value)
        form_layout.addRow('EntityRef:', self.entityRef)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'entityRef':self.entityRef.text(), 'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entityRef.text(), 'value':self.value.text()})
        return RelativeTargetLaneOffset(attrib)
        
class AbsoluteTargetLaneOffsetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.absolute_target_lane_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def absolute_target_lane_info(self):
        main_widget = QWidget()
        self.value = QLineEdit()
        self.value.setValidator(QIntValidator())
        self.value.setPlaceholderText('Signed number of lanes')
        form_layout = QFormLayout()
        form_layout.addRow('Value:', self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        return AbsoluteTargetLaneOffset(attrib)

class LateralDistanceActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.lateral_distance_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def lateral_distance_action_info(self):
        groupbox = QGroupBox('LongitudinalDistanceAction')
        self.continuous_combo_box = QComboBox()
        self.continuous_combo_box.addItems(BOOLEAN_TYPE_LIST)
        coordinate_system_list = [str(coordinate.name) for coordinate in CoordinateSystem]
        self.coordinate_system_combo_box = QComboBox()
        self.coordinate_system_combo_box.addItems(coordinate_system_list)
        lateral_displacement_list = ['any','leftToReferencedEntity','rightToReferencedEntity']	
        self.lateral_displacement_combo_box = QComboBox()
        self.lateral_displacement_combo_box.addItems(lateral_displacement_list)
        self.distance = QLineEdit()
        self.distance.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.distance.setPlaceholderText('Range [0..inf]')
        self.entity_ref = QLineEdit()
        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.dynamic_constraints = DynamicConstraintsWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('Continuous:', self.continuous_combo_box)
        form_layout.addRow('CoordinateSystem:', self.coordinate_system_combo_box)
        form_layout.addRow('Displacement:', self.lateral_displacement_combo_box)
        form_layout.addRow('Distance(m):', self.distance)
        form_layout.addRow('EntityRef:', self.entity_ref)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('DynamicConstraints', self.dynamic_constraints)
        groupbox.setLayout(form_layout)
        return groupbox

    def get_elements(self):
        return clean_empty({'continuous':self.continuous_combo_box.currentText(),
                            'entityRef':self.entity_ref.text(),
                            'freespace':self.freespace_combo_box.currentText(),
                            'distance': self.distance.text(), 
                            'coordinateSystem':self.coordinate_system_combo_box.currentText(), 
                            'displacement':self.lateral_displacement_combo_box.currentText(),
                            'dynamicConstraints':self.dynamic_constraints.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'continuous':self.continuous_combo_box.currentText(),
                              'entityRef':self.entity_ref.text(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'distance': self.distance.text(), 
                              'coordinateSystem':self.coordinate_system_combo_box.currentText(), 
                              'displacement':self.lateral_displacement_combo_box.currentText()})
        return LateralDistanceAction(attrib, dynamic_constraint=self.dynamic_constraints.get_data())
    
class LateralActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.lateral_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def lateral_action_info(self):
        groupbox = QGroupBox('LateralAction')
        action_type_list = ['laneChangeAction', 'laneOffsetAction','lateralDistanceAction']
        self.lateral_action_type_combo_box = QComboBox()
        self.lateral_action_type_combo_box.addItems(action_type_list)
        self.lateral_action_type_combo_box.activated[str].connect(self.update_action)

        self.lateral_action_widget = QStackedWidget()
        self.lane_change_action_widget = LaneChangeActionWidget()
        self.lane_offset_action_widget = LaneOffSetActionWidget()
        self.lateral_distance_action_widget = LateralDistanceActionWidget()
        self.lateral_action_widget.addWidget(self.lane_change_action_widget)
        self.lateral_action_widget.addWidget(self.lane_offset_action_widget)
        self.lateral_action_widget.addWidget(self.lateral_distance_action_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.lateral_action_type_combo_box)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.lateral_action_widget)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        groupbox.setLayout(vbox)
        return groupbox
        
    def update_action(self, choice):
        if choice == 'laneChangeAction':
            self.lateral_action_widget.setCurrentWidget(self.lane_change_action_widget)
        elif choice == 'laneOffsetAction':
            self.lateral_action_widget.setCurrentWidget(self.lane_offset_action_widget)
        elif choice == 'lateralDistanceAction':
            self.lateral_action_widget.setCurrentWidget(self.lateral_distance_action_widget)
        else:
            raise InvalidSelectionError("{} not in lateralAction category".format(choice))

    def get_elements(self):
        if self.lateral_action_type_combo_box.currentText() == 'laneChangeAction':
            return {'action':self.lane_change_action_widget.get_elements()}
        elif self.lateral_action_type_combo_box.currentText() == 'laneOffsetAction':
            return {'action':self.lane_offset_action_widget.get_elements()}
        elif self.lateral_action_type_combo_box.currentText() == 'lateralDistanceAction':
            return {'action':self.lateral_distance_action_widget.get_elements()}
        else:
            raise ValueError('Failed to get element: {}', self.lateral_action_type_combo_box.currentText())

    def get_data(self):
        if self.lateral_action_type_combo_box.currentText() == 'laneChangeAction':
            return LateralAction(action=self.lane_change_action_widget.get_data())
        elif self.lateral_action_type_combo_box.currentText() == 'laneOffsetAction':
            return LateralAction(action=self.lane_offset_action_widget.get_data())
        elif self.lateral_action_type_combo_box.currentText() == 'lateralDistanceAction':
            return LateralAction(action=self.lateral_distance_action_widget.get_data())
        else:
            raise ValueError('Failed to get data: {}', self.lateral_action_type_combo_box.currentText())

class SensorReferenceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        self.name = QLineEdit()
        self.name.setToolTip('Name of the sensor')
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.name)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return {'name':self.name.text()}
    
    def get_data(self):
        return SensorReference({'name':self.name.text()})

class SensorReferenceSetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor_reference_set = []
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        sensor_reference_widget = SensorReferenceWidget()
        self.main_layout.insertWidget(0, sensor_reference_widget)
        self.sensor_reference_set.append(sensor_reference_widget)
        self.button_layout = self.make_button_layout()
        self.main_layout.addLayout(self.button_layout, -1)
        self.setLayout(self.main_layout)
    
    def make_button_layout(self):
        grid_layout = QGridLayout()
        self.add_sensor_reference_btn = QPushButton("add sensorReference")
        self.add_sensor_reference_btn.clicked.connect(self.add_sensor_reference_widget)
        self.delete_sensor_reference_btn = QPushButton('delete sensorReference')
        self.delete_sensor_reference_btn.clicked.connect(self.delete_sensor_reference_widget)
        grid_layout.addWidget(self.add_sensor_reference_btn, 0, 0)
        grid_layout.addWidget(self.delete_sensor_reference_btn, 0, 1)
        return grid_layout

    @pyqtSlot()
    def add_sensor_reference_widget(self):
        new_sensor_reference_widget = SensorReferenceWidget()
        index = self.main_layout.count() - 1
        self.main_layout.insertWidget(index, new_sensor_reference_widget, 1)
        self.sensor_reference_set.append(new_sensor_reference_widget)
    
    @pyqtSlot()
    def delete_sensor_reference_widget(self):
        index = self.main_layout.count() - 2
        if index < 1:
            QMessageBox.warning(self, 'Warning', 'There is nothing to delete')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.sensor_reference_set.pop()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
    
    def get_elements(self):
        return [widget.get_elements() for widget in self.sensor_reference_set]
    
    def get_data(self):
        return SensorReferenceSet([widget.get_data() for widget in self.sensor_reference_set])

class VisibilityActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.visiblity_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def visiblity_action_info(self):
        groupbox = QGroupBox('VisibilityAction')
        self.graphics_combo_box = QComboBox()
        self.graphics_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.graphics_combo_box.setToolTip('True: actor is visible in image generator(s). False: actor is not visible in image generator(s).')
        self.sensors_combo_box = QComboBox()
        self.sensors_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.sensors_combo_box.setToolTip('True: actor is visible in sensor(s). False: actor is not visible in sensor(s).')
        self.traffic_combo_box = QComboBox()
        self.traffic_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.traffic_combo_box.setToolTip('True: actor is visible for other traffic participants, particularly for autonomous driver models. False: actor is not visible for other traffic participants.')
        self.sensor_reference_set_widget = SensorReferenceSetWidget()
        form_layout = QFormLayout()
        form_layout.addRow('Graphics:', self.graphics_combo_box)
        form_layout.addRow('Sensors:', self.sensors_combo_box)
        form_layout.addRow('Traffic:', self.traffic_combo_box)
        form_layout.addRow('SensorReferenceSet:', self.sensor_reference_set_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'graphics':self.graphics_combo_box.currentText(), 
                            'sensors':self.sensors_combo_box.currentText(),
                            'traffic':self.traffic_combo_box.currentText(),
                            'sensorReferenceSet':self.sensor_reference_set_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'graphics':self.graphics_combo_box.currentText(), 
                              'sensors':self.sensors_combo_box.currentText(),
                              'traffic':self.traffic_combo_box.currentText()})
        return VisibilityAction(attrib, self.sensor_reference_set_widget.get_data())
        
class TargetDistanceSteadyStateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.distance = QLineEdit()
        self.distance.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.distance.setPlaceholderText('Range [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('Distance(m):', self.distance)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'distance':self.distance.text()})
    
    def get_data(self):
        attrib = clean_empty({'distance':self.distance.text()})
        return TargetDistanceSteadyState(attrib)

class TargetTimeSteadyStateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.time = QLineEdit()
        self.time.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.time.setPlaceholderText('Range [0..inf]')
        form_layout = QFormLayout()
        form_layout.addRow('Time(s):', self.time)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'time':self.time.text()})
    
    def get_data(self):
        attrib = clean_empty({'time':self.time.text()})
        return TargetTimeSteadyState(attrib)
    
class AbsoluteSpeedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        steady_state_list = ['targetDistanceSteadyState','targetTimeSteadyState']
        self.steady_state_combo_box = QComboBox()
        self.steady_state_combo_box.setToolTip('Optional final phase of constant (final) speed.')
        self.steady_state_combo_box.addItems(steady_state_list)
        self.steady_state_combo_box.activated[str].connect(self.update_steady_state)
        
        self.steady_state_widget = QStackedWidget()
        self.targetDistanceSteadyState_widget = TargetDistanceSteadyStateWidget()
        self.targetTimeSteadyState_widget = TargetTimeSteadyStateWidget()
        
        self.steady_state_widget.addWidget(self.targetDistanceSteadyState_widget)
        self.steady_state_widget.addWidget(self.targetTimeSteadyState_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('Value (m/s):', self.value)
        form_layout.addRow('SteadyState:', self.steady_state_combo_box)
        form_layout.addWidget(self.steady_state_widget)
        self.setLayout(form_layout)

    def update_steady_state(self, choice):
        if choice == 'targetDistanceSteadyState':
            self.steady_state_widget.setCurrentWidget(self.targetDistanceSteadyState_widget)
        elif choice == 'targetTimeSteadyState':
            self.steady_state_widget.setCurrentWidget(self.targetTimeSteadyState_widget)
        else:
            raise InvalidSelectionError("{} not in steadyState category".format(choice))
    
    def get_steady_state_elements(self):
        if self.steady_state_combo_box.currentText() == 'targetDistanceSteadyState':
            return self.targetDistanceSteadyState_widget.get_elements()
        elif self.steady_state_combo_box.currentText() == 'targetTimeSteadyState':
            return self.targetTimeSteadyState_widget.get_elements()
        else:
            raise ValueError('Failed to get element: {}', self.steady_state_combo_box.currentText())
    
    def get_steady_state_data(self):
        if self.steady_state_combo_box.currentText() == 'targetDistanceSteadyState':
            return SteadyState(self.targetDistanceSteadyState_widget.get_data(), None)
        elif self.steady_state_combo_box.currentText() == 'targetTimeSteadyState':
            return SteadyState(None, self.targetTimeSteadyState_widget.get_data())
        else:
            raise ValueError('Failed to get element: {}', self.steady_state_combo_box.currentText())
    
    def get_elements(self):
        return clean_empty({'value':self.value.text(), 'steadyState':self.get_steady_state_elements()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        return AbsoluteSpeed(attrib, steady_state=self.get_steady_state_data())

class RelativeSpeedToMasterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        speed_target_value_type_list = [str(val_type.name) for val_type in SpeedTargetValueType]
        self.speed_target_value_type_combo_box = QComboBox()
        self.speed_target_value_type_combo_box.addItems(speed_target_value_type_list)
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        steady_state_list = ['targetDistanceSteadyState','targetTimeSteadyState']
        self.steady_state_combo_box = QComboBox()
        self.steady_state_combo_box.setToolTip('Optional final phase of constant (final) speed.')
        self.steady_state_combo_box.addItems(steady_state_list)
        self.steady_state_combo_box.activated[str].connect(self.update_steady_state)
        self.steady_state_widget = QStackedWidget()
        self.targetDistanceSteadyState_widget = TargetDistanceSteadyStateWidget()
        self.targetTimeSteadyState_widget = TargetTimeSteadyStateWidget()
        
        self.steady_state_widget.addWidget(self.targetDistanceSteadyState_widget)
        self.steady_state_widget.addWidget(self.targetTimeSteadyState_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('SpeedTargetValueType:', self.speed_target_value_type_combo_box)
        form_layout.addRow('Value(m):', self.value)
        form_layout.addRow('SteadyState:', self.steady_state_combo_box)
        form_layout.addWidget(self.steady_state_widget)
        self.setLayout(form_layout)
        
    def update_steady_state(self, choice):
        if choice == 'targetDistanceSteadyState':
            self.steady_state_widget.setCurrentWidget(self.targetDistanceSteadyState_widget)
        elif choice == 'targetTimeSteadyState':
            self.steady_state_widget.setCurrentWidget(self.targetTimeSteadyState_widget)
        else:
            raise InvalidSelectionError("{} not in steadyState category".format(choice))
    
    def get_steady_state_elements(self):
        if self.steady_state_combo_box.currentText() == 'targetDistanceSteadyState':
            return self.targetDistanceSteadyState_widget.get_elements()
        elif self.steady_state_combo_box.currentText() == 'targetTimeSteadyState':
            return self.targetTimeSteadyState_widget.get_elements()
        else:
            raise ValueError('Failed to get element: {}', self.steady_state_combo_box.currentText())
    
    def get_steady_state_data(self):
        if self.steady_state_combo_box.currentText() == 'targetDistanceSteadyState':
            return self.targetDistanceSteadyState_widget.get_data()
        elif self.steady_state_combo_box.currentText() == 'targetTimeSteadyState':
            return self.targetTimeSteadyState_widget.get_data()
        else:
            raise ValueError('Failed to get data: {}', self.steady_state_combo_box.currentText())
    
    def get_elements(self):
        return clean_empty({'speedTargetValueType':self.speed_target_value_type_combo_box.currentText(),
                            'value':self.value.text(),
                            'steadyState':self.get_steady_state_elements()})
    
    def get_data(self):
        attrib = clean_empty({'speedTargetValueType':self.speed_target_value_type_combo_box.currentText(), 
                              'value':self.value.text()})
        return RelativeSpeedToMaster(attrib, steady_state=self.get_steady_state_data())
        
class SynchronizeActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.synchronize_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def synchronize_action_info(self):
        groupbox = QGroupBox('SynchronizeAction')
        self.masterEntityRef = QLineEdit()
        self.masterEntityRef.setToolTip('A reference to the master entity.')
        self.targetTolerance = QLineEdit()
        self.targetTolerance.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.targetTolerance.setPlaceholderText('Range [0..inf]')
        self.targetToleranceMaster = QLineEdit()
        self.targetToleranceMaster.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.targetToleranceMaster.setPlaceholderText('Range [0..inf]')
        
        form_layout = QFormLayout()
        form_layout.addRow('MasterEntityRef:', self.masterEntityRef)
        form_layout.addRow('TargetTolerance(m):', self.targetTolerance)
        form_layout.addRow('TargetToleranceMaster(m):', self.targetToleranceMaster)
        
        self.combo_master_position_type = QComboBox()
        self.combo_master_position_type.setToolTip('The target position for the master entity.')
        self.combo_master_position_type.addItems(POSITION_LIST)
        self.combo_master_position_type.activated[str].connect(self.update_master_position)
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.setToolTip('The target position for the entity that should be synchronized.')
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.world_position_master = WorldPositionWidget()
        self.link_position_master = LinkPositionWidget()
        self.relative_object_position_master = RelativeObjectPositionWidget()
        self.relative_world_position_master = RelativeWorldPositionWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        
        self.targetPositionMaster_widget = QStackedWidget()
        self.targetPositionMaster_widget.addWidget(self.world_position_master)
        self.targetPositionMaster_widget.addWidget(self.relative_world_position_master)
        self.targetPositionMaster_widget.addWidget(self.link_position_master)
        self.targetPositionMaster_widget.addWidget(self.relative_object_position_master)
        
        self.targetPosition_widget = QStackedWidget()
        self.targetPosition_widget.addWidget(self.world_position)
        self.targetPosition_widget.addWidget(self.relative_world_position)
        self.targetPosition_widget.addWidget(self.link_position)
        self.targetPosition_widget.addWidget(self.relative_object_position)
        
        form_layout.addRow('TargetPositionMaster:', self.combo_master_position_type)
        form_layout.addWidget(self.targetPositionMaster_widget) 
        form_layout.addRow('TargetPosition:', self.position_type_combo_box)
        form_layout.addWidget(self.targetPosition_widget)
        
        final_speed_action_list = ['absoluteSpeed', 'relativeSpeedToMaster']
        self.final_speed_action_combo_box = QComboBox()
        self.final_speed_action_combo_box.setToolTip('The speed that the synchronized entity should have at its target position.')
        self.final_speed_action_combo_box.activated[str].connect(self.update_speed_action)
        self.final_speed_action_combo_box.addItems(final_speed_action_list)
        form_layout.addRow('Finalspeed:', self.final_speed_action_combo_box)
        
        self.final_speed_widget = QStackedWidget()
        self.absolute_speed_widget = AbsoluteSpeedWidget()
        self.relativeSpeedToMaster_widget = RelativeSpeedToMasterWidget()
        self.final_speed_widget.addWidget(self.absolute_speed_widget)
        self.final_speed_widget.addWidget(self.relativeSpeedToMaster_widget)
        form_layout.addWidget(self.final_speed_widget)
        
        groupbox.setLayout(form_layout)
        return groupbox
    
    def update_speed_action(self, choice):
        if choice == 'absoluteSpeed':
            self.final_speed_widget.setCurrentWidget(self.absolute_speed_widget)
        else:
            self.final_speed_widget.setCurrentWidget(self.relativeSpeedToMaster_widget)
    
    def update_master_position(self, choice):
        if choice == 'World Position':
            self.targetPositionMaster_widget.setCurrentWidget(self.world_position_master)
        elif choice == 'RelativeWorldPosition':
            self.targetPositionMaster_widget.setCurrentWidget(self.relative_world_position_master)
        elif choice == 'Link Position':
            self.targetPositionMaster_widget.setCurrentWidget(self.link_position_master)
        elif choice == 'RelativeObjectPosition':
            self.targetPositionMaster_widget.setCurrentWidget(self.relative_object_position_master)
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.targetPosition_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.targetPosition_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.targetPosition_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.targetPosition_widget.setCurrentWidget(self.relative_object_position)
    
    def get_master_position_elements(self):
        if self.combo_master_position_type.currentText() == 'World Position':
            return self.world_position_master.get_elements()
        elif self.combo_master_position_type.currentText() == 'RelativeWorldPosition':
            return self.relative_object_position_master.get_elements()
        elif self.combo_master_position_type.currentText() == 'Link Position':
            return self.link_position_master.get_elements()
        elif self.combo_master_position_type.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position_master.get_elements()
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_object_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_master_position_data(self):
        if self.combo_master_position_type.currentText() == 'World Position':
            return self.world_position_master.get_data()
        elif self.combo_master_position_type.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position_master.get_data()
        elif self.combo_master_position_type.currentText() == 'Link Position':
            return self.link_position_master.get_data()
        elif self.combo_master_position_type.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position_master.get_data()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def get_final_speed_elements(self):
        if self.final_speed_action_combo_box.currentText() == 'absoluteSpeed':
            return self.absolute_speed_widget.get_elements()
        else:
            return self.relativeSpeedToMaster_widget.get_elements()
    
    def get_final_speed_data(self):
        if self.final_speed_action_combo_box.currentText() == 'absoluteSpeed':
            return FinalSpeed(target_speed=self.absolute_speed_widget.get_data())
        else:
            return FinalSpeed(target_speed=self.relativeSpeedToMaster_widget.get_data())
    
    def get_elements(self):
        return clean_empty({'masterEntityRef':self.masterEntityRef.text(), 
                            'targetTolerance':self.targetTolerance.text(),
                            'targetToleranceMaster':self.targetToleranceMaster.text(),
                            'entityPosition':self.get_position_elements(),
                            'masterPosition':self.get_master_position_elements(),
                            'finalSpeed':self.get_final_speed_elements()})
    
    def get_data(self):
        attrib = clean_empty({'masterEntityRef':self.masterEntityRef.text(), 
                              'targetTolerance':self.targetTolerance.text(),
                              'targetToleranceMaster':self.targetToleranceMaster.text()})
        return SynchronizeAction(attrib, 
                                 entity_position=self.get_position_data(),
                                 master_position=self.get_master_position_data(),
                                 final_speed=self.get_final_speed_data())

class AssignControllerActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.assign_controller_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def assign_controller_action_info(self):
        main_widget = QWidget()
        self.activate_animation_combo_box = QComboBox()
        self.activate_animation_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.activate_animation_combo_box.setToolTip('True: The assigned controller gets activated the animation domain. False: the assigned animation controller gets deactivated. If not specified: No change for controlling the animation domain is applied.')
        self.activate_lateral_combo_box = QComboBox()
        self.activate_lateral_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.activate_lateral_combo_box.setToolTip('True: The assigned controller gets activated for the lateral dimension. False: the assigned controller gets deactivated for the lateral dimension. If not specified: No change for controlling the lateral dimension is applied.')
        self.activate_lighting_combo_box = QComboBox()
        self.activate_lighting_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.activate_longitudinal_combo_box = QComboBox()
        self.activate_longitudinal_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.activate_longitudinal_combo_box.setToolTip('True: The assigned controller gets activated for the longitudinal dimension. False: the assigned controller gets deactivated for the longitudinal dimension. If not specified: No change for controlling the longitudinal dimension is applied.')
        
        self.controller_widget = ControllerWidget()
        form_layout = QFormLayout()
        form_layout.addRow('ActivateAnimation:', self.activate_animation_combo_box)
        form_layout.addRow('ActivateLateral:', self.activate_lateral_combo_box)
        form_layout.addRow('ActivateLighting:', self.activate_lighting_combo_box)
        form_layout.addRow('ActivateLongitudinal:', self.activate_longitudinal_combo_box)
        form_layout.addRow('Controller:', self.controller_widget)
        main_widget.setLayout(form_layout)
        return main_widget

    def get_elements(self):
        return clean_empty({'activateAnimation':self.activate_animation_combo_box.currentText(),
                            'activateLateral':self.activate_lateral_combo_box.currentText(),
                            'activateLighting':self.activate_lighting_combo_box.currentText(),
                            'activateLongitudinal':self.activate_longitudinal_combo_box.currentText(),
                            'controller':self.controller_widget.get_elements()})

    def get_data(self):
        attrib = clean_empty({'activateAnimation':self.activate_animation_combo_box.currentText(),
                              'activateLateral':self.activate_lateral_combo_box.currentText(),
                              'activateLighting':self.activate_lighting_combo_box.currentText(),
                              'activateLongitudinal':self.activate_longitudinal_combo_box.currentText()})
        return AssignControllerAction(attrib,
                                      controller=self.controller_widget.get_data())

class OverrideThrottleActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_combo_box = QComboBox()
        self.active_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.active_combo_box.setToolTip('True: override; false: stop overriding.')
        self.maxRate = QLineEdit()
        self.maxRate.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.maxRate.setPlaceholderText('Range [0..inf]')
        self.maxRate.setToolTip('The rate of how fast the new throttle position should be acquired.')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range: [0..1]')
        self.value.setToolTip('Throttle pedal value: 0 represents 0%, 1 represents 100% pressing the throttle pedal.')
        
        form_layout = QFormLayout()
        form_layout.addRow('Active:', self.active_combo_box)
        form_layout.addRow('MaxRate(%/s):', self.maxRate)
        form_layout.addRow('Value(%):', self.value)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'active':self.active_combo_box.currentText(),
                            'maxRate':self.maxRate.text(), 
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'active':self.active_combo_box.currentText(), 
                              'maxRate':self.maxRate.text(),
                              'value':self.value.text()})
        return OverrideThrottleAction(attrib)

class BrakePercentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.brake_percent_info(), 0, 0)
        self.setLayout(grid_layout)

    def brake_percent_info(self):
        main_widget = QWidget()
        self.maxRate = QLineEdit()
        self.maxRate.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        form_layout = QFormLayout()
        form_layout.addRow("MaxRate(%/s):", self.maxRate)
        form_layout.addRow("Value (%):", self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'maxRate':self.maxRate.text(), 'value':self.value.text()})

    def get_data(self):
        attrib = clean_empty({'maxRate':self.maxRate.text(), 'value':self.value.text()})
        return Brake(attrib)

class BrakeForceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.brake_force_info(), 0, 0)
        self.setLayout(grid_layout)

    def brake_force_info(self):
        main_widget = QWidget()
        self.maxRate = QLineEdit()
        self.maxRate.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        form_layout = QFormLayout()
        form_layout.addRow("MaxRate(N/s):", self.maxRate)
        form_layout.addRow("Value (N):", self.value)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'maxRate':self.maxRate.text(), 'value':self.value.text()})

    def get_data(self):
        attrib = clean_empty({'maxRate':self.maxRate.text(), 'value':self.value.text()})
        return Brake(attrib)

class OverrideBrakeActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_combo_box = QComboBox()
        self.active_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.active_combo_box.setToolTip('True: override; false: stop overriding.')
        # self.value = QLineEdit()
        # self.value.setValidator(QDoubleValidator(bottom=0, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        # self.value.setPlaceholderText('Range: [0..1]')
        # self.value.setToolTip('Brake pedal value: 0 represents 0%, 1 represents 100% pressing the throttle pedal.')
        
        brake_input_list = ['brakePercent', 'brakeForce']
        self.brake_input_combo_box = QComboBox()
        self.brake_input_combo_box.addItems(brake_input_list)
        self.brake_input_combo_box.activated[str].connect(self.update_brake_input_info)
        
        self.brake_input_widget = QStackedWidget()
        self.brake_percent_widget = BrakePercentWidget()
        self.brake_force_widget = BrakeForceWidget()
        self.brake_input_widget.addWidget(self.brake_percent_widget)
        self.brake_input_widget.addWidget(self.brake_force_widget)

        form_layout = QFormLayout()
        form_layout.addRow('Active:', self.active_combo_box)
        form_layout.addRow('BrakeInput:', self.brake_input_combo_box)
        form_layout.addWidget(self.brake_input_widget)
        self.setLayout(form_layout)
    
    def update_brake_input_info(self, choice):
        if choice == 'brakePercent':
            self.brake_input_widget.setCurrentWidget(self.brake_percent_widget)
        elif choice == 'brakeForce':
            self.brake_input_widget.setCurrentWidget(self.brake_force_widget)
        else:
            raise InvalidSelectionError("{} not in brakeInput category".format(choice))

    def get_brake_input_elements(self):
        if self.brake_input_combo_box.currentText() == 'brakePercent':
            return self.brake_percent_widget.get_elements()
        elif self.brake_input_combo_box.currentText() == 'brakeForce':
            return self.brake_force_widget.get_elements()
        else:
            raise ValueError('Failed to get element: {}', self.brake_input_combo_box.currentText())

    def get_brake_input_data(self):
        if self.brake_input_combo_box.currentText() == 'brakePercent':
            return BrakeInput(None, self.brake_percent_widget.get_data())
        elif self.brake_input_combo_box.currentText() == 'brakeForce':
            return BrakeInput(self.brake_force_widget.get_data(), None)
        else:
            raise ValueError('Failed to get data: {}', self.brake_input_combo_box.currentText())

    def get_elements(self):
        return clean_empty({'active':self.active_combo_box.currentText(), 'brakeInput':self.get_brake_input_elements()})
    
    def get_data(self):
        attrib = clean_empty({'active':self.active_combo_box.currentText()})
        return OverrideBrakeAction(attrib, self.get_brake_input_data())
        
class OverrideClutchActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_combo_box = QComboBox()
        self.active_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.active_combo_box.setToolTip('True: override; false: stop overriding.')
        self.maxRate = QLineEdit()
        self.maxRate.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.maxRate.setPlaceholderText('Range [-inf..inf]')
        self.maxRate.setToolTip('The rate of how fast the new clutch position should be acquired.')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range: [0..1]')
        self.value.setToolTip('Clutch pedal value: 0 represents 0%, 1 represents 100% pressing the throttle pedal.')
        
        form_layout = QFormLayout()
        form_layout.addRow('Active:', self.active_combo_box)
        form_layout.addRow('MaxRate(%/s):', self.maxRate)
        form_layout.addRow('Value(%):', self.value)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'active':self.active_combo_box.currentText(),
                            'maxRate':self.maxRate.text(),
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'active':self.active_combo_box.currentText(),
                              'maxRate':self.maxRate.text(),
                              'value':self.value.text()})
        return OverrideClutchAction(attrib)
    
class OverrideParkingBrakeActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_combo_box = QComboBox()
        self.active_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.active_combo_box.setToolTip('True: override; false: stop overriding.')
        
        brake_input_list = ['brakePercent', 'brakeForce']
        self.brake_input_combo_box = QComboBox()
        self.brake_input_combo_box.addItems(brake_input_list)
        self.brake_input_combo_box.activated[str].connect(self.update_brake_input_info)

        self.brake_input_widget = QStackedWidget()
        self.brake_percent_widget = BrakePercentWidget()
        self.brake_force_widget = BrakeForceWidget()
        self.brake_input_widget.addWidget(self.brake_percent_widget)
        self.brake_input_widget.addWidget(self.brake_force_widget)

        form_layout = QFormLayout()
        form_layout.addRow('Active:', self.active_combo_box)
        form_layout.addRow('BrakeInput:', self.brake_input_combo_box)
        form_layout.addWidget(self.brake_input_widget)
        self.setLayout(form_layout)

    def update_brake_input_info(self, choice):
        if choice == 'brakePercent':
            self.brake_input_widget.setCurrentWidget(self.brake_percent_widget)
        elif choice == 'brakeForce':
            self.brake_input_widget.setCurrentWidget(self.brake_force_widget)
        else:
            raise InvalidSelectionError("{} not in brakeInput category".format(choice))

    def get_brake_input_elements(self):
        if self.brake_input_combo_box.currentText() == 'brakePercent':
            return self.brake_percent_widget.get_elements()
        elif self.brake_input_combo_box.currentText() == 'brakeForce':
            return self.brake_force_widget.get_elements()
        else:
            raise ValueError('Failed to get element: {}', self.brake_input_combo_box.currentText())

    def get_brake_input_data(self):
        if self.brake_input_combo_box.currentText() == 'brakePercent':
            return BrakeInput(self.brake_percent_widget.get_data())
        elif self.brake_input_combo_box.currentText() == 'brakeForce':
            return BrakeInput(self.brake_force_widget.get_data())
        else:
            raise ValueError('Failed to get data: {}', self.brake_input_combo_box.currentText())

    def get_elements(self):
        return clean_empty({'active':self.active_combo_box.currentText(),'brakeInput':self.get_brake_input_elements()})
    
    def get_data(self):
        attrib = clean_empty({'active':self.active_combo_box.currentText()})
        return OverrideParkingBrakeAction(attrib, self.get_brake_input_data())
                
class OverrideSteeringWheelActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_combo_box = QComboBox()
        self.active_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.active_combo_box.setToolTip('True: override; false: stop overriding.')
        self.maxRate = QLineEdit()
        self.maxRate.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.maxRate.setPlaceholderText('Range [-inf..inf]')
        self.maxTorque = QLineEdit()
        self.maxTorque.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.maxTorque.setPlaceholderText('Range [-inf..inf]')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range: [0..inf]')
        self.value.setToolTip('Steering wheel angle')
        form_layout = QFormLayout()
        form_layout.addRow('Active:', self.active_combo_box)
        form_layout.addRow('MaxRate(%/s):', self.maxRate)
        form_layout.addRow('MaxTorque(Nm):', self.maxTorque)
        form_layout.addRow('Value(rad):', self.value)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'active':self.active_combo_box.currentText(),
                            'maxRate':self.maxRate.text(),
                            'maxTorque':self.maxTorque.text(),
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'active':self.active_combo_box.currentText(),
                              'maxRate':self.maxRate.text(),
                              'maxTorque':self.maxTorque.text(),
                              'value':self.value.text()})
        return OverrideSteeringWheelAction(attrib)

class ManualGearWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.manual_gear_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def manual_gear_info(self):
        main_widget = QWidget()
        self.number = QLineEdit()
        self.number.setValidator(QIntValidator(bottom=1, top=6))
        self.number.setPlaceholderText('Range: [1..6]')
        self.number.setToolTip('Gear number.')
        form_layout = QFormLayout()
        form_layout.addRow('Number:', self.number)
        main_widget.setLayout(form_layout)
        return main_widget

    def get_elements(self):
        return clean_empty({'number':self.number.text()})
    
    def get_data(self):
        attrib = clean_empty({'number':self.number.text()})
        return ManualGear(attrib)

class AutomaticGearWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.automatic_gear_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def automatic_gear_info(self):
        main_widget = QWidget()
        automatic_gear_type_list = [str(ag.name) for ag in AutomaticGearType]
        self.automatic_gear_combo_box = QComboBox()
        self.automatic_gear_combo_box.addItems(automatic_gear_type_list)
        form_layout = QFormLayout()
        form_layout.addRow('Gear:', self.automatic_gear_combo_box)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return {'gear':self.automatic_gear_combo_box.currentText()}
    
    def get_data(self):
        return AutomaticGear({'gear':self.automatic_gear_combo_box.currentText()})

class OverrideGearActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_combo_box = QComboBox()
        self.active_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.active_combo_box.setToolTip('True: override; false: stop overriding.')
        gear_type_list = ['manualGear', 'automaticGear']
        self.gear_combo_box = QComboBox()
        self.gear_combo_box.addItems(gear_type_list)
        self.gear_combo_box.activated[str].connect(self.update_gear_widget)

        self.gear_widget = QStackedWidget()
        self.manual_gear_widget = ManualGearWidget()
        self.automatic_gear_widget = AutomaticGearWidget()
        self.gear_widget.addWidget(self.manual_gear_widget)
        self.gear_widget.addWidget(self.automatic_gear_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('Active:', self.active_combo_box)
        form_layout.addRow('Gear:', self.gear_combo_box)
        form_layout.addWidget(self.gear_widget)
        self.setLayout(form_layout)

    def update_gear_widget(self, choice):
        if choice == 'manualGear':
            self.gear_widget.setCurrentWidget(self.manual_gear_widget)
        elif choice == 'automaticGear':
            self.gear_widget.setCurrentWidget(self.automatic_gear_widget)
        else:
            raise InvalidSelectionError("{} not in Gear category".format(choice))

    def get_gear_elements(self):
        if self.gear_combo_box.currentText() == 'manualGear':
            return self.manual_gear_widget.get_elements()
        elif self.gear_combo_box.currentText() == 'automaticGear':
            return self.automatic_gear_widget.get_elements()
        else:
            raise ValueError('Failed to get element: {}', self.gear_combo_box.currentText())

    def get_gear_data(self):
        if self.gear_combo_box.currentText() == 'manualGear':
            return self.manual_gear_widget.get_data()
        elif self.gear_combo_box.currentText() == 'automaticGear':
            return self.automatic_gear_widget.get_data()
        else:
            raise ValueError('Failed to get data: {}', self.gear_combo_box.currentText())

    def get_elements(self):
        return clean_empty({'active':self.active_combo_box.currentText(), 'gear':self.get_gear_elements()})
    
    def get_data(self):
        attrib = clean_empty({'active':self.active_combo_box.currentText()})
        return OverrideGearAction(attrib, self.get_gear_data())

class OverrideControllerValueActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.override_controller_value_action_info(), 0, 0)
        self.set_default_override_controller_value_action_widget()
        self.setLayout(grid_layout)
    
    def override_controller_value_action_info(self):
        main_widget = QWidget()
        override_controller_value_action_list = ['throttle', 'brake', 'clutch', 'parkingBrake', 'steeringWheel', 'gear']
        self.override_controller_value_action_combo_box = QComboBox()
        self.override_controller_value_action_combo_box.addItems(override_controller_value_action_list)
        self.override_controller_value_action_combo_box.activated[str].connect(self.update_action)
        
        self.override_controller_value_action_layout = QVBoxLayout()
        self.throttle = OverrideThrottleActionWidget()
        self.brake = OverrideBrakeActionWidget()
        self.clutch = OverrideClutchActionWidget()
        self.parkingBrake = OverrideParkingBrakeActionWidget()
        self.steeringWheel = OverrideSteeringWheelActionWidget()
        self.gear = OverrideGearActionWidget()
        self.override_controller_value_action_layout.addWidget(self.throttle)
        self.override_controller_value_action_layout.addWidget(self.brake)
        self.override_controller_value_action_layout.addWidget(self.clutch)
        self.override_controller_value_action_layout.addWidget(self.parkingBrake)
        self.override_controller_value_action_layout.addWidget(self.steeringWheel)
        self.override_controller_value_action_layout.addWidget(self.gear)
        
        form_layout = QFormLayout()
        form_layout.addRow('OverrideControllerValueAction:', self.override_controller_value_action_combo_box)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(self.override_controller_value_action_layout)
        vbox.addStretch()
        main_widget.setLayout(vbox)
        return main_widget
    
    def update_action(self, choice):
        self.hide_all_override_controller_value_action_widget()
        if choice == 'throttle':
            self.throttle.setVisible(True)
        elif choice == 'brake':
            self.brake.setVisible(True)
        elif choice == 'clutch':
            self.clutch.setVisible(True)
        elif choice == 'parkingBrake':
            self.parkingBrake.setVisible(True)
        elif choice == 'steeringWheel':
            self.steeringWheel.setVisible(True)
        elif choice == 'gear':
            self.gear.setVisible(True)
        else:
            self.hide_all_override_controller_value_action_widget()
    
    def set_default_override_controller_value_action_widget(self):
        self.hide_all_override_controller_value_action_widget()
        self.throttle.setVisible(True)
    
    def hide_all_override_controller_value_action_widget(self):
        for i in range(self.override_controller_value_action_layout.count()):
            self.override_controller_value_action_layout.itemAt(i).widget().setVisible(False)
    
    def get_current_visible_action_widget(self):
        for i in range(self.override_controller_value_action_layout.count()):
            widget = self.override_controller_value_action_layout.itemAt(i).widget()
            if isVisibleWidget(widget):
                return widget
    
    def get_override_controller_value_elements(self):
        #'throttle', 'brake', 'clutch', 'parkingBrake', 'steeringWheel', 'gear'
        if self.override_controller_value_action_combo_box.currentText() == 'throttle':
            return self.throttle.get_elements()
        elif self.override_controller_value_action_combo_box.currentText() == 'brake':
            return self.brake.get_elements()
        elif self.override_controller_value_action_combo_box.currentText() == 'clutch':
            return self.clutch.get_elements()
        elif self.override_controller_value_action_combo_box.currentText() == 'parkingBrake':
            return self.parkingBrake.get_elements()
        elif self.override_controller_value_action_combo_box.currentText() == 'steeringWheel':
            return self.steeringWheel.get_elements()
        else:
            return self.gear.get_elements()
    
    def get_elements(self):
        return self.get_override_controller_value_elements()
    
    def get_data(self):
        if self.override_controller_value_action_combo_box.currentText() == 'throttle':
            return OverrideControllerValueAction(self.throttle.get_data(), None, None, None, None, None)
        elif self.override_controller_value_action_combo_box.currentText() == 'brake':
            return OverrideControllerValueAction(None, self.brake.get_data(), None, None, None, None)
        elif self.override_controller_value_action_combo_box.currentText() == 'clutch':
            return OverrideControllerValueAction(None, None, self.clutch.get_data(), None, None, None)
        elif self.override_controller_value_action_combo_box.currentText() == 'parkingBrake':
            return OverrideControllerValueAction(None, None, None, self.parkingBrake.get_data(), None, None)
        elif self.override_controller_value_action_combo_box.currentText() == 'steeringWheel':
            return OverrideControllerValueAction(None, None, None, None, self.steeringWheel.get_data(), None)
        else:
            return OverrideControllerValueAction(None, None, None, None, None, self.gear.get_data())

class ActivateControllerActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.activate_controller_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def activate_controller_action_info(self):
        main_widget = QWidget()
        self.animation = QComboBox()
        self.animation.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.controller_widget = ControllerWidget()
        self.lateral_combo_box = QComboBox()
        self.lateral_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.lighting_combo_box = QComboBox()
        self.lighting_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        self.longitudinal_combo_box = QComboBox()
        self.longitudinal_combo_box.addItems(BOOLEAN_TYPE_LIST_W_NONE)
        form_layout = QFormLayout()
        form_layout.addRow('Animation:', self.animation)
        form_layout.addRow('Lateral:', self.lateral_combo_box)
        form_layout.addRow('Lighting:', self.lighting_combo_box)
        form_layout.addRow('Longitudinal:', self.longitudinal_combo_box)
        form_layout.addRow('Controller:', self.controller_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'animation':self.animation.currentText(),
                            'lateral':self.lateral_combo_box.currentText(), 
                            'lighting':self.lighting_combo_box.currentText(),
                            'longitudinal':self.longitudinal_combo_box.currentText(),
                            'controller':self.controller_widget.get_elements()
                            })
    
    def get_data(self):
        attrib = clean_empty({'animation':self.animation.currentText(),
                            'lateral':self.lateral_combo_box.currentText(), 
                            'lighting':self.lighting_combo_box.currentText(),
                            'longitudinal':self.longitudinal_combo_box.currentText()
                            })
        return ActivateControllerAction(attrib, controller=self.controller_widget.get_data())

class ControllerActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.controller_action_info(), 0, 0)
        self.set_default_controller_action_widget()
        self.setLayout(grid_layout)
        
    def controller_action_info(self):
        groupbox = QGroupBox('ControllerAction')
        controller_action_list = ['assignControllerAction', 'overrideControllerValueAction', 'activateControllerAction']
        self.controller_action_combo_box = QComboBox()
        self.controller_action_combo_box.addItems(controller_action_list)
        self.controller_action_combo_box.activated[str].connect(self.update_action)

        self.controller_action_layout = QVBoxLayout()
        self.assgin_controller_action_widget = AssignControllerActionWidget()
        self.override_controller_value_action_widget = OverrideControllerValueActionWidget()
        self.activate_controller_action_widget = ActivateControllerActionWidget()
        self.controller_action_layout.addWidget(self.assgin_controller_action_widget)
        self.controller_action_layout.addWidget(self.override_controller_value_action_widget)
        self.controller_action_layout.addWidget(self.activate_controller_action_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('ControllerActions:', self.controller_action_combo_box)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(self.controller_action_layout)
        vbox.addStretch()
        groupbox.setLayout(vbox)
        return groupbox
        
    def update_action(self, choice):
        self.hide_all_controller_action_widget()
        if choice == 'assignControllerAction':
            self.assgin_controller_action_widget.setVisible(True)
        elif choice == 'overrideControllerValueAction':
            self.override_controller_value_action_widget.setVisible(True)
        elif choice == 'activateControllerAction':
            self.activate_controller_action_widget.setVisible(True)
        else:
            self.hide_all_controller_action_widget()
    
    def set_default_controller_action_widget(self):
        self.hide_all_controller_action_widget()
        self.assgin_controller_action_widget.setVisible(True)
    
    def hide_all_controller_action_widget(self):
        for i in range(self.controller_action_layout.count()):
            self.controller_action_layout.itemAt(i).widget().setVisible(False)
    
    def get_current_visible_action_widget(self):
        for i in range(self.controller_action_layout.count()):
            widget = self.controller_action_layout.itemAt(i).widget()
            if isVisibleWidget(widget):
                return widget
    
    def get_elements(self):
        if self.controller_action_combo_box.currentText() == 'assignControllerAction':
            return clean_empty({'action':self.assgin_controller_action_widget.get_elements()})
        elif self.controller_action_combo_box.currentText() == 'overrideControllerValueAction':
            return clean_empty({'action:':self.override_controller_value_action_widget.get_elements()})
        else:
            return clean_empty({'action:':self.activate_controller_action_widget.get_elements()})
    
    def get_data(self):
        if self.controller_action_combo_box.currentText() == 'assignControllerAction':
            return ControllerAction(action=self.assgin_controller_action_widget.get_data())
        elif self.controller_action_combo_box.currentText() == 'overrideControllerValueAction':
            return ControllerAction(action=self.override_controller_value_action_widget.get_data())
        else:
            return ControllerAction(action=self.activate_controller_action_widget.get_data())
    
class TeleportActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.teleport_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def teleport_action_info(self):
        groupbox = QGroupBox('TeleportAction')
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)

        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        form_layout = QFormLayout()
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)

    def get_element(self):
        return clean_empty({'position':self.get_position_elements()})
    
    def get_data(self):
        return TeleportAction(position=self.get_position_data())

class WaypointWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.waypoint_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def waypoint_info(self):
        main_widget = QWidget()
        routeStrategy_list = [str(strategy.name) for strategy in RouteStrategy]
        self.route_strategy_combo_box = QComboBox()
        self.route_strategy_combo_box.addItems(routeStrategy_list)
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        form_layout = QFormLayout()
        form_layout.addRow('RouteStrategy:', self.route_strategy_combo_box)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def get_elements(self):
        return clean_empty({'routeStrategy':self.route_strategy_combo_box.currentText(),
                            'position':self.get_position_elements()})
    
    def get_data(self):
        attrib = clean_empty({'routeStrategy':self.route_strategy_combo_box.currentText()})
        return Waypoint(attrib, position=self.get_position_data())

class WaypointListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waypoint_list = []
        self.initUI()
        
    def initUI(self):
        self.main_layout = QVBoxLayout()
        waypoint_widget1 = WaypointWidget()
        waypoint_widget2 = WaypointWidget()
        self.main_layout.insertWidget(0, waypoint_widget1)
        self.main_layout.addStretch(1)
        self.main_layout.insertWidget(1, waypoint_widget2)
        self.waypoint_list.append(waypoint_widget1)
        self.waypoint_list.append(waypoint_widget2)
        self.button_widget = self.make_button_widget()
        self.main_layout.insertWidget(-1, self.button_widget)
        self.setLayout(self.main_layout)
    
    def make_button_widget(self):
        main_widget = QWidget()
        grid_layout = QGridLayout()
        self.add_waypoint_btn = QPushButton("add waypoint")
        self.add_waypoint_btn.clicked.connect(self.add_waypoint)
        self.delete_waypoint_btn = QPushButton("delete waypoint")
        self.delete_waypoint_btn.clicked.connect(self.delete_waypoint)
        
        grid_layout.addWidget(self.add_waypoint_btn, 0, 0)
        grid_layout.addWidget(self.delete_waypoint_btn, 0, 1)
        main_widget.setLayout(grid_layout)
        return main_widget
    
    @pyqtSlot()
    def add_waypoint(self):
        new_waypoint = WaypointWidget()
        index = self.main_layout.count()-2
        self.main_layout.insertWidget(index, new_waypoint, 1)
        self.waypoint_list.append(new_waypoint)
    
    @pyqtSlot()
    def delete_waypoint(self):
        index = self.main_layout.count()-3
        if index < 2:
            QMessageBox.warning(self, 'Warning', 'Cannot delete the waypoint')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.waypoint_list.pop()
    
    def update(self):
        self.delete_widget(self.button_widget)
        self.button_widget = self.make_button_widget()
        self.main_layout.insertWidget(self.control_index, self.button_widget)
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
        
    def get_elements(self):
        return [widget.get_elements() for widget in self.waypoint_list]
    
    def get_data(self):
        return [widget.get_data() for widget in self.waypoint_list]

class RouteWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.route_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def route_info(self):
        main_widget = QWidget()
        self.closed_combo_box = QComboBox()
        self.closed_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.closed_combo_box.setToolTip('In a closed route, the last waypoint is followed by the first waypoint to create a closed route')
        self.name = QLineEdit()
        self.name.setToolTip('Name of the route')
        after_completion_list = ['hide','stop','random']
        self.after_completion_combo_box = QComboBox()
        self.after_completion_combo_box.addItems(after_completion_list)
        #self.parameterDeclarations = QWidget #TODO: 나중 구현 
        self.waypoint = WaypointListWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('Closed:', self.closed_combo_box)
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('AfterCompletion:', self.after_completion_combo_box)
        form_layout.addRow('Waypoints:', self.waypoint)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 'closed':self.closed_combo_box.currentText(),
                            'afterCompletion':self.after_completion_combo_box.currentText(),
                            'waypoints':self.waypoint.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 
                              'closed':self.closed_combo_box.currentText(),
                              'afterCompletion':self.after_completion_combo_box.currentText()})
        return Route(attrib, None, self.waypoint.get_data())

class AssignRouteActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.assign_route_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def assign_route_action_info(self):
        main_widget = QWidget()
        self.route = RouteWidget()
        form_layout = QFormLayout()
        form_layout.addRow('Route:', self.route)
        #form_layout.addRow('catalogreference') #TODO: 나중구현
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return {'route':self.route.get_elements()} 
    
    def get_data(self):
        return AssignRouteAction(self.route.get_data())

class TimingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.timing_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def timing_info(self):
        main_widget = QWidget()
        domainAbsoluteRelative = [str(reference.name) for reference in ReferenceContext]
        self.domainAbsoluteRelative_combo_box = QComboBox()
        self.domainAbsoluteRelative_combo_box.addItems(domainAbsoluteRelative)
        self.offset = QLineEdit()
        self.offset.setValidator(QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation))
        self.offset.setPlaceholderText('Range [-inf..inf]')
        self.offset.setToolTip('Introduction of a global offset for all time values')
        self.scale = QLineEdit()
        self.scale.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.scale.setPlaceholderText('Range: [0..inf]')
        self.scale.setToolTip('Scaling factor for time values')
        
        form_layout = QFormLayout()
        form_layout.addRow('DomainAbsoluteRelative:', self.domainAbsoluteRelative_combo_box)
        form_layout.addRow('Offset(s):', self.offset)
        form_layout.addRow('Scale:', self.scale)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'domainAbsoluteRelative': self.domainAbsoluteRelative_combo_box.currentText(),
                            'offset':self.offset.text(),
                            'scale':self.scale.text()})
    
    def get_data(self):
        attrib = clean_empty({'domainAbsoluteRelative': self.domainAbsoluteRelative_combo_box.currentText(),
                              'offset':self.offset.text(),
                              'scale':self.scale.text()})
        return Timing(attrib)

class VertexWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.vertex_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def vertex_info(self):
        main_widget = QWidget()
        self.time = QLineEdit()
        self.time.setToolTip('Optional time specification of the vertex')
        self.time.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        form_layout = QFormLayout()
        form_layout.addRow('Time:', self.time)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addRow(self.position_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
    
class VertexListWidget(QWidget):
    def __init__(self, vertex_dict, parent=None):
        super().__init__(parent)
        self.vertex_dict = vertex_dict
        self.vertex_list = []
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        vertex1 = VertexWidget()
        vertex2 = VertexWidget()
        self.main_layout.insertWidget(0, vertex1, 1)
        self.main_layout.addStretch(1)
        self.main_layout.insertWidget(1, vertex2, 1)
        self.vertex_list.append(vertex1)
        self.vertex_list.append(vertex2)
        self.button_widget = self.make_button_widget()
        self.main_layout.insertWidget(-1, self.button_widget, 1)
        self.setLayout(self.main_layout)
    
    def make_button_widget(self):
        main_widget = QWidget()
        grid_layout = QGridLayout()
        self.add_vertex_btn = QPushButton("add vertex")
        self.add_vertex_btn.clicked.connect(self.add_vertex)
        self.delete_vertex_btn = QPushButton("delete vertex")
        self.delete_vertex_btn.clicked.connect(self.delete_vertex)
        
        grid_layout.addWidget(self.add_vertex_btn, 0, 0)
        grid_layout.addWidget(self.delete_vertex_btn, 0, 1)
        main_widget.setLayout(grid_layout)
        return main_widget
    
    @pyqtSlot()
    def add_vertex(self):
        new_vertex = VertexWidget()
        index = self.main_layout.count()-2
        self.main_layout.insertWidget(index, new_vertex, 1)
        self.vertex_list.append(new_vertex)
    
    @pyqtSlot()
    def delete_vertex(self):
        index = self.main_layout.count()-3
        if index < 2:
            QMessageBox.warning(self, 'Warning', 'Cannot delete the vertex')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.vertex_list.pop()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None

    def get_data(self):
        return
    
class PolylineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vertex_dict = {}
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.polyline_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def polyline_info(self):
        main_widget = QWidget()
        form_layout = QFormLayout()
        self.vertex_list_widget = VertexListWidget(self.vertex_dict)
        form_layout.addRow('Vertex:', self.vertex_list_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_data(self):
        return

class ClothoidWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.clothoid_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def clothoid_info(self):
        default_double_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        main_widget = QWidget()
        self.curvature = QLineEdit()
        self.curvature.setValidator(default_double_validator)
        self.curvature.setPlaceholderText('Range [-inf..inf]')
        self.curvaturePrime = QLineEdit()
        self.curvaturePrime.setValidator(nonnegative_validator)
        self.curvaturePrime.setPlaceholderText('Range [0..inf]')
        self.length = QLineEdit()
        self.length.setValidator(default_double_validator)
        self.length.setPlaceholderText('Range [-inf..inf]')
        self.startTime = QLineEdit()
        self.startTime.setValidator(nonnegative_validator)
        self.startTime.setPlaceholderText('Range [0..inf]')
        self.stopTime = QLineEdit()
        self.stopTime.setValidator(nonnegative_validator)
        self.stopTime.setPlaceholderText('Range [0..inf]')
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.setToolTip('Start position of a clothoid')
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        form_layout = QFormLayout()
        form_layout.addRow('Curvature(1/m):', self.curvature)
        form_layout.addRow('CurvaturePrime(1/m2):', self.curvaturePrime)
        form_layout.addRow('Length:', self.length)
        form_layout.addRow('StartTime:', self.startTime)
        form_layout.addRow('StopTime:', self.stopTime)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addRow(self.position_widget)
        main_widget.setLayout(form_layout)
        return main_widget
        
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)

    def get_data(self):
        return 
    
class NurbsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel('Not Supported'), 0, 0)
        self.setLayout(grid_layout)
    
class TrajectoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.trajectory_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def trajectory_info(self):
        main_widget = QWidget()
        self.closed_combo_box = QComboBox()
        self.closed_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.closed_combo_box.setToolTip('	True if trajectory is closed.')
        
        self.name = QLineEdit()
        self.name.setToolTip('Name of the trajectory type')
        shape_list = ['polyline', 'clothoid', 'nurbs']
        self.shape_combo_box = QComboBox()
        self.shape_combo_box.addItems(shape_list)
        self.shape_combo_box.activated[str].connect(self.update_shape)
        
        self.shape_widget = QStackedWidget()
        self.polyline = PolylineWidget()
        self.clothoid = ClothoidWidget()
        self.nurbs = NurbsWidget()
        self.shape_widget.addWidget(self.polyline)
        self.shape_widget.addWidget(self.clothoid)
        self.shape_widget.addWidget(self.nurbs)
        
        form_layout = QFormLayout()
        form_layout.addRow('Closed:', self.closed_combo_box)
        form_layout.addRow('Name:', self.name)
        #form_layout.addRow('ParameterDeclarations:', self.parameter_declaration)
        form_layout.addRow('Shape', self.shape_combo_box)
        form_layout.addRow(self.shape_widget)
        main_widget.setLayout(form_layout)
        return main_widget

    def update_shape(self, choice):
        if choice == 'polyline':
            self.shape_widget.setCurrentWidget(self.polyline)
        elif choice == 'clothoid':
            self.shape_widget.setCurrentWidget(self.clothoid)
        else:
            pass #TODO NURB
    
    def get_data(self):
        return {}
    
class FollowTrajectoryActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.follow_trajectory_action_info(), 0, 0)
        self.timing_widget.hide()
        self.setLayout(grid_layout)
    
    def follow_trajectory_action_info(self):
        main_widget = QWidget()
        self.initialDistanceOffset = QLineEdit()
        self.initialDistanceOffset.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.initialDistanceOffset.setPlaceholderText('Range: [0..arclength of the trajectory]')
        self.initialDistanceOffset.setToolTip('An offset into the trajectory.')
        
        self.time_reference_type = ['none', 'timing']
        self.time_reference_type_combo_box = QComboBox()
        self.time_reference_type_combo_box.addItems(self.time_reference_type)
        self.time_reference_type_combo_box.activated[str].connect(self.update_time_reference)
        
        self.time_reference_type_layout = QHBoxLayout()
        self.timing_widget = TimingWidget()
        self.time_reference_type_layout.addWidget(self.timing_widget)
        
        following_mode = ['follow', 'position'] 
        self.following_mode_combo_box = QComboBox()
        self.following_mode_combo_box.addItems(following_mode)
        
        self.trajectory_ref= QLineEdit()
        
        form_layout = QFormLayout()
        form_layout.addRow('InitialDistanceOffset:', self.initialDistanceOffset)
        form_layout.addRow('TimeReference:', self.time_reference_type_combo_box)
        form_layout.addWidget(self.timing_widget)
        form_layout.addRow('FollowingMode:', self.following_mode_combo_box)
        form_layout.addRow('TrajectoryRef:', self.trajectory_ref)
        main_widget.setLayout(form_layout)
        return main_widget

    def hide_widgets(self):
        self.time_reference_type_layout.itemAt(0).widget().hide()
    
    def update_time_reference(self, choice):
        self.hide_widgets()
        if choice == 'timing':
            self.timing_widget.show()
        else:
            self.timing_widget.hide()
    
    def get_elements(self):
        if self.time_reference_type_combo_box.currentText() == 'timing':
            return clean_empty({'initialDistanceOffset':self.initialDistanceOffset.text(),
                                'timeReference':{self.time_reference_type_combo_box.currentText():self.timing_widget.get_elements()},
                                'followingMode':self.following_mode_combo_box.currentText(),
                                'trajectoryRef':self.trajectory_ref.text()})
        else:
            return clean_empty({'initialDistanceOffset':self.initialDistanceOffset.text(),
                                'timeReference':'none',
                                'followingMode':self.following_mode_combo_box.currentText(),
                                'trajectoryRef':self.trajectory_ref.text()})
    
    def get_data(self):
        attrib = clean_empty({'initialDistanceOffset':self.initialDistanceOffset.text()})
        following_mode_attrib = clean_empty({'followingMode': self.following_mode_combo_box.currentText()})
        following_mode = TrajectoryFollowingMode(following_mode_attrib)
        trajectory_attrib = clean_empty({'catalogName':"default_catalog", 'entryName':self.trajectory_ref.text()})
        #TODO: decide whether we're going to use catalogReference UI or Trajectory UI
        trajectory = TrajectoryRef(CatalogReference(trajectory_attrib))       # TODO: trajectory is not implemented
        if self.time_reference_type_combo_box.currentText() == 'timing':
            time_reference = TimeReference(self.timing_widget.get_data())
        else:
            time_reference = TimeReference(NoTiming())
        return FollowTrajectoryAction(attrib, time_reference, following_mode, trajectory)

class AcquirePositionActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.acquire_position_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def acquire_position_action_info(self):
        main_widget = QWidget()
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        
        form_layout = QFormLayout()
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        main_widget.setLayout(form_layout)
        return main_widget 
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
    
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
            
    def get_elements(self):
        return {'position':self.get_position_elements()}
    
    def get_data(self):
        return AcquirePositionAction(position=self.get_position_data())

class RoutingActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.routing_action_info(), 0, 0)
        self.set_default_routing_action_widget()
        self.setLayout(grid_layout)
        
    def routing_action_info(self):
        groupbox = QGroupBox('RoutingAction')
        routing_action_type_list = ['assignRouteAction', 'followTrajectoryAction', 'acquirePositionAction']
        self.routing_action_type_combo_box = QComboBox()
        self.routing_action_type_combo_box.addItems(routing_action_type_list)
        self.routing_action_type_combo_box.activated[str].connect(self.update_action)
        
        self.routing_action_layout = QVBoxLayout()
        self.assignRouteAction_widget = AssignRouteActionWidget()
        self.followTrajectoryAction_widget = FollowTrajectoryActionWidget()
        self.acquirePositionAction_widget = AcquirePositionActionWidget()
        self.routing_action_layout.addWidget(self.assignRouteAction_widget)
        self.routing_action_layout.addWidget(self.followTrajectoryAction_widget)
        self.routing_action_layout.addWidget(self.acquirePositionAction_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.routing_action_type_combo_box)
                
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(self.routing_action_layout)
        groupbox.setLayout(vbox)
        return groupbox
    
    def set_default_routing_action_widget(self):
        self.hide_all_routing_action_widgets()
        self.assignRouteAction_widget.setVisible(True)

    def hide_all_routing_action_widgets(self):
        for i in range(self.routing_action_layout.count()):
            self.routing_action_layout.itemAt(i).widget().setVisible(False)

    def update_action(self, choice):
        self.hide_all_routing_action_widgets()
        if choice == 'assignRouteAction':
            self.assignRouteAction_widget.setVisible(True)
        elif choice == 'followTrajectoryAction':
            self.followTrajectoryAction_widget.setVisible(True)
        else:
            self.acquirePositionAction_widget.setVisible(True) #AcquirePositionAction
    
    def get_elements(self):
        if self.routing_action_type_combo_box.currentText() == 'assignRouteAction':
            return {'action':self.assignRouteAction_widget.get_elements()}
        elif self.routing_action_type_combo_box.currentText() == 'followTrajectoryAction':
            return {'action':self.followTrajectoryAction_widget.get_elements()}
        else:
            return {'action':self.acquirePositionAction_widget.get_elements()}
    
    def get_data(self):
        if self.routing_action_type_combo_box.currentText() == 'assignRouteAction':
            return RoutingAction(action=self.assignRouteAction_widget.get_data())
        elif self.routing_action_type_combo_box.currentText() == 'followTrajectoryAction':
            return RoutingAction(action=self.followTrajectoryAction_widget.get_data())
        else:
            return RoutingAction(action=self.acquirePositionAction_widget.get_data())

class VehicleLightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        vehicle_light_type_list = [str(vehicle_light.name) for vehicle_light in VehicleLightType]
        self.vehicle_light_type_combo_box = QComboBox()
        self.vehicle_light_type_combo_box.addItems(vehicle_light_type_list)
        form_layout = QFormLayout()
        form_layout.addRow('VehicleLightType:', self.vehicle_light_type_combo_box)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return {'vehicleLightType':self.vehicle_light_type_combo_box.currentText()}
    
    def get_data(self):
        return VehicleLight({'vehicleLightType':self.vehicle_light_type_combo_box.currentText()})

class UserDefinedLightWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.userDefinedLightType = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('UserDefinedLightType:', self.userDefinedLightType)
        self.setLayout(form_layout)
        
    def get_elements(self):
        return clean_empty({'userDefinedLightType':self.userDefinedLightType.text()})
    
    def get_data(self):
        attrib = clean_empty({'userDefinedLightType':self.userDefinedLightType.text()})
        return UserDefinedLight(attrib)

class ColorRgbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        color_validator = QDoubleValidator(bottom=0, top=1, decimals=3, notation=QDoubleValidator.StandardNotation)
        self.blue = QLineEdit()
        self.blue.setValidator(color_validator)
        self.blue.setPlaceholderText('Range: [0..1]') 
        self.green = QLineEdit()
        self.green.setValidator(color_validator)
        self.green.setPlaceholderText('Range: [0..1]')
        self.red = QLineEdit()
        self.red.setValidator(color_validator)
        self.red.setPlaceholderText('Range: [0..1]')
        form_layout = QFormLayout()
        form_layout.addRow('Red:', self.red)
        form_layout.addRow('Green:', self.green)
        form_layout.addRow('Blue:', self.blue)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'red':self.red.text(), 'green':self.green.text(), 'blue':self.blue.text()})
    
    def get_data(self):
        attrib = clean_empty({'red':self.red.text(), 'green':self.green.text(), 'blue':self.blue.text()})
        return ColorRgb(attrib)

class ColorCmykWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        color_validator = QDoubleValidator(bottom=0, top=1, decimals=3, notation=QDoubleValidator.StandardNotation)
        self.cyan = QLineEdit()
        self.cyan.setValidator(color_validator)
        self.cyan.setPlaceholderText('Range: [0..1]')
        self.key = QLineEdit()
        self.key.setValidator(color_validator)
        self.key.setPlaceholderText('Range: [0..1]')
        self.magenta = QLineEdit()
        self.magenta.setValidator(color_validator)
        self.magenta.setPlaceholderText('Range: [0..1]')
        self.yellow = QLineEdit()
        self.yellow.setValidator(color_validator)
        self.yellow.setPlaceholderText('Range: [0..1]')
        form_layout = QFormLayout()
        form_layout.addRow('Cyan:', self.cyan)
        form_layout.addRow('Key:', self.key)
        form_layout.addRow('Magenta:', self.magenta)
        form_layout.addRow('Yellow:', self.yellow)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'cyan':self.cyan.text(), 'key':self.key.text(), 
                            'magenta':self.magenta.text(), 'yellow':self.yellow.text()})
    
    def get_data(self):
        attrib = clean_empty({'cyan':self.cyan.text(), 'key':self.key.text(), 
                              'magenta':self.magenta.text(), 'yellow':self.yellow.text()})
        return ColorCmyk(attrib)
    
class ColorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.color_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def color_info(self):
        main_widget = QWidget()
        color_type_list = [str(color_type.name) for color_type in ColorType]
        optional_color_list = ['colorRgb', 'colorCmyk']
        self.color_type_combo_box = QComboBox()
        self.color_type_combo_box.addItems(color_type_list)
        self.color_type_combo_box.setToolTip("Semantic value of the color.")
        self.color_schema_combo_box = QComboBox()
        self.color_schema_combo_box.addItems(optional_color_list)
        self.color_schema_combo_box.setToolTip("Color description in RGB or CMYK schema.")
        self.color_schema_combo_box.activated[str].connect(self.update_optional_color)
        
        self.color_schema_widget = QStackedWidget()
        self.color_rgb_widget = ColorRgbWidget()
        self.color_cymk_widget = ColorCmykWidget()
        self.color_schema_widget.addWidget(self.color_rgb_widget)
        self.color_schema_widget.addWidget(self.color_cymk_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('ColorType:', self.color_type_combo_box)
        form_layout.addRow('ColorScehma:', self.color_schema_combo_box)
        form_layout.addWidget(self.color_schema_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def update_optional_color(self, choice):
        if choice == 'colorRgb':
            self.color_schema_widget.setCurrentWidget(self.color_rgb_widget)
        else:
            self.color_schema_widget.setCurrentWidget(self.color_cymk_widget)
    
    def get_elements(self):
        if self.color_schema_combo_box.currentText() == 'colorRgb':
            return {'ColorType':self.color_type_combo_box.currentText(), 
                    'ColorRgb':self.color_rgb_widget.get_elements(), 
                    'ColorCymk':None}
        else:
            return {'ColorType':self.color_type_combo_box.currentText(), 
                    'ColorRgb':None, 
                    'ColorCymk':self.color_cymk_widget.get_elements()}

    def get_data(self):
        attrib = {'colorType':self.color_type_combo_box.currentText()}
        if self.color_schema_combo_box.currentText() == 'colorRgb':
            return Color(attrib, self.color_rgb_widget.get_data(), None)
        else:
            return Color(attrib, None, self.color_cymk_widget.get_data())
    
class LightStateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.light_state_info(), 0, 0)
        self.set_default_color_info_widget()
        self.setLayout(grid_layout)
        
    def light_state_info(self):
        main_widget = QWidget()
        default_double_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.flashingOffDuration = QLineEdit()
        self.flashingOffDuration.setValidator(default_double_validator)
        self.flashingOffDuration.setPlaceholderText('Range [0..inf]')
        self.flashingOffDuration.setToolTip("When mode is set to flashing, this attribute describes the duration of the 'off' phase of the flashing")
        self.flashingOnDuration = QLineEdit()
        self.flashingOnDuration.setValidator(default_double_validator)
        self.flashingOnDuration.setPlaceholderText('Range [0..inf]')
        self.flashingOnDuration.setToolTip("When mode is set to flashing, this attribute describes the duration of the 'on' phase of the flashing")
        self.luminousIntensity = QLineEdit()
        self.luminousIntensity.setValidator(default_double_validator)
        self.luminousIntensity.setPlaceholderText('Range [0..inf]')
        self.luminousIntensity.setToolTip("Luminous intensity of the light")
        mode_list = [str(light_mode.name) for light_mode in LightMode]
        self.light_mode_combo_box = QComboBox()
        self.light_mode_combo_box.addItems(mode_list)

        self.checkbox = QCheckBox()
        color_lablel = QLabel('Color')
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(color_lablel)
        self.checkbox.stateChanged.connect(self.update_color_info)
        # self.color_combo_box = QComboBox()
        # self.color_combo_box.addItems(color_list)
        # self.color_combo_box.activated[str].connect(self.update_color_info)
        self.hbox = QVBoxLayout()
        self.color_widget = ColorWidget()
        self.hbox.addWidget(self.color_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('FlashingOffDuration(s):', self.flashingOffDuration)
        form_layout.addRow('FlashingOnDuration(s):', self.flashingOnDuration)
        form_layout.addRow('LuminousIntensity(s):', self.luminousIntensity)
        form_layout.addRow('Mode:', self.light_mode_combo_box)

        form_layout2 = QFormLayout()
        form_layout2.addRow(container, self.checkbox)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(form_layout2)
        vbox.addLayout(self.hbox)
        main_widget.setLayout(vbox)
        return main_widget

    def set_default_color_info_widget(self):
        self.hide_all_widgets()
        self.color_widget.setVisible(False)
    
    def hide_all_widgets(self):
        for i in range(0, self.hbox.count()):
            self.hbox.itemAt(i).widget().hide()
    
    def update_color_info(self, state):
        self.hide_all_widgets()
        if state == Qt.Checked:
            self.color_widget.show()
        else:
            self.color_widget.hide()
    
    def get_color_info_elements(self):
        if self.checkbox.isChecked():
            return self.color_widget.get_elements()
        else:
            return None
        
    def get_color_info_data(self):
        if self.checkbox.isChecked():
            return self.color_widget.get_data()
        else:
            return None
        
    def get_elements(self):
        return clean_empty({'flashingOffDuration':self.flashingOffDuration.text(),
                             'flashingOnDuration':self.flashingOnDuration.text(),
                             'luminousIntensity':self.luminousIntensity.text(),
                             'mode':self.light_mode_combo_box.currentText(),
                             'color':self.get_color_info_elements()})
    
    def get_data(self):
        attrib = clean_empty({'flashingOffDuration':self.flashingOffDuration.text(),
                             'flashingOnDuration':self.flashingOnDuration.text(),
                             'luminousIntensity':self.luminousIntensity.text(),
                             'mode':self.light_mode_combo_box.currentText()})
        return LightState(attrib, color=self.get_color_info_data())
        
class LightStateActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.light_state_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def light_state_action_info(self):
        main_widget = QWidget()
        self.transitionTime = QLineEdit()
        self.transitionTime.setValidator(QDoubleValidator(bottom=0, decimals=3, notation=QDoubleValidator.StandardNotation))
        self.transitionTime.setPlaceholderText('Range [0..inf]')
        light_type_list = ['vehicleLight', 'userDefinedLight']
        self.light_type_combo_box = QComboBox()
        self.light_type_combo_box.addItems(light_type_list)
        self.light_type_combo_box.setToolTip('Reference to a certain light of a entity that will be addressed in this LightStateAction')
        self.light_type_combo_box.activated[str].connect(self.update_light_type)
        
        self.light_type_widget = QStackedWidget()
        self.vehicle_light_type_widget = VehicleLightWidget()
        self.user_defined_light_type_widget = UserDefinedLightWidget()
        self.light_type_widget.addWidget(self.vehicle_light_type_widget)
        self.light_type_widget.addWidget(self.user_defined_light_type_widget)
        self.light_state_widget = LightStateWidget()
        form_layout = QFormLayout()
        form_layout.addRow('TransitionTime(s):', self.transitionTime)
        form_layout.addRow('LightType:', self.light_type_combo_box)
        form_layout.addWidget(self.light_type_widget)
        form_layout.addRow('LightState:',self.light_state_widget)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def update_light_type(self, choice):
        if choice == 'vehicleLight':
            self.light_type_widget.setCurrentWidget(self.vehicle_light_type_widget)
        else:
            self.light_type_widget.setCurrentWidget(self.user_defined_light_type_widget)
    
    def get_light_type_elements(self):
        if self.light_type_combo_box.currentText() == 'vehicleLight':
            return self.vehicle_light_type_widget.get_elements()
        else:
            return self.user_defined_light_type_widget.get_elements()
        
    def get_light_type_data(self):
        if self.light_type_combo_box.currentText() == 'vehicleLight':
            return LightType(self.vehicle_light_type_widget.get_data(), None)
        else:
            return LightType(None, self.user_defined_light_type_widget.get_data())
    
    def get_elements(self):
        return clean_empty({'transitionTime':self.transitionTime.text(), 
                            'lightType':self.get_light_type_elements(),
                            'lightState':self.light_state_widget.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'transitionTime':self.transitionTime.text()})
        return LightStateAction(attrib, self.get_light_type_data(), self.light_state_widget.get_data())

class VehicleComponentTypeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        vehicle_component_type_list = [str(vc_type.name) for vc_type in VehicleComponentType]
        self.vehicle_component_type_combo_box = QComboBox()
        self.vehicle_component_type_combo_box.addItems(vehicle_component_type_list)
        form_layout = QFormLayout()
        form_layout.addRow('VehicleComponentType:', self.vehicle_component_type_combo_box)
        self.setLayout(form_layout)
        
    def get_elements(self):
        return {'vehicleComponentType':self.vehicle_component_type_combo_box.currentText()}
    
    def get_data(self):
        return VehicleComponent({'vehicleComponentType':self.vehicle_component_type_combo_box.currentText()})

class UserDefinedComponentTypeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.userDefinedComponentType = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('UserDefinedComponentType', self.userDefinedComponentType)
        self.setLayout(form_layout)

    def get_elements(self):
        return clean_empty({'userDefinedComponentType':self.userDefinedComponentType.text()})
    
    def get_data(self):
        return UserDefinedComponent(clean_empty({'userDefinedComponentType':self.userDefinedComponentType.text()}))
        
class ComponentAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.component_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def component_info(self):
        main_widget = QWidget()
        component_animation_type_list = ['vehicleComponent', 'userDefinedComponent']
        self.component_animation_type_combo_box = QComboBox()
        self.component_animation_type_combo_box.addItems(component_animation_type_list)
        self.component_animation_type_combo_box.activated[str].connect(self.update_component_type)
        
        self.component_animation_type_widget = QStackedWidget()
        self.vehicle_component_widget = VehicleComponentTypeWidget()
        self.user_defined_component_widget = UserDefinedComponentTypeWidget()
        self.component_animation_type_widget.addWidget(self.vehicle_component_widget)
        self.component_animation_type_widget.addWidget(self.user_defined_component_widget)
        form_layout = QFormLayout()
        form_layout.addRow('ComponentAnimation:', self.component_animation_type_combo_box)
        form_layout.addWidget(self.component_animation_type_widget)
        main_widget.setLayout(form_layout)
        return main_widget
        
    def update_component_type(self, choice):
        if choice == 'vehicleComponent':
            self.component_animation_type_widget.setCurrentWidget(self.vehicle_component_widget)
        else:
            self.component_animation_type_widget.setCurrentWidget(self.user_defined_component_widget)
    
    def get_elements(self):
        if self.component_animation_type_combo_box.currentText() == 'vehicleComponent':
            return {'vehicleComponent':self.vehicle_component_widget.get_elements()}
        else:
            return {'userDefinedComponent':self.user_defined_component_widget.get_elements()}
    
    def get_data(self):
        if self.component_animation_type_combo_box.currentText() == 'vehicleComponent':
            return ComponentAnimation(component=self.vehicle_component_widget.get_data())
        else:
            return ComponentAnimation(component=self.user_defined_component_widget.get_data())

class PedestrianAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.pedestrian_animation_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def pedestrian_animation_info(self):
        main_widget = QWidget()
        motion_list = [str(motion.name) for motion in PedestrianMotionType]
        self.motion_combo_box = QComboBox()
        self.motion_combo_box.addItems(motion_list)
        self.user_defined_pedestrian_animation = QLineEdit()
        gesture_list = [str(gesture.name) for gesture in PedestrianGestureType]
        gesture_list.insert(0, "")
        self.gesture_combo_box = QComboBox()
        self.gesture_combo_box.addItems(gesture_list)
        
        form_layout = QFormLayout()
        form_layout.addRow("Motion:",self.motion_combo_box)
        form_layout.addRow("UserDefinedPedestrianAnimation:", self.user_defined_pedestrian_animation)
        form_layout.addRow("Gesture:", self.gesture_combo_box)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'motion':self.motion_combo_box.currentText(), 
                            'userDefinedPedestrianAnimation':self.user_defined_pedestrian_animation.text(),
                            'gesture':self.gesture_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'motion':self.motion_combo_box.currentText(), 
                              'userDefinedPedestrianAnimation':self.user_defined_pedestrian_animation.text()})
        gesture = [PedestrianGesture({'gesture':self.gesture_combo_box.currentText()})]
        return PedestrianAnimation(attrib, gesture)
    
class AnimationFileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.animation_file_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def animation_file_info(self):
        main_widget = QWidget()
        default_double_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        self.timeOffset = QLineEdit()
        self.timeOffset.setValidator(default_double_validator)
        self.timeOffset.setPlaceholderText('Range [0..inf]')
        self.file = FileWidget()
        form_layout = QFormLayout()
        form_layout.addRow('TimeOffset(s):', self.timeOffset)
        form_layout.addRow('File:', self.file)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'timeOffset':self.timeOffset.text(), 'file':self.file.get_elements()})
    
    def get_data(self):
        attrib = clean_empty({'timeOffset':self.timeOffset.text()})
        return AnimationFile(attrib, self.file.get_data())
    
class UserDefinedAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.user_defined_animation_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def user_defined_animation_info(self):
        main_widget = QWidget()
        self.user_defined_animation_type = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('UserDefinedAnimationType:', self.user_defined_animation_type)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'userDefinedAnimationType':self.user_defined_animation_type.text()})
    
    def get_data(self):
        attrib = clean_empty({'userDefinedAnimationType':self.user_defined_animation_type.text()})
        return UserDefinedAnimation(attrib)

class AnimationStateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.animation_state_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def animation_state_info(self):
        main_widget = QWidget()
        double_validator = QDoubleValidator(bottom=0, top=1, decimals=3, notation=QDoubleValidator.StandardNotation)
        self.animation_state = QLineEdit()
        self.animation_state.setValidator(double_validator)
        self.animation_state.setPlaceholderText('Range [0..1]')
        self.animation_state.setToolTip('The goal state of a component after the AnimationStateAction is executed')
        form_layout = QFormLayout()
        form_layout.addRow('State:', self.animation_state)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'state':self.animation_state.text()})
    
    def get_data(self):
        attrib = clean_empty({'state':self.animation_state.text()})
        return AnimationState(attrib)

class AnimationActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.animation_action_info(), 0, 0)
        self.set_default_animation_state_widget()
        self.setLayout(grid_layout)
    
    def animation_action_info(self):
        main_widget = QWidget()
        self.animationDuration = QLineEdit()
        self.animationDuration.setValidator(QDoubleValidator(bottom=0, top=1, decimals=3, notation=QDoubleValidator.StandardNotation))
        self.animationDuration.setPlaceholderText('Range [0..inf]')
        self.loop_combo_box = QComboBox()
        self.loop_combo_box.setToolTip("If set to true, the animation will be looped. Default if omitted: false.")
        self.loop_combo_box.addItems(BOOLEAN_TYPE_LIST)
        animation_type_list = ['componentAnimation', 'pedestrianAnimation', 'animationFile', 'userDefinedAnimation']
        self.animation_type_combo_box = QComboBox()
        self.animation_type_combo_box.addItems(animation_type_list)
        self.animation_type_combo_box.activated[str].connect(self.update_animation_type)
        self.animation_state = QLineEdit()
        
        # Animation Type
        self.animation_type_widget = QStackedWidget()
        self.component_animation_widget = ComponentAnimationWidget()
        self.pedestrian_animation_widget = PedestrianAnimationWidget()
        self.animation_file_widget = AnimationFileWidget()
        self.user_defined_animation_widget = UserDefinedAnimationWidget()
        self.animation_type_widget.addWidget(self.component_animation_widget)
        self.animation_type_widget.addWidget(self.pedestrian_animation_widget)
        self.animation_type_widget.addWidget(self.animation_file_widget)
        self.animation_type_widget.addWidget(self.user_defined_animation_widget)
        
        #Animation State
        animation_state_list = ["", "animationState"]
        self.animation_state_combo_box = QComboBox()
        self.animation_state_combo_box.addItems(animation_state_list)
        self.animation_state_combo_box.activated[str].connect(self.update_animation_state)
        self.animation_state_layout = QVBoxLayout()
        self.animation_state_widget = AnimationStateWidget()
        self.animation_state_layout.addWidget(self.animation_state_widget)
        
        vbox = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.addRow('AnimationDuration(s):', self.animationDuration)
        form_layout.addRow('Loop:', self.loop_combo_box)
        form_layout.addRow('AnimationType:', self.animation_type_combo_box)
        form_layout.addWidget(self.animation_type_widget)
        vbox.addLayout(form_layout)
        
        form_layout1 = QFormLayout()
        form_layout1.addRow('AnimationState:', self.animation_state_combo_box)
        form_layout1.addWidget(self.animation_state_widget)
        vbox.addLayout(form_layout1)
        main_widget.setLayout(vbox)
        return main_widget
    
    def set_default_animation_state_widget(self):
        self.hide_all_animation_state_widgets()
        self.animation_state_widget.setVisible(False)

    def hide_all_animation_state_widgets(self):
        for i in range(self.animation_state_layout.count()):
            self.animation_state_layout.itemAt(i).widget().setVisible(False)
    
    def update_animation_state(self):
        if self.animation_state_combo_box.currentText() == "animationState":
            self.animation_state_widget.setVisible(True)
        else:
            self.animation_state_widget.setVisible(False)   
    
    def update_animation_type(self):
        if self.animation_type_combo_box.currentText() == 'componentAnimation':
            self.animation_type_widget.setCurrentWidget(self.component_animation_widget)
        elif self.animation_type_combo_box.currentText() == 'pedestrianAnimation':
            self.animation_type_widget.setCurrentWidget(self.pedestrian_animation_widget)
        elif self.animation_type_combo_box.currentText() == 'animationFile':
            self.animation_type_widget.setCurrentWidget(self.animation_file_widget)
        else:
            self.animation_type_widget.setCurrentWidget(self.user_defined_animation_widget)
    
    def get_animation_type_data(self):
        if self.animation_type_combo_box.currentText() == 'componentAnimation':
            return AnimationType(self.component_animation_widget.get_data())
        elif self.animation_type_combo_box.currentText() == 'pedestrianAnimation':
            return AnimationType(self.pedestrian_animation_widget.get_data())
        elif self.animation_type_combo_box.currentText() == 'animationFile':
            return AnimationType(self.animation_file_widget.get_data())
        else:
            return AnimationType(self.user_defined_animation_widget.get_data())
    
    def get_animation_state(self):
        if self.animation_state_combo_box.currentText() == "animationState":
            return self.animation_state_widget.get_data()
        else:
            return None
    
    def get_elements(self):
        attrib = clean_empty({'animationDuration':self.animationDuration.text(),
                              'loop':self.loop_combo_box.currentText(),
                              'animationType':self.animation_type_combo_box.currentText(),
                              'animationState':self.animation_state_combo_box.currentText()})
        return attrib
    
    def get_data(self):
        attrib = clean_empty({'animationDuration':self.animationDuration.text(),
                              'loop':self.loop_combo_box.currentText()})
        return AnimationAction(attrib, self.get_animation_type_data(), self.get_animation_state())

class AppearanceActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.appearance_action_info(), 0, 0)
        self.setLayout(grid_layout)

    def appearance_action_info(self):
        groupbox = QGroupBox('AppearanceAction')
        appearance_action_type_list = ['lightStateAction', 'animationAction']
        self.appearance_action_type_combo_box = QComboBox()
        self.appearance_action_type_combo_box.addItems(appearance_action_type_list)
        self.appearance_action_type_combo_box.activated[str].connect(self.update_action)

        self.appearance_action_widget = QStackedWidget()
        self.light_state_action_widget = LightStateActionWidget()
        self.animation_action_widget = AnimationActionWidget()
        self.appearance_action_widget.addWidget(self.light_state_action_widget)
        self.appearance_action_widget.addWidget(self.animation_action_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.appearance_action_type_combo_box)
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.appearance_action_widget)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        groupbox.setLayout(vbox)
        return groupbox
        
    def update_action(self, choice):
        if choice == 'lightStateAction':
            self.appearance_action_widget.setCurrentWidget(self.light_state_action_widget)
        else:
            self.appearance_action_widget.setCurrentWidget(self.animation_action_widget)
    
    def get_elements(self):
        if self.appearance_action_type_combo_box.currentText() == 'lightStateAction':
            return self.light_state_action_widget.get_elements()
        else:
            return self.animation_action_widget.get_elements()
    
    def get_data(self):
        if self.appearance_action_type_combo_box.currentText() == 'lightStateAction':
            return AppearanceAction(self.light_state_action_widget.get_data())
        else:
            return AppearanceAction(self.animation_action_widget.get_data())
        
class ParkingActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.parking_action_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def parking_action_info(self):
        groupbox = QGroupBox('ParkingAction')
        self.name = QLineEdit()
        self.name.setToolTip('ID of the parking space in MGeo.')
        self.name.setPlaceholderText('Parking space ID in MGeo')
        parking_type_list = ['front', 'rear', 'parallel']
        self.parking_type_combo_box = QComboBox()
        self.parking_type_combo_box.setToolTip('Parking methods ("parallel", "rear", "front")')
        self.parking_type_combo_box.addItems(parking_type_list)
        action_list = ['park', 'exit']
        self.parking_action_combo_box = QComboBox()
        self.parking_action_combo_box.setToolTip('“park”: to park at the parking space “exit”: to exit from the parking space')
        self.parking_action_combo_box.addItems(action_list)
        
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('Type:', self.parking_type_combo_box)
        form_layout.addRow('Action:', self.parking_action_combo_box)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 
                            'type':self.parking_type_combo_box.currentText(), 
                            'action':self.parking_action_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 
                              'type':self.parking_type_combo_box.currentText(), 
                              'action':self.parking_action_combo_box.currentText()})
        return ParkingAction(attrib)

class DamageActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        damage_type_list = ['fire']
        self.damage_type_combo_box = QComboBox()
        self.damage_type_combo_box.setToolTip('Damage Type (fire)')
        self.damage_type_combo_box.addItems(damage_type_list)
        form_layout = QFormLayout()
        form_layout.addRow('DamageType:', self.damage_type_combo_box)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return {'type':self.damage_type_combo_box.currentText()}
    
    def get_data(self):
        attrib = {'type':self.damage_type_combo_box.currentText()}
        return DamageAction(attrib)
        
class InoperabilityActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        fault_type_list = ['accel', 'brake', 'steer']
        self.fault_type_combo_box = QComboBox()
        self.fault_type_combo_box.setToolTip('Fault type (accel, brake, steer)')
        self.fault_type_combo_box.addItems(fault_type_list)
        form_layout = QFormLayout()
        form_layout.addRow('FaultType:', self.fault_type_combo_box)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return {'faultType':self.fault_type_combo_box.currentText()}
    
    def get_data(self):
        attrib = {'type':self.fault_type_combo_box.currentText()}
        return InoperabilityAction(attrib)
    
class SensorFaultActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        default_double_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.name = QLineEdit()
        self.offsetX = QLineEdit()
        self.offsetX.setValidator(default_double_validator)
        self.offsetX.setPlaceholderText('Range [-inf..inf]')
        self.offsetY = QLineEdit()
        self.offsetY.setValidator(default_double_validator)
        self.offsetY.setPlaceholderText('Range [-inf..inf]')
        self.offsetZ = QLineEdit()
        self.offsetZ.setValidator(default_double_validator)
        self.offsetZ.setPlaceholderText('Range [-inf..inf]')
        self.offsetP = QLineEdit()
        self.offsetP.setValidator(default_double_validator)
        self.offsetP.setPlaceholderText('Range [-inf..inf]')
        self.offsetQ = QLineEdit()
        self.offsetQ.setValidator(default_double_validator)
        self.offsetQ.setPlaceholderText('Range [-inf..inf]')
        self.offsetR = QLineEdit()
        self.offsetR.setValidator(default_double_validator)
        self.offsetR.setPlaceholderText('Range [-inf..inf]')
        
        form_layout = QFormLayout()
        form_layout.addRow('name:', self.name)
        form_layout.addRow('offsetX:', self.offsetX)
        form_layout.addRow('offsetY:', self.offsetY)
        form_layout.addRow('offsetZ:', self.offsetZ)
        form_layout.addRow('offsetP:', self.offsetP)
        form_layout.addRow('offsetQ:', self.offsetQ)
        form_layout.addRow('offsetR:', self.offsetR)
        self.setLayout(form_layout)
        
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 'offsetX':self.offsetX.text(), 'offsetY':self.offsetY.text(),
                            'offsetZ':self.offsetZ.text(), 'offsetP':self.offsetP.text(), 'offsetQ':self.offsetQ.text(),
                            'offsetR':self.offsetR.text()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 'offsetX':self.offsetX.text(), 'offsetY':self.offsetY.text(),
                            'offsetZ':self.offsetZ.text(), 'offsetP':self.offsetP.text(), 'offsetQ':self.offsetQ.text(),
                            'offsetR':self.offsetR.text()})
        return SensorFaultAction(attrib)

class SteeringDisturbanceActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = QLineEdit()
        self.duration.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.magnitude = QLineEdit()
        self.magnitude.setValidator(QDoubleValidator(bottom=-1, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.magnitude.setPlaceholderText('Range: [-1..1]')
        
        form_layout = QFormLayout()
        form_layout.addRow('Duration(s):', self.duration)
        form_layout.addRow('Magnitude:', self.magnitude)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'duration':self.duration.text(), 'magnitude':self.magnitude.text()})
    
    def get_data(self):
        attrib = clean_empty({'duration':self.duration.text(), 'magnitude':self.magnitude.text()})
        return SteeringDisturbanceAction(attrib)
    
class TireFaultActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        tire_list = ['0', '1', '2', '3']
        self.tire_combo_box = QComboBox()
        self.tire_combo_box.addItems(tire_list)
        self.tire_combo_box.setToolTip('Index of a tire of the actors')
        form_layout = QFormLayout()
        form_layout.addRow('TireIndex:', self.tire_combo_box)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return {'tireIndex':self.tire_combo_box.currentText()}

    def get_data(self):
        attrib = {'tire':self.tire_combo_box.currentText()}
        return TireFaultAction(attrib)

class FaultInjectionActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.falut_injection_action_info(), 0, 0)
        self.set_default_fault_injection_action_widget()
        self.setLayout(grid_layout)
    
    def falut_injection_action_info(self):
        groupbox = QGroupBox('FaultInjectionAction')
        fault_injection_action_list = ['damageAction', 'inoperabilityAction', 'sensorFaultAction', 'steeringDisturbanceAction', 'tireFaultAction']
        self.fault_injection_action_type_combo_box = QComboBox()
        self.fault_injection_action_type_combo_box.addItems(fault_injection_action_list)
        self.fault_injection_action_type_combo_box.activated[str].connect(self.update_action)
        
        self.fault_injection_action_layout = QVBoxLayout()
        self.damageAction_widget = DamageActionWidget()
        self.inoperabilityAction_widget = InoperabilityActionWidget()
        self.sensorFaultAction_widget = SensorFaultActionWidget()
        self.steeringDisturbanceAction_widget = SteeringDisturbanceActionWidget()
        self.tireFaultAction_widget = TireFaultActionWidget()
        self.fault_injection_action_layout.addWidget(self.damageAction_widget)
        self.fault_injection_action_layout.addWidget(self.inoperabilityAction_widget)
        self.fault_injection_action_layout.addWidget(self.sensorFaultAction_widget)
        self.fault_injection_action_layout.addWidget(self.steeringDisturbanceAction_widget)
        self.fault_injection_action_layout.addWidget(self.tireFaultAction_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.fault_injection_action_type_combo_box)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(self.fault_injection_action_layout)
        groupbox.setLayout(vbox)
        return groupbox
    
    def update_action(self, choice):
        self.hide_all_fault_injection_action_widgets()
        if choice == 'damageAction':
            self.damageAction_widget.setVisible(True)
        elif choice == 'inoperabilityAction':
            self.inoperabilityAction_widget.setVisible(True)
        elif choice == 'sensorFaultAction':
            self.sensorFaultAction_widget.setVisible(True)
        elif choice == 'steeringDisturbanceAction':
            self.steeringDisturbanceAction_widget.setVisible(True)
        elif choice == 'tireFaultAction':
            self.tireFaultAction_widget.setVisible(True)
        else:
            self.hide_all_fault_injection_action_widgets()
    
    def set_default_fault_injection_action_widget(self):
        self.hide_all_fault_injection_action_widgets()
        self.damageAction_widget.setVisible(True)
    
    def hide_all_fault_injection_action_widgets(self):
        for i in range(self.fault_injection_action_layout.count()):
            self.fault_injection_action_layout.itemAt(i).widget().setVisible(False)

    def get_elements(self):
        if self.fault_injection_action_type_combo_box.currentText() == 'damageAction':
            return self.damageAction_widget.get_elements()
        elif self.fault_injection_action_type_combo_box.currentText() == 'inoperabilityAction':
            return self.inoperabilityAction_widget.get_elements()
        elif self.fault_injection_action_type_combo_box.currentText() == 'sensorFaultAction':
            return self.sensorFaultAction_widget.get_elements()
        elif self.fault_injection_action_type_combo_box.currentText() == 'steeringDisturbanceAction':
            return self.steeringDisturbanceAction_widget.get_elements()
        else:
            return self.tireFaultAction_widget.get_elements()
    
    def get_data(self):
        if self.fault_injection_action_type_combo_box.currentText() == 'damageAction':
            return FaultInjectionAction(self.damageAction_widget.get_data())
        elif self.fault_injection_action_type_combo_box.currentText() == 'inoperabilityAction':
            return FaultInjectionAction(self.inoperabilityAction_widget.get_data())
        elif self.fault_injection_action_type_combo_box.currentText() == 'sensorFaultAction':
            return FaultInjectionAction(self.sensorFaultAction_widget.get_data())
        elif self.fault_injection_action_type_combo_box.currentText() == 'steeringDisturbanceAction':
            return FaultInjectionAction(self.steeringDisturbanceAction_widget.get_data())
        else:
            return FaultInjectionAction(self.tireFaultAction_widget.get_data())

class CreatePuddleActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        negative_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        degree_validator = QDoubleValidator(bottom=0, top=360, decimals=8, notation=QDoubleValidator.StandardNotation)
        self.name = QLineEdit()
        self.positionX = QLineEdit()
        self.positionX.setValidator(negative_validator)
        self.positionX.setPlaceholderText('Range: [-inf..inf]')
        self.positionY = QLineEdit()
        self.positionY.setValidator(negative_validator)
        self.positionY.setPlaceholderText('Range: [-inf..inf]')
        self.positionZ = QLineEdit()
        self.positionZ.setValidator(negative_validator)
        self.positionZ.setPlaceholderText('Range: [-inf..inf]')
        self.rotationX = QLineEdit()
        self.rotationX.setValidator(degree_validator)
        self.rotationX.setPlaceholderText('Range: [0..360]')
        self.rotationY = QLineEdit()
        self.rotationY.setValidator(degree_validator)
        self.rotationY.setPlaceholderText('Range: [0..360]')
        self.rotationZ = QLineEdit()
        self.rotationZ.setValidator(degree_validator)
        self.rotationZ.setPlaceholderText('Range: [0..360]')
        self.radiusH = QLineEdit()
        self.radiusH.setValidator(nonnegative_validator)
        self.radiusH.setPlaceholderText('Range: [0..inf]')
        self.radiusV = QLineEdit()
        self.radiusV.setValidator(nonnegative_validator)
        self.radiusV.setPlaceholderText('Range: [0..inf]')
        self._height = QLineEdit()
        self._height.setValidator(nonnegative_validator)
        self._height.setPlaceholderText('Range: [0..inf]')
        self.friction = QLineEdit()
        self.friction.setValidator(QDoubleValidator(bottom=0, top=1, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.friction.setPlaceholderText('Range: [0..1]')
        
        form_layout = QFormLayout()
        form_layout.addRow('name:', self.name)
        form_layout.addRow('positionX(m):', self.positionX)
        form_layout.addRow('positionY(m):', self.positionY)
        form_layout.addRow('positionZ(m):', self.positionZ)
        form_layout.addRow('rotationX(deg):', self.rotationX)
        form_layout.addRow('rotationY(deg):', self.rotationY)
        form_layout.addRow('rotationZ(deg):', self.rotationZ)
        form_layout.addRow('radiusH(m):', self.radiusH)
        form_layout.addRow('radiusV(m):', self.radiusV)
        form_layout.addRow('height(m):', self._height)
        form_layout.addRow('friction', self.friction)
        
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 'positionX':self.positionX.text(), 'positionY':self.positionY.text(),
                            'positionZ':self.positionZ.text(), 'rotationX':self.rotationX.text(), 'rotationY':self.rotationY.text(), 
                            'rotationZ':self.rotationZ.text(), 'radiusH':self.radiusH.text(), 'radiusV':self.radiusV.text(),
                            'height':self._height.text(), 'friction':self.friction.text()})
        
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 'positionX':self.positionX.text(), 'positionY':self.positionY.text(),
                            'positionZ':self.positionZ.text(), 'rotationX':self.rotationX.text(), 'rotationY':self.rotationY.text(), 
                            'rotationZ':self.rotationZ.text(), 'radiusH':self.radiusH.text(), 'radiusV':self.radiusV.text(),
                            'height':self._height.text(), 'friction':self.friction.text()})
        return CreatePuddleAction(attrib)

class CreateMapObjectActionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.create_map_object_action_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def create_map_object_action_info(self):
        groupbox = QGroupBox('CreateMapObjectAction')
        action_type_list = ['createPuddleAction'] # 추후에 추가 가능
        self.create_map_object_action_combo_box = QComboBox()
        self.create_map_object_action_combo_box.addItems(action_type_list)
        self.create_map_object_action_combo_box.activated[str].connect(self.update_action)
    
        self.create_map_object_action_widget = QStackedWidget()
        self.create_pudde_action_widget = CreatePuddleActionWidget()
        self.create_map_object_action_widget.addWidget(self.create_pudde_action_widget)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.create_map_object_action_combo_box)
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.create_map_object_action_widget)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        groupbox.setLayout(vbox)
        return groupbox
        
    def update_action(self, choice):
        if choice == 'createPuddleAction':
            self.create_map_object_action_widget.setCurrentWidget(self.create_pudde_action_widget)
            
    def get_elements(self):
        if self.create_map_object_action_combo_box.currentText() == 'createPuddleAction':
            return self.create_pudde_action_widget.get_elements()
    
    def get_data(self):
        if self.create_map_object_action_combo_box.currentText() == 'createPuddleAction':
            return CreateMapObjectAction(self.create_pudde_action_widget.get_data())
    
# Condition UI
# ByValueCondition UI
class ParameterConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.parameter_condition_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def parameter_condition_info(self):
        groupbox = QGroupBox('ParameterCondition')
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        
        self.parameter_ref = QLineEdit()
        self.value = QLineEdit()
        self.value.setToolTip('Value of the parameter.')
        
        form_layout = QFormLayout()
        form_layout.addRow('ParameterRef:', self.parameter_ref)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value:', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'parameterRef':self.parameter_ref.text(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text()
                            })
    
    def get_data(self):
        attrib = clean_empty({'parameterRef':self.parameter_ref.text(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text()
                            })
        return ParameterCondition(attrib)
        
class TimeOfDayConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        "Comparison: true if the simulated time and date verifies the specified relation rule"
        "Comparison can be done after saving the data"
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.time_of_day_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def time_of_day_condition_info(self):
        groupbox = QGroupBox('TimeOfDayCondition')
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.dateTime = QDateTimeEdit()
        form_layout = QFormLayout()
        form_layout.addRow('dateTime:', self.dateTime)
        form_layout.addRow('Rule', self.rule_combo_box)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return {'dateTime':self.dateTime.dateTime().toString(Qt.ISODate), 'rule':self.rule_combo_box.currentText()}
    
    def get_data(self):
        attrib = {'dateTime':self.dateTime.dateTime().toString(Qt.ISODate), 'rule':self.rule_combo_box.currentText()}
        return TimeOfDayCondition(attrib)
        
class SimulationTimeConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.simulation_time_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def simulation_time_condition_info(self):
        groupbox = QGroupBox('SimulationTimeCondition')
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Time Value of the simulation time condition')
        
        form_layout = QFormLayout()
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(s):', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'value':self.value.text(), 'rule':self.rule_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'value':self.value.text(), 'rule':self.rule_combo_box.currentText()})
        return SimulationTimeCondition(attrib)
        
class StoryboardElementStateConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.storyboard_element_state_condition_info(), 0, 0)
        self.setLayout(grid_layout)

    def storyboard_element_state_condition_info(self):
        groupbox = QGroupBox('StoryboardElementStateCondition')
        storyboard_element_list = [str(story_et.name) for story_et in StoryboardElementType]
        # Transition states are not used currently
        storyboard_element_state_list = [str(StoryboardElementState.standbyState.name),
                                         str(StoryboardElementState.runningState.name),
                                         str(StoryboardElementState.completeState.name)]
        self.state_combo_box = QComboBox()
        self.state_combo_box.addItems(storyboard_element_state_list)
        self.element_combo_box = QComboBox()
        self.element_combo_box.addItems(storyboard_element_list)
        self.storyboardElementRef = QLineEdit()
        self.storyboardElementRef.setPlaceholderText('Name of the referenced Storyboard instance.')
        self.storyboardElementRef.setToolTip('Name of the referenced Storyboard instance.')

        form_layout = QFormLayout()
        form_layout.addRow('StoryboardElementRef:', self.storyboardElementRef)
        form_layout.addRow('StoryboardElementType', self.element_combo_box)
        form_layout.addRow('State:', self.state_combo_box)
        groupbox.setLayout(form_layout)
        return groupbox
        
    def get_elements(self):
        return clean_empty({'storyboardElementRef':self.storyboardElementRef.text(),
                            'storyboardElementType':self.element_combo_box.currentText(), 
                            'state':self.state_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'storyboardElementRef':self.storyboardElementRef.text(),
                              'storyboardElementType':self.element_combo_box.currentText(), 
                              'state':self.state_combo_box.currentText()})
        return StoryboardElementStateCondition(attrib)
    
class UserDefinedValueConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.user_defined_value_vondition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def user_defined_value_vondition_info(self):
        groupbox = QGroupBox('UserDefinedValueCondition')
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.name = QLineEdit()
        self.name.setPlaceholderText('Name of the external value.')
        self.name.setToolTip('Name of the external value.')
        self.value = QLineEdit()
        self.value.setPlaceholderText('Reference value the external value is compared to.')
        self.value.setToolTip('Reference value the external value is compared to.')
        
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value:', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text()})
        return UserDefinedValueCondition(attrib)

class TrafficSiganlConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_signal_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traffic_signal_condition_info(self):
        groupbox = QGroupBox('TrafficSignalCondition')
        self.name = QLineEdit()
        self.name.setPlaceholderText('ID of the referenced signal defined in a road network')
        self.state = QLineEdit()
        self.state.setPlaceholderText('State of the signal to be reached for the condition to become true.')
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.name)
        form_layout.addRow('State:', self.state)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'name':self.name.text(), 'state':self.state.text()})
    
    def get_data(self):
        attrib = clean_empty({'name':self.name.text(), 'state':self.state.text()})
        return TrafficSignalCondition(attrib)
    
class TrafficSignalControllerConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traffic_signal_controller_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traffic_signal_controller_condition_info(self):
        groupbox = QGroupBox('TrafficSignalControllerCondition')
        self.phase = QLineEdit()
        self.phase.setToolTip('Targeted phase of the signal controller')
        self.intersection_controller_id = QLineEdit()
        self.intersection_controller_id.setToolTip('ID of the intersection controller in MGeo.')
        
        form_layout = QFormLayout()
        form_layout.addRow('StartingPhase:', self.phase)
        form_layout.addRow('IntersectionControllerId:',self.intersection_controller_id)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_element(self):
        return clean_empty({'intersectionControllerId':self.intersection_controller_id.text(),
                            'phase':self.phase.text()})

    def get_data(self):
        attrib = clean_empty({ 'trafficSignalControllerRef':self.intersection_controller_id.text(), 'phase':self.phase.text()})
        return TrafficSignalControllerCondition(attrib)

class VariableConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.variable_condition_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def variable_condition_info(self):
        groupbox = QGroupBox('VariableCondition')
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        
        self.variable_ref = QLineEdit()
        self.value = QLineEdit()
        self.value.setToolTip('Value of the Variable.')
        
        form_layout = QFormLayout()
        form_layout.addRow('VariableRef:', self.variable_ref)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value:', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'variableRef':self.variable_ref.text(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text()
                           })
    
    def get_data(self):
        attrib = clean_empty({'variableRef':self.variable_ref.text(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text()
                             })
        return VariableCondition(attrib)
    

# ByEntityConditions
class TriggeringEntitiesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.triggering_entities_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def triggering_entities_info(self):
        main_widget = QWidget()
        #TODO: Cover multiple entityRefs Later
        self.entityRef = QLineEdit()
        triggering_entities_list = [str(te.name) for te in TriggeringEntitiesRule]
        self.triggering_entities_combo_box = QComboBox()
        self.triggering_entities_combo_box.addItems(triggering_entities_list)
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_combo_box)
        form_layout.addRow('EntityRef:', self.entityRef)
        main_widget.setLayout(form_layout)
        return main_widget
    
    def get_elements(self):
        return clean_empty({'triggeringEntitiesRule':self.triggering_entities_combo_box.currentText(),
                            'entityRef':self.entityRef.text()})
        
    def get_data(self):
        attrib = {'triggeringEntitiesRule':self.triggering_entities_combo_box.currentText()}
        entity_ref_attrib = clean_empty({'entityRef':self.entityRef.text()})
        return TriggeringEntities(attrib, [EntityRef(entity_ref_attrib)])

class EndOfRoadConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.end_of_road_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def end_of_road_condition_info(self):
        groupbox = QGroupBox('EndOfRoadCondition')
        self.duration = QLineEdit()
        self.duration.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.duration.setToolTip('Amount of time at end of road')
        self.duration.setPlaceholderText('Range: [0..inf]')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('Duration(s):', self.duration)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'duration':self.duration.text()})
    
    def get_data(self):
        attrib = clean_empty({'duration':self.duration.text()})
        return EndOfRoadCondition(attrib)
        
class CollisionConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.collision_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def collision_condition_info(self):
        groupbox = QGroupBox('CollisionCondition')
        byType_list = [str(object_type.name) for object_type in ObjectType]
        self.entityRef = QLineEdit()
        self.entityRef.setToolTip('Name of a specific entity.')
        self.entityRef.setPlaceholderText("If specified, 'type' would be ignored.")
        self.bytype_combo_box = QComboBox()
        self.bytype_combo_box.addItems(byType_list)
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('EntityRef:', self.entityRef)
        form_layout.addRow('byType:', self.bytype_combo_box)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'entityRef':self.entityRef.text(), 
                            'byType':self.bytype_combo_box.currentText()})
    
    def get_data(self):
        entity_ref_attrib = clean_empty({'entityRef':self.entityRef.text()})
        if entity_ref_attrib:
            return CollisionCondition(EntityRef(entity_ref_attrib), None)
        else:
            by_object_attrib = {'type':self.bytype_combo_box.currentText()}
            return CollisionCondition(None, ByObjectType(by_object_attrib))
    
class OffroadConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.off_road_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def off_road_condition_info(self):
        groupbox = QGroupBox('OffroadCondition')
        self.duration = QLineEdit()
        self.duration.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.duration.setToolTip('Amount of time of driving offroad')
        self.duration.setPlaceholderText('Range: [0..inf]')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('Duration(s):', self.duration)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'duration':self.duration.text()})
        
    def get_data(self):
        attrib = clean_empty({'duration':self.duration.text()})
        return OffroadCondition(attrib)
        
class TimeHeadwayConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.time_head_way_condition_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def time_head_way_condition_info(self):
        groupbox = QGroupBox('TimeHeadwayCondition')

        coordinate_system_list = [str(coordinate.name) for coordinate in CoordinateSystem]
        self.coordinate_system_combo_box = QComboBox()
        self.coordinate_system_combo_box.addItems(coordinate_system_list)
        self.coordinate_system_combo_box.setToolTip('Definition of the coordinate system to be used for calculations. If not provided the value is interpreted as "entity". If set, "alongRoute" is ignored.')
        self.entity_ref = QLineEdit()
        self.entity_ref.setToolTip('Reference entity to which the time headway is computed.')
        
        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.freespace_combo_box.setToolTip('True: time headway is measured using the distance between closest bounding box points. False: reference point distance is used.')
        
        relative_distance_type_list = [str(rdt.name) for rdt in RelativeDistanceType]
        self.relative_distance_type_combo_box = QComboBox()
        self.relative_distance_type_combo_box.addItems(relative_distance_type_list)
        self.relative_distance_type_combo_box.setCurrentIndex(relative_distance_type_list.index('euclideanDistance'))
        self.relative_distance_type_combo_box.setToolTip('Definition of the coordinate system dimension(s) to be used for calculating distances. If set "alongRoute" is ignored. If not provided, value is interpreted as "euclideanDistance".')
        
        routing_algorithm_list = [str(routing_algorithm.name) for routing_algorithm in RoutingAlgorithm]
        self.routing_algorithm_combo_box = QComboBox()
        self.routing_algorithm_combo_box.addItems(routing_algorithm_list)

        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setToolTip('The time headway value')
        self.value.setPlaceholderText('Range [0..inf]')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('CoordinateSystem:', self.coordinate_system_combo_box)
        form_layout.addRow('EntityRef:', self.entity_ref)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('RelativeDistanceType:', self.relative_distance_type_combo_box)
        form_layout.addRow('RoutingAlgorithm:', self.routing_algorithm_combo_box)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(s):', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
        
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'entityRef':self.entity_ref.text(),
                            'freespace':self.freespace_combo_box.currentText(),
                            'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text(),
                            'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                            'relativeDistanceType':self.relative_distance_type_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entity_ref.text(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text(),
                              'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                              'relativeDistanceType':self.relative_distance_type_combo_box.currentText()})
        return TimeHeadwayCondition(attrib)

class EntityRefWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entity_ref = QLineEdit()
        self.entity_ref.setToolTip('Reference entity')
        form_layout = QFormLayout()
        form_layout.addRow('EntityRef:', self.entity_ref)
        self.setLayout(form_layout)
    
    def get_elements(self):
        return clean_empty({'entityRef':self.entity_ref.text()})
    
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entity_ref.text()})
        return EntityRef(attrib)

class PositionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)

        self.position_widget = QStackedWidget()
        self.world_position = WorldPositionWidget()
        self.link_position = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position)
        self.position_widget.addWidget(self.relative_object_position)
        form_layout = QFormLayout()
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        self.setLayout(form_layout)
        
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()
        
    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
            
class TimeToCollisionConditionTargetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.time_to_collision_condition_target_info(), 0, 0)
        self.set_default_time_to_collision_condition_target()
        self.setLayout(grid_layout)
        
    def time_to_collision_condition_target_info(self):
        main_widget = QWidget()
        time_to_collision_condition_target_list = ['position', 'entityRef']
        self.time_to_collision_condition_target_combo_box = QComboBox()
        self.time_to_collision_condition_target_combo_box.addItems(time_to_collision_condition_target_list)
        self.time_to_collision_condition_target_combo_box.activated[str].connect(self.update_target)
        self.timetoCollisionConditionTarget_layout = QVBoxLayout()
        self.position_widget = PositionWidget()
        self.entityRef_widget = EntityRefWidget()
        self.timetoCollisionConditionTarget_layout.addWidget(self.position_widget)
        self.timetoCollisionConditionTarget_layout.addWidget(self.entityRef_widget)
        
        form_layout = QFormLayout()
        form_layout.addRow('TimeToCollisionConditionTarget:', self.time_to_collision_condition_target_combo_box)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(self.timetoCollisionConditionTarget_layout)
        main_widget.setLayout(vbox)
        return main_widget

    def set_default_time_to_collision_condition_target(self):
        self.hide_all_widgets()
        self.position_widget.setVisible(True)
    
    def hide_all_widgets(self):
        for i in range(self.timetoCollisionConditionTarget_layout.count()):
            self.timetoCollisionConditionTarget_layout.itemAt(i).widget().setVisible(False)
    
    def update_target(self):
        self.hide_all_widgets()
        if self.time_to_collision_condition_target_combo_box.currentText() == 'position':
            self.position_widget.setVisible(True)
        elif self.time_to_collision_condition_target_combo_box.currentText() == 'entityRef':
            self.entityRef_widget.setVisible(True)
        else:
            self.hide_all_widgets()
    
    def get_elements(self):
        if self.time_to_collision_condition_target_combo_box.currentText() == 'position':
            return self.position_widget.get_position_elements()
        else:
            return self.entityRef_widget.get_elements()

    def get_data(self):
        if self.time_to_collision_condition_target_combo_box.currentText() == 'position':
            return self.position_widget.get_position_data()
        else:
            return self.entityRef_widget.get_data()
        
class TimeToCollisionConditionWidget(QWidget):
    #TODO: Widget Size 확인
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.time_to_collision_condition_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def time_to_collision_condition_info(self):
        groupbox = QGroupBox('TimeToCollisionCondition')
        coordinate_system_list = [str(coordinate.name) for coordinate in CoordinateSystem]
        self.coordinate_system_combo_box = QComboBox()
        self.coordinate_system_combo_box.addItems(coordinate_system_list)
        self.coordinate_system_combo_box.setToolTip('Definition of the coordinate system to be used for calculations. If not provided the value is interpreted as "entity". If set, "alongRoute" is ignored.')

        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.freespace_combo_box.setToolTip('True: time to collision is measured using the distance between closest bounding box points.False: reference point distance is used.')
        
        relative_distance_type_list = [str(rdt.name) for rdt in RelativeDistanceType]
        self.relative_distance_type_combo_box = QComboBox()
        self.relative_distance_type_combo_box.addItems(relative_distance_type_list)
        self.relative_distance_type_combo_box.setCurrentIndex(relative_distance_type_list.index('euclideanDistance'))
        self.relative_distance_type_combo_box.setToolTip('Definition of the coordinate system dimension(s) to be used for calculating distances. If set "alongRoute" is ignored. If not provided, value is interpreted as "euclideanDistance".')
        
        routing_algorithm_list = [str(routing_algorithm.name) for routing_algorithm in RoutingAlgorithm]
        self.routing_algorithm_combo_box = QComboBox()
        self.routing_algorithm_combo_box.addItems(routing_algorithm_list)

        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setToolTip('The time to collision value')
        self.value.setPlaceholderText('Range [0..inf]')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        self.time_to_collision_condition_target_widget = TimeToCollisionConditionTargetWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('CoordinateSystem:', self.coordinate_system_combo_box)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('RelativeDistanceType:', self.relative_distance_type_combo_box)
        form_layout.addRow('RoutingAlgorithm:', self.routing_algorithm_combo_box)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(s):', self.value)
        form_layout.addRow('TimeToCollision\nConditionTarget:', self.time_to_collision_condition_target_widget)
        groupbox.setLayout(form_layout)
        return groupbox

    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                            'freespace':self.freespace_combo_box.currentText(),
                            'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                            'relativeDistanceType':self.relative_distance_type_combo_box.currentText(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text(),
                            'timeToCollisionConditionTarget':self.time_to_collision_condition_target_widget.get_elements()})
        
    def get_data(self):
        attrib = clean_empty({'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                              'relativeDistanceType':self.relative_distance_type_combo_box.currentText(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text()})
        data = self.time_to_collision_condition_target_widget.get_data()
        if isinstance(data, EntityRef):
            return TimeToCollisionCondition(attrib, None, data)
        else:
            return TimeToCollisionCondition(attrib, data, None)

class AccelerationConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.acceleration_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def acceleration_condition_info(self):
        groupbox = QGroupBox('AccelerationCondition')
        rule_list = [str(rule.name) for rule in Rule]
        direction_list = [str(direction.name) for direction in DirectionalDimension]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.direction_combo_box = QComboBox()
        self.direction_combo_box.addItems(direction_list)
        self.direction_combo_box.setToolTip('Direction of the acceleration (if not given, the total acceleration is considered).')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        self.value.setToolTip('Acceleration value')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('Direction:', self.direction_combo_box)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(m/s\u00b2)', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'direction':self.direction_combo_box.currentText(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'direction':self.direction_combo_box.currentText(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text()})
        return AccelerationCondition(attrib)

class StandStillConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.stand_still_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def stand_still_condition_info(self):
        groupbox = QGroupBox('StandStillCondition')
        self.duration = QLineEdit()
        self.duration.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.duration.setToolTip('Duration time of still standing to let the logical expression become true')
        self.duration.setPlaceholderText('Range: [0..inf]')
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('Duration(s):', self.duration)
        groupbox.setLayout(form_layout)
        return groupbox

    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'duration':self.duration.text()})
    
    def get_data(self):
        attrib = clean_empty({'duration':self.duration.text()})
        return StandStillCondition(attrib)

class SpeedConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.speed_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def speed_condition_info(self):
        groupbox = QGroupBox('SpeedCondition')
        direction_list = [str(direction.name) for direction in DirectionalDimension]
        self.direction_combo_box = QComboBox()
        self.direction_combo_box.addItems(direction_list)
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        self.value.setToolTip('Speed value of the speed condition.')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('DirectionalDimension:', self.direction_combo_box)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(m/s):', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text(),
                            'direction':self.direction_combo_box.currentText()})
    
    def get_data(self):
        attrib = clean_empty({'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text(),
                              'direction':self.direction_combo_box.currentText()})
        return SpeedCondition(attrib)
    
class RelativeSpeedConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_speed_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def relative_speed_condition_info(self):
        groupbox = QGroupBox('RelativeSpeedCondition')
        direction_list = [str(direction.name) for direction in DirectionalDimension]
        self.direction_combo_box = QComboBox()
        self.direction_combo_box.addItems(direction_list)
        self.entityRef = QLineEdit()
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        self.value.setToolTip('Relative speed value')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('DirectionalDimension:', self.direction_combo_box)
        form_layout.addRow('EntityRef:', self.entityRef)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(m/s):', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'entityRef':self.entityRef.text(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text(),
                            'direction':self.direction_combo_box.currentText()})
        
    def get_data(self):
        attrib = clean_empty({'entityRef':self.entityRef.text(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text(),
                              'direction':self.direction_combo_box.currentText()})
        return RelativeSpeedCondition(attrib)

class TraveledDistanceConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.traveled_distance_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def traveled_distance_condition_info(self):
        groupbox = QGroupBox('TraveledDistanceCondition')
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setPlaceholderText('Range [0..inf]')
        self.value.setToolTip('Amount of traveled distance')
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('Value(m):', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'value':self.value.text()})
        
    def get_data(self):
        attrib = clean_empty({'value':self.value.text()})
        return TraveledDistanceCondition(attrib)
    
class ReachPositionConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.reach_position_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def reach_position_condition_info(self):
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        groupbox = QGroupBox('ReachPositionCondition')
        self.tolerance = QLineEdit()
        self.tolerance.setValidator(nonnegative_validator)
        self.tolerance.setPlaceholderText('Range [0..inf]')
        self.tolerance.setToolTip('Radius of tolerance circle around given position')
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.setToolTip('The position to be reached with the defined tolerance.')
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position_widget = WorldPositionWidget()
        self.link_position_widget = LinkPositionWidget()
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position_widget)
        self.position_widget.addWidget(self.relative_world_position)
        self.position_widget.addWidget(self.link_position_widget)
        self.position_widget.addWidget(self.relative_object_position)
         
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('Tolerance:', self.tolerance)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position_widget.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position_widget.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_elements()

    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position_widget.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position_widget.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
        
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position_widget)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position_widget)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position)
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'tolerance':self.tolerance.text(),
                            'position':self.get_position_elements()})
    
    def get_data(self):
        attrib = clean_empty({'tolerance':self.tolerance.text()})
        return ReachPositionCondition(attrib, position=self.get_position_data())
    
class DistanceConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.distance_condition_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def distance_condition_info(self):
        groupbox = QGroupBox('DistanceCondition')
        coordinate_system_list = [str(coordinate.name) for coordinate in CoordinateSystem]
        self.coordinate_system_combo_box = QComboBox()
        self.coordinate_system_combo_box.addItems(coordinate_system_list)
        self.coordinate_system_combo_box.setToolTip('Definition of the coordinate system to be used for calculations. If not provided the value is interpreted as "entity". If set, "alongRoute" is ignored.')

        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.freespace_combo_box.setToolTip('True: distance is measured between closest bounding box points. False: reference point distance is used.')
        
        relative_distance_type_list = [str(rdt.name) for rdt in RelativeDistanceType]
        self.relative_distance_type_combo_box = QComboBox()
        self.relative_distance_type_combo_box.addItems(relative_distance_type_list)
        self.relative_distance_type_combo_box.setCurrentIndex(relative_distance_type_list.index('euclideanDistance'))
        self.relative_distance_type_combo_box.setToolTip('Definition of the coordinate system dimension(s) to be used for calculating distances. If set, "alongRoute" is ignored. If not provided, value is interpreted as "euclideanDistance".')
        
        routing_algorithm_list = [str(routing_algorithm.name) for routing_algorithm in RoutingAlgorithm]
        self.routing_algorithm_combo_box = QComboBox()
        self.routing_algorithm_combo_box.addItems(routing_algorithm_list)
        
        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
        
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setToolTip('The distance value.')
        self.value.setPlaceholderText('Range [0..inf]')
        
        self.position_type_combo_box = QComboBox()
        self.position_type_combo_box.addItems(POSITION_LIST)
        self.position_type_combo_box.activated[str].connect(self.update_position)
        
        self.position_widget = QStackedWidget()
        self.world_position_widget = WorldPositionWidget()
        self.link_position_widget = LinkPositionWidget()
        self.relative_object_position_widget = RelativeObjectPositionWidget()
        self.relative_world_position_widget = RelativeWorldPositionWidget()
        self.position_widget.addWidget(self.world_position_widget)
        self.position_widget.addWidget(self.relative_world_position_widget)
        self.position_widget.addWidget(self.link_position_widget)
        self.position_widget.addWidget(self.relative_object_position_widget)
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
        
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('CoordinateSystem:', self.coordinate_system_combo_box)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('RelativeDistanceType:', self.relative_distance_type_combo_box)
        form_layout.addRow('RoutingAlgorithm:', self.routing_algorithm_combo_box)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(m):', self.value)
        form_layout.addRow('Position:', self.position_type_combo_box)
        form_layout.addWidget(self.position_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_position_elements(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position_widget.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position_widget.get_elements()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position_widget.get_elements()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position_widget.get_elements()

    def get_position_data(self):
        if self.position_type_combo_box.currentText() == 'World Position':
            return self.world_position_widget.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position_widget.get_data()
        elif self.position_type_combo_box.currentText() == 'Link Position':
            return self.link_position_widget.get_data()
        elif self.position_type_combo_box.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position_widget.get_data()
    
    def update_position(self, choice):
        if choice == 'World Position':
            self.position_widget.setCurrentWidget(self.world_position_widget)
        elif choice == 'RelativeWorldPosition':
            self.position_widget.setCurrentWidget(self.relative_world_position_widget)
        elif choice == 'Link Position':
            self.position_widget.setCurrentWidget(self.link_position_widget)
        elif choice == 'RelativeObjectPosition':
            self.position_widget.setCurrentWidget(self.relative_object_position_widget)
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                            'freespace':self.freespace_combo_box.currentText(),
                            'relativeDistanceType':self.relative_distance_type_combo_box.currentText(),
                            'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text(),
                            'position':self.get_position_elements()})
    
    def get_data(self):
        attrib = clean_empty({
                              'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'relativeDistanceType':self.relative_distance_type_combo_box.currentText(),
                              'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text()})
        return DistanceCondition(attrib, position=self.get_position_data())
        
class RelativeDistanceConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_distance_condition_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def relative_distance_condition_info(self):
        groupbox = QGroupBox('RelativeDistanceCondition')
        coordinate_system_list = [str(coordinate.name) for coordinate in CoordinateSystem]
        self.coordinate_system_combo_box = QComboBox()
        self.coordinate_system_combo_box.addItems(coordinate_system_list)
        self.coordinate_system_combo_box.setToolTip('Definition of the coordinate system to be used for calculations. If not provided the value is interpreted as "entity"')

        self.entityRef = QLineEdit()
        self.entityRef.setToolTip('Reference entity.')

        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.freespace_combo_box.setToolTip('True: distance is measured between closest bounding box points. False: reference point distance is used.')

        relative_distance_type_list = [str(rdt.name) for rdt in RelativeDistanceType]
        self.relative_distance_type_combo_box = QComboBox()
        self.relative_distance_type_combo_box.addItems(relative_distance_type_list)
        self.relative_distance_type_combo_box.setCurrentIndex(relative_distance_type_list.index('euclideanDistance'))
        self.relative_distance_type_combo_box.setToolTip('Definition of the coordinate system dimension(s) to be used for calculating distances.')
        
        routing_algorithm_list = [str(routing_algorithm.name) for routing_algorithm in RoutingAlgorithm]
        self.routing_algorithm_combo_box = QComboBox()
        self.routing_algorithm_combo_box.addItems(routing_algorithm_list)

        rule_list = [str(rule.name) for rule in Rule]
        self.rule_combo_box = QComboBox()
        self.rule_combo_box.addItems(rule_list)
        self.rule_combo_box.setToolTip('The operator (less, greater, equal).')
            
        self.value = QLineEdit()
        self.value.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.value.setToolTip('The distance value.')
        self.value.setPlaceholderText('Range [0..inf]')
        
        self.triggering_entities_widget = TriggeringEntitiesWidget()
            
        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('CoordinateSystem:', self.coordinate_system_combo_box)
        form_layout.addRow('EntityRef:', self.entityRef)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('RelativeDistanceType:', self.relative_distance_type_combo_box)
        form_layout.addRow('RoutingAlgorithm:', self.routing_algorithm_combo_box)
        form_layout.addRow('Rule:', self.rule_combo_box)
        form_layout.addRow('Value(m):', self.value)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        return clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                            'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                            'entityRef': self.entityRef.text(),
                            'freespace':self.freespace_combo_box.currentText(),
                            'relativeDistanceType':self.relative_distance_type_combo_box.currentText(),
                            'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                            'rule':self.rule_combo_box.currentText(),
                            'value':self.value.text()})
    
    def get_data(self):
        attrib = clean_empty({'coordinateSystem':self.coordinate_system_combo_box.currentText(),
                              'entityRef': self.entityRef.text(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'relativeDistanceType':self.relative_distance_type_combo_box.currentText(),
                              'routingAlgorithm':self.routing_algorithm_combo_box.currentText(),
                              'rule':self.rule_combo_box.currentText(),
                              'value':self.value.text()})
        return RelativeDistanceCondition(attrib)

class RelativeLaneRangeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_lane_range_info(), 0, 0)
        self.setLayout(grid_layout)
        
    def relative_lane_range_info(self):
        main_widget = QWidget()
        self._from = QLineEdit()
        self._from.setValidator(QIntValidator())
        self._from.setToolTip('The lower limit of the range, if missing "-inf"')
        self._to = QLineEdit()
        self._to.setValidator(QIntValidator())
        self._to.setToolTip('The upper limit of the range, if missing "+inf"')
        form_layout = QFormLayout()
        form_layout.addRow('From:', self._from)
        form_layout.addRow('To:', self._to)
        main_widget.setLayout(form_layout)
        return main_widget

    def get_elements(self):
        return clean_empty({'from':self._from.text(), 'to':self._to.text()})
    
    def get_data(self):
        attrib = clean_empty({'from':self._from.text(), 'to':self._to.text()})
        return RelativeLaneRange(attrib)

class RelativeLaneRangeListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.relative_lane_range_list = []
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.button_layout = self.make_button_layout()
        self.main_layout.addLayout(self.button_layout, -1)
        self.setLayout(self.main_layout)
    
    def make_button_layout(self):
        grid_layout = QGridLayout()
        self.add_relative_lane_range_btn = QPushButton("add relativeLaneRange")
        self.add_relative_lane_range_btn.clicked.connect(self.add_relative_lane_range_widget)
        self.delete_relative_lane_range_btn = QPushButton("delete relativeLaneRange")
        self.delete_relative_lane_range_btn.clicked.connect(self.delete_relative_lane_range_widget)
        grid_layout.addWidget(self.add_relative_lane_range_btn, 0, 0)
        grid_layout.addWidget(self.delete_relative_lane_range_btn, 0, 1)
        return grid_layout
    
    @pyqtSlot()
    def add_relative_lane_range_widget(self):
        new_relative_lane_range_widget = RelativeLaneRangeWidget()
        index = self.main_layout.count() - 1
        self.main_layout.insertWidget(index, new_relative_lane_range_widget, 1)
        self.relative_lane_range_list.append(new_relative_lane_range_widget)
    
    @pyqtSlot()
    def delete_relative_lane_range_widget(self):
        index = self.main_layout.count() - 2
        if index < 0:
            QMessageBox.warning(self, 'Warning', 'There is nothing to delete')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.relative_lane_range_list.pop()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
        
    def get_elements(self):
        return [widget.get_elements() for widget in self.relative_lane_range_list]
    
    def get_data(self):
        return [widget.get_data() for widget in self.relative_lane_range_list]
    

class EntityRefsWidget(QWidget):
    """List of EntityRefs"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entity_ref_list = []
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.button_layout = self.make_button_layout()
        self.main_layout.addLayout(self.button_layout, -1)
        self.setLayout(self.main_layout)
        
    def make_button_layout(self):
        grid_layout = QGridLayout()
        self.add_entity_ref_btn = QPushButton("add entityRef")
        self.add_entity_ref_btn.clicked.connect(self.add_entity_ref_widget)
        self.delete_entity_ref_btn = QPushButton('delete entityRef')
        self.delete_entity_ref_btn.clicked.connect(self.delete_entity_ref_widget)
        grid_layout.addWidget(self.add_entity_ref_btn, 0, 0)
        grid_layout.addWidget(self.delete_entity_ref_btn, 0, 1)
        return grid_layout
    
    @pyqtSlot()
    def add_entity_ref_widget(self):
        new_entity_ref_widget = EntityRefWidget()
        index = self.main_layout.count() - 1
        self.main_layout.insertWidget(index, new_entity_ref_widget, 1)
        self.entity_ref_list.append(new_entity_ref_widget)
    
    @pyqtSlot()
    def delete_entity_ref_widget(self):
        index = self.main_layout.count() - 2
        if index < 0:
            QMessageBox.warning(self, 'Warning', 'There is nothing to delete')
        else:
            widget_item = self.main_layout.itemAt(index).widget()
            self.delete_widget(widget_item)
            self.entity_ref_list.pop()
    
    def delete_widget(self, widget):
        self.main_layout.removeWidget(widget)
        widget.deleteLater()
        widget = None
    
    def get_elements(self):
        return [widget.get_elements() for widget in self.entity_ref_list]
    
    def get_data(self):
        return [widget.get_data() for widget in self.entity_ref_list]

class RelativeClearanceConditionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.relative_clearance_condition_info(), 0, 0)
        self.setLayout(grid_layout)
    
    def relative_clearance_condition_info(self):
        groupbox = QGroupBox('RelativeClearanceCondition')
        double_validator = QDoubleValidator(decimals=8, notation=QDoubleValidator.StandardNotation)
        self.distanceBackward = QLineEdit()
        self.distanceBackward.setValidator(double_validator)
        self.distanceBackward.setPlaceholderText('Range: [0..inf]')
        self.distanceBackward.setToolTip('Longitudinal distance behind reference point of the entity to be checked along lane centerline of the current lane of the triggering entity')
        self.distanceForward = QLineEdit()
        self.distanceForward.setValidator(double_validator)
        self.distanceForward.setPlaceholderText('Range: [0..inf]')
        self.distanceForward.setToolTip('Longitudinal distance in front of reference point of the entity to be checked along lane centerline of the current lane of the triggering entity')
        self.freespace_combo_box = QComboBox()
        self.freespace_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.freespace_combo_box.setToolTip('If false, then entityRefs are only considered to be on the lane if their reference point is within the checked area; otherwise the whole bounding box is considered.')
        self.oppositeLanes_combo_box = QComboBox()
        self.oppositeLanes_combo_box.addItems(BOOLEAN_TYPE_LIST)
        self.oppositeLanes_combo_box.setToolTip('If true, then also lanes in the opposite direction are considered; otherwise only lanes in the same direction are considered.')
        self.entityRefs = EntityRefsWidget()
        self.entityRefs.setToolTip('Constraint to check only specific entities. If it is not used then all entities are considered.')
        self.relative_lane_range_widget = RelativeLaneRangeListWidget()
        self.triggering_entities_widget = TriggeringEntitiesWidget()

        form_layout = QFormLayout()
        form_layout.addRow('TriggeringEntities:', self.triggering_entities_widget)
        form_layout.addRow('DistanceBackward:', self.distanceBackward)
        form_layout.addRow('DistanceForward:', self.distanceForward)
        form_layout.addRow('Freespace:', self.freespace_combo_box)
        form_layout.addRow('OppositeLanes:', self.oppositeLanes_combo_box)
        form_layout.addRow('EntityRef:', self.entityRefs)
        form_layout.addRow('RelativeLaneRange:', self.relative_lane_range_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def get_elements(self):
        attrib = clean_empty({'triggeringEntities':self.triggering_entities_widget.get_elements(),
                              'distanceBackward':self.distanceBackward.text(),
                              'distanceForward':self.distanceForward.text(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'oppositeLanes':self.oppositeLanes_combo_box.currentText(),
                              'entityRef':self.entityRefs.get_elements(),
                              'relativeLaneRange':self.relative_lane_range_widget.get_elements()})
        return attrib
        
    def get_data(self):
        attrib = clean_empty({'distanceBackward':self.distanceBackward.text(),
                              'distanceForward':self.distanceForward.text(),
                              'freespace':self.freespace_combo_box.currentText(),
                              'oppositeLanes':self.oppositeLanes_combo_box.currentText()})
        return RelativeClearanceCondition(attrib, self.relative_lane_range_widget.get_data(), 
                                          self.entityRefs.get_data())