import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import math
import json
import csv
import numpy as np

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *
import lib.common.geojson_common as geojson_common
import lib.common.shp_common as shp_common

from lib.stryx.stryx_geojson import *

def export_road_sejongLakePark(input_path):

    output_path = os.path.join(input_path, 'output') 
    relative_loc = True

    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    except OSError:
        print('Error: Creating directory. ' +  output_path)

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__)) 

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get File List
    map_info, filename_map = geojson_common.read_geojson_files(input_path)
    
    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']
    c3_roadedge = map_info['C3_VEHICLEPROTECTIONSAFETY']['features']

    output_file_name_list = dict()
    output_file_name_list['B2_SURFACELINEMARK'] = 'B2_SURFACELINEMARK.csv'
    output_file_name_list['C3_VEHICLEPROTECTIONSAFETY'] = 'C3_VEHICLEPROTECTIONSAFETY.csv'
    
    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])

    each_out = output_file_name_list['C3_VEHICLEPROTECTIONSAFETY']
    with open(each_out, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter = ',')
        for each_line in c3_roadedge:
            coord_obj = each_line['geometry']['coordinates']

            is_single_line = _is_single_line_obj(coord_obj)

            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = coord_obj
                _write_single_line(writer, line, relative_loc, origin)

            else:
                # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)

    each_out = output_file_name_list['B2_SURFACELINEMARK']
    with open(each_out, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter = ',')
        for each_line in surf_line_list:
            coord_obj = each_line['geometry']['coordinates']

            is_single_line = _is_single_line_obj(coord_obj)

            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = coord_obj
                _write_single_line(writer, line, relative_loc, origin)

            else:
                # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)
    print('Road END')



def _is_single_line_obj(coord_obj):
    """
    [NOTE] Point가 실제 어디서 나오는지 확인해야 한다.
    ----------
    Case #1 >> Type = 121과 같은 경우, 겹선으로 예상되는데,
    이 때는 실제 라인이 2개이므로, coord_obj가 실제로는 선의 list 이고, 
    coord_obj[0], coord_obj[1]이 각 선을 이루는 point의 집합이 되는 구조이다. 
    즉, line0 = coord_obj[0]라고 둔다면,
    coord_obj[0][0] 가 point0가 되고, len(coord_obj[0][0])이 3이 되고, type(coord_obj[0][0][0])이 float이다.
    ----------
    Case #2 >> 그 밖의 Case에서는, 
    coord_obj가 실제 point의 집합이 된다
    즉, line0 = coord_obj이다. (위에서는 coord_obj[0]이었음!)
    coord_obj[0] 가 point0가 되고, len(coord_obj[0])이 3이 되고, type(coord_obj[0][0])이 float이다.
    ----------
    결론 >> coord_obj[0][0] 의 type이 list인지, float인지 확인하면 된다.
    """

    if type(coord_obj[0][0]) is float:
        # Case #2 같은 경우임 (일반적인 경우)
        # 즉, coord_obj 1가 유일한 선이고,
        # coord_obj[0]    이 첫번째 point이고,
        # coord_obj[0][0] 이 첫번째 point의 x좌표인것
        point0 = coord_obj[0]
        if len(point0) != 3:
            raise BaseException('[ERROR] @ len(point0) != 3')
        return True

    elif type(coord_obj[0][0]) is list:
        # Case #1 같은 경우임
        # 즉, coord_obj[0], coord_obj[1] 각각이 선이다
        # coord_obj[0]       이 첫번째 line이고,
        # coord_obj[0][0]    이 첫번째 line의 첫번째 point이고
        # coord_obj[0][0][0] 이 첫번째 line의 첫번째 point의 x좌표인 것
        point0 = coord_obj[0][0]
        if len(point0) != 3:
            raise BaseException('[ERROR] @ len(point0) != 3')

        return False
    else:
        raise BaseException('[ERROR] Unexpected type for coord_obj[0][0] = {}'.format(type(coord_obj[0][0])))

def _write_single_line(csvwriter, line, relative_loc, origin=None):
    for point in line:
        if relative_loc:
            point_rel = list()
            for i in range(len(point)):
                point_rel.append(point[i] - origin[i])

            csvwriter.writerow(point_rel)
            continue
        else:
            csvwriter.writerow(point)

if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201120_SejongLakePark'
    export_road_sejongLakePark(input_path)