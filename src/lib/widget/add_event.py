import os
import sys


current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.openscenario.class_defs.condition import EntityConditionSpace, ValueConditionSpace
from lib.openscenario.class_defs.enumerations import ConditionEdge, Priority
from lib.openscenario.class_defs.global_action import GlobalActionSpace
from lib.openscenario.class_defs.private_action import PrivateActionSpace
from lib.openscenario.class_defs.user_defined_action import UserDefinedActionSpace
from lib.openscenario.class_defs.storyboard_element.storyboard import Private
from lib.openscenario.class_defs.storyboard_element.maneuver_group import ManeuverGroup
from lib.openscenario.class_defs.storyboard_element.maneuver import Maneuver
from lib.openscenario.class_defs.storyboard_element.event import Event
from lib.openscenario.class_defs.storyboard_element.action import _Action
from lib.openscenario.class_defs.entities import Actors
from lib.widget.scenario_base_ui import *

from lib.common.logger import Logger
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

DEPRECATED_ACTION_LIST = ['ActivateControllerAction']
DEPRECATED_CONDITION_LIST = ['ReachPositionCondition']

def remove_deprecate_action(global_actions, private_actions, user_defined_actions):
    for action in GlobalActionSpace.action_space:
        if action not in DEPRECATED_ACTION_LIST:
            global_actions.append(action)
    
    for action in PrivateActionSpace.action_space:
        if action not in DEPRECATED_ACTION_LIST:
            private_actions.append(action)
    
    for action in UserDefinedActionSpace.action_space:
        if action not in DEPRECATED_ACTION_LIST:
            user_defined_actions.append(action)
    return global_actions, private_actions, user_defined_actions

def remove_deprecate_condtion(value_conditions, entity_conditions):
    for condition in ValueConditionSpace.condition_space:
        if condition not in DEPRECATED_CONDITION_LIST:
            value_conditions.append(condition)
    
    for condition in EntityConditionSpace.condition_space:
        if condition not in DEPRECATED_CONDITION_LIST:
            entity_conditions.append(condition)
    return value_conditions, entity_conditions

