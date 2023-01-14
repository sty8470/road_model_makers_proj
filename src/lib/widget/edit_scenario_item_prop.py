import os
import sys
import re
import numpy as np
import ast
from lib.openscenario.class_defs.openscenario_item import Enumerations
from lib.openscenario.class_defs.enumerations import *
from PyQt5.QtWidgets import *
from lib.widget.add_scenario_object import *
from lib.widget.scenario_base_ui import *

class ScenarioPropertyEditor(QDialog):
    def __init__(self, data, mgeo_data):
        super().__init__()
        self.data = data
        self.return_value = self.data.text(2)
        self.edit_widget = None
        self.mgeo_data = mgeo_data
        self.initUI()

    def initUI(self):
        # data setting
        data_name = self.data.text(0)
        data_type = self.data.text(1)
        data_value = self.data.text(2)

        vbox = QVBoxLayout()
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        # data check
        if self.data.parent() is not None:
            if data_type == 'boolean':
                self.edit_widget = EditBoolean(self.data)
            elif data_type == 'dateTime':
                self.edit_widget = EditDateTime(self.data)
            elif data_type in Enumerations._member_names_:
                self.edit_widget = EditCombobox(self.data)
            else:
                # traffic state
                if self.data.parent().text(0) == 'TrafficSignalStateAction' or self.data.parent().text(0) == 'TrafficSignalState' or self.data.parent().text(0) == 'TrafficSignalControllerAction':
                    self.edit_widget = EditCombobox(self.data, self.mgeo_data)
                # Vehicle
                elif self.data.parent().text(0) == 'Vehicle':
                    if data_name == 'name':
                        self.edit_widget = EditCombobox(self.data)
                    elif data_name == 'vehicleCategory':
                        self.edit_widget = EditCombobox(self.data)
                    elif data_name == 'role':
                        self.edit_widget = EditCombobox(self.data)
                    else:
                        self.edit_widget = EditOneLine(self.data)
                else:
                    self.edit_widget = EditOneLine(self.data)
        else:
            self.edit_widget = EditOneLine(self.data)

        vbox.addWidget(self.edit_widget)
        vbox.addWidget(self.buttonbox)
        self.setLayout(vbox)
        self.setWindowTitle('Property Editor')
    
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

