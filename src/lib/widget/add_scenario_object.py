import os
import sys
import math

import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.openscenario.class_defs.enumerations import MiscObjectCategory, ObjectType
from lib.openscenario.class_defs.misc_object import MiscObject
from lib.openscenario.class_defs.parameter import Properties
from lib.openscenario.class_defs.pedestrian import Pedestrian
from lib.openscenario.class_defs.position import LinkPosition, WorldPosition
from lib.openscenario.class_defs.private_action import *
from lib.openscenario.class_defs.vehicle import Vehicle
from lib.openscenario.class_defs.entities import ScenarioObject
from lib.widget.scenario_base_ui import *

from lib.common.logger import Logger
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Seperate this list from Secnario_base_ui.py
#POSITION_LIST_ADD_SC_OBJECT = ['World Position', 'Link Position']

# EGO Vehicle Model Lists
EGO_SEDAN_LIST = ['2014_Kia_K7', '2015_Kia_K5', '2016_Hyundai_Genesis_DH', '2016_Hyundai_Ioniq(KAIST)',
                  '2016_Hyundai_Ioniq', '2016_Hyundai_Sonata', '2017_Hyundai_Grandeur','2019_Toyota_Prius',
                  '2019_hyundai_genesis_g90','2020_Kia_K5', '2020_Hyundai_Sonata', '2020_Kia_Stinger', 
                  '2021_Hyundai_G80', 'DEFAULT_SEDAN']

EGO_SUV_LIST = ['2016_Hyundai_Santafe', '2017_Kia_Niro(HEV)', '2017_Kia_Sorento', '2019_Hyundai_Nexo',
                '2020_volvo_xc90', '2021_Hyundai_GV70', '2021_Hyundai_GV70_Senseor', '2021_Hyundai_Genesis_GV80',
                '2021_Volkswagen_Golf_GTI', '2023_Hyundai_Inoiq5', '2023_Kia_EV6', 'DEFAULT_SUV']

EGO_BUS_LIST  = ['2016_Hyundai_Universe', '2016_Hyundai_Universe_B', '2016_Hyundai_Universe_G', '2016_Hyundai_Universe_R',
                 '2016_Hyundai_Universe_Y', '2017_Hyundai_solati_h350', 'DEFAULT_BUS']

EGO_TRUCK_LIST = ['2012_Hyundai_HD65', '2013_Hyundai_Porter2', '2013_Hyundai_Xcient(P520)', '2013_Hyundai_Xcient(P540)',
                  '2014_Hyundai_Xcient(Mixer)', '2016_PeterBilt_579', 'DEFAULT_TRUCK', 'SPMT']

EGO_WAGON_LIST = ['2015_Toyota_Prius(HEV)', 'DEFAULT_WAGON']

EGO_MISC_LIST = ['2019_Toyota_e_palette', 'ETRI_UGV', 'NURO', 'UnmannedSolution_ERP42-V2', 'WMR_TypeA_Model01_Micro',
                 'WMR_TypeA_Model01_Mini', 'WMR_TypeA_XyCar_YModel', 'WMR_TypeB_Model01_Micro', 'WMR_TypeC_Model01_Mini',
                 'WMR_TypeC_Model02_Mini', 'WMR_TypeC_Model03_Mini', 'WeGoERP42', 'WeGoScout-Mini', 'WeGo_WeCAR',
                 'Wego_WeBot2.0', 'Wego_Wecar2']

EGO_MPV_LIST = ['2019_kia_sedona', '2020_chlyser_pacifica_hybrid', '2021_Kia_Carnival', 'DEFAULT_MPV']

#TODO: Mini_Suttle --> Mini_Shuttle
EGO_CUSTOM_LIST = ['2016_Kia_Soul(EV)', '2019_Hyundai_Kona(EV)', '2020_Kia_Soul(EV)', '2020_Kia_Niro(EV)', 
                   '2021_Hanho_Tech_Gilbot', 'AirportTug', 'CBNU', 'Empty_Vehicle', 'Mini_Suttle',
                   'NaverLabs_ALT', 'ParkingBot', 'TurtleBot']

# NPC Vehicle Model Lists
NPC_SEDAN_LIST = ['2014_Kia_K7', '2015_Kia_K5', '2016_Hyundai_Genesis_DH', '2016_Hyundai_Ioniq(KAIST)',
                  '2016_Hyundai_Ioniq', '2016_Hyundai_Sonata', '2017_Hyundai_Grandeur','2019_Toyota_Prius',
                  '2019_hyundai_genesis_g90', '2020_Kia_K5', '2020_Hyundai_Sonata', '2020_Kia_Stinger',
                  '2021_Hyundai_G80', 'DEFAULT_SEDAN']

NPC_SUV_LIST = ['2016_Hyundai_Santafe', '2017_Kia_Niro(HEV)', '2017_Kia_Sorento', '2019_Hyundai_Nexo',
                '2020_volvo_xc90', '2021_Hyundai_Genesis_GV80', '2021_Volkswagen_Golf_GTI', 'DEFAULT_SUV']

NPC_BUS_LIST = ['2016_Hyundai_Universe', '2017_Hyundai_solati_h350', 'DEFAULT_BUS']

NPC_TRUCK_LIST  = ['2012_Hyundai_HD65', '2013_Hyundai_Porter2', '2013_Hyundai_Xcient(P520)', '2013_Hyundai_Xcient(P540)',
                   '2014_Hyundai_Xcient(Mixer)', '2016_PeterBilt_579', 'DEFAULT_TRUCK']

NPC_WAGON_LIST = ['2015_Toyota_Prius(HEV)', 'DEFAULT_WAGON']

NPC_MISC_LIST = ['2019_Toyota_e_palette', 'ETRI_UGV', 'NURO', 'UnmannedSolution_ERP42-V2', 'WMR_TypeA_Model01_Micro'
                 'WMR_TypeA_Model01_Mini', 'WMR_TypeA_XyCar_YModel', 'WMR_TypeB_Model01_Micro',
                 'WeGoERP42', 'WeGoScout-Mini', 'WeGo_WeCAR', 'Wego_WeBot2.0']

