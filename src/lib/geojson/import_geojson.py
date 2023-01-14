import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(current_path + '/../../lib/common') # 프로젝트 Root 경로

import numpy as np
import traceback

import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from pyproj import Proj, Transformer, CRS

from lib.mgeo.class_defs import *
from lib.mgeo.utils.logger import Logger



def mGeoGeojsonImporter(input_path):
    geojson_files, folder_info = geojson_common.read_geojson_files(input_path)
    
    node_set = NodeSet()
    link_set = LineSet()
    junction_set = JunctionSet()
    lane_node_set = NodeSet()
    lane_mark_set = LaneBoundarySet()
    light_set = SignalSet()
    cw_set = CrossWalkSet()
    scw_set = SingleCrosswalkSet()
    intersection_controller_set = IntersectionControllerSet()

    origin = geojson_common.get_first_geojson_point(geojson_files['MGeoNode']['features'])
    proj4_string = Proj(geojson_files['MGeoNode']['crs']['properties']['name']).srs

    lane_node_set, lane_set = __create_lane_node_and_lane_set_from_geojson(geojson_files['MGeoLaneNode']['features'], geojson_files['MGeoLaneBoundary']['features'], origin)
    node_set, link_set, junction_set = __create_node_and_link_set_from_geojson(geojson_files['MGeoNode']['features'], geojson_files['MGeoLink']['features'], lane_set,origin)

    light_set = __create_traffic_signal_from_geojson(geojson_files['MGeoTrafficLight']['features'], link_set, origin)
    sign_set = __create_traffic_signal_from_geojson(geojson_files['MGeoTrafficSign']['features'], link_set, origin)

    scw_set = __create_single_crosswalk_from_geojson(geojson_files['MGeoSingleCrosswalk']['features'], origin)
    if 'MGeoIntersectionController' in geojson_files:
        intersection_controller_set = __create_intersection_controller_from_geojson(geojson_files['MGeoIntersectionController']['features'], light_set, origin)

    mgeo_planner_map = MGeo(
        node_set=node_set, 
        link_set=link_set, 
        junction_set=junction_set,
        lane_node_set=lane_node_set, 
        lane_boundary_set=lane_set,
        light_set=light_set,
        sign_set=sign_set,
        intersection_controller_set=intersection_controller_set,
        scw_set=scw_set)
    mgeo_planner_map.set_origin(origin)
    mgeo_planner_map.global_coordinate_system = proj4_string

    return mgeo_planner_map


def __create_single_crosswalk_from_geojson(datas, origin):
    scw_set = SingleCrosswalkSet()
    for data in datas:
        points = data['geometry']['coordinates'][0]
        points = np.array(points) - np.array(origin)
        idx = data['properties']['idx']
        scw = SingleCrosswalk(points=points, idx=idx)
        scw.sign_type = data['properties']['sign_type']
        scw.ref_crosswalk_id = data['properties']['ref_crosswalk_id']
        scw_set.append_data(scw)
    return scw_set



def __create_traffic_signal_from_geojson(datas, link_set, origin):
    signal_set = SignalSet()
    for data in datas:
        point = data['geometry']['coordinates']
        point = np.array(point) - np.array(origin)
        traffic_signal = Signal()
        traffic_signal.point = point
        traffic_signal.idx = data['properties']['idx']
        traffic_signal.road_id = data['properties']['road_id']
        traffic_signal.type = data['properties']['type']
        traffic_signal.sub_type = data['properties']['sub_type']
        traffic_signal.dynamic = data['properties']['dynamic']
        traffic_signal.orientation = data['properties']['orientation']
        traffic_signal.country = data['properties']['country']
        traffic_signal.z_offset = data['properties']['z_offset']
        traffic_signal.height = data['properties']['height']
        traffic_signal.width = data['properties']['width']
        traffic_signal.type_def = data['properties']['type_def']
        traffic_signal.ref_crosswalk_id = data['properties']['ref_crosswalk_id']
        traffic_signal.heading = data['properties']['heading']
        for i in data['properties']['link_id_list']:
            traffic_signal.link_id_list.append(i)
            traffic_signal.add_link_ref(link_set.lines[i])
        signal_set.append_signal(traffic_signal)
    return signal_set


