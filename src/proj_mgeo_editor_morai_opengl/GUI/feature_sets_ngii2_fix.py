from ast import Raise
import os
import sys

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.mgeo_item import MGeoItem
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_junction, edit_mgeo_planner_map, edit_lane_boundary, edit_singlecrosswalk, edit_road_poly, edit_crosswalk

import math
import numpy as np
from lib.common.logger import Logger
from lib.common.polygon_util import minimum_bounding_rectangle, calculate_centroid, divide_concave_polygon

from PyQt5.QtWidgets import *
from PyQt5.Qt import *

class ChangeNgiitoMGeoWidget(QDialog):

    def __init__(self, type_def):
        super().__init__()
        self.type_def = type_def
        self.initUI()

    def initUI(self):

        widgetLayout = QVBoxLayout()
        
        self.on_stop_line_node = QCheckBox('NODE (on_stop_line)', self)
        self.on_stop_line_node.setChecked(True)
        self.related_signal_link = QCheckBox('LINK (related_signal)', self)
        self.related_signal_link.setChecked(True)
        self.link_id_list_tl = QCheckBox('TRAFFIC_LIGHT (link_id_list)', self)
        self.link_id_list_tl.setChecked(True)
        type_def_layout = QHBoxLayout()
        self.set_type_def = QCheckBox('type_def', self)
        self.set_type_def.setChecked(True)
        self.type_def_text = QLineEdit(str(self.type_def), self)
        type_def_layout.addWidget(self.set_type_def)
        type_def_layout.addWidget(self.type_def_text)

        widgetLayout.addWidget(self.on_stop_line_node)
        widgetLayout.addWidget(self.related_signal_link)
        widgetLayout.addWidget(self.link_id_list_tl)
        widgetLayout.addLayout(type_def_layout)
        

        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        widgetLayout.addWidget(self.buttonbox)
        
        self.setLayout(widgetLayout)
        self.setWindowTitle('Change NGII map to MGeo')   

        # self.show()

    def showDialog(self):
        return super().exec_()
        
    def accept(self):
        self.done(1)

    def close(self):
        self.done(0)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ChangeNgiitoMGeoWidget()
    ex.showDialog()
    sys.exit(app.exec_())