NPC_MPV_LIST = ['2019_kia_sedona', '2020_chlyser_pacifica_hybrid', '2021_Kia_Carnival', 'DEFAULT_MPV']

NPC_CUSTOM_LIST = ['2016_Kia_Soul(EV)', '2019_Hyundai_Kona(EV)', '2020_Kia_Niro(EV)' '2020_Kia_Soul(EV)',
                   'CBNU', 'NaverLabs_ALT']

""" ADD SCENARIO OBJECT UI"""
class VehicleModelUI(QDialog):
    def __init__(self, openscenario_importer, position=None):
        super().__init__()
        self.openscenario_importer = openscenario_importer
        self.position = position
        self.initUI()
        self.show()
        
    def initUI(self):
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.vehicle_info_group(), 0, 0)
        self.grid_layout.addWidget(self.vehicle_velocity_position(), 1, 0)
        self.grid_layout.addWidget(self.vehicle_property(), 2, 0)
        self.ego_vehicle_property_radio_btn()
        self.set_default_position()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.grid_layout.addWidget(self.button_box, 3, 0)
        self.setLayout(self.grid_layout)
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Add Vehicle')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def vehicle_info_group(self):
        groupbox = QGroupBox('Vehicle Model && Type')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.vehicle_type = ['Sedan', 'SUV', 'Bus', 'Truck', 'Wagon', 'Misc', 'MPV', 'Custom']
        self.ego_radio_btn = QRadioButton('Ego')
        self.isEgo = True
        self.check_tl = None
        self.apply_acc = None
        self.npc_radio_btn = QRadioButton('NPC')
        self.ego_radio_btn.clicked.connect(self.radioButtonClicked)
        self.npc_radio_btn.clicked.connect(self.radioButtonClicked)
        
        self.vehicle_name = QLineEdit()
        # Default Setting
        # - Ego checked on --> setText_disable --> setModel (sedan from Ego Vehicle)
        self.ego_radio_btn.setChecked(True)
        self.vehicle_name.setText('Ego')
        self.vehicle_name.setReadOnly(1)
        
        self.model_name = EGO_SEDAN_LIST[0]
        self.combo_vehicle_type = QComboBox()
        self.combo_vehicle_type.addItems(self.vehicle_type)
        self.sublists = EGO_SEDAN_LIST, EGO_SUV_LIST, EGO_BUS_LIST, EGO_TRUCK_LIST, EGO_WAGON_LIST, EGO_MISC_LIST, EGO_MPV_LIST, EGO_CUSTOM_LIST
        self.combo_vehicle_model = QComboBox()
        self.combo_vehicle_model.addItems(EGO_SEDAN_LIST)
        self.combo_vehicle_type.currentIndexChanged.connect(self.updateComboModel)
        
        self.combo_vehicle_type.activated[str].connect(self.onActivatedType)
        self.combo_vehicle_model.activated[str].connect(self.onActivated)
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.ego_radio_btn)
        hbox1.addWidget(self.npc_radio_btn)
        
        form_layout = QFormLayout()
        form_layout.addRow('Entity Name:', self.vehicle_name)
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.combo_vehicle_type)
        hbox2.addWidget(self.combo_vehicle_model)
        form_layout.addRow('Type & Model:', hbox2)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(form_layout)
        vbox.addStretch()
        groupbox.setLayout(vbox)
        return groupbox
    
    def vehicle_velocity_position(self):
        groupbox = QGroupBox('Vehicle Velocity && Position')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.velocity = QLineEdit()
        self.velocity.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.combo_position_type = QComboBox()
        self.combo_position_type.addItems(POSITION_LIST)

        self.combo_position_type.activated[str].connect(self.update_position)
        form_layout = QFormLayout()
        form_layout.addRow('Velocity (m/s) : ', self.velocity)
        form_layout.addRow('Position : ', self.combo_position_type)
        
        inner_widget = QWidget()
        inner_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        inner_widget.setContentsMargins(0, 0, 0, 0)
        
        self.position_layout = QVBoxLayout(inner_widget)
        self.position_layout.setContentsMargins(0, 0, 0 ,0)
        self.world_position = WorldPositionWidget(self.position)
        self.link_position = LinkPositionWidget(self.position)
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_layout.addWidget(self.world_position)
        self.position_layout.addWidget(self.relative_world_position)
        self.position_layout.addWidget(self.link_position)
        self.position_layout.addWidget(self.relative_object_position)

        form_layout.addWidget(inner_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def vehicle_property(self):
        groupbox = QGroupBox('Vehicle Property')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        check_tl_group_box = QGroupBox('Check Tl')
        apply_acc_group_box = QGroupBox('Apply ACC')
        vbox_property = QVBoxLayout()
        self.check_tl_on_btn = QRadioButton('On')
        self.check_tl_off_btn = QRadioButton('Off')
        self.check_tl_on_btn.clicked.connect(self.radioButtonClicked_check_tl)
        self.check_tl_off_btn.clicked.connect(self.radioButtonClicked_check_tl)
        self.apply_acc_on_btn = QRadioButton('On')
        self.apply_acc_off_btn = QRadioButton('Off')
        self.apply_acc_on_btn.clicked.connect(self.radioButtonClicked_apply_acc)
        self.apply_acc_off_btn.clicked.connect(self.radioButtonClicked_apply_acc)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.check_tl_on_btn)
        hbox1.addWidget(self.check_tl_off_btn)
        check_tl_group_box.setLayout(hbox1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.apply_acc_on_btn)
        hbox2.addWidget(self.apply_acc_off_btn)
        apply_acc_group_box.setLayout(hbox2)
        vbox_property.addWidget(check_tl_group_box)
        vbox_property.addWidget(apply_acc_group_box)
        groupbox.setLayout(vbox_property)
        return groupbox
    
    def radioButtonClicked_check_tl(self):
        if self.check_tl_on_btn.isChecked():
            self.check_tl = True
        else:
            self.check_tl = False
    
    def radioButtonClicked_apply_acc(self):
        if self.apply_acc_on_btn.isChecked():
            self.apply_acc = True
        else:
            self.apply_acc = False
    
    def ego_vehicle_property_radio_btn(self):
        self.check_tl = True
        self.apply_acc = True
        self.check_tl_on_btn.setChecked(True)
        self.check_tl_off_btn.setChecked(False)
        self.apply_acc_on_btn.setChecked(True)
        self.apply_acc_off_btn.setChecked(False)

    def npc_vehicle_property_radio_btn(self):
        self.check_tl = True
        self.apply_acc = False
        self.check_tl_on_btn.setChecked(True)
        self.check_tl_off_btn.setChecked(False)
        self.apply_acc_on_btn.setChecked(False)
        self.apply_acc_off_btn.setChecked(True)

    def reset_radio_button(self):
        self.check_tl = None
        self.apply_acc = None
        self.check_tl_on_btn.setChecked(False)
        self.check_tl_off_btn.setChecked(False)
        self.apply_acc_on_btn.setChecked(False)
        self.apply_acc_off_btn.setChecked(False)

    def radioButtonClicked(self):
        if self.ego_radio_btn.isChecked():
            self.isEgo = True
            self.vehicle_name.setText("Ego")
            self.vehicle_name.setReadOnly(1)
            self.sublists = EGO_SEDAN_LIST, EGO_SUV_LIST, EGO_BUS_LIST, EGO_TRUCK_LIST, EGO_WAGON_LIST, EGO_MISC_LIST, EGO_MPV_LIST, EGO_CUSTOM_LIST
            self.model_name = EGO_SEDAN_LIST[0]
            self.combo_vehicle_model.clear()
            self.combo_vehicle_model.addItems(EGO_SEDAN_LIST)
            self.combo_vehicle_type.clear()
            self.combo_vehicle_type.addItems(self.vehicle_type)
            self.reset_radio_button()
            self.ego_vehicle_property_radio_btn()
        else:
            self.isEgo = False
            self.vehicle_name.clear()
            self.vehicle_name.setReadOnly(0)
            self.sublists = NPC_SEDAN_LIST, NPC_SUV_LIST, NPC_BUS_LIST, NPC_TRUCK_LIST, NPC_WAGON_LIST, NPC_MISC_LIST, NPC_MPV_LIST, NPC_CUSTOM_LIST
            self.mode_name = NPC_SEDAN_LIST[0]
            self.combo_vehicle_model.clear()
            self.combo_vehicle_model.addItems(NPC_SEDAN_LIST)
            self.combo_vehicle_type.clear()
            self.combo_vehicle_type.addItems(self.vehicle_type)
            self.reset_radio_button()
            self.npc_vehicle_property_radio_btn()

    def onActivatedType(self, text):
        if self.ego_radio_btn.isChecked():
            if text == 'Sedan':
                self.model_name = EGO_SEDAN_LIST[0]
            elif text == 'SUV':
                self.model_name = EGO_SUV_LIST[0]
            elif text == 'Bus':
                self.model_name = EGO_BUS_LIST[0]
            elif text == 'Truck':
                self.model_name = EGO_TRUCK_LIST[0]
            elif text == 'Wagon':
                self.model_name = EGO_WAGON_LIST[0]
            elif text == 'Misc':
                self.model_name = EGO_MISC_LIST[0]
            elif text == 'MPV':
                self.mode_name = EGO_MPV_LIST[0]
            else:
                self.mode_name = EGO_CUSTOM_LIST[0]
        else:
            if text == 'Sedan':
                self.model_name = NPC_SEDAN_LIST[0]
            elif text == 'SUV':
                self.model_name = NPC_SUV_LIST[0]
            elif text == 'Bus':
                self.model_name = NPC_BUS_LIST[0]
            elif text == 'Truck':
                self.model_name = NPC_TRUCK_LIST[0]
            elif text == 'Wagon':
                self.model_name = NPC_WAGON_LIST[0]
            elif text == 'Misc':
                self.model_name = NPC_MISC_LIST[0]
            elif text == 'MPV':
                self.mode_name = NPC_MPV_LIST[0]
            else:
                self.mode_name = NPC_CUSTOM_LIST[0]
            
    def onActivated(self, text):
        if text in EGO_SEDAN_LIST + EGO_SUV_LIST + EGO_BUS_LIST + EGO_TRUCK_LIST + EGO_WAGON_LIST + EGO_CUSTOM_LIST + EGO_MISC_LIST:
            self.model_name = text
        else:
            self.model_name = text #NPC
        
    def updateComboModel(self, index):
        self.combo_vehicle_model.clear()
        self.combo_vehicle_model.addItems(self.sublists[index])

    def set_default_position(self):
        self.hide_position_widgets()
        self.world_position.setVisible(True) # WorldPosition

    def hide_position_widgets(self):
        for i in range(self.position_layout.count()):
            self.position_layout.itemAt(i).widget().setVisible(False)

    def update_position(self, choice):
        self.hide_position_widgets()
        if choice == 'World Position':
            self.world_position.setVisible(True)
        elif choice == 'RelativeWorldPosition':
            self.relative_world_position.setVisible(True)
        elif choice == 'Link Position':
            self.link_position.setVisible(True)
        elif choice == 'RelativeObjectPosition':
            self.relative_object_position.setVisible(True)
        else:
            self.hide_position_widgets()

    def get_position_data(self):
        if self.combo_position_type.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.combo_position_type.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.combo_position_type.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.combo_position_type.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()

    def showDialog(self):
        return super().exec_()
    
    def accept(self):
        if self.vehicle_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set NPC Vehicle's name")
            return
        
        #NPC Double Check
        if self.vehicle_name.text() in self.openscenario_importer.scenario_definition.entities.entities_dict:
            QMessageBox.warning(self, "Warning", "The Vehicle name you entered already exists in the entities")
            return
        
        position_data = self.get_position_data()
        try:
            msg = ""
            if isinstance(position_data, WorldPosition):
                if position_data.attrib['x'] == 'unspecified' or position_data.attrib['y'] == 'unspecified':
                    msg = ": 'x' and 'y' should be specified"
            elif isinstance(position_data, LinkPosition):
                if position_data.attrib['id'] == 'unspecified':
                    msg = ": 'Link ID' should be specified"

            position_data.load()
            if isinstance(position_data, LinkPosition):
                if position_data.id not in self.openscenario_importer.mgeo.link_set.lines:
                    msg = ": The link doesn't exist"
                    raise ValueError(msg)
                
                if len(self.openscenario_importer.mgeo.link_set.lines[position_data.id].points) <= position_data.index:
                    msg = ": The link index is out of range"
                    raise ValueError(msg)
        except:
            QMessageBox.warning(self, "Warning", "Invalid Position" + msg)
            return
        
        absolute_target_speed = AbsoluteTargetSpeed({'value':self.velocity.text()})
        transition_dynamics = TransitionDynamics({'dynamicsDimension':'time','dynamicsShape':'step','value': "0"})
        new_speed_action = LongitudinalAction(SpeedAction(SpeedActionTarget(absolute_target_speed), transition_dynamics))
        new_teleport_action = TeleportAction(position_data)
        try:
            new_speed_action.load()
            new_teleport_action.load()
        except:
            QMessageBox.warning(self, "Warning", "Invalid vehicle initial state")
            return
        
        # Properties : check_tl & apply_acc
        new_prop = Properties()
        if self.check_tl != None and self.apply_acc != None:
            if self.check_tl == True:
                new_prop.add_property('check_tl', "true")
            else:
                new_prop.add_property('check_tl', "false")
            if self.apply_acc == True:
                new_prop.add_property('apply_acc', "true")
            else:
                new_prop.add_property('apply_acc', "false")

        attrib = {'name':self.vehicle_name.text()}
        info = Vehicle(attrib={'name': self.model_name, 'vehicleCategory': 'car'}, properties=new_prop)
        new_object = ScenarioObject(attrib, ObjectType.vehicle, info)
        try:
            new_object.load()
        except:
            QMessageBox.warning(self, "Warning", "Invalid vehicle info.")
            return

        init_action = self.openscenario_importer.scenario_definition.storyboard.init_element.init_action
        init_action.add_private_action(self.vehicle_name.text(), new_teleport_action)
        init_action.add_private_action(self.vehicle_name.text(), new_speed_action)
        self.openscenario_importer.scenario_definition.entities.scenario_objects.append(new_object)
        self.done(1)
        
    def reject(self):
        self.done(0)

