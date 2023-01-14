import imp
import sys
import os
from typing import Dict, Tuple

from PyQt5.QtCore import left

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 
sys.path.append(os.path.normpath(os.path.join(current_path, '../../'))) 
sys.path.append(os.path.normpath(os.path.join(current_path, '../../../'))) 

import traceback
import numpy as np

from tkinter import filedialog
from lib.common.logger import Logger
from lib.mgeo.class_defs import *
import lib.common.polygon_util as util
import lib.common.yaml_util as yaml_util

import lib.common.coord_trans_tm2ll as tm2ll
from pyproj import Proj
from lib.mgeo.edit.funcs.edit_mgeo_planner_map import change_world_projection
from pyproj.transformer import Transformer
# from unittest.lib.test_check_mgeo import check_related_signal


def v2xExporter(mgeo, mgeo_name):
    file_header = dict()
    file_header['versionMajor'] = 0
    file_header['versionMinor'] = 0
    file_header['descData'] = ''
    file_header['objectRLevel'] = 'Virtual_Data'
    v2xScriptableObject_dict = dict()
    v2xScriptableObject_dict['fileheader'] = file_header
    intersection_info_list = list()

    intersection_id = 100

    for idx in mgeo.intersection_controller_set.intersection_controllers:
        intersection = mgeo.intersection_controller_set.intersection_controllers[idx]
    
        centroid_point = calcProjection(mgeo, get_centroid_intersection_road(intersection))
        
        intersection_info = dict()
        intersection_info['descName'] = intersection.idx
        intersection_info['region'] = ''
        intersection_info['id']= intersection_id
        intersection_info['ll_lat'] = int(centroid_point[1])
        intersection_info['ll_long'] = int(centroid_point[0])
        intersection_info['laneWidth'] = 3.5
        
        speed_limit_dic = dict()
        speed_limit_dic['type'] = 5

        lane_set_list = setLaneId(intersection)

        lane_set_dict_list = list()

        signal_id = 0

        for lane_id in lane_set_list:
            lane_set_dic = dict()
            link = lane_set_list[lane_id][0]
            lane_set_dic['laneId']= lane_id
            lane_set_dic['laneName']= lane_id
            lane_set_dic['egressApproachId']= 0
            lane_set_dic['ingressApproachId']= 0
            lane_attributes_dic = dict()
            lane_attributes_dic['laneDirection'] = 1 if lane_set_list[lane_id][1] else 2
            lane_attributes_dic['laneSharing'] = 0
            lane_attributes_dic['laneTypeAttributes_choice']= 0
            lane_attributes_dic['laneTypeAttributes_value']= 0 # 버스차선이면 8 그외 0
            lane_set_dic['laneAttributes'] = (lane_attributes_dic)
            lane_set_dic['maneuvers']= getManeuvers(link, lane_attributes_dic['laneDirection'])
            node_list_dic = dict()
            node_list_dic['delta']= 5
            node_list_dic['refData']= 0
            node_list_dic['deltaLen'] = 10
            link_list = list()
            link_list.append(link.idx)
            getMatchedLink(link, link_list, lane_set_list[lane_id][1])
            
            node_list_dic['matchedLinkList']= link_list
            
            node_list_dic['customNodes']= ''
            lane_set_dic['nodeList'] = (node_list_dic)
            connection_list = list()
            connection_id_dict = getConnectionIdList(lane_set_list, lane_id)
            
            for id in connection_id_dict:
                connection_list_dic = dict()
                connection_list_dic['laneId']= id
                connection_list_dic['maneuver'] = connection_id_dict[id]
                signal_group = setSignalGroup(intersection, lane_set_list, lane_id)
                connection_list_dic['signalGroup']= 0 if signal_group is None or signal_group is '' else signal_group
                connection_list.append(connection_list_dic)
            
            lane_set_dic['connectionList'] = connection_list
            lane_set_dict_list.append(lane_set_dic)
            
            speed_limit_dic['speed'] = int(link.max_speed)

        intersection_info['laneSet'] = lane_set_dict_list
        speed_limit_list = list()
        speed_limit_list.append(speed_limit_dic)
        intersection_info['speedLimits'] = speed_limit_list
        intersection_info_list.append(intersection_info)

        intersection_id = intersection_id + 100
        
    v2xScriptableObject_dict['intersection_information'] = intersection_info_list
   
    file_path = os.path.normpath(os.path.join(current_path, '../../../data'))
    file_name = str.format('v2x_{}.yml', mgeo_name)
    file_full_path = os.path.join(file_path, file_name)
    v2xScriptableObject = yaml_util.createYaml(v2xScriptableObject_dict, file_full_path)

    return v2xScriptableObject



