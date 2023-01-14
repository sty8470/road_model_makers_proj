import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../lib/common/')))


from mgeo_odr_converter import MGeoToOdrDataConverter
from shp_common import *
import shapefile

import numpy as np
import json
from pyproj import CRS, Proj

from lib.mgeo.class_defs import *
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save

from lib.mgeo.utils import lane_change_link_creation

def test_save_geojson(input_path):

    mgeo_planner_map = MGeo.create_instance_from_json(input_path)

    mgeo_to_geojson(mgeo_planner_map, input_path)


def mgeo_to_geojson(mgeo_planner_map, output_path):

    # global_coordinate_system
    crs_str = Proj(mgeo_planner_map.global_coordinate_system).srs.replace('+towgs84=0,0,0,0,0,0,0 ', '')

    # 원점
    origin = mgeo_planner_map.get_origin()

    node_set = mgeo_planner_map.node_set.nodes
    link_set = mgeo_planner_map.link_set.lines

    # TS, TL, Lane_marking, singlecrosswalk
    sign_set = mgeo_planner_map.sign_set.signals
    light_set = mgeo_planner_map.light_set.signals

    lane_boundary_set = mgeo_planner_map.lane_marking_set.lanes
    lane_node_set = mgeo_planner_map.lane_node_set.nodes

    scw_set = mgeo_planner_map.scw_set.data

    node_to_geojson(crs_str, origin, node_set, output_path, 'MGeoNode')
    line_to_geojson(crs_str, origin, link_set, output_path, 'MGeoLink')

    node_to_geojson(crs_str, origin, lane_node_set, output_path, 'MGeoLaneNode')
    line_to_geojson(crs_str, origin, lane_marking_set, output_path, 'MGeoLaneMarking')
    
    signal_to_geojson(crs_str, origin, sign_set, output_path, 'MGeoTrafficSign')
    signal_to_geojson(crs_str, origin, light_set, output_path, 'MGeoTrafficLight')
    
    plane_to_geojson(crs_str, origin, scw_set, output_path, 'MGeoSingleCrosswalk')


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


if __name__ == '__main__':
    input_path = os.path.normpath(os.path.join(current_path, '../../../saved/지오제이슨/상암'))
    test_save_geojson(input_path)