class PedestrianModelUI(QDialog):
    def __init__(self, openscenario_importer, position=None):
        super().__init__()
        self.openscenario_importer = openscenario_importer
        self.position = position
        self.initUI()
        self.show()
        
    def initUI(self):
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.pedestrian_info_group(), 0, 0)
        grid_layout.addWidget(self.pedestrian_velocity_position(), 1, 0)
        grid_layout.addWidget(self.pedestrian_property(), 2, 0)
        self.set_default_position()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        grid_layout.addWidget(self.button_box, 3, 0)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.setLayout(grid_layout)
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Add Pedestrian')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def pedestrian_info_group(self):
        groupbox = QGroupBox('Pedestrian Model && Type')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.pedestrian_type = ['Adult', 'Child']
        self.adult_list = ['Man1', 'Man2', 'Man3', 'Man4_phone', 'Man4', 'Man5', 'Man6', 'Man7', 'Man8','NCAP_EBT','NCAP_EBT_MINI'
                           'NCAP_EPTa', 'Old man1', 'Old woman1', 'Woman1', 'Woman2', 'Woman3', 'Woman4',
                           'Woman5', 'Woman6', 'Woman7', 'Woman8', 'old man1_phone', 'old woman1_phone', 'police1', 'woman7_phone',
                           'man1_ai', 'man2_ai', 'man3_ai', 'man5_ai', 'man6_ai', 'man7_ai', 'man8_ai', 'woman4_ai',
                           'woman5_ai', 'woman6_ai']
        self.child_list = ['Boy1', 'Boy2', 'Boy2_phone', 'Girl1', 'Girl2', 'Girl2_phone', 'NCAP_EPTc']
        
        self.model_name = self.adult_list[0]
        self.combo_pedestrian_type = QComboBox()
        self.combo_pedestrian_type.addItems(self.pedestrian_type)
        self.sublists = self.adult_list, self.child_list
        self.combo_pedestrian_model = QComboBox()
        self.combo_pedestrian_model.addItems(self.adult_list)
        self.combo_pedestrian_type.currentIndexChanged.connect(self.updateComboModel)
        self.combo_pedestrian_type.activated[str].connect(self.onActivatedType)
        self.combo_pedestrian_model.activated[str].connect(self.onActivated)
        
        self.pedestrian_name = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('Entity Name:', self.pedestrian_name)
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.combo_pedestrian_type)
        hbox2.addWidget(self.combo_pedestrian_model)
        form_layout.addRow('Type & Model:', hbox2)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addStretch()
        groupbox.setLayout(vbox)
        return groupbox
    
    def pedestrian_velocity_position(self):
        groupbox = QGroupBox('Pedestrian Position && Velocity')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.velocity = QLineEdit()
        self.velocity.setValidator(QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation))
        self.combo_position_type = QComboBox()
        self.combo_position_type.addItems(POSITION_LIST)

        self.combo_position_type.activated[str].connect(self.update_position)
        form_layout = QFormLayout()
        form_layout.addRow('Velocity (m/s) : ', self.velocity)
        form_layout.addRow('Position : ', self.combo_position_type)
        
        inner_widget = QWidget()
        inner_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        inner_widget.setContentsMargins(0, 0, 0, 0)
        
        self.position_layout = QVBoxLayout(inner_widget)
        self.position_layout.setContentsMargins(0, 0, 0 ,0)
        self.world_position = WorldPositionWidget(self.position)
        self.link_position = LinkPositionWidget(self.position)
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_layout.addWidget(self.world_position)
        self.position_layout.addWidget(self.relative_world_position)
        self.position_layout.addWidget(self.link_position)
        self.position_layout.addWidget(self.relative_object_position)

        form_layout.addWidget(inner_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def pedestrian_property(self):
        groupbox = QGroupBox('Pedestrian Property')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        vbox_property = QVBoxLayout()
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel('Active Distance:'))
        self.active_distance = QLineEdit()
        hbox1.addWidget(self.active_distance)
        hbox1.addWidget(QLabel('(m)'))
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('Move Distance:'))
        hbox2.addSpacing(3)
        self.move_distance = QLineEdit()
        hbox2.addWidget(self.move_distance)
        hbox2.addWidget(QLabel('(m)'))
        
        vbox_property.addLayout(hbox1)
        vbox_property.addLayout(hbox2)
        vbox_property.addStretch()
        groupbox.setLayout(vbox_property)
        return groupbox
    
    def onActivatedType(self, text):
        if text == 'Adult':
            self.model_name = self.adult_list[0]
        elif text == 'Child':
            self.model_name = self.child_list[0]
        else:
            pass
            
    def onActivated(self, text):
        if text in self.adult_list or text in self.child_list:
            self.model_name = text
        elif text in self.ai_list:
            QMessageBox.warning(self, "Warning", "AI Model Can be Spawned in Suburb Map")
            self.model_name = text
        
    def updateComboModel(self, index):
        self.combo_pedestrian_model.clear()
        self.combo_pedestrian_model.addItems(self.sublists[index])
    
    def set_default_position(self):
        self.hide_position_widgets()
        self.world_position.setVisible(True) # WorldPosition

    def hide_position_widgets(self):
        for i in range(self.position_layout.count()):
            self.position_layout.itemAt(i).widget().setVisible(False)

    def update_position(self, choice):
        self.hide_position_widgets()
        if choice == 'World Position':
            self.world_position.setVisible(True)
        elif choice == 'RelativeWorldPosition':
            self.relative_world_position.setVisible(True)
        elif choice == 'Link Position':
            self.link_position.setVisible(True)
        elif choice == 'RelativeObjectPosition':
            self.relative_object_position.setVisible(True)
        else:
            self.hide_position_widgets()

    def get_position_data(self):
        if self.combo_position_type.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.combo_position_type.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.combo_position_type.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.combo_position_type.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()

    def showDialog(self):
        return super().exec_()
            
    def accept(self):
        if self.pedestrian_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set Pedestrian's name")
            return
        if self.pedestrian_name.text() in self.openscenario_importer.scenario_definition.entities.entities_dict:
            QMessageBox.warning(self, "Warning", "The Pedestrian name you entered already exists in the entities")
            return
        
        position_data = self.get_position_data()
        try:
            msg = ""
            # WorldPosition
            if isinstance(position_data, WorldPosition):
                if position_data.attrib['x'] == 'unspecified' or position_data.attrib['y'] == 'unspecified':
                    msg = ": 'x' and 'y' should be specified"
            elif isinstance(position_data,LinkPosition):
                if position_data.attrib['id'] == 'unspecified':
                    msg = ": 'Link ID' should be specified"
            
            position_data.load()
            if isinstance(position_data, LinkPosition):
                if position_data.id not in self.openscenario_importer.mgeo.link_set.lines:
                    msg = ": The link doesn't exist"
                    raise ValueError(msg)
                
                if len(self.openscenario_importer.mgeo.link_set.lines[position_data.id].points) < position_data.index:
                    msg = ": The link index is out of range"
                    raise ValueError(msg)
        except:
            QMessageBox.warning(self, "Warning", "Invalid Position" + msg)
            return
            
        absolute_target_speed = AbsoluteTargetSpeed({'value':self.velocity.text()})
        transition_dynamics = TransitionDynamics({'dynamicsDimension':'time','dynamicsShape':'step','value': '0'})
        new_speed_action = LongitudinalAction(SpeedAction(SpeedActionTarget(absolute_target_speed), transition_dynamics))
        new_teleport_action = TeleportAction(position_data)
        try:
            new_speed_action.load()
            new_teleport_action.load()
        except:
            QMessageBox.warning(self, "Warning", "Invalid pedestrian initial state")
            return
        
        new_prop = Properties()
        if self.active_distance.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set Active Distance")
            return
        else:
            new_prop.add_property('activeDistance', self.active_distance.text())
        
        if self.move_distance.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set Move Distance")
            return
        else:
            new_prop.add_property('moveDistance', self.move_distance.text())  
        
        attrib = {'name':self.pedestrian_name.text()}
        pedestrian_info = {'name':self.model_name,'mass':"0",'pedestrianCategory':'pedestrian'}
        info = Pedestrian(attrib=pedestrian_info, properties=new_prop)
        new_object = ScenarioObject(attrib, ObjectType.pedestrian, info)
        try:
            new_object.load()
        except:
            QMessageBox.warning(self, "Warning", "Invalid pedestrian info.")
            return

        init_action = self.openscenario_importer.scenario_definition.storyboard.init_element.init_action
        init_action.add_private_action(self.pedestrian_name.text(), new_teleport_action)
        init_action.add_private_action(self.pedestrian_name.text(), new_speed_action)
        self.openscenario_importer.scenario_definition.entities.scenario_objects.append(new_object)
        self.done(1)
        
    def reject(self):
        self.done(0)
        