class EditDateTime(QWidget):
    def __init__(self, data):
        super().__init__()
        self.field = data.text(0)
        self.data = data.text(2)
        self.initUI()
    
    def initUI(self):
        vbox = QVBoxLayout()
        self.dateTime = QDateTimeEdit()
        # idx = QLabel(self.field)
        # vbox.addWidget(idx)
        vbox.addWidget(self.dateTime)
        self.setLayout(vbox)

    def accept(self):
        self.new_status = self.dateTime.dateTime().toString(Qt.ISODate)
        return self.new_status
        
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
    def __init__(self, data, mgeo_data=None):
        super().__init__()
        self.field = data.text(0)
        self.type = data.text(1)
        self.data = data.text(2)
        self.element = data.data(3, Qt.UserRole)
        # For Tl state
        self.mgeo_data = mgeo_data
        self.parent_data = data.parent()
        self.initUI()
        self.new_status = self.data

    def initUI(self):
        vbox = QVBoxLayout()
        self.combo = QComboBox()

        idx = QLabel(self.field)
        if self.type == 'AutomaticGearType':
            self.combo.addItems([str(am_gear_type.name) for am_gear_type in AutomaticGearType])
        elif self.type == 'ColorType':
            self.combo.addItems([str(color_type.name) for color_type in ColorType])
        elif self.type == 'ConditionEdge':            
            self.combo.addItems([str(condition_edge.name) for condition_edge in ConditionEdge])
        elif self.type == 'ControllerType':
            self.combo.addItems([str(controller_type.name) for controller_type in ControllerType])
        elif self.type == 'CoordinateSystem':
            self.combo.addItems([str(coordinate_system.name) for coordinate_system in CoordinateSystem])
        elif self.type == 'DamageType':
            self.combo.addItems([str(dmg.name) for dmg in DamageType])
        elif self.type == 'DirectionalDimension':
            self.combo.addItems([str(direction.name) for direction in DirectionalDimension])
        elif self.type == 'DynamicsDimension':
            self.combo.addItems([str(dynamicsDimension.name) for dynamicsDimension in DynamicsDimension])
        elif self.type == 'DynamicsShape':
            self.combo.addItems([str(dynamicsShape.name) for dynamicsShape in DynamicsShape])
        elif self.type == 'FaultType':
            self.combo.addItems([str(fault_type.name) for fault_type in FaultType])
        elif self.type == 'FollowingMode':
            self.combo.addItems([str(followingMode.name) for followingMode in FollowingMode])
        elif self.type == 'FractionalCloudCover':
            self.combo.addItems([str(fractionalCloudCover.name) for fractionalCloudCover in FractionalCloudCover])
        elif self.type == 'LateralDisplacement':
            self.combo.addItems([str(displacement.name) for displacement in LateralDisplacement])
        elif self.type == 'LightMode':
            self.combo.addItems([str(mode.name) for mode in LightMode])
        elif self.type == 'LongitudinalDisplacement':
            self.combo.addItems([str(displacement.name) for displacement in LongitudinalDisplacement])
        elif self.type == 'MiscObjectCategory':
            self.combo.addItems([str(category.name) for category in MiscObjectCategory])
        elif self.type == 'ObjectType':
            self.combo.addItems([str(objectType.name) for objectType in ObjectType])
        elif self.type == 'ParameterType':
            self.combo.addItems([str(parameter_type.name) for parameter_type in ParameterType])
        elif self.type == 'PedestrianCategory':
            self.combo.addItems([str(pedestrian_category.name) for pedestrian_category in PedestrianCategory])
        elif self.type == 'PedestrianGestureType':
            self.combo.addItems([str(pedestrian_gesture.name) for pedestrian_gesture in PedestrianGestureType])
        elif self.type == 'PedestrianMotionType':
            self.combo.addItems([str(pedestrian_motion.name) for pedestrian_motion in PedestrianMotionType])
        elif self.type == 'PrecipitationType':
            self.combo.addItems([str(precipitation_type.name) for precipitation_type in PrecipitationType])
        elif self.type == 'Priority':
            self.combo.addItems([str(priority.name) for priority in Priority])
        elif self.type == 'ReferenceContext':
            self.combo.addItems([str(reference_context.name) for reference_context in ReferenceContext])
        elif self.type == 'RelativeDistanceType':
            self.combo.addItems([str(relative_distance_type.name) for relative_distance_type in RelativeDistanceType])
        elif self.type == 'Role':
            self.combo.addItems([str(role.name) for role in Role])
        elif self.type == 'RouteStrategy':
            self.combo.addItems([str(route_strategy.name) for route_strategy in RouteStrategy])
        elif self.type == 'RoutingAlgorithm':
            self.combo.addItems([str(routing_algorithm.name) for routing_algorithm in RoutingAlgorithm])
        elif self.type == 'Rule':
            self.combo.addItems([str(rule.name) for rule in Rule])
        elif self.type == 'SpeedTargetValueType':
            self.combo.addItems([str(speed_target_value_type.name) for speed_target_value_type in SpeedTargetValueType])
        elif self.type == 'StoryboardElementState':
            self.combo.addItems([str(storyboard_element_state.name) for storyboard_element_state in StoryboardElementState])
        elif self.type == 'StoryboardElementType':
            self.combo.addItems([str(storyboard_element_type.name) for storyboard_element_type in StoryboardElementType])
        elif self.type == 'TriggeringEntitiesRule':
            self.combo.addItems([str(triggering_entities_rule.name) for triggering_entities_rule in TriggeringEntitiesRule])
        elif self.type == 'VelocityType':
            self.combo.addItems([str(velocity_type.name) for velocity_type in VelocityType])
        elif self.type == 'VehicleCategory':
            self.combo.addItems([str(vc.name) for vc in VehicleCategory])
        elif self.type == 'VehicleComponentType':
            self.combo.addItems([str(vct.name) for vct in VehicleComponentType])
        elif self.type == 'VehicleLightType':
            self.combo.addItems([str(vcl.name) for vcl in VehicleLightType])
        elif self.type == 'Wetness':
            self.combo.addItems([str(wetness.name) for wetness in Wetness])
        elif self.parent_data.text(0) == 'TrafficSignalStateAction':
            if self.field == 'state':
                tl_id = self.element.name
                if tl_id not in self.mgeo_data.light_set.signals.keys():
                    self.combo.setLineEdit(QLineEdit())
                    self.combo.editTextChanged[str].connect(self.setStatus)
                else:
                    tl_available_list = self.convert_tl(self.mgeo_data.light_set.signals[tl_id].sub_type)
                    self.combo.addItems(tl_available_list)
            if self.field == 'name':
                tl_list = []
                for key, val in self.mgeo_data.light_set.signals.items():
                    if val.sub_type != None:
                        tl_list.append(key)
                self.combo.addItems(tl_list)
                self.combo.setEditable(True)
                self.combo.editTextChanged[str].connect(self.setStatus)
        elif self.parent_data.text(0) == 'TrafficSignalState':
            # Controller Action 일 경우
            if self.field == 'state':
                tl_id = self.element.id
                if tl_id not in self.mgeo_data.light_set.signals.keys():
                    self.combo.setLineEdit(QLineEdit())
                    self.combo.editTextChanged[str].connect(self.setStatus)
                else:
                    tl_available_list = self.convert_tl(self.mgeo_data.light_set.signals[tl_id].sub_type)
                    self.combo.addItems(tl_available_list)
            if self.field == 'trafficSignalId':
                tl_list = []
                for key, val in self.mgeo_data.light_set.signals.items():
                    if val.sub_type != None:
                        tl_list.append(key)
                self.combo.addItems(tl_list)
                self.combo.setEditable(True)
                self.combo.editTextChanged[str].connect(self.setStatus)
        elif self.parent_data.text(0) == 'TrafficSignalControllerAction':
            intl_id = self.element.traffic_signal_controller_ref
            intl_available_list = list(self.mgeo_data.intersection_controller_set.intersection_controllers.keys())
            self.combo.addItems(intl_available_list)

        elif self.parent_data.text(0) == 'Vehicle':
            if self.element.isEgo == 'Ego':
                self.combo.addItems(EGO_SEDAN_LIST + EGO_BUS_LIST + EGO_CUSTOM_LIST + EGO_MISC_LIST + EGO_MPV_LIST + EGO_SUV_LIST + EGO_TRUCK_LIST + EGO_WAGON_LIST)
                self.combo.setEditable(True)
                self.combo.editTextChanged[str].connect(self.setStatus)
            else:
                self.combo.addItems(NPC_SEDAN_LIST + NPC_BUS_LIST + NPC_CUSTOM_LIST + NPC_MISC_LIST + NPC_MPV_LIST + NPC_SUV_LIST + NPC_TRUCK_LIST + NPC_WAGON_LIST)
                self.combo.setEditable(True)
                self.combo.editTextChanged[str].connect(self.setStatus)
        else: 
            self.combo.addItems(BOOLEAN_TYPE_LIST)

        self.combo.setCurrentIndex(self.combo.findText(self.data))
        self.combo.activated[str].connect(self.setStatus)
        vbox.addWidget(idx)
        vbox.addWidget(self.combo)
        self.setLayout(vbox)

    def setStatus(self, data):
        self.new_status = data

    def accept(self):
        if self.combo.currentText() == "":
            self.new_status = "none"
        return self.new_status
    
    def convert_tl(self, lights):
        result_light_list = []
        available_light_list = {
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

        for light in lights:
            if light in available_light_list:
                result_light_list.append(available_light_list[light])

        if 'red' and 'yellow' in lights:
            result_light_list.append('R_with_Y')
        elif 'yellow' in lights and 'straight' in lights:
            result_light_list.append('Y_with_G')
        elif 'yellow' in lights and 'left' in lights:
            result_light_list.append('Y_with_GLeft')
        elif 'straight' in lights and 'left' in lights:
            result_light_list.append('G_with_GLeft')
        elif 'red' in lights and 'left' in lights:
            result_light_list.append('R_with_GLeft')
        elif 'lowerleft' in lights and 'straight' in lights:
            result_light_list.append('LLG_SG')
        elif 'red' in lights and 'lowerleft' in lights:
            result_light_list.append('R_LLG')
        elif 'upperleft' in lights and 'upperright' in lights:
            result_light_list.append('ULG_URG')
        return result_light_list

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
        combo.addItems(BOOLEAN_TYPE_LIST)
        combo.setCurrentIndex(combo.findText(self.data))
        combo.activated[str].connect(self.setStatus)

        vbox.addWidget(idx)
        vbox.addWidget(combo)

        self.setLayout(vbox)

    def setStatus(self, data):
        self.new_status = data

    def accept(self):
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