def get_intersection_item(mgeo,intersection):
    centroid_point = calcProjection(mgeo, get_centroid_intersection_road(intersection))
        
    intersection_info = dict()
    intersection_info['descName'] = intersection.idx
    intersection_info['region'] = ''
    intersection_info['id']= intersection.idx
    intersection_info['ll_lat'] = int(centroid_point[1])
    intersection_info['ll_long'] = int(centroid_point[0])
    intersection_info['laneWidth'] = 3.5
    
    speed_limit_dic = dict()
    speed_limit_dic['type'] = 5

    lane_set_list = setLaneId(intersection)

    lane_set_dict_list = list()

    signal_id = 0

    for lane_id in lane_set_list:
        lane_set_dic = dict()
        link = lane_set_list[lane_id][0]
        lane_set_dic['laneId']= lane_id
        lane_set_dic['laneName']= lane_id
        lane_set_dic['egressApproachId']= 0
        lane_set_dic['ingressApproachId']= 0
        lane_attributes_dic = dict()
        lane_attributes_dic['laneDirection'] = 1 if lane_set_list[lane_id][1] else 2
        lane_attributes_dic['laneSharing'] = 0
        lane_attributes_dic['laneTypeAttributes_choice']= 0
        lane_attributes_dic['laneTypeAttributes_value']= 0 # 버스차선이면 8 그외 0
        lane_set_dic['laneAttributes'] = (lane_attributes_dic)
        lane_set_dic['maneuvers']= getManeuvers(link, lane_attributes_dic['laneDirection'])
        node_list_dic = dict()
        node_list_dic['delta']= 5
        node_list_dic['refData']= 0
        node_list_dic['deltaLen'] = 10
        link_list = list()
        link_list.append(link.idx)
        getMatchedLink(link, link_list, lane_set_list[lane_id][1])
        
        node_list_dic['matchedLinkList']= link_list
        
        node_list_dic['customNodes']= ''
        lane_set_dic['nodeList'] = (node_list_dic)
        connection_list = list()
        connection_id_dict = getConnectionIdList(lane_set_list, lane_id)
        
        for id in connection_id_dict:
            connection_list_dic = dict()
            connection_list_dic['laneId']= id
            connection_list_dic['maneuver'] = connection_id_dict[id]
            signal_group = setSignalGroup(intersection, lane_set_list, lane_id)
            connection_list_dic['signalGroup']= 0 if signal_group is None or signal_group is '' else signal_group
            connection_list.append(connection_list_dic)
        
        lane_set_dic['connectionList'] = connection_list
        lane_set_dict_list.append(lane_set_dic)
        
        speed_limit_dic['speed'] = int(link.max_speed)

    intersection_info['laneSet'] = lane_set_dict_list
    speed_limit_list = list()
    speed_limit_list.append(speed_limit_dic)
    intersection_info['speedLimits'] = speed_limit_list
    

    return intersection_info


def get_centroid_intersection_road(intersection_control):
    points = intersection_control.get_intersection_controller_points()
    centroid_point = util.calculate_centroid(points)

    return centroid_point
   

def setLaneId(intersection):
    lane_dict = dict()
    lane_id = 0
    for tl_list in intersection.TL:
        car_tl_index = list(filter((lambda x: intersection.TL_dict[tl_list[x]].type == 'car'), range(tl_list.__len__())))
        if car_tl_index.__len__() == 0:
            continue
        tl = intersection.TL_dict[tl_list[car_tl_index[0]]]
        if tl.type == 'pedestrian':
            tl = intersection.TL_dict[tl_list[1]]
        for link in tl.link_list:
            ingress_link_list = link.get_from_links()
            egress_link_list = link.get_to_links()
            for ingress_link in ingress_link_list:
                for egress_link in egress_link_list:
                    if ingress_link.is_it_for_lane_change() == True:
                        continue

                    if (ingress_link, True)  not in lane_dict.values():
                        
                        lane_id = lane_id + 1
                        lane_dict[lane_id] = ingress_link, True
                    
                    if egress_link.is_it_for_lane_change() == True:
                        continue
                    
                    if (egress_link, False) not in lane_dict.values():
                        
                        lane_id = lane_id + 1
                        lane_dict[lane_id] = egress_link, False
    return lane_dict
            