class MiscObjectModelUI(QDialog):
    def __init__(self, openscenario_importer, position=None):
        super().__init__()
        self.openscenario_importer = openscenario_importer
        self.position = position
        self.initUI()
        self.show()
        
    def initUI(self):
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.misc_object_category_model(), 0, 0)
        grid_layout.addWidget(self.misc_object_position(), 1, 0)
        grid_layout.addWidget(self.misc_object_property(), 2, 0)
        self.set_default_position()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        grid_layout.addWidget(self.button_box, 3, 0)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.setLayout(grid_layout)
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Add MiscObject')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def misc_object_category_model(self):
        groupbox = QGroupBox('MiscObject Name && Type')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.mis_object_type = [str(category.name) for category in MiscObjectCategory]
        # MORAI 에서 정의한 Model 나열
        # self.stop_point = ['none']
        # self.obstacle_list = [
        #     'CargoBox','Lane_Separation_Bar','OBJ ERP','OBJ_ETRI_UGV','OBJ_Hyndai_Grandeur',
        #     'OBJ_Hyundai_HD65','OBJ_Hyundai_HR','OBJ_Hyundai_Ioniq','OBJ_Hyundai_SantaFe','OBJ_Hyundai_Sonata',
        #     'OBJ_Hyundai_Universe_High','OBJ_Hyundai_Xcient_Mixer','OBJ_Hyundai_Xcient_P520','OBJ_Hyundai_Xcient_P540',
        #     'OBJ_Kia_K5','OBJ_Kia_K7','OBJ_Kia_Niro','OBJ_Kia_Sorento','OBJ_Kona_EV_2019','OBJ_Morai_Car','OBJ_NaverLab_ALT',
        #     'OBJ_Niro_EV_2020','PE_Drum','PE_Firewall_Orange','PE_Firewall_White','RedBarrel','Road_Sign_Mark','Speed_Bump',
        #     'Steel_Barricade','TrafficBarrel','WoodBox','YellowBarrel'
        #                       ]
        # self.custom_object_list = [
        #     'BabyStroller1','BabyStroller2','BabyStroller3','Bike1','Bike2','Color_Cone','ETRI_Drone_01','ETRI_Drone_02',
        #     'ETRI_Drone_03','ETRI_Drone_04','ETRI_Drone_05','ETRI_Drone_06','ETRI_Drone_07','ETRI_Drone_08','ETRI_Drone_09',
        #     'ETRI_Drone_10','ETRI_Drone_11','ETRI_Drone_12','ETRI_Drone_13','ETRI_Drone_14','ETRI_Drone_15','ETRI_Drone_16',
        #     'ETRI_LandingPad01','ETRI_LandingPad02','ETRI_LandingPad03','ETRI_Postman','ETRI_Postwoman','ElectricScooter1',
        #     'ElectricScooter2','KATECH-RoadSign','KR_Sign_SL_100','KR_Sign_SL_110','KR_Sign_SL_30','KR_Sign_SL_40','KR_Sign_SL_50',
        #     'KR_Sign_SL_60','KR_Sign_SL_70','KR_Sign_SL_80','KR_Sign_SL_90','NCAP_GVT','OBJ_Nuro','OBJ_toyoto_e_palette','Rubber_Cone',
        #     'Scooter1','Scooter2','SportBike','Tree01','Tree02','Tree03','Tree04','Tree05','Tree06','Tree07','Tree08','Tree09',
        #     'US_Sign_SLSCH_20','US_Sign_SLSCH_35','US_Sign_SL_15','US_Sign_SL_20','US_Sign_SL_25','US_Sign_SL_30''US_Sign_SL_35','US_Sign_SL_40',
        #     'US_Sign_SL_45','US_Sign_SL_50','US_Sign_SL_55','US_Sign_SL_60','US_Sign_SL_65','US_Sign_SL_70','US_Sign_SL_75','etri_bump_0.15m',
        #     'etri_bump_0.1m_Wide','etri_bump_0.1m','etri_bump_0.25m','etri_bump_0.2m_Wide','etri_bump_0.2m','etri_bump_0.35m','etri_bump_0.3m',
        #     'etri_bump_0.3m_Wide','etri_bump_0.4m','etri_bump_0.5m','etri_bump_0.7m','etri_bump_1.0m','etri_slope','etri_slope_15-20',
        #     'etri_slope_16-21','etri_slope_17-22','etri_slope_18-23','etri_slope_19-24','obj_korea_soldier','obj_obstacle_dog','obj_usa_soldier',
        #     'ped_pullbike'
        #     ]
        self.object_type = self.mis_object_type[0]
        self.misc_object_category = QComboBox()
        self.misc_object_category.addItems(self.mis_object_type)
        self.mis_object_type_name = QLineEdit()
        self.misc_object_category.activated[str].connect(self.onActivated)
        
        self.mis_object_name = QLineEdit()
        form_layout = QFormLayout()
        form_layout.addRow('Entity Name:     ', self.mis_object_name)
       
        object_category_layout = QFormLayout()
        object_category_layout.addRow('Object Category:', self.misc_object_category)
        
        object_type_name_layout = QFormLayout()
        object_type_name_layout.addRow('Object Type Name:', self.mis_object_type_name)
        
        hbox = QHBoxLayout()
        hbox.addLayout(object_category_layout)
        hbox.addLayout(object_type_name_layout)
        
        vbox = QVBoxLayout()
        #vbox.addSpacing(10)
        vbox.addLayout(form_layout)
        #vbox.addSpacing(10)
        vbox.addLayout(hbox)
        vbox.addStretch()
        groupbox.setLayout(vbox)
        return groupbox

    def misc_object_position(self):
        groupbox = QGroupBox('MiscObject Position')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.combo_position_type = QComboBox()
        self.combo_position_type.addItems(POSITION_LIST)

        self.combo_position_type.activated[str].connect(self.update_position)
        form_layout = QFormLayout()
        form_layout.addRow('Position : ', self.combo_position_type)
        
        inner_widget = QWidget()
        inner_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        inner_widget.setContentsMargins(0, 0, 0, 0)
        
        self.position_layout = QVBoxLayout(inner_widget)
        self.position_layout.setContentsMargins(0, 0, 0 ,0)
        self.world_position = WorldPositionWidget(self.position)
        self.link_position = LinkPositionWidget(self.position)
        self.relative_object_position = RelativeObjectPositionWidget()
        self.relative_world_position = RelativeWorldPositionWidget()
        self.position_layout.addWidget(self.world_position)
        self.position_layout.addWidget(self.relative_world_position)
        self.position_layout.addWidget(self.link_position)
        self.position_layout.addWidget(self.relative_object_position)

        form_layout.addWidget(inner_widget)
        groupbox.setLayout(form_layout)
        return groupbox
    
    def misc_object_property(self):
        groupbox = QGroupBox('MiscObject Property')
        groupbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        vbox_property = QVBoxLayout()
        nonnegative_validator = QDoubleValidator(bottom=0, decimals=8, notation=QDoubleValidator.StandardNotation)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("X scale"))
        self.scale_x = QLineEdit()
        self.scale_x.setValidator(nonnegative_validator)
        self.scale_x.setPlaceholderText("1.0")
        hbox1.addWidget(self.scale_x)
        hbox1.addWidget(QLabel("Y scale"))
        self.scale_y = QLineEdit()
        self.scale_y.setValidator(nonnegative_validator)
        self.scale_y.setPlaceholderText("1.0")
        hbox1.addWidget(self.scale_y)
        hbox1.addWidget(QLabel("Z scale"))
        self.scale_z = QLineEdit()
        self.scale_z.setValidator(nonnegative_validator)
        self.scale_z.setPlaceholderText("1.0")
        hbox1.addWidget(self.scale_z)
        
        vbox_property.addLayout(hbox1)
        vbox_property.addStretch()
        groupbox.setLayout(vbox_property)
        return groupbox
    
    def onActivated(self, text):
        self.object_type = text
    
    def set_default_position(self):
        self.hide_position_widgets()
        self.world_position.setVisible(True) # WorldPosition

    def hide_position_widgets(self):
        for i in range(self.position_layout.count()):
            self.position_layout.itemAt(i).widget().setVisible(False)

    def update_position(self, choice):
        self.hide_position_widgets()
        if choice == 'World Position':
            self.world_position.setVisible(True)
        elif choice == 'RelativeWorldPosition':
            self.relative_world_position.setVisible(True)
        elif choice == 'Link Position':
            self.link_position.setVisible(True)
        elif choice == 'RelativeObjectPosition':
            self.relative_object_position.setVisible(True)
        else:
            self.hide_position_widgets()

    def get_position_data(self):
        if self.combo_position_type.currentText() == 'World Position':
            return self.world_position.get_data()
        elif self.combo_position_type.currentText() == 'RelativeWorldPosition':
            return self.relative_world_position.get_data()
        elif self.combo_position_type.currentText() == 'Link Position':
            return self.link_position.get_data()
        elif self.combo_position_type.currentText() == 'RelativeObjectPosition':
            return self.relative_object_position.get_data()
    
    def showDialog(self):
        return super().exec_()
        
    def accept(self):        
        if self.mis_object_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set MiscObject's name")
            return
        if self.mis_object_name.text() in self.openscenario_importer.scenario_definition.entities.entities_dict:
            QMessageBox.warning(self, "Warning", "The Pedestrian name you entered already exists in the entities")
            return

        position_data = self.get_position_data()
        try:
            msg = ""
            if isinstance(position_data, WorldPosition):
                if position_data.attrib['x'] == 'unspecified' or position_data.attrib['y'] == 'unspecified':
                    msg = ": 'x' and 'y' should be specified"
            elif isinstance(position_data, LinkPosition):
                if position_data.attrib['id'] == 'unspecified':
                    msg = ": 'Link ID' should be specified"

            position_data.load()
            if isinstance(position_data, LinkPosition):
                if position_data.id not in self.openscenario_importer.mgeo.link_set.lines:
                    msg = ": The link doesn't exist"
                    raise ValueError(msg)
                
                if len(self.openscenario_importer.mgeo.link_set.lines[position_data.id].points) < position_data.index:
                    msg = ": The link index is out of range"
                    raise ValueError(msg)
        except:
            QMessageBox.warning(self, "Warning", "Invalid Position" + msg)
            return
        
        if self.mis_object_type_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set Object Type Name")
            return
        
        new_prop = Properties()
        scale_x = self.scale_x.text() if self.scale_x.text() != "" else "1.0"
        scale_y = self.scale_y.text() if self.scale_y.text() != "" else "1.0"
        scale_z = self.scale_z.text() if self.scale_z.text() != "" else "1.0"
        new_prop.add_property('scale_x', scale_x)
        new_prop.add_property('scale_y', scale_y)
        new_prop.add_property('scale_z', scale_z)
        
        attrib ={'name':self.mis_object_name.text()}
        misc_object_info = {'name':self.mis_object_type_name.text(),'mass':'0','miscObjectCategory':self.object_type}
        info = MiscObject(attrib=misc_object_info, properties=new_prop)
        new_object = ScenarioObject(attrib, ObjectType.miscellaneous, info)
        try:
            new_object.load()
        except:
            QMessageBox.warning(self, "Warning", "Invalid object info.")
            return
        
        init_action = self.openscenario_importer.scenario_definition.storyboard.init_element.init_action
        init_action.add_private_action(self.mis_object_name.text(), TeleportAction(position_data))
        self.openscenario_importer.scenario_definition.entities.scenario_objects.append(new_object)
        self.done(1)
    
    def reject(self):
        self.done(0)

