# Concrete Commands Lists inherit from the command interface
import numpy as np
import copy
from abc import ABCMeta, abstractmethod
from lib.mgeo.class_defs.crosswalk import Crosswalk
from lib.mgeo.class_defs.lane_boundary import LaneBoundary 

from lib.mgeo.class_defs.mgeo_item import MGeoItem, MGeoItemFlags
from lib.mgeo.class_defs.node import Node
from lib.mgeo.class_defs.link import Link
from lib.mgeo.class_defs.parking_space import ParkingSpace
from lib.mgeo.class_defs.road_polygon import RoadPolygon
from lib.mgeo.class_defs.signal import Signal
from lib.mgeo.class_defs.junction import Junction
from lib.mgeo.class_defs.singlecrosswalk import SingleCrosswalk
from lib.mgeo.class_defs.synced_signal import SyncedSignal
from lib.mgeo.class_defs.signal_set import SignalSet
from lib.mgeo.class_defs.intersection_controller import IntersectionController

from lib.command_manager.command_interface import ICommand
from lib.common.logger import Logger
from lib.common.polygon_util import minimum_bounding_rectangle, divide_concave_polygon

from lib.opendrive.mesh_utils import vtkPoly, vtkTrianglePoly, vtkPoly_to_MeshData, generate_normals
from lib.mgeo.edit.funcs import edit_node, edit_link, edit_signal, edit_singlecrosswalk, edit_junction, edit_lane_boundary, edit_road_poly, edit_parking_space, edit_line, edit_surfacemarking
from lib.mgeo.utils.set_link_lane_mark import *
from lib.mgeo.utils.lane_change_link_creation import *
from proj_mgeo_editor_morai_opengl.GUI.feature_sets_ngii2_fix import ChangeNgiitoMGeo
from lib.mgeo.class_defs.intersection_controller_set_builder_rev import IntersectionControllerSetBuilder

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

class AddNewMgeoItem(ICommand) :
    def __init__(self, canvas, item_type, point, xlim, ylim):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.item_type = item_type
        self.point = point
        self.xlim = xlim
        self.ylim = ylim
        self.new_item = None
        self.mgeo_flags = None
        
    def execute(self):
        add_z = 0
        if self.item_type == MGeoItem.NODE:
            item_set = self.canvas.getNodeSet(self.mgeo_key)
            new_item = Node()
            self.mgeo_flags = MGeoItemFlags.NODE.value
        elif self.item_type == MGeoItem.LANE_NODE:
            item_set = self.canvas.getLaneNodeSet(self.mgeo_key)
            new_item = Node()
            self.mgeo_flags = MGeoItemFlags.LANE_NODE.value
        elif self.item_type == MGeoItem.TRAFFIC_SIGN:
            item_set = self.canvas.getTSSet(self.mgeo_key)
            add_z = 2.5
            new_item = Signal()
            new_item.dynamic = False
            self.mgeo_flags = MGeoItemFlags.TRAFFIC_SIGN.value
        elif self.item_type == MGeoItem.TRAFFIC_LIGHT:
            item_set = self.canvas.getTLSet(self.mgeo_key)
            add_z = 2.5
            new_item = Signal()
            new_item.dynamic = True
            self.mgeo_flags = MGeoItemFlags.TRAFFIC_LIGHT.value
        
        new_point = self.point
        if len(self.canvas.getLaneNodeSet(self.mgeo_key).nodes) > 0:
            min_dist = 100
            min_dist_z = 0
            for node in self.canvas.getLaneNodeSet(self.mgeo_key).nodes:
                if self.canvas.getLaneNodeSet(self.mgeo_key).nodes[node].is_out_of_xy_range(self.xlim, self.ylim):
                    continue
                cpoint = self.canvas.getLaneNodeSet(self.mgeo_key).nodes[node].point
                dist = np.sqrt(sum(((cpoint[0:2]-self.point[0:2])**2)))
                if min_dist >= dist:
                    min_dist = dist
                    min_dist_z = cpoint[2]
            new_point = [self.point[0], self.point[1], min_dist_z + add_z]

        new_item.point = np.array(new_point)
        if type(new_item) == Signal:
            new_item.country = 'KR'
            new_item.orientation = '+'
            new_item.type_def = 'mgeo'
            item_set.append_signal(new_item, create_new_key=True)
            self.canvas.mgeo_item_added(self.mgeo_key, self.item_type, new_item)
            self.new_item = new_item
        elif type(new_item) == Node:
            item_set.append_node(new_item, create_new_key=True)
            self.canvas.mgeo_item_added(self.mgeo_key, self.item_type, new_item)
            self.new_item = new_item
        self.update_widget()
        Logger.log_info('add {} point: id: {}, point: {} in Map: {}'.format(self.item_type, new_item.idx, new_item.point, self.mgeo_key))
        return True
    
    def redo(self):
        if self.new_item is None :
            return
        
        if self.item_type == MGeoItem.NODE:
            item_set = self.canvas.getNodeSet(self.mgeo_key)
            item_set.append_node(self.new_item)
            self.canvas.mgeo_item_added(self.mgeo_key, self.item_type, self.new_item)
        elif self.item_type == MGeoItem.LANE_NODE:
            item_set = self.canvas.getLaneNodeSet(self.mgeo_key)
            item_set.append_node(self.new_item)
            self.canvas.mgeo_item_added(self.mgeo_key, self.item_type, self.new_item)
        elif self.item_type == MGeoItem.TRAFFIC_SIGN:
            item_set = self.canvas.getTSSet(self.mgeo_key)
            item_set.append_signal(self.new_item)
            self.canvas.mgeo_item_added(self.mgeo_key, self.item_type, self.new_item)
        elif self.item_type == MGeoItem.TRAFFIC_LIGHT:
            item_set = self.canvas.getTLSet(self.mgeo_key)
            item_set.append_signal(self.new_item)
            self.canvas.mgeo_item_added(self.mgeo_key, self.item_type, self.new_item)

        self.update_widget()
    
    def undo(self):
        if self.new_item is None :
            return

        if self.item_type == MGeoItem.NODE:
            item_set = self.canvas.getNodeSet(self.mgeo_key)
            item_set.remove_node(self.new_item)
            self.canvas.mgeo_item_deleted(self.mgeo_key, self.item_type, self.new_item.idx)
        elif self.item_type == MGeoItem.LANE_NODE:
            item_set = self.canvas.getLaneNodeSet(self.mgeo_key)
            item_set.remove_node(self.new_item)
            self.canvas.mgeo_item_deleted(self.mgeo_key, self.item_type, self.new_item.idx)
        elif self.item_type == MGeoItem.TRAFFIC_SIGN:
            item_set = self.canvas.getTSSet(self.mgeo_key)
            item_set.remove_signal(self.new_item)
            self.canvas.mgeo_item_deleted(self.mgeo_key, self.item_type, self.new_item.idx)
        elif self.item_type == MGeoItem.TRAFFIC_LIGHT:
            item_set = self.canvas.getTLSet(self.mgeo_key)
            item_set.remove_signal(self.new_item)
            self.canvas.mgeo_item_deleted(self.mgeo_key, self.item_type, self.new_item.idx)

        self.update_widget()

    def update_widget(self) :
        self.canvas.updateMgeoIdWidget(self.mgeo_flags)