"""ADD EVENT UI"""
class AddEventUI(QDialog):
    def __init__(self, openscenario_importer):
        super().__init__()
        self.openscenario_importer = openscenario_importer
        self.mgeo = self.openscenario_importer.mgeo
        self.initUI()
        self.show()
        
    def initUI(self):
        self.scroll_area=QScrollArea()
        self.main_layout=QHBoxLayout()
        self.scroll_area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 880, 500))
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)
        self.grid_layout.addWidget(self.actor_info(), 0, 0)
        self.grid_layout.addWidget(self.event_info(), 1, 0)
        self.grid_layout.addWidget(self.action_info(), 2, 0)
        self.set_default_action_widgets()
        self.grid_layout.addWidget(self.condition_info(), 3, 0)
        self.set_default_condition_widgets()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.grid_layout.addWidget(self.button_box, 4, 0)
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.scroll_area)
        self.setLayout(self.main_layout)
        self.setGeometry(300, 300, 900, 810)
        self.setFixedSize(900, 810)
        self.setWindowTitle('Add Events')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def actor_info(self):
        groupbox  = QGroupBox('Actor Information')
        self.actor_name = QLineEdit()
        self.actor_name.setFixedWidth(405)
        
        hbox1 = QFormLayout()
        hbox1.addRow('Name:', self.actor_name)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(830)
        return groupbox
    
    def event_info(self):
        groupbox = QGroupBox('Event Information')
        self.maximumExecutionCount = QLineEdit()
        self.maximumExecutionCount.setValidator(QIntValidator(1, 999))
        self.maximumExecutionCount.setPlaceholderText('Range [1..inf]')
        self.maximumExecutionCount.setFixedWidth(405)
        self.event_name = QLineEdit()
        self.event_name.setFixedWidth(405)
        
        priority_list = [str(p.name) for p in Priority]
        self.priority_combo_box = QComboBox()
        self.priority_combo_box.addItems(priority_list)
        self.priority_combo_box.setFixedWidth(405)
        
        form_layout = QFormLayout()
        form_layout.addRow('MaximumExecutionCount:', self.maximumExecutionCount)
        form_layout.addRow('Name:', self.event_name)
        form_layout.addRow('Priority', self.priority_combo_box)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(830)
        return groupbox
    
    def action_info(self):
        groupbox = QGroupBox('Action Information')
        self.action_type = ['Global Action', 'Private Action', 'User Defined Action']
        
        self.global_actions = []
        self.user_defined_actions = []
        self.private_actions = []
        
        self.global_actions, self.private_actions, self.user_defined_actions = remove_deprecate_action(self.global_actions, self.private_actions, self.user_defined_actions)
        self.action_name = QLineEdit()
        self.action_name.setFixedWidth(405)
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.action_name)
        
        self.action_type_combo_box = QComboBox()
        self.action_type_combo_box.setFixedWidth(200)
        self.action_type_combo_box.addItems(self.action_type)
        self.action_sublists = self.global_actions, self.private_actions, self.user_defined_actions
        self.combo_actions = QComboBox()
        self.combo_actions.setFixedWidth(200)
        self.combo_actions.addItems(self.global_actions)
        self.action_type_combo_box.currentIndexChanged.connect(self.update_action_type_combo_box)
        self.action_type_combo_box.activated[str].connect(self.update_sub_action)
        self.combo_actions.activated[str].connect(self.update_action)
        
        self.action_layout = QVBoxLayout()
        self.environment_action_widget = EnvironmentActionWidget()
        self.entity_action_widget = EntityActionWidget()
        self.parameter_action_widget = ParameterActionWidget()
        self.infrastructure_action_widget = InfrastructureActionWidget(mgeo=self.mgeo)
        self.traffic_action_widget = TrafficActionWidget()
        self.variable_action_widget = VariableActionWidget()
        self.longitudinal_action_widget = LongitudinalActionWidget()
        self.lateral_action_widget = LateralActionWidget()
        self.visibility_action_widget = VisibilityActionWidget()
        self.synchronize_action_widget = SynchronizeActionWidget()
        self.controller_action_widget = ControllerActionWidget()
        self.teleport_action_widget = TeleportActionWidget()
        self.routing_action_widget = RoutingActionWidget()
        self.appearance_action_widget = AppearanceActionWidget()
        self.parking_action_widget = ParkingActionWidget()
        self.fault_injection_action_widget = FaultInjectionActionWidget()
        self.create_map_object_action_widget = CreateMapObjectActionWidget()
        self.add_all_actions()
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.action_type_combo_box)
        hbox2.addSpacing(1)
        hbox2.addWidget(self.combo_actions)
        form_layout.addRow('Type: ', hbox2)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(self.action_layout)
        vbox.addStretch()
        groupbox.setFixedWidth(830)
        groupbox.setLayout(vbox)
        return groupbox

    def condition_info(self):
        groupbox = QGroupBox('Condition Information')
        condition_edge_list = [str(condition_edge.name) for condition_edge in ConditionEdge]
        self.condition_edge_combo_box = QComboBox()
        self.condition_edge_combo_box.addItems(condition_edge_list)
        self.condition_edge_combo_box.setToolTip('specifies the edge when the condition is evaluated to true')
        condition_type = ['ByEntityCondition', 'ByValueCondition']
        self.value_condition_list = []
        self.entity_condition_list = []

        # Check Deprecated Condition Element
        self.value_condition_list, self.entity_condition_list = remove_deprecate_condtion(self.value_condition_list, self.entity_condition_list)
        
        self.condition_name = QLineEdit()
        self.condition_name.setToolTip('Name of the condition')
        self.condition_delay = QLineEdit()
        self.condition_delay.setValidator(QDoubleValidator(0, 9999.0, 2))
        self.condition_delay.setPlaceholderText('Range [0..inf]')
        self.condition_delay.setToolTip('Time elapsed after the edge condition is verified')
        
        self.condition_name.setFixedWidth(405)
        self.condition_delay.setFixedWidth(405)
        self.condition_edge_combo_box.setFixedWidth(405)
        
        form_layout = QFormLayout()
        form_layout.addRow('Name:', self.condition_name)
        form_layout.addRow('Dalay(s):', self.condition_delay)
        form_layout.addRow('ConditionEdge:', self.condition_edge_combo_box)
        
        self.condition_type_combo_box = QComboBox()
        self.condition_type_combo_box.setFixedWidth(200)
        self.condition_type_combo_box.addItems(condition_type)
        self.condition_sublists = self.entity_condition_list, self.value_condition_list
        
        self.conditions_combo_box = QComboBox()
        self.conditions_combo_box.setFixedWidth(200)
        self.conditions_combo_box.addItems(self.entity_condition_list)
        self.condition_type_combo_box.currentIndexChanged.connect(self.update_condition_type_combo_box)
        self.conditions_combo_box.activated[str].connect(self.update_condition)
        self.condition_type_combo_box.activated[str].connect(self.update_sub_condition)
        
        # ByValueCondition
        self.condition_layout = QVBoxLayout()
        self.parameter_condition_widget = ParameterConditionWidget()
        self.time_of_day_condition_widget = TimeOfDayConditionWidget()
        self.simulation_time_condition_widget = SimulationTimeConditionWidget()
        self.storyboard_element_state_condition_widget = StoryboardElementStateConditionWidget()
        self.user_definedvalue_condition_widget = UserDefinedValueConditionWidget()
        self.traffic_signal_condition_widget = TrafficSiganlConditionWidget()
        self.traffic_signal_controller_condition_widget = TrafficSignalControllerConditionWidget()
        self.variable_condition_widget = VariableConditionWidget()
        # ByEntityCondition
        self.end_of_road_condition_widget = EndOfRoadConditionWidget()
        self.collision_condition_widget = CollisionConditionWidget()
        self.off_road_condition_widget = OffroadConditionWidget()
        self.time_headway_condition_widget = TimeHeadwayConditionWidget()
        self.time_to_collision_condition_widget = TimeToCollisionConditionWidget()
        self.acceleration_condition_widget = AccelerationConditionWidget()
        self.stand_still_condition_widget = StandStillConditionWidget()
        self.speed_condition_widget = SpeedConditionWidget()
        self.relative_speed_condition_widget = RelativeSpeedConditionWidget()
        self.traveled_distance_condition_widget = TraveledDistanceConditionWidget()
        self.distance_condition_widget = DistanceConditionWidget()
        self.relative_distance_condition_widget = RelativeDistanceConditionWidget()
        self.relative_clearance_condition_widget = RelativeClearanceConditionWidget()
        self.add_all_conditions()
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.condition_type_combo_box)
        hbox2.addSpacing(1)
        hbox2.addWidget(self.conditions_combo_box)
        form_layout.addRow('Type: ', hbox2)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        vbox.addLayout(self.condition_layout)
        vbox.addStretch()
        groupbox.setFixedWidth(830)
        groupbox.setLayout(vbox)
        return groupbox
            
    def update_action_type_combo_box(self, index):
        self.combo_actions.clear()
        self.combo_actions.addItems(self.action_sublists[index])
    
    def update_condition_type_combo_box(self, index):
        self.conditions_combo_box.clear()
        self.conditions_combo_box.addItems(self.condition_sublists[index])
    
    def update_sub_action(self, text):
        if text == 'Global Action':
            self.set_default_action_widgets()
        elif text == 'Private Action':
            self.set_default_private_action_widgets()
        else:
            self.set_default_user_defined_action_widget()
    
    def update_sub_condition(self, text):
        if text == 'ByValueCondition':
            self.set_default_by_value_widgets()
        else:
            self.set_default_condition_widgets()
    
    def set_default_private_action_widgets(self):
        self.hide_all_action_widgets()
        self.longitudinal_action_widget.show()
    
    def set_default_user_defined_action_widget(self):
        self.hide_all_action_widgets()
        self.fault_injection_action_widget.show()
    
    def set_default_action_widgets(self):
        self.hide_all_action_widgets()
        self.environment_action_widget.show()
    
    def set_default_by_value_widgets(self):
        self.hide_all_condition_widgets()
        self.parameter_condition_widget.show()
    
    def set_default_condition_widgets(self):
        self.hide_all_condition_widgets()
        self.end_of_road_condition_widget.show()
    
    def hide_all_action_widgets(self):
        """Set widgets in action layout to be hidden"""
        for i in range(self.action_layout.count()):
            self.action_layout.itemAt(i).widget().hide()
    
    def hide_all_condition_widgets(self):
        """Set widgets in action layout to be hidden"""
        for i in range(self.condition_layout.count()):
            self.condition_layout.itemAt(i).widget().hide()
    
    def add_all_actions(self):
        '''Add all Private Actions into 'Action Layout'''
        self.action_layout.addWidget(self.environment_action_widget)
        self.action_layout.addWidget(self.entity_action_widget)
        self.action_layout.addWidget(self.parameter_action_widget)
        self.action_layout.addWidget(self.infrastructure_action_widget)
        self.action_layout.addWidget(self.traffic_action_widget)
        self.action_layout.addWidget(self.variable_action_widget)
        self.action_layout.addWidget(self.longitudinal_action_widget)
        self.action_layout.addWidget(self.lateral_action_widget)
        self.action_layout.addWidget(self.visibility_action_widget)
        self.action_layout.addWidget(self.synchronize_action_widget)
        #self.action_layout.addWidget(self.activate_controller_action_widget)
        self.action_layout.addWidget(self.controller_action_widget)
        self.action_layout.addWidget(self.teleport_action_widget)
        self.action_layout.addWidget(self.routing_action_widget)
        self.action_layout.addWidget(self.appearance_action_widget)
        self.action_layout.addWidget(self.parking_action_widget)
        self.action_layout.addWidget(self.fault_injection_action_widget)
        self.action_layout.addWidget(self.create_map_object_action_widget)
    
    def add_all_conditions(self):
        '''Add all Conditions into 'Condition Layout'''
        self.condition_layout.addWidget(self.end_of_road_condition_widget)
        self.condition_layout.addWidget(self.collision_condition_widget)
        self.condition_layout.addWidget(self.off_road_condition_widget)
        self.condition_layout.addWidget(self.time_headway_condition_widget)
        self.condition_layout.addWidget(self.time_to_collision_condition_widget)
        self.condition_layout.addWidget(self.acceleration_condition_widget)
        self.condition_layout.addWidget(self.stand_still_condition_widget)
        self.condition_layout.addWidget(self.speed_condition_widget)
        self.condition_layout.addWidget(self.relative_speed_condition_widget)
        self.condition_layout.addWidget(self.traveled_distance_condition_widget)
        #self.condition_layout.addWidget(self.reach_position_condition_widget)
        self.condition_layout.addWidget(self.distance_condition_widget)
        self.condition_layout.addWidget(self.relative_distance_condition_widget)
        self.condition_layout.addWidget(self.relative_clearance_condition_widget)
        self.condition_layout.addWidget(self.parameter_condition_widget)
        self.condition_layout.addWidget(self.time_of_day_condition_widget)
        self.condition_layout.addWidget(self.simulation_time_condition_widget)
        self.condition_layout.addWidget(self.storyboard_element_state_condition_widget)
        self.condition_layout.addWidget(self.user_definedvalue_condition_widget)
        self.condition_layout.addWidget(self.traffic_signal_condition_widget)
        self.condition_layout.addWidget(self.traffic_signal_controller_condition_widget)
        self.condition_layout.addWidget(self.variable_condition_widget)
                
    def update_action(self, choice):
        self.hide_all_action_widgets()
        if choice == 'EnvironmentAction':
            self.environment_action_widget.show()
        elif choice == 'EntityAction':
            self.entity_action_widget.show()
        elif choice == 'ParameterAction':
            self.parameter_action_widget.show()
        elif choice == 'InfrastructureAction':
            self.infrastructure_action_widget.show()
        elif choice == 'TrafficAction':
            self.traffic_action_widget.show()
        elif choice == 'VariableAction':
            self.variable_action_widget.show()
        elif choice == 'LongitudinalAction':
            self.longitudinal_action_widget.show()
        elif choice == 'LateralAction':
            self.lateral_action_widget.show()
        elif choice == 'VisibilityAction':
            self.visibility_action_widget.show()
        elif choice == 'SynchronizeAction':
            self.synchronize_action_widget.show()
        # elif choice == 'ActivateControllerAction':
        #     self.activate_controller_action_widget.show()
        elif choice == 'ControllerAction':
            self.controller_action_widget.show()
        elif choice == 'TeleportAction':
            self.teleport_action_widget.show()
        elif choice == 'RoutingAction':
            self.routing_action_widget.show()
        elif choice == 'AppearanceAction':
            self.appearance_action_widget.show()
        elif choice == 'ParkingAction':
            self.parking_action_widget.show()
        elif choice == 'FaultInjectionAction':
            self.fault_injection_action_widget.show()
        elif choice == 'CreateMapObjectAction':
            self.create_map_object_action_widget.show()
        else:
            pass
            # raise Error
    
    def update_condition(self, choice):
        self.hide_all_condition_widgets()
        if choice == 'ParameterCondition':
            self.parameter_condition_widget.show()
        elif choice == 'TimeOfDayCondition':
            self.time_of_day_condition_widget.show()
        elif choice == 'SimulationTimeCondition':
            self.simulation_time_condition_widget.show()
        elif choice == 'StoryboardElementStateCondition':
            self.storyboard_element_state_condition_widget.show()
        elif choice == 'UserDefinedValueCondition':
            self.user_definedvalue_condition_widget.show()
        elif choice == 'TrafficSignalCondition':
            self.traffic_signal_condition_widget.show()
        elif choice == 'TrafficSignalControllerCondition':
            self.traffic_signal_controller_condition_widget.show()
        elif choice == 'VariableCondition':
            self.variable_condition_widget.show()
        elif choice == 'EndOfRoadCondition':
            self.end_of_road_condition_widget.show()
        elif choice == 'CollisionCondition':
            self.collision_condition_widget.show()
        elif choice == 'OffroadCondition':
            self.off_road_condition_widget.show()
        elif choice == 'TimeHeadwayCondition':
            self.time_headway_condition_widget.show()
        elif choice == 'TimeToCollisionCondition':
            self.time_to_collision_condition_widget.show()
        elif choice == 'AccelerationCondition':
            self.acceleration_condition_widget.show()
        elif choice == 'StandStillCondition':
            self.stand_still_condition_widget.show()
        elif choice == 'SpeedCondition':
            self.speed_condition_widget.show()
        elif choice == 'RelativeSpeedCondition':
            self.relative_speed_condition_widget.show()
        elif choice == 'TraveledDistanceCondition':
            self.traveled_distance_condition_widget.show()
        # elif choice == 'ReachPositionCondition':
        #     self.reach_position_condition_widget.show()
        elif choice == 'DistanceCondition':
            self.distance_condition_widget.show()
        elif choice == 'RelativeDistanceCondition':
            self.relative_distance_condition_widget.show()
        elif choice == 'RelativeClearanceCondition':
            self.relative_clearance_condition_widget.show()
        else:
            pass
            #raise Error
    
    def get_current_visible_action_widget(self):
        for i in range(self.action_layout.count()):
            widget = self.action_layout.itemAt(i).widget()
            if widget.isVisible():
                return widget
    
    def get_current_visible_condition_widget(self):
        for i in range(self.condition_layout.count()):
            widget = self.condition_layout.itemAt(i).widget()
            if widget.isVisible():
                return widget
    
    def showDialog(self):
        return super().exec_()
    
    def accept(self):
        # Validity check
        if self.event_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Event Name")
            return
        if self.action_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Action Name")
            return
        if self.condition_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Condition Name")
            return
        if self.condition_delay.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Condition Delay")
            return

        # Get an action element
        current_visible_action_widget = self.get_current_visible_action_widget()
        action = current_visible_action_widget.get_data()
        try:
            action.load()
        except BaseException as e:
            QMessageBox.warning(self, "Warning", "Failed to create an action element")
            return

        # Get a condition element
        current_visible_condition_widget = self.get_current_visible_condition_widget()
        condition = current_visible_condition_widget.get_data()
        triggering_entities = None
        if self.condition_type_combo_box.currentText() == 'ByEntityCondition':
            triggering_entities = current_visible_condition_widget.triggering_entities_widget.get_data()
        try:
            condition.load()
            if triggering_entities:
                triggering_entities.load()
        except:
            QMessageBox.warning(self, "Warning", "Failed to create a condition element")
            return

        # Create an Event element
        condition_attrib = {'name':self.condition_name.text(),
                            'delay':self.condition_delay.text(),
                            'conditionEdge':self.condition_edge_combo_box.currentText()}
        start_trigger = Trigger([ConditionGroup([Condition(condition_attrib, triggering_entities, condition)])])
        
        new_action = _Action({'name':self.action_name.text()}, action)
        event_attrib = {'name':self.event_name.text(),
                        'maximumExecutionCount':self.maximumExecutionCount.text(),
                        'priority':self.priority_combo_box.currentText()}
        new_event = Event(event_attrib, [new_action], start_trigger)
        new_entity_ref = EntityRef({'entityRef': self.actor_name.text()})
        try:
            new_event.load()
            new_entity_ref.load()
        except:
            QMessageBox.warning(self, "Warning", "Failed to create an event element")
            return
 
        story_elements = self.openscenario_importer.scenario_definition.storyboard.stories
        for story in story_elements:
            for act in story.acts:
                for maneuver_group in act.maneuver_groups:
                    # Find the same Actor in ManeuverGroups
                    entity_refs = maneuver_group.actors.get_entity_refs()
                    if (len(entity_refs) == 0 and new_entity_ref.entity_refs == '') or \
                            (len(entity_refs) == 1 and new_entity_ref.entity_refs in entity_refs):
                        if len(maneuver_group.maneuvers) == 0:
                            # Create new maneuver
                            new_maneuver = Maneuver({'name': "Maneuver_" + new_event.name}, 
                                                    None,
                                                    [new_event])
                            maneuver_group.maneuvers.append(new_maneuver)
                        else:
                            maneuver_group.maneuvers[-1].events.append(new_event)
                        
                        self.done(1)
                        return

        # Create New ManeuverGroup
        new_entity_refs = [] if new_entity_ref.entity_refs == "" else [new_entity_ref]
        new_maneuver = Maneuver({'name': "Maneuver_" + new_event.name},
                                None,
                                [new_event])
        new_maneuver_group = ManeuverGroup({'name': "ManueverGroup_" + new_event.name},
                                           Actors({'selectTriggeringEntities': 'false'}, new_entity_refs),
                                           [new_maneuver])
        story_elements[-1].acts[-1].maneuver_groups.append(new_maneuver_group)
        self.done(1)
    
    def reject(self):
        self.done(0)