def setSignalGroup(intersection, lane_dict, lane_id):
    synced_signal_dict = dict()
    signal_group_id = 1 
    for syncedSginalList in intersection.TL:
        tl_list = list()
        for tl_id in syncedSginalList:
            tl = intersection.TL_dict[tl_id]
            if tl.type == 'pedestrian':
                continue
            else:
                tl_list.append(tl)
        
        synced_signal_dict[signal_group_id] = tl_list
        signal_group_id = signal_group_id + 1

    # lane 매칭
    if lane_dict[lane_id][1] == 1:
        links = lane_dict[lane_id][0].get_to_links()
        for link in links:
            tl_list = link.get_traffic_lights()
            for key in synced_signal_dict.keys():
                contain_value = next((k for k in tl_list if k in synced_signal_dict[key]), None)
                if contain_value is not None:
                    
                    return key
            # if tl_list in synced_signal_dict.values():
            #     key = next((k for k in synced_signal_dict if synced_signal_dict[k] == tl_list), None)
            #     return key
               

def getConnectionIdList(lane_list, lane_id):
    matchedLink = lane_list[lane_id]
    return_value = dict()
    if matchedLink[1]: #ingress
        to_link = matchedLink[0].get_to_links() # 사거리내링크
        for link in to_link: # 사거리 내 링크
            # if link.idx in lane_list
            if len(link.get_to_links()) > 0: 
                egress_link = link.get_to_links()[0] # 사거리에서 나온 링크
                for key in lane_list.keys():
                    if lane_list[key][0].idx == egress_link.idx: # 사거리에서 나온 링크의 lane id 매칭
                        if link.is_it_for_lane_change() == True:
                            continue
                        elif link.related_signal is None:
                            Logger.log_error('related signal is None. link : {}'.format(link.idx))
                            continue
                        else:
                            return_value[key] = get_manuvers(link)
                       
                
    return return_value

def get_manuvers(link):
    straight, left, right, uturn, left_red, right_red, change_lane, no_parking, start_after_pause, caution = 0,0,0,0,0,0,0,0,0,0
    # if link.related_signal is None:
    #         Logger.log_error('related signal is None. link : {}'.format(link.idx))
    #         return
    # else:
    if link.related_signal == 'straight':
        # straight = 1
        straight = 0b00000000001
    elif link.related_signal.__contains__('left'):
        # left = 1
        left = 0b00000000010
    elif link.related_signal.__contains__('right_unprotected'):
        right_red = 0b00000100000
    elif link.related_signal.__contains__('right'):
        # right = 1
        # right_red = 1
        right = 0b0000000100
    elif link.related_signal.__contains__('uturn'):
        # uturn = 1
        uturn = 0b000000001000
      
    maneuvers = straight|left|right|uturn|right_red

    return maneuvers
    
       

def getMatchedLink(link, link_list, isIngress):
    if isIngress:
        from_link = get_from_link(link)
        if from_link == None:
            if len(link_list) > 0:
                return link_list
            else:
                return
            
        else:
            link_list.append(from_link.idx)
            link_list = getMatchedLink(from_link, link_list, isIngress)

    else:
        to_link = get_to_link(link)
        if to_link == None:
            if len(link_list) > 0:
                return link_list
            else:
                return
        else:
            link_list.append(to_link.idx)
            link_list = getMatchedLink(to_link, link_list, isIngress)
            

def get_from_link(link):
    for from_link in link.get_from_links():
        
        if from_link.related_signal != None:
            if from_link.related_signal != '':
                return None
        
        return from_link

def get_to_link(link):
    for to_link in link.get_to_links():
        
        if to_link.related_signal != None:
            if to_link.related_signal != '':
                return None

        return to_link