# Delete 기능
class DeleteMgeoItem(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.items = items.copy()
        
        self.mgeo_key = ""
        self.mgeo_flags = 0x00000000
        self.changed_list = list()
        self.lane_ch_link_path_dict = dict()

    def clear_change_data(self) :
        self.changed_list.clear()
        self.lane_ch_link_path_dict.clear()

    def execute(self):
        self.mgeo_key = self.canvas.mgeo_key
        if self.mgeo_key == None :
            raise BaseException('Mgeo must be selected')
        else :
            self.clear_change_data()
            for item in self.items:
                idx = item['id']
                item_type = item['type']
                
                if item_type == MGeoItem.NODE:
                    self.delete_node(idx, item_type)
                elif item_type == MGeoItem.LINK:
                    self.delete_link(idx)
                elif item_type == MGeoItem.TRAFFIC_SIGN:
                    ts_set = self.canvas.getTSSet(self.mgeo_key)
                    self.delete_signal(ts_set, ts_set.signals[idx])
                elif item_type == MGeoItem.TRAFFIC_LIGHT:
                    tl_set = self.canvas.getTLSet(self.mgeo_key)
                    self.delete_signal(tl_set, tl_set.signals[idx])
                elif item_type == MGeoItem.SYNCED_TRAFFIC_LIGHT:
                    self.delete_synced_traffic_light(idx)
                elif item_type == MGeoItem.INTERSECTION_CONTROLLER:
                    self.delete_intersection_controller(idx)
                elif item_type == MGeoItem.JUNCTION:
                    self.delete_junction(idx)
                elif item_type == MGeoItem.LANE_BOUNDARY: 
                    self.delete_lane_boundary(idx)
                elif item_type == MGeoItem.LANE_NODE: 
                    self.delete_node(idx, item_type)
                elif item_type == MGeoItem.SINGLECROSSWALK:
                    self.delete_single_crosswalk(idx)
                elif item_type == MGeoItem.ROADPOLYGON:
                    self.delete_road_poly(idx)
                elif item_type == MGeoItem.CROSSWALK:
                    self.delete_crosswalk(idx)
                elif item_type == MGeoItem.PARKING_SPACE:
                    self.delete_parking_space(idx)
                elif item_type == MGeoItem.SURFACE_MARKING:
                    self.delete_surface_marking(idx)
                elif item_type == MGeoItem.ROAD:
                    if self.canvas.odr_data is not None:
                        road_set = self.canvas.odr_data.roads
                        self.canvas.odr_data.remove_road_to_data(road_set[idx])
                else :
                    continue
                Logger.log_info('{} (id: {}) deleted.'.format(item['type'].name, idx))

            # delete attribute widget
            self.canvas.sp = {'type': None, 'id': 0}
            self.canvas.list_sp.clear()
            self.canvas.tree_attr.clear()
            self.canvas.updateMgeoIdWidget(self.mgeo_flags)
            self.canvas.reset_inner_link_point_ptr()

        return True
    
    def redo(self):
        self.execute()
    
    def undo(self):
        #UNDO 는 실행의 역순
        self.changed_list = self.changed_list[::-1]
        for change in self.changed_list :
            type = change[0]
            data_dict = change[1]
            extra_data = change[2]

            if type == MGeoItem.NODE:
                self.undo_del_node(data_dict, type)
            elif type == MGeoItem.LINK:
                self.undo_del_link(data_dict, extra_data)
            elif type == MGeoItem.TRAFFIC_SIGN or type == MGeoItem.TRAFFIC_LIGHT :
                self.undo_del_signal(data_dict, extra_data)
            elif type == MGeoItem.SYNCED_TRAFFIC_LIGHT :
                self.undo_del_synced_traffic_light(data_dict)
            elif type == MGeoItem.INTERSECTION_CONTROLLER :
                self.undo_del_intersection_controller(data_dict, extra_data)
            elif type == MGeoItem.JUNCTION :
                self.undo_del_junction(data_dict)
            elif type == MGeoItem.SINGLECROSSWALK :
                self.undo_del_single_crosswalk(data_dict)
            elif type == MGeoItem.ROADPOLYGON :
                self.undo_del_road_poly(data_dict)
            elif type == MGeoItem.CROSSWALK :
                self.undo_del_crosswalk(data_dict)
            elif type == MGeoItem.LANE_NODE :
                self.undo_del_node(data_dict, type)
            elif type == MGeoItem.LANE_BOUNDARY :
                self.undo_del_lane_boundary(data_dict, extra_data)
            elif type == MGeoItem.PARKING_SPACE :
                self.undo_del_parking_space(data_dict)
            elif type == MGeoItem.SURFACE_MARKING :
                self.undo_del_surface_marking(data_dict)
            else:
                continue

        if len(self.lane_ch_link_path_dict) > 0 :
            link_set = self.canvas.getLinkSet(self.mgeo_key)            
            for link_idx in self.lane_ch_link_path_dict :
                link = link_set.lines[link_idx]
                lane_ch_link_path = list()
                lane_ch_link_path_list = self.lane_ch_link_path_dict[link_idx]

                for lane_ch_link_path_idx in lane_ch_link_path_list:
                    if lane_ch_link_path_idx in link_set.lines:
                        lane_ch_link_path.append(link_set.lines[lane_ch_link_path_idx])

                if len(lane_ch_link_path) >= 2 :
                    link.set_values_for_lane_change_link(lane_ch_link_path)
        self.canvas.updateMgeoIdWidget(self.mgeo_flags)
        self.clear_change_data()

    def delete_node(self, idx, item_type) :
        if item_type == MGeoItem.NODE:
            node_set = self.canvas.getNodeSet(self.mgeo_key)
        elif item_type == MGeoItem.LANE_NODE:
            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        else :
            node_set = None

        if node_set is None:
            raise BaseException('None is passed for an argument node_set')
            
        node = node_set.nodes[idx]
        junction_set=self.canvas.getJunctionSet(self.mgeo_key)

        node_dict = node.to_dict()
        
        if node is None:
            raise BaseException('None is passed for an argument node')

        # 현재는 node가 dangling node일때만 삭제를 지원한다
        if not node.is_dangling_node():
            raise BaseException('Node must be a dangling node to delete') 

        for jc in node.junctions:
            # junction에서 현재 노드에 대한 reference를 삭제한다
            jc.jc_nodes.remove(node)

            # junction에 남은 노드가 없으면 이번 노드를 삭제하면 junction도 삭제되어야 한다
            if len(jc.jc_nodes) == 0:
                if junction_set is None:
                    raise BaseException('Error @ delete_node: junction_set must be provided to clear related junctions')
                junction_set.junctions.pop(jc.idx)
                self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.JUNCTION, jc.idx)
            else :
                self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.JUNCTION, jc.idx, jc)
                
        node_set.remove_node(node)
        self.canvas.mgeo_item_deleted(self.mgeo_key, item_type, idx)
        
        self.mgeo_flags |= MGeoItemFlags.JUNCTION.value

        if item_type == MGeoItem.NODE:
            self.mgeo_flags |= MGeoItemFlags.NODE.value
            self.changed_list.append((MGeoItem.NODE, node_dict, None))
        elif item_type == MGeoItem.LANE_NODE:
            self.mgeo_flags |= MGeoItemFlags.LANE_NODE.value
            self.changed_list.append((MGeoItem.LANE_NODE, node_dict, None))

    def undo_del_node(self, data_dict, item_type) :
        if item_type == MGeoItem.NODE:
            node_set = self.canvas.getNodeSet(self.mgeo_key)
        elif item_type == MGeoItem.LANE_NODE:
            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        else :
            node_set = None

        if node_set is None:
            raise BaseException('None is passed for an argument node_set')
            
        junction_set=self.canvas.getJunctionSet(self.mgeo_key)

        node = Node(data_dict['idx'])
        node.point = np.array(data_dict['point'])
        node.on_stop_line = data_dict['on_stop_line']

        node_set.append_node(node)
        self.canvas.mgeo_item_added(self.mgeo_key, item_type, node)
        junction_id_list = data_dict['junction']
        for junction_id in junction_id_list :
            if junction_id in junction_set.junctions :
                junction = junction_set.junctions[junction_id]
            else :
                junction = Junction(junction_id)
                junction_set.append_junction(junction)
                self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.JUNCTION, junction)
            junction.add_jc_node(node)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.JUNCTION, junction_id, junction)

    def delete_link_from_linkset(self, link_set, link) :
        link_dict = link.to_dict()
        
        """선택한 링크를 삭제한다"""
        if link_set is None:
            raise BaseException('None is passed for an argument link_set')
    
        if link is None:
            raise BaseException('None is passed for an argument link')

        if link.included_plane:
            raise BaseException('This link has a plane associated to it\
                please delete the plane first')

        # 연결된 노드에서 line에 대한 reference를 제거한다
        to_node = link.get_to_node()
        from_node = link.get_from_node()

        to_node.remove_from_links(link)
        from_node.remove_to_links(link)

        # Line Set에서 line에 대한 reference를 제거한다
        link_set.remove_line(link)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, link.idx)

        return link_dict

    def delete_link(self, idx) :
        link_set = self.canvas.getLinkSet(self.mgeo_key)

        #여러개를 삭제하는 경우 lane change link 는 다른 link 와 같이 삭제될 수 있음
        if idx not in link_set.lines :
            return
        link = link_set.lines[idx]
        link_dict = self.delete_link_from_linkset(link_set, link)
        self.mgeo_flags |= MGeoItemFlags.LINK.value
        
        extra_data = list()
        del_link_list = list()
        # 현재의 링크가 다른 링크의 dst link로 설정되어 있으면 이를 None으로 변경해주어야 한다
        for key, another_link in link_set.lines.items():
            # 차선 변경이 아닌 링크에 대해서만 검사하면 된다.
            if not another_link.is_it_for_lane_change():
                if another_link.get_left_lane_change_dst_link() is link:
                    another_link.lane_ch_link_left = None
                    extra_data.append((another_link.idx, "left"))
                if another_link.get_right_lane_change_dst_link() is link:
                    another_link.lane_ch_link_right = None
                    extra_data.append((another_link.idx, "right"))
            else :
                is_delete = False
                for lane_change_pair in another_link.lane_change_pair_list :
                    if lane_change_pair['from'] is link or lane_change_pair['to'] is link :
                        is_delete = True
                        break
                if is_delete :
                    del_link_list.append(another_link)
                    
        for del_link in del_link_list :
            del_link_dict = self.delete_link_from_linkset(link_set, del_link)
            self.changed_list.append((MGeoItem.LINK, del_link_dict, list()))
        self.changed_list.append((MGeoItem.LINK, link_dict, extra_data))

    def undo_del_link(self, data_dict, extra_data) :
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        link = Link(idx=data_dict['idx'])
        link.set_points(np.array(data_dict['points']))
        link.max_speed = data_dict['max_speed']
        link.lazy_point_init = data_dict['lazy_init']
        link.can_move_left_lane = data_dict['can_move_left_lane']
        link.can_move_right_lane = data_dict['can_move_right_lane']
        link.link_type = data_dict['link_type']
        link.link_type_def = data_dict['link_type_def']
        link.road_type = data_dict['road_type']
        link.road_id = data_dict['road_id']
        link.ego_lane = data_dict['ego_lane']
        link.lane_change_dir = data_dict['lane_change_dir']
        link.hov = data_dict['hov']
        link.geometry = data_dict['geometry']
        link.related_signal = data_dict['related_signal']
        link.its_link_id = data_dict['its_link_id']
        link.force_width_start = data_dict['force_width_start']
        link.width_start = data_dict['width_start']
        link.force_width_end = data_dict['force_width_end']
        link.width_end = data_dict['width_end']
        link.enable_side_border = data_dict['enable_side_border']
        link.opp_traffic = data_dict['opp_traffic']
        link.is_entrance = data_dict['is_entrance']
        link.is_exit = data_dict['is_exit']
        link.speed_unit = data_dict['speed_unit']
        link.speed_offset = data_dict['speed_offset']
        link.speed_list = data_dict['speed_list']
        link.recommended_speed = data_dict['recommended_speed']

        #from_node, to_node 넣기
        node_set = self.canvas.getNodeSet(self.mgeo_key)
        from_node_idx = data_dict['from_node_idx']
        if from_node_idx in node_set.nodes :
            from_node = node_set.nodes[from_node_idx]
            link.set_from_node(from_node)
        to_node_idx = data_dict['to_node_idx']
        if to_node_idx in node_set.nodes :
            to_node = node_set.nodes[to_node_idx]
            link.set_to_node(to_node)

        #lane_change_dst_link
        left_lane_change_dst_link_idx = data_dict['left_lane_change_dst_link_idx']
        if left_lane_change_dst_link_idx in link_set.lines :
            left_lane_change_dst_link = link_set.lines[left_lane_change_dst_link_idx]
            link.set_left_lane_change_dst_link(left_lane_change_dst_link)

        right_lane_change_dst_link_idx = data_dict['right_lane_change_dst_link_idx']
        if right_lane_change_dst_link_idx in link_set.lines :
            right_lane_change_dst_link = link_set.lines[right_lane_change_dst_link_idx]
            link.set_right_lane_change_dst_link(right_lane_change_dst_link)

        #lane_mark_left, lane_mark_right
        lane_boundary_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        lane_mark_left_idx_list = data_dict['lane_mark_left']
        for lane_mark_left_idx in lane_mark_left_idx_list :
            if lane_mark_left_idx in lane_boundary_set.lanes :
                link.set_lane_mark_left(lane_boundary_set.lanes[lane_mark_left_idx])

        lane_mark_right_idx_list = data_dict['lane_mark_right']
        for lane_mark_right_idx in lane_mark_right_idx_list :
            if lane_mark_right_idx in lane_boundary_set.lanes :
                link.set_lane_mark_right(lane_boundary_set.lanes[lane_mark_right_idx])

        #lane_ch_link_path : UNDO 시점에서 존재하지 않는 링크가 있을 수도 있으므로 나중에 업데이트한다
        self.lane_ch_link_path_dict[link.idx] = data_dict['lane_ch_link_path']

        #lane_change_link 넣기
        for extra_data_item in extra_data :
            another_link_idx = extra_data_item[0]
            another_link_side = extra_data_item[1]

            if another_link_idx in link_set.lines :
                another_link = link_set.lines[another_link_idx]
                if another_link_side == "left" :
                    another_link.set_left_lane_change_dst_link(link)
                else :
                    another_link.set_right_lane_change_dst_link(link)

        link_set.append_line(link)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, link)

    def delete_signal(self, signal_set, signal) :
        if signal_set is None:
            raise BaseException('None is passed for an argument signal_set')
        if signal is None:
            raise BaseException('None is passed for an argument signal')
        
        '''TS / TL | Synced TL / IC TL 분리'''
        if hasattr(signal, 'dynamic') == True:
            # TS 일 경우
            if signal.dynamic == False:
                signal_dict = Signal.to_dict(signal)
                extra_data = None
                signal_set.remove_signal(signal)
                self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.TRAFFIC_SIGN, signal.idx)
                self.changed_list.append((MGeoItem.TRAFFIC_SIGN, signal_dict, extra_data))
                self.mgeo_flags |= MGeoItemFlags.TRAFFIC_SIGN.value
        
            # TL 일 경우
            if signal.dynamic == True:
                '''  
                1. Synced TL List 에서 해당되는 TL 삭제
                2. Intersection Controller 에서 해당 되는 TL 삭제
                3. Crosswalk 지우는 방식
                '''
                extra_data = dict()
                extra_data['ss'] = list()
                extra_data['ic'] = list()
                extra_data['cw'] = list()
                synced_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key)
                ic_set = self.canvas.getIntersectionControllerSet(self.mgeo_key)
                
                if synced_tl_set == None and ic_set == None:
                    raise BaseException("None is passed for an argument in synced_tl and intersection controller")
                
                # Synced 제거
                for idx, ss in synced_tl_set.synced_signals.items():
                    if signal.idx in ss.signal_id_list:
                        extra_data['ss'].append(idx)
                        ss.signal_id_list.remove(signal.idx)
                        ss.signal_set.signals.pop(signal.idx)
                        self.mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
                        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, ss.idx, ss)
            
                # IC 제거 
                for idx, ic in ic_set.intersection_controllers.items():
                    id_updated = False
                    for tl in ic.TL:
                        if signal.idx in tl:
                            extra_data['ic'].append((idx, tl))
                            tl.remove(signal.idx)
                            self.mgeo_flags |= MGeoItemFlags.INTERSECTION_CONTROLLER.value
                            id_updated = True
                        
                    if signal.idx in ic.TL_dict:
                        ic.TL_dict.pop(signal.idx)
                        self.mgeo_flags |= MGeoItemFlags.INTERSECTION_CONTROLLER.value
                        id_updated = True

                    if id_updated :
                        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, ic.idx, ic)
                        
                cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
                # Crosswalk Set 에서 제거
                if cw_set == None:
                    raise BaseException("None is passed for an arugment in cw_set")
                
                for idx, cw in cw_set.data.items():
                    if signal in cw.ref_traffic_light_list:
                        cw.ref_traffic_light_list.remove(signal)
                        extra_data['cw'].append(idx)
                        self.mgeo_flags |= MGeoItemFlags.CROSSWALK.value
                        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.CROSSWALK, cw.idx, cw)

                signal_dict = Signal.to_dict(signal)
                self.changed_list.append((MGeoItem.TRAFFIC_LIGHT, signal_dict, extra_data))
                self.mgeo_flags |= MGeoItemFlags.TRAFFIC_LIGHT.value
                signal_set.remove_signal(signal)
                self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.TRAFFIC_LIGHT, signal.idx)

    def undo_del_signal(self, data_dict, extra_data) :
        '''
        1. signal 되돌리기
        2. synced signal
        3. intersection controller
        4. crosswalk set
        '''
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        signal = Signal.from_dict(data_dict, link_set)
        if signal.dynamic == False :
            self.mgeo_flags |= MGeoItemFlags.TRAFFIC_SIGN.value
            signal_set = self.canvas.getTSSet(self.mgeo_key)
            signal_set.append_signal(signal)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.TRAFFIC_SIGN, signal)
        else :
            self.mgeo_flags |= MGeoItemFlags.TRAFFIC_LIGHT.value
            self.mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
            self.mgeo_flags |= MGeoItemFlags.INTERSECTION_CONTROLLER.value
            self.mgeo_flags |= MGeoItemFlags.CROSSWALK.value
            signal_set = self.canvas.getTLSet(self.mgeo_key)
            signal_set.append_signal(signal)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.TRAFFIC_LIGHT, signal)

            synced_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key)
            for synced_tl_idx in extra_data['ss'] :
                synced_signal = synced_tl_set.synced_signals[synced_tl_idx]
                synced_signal.signal_id_list.append(signal.idx)
                synced_signal.signal_set.append_signal(signal)
                self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_tl_idx, synced_signal)

            ic_set = self.canvas.getIntersectionControllerSet(self.mgeo_key)
            for ic_data in extra_data['ic'] :
                ic_idx = ic_data[0]
                ic = ic_set.intersection_controllers[ic_idx]
                ic_tl_list = ic_data[1]
                ic_tl_list.append(signal.idx)
                ic.TL_dict[signal.idx] = signal
                self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, ic_idx, ic)

            cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
            for cw_idx in extra_data['cw'] :
                cw = cw_set.data[cw_idx]
                cw.ref_traffic_light_list.append(signal)
                self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.CROSSWALK, cw_idx, cw)

    def delete_synced_traffic_light(self, idx) :
        synced_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key)
        synced_tl = synced_tl_set.synced_signals[idx]

        synced_tl_dict = SyncedSignal.to_dict(synced_tl)

        if synced_tl_set is None:
            raise BaseException('None is passed for an argument synced_traffic_light_set')
    
        if synced_tl is None:
            raise BaseException('None is passed for an argument synced_traffic_light')
            
        synced_tl_set.remove_data(idx)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, idx)

        self.mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.changed_list.append((MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_tl_dict, None))

    def undo_del_synced_traffic_light(self, data_dict) :
        synced_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key)
        synced_tl = SyncedSignal.from_dict(data_dict)

        synced_tl_set.append_synced_signal(synced_tl)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_tl)

    def delete_intersection_controller(self, idx) :
        ic_set = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        ic = ic_set.intersection_controllers[idx]
        ic_dict = IntersectionController.to_dict(ic)
        synced_tl_set =  self.canvas.getSyncedTLSet(self.mgeo_key)
        extra_data = list()
        if ic_set is None:
            raise BaseException('None is passed for an argument intersection_controller_set')
        
        if ic is None:
            raise BaseException('None is passed for an argument intersection_controller')

        if synced_tl_set != None:
            for idx in synced_tl_set.synced_signals:
                if synced_tl_set.synced_signals[idx].intersection_controller_id == ic.idx:
                    extra_data.append(idx)
                    synced_tl_set.synced_signals[idx].intersection_controller_id = ''
                    self.mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value

        ic_set.remove_data(ic.idx)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, ic.idx)
        self.mgeo_flags |= MGeoItemFlags.INTERSECTION_CONTROLLER.value
        self.changed_list.append((MGeoItem.INTERSECTION_CONTROLLER, ic_dict, extra_data))

    def undo_del_intersection_controller(self, data_dict, extra_data) :
        ic_set = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        synced_tl_set =  self.canvas.getSyncedTLSet(self.mgeo_key)
        ic = IntersectionController.from_dict(data_dict, self.canvas.getTLSet(self.mgeo_key))

        for synced_tl_idx in extra_data :
            if synced_tl_idx in synced_tl_set.synced_signals :
                synced_tl_set.synced_signals[synced_tl_idx].intersection_controller_id = ic.idx
            
        ic_set.append_controller(ic)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, ic)
        self.mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.mgeo_flags |= MGeoItemFlags.INTERSECTION_CONTROLLER.value
        
    def delete_junction(self, idx) :
        junction_set = self.canvas.getJunctionSet(self.mgeo_key)
        junction = junction_set.junctions[idx]
        node_index_list = junction.get_jc_node_indices()
        junction_dict = {"idx":junction.idx, "nodes":node_index_list}
        self.changed_list.append((MGeoItem.JUNCTION, junction_dict, None))
        self.mgeo_flags |= MGeoItemFlags.JUNCTION.value

        # junction을 참조하고 있는 node에서, 이 junction에 대한 reference 제거
        for node in junction.jc_nodes:
            node.junctions.remove(junction)

        # junction 내 각 node에 대한 reference 제거
        junction.jc_nodes = []

        # junction_set에서 제거
        junction_set.junctions.pop(junction.idx)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.JUNCTION, junction.idx)

    def undo_del_junction(self, data_dict) :
        junction_set = self.canvas.getJunctionSet(self.mgeo_key)
        junction_idx = data_dict["idx"]
        node_index_list = data_dict["nodes"]
        node_set =  self.canvas.getNodeSet(self.mgeo_key)
        junction = Junction(junction_idx)
        junction_set.append_junction(junction)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.JUNCTION, junction)

        for node_idx in node_index_list :
            node = node_set.nodes[node_idx]
            junction.add_jc_node(node)

        self.mgeo_flags |= MGeoItemFlags.JUNCTION.value

    def delete_single_crosswalk(self, idx) :
        scw_set = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        scw = scw_set.data[idx]
        scw_dict = scw.to_dict()

        if scw_set is None:
            raise BaseException('None is passed for an argument scw_set')
        if scw is None:
            raise BaseException('None is passed for an argument scw')
        
        if scw.ref_crosswalk_id == '':
            scw_set.remove_data(scw)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SINGLECROSSWALK, scw.idx)
        else:
            raise BaseException('[ERROR] Remove this SingleCrosswalk instance from the Crosswalk instance that this belogs to first.')

        self.changed_list.append((MGeoItem.SINGLECROSSWALK, scw_dict, None))
        self.mgeo_flags |= MGeoItemFlags.SINGLECROSSWALK.value

    def undo_del_single_crosswalk(self, data_dict) :
        scw_set = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        scw = SingleCrosswalk.from_dict(data_dict)
        scw_set.append_data(scw)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SINGLECROSSWALK, scw)

        self.mgeo_flags |= MGeoItemFlags.SINGLECROSSWALK.value
        
    def delete_road_poly(self, idx) :
        road_poly_set = self.canvas.getRoadPolygonSet(self.mgeo_key)
        road_poly = road_poly_set.data[idx]
        road_poly_dict = RoadPolygon.to_dict(road_poly)

        if road_poly_set is None:
            raise BaseException('None is passed for an argument road_poly_set')
    
        if road_poly is None:
            raise BaseException('None is passed for an argument road_poly')

        road_poly_set.remove_data(road_poly)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.ROADPOLYGON, road_poly.idx)

        self.changed_list.append((MGeoItem.ROADPOLYGON, road_poly_dict, None))
        self.mgeo_flags |= MGeoItemFlags.ROADPOLYGON.value

    def undo_del_road_poly(self, data_dict) :
        road_poly_set = self.canvas.getRoadPolygonSet(self.mgeo_key)
        road_poly =RoadPolygon.from_dict(data_dict)
        road_poly_set.append_data(road_poly)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.ROADPOLYGON, road_poly)
        self.mgeo_flags |= MGeoItemFlags.ROADPOLYGON.value

    def delete_crosswalk(self, idx) :
        cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
        cw = cw_set.data[idx]
        cw_dict = Crosswalk.to_dict(cw)

        if cw_set is None:
            raise BaseException('None is passed for an argument cw_set')
        
        if cw is None:
            raise BaseException('None is passed for an argument cw')
                
        cw_set.remove_data(cw)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.CROSSWALK, cw.idx)
        self.changed_list.append((MGeoItem.CROSSWALK, cw_dict, None))        
        self.mgeo_flags |= MGeoItemFlags.CROSSWALK.value
        self.mgeo_flags |= MGeoItemFlags.SINGLECROSSWALK.value
        self.mgeo_flags |= MGeoItemFlags.TRAFFIC_LIGHT.value

    def undo_del_crosswalk(self, data_dict) :
        cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
        scw_set = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        tl_set = self.canvas.getTLSet(self.mgeo_key)
        cw = Crosswalk.from_dict(data_dict, scw_set, tl_set)
        cw.get_centroid_points()
        cw_set.append_data(cw, False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.CROSSWALK, cw)

        for idx in cw.scw_dic.keys():
            cw.scw_dic[idx].ref_crosswalk_id = cw.idx
        
        for idx in cw.tl_dic.keys():
            cw.tl_dic[idx].ref_crosswalk_id = cw.idx

        self.mgeo_flags |= MGeoItemFlags.CROSSWALK.value
        self.mgeo_flags |= MGeoItemFlags.SINGLECROSSWALK.value
        self.mgeo_flags |= MGeoItemFlags.TRAFFIC_LIGHT.value

    def delete_lane_boundary(self, idx) :
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        lane = lane_set.lanes[idx]
        lane_dict = lane.to_dict()

        if lane_set is None:
            raise BaseException('None is passed for an argument lane_set')
    
        if lane is None:
            raise BaseException('None is passed for an argument lane')

        # 연결된 노드에서 line에 대한 reference를 제거한다
        to_node = lane.get_to_node()
        from_node = lane.get_from_node()

        if to_node is not None:
            to_node.remove_from_links(lane)
        if from_node is not None:
            from_node.remove_to_links(lane)

        # Line Set에서 line에 대한 reference를 제거한다
        lane_set.remove_line(lane)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane.idx)

        extra_data = list()
        # Link 에 있는 지우려고 하는 Lane Boundary 를 제거 한다.
        for idx, link in link_set.lines.items():
            if lane in link.lane_mark_left: 
                extra_data.append((idx, "left"))
                link.lane_mark_left.remove(lane)
            
            if lane in link.lane_mark_right:
                extra_data.append((idx, "right"))
                link.lane_mark_right.remove(lane)

        self.changed_list.append((MGeoItem.LANE_BOUNDARY, lane_dict, extra_data))        
        self.mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
        self.mgeo_flags |= MGeoItemFlags.LANE_NODE.value
        self.mgeo_flags |= MGeoItemFlags.LINK.value

    def undo_del_lane_boundary(self, data_dict, extra_data) :
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lanenode_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        lane = LaneBoundary.from_dict(data_dict, lanenode_set)
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)

        lane_set.append_line(lane)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane)

        for link_item in extra_data :
            link_idx = link_item[0]
            link_side = link_item[1]
            link = link_set.lines[link_idx]

            if link_side == "left" :
                if lane not in link.lane_mark_left :
                    link.lane_mark_left.append(lane)
            else :
                if lane not in link.lane_mark_right :
                    link.lane_mark_right.append(lane)

        self.mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
        self.mgeo_flags |= MGeoItemFlags.LANE_NODE.value
        self.mgeo_flags |= MGeoItemFlags.LINK.value

    def delete_parking_space(self, idx) :
        ps_set = self.canvas.getParkingSpaceSet(self.mgeo_key)
        ps = ps_set.data[idx]
        ps_dict = ps.to_dict()

        if ps_set is None:
            raise BaseException('None is passed for an argument parking_space_set')
        if ps is None:
            raise BaseException('None is passed for an argument parking_space')

        ps_set.remove_data(ps)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.PARKING_SPACE, ps.idx)
        self.changed_list.append((MGeoItem.PARKING_SPACE, ps_dict, None))        
        self.mgeo_flags |= MGeoItemFlags.PARKING_SPACE.value

    def undo_del_parking_space(self, data_dict) :
        ps_set = self.canvas.getParkingSpaceSet(self.mgeo_key)
        ps = ParkingSpace.from_dict(data_dict)
        ps_set.append_data(ps)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.PARKING_SPACE, ps)
        self.mgeo_flags |= MGeoItemFlags.PARKING_SPACE.value

    def delete_surface_marking(self, idx):
        sm_set = self.canvas.getSurfaceMarkingSet(self.mgeo_key)
        sm = sm_set.data[idx]
        sm_dict = sm.to_dict(sm)

        if sm_set is None:
            raise BaseException('None is passed for an argument surface_marking_set')
        if sm is None:
            raise BaseException('None is passed for an argument surface_marking')

        sm_set.remove_data(sm)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SURFACE_MARKING, sm.idx)
        self.changed_list.append((MGeoItem.SURFACE_MARKING, sm_dict, None))
        self.mgeo_flags |= MGeoItemFlags.SURFACE_MARKING.value

    def undo_del_surface_marking(self, data_dict) :
        sm_set = self.canvas.getSurfaceMarkingSet(self.mgeo_key)
        sm = SurfaceMarking.from_dict(data_dict)
        sm_set.append_data(sm)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SURFACE_MARKING, sm)
        self.mgeo_flags |= MGeoItemFlags.SURFACE_MARKING.value

