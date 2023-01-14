import os
import sys

from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from lib.common.logger import Logger
from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map

from lib.widget.edit_item_prop import MGeoPropertyEditor


class DisplayProp:
    def set_prop(self, canvas, widget, sp, road_set=None):
        if sp is None or sp['id'] is None:
            return

        self.widget = widget
        self.widget.clear()
        
        self.canvas = canvas
        self.sp = sp
        self.mgeo_items = self.canvas.mgeo_planner_map

        if sp['type'] in MGeoItem:
            self.display_mgeo_prop(road_set)


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

        try:
            i = items[self.sp['id']]
            item = i.item_prop()
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


    def edit_item_prop(self, item, column):
        selectItem = self.sp
        if item is not self.widget.topLevelItem(0):
            data_name = item.text(0)
            data_type = item.text(1)
            prev_data_value = item.text(2)
            # read-only
            if data_name in ['dynamic', 'predecessor_id', 'is_pre_junction', 'successor_id', 'is_suc_junction']:
                QMessageBox.warning(self.canvas, "Warning", "This field is read-only")
                return
            # [STEP #02] ProperyEditor를 통해서 새로운 값을 받는다
            property_edit = MGeoPropertyEditor(item,
                self.mgeo_items.node_set.nodes.keys(),
                self.mgeo_items.link_set.lines.keys(),
                self.mgeo_items.light_set.signals.keys(),
                self.mgeo_items.sign_set.signals.keys(),
                self.mgeo_items.junction_set.junctions.keys())
            property_edit.showDialog()
            new_Data = property_edit.returnNewAtrri()

            # 기존 값과 변경 값이 같다면 리턴
            if prev_data_value == new_Data:
                return
            try:
                # [STEP #03] 타입에 맞는 데이터 업데이트
                # 데이터 타입이 NODE 인 경우
                if selectItem['type'] == MGeoItem.NODE:
                    node_set = self.mgeo_items.node_set.nodes
                    node = node_set[selectItem['id']]
                    edit_node.update_node(node_set, self.mgeo_items.link_set.lines, self.mgeo_items.junction_set.junctions, node, data_name, prev_data_value, new_Data)

                # 데이터 타입이 LINK 인 경우
                elif selectItem['type'] == MGeoItem.LINK:
                    link_set = self.mgeo_items.link_set.lines
                    link = link_set[selectItem['id']]
                    if new_Data is '':
                        new_Data = None
                    edit_link.update_link(link_set, self.mgeo_items.node_set.nodes, link, data_name, prev_data_value, new_Data)                  

                # 데이터 타입이 TRAFFIC_SIGN 인 경우
                elif selectItem['type'] == MGeoItem.TRAFFIC_SIGN:
                    ts_list = self.mgeo_items.sign_set.signals
                    ts = ts_list[selectItem['id']]
                    edit_signal.update_signal(ts_list, self.mgeo_items.link_set.lines, ts, data_name, prev_data_value, new_Data)

                # 데이터 타입이 TRAFFIC_LIGHT 인 경우
                elif selectItem['type'] == MGeoItem.TRAFFIC_LIGHT:
                    tl_list = self.mgeo_items.light_set.signals
                    tl = tl_list[selectItem['id']]
                    edit_signal.update_signal(tl_list, self.mgeo_items.link_set.lines, tl, data_name, prev_data_value, new_Data)
                    
                # 데이터 타입이 JUNCTION 인 경우
                elif selectItem['type'] == MGeoItem.JUNCTION:
                    junction = self.mgeo_items.junction_set.junctions[selectItem['id']]
                    if data_name == "idx":
                        edit_junction.edit_junction_id(self.mgeo_items.junction_set, junction, new_Data)
                    elif data_name == "jc nodes id":
                        edit_junction.edit_junction_node(junction, self.mgeo_items.node_set, new_Data)

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


    def display_node_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        pit_item = QTreeWidgetItem(widget)
        pit_item.setText(0, "point")
        pit_item.setText(1, "list<float>")
        pit_item.setText(2, str(i.point.tolist()))
                            
        tl_item = QTreeWidgetItem(widget)
        tl_item.setText(0, "to_links")
        tl_value = DisplayProp.convertRefToIdx(i.to_links)
        tl_item.setText(1, "list<string>")
        tl_item.setText(2, str(tl_value))

        fl_item = QTreeWidgetItem(widget)
        fl_item.setText(0, "from_links")
        fl_value = DisplayProp.convertRefToIdx(i.from_links)
        fl_item.setText(1, "list<string>")
        fl_item.setText(2, str(fl_value))
                
        stop_item = QTreeWidgetItem(widget)
        stop_item.setText(0, "on_stop_line")
        stop_item.setText(1, "boolean")
        stop_item.setText(2, str(i.on_stop_line))

        jct_item = QTreeWidgetItem(widget)
        jct_item.setText(0, "junctions")
        jct_value = DisplayProp.convertRefToIdx(i.junctions)
        jct_item.setText(1, "list<string>")
        jct_item.setText(2, str(jct_value))

        widget.setExpanded(True)
            
    def display_link_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        pit_item = QTreeWidgetItem(widget)
        pit_item.setText(0, "points")
        pit_item.setText(1, "list<list<float>>")
        pit_item.setText(2, str(i.points.tolist()))

        fn_item = QTreeWidgetItem(widget)
        fn_item.setText(0, "from_node")
        fn_item.setText(1, "string")
        fn_val = None
        if i.from_node is not None:
            fn_val = i.from_node.idx
        fn_item.setText(2, str(fn_val))

        tn_item = QTreeWidgetItem(widget)
        tn_item.setText(0, "to_node")
        tn_item.setText(1, "string")
        tn_val = None
        if i.to_node is not None:
            tn_val = i.to_node.idx
        tn_item.setText(2, str(tn_val))
                
        can_move_left_lane_item = QTreeWidgetItem(widget)
        can_move_left_lane_item.setText(0, "can_move_left_lane")
        can_move_left_lane_item.setText(1, "boolean")
        can_move_left_lane_item.setText(2, str(i.can_move_left_lane))

        can_move_right_lane_item = QTreeWidgetItem(widget)
        can_move_right_lane_item.setText(0, "can_move_right_lane")
        can_move_right_lane_item.setText(1, "boolean")
        can_move_right_lane_item.setText(2, str(i.can_move_right_lane))

        chl_item = QTreeWidgetItem(widget)
        chl_item.setText(0, "lane_ch_link_left")
        chl_item.setText(1, "string")
        chl_val = None
        if i.lane_ch_link_left is not None:
            chl_val = i.lane_ch_link_left.idx
        chl_item.setText(2, str(chl_val))
                
        chr_item = QTreeWidgetItem(widget)
        chr_item.setText(0, "lane_ch_link_right")
        chr_item.setText(1, "string")
        chr_val = None
        if i.lane_ch_link_right is not None:
            chr_val = i.lane_ch_link_right.idx
        chr_item.setText(2, str(chr_val))
                
        max_sp_item = QTreeWidgetItem(widget)
        max_sp_item.setText(0, "max_speed_kph")
        max_sp_item.setText(1, "int")
        max_sp_item.setText(2, str(i.max_speed_kph))
                
        min_sp_item = QTreeWidgetItem(widget)
        min_sp_item.setText(0, "min_speed_kph")
        min_sp_item.setText(1, "int")
        min_sp_item.setText(2, str(i.min_speed_kph))
                
        lt_item = QTreeWidgetItem(widget)
        lt_item.setText(0, "link_type")
        lt_item.setText(1, "string")
        lt_item.setText(2, str(i.link_type))

        rt_item = QTreeWidgetItem(widget)
        rt_item.setText(0, "road_type")
        rt_item.setText(1, "string")
        rt_item.setText(2, str(i.road_type))
                
        ri_item = QTreeWidgetItem(widget)
        ri_item.setText(0, "road_id")
        ri_item.setText(1, "string")
        ri_item.setText(2, str(i.road_id))
                
        el_item = QTreeWidgetItem(widget)
        el_item.setText(0, "ego_lane")
        el_item.setText(1, "int")
        el_item.setText(2, str(i.ego_lane))
                
        hov_item = QTreeWidgetItem(widget)
        hov_item.setText(0, "hov")
        hov_item.setText(1, "boolean")
        hov_item.setText(2, str(i.hov))

        related_signal_item = QTreeWidgetItem(widget)
        related_signal_item.setText(0, "related_signal")
        related_signal_item.setText(1, "string")
        related_signal_item.setText(2, str(i.related_signal))

        its_link_id_item = QTreeWidgetItem(widget)
        its_link_id_item.setText(0, "its_link_id")
        its_link_id_item.setText(1, "string")
        its_link_id_item.setText(2, str(i.its_link_id))

        geochange_item = QTreeWidgetItem(widget)
        geochange_item.setText(0, "geometry")
        geochange_item.setText(1, "list<dict>")
        geochange_item.setText(2, str(i.geometry))

        force_width_item = QTreeWidgetItem(widget)
        force_width_item.setText(0, "force width (start)")
        force_width_item.setText(1, "boolean")
        force_width_item.setText(2, str(i.force_width_start))

        width_start_item = QTreeWidgetItem(widget)
        width_start_item.setText(0, "width_start")
        width_start_item.setText(1, "float")
        width_start_item.setText(2, str(i.width_start))

        force_width_item = QTreeWidgetItem(widget)
        force_width_item.setText(0, "force width (end)")
        force_width_item.setText(1, "boolean")
        force_width_item.setText(2, str(i.force_width_end))

        width_end_item = QTreeWidgetItem(widget)
        width_end_item.setText(0, "width_end")
        width_end_item.setText(1, "float")
        width_end_item.setText(2, str(i.width_end))

        side_border_item = QTreeWidgetItem(widget)
        side_border_item.setText(0, "side_border")
        side_border_item.setText(1, "boolean")
        side_border_item.setText(2, str(i.enable_side_border))

        # offset_item = QTreeWidgetItem(widget)
        # offset_item.setText(0, "offset")
        # offset_item.setText(1, "float")
        # offset_item.setText(2, str(i.offset))

        widget.setExpanded(True)

    def display_TL_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        lil_item = QTreeWidgetItem(widget)
        lil_item.setText(0, "link_id_list")
        lil_item.setText(1, "list<string>")
        lil_item.setText(2, str(i.link_id_list))

        road_id_item = QTreeWidgetItem(widget)
        road_id_item.setText(0, "road_id")
        road_id_item.setText(1, "string")
        road_id_item.setText(2, str(i.road_id))

        type_item = QTreeWidgetItem(widget)
        type_item.setText(0, "type")
        type_item.setText(1, "string")
        type_item.setText(2, str(i.type))

        sub_type_item = QTreeWidgetItem(widget)
        sub_type_item.setText(0, "sub_type")
        sub_type_item.setText(1, "string")
        sub_type_item.setText(2, str(i.sub_type))

        dyn_item = QTreeWidgetItem(widget)
        dyn_item.setText(0, "dynamic")
        dyn_item.setText(1, "string")
        dyn_item.setText(2, str(i.dynamic))

        ori_item = QTreeWidgetItem(widget)
        ori_item.setText(0, "orientation")
        ori_item.setText(1, "string")
        ori_item.setText(2, str(i.orientation))

        val_item = QTreeWidgetItem(widget)
        val_item.setText(0, "value")
        val_item.setText(1, "string")
        val_item.setText(2, str(i.value))

        pit_item = QTreeWidgetItem(widget)
        pit_item.setText(0, "point")
        pit_item.setText(1, "list<float>")
        pit_item.setText(2, str(i.point.tolist()))

        cty_item = QTreeWidgetItem(widget)
        cty_item.setText(0, "country")
        cty_item.setText(1, "string")
        cty_item.setText(2, str(i.country))

        z_item = QTreeWidgetItem(widget)
        z_item.setText(0, "z_offset")
        z_item.setText(1, "float")
        z_item.setText(2, str(i.z_offset))

        w_item = QTreeWidgetItem(widget)
        w_item.setText(0, "width")
        w_item.setText(1, "float")
        w_item.setText(2, str(i.width))

        h_item = QTreeWidgetItem(widget)
        h_item.setText(0, "height")
        h_item.setText(1, "float")
        h_item.setText(2, str(i.height))

        widget.setExpanded(True)

    def display_Synced_TL_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        pit_item = QTreeWidgetItem(widget)
        pit_item.setText(0, "point")
        pit_item.setText(1, "list<float>")
        pit_item.setText(2, str(i.point.tolist()))

        icid_item = QTreeWidgetItem(widget)
        icid_item.setText(0, "intersection_controller_id")
        icid_item.setText(1, "string")
        icid_item.setText(2, str(i.intersection_controller_id))

        tl_item = QTreeWidgetItem(widget)
        tl_item.setText(0, "signal_id_list")
        tl_item.setText(1, "list<string>")
        tl_item.setText(2, str(i.signal_id_list))

        widget.setExpanded(True)

    def display_IC_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        pit_item = QTreeWidgetItem(widget)
        pit_item.setText(0, "point")
        pit_item.setText(1, "list<float>")
        pit_item.setText(2, str(i.point.tolist()))
                            
        synced_tl_item = QTreeWidgetItem(widget)
        synced_tl_item.setText(0, "synced_signal_id_list")
        synced_tl_item.setText(1, "list<string>")
        synced_tl_item.setText(2, str(i.synced_signal_id_list))

        widget.setExpanded(True)

    def display_TS_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        lil_item = QTreeWidgetItem(widget)
        lil_item.setText(0, "link_id_list")
        lil_item.setText(1, "list<string>")
        lil_item.setText(2, str(i.link_id_list))

        road_id_item = QTreeWidgetItem(widget)
        road_id_item.setText(0, "road_id")
        road_id_item.setText(1, "string")
        road_id_item.setText(2, str(i.road_id))

        type_item = QTreeWidgetItem(widget)
        type_item.setText(0, "type")
        type_item.setText(1, "string")
        type_item.setText(2, str(i.type))

        sub_type_item = QTreeWidgetItem(widget)
        sub_type_item.setText(0, "sub_type")
        sub_type_item.setText(1, "string")
        sub_type_item.setText(2, str(i.sub_type))

        dyn_item = QTreeWidgetItem(widget)
        dyn_item.setText(0, "dynamic")
        dyn_item.setText(1, "string")
        dyn_item.setText(2, str(i.dynamic))

        ori_item = QTreeWidgetItem(widget)
        ori_item.setText(0, "orientation")
        ori_item.setText(1, "string")
        ori_item.setText(2, str(i.orientation))

        val_item = QTreeWidgetItem(widget)
        val_item.setText(0, "value")
        val_item.setText(1, "string")
        val_item.setText(2, str(i.value))

        pit_item = QTreeWidgetItem(widget)
        pit_item.setText(0, "point")
        pit_item.setText(1, "list<float>")
        pit_item.setText(2, str(i.point.tolist()))

        cty_item = QTreeWidgetItem(widget)
        cty_item.setText(0, "country")
        cty_item.setText(1, "string")
        cty_item.setText(2, str(i.country))

        z_item = QTreeWidgetItem(widget)
        z_item.setText(0, "z_offset")
        z_item.setText(1, "float")
        z_item.setText(2, str(i.z_offset))

        w_item = QTreeWidgetItem(widget)
        w_item.setText(0, "width")
        w_item.setText(1, "float")
        w_item.setText(2, str(i.width))

        h_item = QTreeWidgetItem(widget)
        h_item.setText(0, "height")
        h_item.setText(1, "float")
        h_item.setText(2, str(i.height))
        
        widget.setExpanded(True)

    def display_junction_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.idx))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "idx")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.idx))

        nodes_id_item = QTreeWidgetItem(widget)
        nodes_id_item.setText(0, "jc nodes id")
        nodes_id_item.setText(1, "list<string>")
        nodes_id_item.setText(2, str(i.get_jc_node_indices()))
        
        widget.setExpanded(True)

    def display_road_prop(self, items):
        i = items[self.sp['id']]
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(i.road_id))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "road_id")
        id_item.setText(1, "string")
        id_item.setText(2, str(i.road_id))

        is_pre_junction_item = QTreeWidgetItem(widget)
        is_pre_junction_item.setText(0, "is_pre_junction")
        is_pre_junction_item.setText(1, "bool")
        is_pre_junction_item.setText(2, str(i.is_pre_junction))

        predecessor_item = QTreeWidgetItem(widget)
        predecessor_item.setText(0, "predecessor_id")
        predecessor_item.setText(1, "string")
        predecessor_item.setText(2, str(i.predecessor_id))

        is_suc_junction_item = QTreeWidgetItem(widget)
        is_suc_junction_item.setText(0, "is_suc_junction")
        is_suc_junction_item.setText(1, "bool")
        is_suc_junction_item.setText(2, str(i.is_suc_junction))

        successor_item = QTreeWidgetItem(widget)
        successor_item.setText(0, "successor_id")
        successor_item.setText(1, "string")
        successor_item.setText(2, str(i.successor_id))

        ref_lines_item = QTreeWidgetItem(widget)
        ref_lines_item.setText(0, "ref_lines")
        ref_lines_item.setText(1, "list<string>")
        ref_lines_item.setText(2, str(i.get_ref_line_id_list()))

        # all_lines_item = QTreeWidgetItem(widget)
        # all_lines_item.setText(0, "all_lines")
        # all_lines_item.setText(1, "list<string>")
        # all_lines_item.setText(2, str(i.get_all_link_id_list()))

        all_lines_item = QTreeWidgetItem(widget)
        all_lines_item.setText(0, "links")
        all_lines_item.setText(1, "list<string>")
        all_lines_item.setText(2, str(i.get_all_link_list_not_organized_id_list()))
        
        widget.setExpanded(True)

    def display_ego_vehicle_prop(self, items):
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(items.id))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "index")
        id_item.setText(1, "int")
        id_item.setText(2, str(items.index))

        posmode_item = QTreeWidgetItem(widget)
        posmode_item.setText(0, "initPositionMode")
        posmode_item.setText(1, "string")
        posmode_item.setText(2, str(items.init_position['initPositionMode']))

        pos_item = QTreeWidgetItem(widget)
        pos_item.setText(0, "pos")
        pos_item.setText(1, "dict")
        pos_item.setText(2, str(items.init_position['pos']))

        rot_item = QTreeWidgetItem(widget)
        rot_item.setText(0, "rot")
        rot_item.setText(1, "dict")
        rot_item.setText(2, str(items.init_position['rot']))

        curr_item = QTreeWidgetItem(widget)
        curr_item.setText(0, "currentVelocity")
        curr_item.setText(1, "int")
        curr_item.setText(2, str(items.current_velocity))
        
        gear_item = QTreeWidgetItem(widget)
        gear_item.setText(0, "gear")
        gear_item.setText(1, "int")
        gear_item.setText(2, str(items.gear))
        
        widget.setExpanded(True)

    def display_vehicle_prop(self, items):
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(items.id))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "index")
        id_item.setText(1, "int")
        id_item.setText(2, str(items.index))

        is_ran_item = QTreeWidgetItem(widget)
        is_ran_item.setText(0, "isRandomCreation")
        is_ran_item.setText(1, "boolean")
        is_ran_item.setText(2, str(items.is_random_creation))
        
        model_idx_item = QTreeWidgetItem(widget)
        model_idx_item.setText(0, "modelIndexList")
        model_idx_item.setText(1, "list<int>")
        model_idx_item.setText(2, str(items.model_index_list))

        posmode_item = QTreeWidgetItem(widget)
        posmode_item.setText(0, "initPositionMode")
        posmode_item.setText(1, "string")
        posmode_item.setText(2, str(items.init_position['initPositionMode']))

        pos_item = QTreeWidgetItem(widget)
        pos_item.setText(0, "pos")
        pos_item.setText(1, "dict")
        pos_item.setText(2, str(items.init_position['pos']))

        rot_item = QTreeWidgetItem(widget)
        rot_item.setText(0, "rot")
        rot_item.setText(1, "dict")
        rot_item.setText(2, str(items.init_position['rot']))

        path_gen_item = QTreeWidgetItem(widget)
        path_gen_item.setText(0, "pathGenerationMethod")
        path_gen_item.setText(1, "string")
        path_gen_item.setText(2, str(items.path_generation_method))

        path_item = QTreeWidgetItem(widget)
        path_item.setText(0, "path")
        path_item.setText(1, "list<string>")
        path_item.setText(2, str(items.path))

        resp_item = QTreeWidgetItem(widget)
        resp_item.setText(0, "respawnDistance")
        resp_item.setText(1, "int")
        resp_item.setText(2, str(items.respawn_distance))
        
        desir_item = QTreeWidgetItem(widget)
        desir_item.setText(0, "desiredVelocitiyMode")
        desir_item.setText(1, "string")
        desir_item.setText(2, str(items.desired_velocitiy_mode))
        
        desir_v_item = QTreeWidgetItem(widget)
        desir_v_item.setText(0, "desiredVelocity")
        desir_v_item.setText(1, "int")
        desir_v_item.setText(2, str(items.desired_velocity))

        curr_v_item = QTreeWidgetItem(widget)
        curr_v_item.setText(0, "currentVelocity")
        curr_v_item.setText(1, "int")
        curr_v_item.setText(2, str(items.current_velocity))
        
        widget.setExpanded(True)
        

    def display_pedestrian_prop(self, items):
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(items.id))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "index")
        id_item.setText(1, "int")
        id_item.setText(2, str(items.index))
        
        uniq_item = QTreeWidgetItem(widget)
        uniq_item.setText(0, "UNIQUEID")
        uniq_item.setText(1, "int")
        uniq_item.setText(2, str(items.unique_id))

        m_eob_item = QTreeWidgetItem(widget)
        m_eob_item.setText(0, "m_eobstacleObjType")
        m_eob_item.setText(1, "int")
        m_eob_item.setText(2, str(items.obstacle_obj_type))

        pos_item = QTreeWidgetItem(widget)
        pos_item.setText(0, "pos")
        pos_item.setText(1, "dict")
        pos_item.setText(2, str(items.init_position['pos']))

        rot_item = QTreeWidgetItem(widget)
        rot_item.setText(0, "rot")
        rot_item.setText(1, "dict")
        rot_item.setText(2, str(items.init_position['rot']))

        act_dis_item = QTreeWidgetItem(widget)
        act_dis_item.setText(0, "activeDistance")
        act_dis_item.setText(1, "float")
        act_dis_item.setText(2, str(items.active_distance))

        speed_item = QTreeWidgetItem(widget)
        speed_item.setText(0, "speed")
        speed_item.setText(1, "float")
        speed_item.setText(2, str(items.speed))

        acti_item = QTreeWidgetItem(widget)
        acti_item.setText(0, "active")
        acti_item.setText(1, "boolean")
        acti_item.setText(2, str(items.active))
        
        loop_item = QTreeWidgetItem(widget)
        loop_item.setText(0, "loop")
        loop_item.setText(1, "boolean")
        loop_item.setText(2, str(items.loop))

        mov_item = QTreeWidgetItem(widget)
        mov_item.setText(0, "movingDistance")
        mov_item.setText(1, "float")
        mov_item.setText(2, str(items.moving_distance))
        
        mov_amo_item = QTreeWidgetItem(widget)
        mov_amo_item.setText(0, "movingDistanceAmount")
        mov_amo_item.setText(1, "float")
        mov_amo_item.setText(2, str(items.moving_distance_amount))
        
        widget.setExpanded(True)

    def display_obstacle_prop(self, items):
        widget = QTreeWidgetItem(self.widget)
        widget.setText(0, self.sp['type'].name)
        widget.setText(1, str(items.id))

        id_item = QTreeWidgetItem(widget)
        id_item.setText(0, "index")
        id_item.setText(1, "int")
        id_item.setText(2, str(items.index))
        
        uniq_item = QTreeWidgetItem(widget)
        uniq_item.setText(0, "UNIQUEID")
        uniq_item.setText(1, "int")
        uniq_item.setText(2, str(items.unique_id))

        m_eob_item = QTreeWidgetItem(widget)
        m_eob_item.setText(0, "m_eobstacleObjType")
        m_eob_item.setText(1, "int")
        m_eob_item.setText(2, str(items.obstacle_obj_type))

        pos_item = QTreeWidgetItem(widget)
        pos_item.setText(0, "pos")
        pos_item.setText(1, "dict")
        pos_item.setText(2, str(items.init_transform['pos']))

        rot_item = QTreeWidgetItem(widget)
        rot_item.setText(0, "rot")
        rot_item.setText(1, "dict")
        rot_item.setText(2, str(items.init_transform['rot']))
        
        scale_item = QTreeWidgetItem(widget)
        scale_item.setText(0, "scale")
        scale_item.setText(1, "dict")
        scale_item.setText(2, str(items.init_transform['scale']))

        widget.setExpanded(True)

    @staticmethod
    def convertRefToIdx(ref_list):
        id_list = []
        for v in ref_list:
            id_list.append(v.idx)
        return id_list