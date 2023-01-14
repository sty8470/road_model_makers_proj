import os
import sys
import ast
from xmlrpc.client import boolean

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from lib.command_manager.concrete_commands import EditPropUpdateJunction, EditPropUpdateLaneBoundary, EditPropUpdateLaneNode, EditPropUpdateLink, EditPropUpdateNode, EditPropUpdateParkingSpace, EditPropUpdateTrafficLight, EditPropUpdateTrafficSign, EditPropUpdateRoadPolygon, EditPropUpdateSurfaceMarking

from lib.common.logger import Logger
from lib.mgeo.class_defs import road_polygon_set
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction,  edit_lane_boundary, edit_singlecrosswalk
from lib.mgeo.edit.funcs import edit_mgeo_planner_map, edit_road_poly, edit_parking_space
from lib.widget.edit_scenario_item_prop import ScenarioPropertyEditor
from lib.widget.edit_item_prop import MGeoPropertyEditor

# 이 support.py 만 릴리즈 시 변경
from lib.mgeo.class_defs.support import supported_class
if supported_class['mscenario']:
    from lib.mscenario.class_defs.mscenario_item import MScenarioItem
    from lib.mscenario.edit.funcs import edit_vehicle, edit_obstacle, edit_pedestrian
if supported_class['openscenario']:
    from lib.openscenario.class_defs.openscenario_item import ScenarioItem