"""ADD INIT ACTION"""
class AddInitActionUI(AddEventUI):
    def __init__(self, scenario_importer, init_action_element, 
                 init_action_type="Global"):
        idx_dict = {"Global":0, "Private":1, "User Defined":2}
        self.init_action_element = init_action_element
        self.init_action_type = init_action_type + " Action"
        self.action_idx = idx_dict[init_action_type]
        self.scenario_obj_list = list(scenario_importer.scenario_object_dict.keys())
        super().__init__(scenario_importer)

    def initUI(self):
        self.scroll_area=QScrollArea()
        self.main_layout=QVBoxLayout()
        self.scroll_area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 880, 550))
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)

        self.grid_layout.addWidget(self.private_entity_ref_info(), 0, 0)
        action_group = self.action_info()
        action_group.resize(880, 600)
        self.grid_layout.addWidget(action_group, 1, 0)
        self.unused_widget_block()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.insertWidget(-1, self.button_box, 1)
        self.setLayout(self.main_layout)
        self.setFixedWidth(880)
        self.setMinimumHeight(600)
        self.setWindowTitle('Add Init Action')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))

    def private_entity_ref_info(self):
        groupbox = QGroupBox('Private Entity Reference')
        block_falg = False
        
        if self.action_idx != 1:
            entity_name_list = ["Can only be selected in private mode", ]
            block_falg = True
        elif not self.scenario_obj_list:
            entity_name_list = ["There is no Entity to choose from", ]
            block_falg = True
        else:
            entity_name_list = self.scenario_obj_list

        self.entity_combo_box = QComboBox()
        self.entity_combo_box.addItems(entity_name_list)
        self.entity_combo_box.setFixedWidth(405)
        self.entity_combo_box.setDisabled(block_falg)

        information_this = QLabel()
        information_this.setText('※ This is only used when adding Private.')

        form_layout = QFormLayout()
        form_layout.addRow('Entity Ref:', self.entity_combo_box)
        form_layout.addRow(information_this)
        
        vbox = QVBoxLayout()
        vbox.addLayout(form_layout)
        groupbox.setLayout(vbox)
        groupbox.setFixedWidth(810)
        return groupbox

    def unused_widget_block(self):
        # block name
        self.action_name.setText("Not used")
        self.action_name.setDisabled(True)

        # block action combobox
        self.action_type_combo_box.setCurrentIndex(self.action_idx)
        self.action_type_combo_box.setDisabled(True)

        # set sub action combobox
        self.update_sub_action(self.init_action_type)
        self.update_action_type_combo_box(self.action_idx)

    def accept(self):
        # Validity check
        if self.action_idx == 1 and not self.scenario_obj_list:
            QMessageBox.warning(self, "Warning", "Please [Edit-Add Scenario Objects] first")
            return
            
        # Get an action element
        try:
            action = self.get_current_visible_action_widget().get_data()
            action.load()
        except:
            QMessageBox.warning(self, "Warning", "Failed to create an action element")
            return
        
        # Add an action element
        if self.action_idx == 0:
            self.init_action_element.global_actions.append(action)
        elif self.action_idx == 1:
            selected_entity = self.entity_combo_box.currentText()
            for private in self.init_action_element.private_actions:
                if selected_entity in private.entity_refs:
                    private.actions.append(action)
                    break
            else:
                new_private = Private({'entityRef': selected_entity}, [action,])
                new_private.entity_refs = [selected_entity]
                self.init_action_element.private_actions.append(new_private)
        elif self.action_idx == 2:
            self.init_action_element.user_defined_actions.append(action)
        self.done(1)