class DivdeLink(ICommand):
    def __init__(self, canvas, link, point_idx, keep_front):
        # Command 정보
        self.canvas = canvas
        self.mgeo_key = self.canvas.mgeo_key
        self.link = link
        self.point_idx = point_idx
        self.keep_front = keep_front

        #undo/redo 를 위한 정보
        self.new_link = None
        self.new_node = None
        self.link_points_before = self.link.points
        self.link_points_after = None
        self.geometry_before = self.link.geometry
        self.geometry_after = None
    
    def execute(self):
        link = self.link
        point_idx = self.point_idx

        # 이 위치에 새로운 Node를 생성
        new_node = Node()
        new_node.point = link.points[point_idx]
        self.canvas.getNodeSet(self.mgeo_key).append_node(new_node, create_new_key=True)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, new_node)


        """새로운 point 생성하는 부분"""
        # 2개의 points로 분리한다
        new_points_start = link.points[:point_idx+1] # point_idx를 포함해야 하므로
        new_points_end = link.points[point_idx:]


        """Geometry Point 새로 생성하는 부분"""
        # geometry point 또한 분리한다
        new_geometry_start = list()
        new_geometry_end = list()
        for i in range(len(link.geometry)):
            pts = link.geometry[i]
            if pts['id'] < point_idx:
                new_geometry_start.append(pts)
            else:
                new_pts = {'id':pts['id'] - point_idx, 'method': pts['method']}
                new_geometry_end.append(new_pts)

        # new_geometry_end에서 0위치에 아무것도 없는지 확인
        if len(new_geometry_end) == 0:
            new_geometry_end = [{'id': 0, 'method':'poly3'}]
        else:
            # 맨 처음 element의 id는 0 이어야 하는데,
            # 아무것도 없으면, 추가해주면 된다.
            if new_geometry_end[0]['id'] > 0:
                new_geometry_end = [{'id': 0, 'method':'poly3'}] + new_geometry_end


        # 어떤 링크를 살릴 것인가? 우선 시작점에서의 링크를 살린다고 하면,
        if self.keep_front:
            # 기존 링크는 to_node를 새로운 노드로 변경해야 함
            prev_to_node = link.to_node # 새 링크에서 이 to_node로 연결할 것이므로 백업
            link.remove_to_node()
            link.set_to_node(new_node)

            # 우선 가리키려는 링크 위 포인트를 0으로 돌려놓는다
            # link.set_points를 호출하면서 링크 내 point 수가 변하므로 오류 발생 가능
            self.canvas.set_point_in_line(0)

            # 포인트 변경
            link.set_points(new_points_start)  
            link.geometry = new_geometry_start
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)

            # 새로운 링크 생성
            new_link = Link()
            self.canvas.getLinkSet(self.mgeo_key).append_line(new_link, create_new_key=True)

            new_link.set_from_node(new_node)
            new_link.set_to_node(prev_to_node)
            new_link.set_points(new_points_end)
            new_link.geometry = new_geometry_end
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, new_link)

            self.link_points_after = new_points_start
            self.geometry_after = new_geometry_start

        else:
            # 기존 링크는 from_node를 새로운 노드로 변경해야 함
            prev_from_node = link.from_node # 새 링크에서 이 from_node 연결할 것이므로 백업
            link.remove_from_node()
            link.set_from_node(new_node)

            # 우선 가리키려는 링크 위 포인트를 0으로 돌려놓는다
            # link.set_points를 호출하면서 링크 내 point 수가 변하므로 오류 발생 가능
            self.canvas.set_point_in_line(0)

            # 포인트 변경
            link.set_points(new_points_end)
            link.geometry = new_geometry_end
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)
            
            # 새로운 링크 생성
            new_link = Link()
            self.canvas.getLinkSet(self.mgeo_key).append_line(new_link, create_new_key=True)

            new_link.set_from_node(prev_from_node)
            new_link.set_to_node(new_node)
            new_link.set_points(new_points_start)
            new_link.geometry = new_geometry_start
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, new_link)

            self.link_points_after = new_points_end
            self.geometry_after = new_geometry_end

        # 그 밖에 공통적으로 copy해도 되는 attribute는 복사한다         
        new_link.max_speed = link.max_speed
        new_link.min_speed = link.min_speed
        new_link.speed_unit = link.speed_unit
        new_link.link_type = link.link_type

        new_link.road_id = link.road_id # 이걸 새로운 값으로 변경해주어야 한다
        new_link.ego_lane = link.ego_lane
        new_link.lane_change_dir = link.lane_change_dir
        new_link.hov = link.hov

        self.new_node = new_node
        self.new_link = new_link
        self.update_widget()

        return True
    
    def redo(self):

        if self.keep_front:
            to_node = self.link.to_node
            self.link.remove_to_node()
            self.link.set_to_node(self.new_node)
            self.new_link.set_to_node(to_node)

        else :
            from_node = self.link.from_node
            self.link.remove_from_node()
            self.link.set_from_node(self.new_node)
            self.new_link.set_from_node(from_node)

        self.link.set_points(self.link_points_after)
        self.link.geometry = self.geometry_after
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, self.link.idx, self.link)

        #new_node 넣기
        node_set = self.canvas.getNodeSet(self.mgeo_key)
        node_set.append_node(self.new_node, create_new_key=False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, self.new_node)

        #new_link 넣기
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        link_set.append_line(self.new_link, create_new_key=False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, self.new_link)

        self.update_widget()
    
    def undo(self):
        #new_node 삭제
        node_set = self.canvas.getNodeSet(self.mgeo_key)
        node_set.remove_node(self.new_node)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.NODE, self.new_node.idx)

        #new_link 삭제
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        link_set.remove_line(self.new_link)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, self.new_link.idx)

        #from_node, to_node 되돌리기
        if self.keep_front:
            to_node = self.new_link.get_to_node()
            self.new_link.remove_to_node()
            self.link.remove_to_node()
            self.link.set_to_node(to_node)
        else :
            from_node = self.new_link.get_from_node()
            self.new_link.remove_from_node()
            self.link.remove_from_node()
            self.link.set_from_node(from_node)

        #points, geometry
        self.link.set_points(self.link_points_before)
        self.link.geometry = self.geometry_before
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, self.link.idx, self.link)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.NODE.value
        mgeo_flags |= MGeoItemFlags.LINK.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class DivdeLandBoundary(ICommand):
    def __init__(self, canvas, link, point_idx, keep_front):
        # Command 정보
        self.canvas = canvas
        self.mgeo_key = self.canvas.mgeo_key
        self.link = link
        self.point_idx = point_idx
        self.keep_front = keep_front

        #undo/redo 를 위한 정보
        self.new_link = None
        self.new_node = None
        self.link_points_before = self.link.points
        self.link_points_after = None
    
    def execute(self):
        link = self.link
        point_idx = self.point_idx

        # 이 위치에 새로운 Node를 생성
        new_node = Node()
        new_node.point = link.points[point_idx]
        self.canvas.getLaneNodeSet(self.mgeo_key).append_node(new_node, create_new_key=True)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_NODE, new_node)


        """새로운 point 생성하는 부분"""
        # 2개의 points로 분리한다
        new_points_start = link.points[:point_idx+1] # point_idx를 포함해야 하므로
        new_points_end = link.points[point_idx:]


        # 어떤 링크를 살릴 것인가? 우선 시작점에서의 링크를 살린다고 하면,
        if self.keep_front:
            # 기존 링크는 to_node를 새로운 노드로 변경해야 함
            prev_to_node = link.to_node # 새 링크에서 이 to_node로 연결할 것이므로 백업
            link.remove_to_node()
            link.set_to_node(new_node)

            # 우선 가리키려는 링크 위 포인트를 0으로 돌려놓는다
            # link.set_points를 호출하면서 링크 내 point 수가 변하므로 오류 발생 가능
            self.canvas.set_point_in_line(0)

            # 포인트 변경
            link.set_points(new_points_start)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, link.idx, link)

            # 새로운 링크 생성
            new_link = LaneBoundary()
            self.canvas.getLaneBoundarySet(self.mgeo_key).append_line(new_link, create_new_key=True)

            new_link.set_from_node(new_node)
            new_link.set_to_node(prev_to_node)
            new_link.set_points(new_points_end)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, new_link)

            self.link_points_after = new_points_start

            if len(link.lane_type) == 1:
                new_link.lane_type = link.lane_type
                new_link.lane_color = link.lane_color
                new_link.lane_shape = link.lane_shape
                new_link.lane_type_offset = link.lane_type_offset
            
            else:
                prv_dist = link.get_total_distance()
                nxt_dist = new_link.get_total_distance()
                
                link_lane_type_offset = []
                link_lane_type = []
                link_lane_shape = []
                link_lane_color = []

                nxt_lane_type_offset = [0]
                link.lane_type_offset.append(1)
                # prev : link, next : new_link
                for i, o_offset in enumerate(link.lane_type_offset):
                    o_dist = o_offset*(prv_dist + nxt_dist)
                    if o_offset == 1:
                        # nxt_lane_type_offset.append((o_dist-prv_dist)/nxt_dist)
                        new_link.lane_type.append(link.lane_type[i-1])
                        new_link.lane_shape.append(link.lane_shape[i-1])
                        new_link.lane_color.append(link.lane_color[i-1])
                        continue

                    if prv_dist - o_dist > 0:
                        link_lane_type_offset.append(o_dist/prv_dist)
                        link_lane_type.append(link.lane_type[i])
                        link_lane_shape.append(link.lane_shape[i])
                        link_lane_color.append(link.lane_color[i])
                    else:
                        nxt_lane_type_offset.append((o_dist-prv_dist)/nxt_dist)
                        new_link.lane_type.append(link.lane_type[i])
                        new_link.lane_shape.append(link.lane_shape[i])
                        new_link.lane_color.append(link.lane_color[i])

                new_link.lane_type_offset = nxt_lane_type_offset
                link.lane_type_offset = link_lane_type_offset
                link.lane_type = link_lane_type
                link.lane_shape = link_lane_shape
                link.lane_color = link_lane_color

        else:
            # 기존 링크는 from_node를 새로운 노드로 변경해야 함
            prev_from_node = link.from_node # 새 링크에서 이 from_node 연결할 것이므로 백업
            link.remove_from_node()
            link.set_from_node(new_node)

            # 우선 가리키려는 링크 위 포인트를 0으로 돌려놓는다
            # link.set_points를 호출하면서 링크 내 point 수가 변하므로 오류 발생 가능
            self.canvas.set_point_in_line(0)

            # 포인트 변경
            link.set_points(new_points_end)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, link.idx, link)

            # 새로운 링크 생성
            new_link = LaneBoundary()
            self.canvas.getLaneBoundarySet(self.mgeo_key).append_line(new_link, create_new_key=True)

            new_link.set_from_node(prev_from_node)
            new_link.set_to_node(new_node)
            new_link.set_points(new_points_start)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, new_link)

            self.link_points_after = new_points_end

            if len(link.lane_type) == 1:
                new_link.lane_type = link.lane_type
                new_link.lane_color = link.lane_color
                new_link.lane_shape = link.lane_shape
                new_link.lane_type_offset = link.lane_type_offset
            
            else:
                prv_dist = new_link.get_total_distance()
                nxt_dist = link.get_total_distance()
                
                link_lane_type_offset = [0]
                link_lane_type = []
                link_lane_shape = []
                link_lane_color = []

                prv_lane_type_offset = []

                # prev : new_link, next : link
                for i, o_offset in enumerate(link.lane_type_offset):
                    o_dist = o_offset*(prv_dist + nxt_dist)
                    if o_dist - prv_dist > 0:
                        if link_lane_type_offset[-1] == 0 and i != 0:
                            link_lane_type.append(link.lane_type[i-1])
                            link_lane_shape.append(link.lane_shape[i-1])
                            link_lane_color.append(link.lane_color[i-1])

                        link_lane_type_offset.append((o_dist-prv_dist)/nxt_dist)
                        link_lane_type.append(link.lane_type[i])
                        link_lane_shape.append(link.lane_shape[i])
                        link_lane_color.append(link.lane_color[i])
                    else:
                        prv_lane_type_offset.append(o_dist/prv_dist)
                        new_link.lane_type.append(link.lane_type[i])
                        new_link.lane_shape.append(link.lane_shape[i])
                        new_link.lane_color.append(link.lane_color[i])

                new_link.lane_type_offset = prv_lane_type_offset
                link.lane_type_offset = link_lane_type_offset
                link.lane_type = link_lane_type
                link.lane_shape = link_lane_shape
                link.lane_color = link_lane_color

        self.new_node = new_node
        self.new_link = new_link

        # 그 밖에 공통적으로 copy해도 되는 attribute는 복사한다
        new_link.copy_attribute(link, new_link)
        self.update_widget()
        return True
    
    def redo(self):

        if self.keep_front:
            to_node = self.link.to_node
            self.link.remove_to_node()
            self.link.set_to_node(self.new_node)
            self.new_link.set_to_node(to_node)

        else :
            from_node = self.link.from_node
            self.link.remove_from_node()
            self.link.set_from_node(self.new_node)
            self.new_link.set_from_node(from_node)

        self.link.set_points(self.link_points_after)
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link.idx, self.link)

        #new_node 넣기
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        node_set.append_node(self.new_node, create_new_key=False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_NODE, self.new_node)

        #new_link 넣기
        link_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        link_set.append_line(self.new_link, create_new_key=False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.new_link)

        self.update_widget()
    
    def undo(self):
        #new_node 삭제
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        node_set.remove_node(self.new_node)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_NODE, self.new_node.idx)

        #new_link 삭제
        link_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        link_set.remove_line(self.new_link)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.new_link.idx)

        #from_node, to_node 되돌리기
        if self.keep_front:
            to_node = self.new_link.get_to_node()
            self.new_link.remove_to_node()
            self.link.remove_to_node()
            self.link.set_to_node(to_node)
        else :
            from_node = self.new_link.get_from_node()
            self.new_link.remove_from_node()
            self.link.remove_from_node()
            self.link.set_from_node(from_node)

        #points
        self.link.set_points(self.link_points_before)
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link.idx, self.link)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LANE_NODE.value
        mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class AddLinkPoint(ICommand):
    def __init__(self, canvas, link, point_idx):
        self.canvas = canvas
        self.mgeo_key = self.canvas.mgeo_key
        self.link = link
        self.point_idx = point_idx
        self.point_list_before = link.points
        self.point_list_after = None
        
        if type(link).__name__ == 'Link':
            self.mgeo_flags = MGeoItemFlags.LINK.value
        else :
            self.mgeo_flags = MGeoItemFlags.LANE_BOUNDARY.value
    
    def execute(self):
        link = self.link
        point_idx = self.point_idx

        # 추가할 포인트 위치를 계산한다
        new_point = (link.points[point_idx] + link.points[point_idx + 1]) / 2.0

        # 이 포인트를 새로운 위치에 입력해야 한다
        new_point_list = np.vstack((link.points[:point_idx+1], new_point)) # 현재 포인트를 포함하도록
        new_point_list = np.vstack((new_point_list, link.points[point_idx+1:]))
        link.set_points(new_point_list)

        if type(link) is Link :
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, self.link.idx, self.link)
        elif type(link) is LaneBoundary :
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link.idx, self.link)

        self.point_list_after = new_point_list

        # geometry point의 경우, 현재 point보다 다음에 있으면 idx를 증가시켜준다
        if type(link).__name__ == 'Link':
            for i in range(len(link.geometry)):
                pts = link.geometry[i]
                if pts['id'] > point_idx: #
                    link.geometry[i]['id'] += 1 

        self.update_widget()

        return True
    
    def redo(self):
        self.execute()
    
    def undo(self):
        link = self.link
        point_idx = self.point_idx

        link.set_points(self.point_list_before)
        
        if type(link) is Link :
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, self.link.idx, self.link)
        elif type(link) is LaneBoundary :
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link.idx, self.link)

        if type(link).__name__ == 'Link':
            for i in range(len(link.geometry)):
                pts = link.geometry[i]
                if pts['id'] > point_idx + 1 :
                    link.geometry[i]['id'] -= 1 
        self.update_widget()
    
    def update_widget(self) :
        self.canvas.updateMgeoIdWidget(self.mgeo_flags)