# Add entity in tree
class VehicleModeWidget(VehicleModelUI):
    def __init__(self, openscenario_importer, position=None):
        QWidget.__init__(self)  # diaglog to widget
        self.openscenario_importer = openscenario_importer
        self.position = position
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.vehicle_info_group(), 0, 0)
        grid_layout.addWidget(self.vehicle_property(), 1, 0)
        self.ego_vehicle_property_radio_btn()
        self.setLayout(grid_layout)

    def accept(self):
        if self.vehicle_name.text() == '':
            raise AttributeError("Please Set NPC Vehicle's name")
        #NPC Double Check
        if self.vehicle_name.text() in self.openscenario_importer.scenario_definition.entities.entities_dict:
            raise AttributeError("The Vehicle name you entered already exists in the entities")
        
        attrib = {'name':self.vehicle_name.text()}
        info = Vehicle(attrib={'name': self.model_name, 'vehicleCategory': 'car'})
        new_object = ScenarioObject(attrib, ObjectType.vehicle, info)

        return new_object

class PedestrianModeWidget(PedestrianModelUI):
    def __init__(self, openscenario_importer, position=None):
        QWidget.__init__(self)  # diaglog to widget
        self.openscenario_importer = openscenario_importer
        self.position = position
        grid_layout = QGridLayout()
        # pedestrian_info + pedestrian_property
        grid_layout.addWidget(self.pedestrian_info_group(), 0, 0)
        grid_layout.addWidget(self.pedestrian_property(), 1, 0)
        self.setLayout(grid_layout)
        
    def accept(self):
        if self.pedestrian_name.text() == '':
            raise AttributeError("Please Set Pedestrian's name")
        if self.pedestrian_name.text() in self.openscenario_importer.scenario_definition.entities.entities_dict:
            raise AttributeError("The Pedestrian name you entered already exists in the entities")
        if self.active_distance.text() == '':
            raise AttributeError("Please Set Active Distance")
        if self.move_distance.text() == '':
            raise AttributeError("Please Set Move Distance")
        
        new_prop = Properties()
        new_prop.add_property('activeDistance', self.active_distance.text())
        new_prop.add_property('moveDistance', self.move_distance.text())  
        attrib = {'name':self.pedestrian_name.text()}
        pedestrian_info = {'name':self.model_name,'mass':"0",'pedestrianCategory':'pedestrian'}
        info = Pedestrian(attrib=pedestrian_info, properties=new_prop)
        new_object = ScenarioObject(attrib, ObjectType.pedestrian, info)

        return new_object