def __create_lane_node_and_lane_set_from_geojson(nodes, lanes, origin):
    node_set = NodeSet()
    lane_set = LaneBoundarySet()
    for data in nodes:
        point = data['geometry']['coordinates']
        point = np.array(point) - np.array(origin)
        node = Node()
        node.point = point
        node.idx = data['properties']['idx']
        node.node_type = data['properties']['node_type']
        node.junction = data['properties']['junction']
        node.on_stop_line = data['properties']['on_stop_line']
        node_set.append_node(node)

    for data in lanes:
        points = data['geometry']['coordinates']
        points = np.array(points) - np.array(origin)
        idx = data['properties']['idx']
        lane = LaneBoundary(points=points, idx=idx)
        from_node = node_set.nodes[data['properties']['from_node_idx']]
        from_node.add_to_links(lane)
        to_node = node_set.nodes[data['properties']['to_node_idx']]
        to_node.add_from_links(lane)
        lane.lane_type_def = data['properties']['lane_type_def']
        
        lane.lane_width = data['properties']['lane_width']
        lane.dash_interval_L1 = data['properties']['dash_interval_L1']
        lane.dash_interval_L2 = data['properties']['dash_interval_L2']
        lane.double_line_interval = data['properties']['double_line_interval']
        lane.geometry = data['properties']['geometry']
        if 'pass_restr' in data['properties']:
            lane.pass_restr = data['properties']['pass_restr']
        elif 'passRestr' in data['properties']:
            lane.pass_restr = data['properties']['passRestr']
        
        lane_type_offset = [0]
        if 'lane_type_offset' in data['properties']:
            lane_type_offset = data['properties']['lane_type_offset']
        elif 'lane_type_start' in data['properties']:
            lane_type_offset = data['properties']['lane_type_start']
        lane.lane_type_offset = lane_type_offset
        
        lane_type = None
        lane_type_list = []
        if 'lane_type' in data['properties']:
            lane_type = data['properties']['lane_type']
        elif 'lane_code' in data['properties']:
            lane_type = data['properties']['lane_code']
        if 'lane_type_list' in data['properties']:
            lane_type_list = data['properties']['lane_type_list']

        if len(lane_type_list) == 0 and lane_type is not None:
            if type(lane_type) == int:
                lane_type_list.append(lane_type)
            else:
                lane_type_list = lane_type
        lane.lane_type = lane_type_list

        if 'lane_sub_type' in data['properties']:
            lane.lane_sub_type = data['properties']['lane_sub_type']

        lane_color = data['properties']['lane_color']
        lane_color_list = []
        if 'lane_color_list' in data['properties']:
            lane_color_list = data['properties']['lane_color_list']
        if len(lane_color_list) == 0 and lane_color is not None:
            if type(lane_color) == str:
                lane_color_list.append(lane_color)
            else:
                lane_color_list = lane_color
        lane.lane_color = lane_color_list

        lane_type_count = len(lane.lane_type_offset)
        lane_shape = data['properties']['lane_shape']
        shape_list = []
        if len(lane_shape) == lane_type_count:
            shape_list = lane_shape
        if 'lane_shape_list' in data['properties']:
            lane_shape_list = data['properties']['lane_shape_list']
            if len(lane_shape_list) == lane_type_count:
                shape_list = lane_shape_list
        if len(shape_list) == 0 and lane_shape is not None:
            lane_shape_str = ''
            for i in range(len(lane_shape)):
                if i == 0:
                    lane_shape_str += '{}'.format(lane_shape[i])
                else:
                    lane_shape_str += ' {}'.format(lane_shape[i])
            shape_list.append(lane_shape_str)

        lane.lane_shape = shape_list
        lane_set.append_line(lane)
        
    return node_set, lane_set