class ReverseLinkPoint(ICommand) :
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = self.canvas.mgeo_key
        self.items = items.copy()
    
    def execute(self):
        for sp in self.items:
            if sp['type'] == MGeoItem.LINK:
                line = self.canvas.getLinkSet(self.mgeo_key).lines[sp['id']]
            elif sp['type'] == MGeoItem.LANE_BOUNDARY:
                line = self.canvas.getLaneBoundarySet(self.mgeo_key).lanes[sp['id']]
            line.points = np.flip(line.points, axis=0)
            to_node = line.to_node
            from_node = line.from_node
            line.set_to_node(from_node)
            line.set_from_node(to_node)

        self.update_widget()
        return True
    
    def redo(self):
        self.execute()
    
    def undo(self):
        self.execute()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class MergeLink(ICommand):
    def __init__(self, canvas, line_type, link0, link1):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.link0 = link0
        self.link1 = link1
        self.line_type = line_type

        self.is_pre_link = False
        self.points_before = None
        self.points_after = None
        self.geometry_before = None
        self.geometry_after = None
        self.node_mid = None
        self.lane_change_left_idx_list = list()
        self.lane_change_right_idx_list = list()
    
    def execute(self):
        link0 = self.link0
        link1 = self.link1

        if link1 in link0.get_from_links():
            # link1 -> link0 인 경우
            pre_link = link1
            suc_link = link0

        elif link1 in link0.get_to_links():
            # link0 -> link1 인 경우
            pre_link = link0
            suc_link = link1
            
        else:
            Logger.log_info('Invalid operation: merge_links works only when two connected links are selected. (two links are not connected to each other)')
            return False

        # 노드에 연결된 링크 수를 확인하여, 두 링크 이외에 다른 링크가 연결 되어 있는지 확인한다
        node_mid = pre_link.to_node
        self.node_mid = node_mid
        if len(node_mid.get_from_links()) != 1 or len(node_mid.get_to_links()) != 1:
            Logger.log_info('Invalid operation: cannot delete node between the two selected links. (another link is connected to the node)')
            return False

        if len(node_mid.junctions) != 0:
            Logger.log_info('Invalid operation: cannot delete node that belongs to a junction (node id = {})'.format(node_mid.idx))
            return False

        pre_lane_distance = pre_link.get_total_distance()
        # 이제 노드를 지우고, 두 link를 합치면 된다.
        # 이 때, link0의 property로 link를 구성하게 된다. (link1은 point만 넘겨주고, 삭제하면 된다)

        # 우선 삭제되어야 할 node의 reference를 끊는다
        #node_mid.to_links = list()
        #node_mid.from_links = list()

        # 일부 link attribute는 보관되거나 수정되어야 하고, 다음과 같이 한다.
        # NOTE: [ASSUMPTION] point는 pre_link의 마지막 point, suc_link의 마지막 point가 겹치므로,
        # suc_link의 첫번째 포인트는 사용하지 않는다
        new_points = np.vstack((pre_link.points, suc_link.points[1:]) )

        # 예를 들어 pre_link point가 10개 였으면,
        # suc_link의 geometry는 9만큼 뒤로 밀려야 함 (suc_link의 첫번째 포인트는 사용하지 않으므로)
        point_idx_offset = len(pre_link.points) - 1

        #undo, redo 를 위해 저장
        self.points_before = link0.points
        self.points_after = new_points

        if self.line_type == MGeoItem.LANE_BOUNDARY:
            link0.set_points(new_points)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, link0.idx, link0)
            # keep 하는 링크의 node reference 변경
            if link0 is pre_link:
                self.is_pre_link = True
                # link0 뒤에 link1이 붙는다
                new_lane_type = link0.lane_type
                new_lane_color = link0.lane_color
                new_lane_shape = link0.lane_shape
                link0_dist = link0.get_total_distance()
                link1_dist = link1.get_total_distance()
                new_offset_list = []
                link0_offset_list = link0.lane_type_offset
                for offset_value in link0_offset_list:
                    new_offset_list.append((offset_value*link0_dist)/(link0_dist+link1_dist))

                new_lane_type += link1.lane_type
                new_lane_color += link1.lane_color
                new_lane_shape += link1.lane_shape
                link1_offset_list = link1.lane_type_offset
                for offset_value in link1_offset_list:
                    new_offset_list.append(((offset_value*link1_dist)+link0_dist)/(link0_dist+link1_dist))

                link0.lane_type = new_lane_type
                link0.lane_color = new_lane_color
                link0.lane_shape = new_lane_shape
                link0.lane_type_offset = new_offset_list

                to_node = link1.to_node
                to_node.remove_from_links(link1)

                link0.remove_to_node()
                to_node.add_from_links(link0)
                
            else:
                self.is_pre_link = False
                # link0 앞에 link1이 붙는다
                new_lane_type = link1.lane_type
                new_lane_color = link1.lane_color
                new_lane_shape = link1.lane_shape
                link0_dist = link0.get_total_distance()
                link1_dist = link1.get_total_distance()
                new_offset_list = []
                link1_offset_list = link1.lane_type_offset
                for offset_value in link1_offset_list:
                    new_offset_list.append((offset_value*link1_dist)/(link0_dist+link1_dist))

                new_lane_type += link0.lane_type
                new_lane_color += link0.lane_color
                new_lane_shape += link0.lane_shape
                link0_offset_list = link0.lane_type_offset
                for offset_value in link0_offset_list:
                    new_offset_list.append(((offset_value*link0_dist)+link1_dist)/(link0_dist+link1_dist))

                link0.lane_type = new_lane_type
                link0.lane_color = new_lane_color
                link0.lane_shape = new_lane_shape
                link0.lane_type_offset = new_offset_list

                from_node = link1.from_node
                from_node.remove_to_links(link1)

                link0.remove_from_node()
                from_node.add_to_links(link0)

            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
            node_set.remove_node(node_mid)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_NODE, node_mid.idx)

            lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
            lane_set.remove_line(link1)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, link1.idx)
        else:
            new_geometry = pre_link.geometry
            for i in range(1, len(suc_link.geometry)):
                geo_change_point = suc_link.geometry[i]
                geo_change_point['id'] += point_idx_offset
                new_geometry.append(geo_change_point)

            self.geometry_before = link0.geometry
            self.geometry_after = new_geometry
            
            link0.set_points(new_points) # 주의: geo_change_point 수정하기 전에 여기를 호출하면 안 된다!
            link0.geometry = new_geometry
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link0.idx, link0)
            
            # keep 하는 링크의 node reference 변경
            if link0 is pre_link:
                self.is_pre_link = True
                # link0 뒤에 link1이 붙는다
                to_node = link1.to_node
                to_node.remove_from_links(link1)

                link0.remove_to_node()
                to_node.add_from_links(link0)
            else:
                self.is_pre_link = False
                # link0 앞에 link1이 붙는다
                from_node = link1.from_node
                from_node.remove_to_links(link1)

                link0.remove_from_node()
                from_node.add_to_links(link0)

            node_set = self.canvas.getNodeSet(self.mgeo_key)
            node_set.remove_node(node_mid)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.NODE, node_mid.idx)

            link_set = self.canvas.getLinkSet(self.mgeo_key)
            link_set.remove_line(link1)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, link1.idx)

            for another_idx, another_link in link_set.lines.items():
                # 차선 변경이 아닌 링크에 대해서만 검사하면 된다.
                if not another_link.is_it_for_lane_change():
                    if another_link.get_left_lane_change_dst_link() is link1:
                        another_link.lane_ch_link_left = None
                        self.lane_change_left_idx_list.append(another_idx)
                    if another_link.get_right_lane_change_dst_link() is link1:
                        another_link.lane_ch_link_right = None
                        self.lane_change_right_idx_list.append(another_idx)

        Logger.log_info('merge_links is done successfully.')
        self.sp = {'type': None, 'id': 0}
        self.canvas.list_sp.clear()
        self.canvas.tree_attr.clear()
        self.update_widget()
        return True
    
    def redo(self):
        if self.is_pre_link :
            #link0 뒤에 link1이 붙은 경우
            to_node = self.link1.to_node
            self.link0.remove_to_node()
            self.link1.remove_to_node()
            self.link0.set_to_node(to_node)
        else :
            #link1 뒤에 link0이 붙은 경우
            from_node = self.link1.from_node
            self.link0.remove_from_node()
            self.link1.remove_from_node()
            self.link0.set_from_node(from_node)

        #point
        self.link0.set_points(self.points_after)

        #lane boundary 인지 link 인지
        if self.line_type == MGeoItem.LANE_BOUNDARY:
            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
            line_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link0.idx, self.link0)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link1.idx)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_NODE, self.node_mid.idx)
        else :
            node_set = self.canvas.getNodeSet(self.mgeo_key)
            line_set = self.canvas.getLinkSet(self.mgeo_key)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, self.link0.idx, self.link0)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, self.link1.idx)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.NODE, self.node_mid.idx)

        node_set.remove_node(self.node_mid)
        line_set.remove_line(self.link1)

        if self.line_type == MGeoItem.LINK :
            #lane change link
            for idx in self.lane_change_left_idx_list :
                another_link = line_set.lines[idx]
                another_link.lane_ch_link_left = None

            for idx in self.lane_change_right_idx_list :
                another_link = line_set.lines[idx]
                another_link.lane_ch_link_right = None

            #geometry 복구
            self.link0.geometry = self.geometry_after

        self.update_widget()
    
    def undo(self):
        #lane boundary 인지 link 인지
        if self.line_type == MGeoItem.LANE_BOUNDARY:
            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
            line_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_NODE, self.node_mid)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.link1)
        else :
            node_set = self.canvas.getNodeSet(self.mgeo_key)
            line_set = self.canvas.getLinkSet(self.mgeo_key)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, self.node_mid)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, self.link1)
            
        node_set.append_node(self.node_mid)
        line_set.append_line(self.link1)

        if self.is_pre_link :
            #link0 뒤에 link1이 붙은 경우
            to_node = self.link0.to_node
            self.link0.remove_to_node()
            self.link0.set_to_node(self.node_mid)
            self.link1.set_to_node(to_node)
        else :
            #link1 뒤에 link0이 붙은 경우
            from_node = self.link0.from_node
            self.link0.remove_from_node()
            self.link0.set_from_node(self.node_mid)
            self.link1.set_from_node(from_node)

        #point 복구
        self.link0.set_points(self.points_before)
        self.canvas.mgeo_item_updated(self.mgeo_key, self.line_type, self.link0.idx, self.link0)

        if self.line_type == MGeoItem.LINK :
            #lane change link 복구
            for idx in self.lane_change_left_idx_list :
                another_link = line_set.lines[idx]
                another_link.set_left_lane_change_dst_link(self.link1)

            for idx in self.lane_change_right_idx_list :
                another_link = line_set.lines[idx]
                another_link.set_right_lane_change_dst_link(self.link1)

            #geometry 복구
            self.link0.geometry = self.geometry_before
        
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        mgeo_flags |= MGeoItemFlags.NODE.value
        mgeo_flags |= MGeoItemFlags.LANE_NODE.value
        mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class ConnectNode(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items
        self.connecting_link = None
        self.from_node = None
        self.to_node = None
        self.type = None
        self.mgeo_flags = 0x00000000
    
    def execute(self):
        # 현재 선택된 아이템이 node이고, 2개일 때만 동작한다.
        if len(self.items) != 2:
            Logger.log_info('Invalid operation: connect_nodes works only when two nodes are selected (# of selected items: {})'.format(len(self.items)))
            return False

        for selected_item in self.items:
            if selected_item['type'] != MGeoItem.NODE and selected_item['type'] != MGeoItem.LANE_NODE:
                Logger.log_info('Invalid operation: connect_nodes works only when two nodes are selected. ({} type data is included)'.format(selected_item['type']))
                return False

        if self.items[0]['type'] != self.items[1]['type'] :
            Logger.log_info('Invalid operation: connect_nodes works only when two nodes are selected.')
            return False

        #  선택된 타입에 따라 생성하는거 다르게
        if self.items[0]['type'] == MGeoItem.LANE_NODE:
            self.type = MGeoItem.LANE_NODE
            nodes = self.canvas.getLaneNodeSet(self.mgeo_key).nodes
            lines = self.canvas.getLaneBoundarySet(self.mgeo_key)
            connecting_link = LaneBoundary()
            self.mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
            self.mgeo_flags |= MGeoItemFlags.LANE_NODE.value
            try:
                connecting_link.copy_attribute(nodes[self.items[0]['id']].from_links[0], connecting_link)
            except:
                Logger.log_info("There is no from_links on the first node.")
        else:
            self.type = MGeoItem.NODE
            nodes = self.canvas.getNodeSet(self.mgeo_key).nodes
            lines = self.canvas.getLinkSet(self.mgeo_key)
            connecting_link = Link()
            self.mgeo_flags |= MGeoItemFlags.LINK.value
            self.mgeo_flags |= MGeoItemFlags.NODE.value

        # 두 노드가 이미 연결되어있는 노드인지 검색해본다
        start_node = nodes[self.items[0]['id']]
        end_node = nodes[self.items[1]['id']]

        if (end_node in start_node.get_to_nodes()) or (end_node in start_node.get_from_nodes()):
            Logger.log_info('Invalid operation: two links are already connected!')
            return False
        
        # 새로운 링크를 생성한다 (attribute는 비어있다)
        points = np.vstack((start_node.point,end_node.point))
        connecting_link.set_points(points)

        # 이 라인의 from_node, to_node 설정해주기
        connecting_link.set_from_node(start_node)
        connecting_link.set_to_node(end_node)

        lines.append_line(connecting_link, create_new_key=True)
        if self.type == MGeoItem.NODE :
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, connecting_link)
        else :
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, connecting_link)


        Logger.log_info('connecting link (id: {}) created (from node: {} -> to: {})'.format(connecting_link.idx, start_node.idx, end_node.idx))
        self.connecting_link = connecting_link
        self.from_node = start_node
        self.to_node = end_node
        self.canvas.updateMgeoIdWidget(self.mgeo_flags)
        
        return True
    
    def redo(self):
        self.connecting_link.set_from_node(self.from_node)
        self.connecting_link.set_to_node(self.to_node)
        if self.type == MGeoItem.NODE :
            lines = self.canvas.getLinkSet(self.mgeo_key)
        else : 
            lines = self.canvas.getLaneBoundarySet(self.mgeo_key)

        lines.append_line(self.connecting_link, create_new_key=False)
        if self.type == MGeoItem.NODE :
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, self.connecting_link)
        else :
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.connecting_link)

        self.canvas.updateMgeoIdWidget(self.mgeo_flags)
    
    def undo(self):
        self.connecting_link.remove_from_node()
        self.connecting_link.remove_to_node()
        if self.type == MGeoItem.NODE :
            lines = self.canvas.getLinkSet(self.mgeo_key)
        else : 
            lines = self.canvas.getLaneBoundarySet(self.mgeo_key)

        lines.remove_line(self.connecting_link)
        if self.type == MGeoItem.NODE :
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, self.connecting_link.idx)
        else :
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, self.connecting_link.idx)
        self.canvas.updateMgeoIdWidget(self.mgeo_flags)