class MiscObjectModeWidget(MiscObjectModelUI):
    def __init__(self, openscenario_importer, position=None):
        QWidget.__init__(self)  # diaglog to widget
        self.openscenario_importer = openscenario_importer
        self.position = position
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.misc_object_category_model())
        grid_layout.addWidget(self.misc_object_property())
        self.setLayout(grid_layout)

    def accept(self):
        if self.mis_object_name.text() == '':
            raise AttributeError("Please Set MiscObject's name")
        if self.mis_object_name.text() in self.openscenario_importer.scenario_definition.entities.entities_dict:
            raise AttributeError("The Misc object name you entered already exists in the entities")
        if self.mis_object_type_name.text() == '':
            raise AttributeError("Please Set Object Type Name")
        
        new_prop = Properties()
        scale_x = self.scale_x.text() if self.scale_x.text() != "" else "1.0"
        scale_y = self.scale_y.text() if self.scale_y.text() != "" else "1.0"
        scale_z = self.scale_z.text() if self.scale_z.text() != "" else "1.0"
        new_prop.add_property('scale_x', scale_x)
        new_prop.add_property('scale_y', scale_y)
        new_prop.add_property('scale_z', scale_z)
        
        attrib ={'name':self.mis_object_name.text()}
        misc_object_info = {'name':self.mis_object_type_name.text(),'mass':'0','miscObjectCategory':self.object_type}
        info = MiscObject(attrib=misc_object_info, properties=new_prop)
        new_object = ScenarioObject(attrib, ObjectType.miscellaneous, info)

        return new_object