"""ADD ACTION UI"""
class AddActionUI(AddEventUI):
    def __init__(self, openscenario_importer, event_element):
        self.event_element = event_element
        super().__init__(openscenario_importer)

    def initUI(self):
        self.scroll_area=QScrollArea()
        self.main_layout=QVBoxLayout()
        self.scroll_area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 880, 600))
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        action_group = self.action_info()
        action_group.resize(880, 600)
        self.grid_layout.addWidget(action_group, 0, 0)
        self.set_default_action_widgets()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.insertWidget(-1, self.button_box, 1)
        self.setLayout(self.main_layout)
        self.setFixedWidth(880)
        self.setMinimumHeight(600)
        self.setWindowTitle('Add Action Wizard')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def accept(self):
        # Validity check
        if self.action_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Action Name")
            return

        # Get an action element
        try:
            action = self.get_current_visible_action_widget().get_data()
            new_action = _Action({'name':self.action_name.text()}, action)
            new_action.load()
        except:
            QMessageBox.warning(self, "Warning", "Failed to create an action element")
            return
        
        # Add an action element
        self.event_element.actions.append(new_action)
        self.done(1)

"""ADD CONDITION UI"""
class AddConditionUI(AddEventUI):
    def __init__(self, openscenario_importer, condition_group_element):
        self.condition_group_element = condition_group_element
        super().__init__(openscenario_importer)

    def initUI(self):
        self.scroll_area=QScrollArea()
        self.main_layout=QVBoxLayout()
        self.scroll_area.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 880, 550))
        self.grid_layout = QGridLayout(self.scrollAreaWidgetContents)
        self.grid_layout.addWidget(self.condition_info(), 0, 0)
        self.set_default_condition_widgets()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.scroll_area.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.insertWidget(-1, self.button_box, 1)
        self.setLayout(self.main_layout)
        self.setFixedWidth(880)
        self.setMinimumHeight(550)
        self.setWindowTitle('Add Condition Wizard')
        self.setWindowFlags(self.windowFlags() | Qt.WindowFlags(Qt.WindowMinimizeButtonHint))
    
    def accept(self):
        # Validity check
        if self.condition_name.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Condition Name")
            return
        if self.condition_delay.text() == '':
            QMessageBox.warning(self, "Warning", "Please Set the Condition Delay")
            return

        # Get a condition element
        current_visible_condition_widget = self.get_current_visible_condition_widget()
        condition = current_visible_condition_widget.get_data()
        triggering_entities = None
        if self.condition_type_combo_box.currentText() == 'ByEntityCondition':
            triggering_entities = current_visible_condition_widget.triggering_entities_widget.get_data()
        try:
            condition.load()
            if triggering_entities:
                triggering_entities.load()
        except:
            QMessageBox.warning(self, "Warning", "Failed to create a condition element")
            return

        # Add a condition element
        condition_attrib = {'name':self.condition_name.text(),
                            'delay':self.condition_delay.text(),
                            'conditionEdge':self.condition_edge_combo_box.currentText()}
        self.condition_group_element.conditions.append(Condition(condition_attrib, triggering_entities, condition))
        self.done(1)