class GenerateRoadPoly(ICommand) :
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items
        self.road_poly = None
    
    def execute(self):
        lanemarking_set = self.canvas.getLaneBoundarySet(self.mgeo_key)

        current_idx = 0
        current_lanemarking = lanemarking_set.lanes[self.items[0]['id']]
        current_points = current_lanemarking.points
        check_processed = dict()
        poly_points = list()

        loop_cnt = 0
        while True :
            if loop_cnt > len(self.items):
                break
            loop_cnt += 1
            current_point = current_points[-1]

            min_distance = None
            min_item_idx = None
            is_reverse = False

            for i in range(len(self.items)):
                if current_idx == i : 
                    continue
                if i in check_processed and check_processed[i] == True:
                    continue

                selected_item = lanemarking_set.lanes[self.items[i]['id']]

                vect1 = current_point - selected_item.points[0]
                dist1 = np.linalg.norm(vect1, ord=2)
                if min_distance == None or dist1 < min_distance :
                    min_item_idx = i
                    min_distance = dist1
                    is_reverse = False

                vect2 = current_point - selected_item.points[-1]
                dist2 = np.linalg.norm(vect2, ord=2)
                if min_distance == None or dist2 < min_distance :
                    min_item_idx = i
                    min_distance = dist2
                    is_reverse = True
            
            current_idx = min_item_idx
            check_processed[current_idx] = True
            current_lanemarking = lanemarking_set.lanes[self.items[current_idx]['id']]
            current_points = current_lanemarking.points
            if is_reverse : 
                current_points = current_points[::-1]
            if len(poly_points) == 0:
                poly_points = current_points.tolist()
            else :
                current_points = current_points.tolist()
                if poly_points[-1] == current_points[0] : 
                    current_points = current_points[1:]
                poly_points.extend(current_points)
            
            if current_idx == 0 :
                break

        face = list()
        for point_idx in range(len(poly_points)) :
            face.append(point_idx)
        faces = list()
        faces.append(face)
        poly = vtkPoly(poly_points, faces)
        poly = generate_normals(poly)
        poly = vtkTrianglePoly(poly)

        poly_points, poly_faces = vtkPoly_to_MeshData(poly)

        road_poly = RoadPolygon(poly_points, poly_faces)

        road_poly_set = self.canvas.getRoadPolygonSet(self.mgeo_key)
        road_poly_set.append_data(road_poly, True)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.ROADPOLYGON, road_poly)

        self.road_poly = road_poly
        self.update_widget()
        return True
    
    def redo(self):
        road_poly_set = self.canvas.getRoadPolygonSet(self.mgeo_key)
        road_poly_set.append_data(self.road_poly, False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.ROADPOLYGON, self.road_poly)
        self.update_widget()
    
    def undo(self):
        road_poly_set = self.canvas.getRoadPolygonSet(self.mgeo_key)
        road_poly_set.remove_data(self.road_poly)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.ROADPOLYGON, self.road_poly.idx)
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.ROADPOLYGON.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class SetStopNode(ICommand):
    def __init__(self, canvas, items, val):
        self.canvas = canvas
        self.items = items.copy()
        self.mgeo_key = canvas.mgeo_key
        self.val = val
        self.prev_data = dict()
        
    def execute(self):
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        for item in self.items:
            if item['type'] == MGeoItem.NODE :
                node_idx = item['id']
                node = node_set[node_idx]
                pre_val = node.on_stop_line
                self.prev_data[node_idx] = pre_val
                node.on_stop_line = self.val
                
                Logger.log_info('[Edit item properties] id: {}, on_stop_line : {} > {}'.format(node_idx, pre_val, self.val))

        self.update()
        
        return True
    
    def redo(self):
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        for node_idx in self.prev_data :
            node = node_set[node_idx]
            node.on_stop_line = self.val

        self.update()
    
    def undo(self):
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        for node_idx in self.prev_data :
            prev_val = self.prev_data[node_idx]
            node = node_set[node_idx]
            node.on_stop_line = prev_val

        self.update()

    def update(self) :
        if len(self.canvas.list_sp) == 1 :
            self.canvas.updateMgeoPropWidget(self.canvas.sp)

class RepairOverlappedNode(ICommand):
    def __init__(self, canvas, overlapped_node_set, node_type=MGeoItem.NODE):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.overlapped_node_set = overlapped_node_set
        self.deleted_node_set = list()
        self.node_type = node_type
        
    def execute(self):
        if self.node_type == MGeoItem.NODE :
            node_set = self.canvas.getNodeSet(self.mgeo_key)
        elif self.node_type == MGeoItem.LANE_NODE :
            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        else :
            return False

        for nodes in self.overlapped_node_set:
            # 가장 처음에 있는 값을 기준으로 맞춘다
            node_fix = nodes[0]
            deleted_nodes = list()

            for i in range(1, len(nodes)):
                from_links = nodes[i].get_from_links() 
                to_links = nodes[i].get_to_links()

                # for link in from_links:
                changed_from_links = list()
                for link in copy.copy(from_links):
                    # 이 노드로 들어가던 링크들은, to_link를 node_fix로 바꾸어야 한다
                    link.set_to_node(node_fix)
                    changed_from_links.append(link)

                # for link in to_links:
                changed_to_links = list()
                for link in copy.copy(to_links):
                    # 이 노드에서 나오던 링크들은, from_link를 node_fix로 바꾸어야 한다
                    link.set_from_node(node_fix)
                    changed_to_links.append(link)

                # nodes[i]의 to_links, from_links를 초기화한다
                nodes[i].to_links = list()
                nodes[i].from_links = list()

                node_set.remove_node(nodes[i])
                self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.NODE, nodes[i].idx)
                deleted_nodes.append([nodes[i], changed_from_links, changed_to_links])

            self.deleted_node_set.append(deleted_nodes)

        self.update_widget()
        return True
    
    def redo(self):
        self.execute()
    
    def undo(self):
        if self.node_type == MGeoItem.NODE :
            node_set = self.canvas.getNodeSet(self.mgeo_key)
        elif self.node_type == MGeoItem.LANE_NODE :
            node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        else :
            return

        for deleted_node_list in self.deleted_node_set :
            for deleted_node_info in deleted_node_list :
                deleted_node = deleted_node_info[0]
                from_link_list = deleted_node_info[1]
                to_link_list = deleted_node_info[2]

                for link in from_link_list:
                    link.set_to_node(deleted_node)

                for link in to_link_list:
                    link.set_from_node(deleted_node)

                node_set.append_node(deleted_node)
                self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, deleted_node)
        self.deleted_node_set = list()
        self.update_widget()

    def update_widget(self) :
        if self.node_type == MGeoItem.NODE :
            mgeo_flags = MGeoItemFlags.NODE.value
            mgeo_flags |= MGeoItemFlags.LINK.value
        elif self.node_type == MGeoItem.LANE_NODE :
            mgeo_flags = MGeoItemFlags.LANE_NODE.value
            mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
        else :
            return
        
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class AddCreateLaneChange(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.before_data_dict = dict()
        self.after_data_dict = dict()
        
    def execute(self):
        list_sp = self.items
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        last_i = len(list_sp)-1
        
        if len(list_sp) < 2:
            current_link = link_set[list_sp[0]['id']]
            before_data = dict()
            before_data['lane_ch_link_right'] = current_link.lane_ch_link_right
            before_data['can_move_right_lane'] = current_link.can_move_right_lane
            before_data['lane_ch_link_left'] = current_link.lane_ch_link_left
            before_data['can_move_left_lane'] = current_link.can_move_left_lane
            before_data['ego_lane'] = current_link.ego_lane

            edit_link.update_link(link_set, node_set, current_link, 'lane_ch_link_right', None, None)  
            edit_link.update_link(link_set, node_set, current_link, 'can_move_right_lane', False, False)
            edit_link.update_link(link_set, node_set, current_link, 'lane_ch_link_left', None, None)
            edit_link.update_link(link_set, node_set, current_link, 'can_move_left_lane', False, False)
            edit_link.update_link(link_set, node_set, current_link, 'ego_lane', None, 1)

            after_data = dict()
            after_data['lane_ch_link_right'] = current_link.lane_ch_link_right
            after_data['can_move_right_lane'] = current_link.can_move_right_lane
            after_data['lane_ch_link_left'] = current_link.lane_ch_link_left
            after_data['can_move_left_lane'] = current_link.can_move_left_lane
            after_data['ego_lane'] = current_link.ego_lane

            self.after_data_dict[current_link.idx] = after_data

            return True

        for i, sp in enumerate(list_sp):
            if sp['type'] == MGeoItem.LINK:
                before_data = dict()
                after_data = dict()
                current_link = link_set[list_sp[i]['id']]

                before_data['ego_lane'] = current_link.ego_lane
                before_data['lane_ch_link_right'] = current_link.lane_ch_link_right
                before_data['can_move_right_lane'] = current_link.can_move_right_lane
                before_data['lane_ch_link_left'] = current_link.lane_ch_link_left
                before_data['can_move_left_lane'] = current_link.can_move_left_lane

                edit_link.update_link(link_set, node_set, current_link, 'ego_lane', None, i+1)
                
                # edit_link.update_link(link_set, node_set, current_link, 'road_id', '', 'Road{}'.format(self.road_id_idx))
                if i == 0:
                    right_link = list_sp[i+1]['id']
                    left_link = None
                elif i == last_i:
                    right_link = None
                    left_link = list_sp[i-1]['id']
                else:
                    right_link = list_sp[i+1]['id']
                    left_link = list_sp[i-1]['id']
                
                # if right_link is not None:
                right_state = right_link is not None
                
                edit_link.update_link(link_set, node_set, current_link, 'lane_ch_link_right', None, right_link)  
                edit_link.update_link(link_set, node_set, current_link, 'can_move_right_lane', False, right_state)
                before_idx = None if before_data['lane_ch_link_right'] == None else before_data['lane_ch_link_right'].idx
                Logger.log_info('[Edit item properties] id: {}, lane_ch_link_right : {} > {}'.format(current_link.idx, before_idx, right_link))

                # if left_link is not None:
                left_state = left_link is not None
                
                edit_link.update_link(link_set, node_set, current_link, 'lane_ch_link_left', None, left_link)
                edit_link.update_link(link_set, node_set, current_link, 'can_move_left_lane', False, left_state)
                before_idx = None if before_data['lane_ch_link_left'] == None else before_data['lane_ch_link_left'].idx
                Logger.log_info('[Edit item properties] id: {}, lane_ch_link_left : {} > {}'.format(current_link.idx, before_idx, left_link))

                after_data['ego_lane'] = current_link.ego_lane
                after_data['lane_ch_link_right'] = current_link.lane_ch_link_right
                after_data['can_move_right_lane'] = current_link.can_move_right_lane
                after_data['lane_ch_link_left'] = current_link.lane_ch_link_left
                after_data['can_move_left_lane'] = current_link.can_move_left_lane

                self.before_data_dict[current_link.idx] = before_data
                self.after_data_dict[current_link.idx] = after_data

        self.update_widget()
        return True
    
    def redo(self):
        self.apply_data_dict(self.after_data_dict)
        self.update_widget()
    
    def undo(self):
        self.apply_data_dict(self.before_data_dict)
        self.update_widget()

    def apply_data_dict(self, data_dict) :
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        
        for idx in data_dict :
            current_link = link_set[idx]
            link_data = data_dict[idx]

            lane_ch_link_right_idx = None if link_data['lane_ch_link_right'] == None else link_data['lane_ch_link_right'].idx
            lane_ch_link_left_idx = None if link_data['lane_ch_link_left'] == None else link_data['lane_ch_link_left'].idx

            edit_link.update_link(link_set, node_set, current_link, 'lane_ch_link_right', None, lane_ch_link_right_idx)  
            edit_link.update_link(link_set, node_set, current_link, 'can_move_right_lane', None, link_data['can_move_right_lane'])
            edit_link.update_link(link_set, node_set, current_link, 'lane_ch_link_left', None, lane_ch_link_left_idx)
            edit_link.update_link(link_set, node_set, current_link, 'can_move_left_lane', None, link_data['can_move_left_lane'])
            edit_link.update_link(link_set, node_set, current_link, 'ego_lane', None, link_data['ego_lane'])

    def update_widget(self) :
        self.canvas.updateMgeoPropWidget(self.canvas.sp)

class AddRelatedSignal(ICommand):
    def __init__(self, canvas, items, value):
        self.canvas = canvas
        self.items = items.copy()
        self.mgeo_key = self.canvas.mgeo_key
        self.value = value
        self.pre_value_dict = dict()
        
    def execute(self):
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines

        for item in self.items:
            link_id = item['id']
            
            if item['type'] != MGeoItem.LINK:
                continue

            link = link_set[link_id]
            pre_val = link.related_signal
            self.pre_value_dict[link_id] = pre_val

            edit_link.update_link(link_set, node_set, link, 'related_signal', pre_val, self.value)  
            Logger.log_info('[Edit item properties] id: {}, related_signal : {} > {}'.format(link_id, pre_val, self.value))

        self.update_widget()
        return True
    
    def redo(self):
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines

        for link_idx in self.pre_value_dict :
            link = link_set[link_idx]
            edit_link.update_link(link_set, node_set, link, 'related_signal', self.pre_value_dict[link_idx], self.value)

        self.update_widget()
    
    def undo(self):
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines

        for link_idx in self.pre_value_dict :
            link = link_set[link_idx]
            edit_link.update_link(link_set, node_set, link, 'related_signal', self.value, self.pre_value_dict[link_idx])  

        self.update_widget()

    def update_widget(self) :
        self.canvas.updateMgeoPropWidget(self.canvas.sp)

class InputSignalLinkIdList(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_data_value = list()
        self.prev_data_dict = dict()
        
    def execute(self):
        link_list = []
        signal_list = []
        for item in self.items:
            if item['type'] == MGeoItem.LINK:
                link_list.append(item)
            elif item['type'] == MGeoItem.TRAFFIC_LIGHT or item['type'] == MGeoItem.TRAFFIC_SIGN:
                signal_list.append(item)

        self.new_data_value = []
        for link in link_list:
            self.new_data_value.append(link['id'])
        
        for signal in signal_list:
            if signal['type'] == MGeoItem.TRAFFIC_LIGHT:
                signals = self.canvas.getTLSet(self.mgeo_key).signals
            elif signal['type'] == MGeoItem.TRAFFIC_SIGN:
                signals = self.canvas.getTSSet(self.mgeo_key).signals
            else :
                continue

            item = signals[signal['id']]
            prev_data_value = item.link_id_list
            self.prev_data_dict[signal['id']] = [signal['type'], prev_data_value]
            
            # str(new_data_value) > new_data_value로 변경
            edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, item, 'link_id_list', prev_data_value, self.new_data_value)
            Logger.log_info('Add Links in Traffic Light id {}, list{}'.format(signal['id'], self.new_data_value))
            
        return True
    
    def redo(self):
        self.update_signals(False)
    
    def undo(self):
        self.update_signals(True)

    def update_signals(self, is_undo) :
        for idx in self.prev_data_dict :
            sig_type = self.prev_data_dict[idx][0]
            prev_value = self.prev_data_dict[idx][1]

            if sig_type == MGeoItem.TRAFFIC_LIGHT:
                signals = self.canvas.getTLSet(self.mgeo_key).signals
            elif sig_type == MGeoItem.TRAFFIC_SIGN:
                signals = self.canvas.getTSSet(self.mgeo_key).signals
            else :
                continue

            item = signals[idx]
            if is_undo :
                edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, item, 'link_id_list', self.new_data_value, prev_value)
            else :
                edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, item, 'link_id_list', prev_value, self.new_data_value)