class AddEntityInTreeUI(QDialog):
    def __init__(self, openscenario_importer, position=None):
        super().__init__()
        self.openscenario_importer = openscenario_importer
        self.position = position
        self.initUI()
        self.show()

    def initUI(self):
        self.scroll_area=QScrollArea()
        self.main_layout=QVBoxLayout()
        self.scroll_area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 880, 390))
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)
        
        self.stack_widget = QStackedWidget()
        self.stack_widget.addWidget(VehicleModeWidget(self.openscenario_importer))
        self.stack_widget.addWidget(PedestrianModeWidget(self.openscenario_importer))
        self.stack_widget.addWidget(MiscObjectModeWidget(self.openscenario_importer))

        self.grid_layout.addWidget(self.select_entity_widget(), 0, 0, Qt.AlignCenter)
        self.grid_layout.addWidget(self.stack_widget, 1, 0)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.insertWidget(-1, self.button_box, 1)

        self.setLayout(self.main_layout)
        self.setFixedWidth(880)
        self.setMinimumHeight(420)
        self.setWindowTitle('Add Entity Wizard')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def select_entity_widget(self):
        entity_types = ["Vehicle", "Pedestrian", "Misc Object"]
        groupbox = QGroupBox("Select Entity type")
        self.entity_type_combo_box = QComboBox()
        self.entity_type_combo_box.addItems(entity_types)
        self.entity_type_combo_box.setFixedWidth(405)
        self.entity_type_combo_box.currentIndexChanged.connect(self.update_entity_widget)

        information_this = QLabel()
        information_this.setText('※ This will only create entity without init action.')

        form_layout = QFormLayout()
        form_layout.addRow('Entity type:', self.entity_type_combo_box)
        form_layout.addRow(information_this)

        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)

        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(820)
        return groupbox

    def update_entity_widget(self, index):
        self.stack_widget.setCurrentIndex(index)

    def showDialog(self):
        return super().exec_()

    def accept(self):
        try:
            new_object = self.stack_widget.currentWidget().accept()
        except AttributeError as ae:
            QMessageBox.warning(self, "Warning", str(ae))
            return
        except:
            QMessageBox.warning(self, "Warning", "An error occurred while creating object.")
            return
        try:
            new_object.load()
        except:
            QMessageBox.warning(self, "Warning", "Invalid entity info.")
            return
        self.openscenario_importer.scenario_definition.entities.scenario_objects.append(new_object)
        self.done(1)
    
    def reject(self):
        self.done(0)
