import os
import sys

from lib.mgeo.class_defs import mgeo_map_planner
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import traceback

import numpy as np
import json
from pyproj import CRS, Proj

from lib.common.logger import Logger
from lib.mgeo.class_defs import *


def mgeo_to_geojson(mgeo_map_dict, output_path):
    """
    global_coordinate_system 
    QGIS에서 열면 알 수 없는 좌표계 > +towgs84=0,0,... 지우면 괜찮음

    ** PROJ 4.x/5.x paradigm
    +datum : Datum name
    +geoidgrids : Filename of GTX grid file to use for vertical datum transforms
    +nadgrids : Filename of NTv2 grid file to use for datum transforms
    +towgs84 : 3 or 7 term datum transform parameters
    +to_meter : Multiplier to convert map units to 1.0m
    +vto_meter : Vertical conversion to meters

    towgs84 parameter
    dx(m), dy(m), dz(m), rx, ry, rz, sf
    
    """
    mgeo_key = list(mgeo_map_dict.keys())[0]
    mgeo_planner_map = mgeo_map_dict[mgeo_key]
    
    # Proj 클래스 초기화 안 될 경우 geojson export해도 의미가 없으므로, 무조건 Proj 클래스를 초기화해본다
    crs_str = None
    if mgeo_planner_map.global_coordinate_system != '':
        crs_str = Proj(mgeo_planner_map.global_coordinate_system).srs 

    # 원점
    origin = mgeo_planner_map.get_origin()

    node_set = mgeo_planner_map.node_set.nodes
    link_set = mgeo_planner_map.link_set.lines

    # TS, TL, Lane_marking, singlecrosswalk
    sign_set = mgeo_planner_map.sign_set.signals
    light_set = mgeo_planner_map.light_set.signals

    lane_boundary_set = mgeo_planner_map.lane_boundary_set.lanes
    lane_node_set = mgeo_planner_map.lane_node_set.nodes

    scw_set = mgeo_planner_map.scw_set.data

    # intersection controller
    intersection_controller_set = mgeo_planner_map.intersection_controller_set.intersection_controllers

    node_to_geojson(crs_str, origin, node_set, output_path, 'MGeoNode')
    line_to_geojson(crs_str, origin, link_set, output_path, 'MGeoLink')

    node_to_geojson(crs_str, origin, lane_node_set, output_path, 'MGeoLaneNode')
    line_to_geojson(crs_str, origin, lane_boundary_set, output_path, 'MGeoLaneBoundary')
    
    signal_to_geojson(crs_str, origin, sign_set, output_path, 'MGeoTrafficSign')
    signal_to_geojson(crs_str, origin, light_set, output_path, 'MGeoTrafficLight')
    
    plane_to_geojson(crs_str, origin, scw_set, output_path, 'MGeoSingleCrosswalk')

    intersection_controller_to_geojson(crs_str, origin, light_set, intersection_controller_set, output_path, 'MGeoIntersectionController')


# node to geojson
def node_to_geojson(crs_str, origin, node_set, output_path, data_name):

    feature = []

    for idx in node_set:

        node_prop = node_set[idx].to_dict()
        coordinates = np.array(node_prop['point']) + origin

        geojson_info = {
            'geometry': {
                'coordinates': coordinates.tolist(),
                'type': 'Point'
            },
            'properties' : node_prop,
            'type': 'Feature'
        }

        feature.append(geojson_info)

    save_feature = {
        'type':'FeatureCollection',
        'name': data_name,
        'crs': {
            'type':'name',
            'properties':{
                'name': crs_str
            }
        },
        'features':feature,
    }

    save_file = os.path.join(output_path, '{}.geojson'.format(data_name))
    with open(save_file, 'w') as f:
        json.dump(save_feature, f, indent='\t')


# line to geojson
def line_to_geojson(crs_str, origin, line_set, output_path, data_name):

    feature = []

    for idx in line_set:

        line_prop = line_set[idx].to_dict()
        coordinates = np.array(line_prop['points']) + origin

        geojson_info = {
            'geometry': {
                'coordinates': coordinates.tolist(),
                'type': 'LineString'
            },
            'properties' : line_prop,
            'type': 'Feature'
        }

        feature.append(geojson_info)

    save_feature = {
        'type':'FeatureCollection',
        'name': data_name,
        'crs': {
            'type':'name',
            'properties':{
                'name': crs_str
            }
        },
        'features':feature,
    }

    save_file = os.path.join(output_path, '{}.geojson'.format(data_name))
    with open(save_file, 'w') as f:
        json.dump(save_feature, f, indent='\t')


# signal to geojson
def signal_to_geojson(crs_str, origin, signal_set, output_path, data_name):

    feature = []

    for idx, ts in signal_set.items():

        signal_prop = Signal.to_dict(ts)
        coordinates = np.array(signal_prop['point']) + origin

        geojson_info = {
            'geometry': {
                'coordinates': coordinates.tolist(),
                'type': 'Point'
            },
            'properties' : signal_prop,
            'type': 'Feature'
        }

        feature.append(geojson_info)

    save_feature = {
        'type':'FeatureCollection',
        'name': data_name,
        'crs': {
            'type':'name',
            'properties':{
                'name': crs_str
            }
        },
        'features':feature,
    }

    save_file = os.path.join(output_path, '{}.geojson'.format(data_name))
    with open(save_file, 'w') as f:
        json.dump(save_feature, f, indent='\t')


def plane_to_geojson(crs_str, origin, plane_set, output_path, data_name):

    feature = []

    for idx, plane in plane_set.items():

        plane_prop = plane.to_dict()
        coordinates = np.array(plane_prop['points']) + origin

        geojson_info = {
            'geometry': {
                'coordinates': [coordinates.tolist()],
                'type': 'Polygon'
            },
            'properties' : plane_prop,
            'type': 'Feature'
        }

        feature.append(geojson_info)

    save_feature = {
        'type':'FeatureCollection',
        'name': data_name,
        'crs': {
            'type':'name',
            'properties':{
                'name': crs_str
            }
        },
        'features':feature,
    }

    save_file = os.path.join(output_path, '{}.geojson'.format(data_name))
    with open(save_file, 'w') as f:
        json.dump(save_feature, f, indent='\t')


def intersection_controller_to_geojson(crs_str, origin, signal_set, controller_set, output_path, data_name):

    feature = []

    for idx, intTL in controller_set.items():

        intTL_prop = intTL.to_dict(intTL)
        
        coordinates = []
        for tls in intTL.TL:
            for tl in tls:
                coor = np.array(signal_set[tl].point) + origin
                coordinates.append(coor)
        coordinates = np.array(coordinates)
        coordinates = coordinates.mean(axis=0)

        geojson_info = {
            'geometry': {
                'coordinates': coordinates.tolist(),
                'type': 'Point'
            },
            'properties' : intTL_prop,
            'type': 'Feature'
        }

        feature.append(geojson_info)

    save_feature = {
        'type':'FeatureCollection',
        'name': data_name,
        'crs': {
            'type':'name',
            'properties':{
                'name': crs_str
            }
        },
        'features':feature,
    }

    save_file = os.path.join(output_path, '{}.geojson'.format(data_name))
    with open(save_file, 'w') as f:
        json.dump(save_feature, f, indent='\t')