class FillPointsInLinks(ICommand):
    def __init__(self, canvas, items, step_len, keep_points):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.step_len = step_len
        self.keep_points = keep_points
        self.points_dict = dict()
        
    def execute(self):
        for item in self.items:
            idx = item['id']
            link = self.canvas.getLinkSet(self.mgeo_key).lines[idx]
            prev_points = link.points
            edit_line.fill_in_points_evenly(link, self.step_len, self.keep_points)
            new_points = link.points
            self.points_dict[idx] = [prev_points, new_points]
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)
            
        self.update_canvas()

        return True
    
    def redo(self):
        self.update_link(False)
    
    def undo(self):
        self.update_link(True)

    def update_link(self, is_undo) :
        for idx in self.points_dict :
            link = self.canvas.getLinkSet(self.mgeo_key).lines[idx]
            
            if is_undo :
                prev_points = self.points_dict[idx][0]
                link.set_points(prev_points)
            else :
                new_points = self.points_dict[idx][1]
                link.set_points(new_points)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)
        self.update_canvas()

    def update_canvas(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMapData(mgeo_flags)

class SetLinkLaneBoundary(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy() 
        self.left_changes_dict = dict()
        self.right_changes_dict = dict()

    def execute(self):
        list_sp = self.items
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key).lanes

        for sp in list_sp:
            if sp['type'] != MGeoItem.LINK:
                continue
            link_id = sp['id']
            clink = link_set[link_id]
            clink_vector = (clink.points[-1]-clink.points[0])/np.linalg.norm(clink.points[-1]-clink.points[0])
            
            left_link_list = clink.get_all_left_links(check_road=False)
            # if len(left_link_list) > 0 :
            #     continue
            right_link_list = clink.get_all_right_links(check_road=False)

            reset_link_list = []
            reset_link_list.extend(left_link_list)
            reset_link_list.append(clink)
            reset_link_list.extend(right_link_list)

            area_points = []
            for i in reset_link_list:
                area_points.append(i.points[0])
                area_points.append(i.points[-1])
            area_points = np.array(minimum_bounding_rectangle(area_points))
            x_range = [np.min(area_points[:,0]), np.max(area_points[:,0])]
            y_range = [np.min(area_points[:,1]), np.max(area_points[:,1])]
            
            list_lane = []
            for i in lane_set:
                clane = lane_set[i]
                if clane.is_out_of_xy_range(x_range, y_range):
                    continue
                clane_vector = (clane.points[-1]-clane.points[0])/np.linalg.norm(clane.points[-1]-clane.points[0])
                if abs(np.inner(clink_vector, clane_vector)) < 0.8:
                    continue
                list_lane.append(clane)
                # sp_dict = {'type': MGeoItem.LANE_BOUNDARY, 'id': i}
                # self.list_highlight2.append(sp_dict)
            for rlk in reset_link_list:
                rlk_vector = (rlk.points[-1]-rlk.points[0]) / np.linalg.norm(rlk.points[-1]-rlk.points[0])
                prev_lane_mark_left = rlk.lane_mark_left
                prev_lane_mark_right = rlk.lane_mark_right
                rlk.lane_mark_left = []
                rlk.lane_mark_right = []
                # 가장 가까운 lane_boundary 넣기
                left_lane = {'dist' : 3, 'lane' : None}
                right_lane = {'dist' : 3, 'lane' : None}
                for ll in list_lane:
                    if len(ll.points) > 3:
                        point_1 = ll.points[1]
                        point_n_1 = ll.points[-2]
                        cpoint = ll.points[int(len(ll.points)/2)]
                        bool_val, z_val, pt_idx, dist = point_out_of_link(point_1, rlk)
                        if bool_val == False:
                            bool_val, z_val, pt_idx, dist = point_out_of_link(point_n_1, rlk)
                        if bool_val == False:
                            bool_val, z_val, pt_idx, dist = point_out_of_link(cpoint, rlk)
                    else:
                        cpoint = ll.points[int(len(ll.points)/2)]
                        bool_val, z_val, pt_idx, dist = point_out_of_link(cpoint, rlk)

                    if bool_val and dist < 3:
                        ll_vector = (ll.points[-1]-rlk.points[0]) / np.linalg.norm(ll.points[-1]-rlk.points[0])
                        cross = np.cross(rlk_vector[0:2], ll_vector[0:2])
                        if cross > 0:
                            if left_lane['dist'] > dist:
                                left_lane['dist'] = dist
                                left_lane['lane'] = ll
                        elif cross < 0:
                            if right_lane['dist'] > dist:
                                right_lane['dist'] = dist
                                right_lane['lane'] = ll
                if left_lane['lane'] is not None:
                    simplify_lane_for_opendrive(self.canvas, left_lane['lane'], rlk)
                    if left_lane['lane'] not in rlk.lane_mark_left:
                        rlk.set_lane_mark_left(left_lane['lane'])
                if right_lane['lane'] is not None:
                    simplify_lane_for_opendrive(self.canvas, right_lane['lane'], rlk)
                    if right_lane['lane'] not in rlk.lane_mark_right:
                        rlk.set_lane_mark_right(right_lane['lane'])
                self.left_changes_dict[rlk.idx] = [prev_lane_mark_left, rlk.lane_mark_left]
                self.right_changes_dict[rlk.idx] = [prev_lane_mark_right, rlk.lane_mark_right]
        return True
    
    def redo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        for idx in self.left_changes_dict :
            link = link_set[idx]
            new_lane_boundary = self.left_changes_dict[idx][1]
            link.lane_mark_left = new_lane_boundary

        for idx in self.right_changes_dict :
            link = link_set[idx]
            new_lane_boundary = self.left_changes_dict[idx][1]
            link.lane_mark_right = new_lane_boundary

    def undo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        for idx in self.left_changes_dict :
            link = link_set[idx]
            prev_lane_boundary = self.left_changes_dict[idx][0]
            link.lane_mark_left = prev_lane_boundary

        for idx in self.right_changes_dict :
            link = link_set[idx]
            prev_lane_boundary = self.right_changes_dict[idx][0]
            link.lane_mark_right = prev_lane_boundary

class EditTrafficLight(ICommand):
    def __init__(self, canvas, items, new_type, new_sub_type, new_orien):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_type = new_type
        self.new_sub_type = new_sub_type
        self.new_orien = new_orien
        self.changes_dict = dict()
        
    def execute(self):
        signals = self.canvas.getTLSet(self.mgeo_key).signals
        for item in self.items:
            idx = item['id']
            if item['type'] != MGeoItem.TRAFFIC_LIGHT:
                continue
            signal_item = signals[idx]

            changes_list = list()
            changes_list.append(['type', signal_item.type, self.new_type])
            Logger.log_info('[Edit item properties] id: {}, type : {} -> {}'.format(idx, signal_item.type, self.new_type))
            edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal_item, 'type', signal_item.type, self.new_type)
            
            if self.new_type == 'car':
                changes_list.append(['sub_type', signal_item.sub_type, self.new_sub_type])
                changes_list.append(['orientation', signal_item.orientation, self.new_orien])
                Logger.log_info('[Edit item properties] id: {}, sub_type : {} -> {}'.format(idx, signal_item.sub_type, self.new_sub_type))
                edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal_item, 'sub_type', signal_item.sub_type, self.new_sub_type)
                Logger.log_info('[Edit item properties] id: {}, orientation : {} -> {}'.format(idx, signal_item.orientation, self.new_orien))
                edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal_item, 'orientation', signal_item.orientation, self.new_orien)

            self.changes_dict[idx] = changes_list
        
        return True
    
    def redo(self):
        self.update_signal(False)
    
    def undo(self):
        self.update_signal(True)

    def update_signal(self, is_undo) :
        signals = self.canvas.getTLSet(self.mgeo_key).signals
        for idx in self.changes_dict :
            signal_item = signals[idx]

            for changed_item in self.changes_dict[idx] :
                field_name = changed_item[0]
                prev_val = changed_item[1]
                new_val = changed_item[2]
                if is_undo :
                    edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal_item, field_name, new_val, prev_val)
                else :
                    edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal_item, field_name, prev_val, new_val)


class EditSyncedTrafficLight(ICommand):
    from typing import Union

    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items
        self.selected_ps_lights = []
        self.selected_synced_tl = None
        self.parent_intscn_ctlr = None

    def execute(self):
        intscn_ctlr_builder = IntersectionControllerSetBuilder(self.canvas.getTLSet(self.mgeo_key))
        self.selected_ps_lights, self.selected_synced_tl, self.parent_intscn_ctlr = intscn_ctlr_builder.append_ps_light(self.canvas.list_sp, self.items, self.canvas.getIntersectionControllerSet(self.mgeo_key))
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, self.selected_synced_tl.idx, self.selected_synced_tl)
        self.update_widget()
        return True

    def redo(self):
        synced_tl_set: 'SyncedSignalSet' = self.canvas.getSyncedTLSet(self.mgeo_key)
        target_synced_tl: 'SyncedSignal' = synced_tl_set.synced_signals[self.selected_synced_tl.idx]
        intscn_ctlr_set: 'IntersectionControllerSet' = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        target_intscn_ctlr: 'IntersectionController' = intscn_ctlr_set.intersection_controllers[self.parent_intscn_ctlr.idx]

        self.selected_synced_tl.signal_id_list.extend(self.selected_ps_lights)
        self.__append_tl_obj(self.selected_ps_lights, target_synced_tl.signal_set)
        self.__append_tl_obj(self.selected_ps_lights, intscn_ctlr_set)

        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, target_synced_tl.idx, target_synced_tl)
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, target_intscn_ctlr.idx, target_intscn_ctlr)

        self.update_widget()

    def undo(self):
        mgeo_signal_set: 'SignalSet' = self.canvas.getTLSet(self.mgeo_key)
        for item in self.selected_ps_lights:
            self.selected_synced_tl.signal_id_list.remove(item)
        for ps_light in self.selected_ps_lights:
            self.selected_synced_tl.signal_set.remove_signal(mgeo_signal_set.signals[ps_light])
            if ps_light in self.parent_intscn_ctlr.TL[-1]:
                del self.parent_intscn_ctlr.TL[-1]
                del self.parent_intscn_ctlr.TL_dict[ps_light]
                self.parent_intscn_ctlr.point = self.parent_intscn_ctlr.TL_dict[self.parent_intscn_ctlr.TL[-1][0]].point

        synced_tl_set: 'SyncedSignalSet' = self.canvas.getSyncedTLSet(self.mgeo_key)
        target_synced_tl: 'SyncedSignal' = synced_tl_set.synced_signals[self.selected_synced_tl.idx]
        intscn_ctlr_set: 'IntersectionControllerSet' = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        target_intscn_ctlr: 'IntersectionController' = intscn_ctlr_set.intersection_controllers[self.parent_intscn_ctlr.idx]

        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, target_synced_tl.idx, target_synced_tl)
        self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, target_intscn_ctlr.idx, target_intscn_ctlr)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.INTERSECTION_CONTROLLER.value
        mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

    def __append_tl_obj(self, tl_id_list, parent: Union['SignalSet', 'IntersectionControllerSet']):
        signal_set: 'SignalSet' = self.canvas.getTLSet(self.mgeo_key)
        if isinstance(parent, SignalSet):
            [parent.append_signal(signal_set.signals[tl_id]) for tl_id in tl_id_list]
        elif isinstance(parent, IntersectionControllerSet):
            target_intscn_ctlr: 'IntersectionController' = parent.intersection_controllers[self.parent_intscn_ctlr.idx]
            target_intscn_ctlr.new_synced_signal()
            [target_intscn_ctlr.append_signal(signal_set.signals[tl_id]) for tl_id in tl_id_list]


class CreateCrossWalk(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_crosswalk = None
        self.changed_scw_dict = dict()
        self.changed_signal_dict = dict()
        
    def execute(self):
        """
        scw, tl => cw 생성하고 scw, tl 연결, scw, tl 업데이트
        """
        cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
        singleCrosswalk_list = []
        tl_list = []
        cw_id = ''

        for item in self.items:
            if item['type'] == MGeoItem.SINGLECROSSWALK:
                singleCrosswalk_list.append(item)
            elif item['type'] == MGeoItem.TRAFFIC_LIGHT:
                tl_list.append(item)
                
        if len(tl_list) > 0:
            if tl_list[0]['type'] == MGeoItem.TRAFFIC_LIGHT:
                signals = self.canvas.getTLSet(self.mgeo_key).signals
                

        if len(singleCrosswalk_list) > 0:
            if singleCrosswalk_list[0]['type'] == MGeoItem.SINGLECROSSWALK:
                scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key).data

        # 새로 생성
        crosswalk = Crosswalk()
        tls = []
        cws = []
        for tl in tl_list:
            signal = signals[tl['id']]
            if signal.IsPedestrianSign() == False:
                # TODO : alert popup & log 보행자 신호등만 선택 가능합니다 표시
                raise BaseException('Only Choose Pedestrian Traffic Light.')

            crosswalk.append_ref_traffic_light(signal)
            tls.append(signal)
            
        for scw in singleCrosswalk_list:
            singleCrosswalk = scws[scw['id']]
            crosswalk.append_single_scw_list(singleCrosswalk)
            cws.append(singleCrosswalk)
        
        # 중복체크
        if cw_set.isDuplicationCheck(crosswalk):
            raise BaseException('The same Crosswalk MGeoItem is already exists')

        cw_set.append_data(crosswalk)
        cw_id = crosswalk.idx
        self.new_crosswalk = crosswalk
        
        for tl in tls:
            prev_data_value = tl.ref_crosswalk_id
            self.changed_signal_dict[tl.idx] = [prev_data_value, cw_id]
            edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, tl, 'ref_crosswalk_id', prev_data_value, cw_id)
        for cw in cws:
            self.changed_scw_dict[cw.idx] = [cw.ref_crosswalk_id, cw_id]
            edit_singlecrosswalk.update_singlecrosswalk(scws,cw, 'ref_crosswalk_id', cw_id )
        
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.CROSSWALK, crosswalk)
        self.update_widget()
        return True
    
    def redo(self):
        cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
        cw_set.append_data(self.new_crosswalk, create_new_key=False)

        signals = self.canvas.getTLSet(self.mgeo_key).signals
        for signal_idx in self.changed_signal_dict :
            signal = signals[signal_idx]
            prev_data = self.changed_signal_dict[signal_idx][0]
            new_data = self.changed_signal_dict[signal_idx][1]

            self.new_crosswalk.append_ref_traffic_light(signal)
            edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal, 'ref_crosswalk_id', prev_data, new_data)
            
        scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key).data
        for scw_idx in self.changed_scw_dict :
            scw = scws[scw_idx]
            new_data = self.changed_scw_dict[scw_idx][1]

            self.new_crosswalk.append_single_scw_list(scw)
            edit_singlecrosswalk.update_singlecrosswalk(scws, scw, 'ref_crosswalk_id', new_data)

        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.CROSSWALK, self.new_crosswalk)
        self.update_widget()
    
    def undo(self):
        cw_set = self.canvas.getCrosswalkSet(self.mgeo_key)
        cw_set.remove_data(self.new_crosswalk)

        signals = self.canvas.getTLSet(self.mgeo_key).signals
        for signal_idx in self.changed_signal_dict :
            signal = signals[signal_idx]
            prev_data = self.changed_signal_dict[signal_idx][0]
            new_data = self.changed_signal_dict[signal_idx][1]

            edit_signal.update_signal(signals, self.canvas.getLinkSet(self.mgeo_key).lines, signal, 'ref_crosswalk_id', new_data, prev_data)
            
        scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key).data
        for scw_idx in self.changed_scw_dict :
            scw = scws[scw_idx]
            prev_data = self.changed_scw_dict[scw_idx][0]

            edit_singlecrosswalk.update_singlecrosswalk(scws, scw, 'ref_crosswalk_id', prev_data)

        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.CROSSWALK, self.new_crosswalk.idx)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.CROSSWALK.value
        mgeo_flags |= MGeoItemFlags.SINGLECROSSWALK.value
        mgeo_flags |= MGeoItemFlags.TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class CreateSycLightSet(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_synced_signal = None
        
    def execute(self):
        tl_set = self.canvas.getTLSet(self.mgeo_key).signals

        if next((item for item in self.items if item['type'] != MGeoItem.TRAFFIC_LIGHT), None) is not None:
            Logger.log_error('Only Choose Traffic Light.')
            return False

        tl_set = self.canvas.getTLSet(self.mgeo_key).signals
        syn_light_id_list = []
        syn_light_set = SignalSet()
        
        for item in self.items:
            if item['type'] != MGeoItem.TRAFFIC_LIGHT:
                continue
            tl_id = item['id']
            signal = tl_set[tl_id]
            syn_light_id_list.append(tl_id)
            syn_light_set.append_signal(signal)

        syn_light = SyncedSignal()
        syn_light.signal_id_list = syn_light_id_list
        syn_light.signal_set = syn_light_set
        syn_light.link_id_list = tl_set[self.items[0]['id']].link_id_list
        self.new_synced_signal = syn_light

        self.canvas.getSyncedTLSet(self.mgeo_key).append_synced_signal(syn_light, create_new_key = True)

        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, syn_light)

        Logger.log_info('Called: create_sync_light_set')

        self.update_widget()
        return True
    
    def redo(self):
        self.canvas.getSyncedTLSet(self.mgeo_key).append_synced_signal(self.new_synced_signal, create_new_key = False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, self.new_synced_signal)
        self.update_widget()
    
    def undo(self):
        self.canvas.getSyncedTLSet(self.mgeo_key).remove_synced_signal(self.new_synced_signal)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, self.new_synced_signal.idx)
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        mgeo_flags |= MGeoItemFlags.TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)