class ChangeNgiitoMGeo:

    # type_def 설정
    def find_and_repair_null_type_def(self, mgeo_planner_map, type_def):
        Logger.log_trace('Called: find_and_repair_null_type_def')
        links = mgeo_planner_map.link_set.lines
        lanes = mgeo_planner_map.lane_boundary_set.lanes
        tls = mgeo_planner_map.light_set.signals
        tss = mgeo_planner_map.sign_set.signals
        for link_id in links:
            if links[link_id].__dict__.__contains__('lane_ch_link_path'):
                if links[link_id].lane_ch_link_path is not None:
                    continue
            if links[link_id].__dict__.__contains__('lazy_point_init'):
                if bool(links[link_id].lazy_point_init):
                    continue
            if links[link_id].link_type_def == '' or links[link_id].link_type_def == None:
                links[link_id].link_type_def = type_def
        for lane_id in lanes:
            if lanes[lane_id].lane_type_def == '' or lanes[lane_id].lane_type_def == None:
                lanes[lane_id].lane_type_def = type_def
        for tl_id in tls:
            if tls[tl_id].type_def == '' or tls[tl_id].type_def == None:
                tls[tl_id].type_def = 'mgeo'
        for ts_id in tss:
            if tss[ts_id].type_def == '' or tss[ts_id].type_def == None:
                tss[ts_id].type_def = type_def
        Logger.log_info('type_def null → {}'.format(type_def))

    

    # 정지선 위에 있는 Node가 on_stop_line True로 설정되지 않은 링크 찾기
    def find_mismatch_on_stop_line(self, mgeo_planner_map, list_error):
        Logger.log_trace('Called: find_mismatch_on_stop_line')
        nodes = mgeo_planner_map.node_set.nodes
        lane_boundary = mgeo_planner_map.lane_boundary_set.lanes

        on_stop_line_nodes = []

        for node_id in nodes:
            node_item = nodes[node_id]
            for lane_id in lane_boundary:
                lane_item = lane_boundary[lane_id]
                if lane_item.lane_type != 530:
                    continue

                if node_item.is_out_of_xy_range(lane_item.bbox_x, lane_item.bbox_y):
                    continue
                else:
                    if node_item.on_stop_line == False:
                        sp_dict = {'type': MGeoItem.NODE, 'id': node_id}
                        if sp_dict not in list_error:
                            list_error.append(sp_dict)
        Logger.log_info('Find mismatch NODE')
        

    def repair_mismatch_on_stop_line(self, mgeo_planner_map, list_error):
        Logger.log_trace('Called: repair_mismatch_on_stop_line')
        nodes = mgeo_planner_map.node_set.nodes
        for item in list_error:
            node_item = nodes[item['id']]
            node_item.on_stop_line = True
        list_error.clear()
        Logger.log_info('repair on stop line NODE')

    def find_mismatch_traffic_ligth_link_id(self, mgeo_planner_map, list_error):
        Logger.log_trace('Called: find_mismatch_traffic_ligth_link_id')
        links = mgeo_planner_map.link_set.lines
        lights = mgeo_planner_map.light_set.signals
        for light_id in lights:
            if lights[light_id].type == 'pedestrian':
                continue
            link_id_list = lights[light_id].link_id_list
            if len(link_id_list) > 1:
                continue
            if links[link_id_list[0]].link_type != 1:
                sp_dict = {'type': MGeoItem.TRAFFIC_LIGHT, 'id': light_id}
                if sp_dict not in list_error:
                    list_error.append(sp_dict)
        Logger.log_info('Find mismatch TRAFFIC LIGHT')


    def repair_mismatch_traffic_ligth_link_id(self, mgeo_planner_map, list_error):
        Logger.log_trace('Called: repair_mismatch_traffic_ligth_link_id')
        nodes = mgeo_planner_map.node_set.nodes
        links = mgeo_planner_map.link_set.lines
        lights = mgeo_planner_map.light_set.signals
        for item in list_error:

            new_link_list = []
            light_item = lights[item['id']]
            
            if light_item.type == 'pedestrian':
                continue
            
            link_id_list = light_item.link_id_list
            for link_id in link_id_list:
                currnent_link_item = links[link_id]

                if len(currnent_link_item.from_node.to_links) == 2:
                    com_links = currnent_link_item.from_node.to_links

                    item1_vector = com_links[0].points[-1] - currnent_link_item.from_node.point
                    item1_heding_vector = item1_vector / np.linalg.norm(item1_vector)
                    item2_vector = com_links[1].points[-1] - currnent_link_item.from_node.point
                    item2_heding_vector = item2_vector / np.linalg.norm(item2_vector)
                
                    if abs(np.inner(item1_heding_vector, item2_heding_vector)) < 0.2:
                        if link_id == com_links[0].idx:
                            # edit_link.update_link(links, nodes, com_links[1], 'related_signal', None, 'uturn_normal')
                            new_link_list.append(com_links[1].idx)
                        else:
                            # edit_link.update_link(links, nodes, com_links[0], 'related_signal', None, 'uturn_normal')
                            new_link_list.append(com_links[0].idx)


                for new_link in currnent_link_item.to_node.to_links:
                    if new_link.link_type == '1':
                        if new_link.idx not in new_link_list:
                            new_link_list.append(new_link.idx)
            
                while currnent_link_item.lane_ch_link_left is not None:
                    currnent_link_item = currnent_link_item.lane_ch_link_left
                    for new_link in currnent_link_item.to_node.to_links:
                        if new_link.link_type == '1':
                            if new_link.idx not in new_link_list:
                                new_link_list.append(new_link.idx)

                currnent_link_item = links[link_id]
                while currnent_link_item.lane_ch_link_right is not None:
                    currnent_link_item = currnent_link_item.lane_ch_link_right
                    for new_link in currnent_link_item.to_node.to_links:
                        if new_link.link_type == '1':
                            if new_link.idx not in new_link_list:
                                new_link_list.append(new_link.idx)
                if len(new_link_list) > 1:
                    edit_signal.update_signal(lights, links, light_item, 'link_id_list', link_id_list, new_link_list)

        list_error.clear()
        Logger.log_info('repair mismatch traffic ligth link id list')

    def set_link_related_signal(self, mgeo_planner_map):
        Logger.log_trace('Called: set_link_related_signal')
        nodes = mgeo_planner_map.node_set.nodes
        links = mgeo_planner_map.link_set.lines
        lights = mgeo_planner_map.light_set.signals
        for light in lights:
            light_item = lights[light]

            if light_item.type == 'pedestrian':
                continue
            
            link_id_list = light_item.link_id_list
            for link_id in link_id_list:
                link_item = links[link_id]
                # related_signal 연결된 link의 from_node on stop line True로 설정
                # link_item.from_node.on_stop_line = True
                
                if len(link_item.to_node.to_links) > 0 and len(link_item.from_node.from_links) > 0:
                    next_link = link_item.to_node.to_links[0]
                    prev_link = link_item.from_node.from_links[0]

                    next_vector = next_link.points[-1] - next_link.points[0]
                    prev_vector = prev_link.points[-1] - prev_link.points[0]
                else:
                    next_vector = link_item.points[-1] - link_item.points[0]
                    prev_vector = link_item.points[1] - link_item.points[0]


                heading_next = next_vector / np.linalg.norm(next_vector)
                heading_prev = prev_vector / np.linalg.norm(prev_vector)

                dot_prod = np.inner(heading_prev, heading_next)
                angle_deg = np.arccos(dot_prod) * 180 / np.pi

                if angle_deg > 170:
                    edit_link.update_link(links, nodes, link_item, 'related_signal', None, 'uturn_normal')
                    continue
                change_val = 'straight'
                if abs(dot_prod) < 0.5:
                    cross = np.cross(heading_prev[0:2], heading_next[0:2])
                    if cross > 0:
                        if 'left' in light_item.sub_type:
                            change_val = 'left'
                        else:
                            change_val = 'left_unprotected'
                    elif cross < 0:
                        if 'right' in light_item.sub_type:
                            change_val = 'right'
                        else:
                            change_val = 'right_unprotected'
                edit_link.update_link(links, nodes, link_item, 'related_signal', None, change_val)
        Logger.log_info('complete set_link_related_signal')


    # single crosswalk -> crosswalk으로 묶기
    def create_crosswalk_auto(self, mgeo_planner_map):
        Logger.log_trace('Called: create_crosswalk_auto')
        scws = mgeo_planner_map.scw_set.data
        lights = mgeo_planner_map.light_set.signals
        links = mgeo_planner_map.link_set.lines

        cw_set = mgeo_planner_map.cw_set

        scw_link_id_list_key = dict()
        for scw in scws:
            scw_item = scws[scw]
            if next((item for item in cw_set.data if scw in cw_set.data[item].scw_id_list), False):
                continue
            cw_type = ['5321', '5322', '5323', '533', '534']

            if scw_item.sign_type not in cw_type:
                continue

            close_scw_list = []
            close_scw_points = []
            for com_scw in scws:
                base_point = calculate_centroid(scw_item.points)
                com_point = calculate_centroid(scws[com_scw].points)
                dist = np.sqrt(sum(((base_point[0:2]-com_point[0:2])**2)))

                if dist < 10:
                    close_scw_list.append(com_scw)
                    for i in scws[com_scw].points:
                        close_scw_points.append(i)

            temp_plane_points = minimum_bounding_rectangle(np.array(close_scw_points))
            temp_plane_x = temp_plane_points[:,0]
            temp_plane_y = temp_plane_points[:,1]
            range_x = [temp_plane_x.min()-3, temp_plane_x.max()+3]
            range_y = [temp_plane_y.min()-3, temp_plane_y.max()+3]

            close_tl_list = []
            for com_light in lights:
                light_item = lights[com_light]
                if light_item.type != 'pedestrian':
                    continue
                if light_item.is_out_of_xy_range(range_x, range_y):
                    continue
                if next((item for item in cw_set.data if com_light in cw_set.data[item].tl_id_list), False):
                    continue
                close_tl_list.append(com_light)
            
            for i in close_scw_list:
                crosswalk = Crosswalk()
                for idx in close_scw_list:
                    crosswalk.append_single_scw_list(scws[idx])
                for idx in close_tl_list:
                    crosswalk.append_ref_traffic_light(lights[idx])

                if next((item for item in cw_set.data if crosswalk.scw_id_list == cw_set.data[item].scw_id_list), None) is None:
                    cw_set.append_data(crosswalk)
        Logger.log_info('complete create crosswalk auto')

        
    def add_int_ctrl_set(self, mgeo, traffic_light_list):
        # 하나의 교차로에 묶이는 신호등 전체 선택해서 intersection_controller로 묶기
        # 이미 차량용 신호등에 링크 묶여 있는 상태로
        nodes = mgeo.node_set.nodes
        lights = mgeo.light_set.signals
        links = mgeo.link_set.lines
        synced_lights = mgeo.synced_light_set
        int_ctrls = mgeo.intersection_controller_set
        
        # 1. Synced light Set
        temp_synced_set = dict()
        temp_synced_key = 0
        other_ped_lights = []
        for tl in traffic_light_list:
            traffic_light = lights[tl['id']]
            exist = next((item for item in temp_synced_set if temp_synced_set[item]['link'] == traffic_light.link_id_list), None)
            # 보행자 신호등에 link_id_list가 다 연결되어있을 때/연결 안되어 있을 때
            if traffic_light.type == 'pedestrian':
                if exist is not None:
                    temp_synced_set[exist]['ps'].append(traffic_light)
                else:
                    other_ped_lights.append(traffic_light)
                    continue
            else:
                if exist is not None:
                    temp_synced_set[exist]['light'].append(traffic_light)
                else:
                    temp_synced_key += 1
                    temp_synced_set[temp_synced_key] = {'link':traffic_light.link_id_list, 'light': [traffic_light], 'ps': []}
        
        # 링크 오른쪽에 있고 연결된 링크랑 직진 그거랑 구십도
        # np.cross(빨간색벡터, 검은색 벡터) 양수면 오른쪽
        if len(other_ped_lights) > 0:

            for i in temp_synced_set:
                slink = None
                for link_id in temp_synced_set[i]['link']:
                    if links[link_id].related_signal == 'straight':
                        slink = link_id
                        break
                    slink = link_id
                
                base_link = links[slink]
                ref_links = base_link.get_from_links()
                if len(ref_links) > 0 :  
                    base_link = links[slink].from_node.from_links[0]
                base_vector = base_link.points[1] - base_link.points[0]
                heading_base = base_vector / np.linalg.norm(base_vector)

                link_right_ped_lights = []
                for ps_item in other_ped_lights:
                    # 방향 비교
                    vector_ps = ps_item.point - base_link.points[0]
                    heading_ps = vector_ps / np.linalg.norm(vector_ps)
                    cross_ps = np.cross(heading_base[0:2], heading_ps[0:2])
                    if cross_ps > 0:
                        continue
                    link_right_ped_lights.append(ps_item)
                
                link_right_ped_lights_dist = dict()
                for ps_item in link_right_ped_lights:
                    compare = ps_item.point - base_link.points[0]
                    link_right_ped_lights_dist[ps_item.idx] = compare[1]
                if len(link_right_ped_lights_dist) != 4:
                    print("can't....")
                    continue
                link_right_ped_lights_dist = sorted(link_right_ped_lights_dist.items(), temp_synced_key=lambda x:x[1])

                temp_synced_set[i]['ps'].append(lights[link_right_ped_lights_dist[1][0]])
                temp_synced_set[i]['ps'].append(lights[link_right_ped_lights_dist[2][0]])
         

        new_int = IntersectionController()
        int_ctrls.append_controller(new_int, create_new_key=True)
        new_ic = new_int
        new_ss_list = list()

        for i in temp_synced_set:
            sync_light = SyncedSignal()
            sync_light.intersection_controller_id = new_int.idx
            signal_set = SignalSet()
            # intersection controller
            new_int.new_synced_signal()

            for link_id in temp_synced_set[i]['link']:
                sync_light.link_id_list.append(link_id)
            for item_light in temp_synced_set[i]['light']:
                sync_light.signal_id_list.append(item_light.idx)
                signal_set.append_signal(item_light)
            for item_light in temp_synced_set[i]['ps']:
                sync_light.signal_id_list.append(item_light.idx)
                signal_set.append_signal(item_light)
            # intersection controller 
            sync_light.signal_set = signal_set
            for tl_id in sync_light.signal_set.signals:
                tl_obj = lights[tl_id]
                new_int.append_signal(tl_obj)

            synced_lights.append_synced_signal(sync_light, create_new_key=True)
            new_ss_list.append(sync_light)
        return new_ic, new_ss_list

    def create_int_ctrl_set(self, mgeo_planner_map, tl_list):
        # 하나의 교차로에 묶이는 신호등 전체 선택해서 intersection_controller로 묶기
        # 이미 차량용 신호등에 링크 묶여 있는 상태로
        nodes = mgeo_planner_map.node_set.nodes
        lights = mgeo_planner_map.light_set.signals
        links = mgeo_planner_map.link_set.lines
        synced_lights = mgeo_planner_map.synced_light_set
        int_ctrls = mgeo_planner_map.intersection_controller_set
        
        # 1. Synced light Set
        link_n_tl = dict()
        key = 0
        ps_list = []
        for tl in tl_list:
            tl_item = lights[tl['id']]
            # sorted(list5) == sorted(list6
            exist = next((item for item in link_n_tl if sorted(link_n_tl[item]['link']) == sorted(tl_item.link_id_list)), None)
            if exist is not None:
                link_n_tl[exist]['light'].append(tl_item)
            else:
                key += 1
                link_n_tl[key] = {'link':tl_item.link_id_list, 'light': [tl_item]}
        
        new_int = IntersectionController()
        int_ctrls.append_controller(new_int, create_new_key=True)

        for i in link_n_tl:
            sync_light = SyncedSignal()
            signal_set = SignalSet()
            for link_id in link_n_tl[i]['link']:
                sync_light.link_id_list.append(link_id)
            for item_light in link_n_tl[i]['light']:
                sync_light.signal_id_list.append(item_light.idx)
                signal_set.append_signal(item_light)
            sync_light.signal_set = signal_set
            sync_light.intersection_controller_id = new_int.idx
            new_int.TL.append(sync_light.signal_id_list)
            synced_lights.append_synced_signal(sync_light, create_new_key=True)