class DisplayProp:
    def set_prop(self, canvas, widget, sp, road_set=None):
        if sp is None or sp['id'] is None:
            return

        self.widget = widget
        self.widget.clear()

        self.canvas = canvas
        self.sp = sp

        if road_set is not None:
            self.mgeo_items = self.canvas.mgeo_planner_map
            if sp['type'] in MGeoItem:
                self.display_mgeo_prop(road_set)

        if supported_class['mscenario']:
            self.mscenario_item = self.canvas.mscenario
            if self.mscenario_item and sp['type'] in MScenarioItem:
                self.display_mscenario_prop(self.mscenario_item)

        if supported_class['openscenario']:
            if sp['type'] in ScenarioItem:
                self.display_openscenario_prop(sp['element'], self.widget)

    def display_mgeo_prop(self, road_set):
        if self.sp['type'] == MGeoItem.NODE:
            items = self.mgeo_items.node_set.nodes

        elif self.sp['type'] == MGeoItem.LINK:
            items = self.mgeo_items.link_set.lines

        elif self.sp['type'] == MGeoItem.TRAFFIC_LIGHT:
            items = self.mgeo_items.light_set.signals

        elif self.sp['type'] == MGeoItem.SYNCED_TRAFFIC_LIGHT:
            items = self.mgeo_items.synced_light_set.synced_signals

        elif self.sp['type'] == MGeoItem.INTERSECTION_CONTROLLER:
            items = self.mgeo_items.intersection_controller_set.intersection_controllers

        elif self.sp['type'] == MGeoItem.TRAFFIC_SIGN:
            items = self.mgeo_items.sign_set.signals

        elif self.sp['type'] == MGeoItem.JUNCTION:
            items = self.mgeo_items.junction_set.junctions

        elif self.sp['type'] == MGeoItem.ROAD and (road_set is not None or len(road_set) == 0):
            items = road_set

        elif self.sp['type'] == MGeoItem.LANE_NODE:
            items = self.mgeo_items.lane_node_set.nodes

        elif self.sp['type'] == MGeoItem.LANE_BOUNDARY:
            items = self.mgeo_items.lane_boundary_set.lanes

        elif self.sp['type'] == MGeoItem.SINGLECROSSWALK:
            items = self.mgeo_items.scw_set.data
        
        elif self.sp['type'] == MGeoItem.CROSSWALK:
            items = self.mgeo_items.cw_set.data
            
        elif self.sp['type'] == MGeoItem.ROADPOLYGON:
            items = self.mgeo_items.road_polygon_set.data

        elif self.sp['type'] == MGeoItem.PARKING_SPACE:
            items = self.mgeo_items.parking_space_set.data

        elif self.sp['type'] == MGeoItem.SURFACE_MARKING:
            items = self.mgeo_items.sm_set.data
        
        # merge 했을 때 하이라이트 했던 link가 사라지면 key값이 없어서 에러가 발생함
        try:
            i = items[self.sp['id']]
            try:
                item = i.item_prop()
            except:
                pass
            widget = QTreeWidgetItem(self.widget)
            widget.setText(0, self.sp['type'].name)
            if self.sp['type'] == MGeoItem.ROAD:
                widget.setText(1, str(i.road_id))
            else:
                widget.setText(1, str(i.idx))
            for tree in item:
                tree_item = QTreeWidgetItem(widget)
                tree_item.setText(0, tree)
                tree_item.setText(1, str(item[tree]['type']))
                tree_item.setText(2, str(item[tree]['value']))

            widget.setExpanded(True)
        except:
            return

    def display_mscenario_prop(self, scenario_item=None):
        if scenario_item is not None:
            if self.sp['type'] == MScenarioItem.EGO_VEHICLE and scenario_item is not None:
                item = scenario_item.ego_vehicle

            elif self.sp['type'] == MScenarioItem.SURROUNDING_VEHICLE and scenario_item is not None:
                vehicle_list = scenario_item.vehicle_list
                for vehicle in vehicle_list:
                    if str(vehicle.id) == self.sp['id'] or vehicle.id == self.sp['id']:
                        item = vehicle
                
            elif self.sp['type'] == MScenarioItem.PEDESTRIAN and scenario_item is not None:
                pedestrian_list = scenario_item.pedestrian_list
                for pedestrian in pedestrian_list:
                    if str(pedestrian.id) == self.sp['id'] or pedestrian.id == self.sp['id']:
                        item = pedestrian
                
            elif self.sp['type'] == MScenarioItem.OBSTACLE and scenario_item is not None:
                obstacle_list = scenario_item.obstacle_list
                for obstacle in obstacle_list:
                    if str(obstacle.id) == self.sp['id'] or obstacle.id == self.sp['id']:
                        item = obstacle

        if self.sp['type'] == MScenarioItem.EGO_VEHICLE:
            mitem = item.item_prop(True)
        else:
            mitem = item.item_prop()
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(item.id))
        for tree in mitem:
            tree_item = QTreeWidgetItem(widget)
            tree_item.setText(0, tree)
            tree_item.setText(1, str(mitem[tree]['type']))
            tree_item.setText(2, str(mitem[tree]['value']))

        widget.setExpanded(True)
    
    def display_openscenario_prop(self, scenario_item, parent_widget):
        self_widget = QTreeWidgetItem(parent_widget)
        self_widget.setText(0, type(scenario_item).__name__)
        if hasattr(scenario_item, 'attrib'):
            for key, val in scenario_item.attrib.items():
                widget = QTreeWidgetItem(self_widget)
                widget.setText(0, key)
                widget.setText(1, scenario_item.attrib_type[key])
                widget.setText(2, val)
                widget.setData(3, Qt.UserRole, scenario_item)
                widget.setExpanded(True)

        for element in scenario_item.get_child_elements():
            # widget = QTreeWidgetItem(self_widget)
            # widget.setText(0, type(element).__name__)
            self.display_openscenario_prop(element, self_widget)
        
        self_widget.setExpanded(True)

    def edit_item_prop(self, item, column):
        selectItem = self.sp
        element = item.data(3, Qt.UserRole)
        # OpenScenario Item
        if type(element).__name__ in ScenarioItem._member_names_:
            if self.canvas.osc_client_triggered == True:
                return
            
            property_edit = ScenarioPropertyEditor(item, self.canvas.open_scenario.mgeo)
            property_edit.showDialog()
            new_Data = property_edit.return_value
            # Set new data
            attrib_key = item.text(0)
            attrib_val = item.text(2)
            element.attrib[attrib_key] = new_Data
            # Set reference data
            element_type = ScenarioItem[type(element).__name__]
            if attrib_key == 'name':
                if element_type in [ScenarioItem.ScenarioObject, ScenarioItem.EntitySelection]:
                    self.canvas.open_scenario.set_all_attributes('entityRef', attrib_val, new_Data)
                    self.canvas.open_scenario.set_all_attributes('masterEntityRef', attrib_val, new_Data)
                elif element_type == ScenarioItem.Parameter:
                    self.canvas.open_scenario.set_all_attributes('parameterRef', attrib_val, new_Data)
                elif element_type in [ScenarioItem.Story, ScenarioItem.Act, ScenarioItem.ManeuverGroup,
                                        ScenarioItem.Maneuver, ScenarioItem.Event, ScenarioItem._Action]:
                    self.canvas.open_scenario.set_all_attributes('storyboardElementRef', attrib_val, new_Data)
                elif element_type == ScenarioItem.TrafficSignalController:
                    self.canvas.open_scenario.set_all_attributes('trafficSignalControllerRef', attrib_val, new_Data)
            # Update widget
            self.canvas.updateMgeoIdWidget()
            self.widget.clear()
            self.display_openscenario_prop(selectItem['element'], self.widget)

        # MGeo Item
        elif item is not self.widget.topLevelItem(0):
            data_name = item.text(0)
            data_type = item.text(1)
            prev_data_value = item.text(2)

            # read-only
            if data_name in ['dynamic', 'predecessor_id', 'is_pre_junction', 'successor_id', 'is_suc_junction']:
                QMessageBox.warning(self.canvas, "Warning", "This field is read-only")
                return
            # [STEP #02] ProperyEditor를 통해서 새로운 값을 받는다
            if self.mscenario_item is not None:
                ego_vehicle = self.mscenario_item.ego_vehicle
                vehicle_list = self.mscenario_item.vehicle_list
                pedestrian_list = self.mscenario_item.pedestrian_list
                obstacle_list = self.mscenario_item.obstacle_list
            else:
                ego_vehicle = None
                vehicle_list = None
                pedestrian_list = None
                obstacle_list = None


            property_edit = MGeoPropertyEditor(item,
                node_map=self.mgeo_items.node_set.nodes.keys(),
                line_map=self.mgeo_items.link_set.lines.keys(),
                ts_map=self.mgeo_items.light_set.signals.keys(),
                tl_map=self.mgeo_items.sign_set.signals.keys(),
                jc_map=self.mgeo_items.junction_set.junctions.keys(),
                cw_map=self.mgeo_items.cw_set.data.keys(),
                scw_map=self.mgeo_items.scw_set.data.keys(),
                ps_map=self.mgeo_items.parking_space_set.data.keys(),
                ego_vehicle=ego_vehicle,
                vehicle_list=vehicle_list,
                pedestrian_list=pedestrian_list,
                obstacle_list=obstacle_list,
                lane_marking_map=self.mgeo_items.lane_boundary_set.lanes.keys()
            )

            property_edit.showDialog()
            new_Data = property_edit.returnNewAtrri()

            # 기존 값과 변경 값이 같다면 리턴
            if prev_data_value == new_Data:
                return
            try:
                if data_type == "boolean" :
                    if prev_data_value == "True" :
                        prev_data_value = True
                    else :
                        prev_data_value = False
                elif data_type == "int" :
                    prev_data_value = int(prev_data_value)
                elif data_type == "float" :
                    prev_data_value = float(prev_data_value)
                elif data_type.startswith("list") :
                    prev_data_value = ast.literal_eval(prev_data_value)

                # [STEP #03] 타입에 맞는 데이터 업데이트
                # 데이터 타입이 NODE 인 경우
                if selectItem['type'] == MGeoItem.NODE:
                    cmd_update_node = EditPropUpdateNode(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_node)
                    
                # 데이터 타입이 LINK 인 경우
                elif selectItem['type'] == MGeoItem.LINK:
                    if new_Data is '':
                        new_Data = None
                    if data_name in ('lane_mark_left', 'lane_mark_right'):
                        lane_marking_list = []
                        for lane_marking_id in new_Data:
                            if lane_marking_id not in self.mgeo_items.lane_boundary_set.lanes.keys():
                                QMessageBox.warning(self.canvas, "Type Error", "You must enter lane marking id")
                                return
                            new_lane_mark = self.mgeo_items.lane_boundary_set.lanes[lane_marking_id]
                            lane_marking_list.append(new_lane_mark)

                        prev_lane_marking_list = []
                        for prev_lm_idx in prev_data_value :
                            if prev_lm_idx in self.mgeo_items.lane_boundary_set.lanes.keys():
                                prev_lm = self.mgeo_items.lane_boundary_set.lanes[prev_lm_idx]
                                prev_lane_marking_list.append(prev_lm)

                        new_update_data = lane_marking_list
                        prev_update_data = prev_lane_marking_list
                    else:
                        new_update_data = new_Data
                        prev_update_data = prev_data_value

                    cmd_update_link = EditPropUpdateLink(self.canvas, selectItem['id'], data_name, prev_update_data, new_update_data)
                    self.canvas.command_manager.execute(cmd_update_link)
    
                # 데이터 타입이 TRAFFIC_SIGN 인 경우
                elif selectItem['type'] == MGeoItem.TRAFFIC_SIGN:
                    cmd_update_ts = EditPropUpdateTrafficSign(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_ts)

                # 데이터 타입이 TRAFFIC_LIGHT 인 경우
                elif selectItem['type'] == MGeoItem.TRAFFIC_LIGHT:
                    cmd_update_tl = EditPropUpdateTrafficLight(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_tl)
                    
                # 데이터 타입이 JUNCTION 인 경우
                elif selectItem['type'] == MGeoItem.JUNCTION:
                    cmd_update_jc = EditPropUpdateJunction(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_jc)
                
                # 데이터 타입이 LANE_MARKING인 경우(LANE_NODE는 수정 안함)
                elif selectItem['type'] == MGeoItem.LANE_NODE:
                    if new_Data is '':
                        new_Data = None    
                    cmd_update_lanenode = EditPropUpdateLaneNode(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_lanenode)

                elif selectItem['type'] == MGeoItem.LANE_BOUNDARY:
                    if new_Data is '':
                        new_Data = None
                    cmd_update_laneboundary = EditPropUpdateLaneBoundary(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_laneboundary)
                
                elif selectItem['type'] == MGeoItem.ROADPOLYGON:
                    if new_Data is '':
                        new_Data = None
                    cmd_update_road_poly = EditPropUpdateRoadPolygon(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_road_poly)

                # 데이터 타입이 EGO VEHICLE 인 경우
                elif selectItem['type'] == MScenarioItem.EGO_VEHICLE:
                    ego_vehicle = self.mscenario_item.ego_vehicle
                    edit_vehicle.update_vehicle(ego_vehicle, data_name, prev_data_value, new_Data)

                # 데이터 타입이 SURROUNDING VEHICLE 인 경우
                elif selectItem['type'] == MScenarioItem.SURROUNDING_VEHICLE:
                    select_id = selectItem['id']
                    vehicle = next((vehicle for vehicle in self.mscenario_item.vehicle_list if vehicle.id == int(select_id)), None)
                    if vehicle is None:
                        QMessageBox.warning(self.canvas, "Warning", 'Cannot find vehicle(id = {select_id})')
                        return

                    edit_vehicle.update_vehicle(vehicle, data_name, prev_data_value, new_Data)

                # 데이터 타입이 OBSTACLE 인 경우
                elif selectItem['type'] == MScenarioItem.OBSTACLE:
                    select_id = selectItem['id']
                    obstacle = next((obstacle for obstacle in self.mscenario_item.obstacle_list if obstacle.id == int(select_id)), None)
                    if obstacle is None:
                        QMessageBox.warning(self.canvas, "Warning", 'Cannot find obstacle(id = {select_id})')
                        return

                    edit_obstacle.update_obstacle(obstacle, data_name, prev_data_value, new_Data)

                # 데이터 타입이 PEDESTRIAN 인 경우
                elif selectItem['type'] == MScenarioItem.PEDESTRIAN:
                    select_id = selectItem['id']
                    pedestrian = next((pedestrian for pedestrian in self.mscenario_item.pedestrian_list if pedestrian.id == int(select_id)), None)
                    if pedestrian is None:
                        QMessageBox.warning(self.canvas, "Warning", 'Cannot find pedestrian(id = {select_id})')
                        return

                    edit_pedestrian.update_pedestrian(pedestrian, data_name, prev_data_value, new_Data)
                
                elif selectItem['type'] == MGeoItem.CROSSWALK:
                    cw = self.mgeo_items.cw_set.data[selectItem['id']]
                    
                elif selectItem['type'] == MGeoItem.SINGLECROSSWALK:
                    scw = self.mgeo_items.scw_set.data[selectItem['id']]

                elif selectItem['type'] == MGeoItem.PARKING_SPACE:
                    if new_Data is '':
                        new_Data = None    
                    cmd_update_parking_space = EditPropUpdateParkingSpace(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_parking_space)

                elif selectItem['type'] == MGeoItem.SURFACE_MARKING:
                    if new_Data is '':
                        new_Data = None    
                    cmd_update_surface_marking = EditPropUpdateSurfaceMarking(self.canvas, selectItem['id'], data_name, prev_data_value, new_Data)
                    self.canvas.command_manager.execute(cmd_update_surface_marking)

                self.canvas.updateMgeoIdWidget()
                
            except BaseException as e:
                QMessageBox.warning(self.canvas, "Warning", e.args[0])
                return
                
            # id 값이 수정된 경우 최근 선택된 데이터의 id 값을 수정된 값으로 업데이트
            if data_name == 'idx':
                selectItem['id'] = new_Data

            # [STEP #04] Attribute 보여주는 화면 업데이트
            item.setText(2, str(new_Data))
            if data_name == 'idx':
                self.widget.topLevelItem(0).setText(1, "{} {}".format(selectItem['type'].name, new_Data))
                    
            self.widget.update()

            Logger.log_info('[Edit item properties] type: {}, id: {}, {} \n: {} → {}'.format(selectItem['type'].name, selectItem['id'], data_name, prev_data_value, new_Data))

    @staticmethod
    def convertRefToIdx(ref_list):
        id_list = []
        for v in ref_list:
            id_list.append(v.idx)
        return id_list