class CreateSyncedTLIntTL(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_ic = ""
        self.new_ss_list = list()


    def execute(self):
        funcs_ngii_to_mgeo = ChangeNgiitoMGeo()
        self.new_ic, self.new_ss_list = funcs_ngii_to_mgeo.add_int_ctrl_set(self.canvas.mgeo_maps_dict[self.mgeo_key], self.items)

        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic)
        for synced_light in self.new_ss_list :
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_light)

        self.update_widget()
        return True

    def redo(self):
        int_ctrls = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        int_ctrls.append_controller(self.new_ic, create_new_key=False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic)

        synced_lights = self.canvas.getSyncedTLSet(self.mgeo_key)
        for synced_light in self.new_ss_list :
            synced_lights.append_synced_signal(synced_light, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_light)

        self.update_widget()

    def undo(self):
        int_ctrls = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        int_ctrls.remove_ic_signal(self.new_ic)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic.idx)

        synced_lights = self.canvas.getSyncedTLSet(self.mgeo_key)
        for synced_light in self.new_ss_list :
            synced_lights.remove_synced_signal(synced_light)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_light.idx)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.INTERSECTION_CONTROLLER.value
        mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)


class CreateSyncIntscnTLSet(ICommand):

    def __init__(self, canvas, items):
        from typing import List
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_ic = ""
        self.new_ss_list: List['SyncedSignal'] = list()

    def execute(self):
        intscn_ctrl_builder = IntersectionControllerSetBuilder(self.canvas.getTLSet(self.mgeo_key))
        intscn_ctrl_builder.set_highlight_traffic_lights(self.items)
        intscn_ctrl_builder.find_synced_traffic_light()
        self.new_ic, self.new_ss_list = intscn_ctrl_builder.make_synced_traffic_light_set(self.canvas.mgeo_maps_dict[self.mgeo_key])

        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic)
        for synced_light in self.new_ss_list :
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_light)

        self.update_widget()
        return True

    def redo(self):
        int_ctrls: 'IntersectionControllerSet' = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        int_ctrls.append_controller(self.new_ic, create_new_key=False)
        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic)

        synced_lights: 'SyncedSignalSet' = self.canvas.getSyncedTLSet(self.mgeo_key)
        for synced_light in self.new_ss_list :
            synced_lights.append_synced_signal(synced_light, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_light)

        self.update_widget()

    def undo(self):
        int_ctrls: 'IntersectionControllerSet' = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        int_ctrls.remove_ic_signal(self.new_ic)
        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic.idx)

        synced_lights: 'SyncedSignalSet' = self.canvas.getSyncedTLSet(self.mgeo_key)
        for synced_light in self.new_ss_list :
            synced_lights.remove_synced_signal(synced_light)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, synced_light.idx)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.INTERSECTION_CONTROLLER.value
        mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)


class CreateIntersection(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_ic = None
        self.changed_sync_signal_dict = dict()
        
    def execute(self):
        syn_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key).synced_signals

        new_int = IntersectionController()
        self.canvas.getIntersectionControllerSet(self.mgeo_key).append_controller(new_int, create_new_key=True)
        self.new_ic = new_int

        for item in self.items:
            if item['type'] != MGeoItem.SYNCED_TRAFFIC_LIGHT:
                continue
            syn_tl_id = item['id']
            sync_light = syn_tl_set[syn_tl_id]
            self.changed_sync_signal_dict[syn_tl_id] = [sync_light.intersection_controller_id, new_int.idx]
            sync_light.intersection_controller_id = new_int.idx
            # new_int.TL.append(sync_light.signal_id_list)
            new_int.new_synced_signal()
            for tl_id in sync_light.signal_id_list:
                tl_obj = self.canvas.getTLSet(self.mgeo_key).signals[tl_id]
                new_int.append_signal(tl_obj)
        Logger.log_info('Called: action_create_intersection')

        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, new_int)

        self.update_widget()
        return True
    
    def redo(self):
        ic_set = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        ic_set.append_controller(self.new_ic)

        syn_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key).synced_signals
        for sync_tl_idx in self.changed_sync_signal_dict :
            sync_tl = syn_tl_set[sync_tl_idx]
            new_data = self.changed_sync_signal_dict[sync_tl_idx][1]

            sync_tl.intersection_controller_id = new_data

        self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic)

        self.update_widget()
    
    def undo(self):
        ic_set = self.canvas.getIntersectionControllerSet(self.mgeo_key)
        ic_set.remove_ic_signal(self.new_ic)

        syn_tl_set = self.canvas.getSyncedTLSet(self.mgeo_key).synced_signals
        for sync_tl_idx in self.changed_sync_signal_dict :
            sync_tl = syn_tl_set[sync_tl_idx]
            prev_data = self.changed_sync_signal_dict[sync_tl_idx][0]

            sync_tl.intersection_controller_id = prev_data

        self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, self.new_ic.idx)
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.INTERSECTION_CONTROLLER.value
        mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdate(ICommand, metaclass=ABCMeta):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.sp = self.canvas.sp.copy()
        self.idx = idx
        self.field_name = field_name
        self.prev_val = prev_val
        self.new_val = new_val

    def execute(self):
        self.update_value(self.prev_val, self.new_val)
        self.update_widget()
        return True
    
    def redo(self):
        self.update_value(self.prev_val, self.new_val)
        self.canvas.updateMgeoPropWidget(self.sp)
        self.update_widget()
    
    def undo(self):
        self.update_value(self.new_val, self.prev_val)
        self.canvas.updateMgeoPropWidget(self.sp)
        self.update_widget()

    @abstractmethod
    def update_value(self, prev_val, new_val) :
        pass

    @abstractmethod
    def update_widget(self) :
        pass

class EditPropUpdateNode(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateNode, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        node_set = self.canvas.getNodeSet(self.mgeo_key).nodes
        node = node_set[self.idx]
        edit_node.update_node(node_set, self.canvas.getLinkSet(self.mgeo_key).lines, self.canvas.getJunctionSet(self.mgeo_key).junctions, node, self.field_name, prev_val, new_val)
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.NODE, prev_val, node)
        elif self.field_name == 'point':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.NODE, node.idx, node)
            if node.junctions is not None :
                for junction_idx in node.junctions :
                    self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.JUNCTION, junction_idx, node.junctions[junction_idx])
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.NODE.value
        mgeo_flags |= MGeoItemFlags.JUNCTION.value
        if self.field_name == "from_links" or self.field_name == "to_links" :
            mgeo_flags |= MGeoItemFlags.LINK.value
            
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateLink(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateLink, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        link = link_set[self.idx]
        edit_link.update_link(link_set, self.canvas.getNodeSet(self.mgeo_key).nodes, link, self.field_name, prev_val, new_val)
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, prev_val, link)
        elif self.field_name == 'points' :
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
        if self.field_name == "from_node" or self.field_name == "to_node" :
            mgeo_flags |= MGeoItemFlags.NODE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateTrafficSign(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateTrafficSign, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        ts_list = self.canvas.getTSSet(self.mgeo_key).signals
        ts = ts_list[self.idx]
        edit_signal.update_signal(ts_list, self.canvas.getLinkSet(self.mgeo_key).lines, ts, self.field_name, prev_val, new_val)

        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.TRAFFIC_SIGN, prev_val, ts)
        elif self.field_name == 'point':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.TRAFFIC_SIGN, ts.idx, ts)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.TRAFFIC_SIGN.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateTrafficLight(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateTrafficLight, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        tl_list = self.canvas.getTLSet(self.mgeo_key).signals
        tl = tl_list[self.idx]
        edit_signal.update_signal(tl_list, self.canvas.getLinkSet(self.mgeo_key).lines, tl, self.field_name, prev_val, new_val)

        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.TRAFFIC_LIGHT, prev_val, tl)
        elif self.field_name == 'point':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.TRAFFIC_LIGHT, tl.idx, tl)
            ic_dict = self.canvas.getIntersectionControllerSet(self.mgeo_key).intersection_controllers
            for ic_idx in ic_dict :
                ic = ic_dict[ic_idx]
                if tl.idx in ic.TL_dict :
                    self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.INTERSECTION_CONTROLLER, ic_idx, ic)

            ss_dict = self.canvas.getSyncedTLSet(self.mgeo_key).synced_signals
            for ss_idx in ss_dict :
                ss = ss_dict[ss_idx]
                if tl.idx in ss.signal_id_list :
                    self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SYNCED_TRAFFIC_LIGHT, ss_idx, ss)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.TRAFFIC_LIGHT.value
        mgeo_flags |= MGeoItemFlags.INTERSECTION_CONTROLLER.value
        mgeo_flags |= MGeoItemFlags.SYNCED_TRAFFIC_LIGHT.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateJunction(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateJunction, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        junction_set = self.canvas.getJunctionSet(self.mgeo_key)
        node_set = self.canvas.getNodeSet(self.mgeo_key)
        junction = junction_set.junctions[self.idx]

        if self.field_name == "idx" :
            edit_junction.edit_junction_id(junction_set, junction, new_val)
        elif self.field_name == "jc nodes id":
            edit_junction.edit_junction_node(junction, node_set, new_val)

        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.JUNCTION, prev_val, junction)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.JUNCTION.value
        mgeo_flags |= MGeoItemFlags.NODE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateLaneNode(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateLaneNode, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        lanenode_set = self.canvas.getLaneNodeSet(self.mgeo_key).nodes
        lanenode = lanenode_set[self.idx]
        edit_node.update_node(lanenode_set, self.canvas.getLaneBoundarySet(self.mgeo_key).lanes, self.canvas.getJunctionSet(self.mgeo_key).junctions, lanenode, self.field_name, prev_val, new_val)
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_NODE, prev_val, lanenode)
        elif self.field_name == 'point':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_NODE, lanenode.idx, lanenode)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LANE_NODE.value
        mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
            
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateLaneBoundary(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateLaneBoundary, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key).lanes
        lane = lane_set[self.idx]
        edit_lane_boundary.update_lane(lane_set, self.canvas.getLaneNodeSet(self.mgeo_key).nodes, lane, self.field_name, prev_val, new_val)                  
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, prev_val, lane)
        elif self.field_name == 'points':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane.idx, lane)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LANE_NODE.value
        mgeo_flags |= MGeoItemFlags.LANE_BOUNDARY.value
            
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateRoadPolygon(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateRoadPolygon, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        rp_set = self.canvas.getRoadPolygonSet(self.mgeo_key).data
        road_polygon = rp_set[self.idx]
        edit_road_poly.update_road_poly(rp_set, road_polygon, self.field_name, prev_val, new_val)
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.ROADPOLYGON, prev_val, road_polygon)
        elif self.field_name == 'points':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.ROADPOLYGON, road_polygon.idx, road_polygon)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.ROADPOLYGON.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateParkingSpace(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateParkingSpace, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        ps_set = self.canvas.getParkingSpaceSet(self.mgeo_key).data
        ps = ps_set[self.idx]

        edit_parking_space.update_parking_space(ps_set, self.canvas.getLinkSet(self.mgeo_key).lines, ps, self.field_name, new_val)
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.PARKING_SPACE, prev_val, ps)
        elif self.field_name == 'points':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.PARKING_SPACE, ps.idx, ps)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.PARKING_SPACE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class EditPropUpdateSurfaceMarking(EditPropUpdate):
    def __init__(self, canvas, idx, field_name, prev_val, new_val):
        super(EditPropUpdateSurfaceMarking, self).__init__(canvas, idx, field_name, prev_val, new_val)

    def update_value(self, prev_val, new_val) :
        sm_set = self.canvas.getSurfaceMarkingSet(self.mgeo_key).data
        sm = sm_set[self.idx]

        edit_surfacemarking.update_surfacemarking(sm_set, self.canvas.getLinkSet(self.mgeo_key).lines, sm, self.field_name, new_val)
        if self.field_name == 'idx':
            self.idx = new_val
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SURFACE_MARKING, prev_val, sm)
        elif self.field_name == 'points':
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.SURFACE_MARKING, sm.idx, sm)
        
    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.PARKING_SPACE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class CreateLaneChangeLinks(ICommand):
    def __init__(self, canvas):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.new_link_set = None
        
    def execute(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lane_ch_link_set = create_lane_change_link_auto_depth_using_length(
                link_set, method=1, min_length_for_lane_change=20)

        link_set = LineSet.merge_two_sets(link_set, lane_ch_link_set)
        self.canvas.mgeo_maps_dict[self.mgeo_key].link_set = link_set
        for new_link_idx in lane_ch_link_set.lines :
            new_link = lane_ch_link_set.lines[new_link_idx]
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, new_link)

        link_set.erase_plot()
        self.canvas.mgeo_maps_dict[self.mgeo_key].lane_change_link_included = True
        self.update_widget()

        #undo 를 위해 저장
        self.new_link_set = lane_ch_link_set
        return True
    
    def redo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        link_set = LineSet.merge_two_sets(link_set, self.new_link_set)
        self.canvas.mgeo_maps_dict[self.mgeo_key].link_set = link_set

        for new_link_idx in self.new_link_set.lines :
            new_link = self.new_link_set.lines[new_link_idx]
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, new_link)

        link_set.erase_plot()
        self.canvas.mgeo_maps_dict[self.mgeo_key].lane_change_link_included = True
        self.update_widget()
    
    def undo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        for idx in self.new_link_set.lines :
            new_link = link_set.lines[idx]
            link_set.remove_line(new_link)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, idx)

        link_set.erase_plot()
        self.canvas.mgeo_maps_dict[self.mgeo_key].lane_change_link_included = False
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class DeleteLaneChangeLinks(ICommand):
    def __init__(self, canvas):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.node_dict = dict()
        self.removed_links = list()
        self.another_link_left = list()
        self.another_link_right = list()
        
    def execute(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lines = link_set.lines

        delete_list = list()
        for line_idx in lines:
            link = lines[line_idx]
            is_lane_change_link = link.lazy_point_init
            if is_lane_change_link:
                delete_list.append(line_idx)
        
        for line_idx in delete_list:
            link = lines[line_idx]
            is_lane_change_link = link.lazy_point_init
            if is_lane_change_link:
                to_node = link.get_to_node()
                from_node = link.get_from_node()

                to_node_idx = to_node.idx if to_node != None else None
                from_node_idx = from_node.idx if from_node != None else None

                self.node_dict[line_idx] = [from_node_idx, to_node_idx]

                to_node.remove_from_links(link)
                from_node.remove_to_links(link)

                # Line Set에서 line에 대한 reference를 제거한다
                link_set.remove_line(link)
                self.removed_links.append(link)
                self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, link.idx)

                # 현재의 링크가 다른 링크의 dst link로 설정되어 있으면 이를 None으로 변경해주어야 한다
                for key, another_link in link_set.lines.items():
                    
                    # 차선 변경이 아닌 링크에 대해서만 검사하면 된다.
                    if not another_link.is_it_for_lane_change():
                        if another_link.get_left_lane_change_dst_link() is link:
                            another_link.lane_ch_link_left = None
                            self.another_link_left.append([key, line_idx])
                        if another_link.get_right_lane_change_dst_link() is link:
                            another_link.lane_ch_link_right = None
                            self.another_link_right.append([key, line_idx])

        Logger.log_info('Lane Change Links deleted.')
        self.canvas.mgeo_maps_dict[self.mgeo_key].lane_change_link_included = False
        self.update_widget()

        return True
    
    def redo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        for link in self.removed_links :
            to_node = link.get_to_node()
            from_node = link.get_from_node()

            to_node.remove_from_links(link)
            from_node.remove_to_links(link)

            link_set.remove_line(link)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LINK, link.idx)

        for ref_info in self.another_link_left :
            another_link_key = ref_info[0]
            another_link = link_set.lines[another_link_key]

            another_link.lane_ch_link_left = None

        for ref_info in self.another_link_right :
            another_link_key = ref_info[0]
            another_link = link_set.lines[another_link_key]

            another_link.lane_ch_link_right = None

        self.canvas.mgeo_maps_dict[self.mgeo_key].lane_change_link_included = False
        self.update_widget()
    
    def undo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        node_set = self.canvas.getNodeSet(self.mgeo_key)
        for link in self.removed_links :
            link_set.append_line(link, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LINK, link)
            if link.idx in self.node_dict :
                node_data = self.node_dict[link.idx]
                from_node_idx = node_data[0]
                to_node_idx = node_data[1]

                if from_node_idx != None and from_node_idx in node_set.nodes :
                    from_node = node_set.nodes[from_node_idx]
                    link.set_from_node(from_node)

                if to_node_idx != None and to_node_idx in node_set.nodes :
                    to_node = node_set.nodes[to_node_idx]
                    link.set_to_node(to_node)

        for ref_info in self.another_link_left :
            another_link_key = ref_info[0]
            link_key = ref_info[1]
            another_link = link_set.lines[another_link_key]
            ref_link = link_set.lines[link_key]

            another_link.lane_ch_link_left = ref_link

        for ref_info in self.another_link_right :
            another_link_key = ref_info[0]
            link_key = ref_info[1]
            another_link = link_set.lines[another_link_key]
            ref_link = link_set.lines[link_key]

            another_link.lane_ch_link_right = ref_link

        self.canvas.mgeo_maps_dict[self.mgeo_key].lane_change_link_included = True
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class FillPointsInAllLinks(ICommand):
    def __init__(self, canvas, step_len, keep_points):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.step_len = step_len
        self.keep_points = keep_points
        self.points_dict = dict()
        
    def execute(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        for idx in link_set.lines:
            link = link_set.lines[idx]
            prev_points = link.points
            edit_line.fill_in_points_evenly(link, self.step_len, self.keep_points)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)

            new_points = link.points
            self.points_dict[idx] = [prev_points, new_points]
            
        self.update_canvas()

        return True
    
    def redo(self):
        self.update_link(False)
    
    def undo(self):
        self.update_link(True)

    def update_link(self, is_undo) :
        for idx in self.points_dict :
            link = self.canvas.getLinkSet(self.mgeo_key).lines[idx]
            
            if is_undo :
                prev_points = self.points_dict[idx][0]
                link.set_points(prev_points)
            else :
                new_points = self.points_dict[idx][1]
                link.set_points(new_points)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LINK, link.idx, link)
        self.update_canvas()

    def update_canvas(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMapData(mgeo_flags)

class FillPointsInAllLaneBoundary(ICommand):
    def __init__(self, canvas, step_len, keep_points):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.step_len = step_len
        self.keep_points = keep_points
        self.points_dict = dict()
        
    def execute(self):
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        for idx in lane_set.lanes:
            lane = lane_set.lanes[idx]
            prev_points = lane.points
            edit_line.fill_in_points_evenly(lane, self.step_len, self.keep_points)
            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane.idx, lane)

            new_points = lane.points
            self.points_dict[idx] = [prev_points, new_points]
            
        self.update_canvas()

        return True
    
    def redo(self):
        self.update_link(False)
    
    def undo(self):
        self.update_link(True)

    def update_link(self, is_undo) :
        for idx in self.points_dict :
            lane = self.canvas.getLaneBoundarySet(self.mgeo_key).lanes[idx]
            
            if is_undo :
                prev_points = self.points_dict[idx][0]
                lane.set_points(prev_points)
            else :
                new_points = self.points_dict[idx][1]
                lane.set_points(new_points)

            self.canvas.mgeo_item_updated(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane.idx, lane)
        self.update_canvas()

    def update_canvas(self) :
        mgeo_flags = MGeoItemFlags.LANE_BOUNDARY.value
        self.canvas.updateMapData(mgeo_flags)