def getManeuvers(link, direction):
    straight, left, right, uturn, left_red, right_red, change_lane, no_parking, start_after_pause, caution = 0,0,0,0,0,0,0,0,0,0
    
    internal_link_list = list()
    if direction == 1:
        internal_link_list = link.get_to_links()
    elif direction == 2:
        return 1
    elif direction == 0: #원래는 없는거
        internal_link_list.append(link)


    for internal_link in internal_link_list:
        if internal_link.related_signal is None:
            continue
        else:
            if internal_link.related_signal == 'straight':
                # straight = 1
                straight = 0b00000000001
            elif internal_link.related_signal.__contains__('left'):
                # left = 1
                left = 0b00000000010
            elif internal_link.related_signal.__contains__('right_unprotected'):
                right_red = 0b00000100000
            elif internal_link.related_signal.__contains__('right'):
                # right = 1
                # right_red = 1
                right = 0b0000000100
            elif internal_link.related_signal.__contains__('uturn'):
                # uturn = 1
                uturn = 0b000000001000
      
    maneuvers = straight|left|right|uturn|right_red

    return maneuvers
            

def calcProjection(mgeo, point_array):
    # TODO: 버츄어 맵이랑 일반 맵이랑 porjection 설정하는게 달라서 분기처리해야함

    prj_string = '+proj=tmerc +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
    proj4 = Proj(prj_string)

    # change_world_projection(mgeo, proj4)
    

    # change projection
    transformer = Transformer.from_crs(mgeo.global_coordinate_system, prj_string)
    
    # 1. origin change
    origin = point_array + mgeo.local_origin_in_global
    # intersection_point = orign + offset (offset은 mgeo local offset으로 부터 획득)
    changed_origin = np.array(transformer.transform(origin[0], origin[1], origin[2])) # easting northing (TM 좌표계에서 x,y값)
    # easting, northing --> lat, lon 출력 변환
    ll = proj4(changed_origin[0], changed_origin[1], inverse= True)
    ll_array = np.array(ll)
    # wgs84인경우
    # coord_trans = tm2ll.CoordTrans_TM2LL()
    # coord_trans.set_tm_params(
    #     spheroid='WGS84',
    #     latitude_of_origin=0,
    #     # central_meridian=129,
    #     central_meridian=0,
    #     scale_factor=0.9996,
    #     false_easting=0,
    #     # false_easting=500000,
    #     false_northing=0)

    # ll = coord_trans.tm2ll(
    #     east=point_array[0],
    #     north=point_array[1]
    # )

    # ll_array = np.array(ll)

    return ll_array * (1e+7)
    # return ll_array
    # wgs84 아닌경우 변환하는 로직 추가해야함 ...

    
def get_mgeo_data(load_path):
    try:
        Logger.log_trace('load MGeo data from: {}'.format(load_path))

        if len([string for string in os.listdir(load_path) if '.json' in string]) == 0:
            new_load_path = os.path.join(load_path, os.listdir(load_path)[0])
        else:
            new_load_path = load_path

        mgeo = MGeo.create_instance_from_json(new_load_path)     

        return mgeo

    except BaseException as e:
        Logger.log_error('load_mgeo failed (traceback is down below) \n{}'.format(traceback.format_exc()))
        return None

if __name__ == u'__main__':
    # test
    input_path = '../../../saved/'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)

    mgeo_file_path = filedialog.askdirectory(initialdir = input_path, 
        title = 'Load files from')
        
    mgeo = get_mgeo_data(mgeo_file_path)

    #TODO: TEST
    prj_string = '+proj=tmerc +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs'
    proj4 = Proj(prj_string).srs

    change_world_projection(mgeo, proj4)
    v2xExporter(mgeo, mgeo_file_path.split('/')[-1])



# class v2x_Lane:
#     def __init__(self, id):
#         self.lane_id = id
#         self.lane_attribute = dict()
#         self.lane_direction = 0
#         self.lane_sharing = 0
#         self.lane_type_attribute_choice = 0
#         self.lane_type_attribute_value = 0
#         self.manuvers = 0
#         self.custom_node = ''
#         self.delta = 5
#         self.delta_len = 10
#         self.matched_link_list = list()
#         self.ref_data = 0
#         self.connection_list = list()
    
    
    