def __create_node_and_link_set_from_geojson(nodes, links, lane_set, origin):
    node_set = NodeSet()
    link_set = LineSet()
    junction_set = JunctionSet()
    for data in nodes:
        point = data['geometry']['coordinates']
        point = np.array(point) - np.array(origin)
        node = Node()
        node.point = point
        node.idx = data['properties']['idx']
        node.node_type = data['properties']['node_type']
        node.junction = data['properties']['junction']
        node.on_stop_line = data['properties']['on_stop_line']
        node_set.append_node(node)
        for jc in node.junction:
            if jc in junction_set.junctions:
                junction_set.junctions[jc].add_jc_node(node)
            else:
                junction = Junction(_id=jc)
                junction.add_jc_node(node)
                junction_set.append_junction(junction)


    for data in links:
        points = data['geometry']['coordinates']
        points = np.array(points) - np.array(origin)
        idx = data['properties']['idx']
        link = Link(points=points, idx=idx)
        from_node = node_set.nodes[data['properties']['from_node_idx']]
        from_node.add_to_links(link)
        to_node = node_set.nodes[data['properties']['to_node_idx']]
        to_node.add_from_links(link)
        link.max_speed = data['properties']['max_speed']
        link.lazy_point_init = data['properties']['lazy_init']
        link.can_move_left_lane = data['properties']['can_move_left_lane']
        link.can_move_right_lane = data['properties']['can_move_right_lane']
        link.left_lane_change_dst_link_idx = data['properties']['left_lane_change_dst_link_idx']
        link.right_lane_change_dst_link_idx = data['properties']['right_lane_change_dst_link_idx']
        link.link_type = data['properties']['link_type']
        link.link_type_def = data['properties']['link_type_def']
        link.road_type = data['properties']['road_type']
        link.road_id = data['properties']['road_id']
        link.ego_lane = data['properties']['ego_lane']
        link.lane_change_dir = data['properties']['lane_change_dir']
        link.hov = data['properties']['hov']
        link.geometry = data['properties']['geometry']
        link.related_signal = data['properties']['related_signal']
        link.its_link_id = data['properties']['its_link_id']
        link.force_width_start = data['properties']['force_width_start']
        link.width_start = data['properties']['width_start']
        link.force_width_end = data['properties']['force_width_end']
        link.width_end = data['properties']['width_end']
        link.enable_side_border = data['properties']['enable_side_border']
        for i in data['properties']['lane_mark_left']:
            link.set_lane_mark_left(lane_set.lanes[i])
        for i in data['properties']['lane_mark_right']:
            link.set_lane_mark_right(lane_set.lanes[i])
        if 'opp_traffic' in data['properties']:
            link.opp_traffic = data['properties']['opp_traffic']
        elif 'oppTraffic' in data['properties']:
            link.opp_traffic = data['properties']['oppTraffic']
        else:
            link.opp_traffic = False
        link.is_entrance = data['properties']['is_entrance']
        link.is_exit = data['properties']['is_exit']
        link.speed_unit = data['properties']['speed_unit']

        if 'speed_offset' in data['properties']:
            link.speed_offset = data['properties']['speed_offset']
        elif 'speed_start' in data['properties']:
            link.speed_offset = data['properties']['speed_start']
        else:
            link.speed_offset = []
        link.speed_list = data['properties']['speed_list']
        link.recommended_speed = data['properties']['recommended_speed']
        link_set.append_line(link)

    for idx, link in link_set.lines.items():
        if link.left_lane_change_dst_link_idx is not None:
            left_link = link_set.lines[link.left_lane_change_dst_link_idx]
            link.set_left_lane_change_dst_link(left_link)
        if link.right_lane_change_dst_link_idx is not None:
            right_link = link_set.lines[link.right_lane_change_dst_link_idx]
            link.set_right_lane_change_dst_link(right_link)

    return node_set, link_set, junction_set


def __create_intersection_controller_from_geojson(datas, light_set, origin):
    intersection_controller_set = IntersectionControllerSet()
    for data in datas:
        intTL = IntersectionController.from_dict(data['properties'], light_set)
        intersection_controller_set.append_controller(intTL)
    return intersection_controller_set

if __name__ == '__main__':
    input_path = 'C:\\Users\\sjhan\\Desktop\\geojsontest'
    mGeoGeojsonImporter(input_path)