class SimplifyLaneBoundary(ICommand):
    def __init__(self, canvas):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key

        self.new_link_list = list()
        self.old_link_list = list()
        self.old_node_list = list()
        
    def execute(self):
        simplify_candidate = list()

        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)

        for idx, node in node_set.nodes.items():
            if len(node.get_to_links()) == 1 and len(node.get_from_links()) == 1:
                    
                # 또한, attribute가 같아야 한다!
                to_link = node.get_to_links()[0]
                from_link = node.get_from_links()[0]
                if from_link.is_every_attribute_equal(to_link):
                    simplify_candidate.append(node)

        Logger.log_info('{} nodes (out of total {}) will be deleted'.format(
            len(simplify_candidate),
            len(node_set.nodes.keys())))

        # 이미 삭제한 라인의 idx를 저장 >> 중복으로 삭제 요청하는 걸 막기 위함
        new_line_idx_list = list()
        for sc_node in simplify_candidate:
            # for each node, connect its from_link and to_link together
            # then, update each from_node and to_node
            # NOTE: (hjpark) 아직 여러 경우에 수에 대해 테스팅이 필요함
            #       특히 to_node, from_node를 여러 개 소유하는 node의 경우
            #       for문 대신 index[0]를 explicit하게 처리하여 (구현 편의 위해)
            #       충분히 예외가 발생할 여지가 있음 
            current_node_to_link = sc_node.get_to_links()[0]
            current_node_from_link = sc_node.get_from_links()[0]

            # 선 2개로 이뤄진 circular line 예외처리
            if current_node_from_link == current_node_to_link:
                continue

            self.old_link_list.append([current_node_to_link, current_node_to_link.get_from_node().idx, current_node_to_link.get_to_node().idx])
            self.old_link_list.append([current_node_from_link, current_node_from_link.get_from_node().idx, current_node_from_link.get_to_node().idx])
            self.old_node_list.append(sc_node)

            # 새로운 라인/링크 생성
            new_line = LaneBoundary()

            # 포인트 생성 시, from_link의 마지막점과, to_link의 시작점이 겹치므로 from_link에서 마지막 점을 제외시킨다
            new_line.set_points(np.vstack((current_node_from_link.points[:-1], current_node_to_link.points)))

            to_node = sc_node.get_to_nodes()[0]
            from_node = sc_node.get_from_nodes()[0]
                
            to_node.remove_from_links(current_node_to_link)
            from_node.remove_to_links(current_node_from_link)

            new_line.set_to_node(to_node)
            new_line.set_from_node(from_node)

            new_line.get_attribute_from(current_node_from_link)

            lane_set.append_line(new_line, create_new_key=True)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, new_line)

            #self.new_link_list.append([new_line, from_node.idx, to_node.idx])
            new_line_idx_list.append(new_line.idx)

            lane_set.remove_line(current_node_to_link)
            lane_set.remove_line(current_node_from_link)
            node_set.remove_node(sc_node)

            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, current_node_to_link.idx)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, current_node_from_link.idx)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_NODE, sc_node.idx)

        Logger.log_info('Starting to update plot ... ')
        Logger.log_info('Simplify operation done OK. Plot update finished.')

        for new_line_idx in new_line_idx_list :
            if new_line_idx in lane_set.lanes :
                new_lane = lane_set.lanes[new_line_idx]
                new_from_node = new_lane.get_from_node()
                new_to_node = new_lane.get_to_node()

                self.new_link_list.append([new_lane, new_from_node.idx, new_to_node.idx])
        
        self.update_widget()
        return True
    
    def redo(self):
        self.remove_lanes(self.old_link_list)
        self.remove_nodes(self.old_node_list)
        self.restore_lanes(self.new_link_list)
        self.restore_refs(self.new_link_list)
        self.update_widget()
    
    def undo(self):
        self.remove_lanes(self.new_link_list)
        self.restore_lanes(self.old_link_list)
        self.restore_nodes(self.old_node_list)
        self.restore_refs(self.old_link_list)
        self.update_widget()

    def restore_refs(self, lane_list) :
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)

        for lane_item in lane_list :
            lane = lane_item[0]
            from_node_idx = lane_item[1]
            to_node_idx = lane_item[2]

            from_node = node_set.nodes[from_node_idx]
            to_node = node_set.nodes[to_node_idx]

            lane.set_from_node(from_node)
            lane.set_to_node(to_node)

    def restore_lanes(self, lane_list) :
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)

        for lane_item in lane_list :
            lane = lane_item[0]
            lane_set.append_line(lane, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane)

    def restore_nodes(self, node_list) :
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        for node in node_list :
            node_set.append_node(node, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_NODE, node)

    def remove_lanes(self, lane_list) :
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)

        for lane_item in lane_list :
            lane = lane_item[0]

            if lane.from_node != None :
                lane.remove_from_node()
            if lane.to_node != None :
                lane.remove_to_node()
            lane_set.remove_line(lane)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_BOUNDARY, lane.idx)

    def remove_nodes(self, node_list) :
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        for node in node_list :
            node_set.remove_node(node)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_NODE, node.idx)

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LANE_BOUNDARY.value
        mgeo_flags |= MGeoItemFlags.LANE_NODE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class FixDanglingLinks(ICommand):
    def __init__(self, canvas, dangling_link_idx_list):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.dangling_link_idx_list = dangling_link_idx_list
        self.new_node_list = list()
        
    def execute(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        node_set = self.canvas.getNodeSet(self.mgeo_key)
        for link_idx in self.dangling_link_idx_list:
            link = link_set.lines[link_idx]

            if link.from_node is None :
                start_node = Node()
                start_node.point = link.points[0]
                node_set.append_node(start_node, True)
                self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, start_node)
                link.set_from_node(start_node)
                self.new_node_list.append({'node':start_node, 'type':'from', 'link_idx':link.idx})

            if link.to_node is None :
                end_node = Node()
                end_node.point = link.points[len(link.points) - 1]
                node_set.append_node(end_node, True)            
                self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, end_node)
                link.set_to_node(end_node)
                self.new_node_list.append({'node':end_node, 'type':'to', 'link_idx':link.idx})

            Logger.log_info('Dangling links fixed: {}'.format(link.idx))

        self.update_widget()
        return True
    
    def redo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        node_set = self.canvas.getNodeSet(self.mgeo_key)

        for new_node_info in self.new_node_list :
            new_node = new_node_info['node']
            node_type = new_node_info['type']
            link_idx = new_node_info['link_idx']

            node_set.append_node(new_node, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, new_node)

            link = link_set.lines[link_idx]
            if node_type == 'from' :
                link.set_from_node(new_node)
            else :
                link.set_to_node(new_node)
            
        self.update_widget()
    
    def undo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        node_set = self.canvas.getNodeSet(self.mgeo_key)

        for new_node_info in self.new_node_list :
            new_node = new_node_info['node']
            node_type = new_node_info['type']
            link_idx = new_node_info['link_idx']

            link = link_set.lines[link_idx]
            if node_type == 'from' :
                link.remove_from_node()
            else :
                link.remove_to_node()
            node_set.remove_node(new_node)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.NODE, new_node.idx)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        mgeo_flags |= MGeoItemFlags.NODE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class FixDanglingLanes(ICommand):
    def __init__(self, canvas, dangling_lane_idx_list):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.dangling_lane_idx_list = dangling_lane_idx_list
        self.new_node_list = list()
        
    def execute(self):
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)
        for link_idx in self.dangling_lane_idx_list:
            lane = lane_set.lanes[link_idx]

            if lane.from_node is None :
                start_node = Node()
                start_node.point = lane.points[0]
                node_set.append_node(start_node, True)
                self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.NODE, start_node)
                lane.set_from_node(start_node)
                self.new_node_list.append({'node':start_node, 'type':'from', 'lane_idx':lane.idx})

            if lane.to_node is None :
                end_node = Node()
                end_node.point = lane.points[len(lane.points) - 1]
                node_set.append_node(end_node, True)            
                self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_NODE, end_node)
                lane.set_to_node(end_node)
                self.new_node_list.append({'node':end_node, 'type':'to', 'lane_idx':lane.idx})

            Logger.log_info('Dangling lanes fixed: {}'.format(lane.idx))

        self.update_widget()
        return True
    
    def redo(self):
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)

        for new_node_info in self.new_node_list :
            new_node = new_node_info['node']
            node_type = new_node_info['type']
            lane_idx = new_node_info['lane_idx']

            node_set.append_node(new_node, create_new_key=False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.LANE_NODE, new_node)

            lane = lane_set.lanes[lane_idx]
            if node_type == 'from' :
                lane.set_from_node(new_node)
            else :
                lane.set_to_node(new_node)
            
        self.update_widget()
    
    def undo(self):
        lane_set = self.canvas.getLaneBoundarySet(self.mgeo_key)
        node_set = self.canvas.getLaneNodeSet(self.mgeo_key)

        for new_node_info in self.new_node_list :
            new_node = new_node_info['node']
            node_type = new_node_info['type']
            lane_idx = new_node_info['lane_idx']

            link = lane_set.lanes[lane_idx]
            if node_type == 'from' :
                link.remove_from_node()
            else :
                link.remove_to_node()
            node_set.remove_node(new_node)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.LANE_NODE, new_node.idx)

        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LANE_BOUNDARY.value
        mgeo_flags |= MGeoItemFlags.LANE_NODE.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

class SetMaxSpeedLink(ICommand):
    def __init__(self, canvas, edit_value, edit_type='all_links'):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.edit_value = edit_value
        self.edit_type = edit_type
        self.prev_val_dict = dict()
        
    def execute(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lines = link_set.lines

        for link_id in lines:
            link = lines[link_id]

            if self.edit_type == 'all_links' or \
                (self.edit_type == 'empty_links' and (link.max_speed == '' or link.max_speed == None or link.max_speed == 0 or link.max_speed == '0')):
                self.prev_val_dict[link.idx] = link.max_speed
                link.max_speed = self.edit_value
                
        return True
    
    def redo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lines = link_set.lines

        for link_idx in self.prev_val_dict :
            link = lines[link_idx]
            link.max_speed = self.edit_value
    
    def undo(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key)
        lines = link_set.lines

        for link_idx in self.prev_val_dict :
            link = lines[link_idx]
            prev_val = self.prev_val_dict[link_idx]
            link.max_speed = prev_val

class FixSignalRoadConnection(ICommand):
    def __init__(self, canvas):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.road_id_dict = dict()
        self.counter = 0
        
    def execute(self):
        link_set = self.canvas.getLinkSet(self.mgeo_key).lines
        tl_set = self.canvas.getTLSet(self.mgeo_key).signals

        if tl_set is None or len(tl_set) < 1:
            Logger.log_warning('No traffic signals loaded')
            return

        counter = 0

        for signal_id, signal in tl_set.items():
            if len(signal.link_id_list) > 0:
                link_id = signal.link_id_list[0] # assume all links are in one road
                link_connected = link_set[link_id]
                link_road_id = link_connected.road_id
                if link_road_id != signal.road_id:
                    self.road_id_dict[signal_id] = [signal.road_id, link_road_id]
                    signal.road_id = link_road_id
                    counter += 1

        self.counter = counter
        return True
    
    def redo(self):
        tl_set = self.canvas.getTLSet(self.mgeo_key).signals

        for sig_id in self.road_id_dict :
            signal = tl_set[sig_id]
            new_road_id = self.road_id_dict[sig_id][1]
            signal.road_id = new_road_id
    
    def undo(self):
        tl_set = self.canvas.getTLSet(self.mgeo_key).signals

        for sig_id in self.road_id_dict :
            signal = tl_set[sig_id]
            prev_road_id = self.road_id_dict[sig_id][0]
            signal.road_id = prev_road_id

class RepairConcavePolygon(ICommand):
    def __init__(self, canvas, items):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        self.items = items.copy()
        self.new_scw_list = list()
        self.old_scw_list = list()
        
    def execute(self):
        scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        for item in self.items:
            if item['type'] == MGeoItem.SINGLECROSSWALK:
                current_item = scws.data[item['id']]
                polygon_list = divide_concave_polygon(current_item.points)
                for polygon in polygon_list:
                    scw = SingleCrosswalk()
                    scw.set_points(polygon)
                    scw.sign_type = current_item.sign_type
                    scws.append_data(scw, True)
                    self.new_scw_list.append(scw)
                    
                    self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SINGLECROSSWALK, scw)
                edit_singlecrosswalk.delete_singlecrosswalk(scws, current_item)
                self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SINGLECROSSWALK, current_item.idx)

                self.old_scw_list.append(current_item)
        
        self.update_bounding_box()
        self.update_widget()
        return True
    
    def redo(self):
        scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        for old_scw in self.old_scw_list :
            scws.remove_data(old_scw)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SINGLECROSSWALK, old_scw.idx)

        for new_scw in self.new_scw_list :
            scws.append_data(new_scw, False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SINGLECROSSWALK, new_scw)

        self.update_bounding_box()
        self.update_widget()
    
    def undo(self):
        scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        for new_scw in self.new_scw_list :
            scws.remove_data(new_scw)
            self.canvas.mgeo_item_deleted(self.mgeo_key, MGeoItem.SINGLECROSSWALK, new_scw.idx)

        for old_scw in self.old_scw_list :
            scws.append_data(old_scw, False)
            self.canvas.mgeo_item_added(self.mgeo_key, MGeoItem.SINGLECROSSWALK, old_scw)

        self.update_bounding_box()
        self.update_widget()

    def update_bounding_box(self) :
        scws = self.canvas.getSingleCrosswalkSet(self.mgeo_key)
        for scw in scws.data:
            item = scws.data[scw]
            new_points = minimum_bounding_rectangle(item.points)
            new_points = np.vstack((new_points, new_points[0]))
            item.set_points(new_points)

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)

'''
class AAA(ICommand):
    def __init__(self, canvas):
        self.canvas = canvas
        self.mgeo_key = canvas.mgeo_key
        
    def execute(self):
        self.update_widget()
        return True
    
    def redo(self):
        self.update_widget()
    
    def undo(self):
        self.update_widget()

    def update_widget(self) :
        mgeo_flags = MGeoItemFlags.LINK.value
        self.canvas.updateMgeoIdWidget(mgeo_flags)
'''