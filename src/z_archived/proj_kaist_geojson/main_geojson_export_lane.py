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

def export_lane(input_path):

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

    map_info, filename_map = geojson_common.read_geojson_files(input_path)

    # map_info['A1_NODE']
    # map_info['A2_LINK']
    # map_info['A5_PARKINGLOT']
    # map_info['B2_SURFACELINEMARK'] >> 차선 위치/교차로 유도선
    # map_info['B3_SURFACEMARK']
    # map_info['B4_CROSSWALK']
    # map_info['C3_VEHICLEPROTECTIONSAFETY'] >> 도로 경계
    # map_info['D3_SIDEWALK'] >> 인도

    origin = map_info['A1_NODE']['features'][0]['geometry']['coordinates']
    print('[INFO] Origin Set as: ', origin)

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']
    a2_path_list = map_info['A2_LINK']['features']
    b3_surfmark_list = map_info['B3_SURFACEMARK']['features']
    b4_crosswalk = map_info['B4_CROSSWALK']['features']
    d3_sidewalk = map_info['D3_SIDEWALK']['features']
    c3_roadedge = map_info['C3_VEHICLEPROTECTIONSAFETY']['features']

    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()

    for i in range(len(surf_line_list)):
        each_line = surf_line_list[i]
        obj_prop = each_line['properties']
        # 종류 추가함
        kind_str = surfline_kind_code_to_str(obj_prop['Kind'])

        if kind_str == 'Lane_Border' or kind_str == 'Lane_Center':
            # Border 이거나 CenterLine 이면 하나의 파일로 한다
            type_name = 'Lane_Center'
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name

        else:
            type_name = kind_str
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name
                
    # A2_LINK에서 나오는 파일들: 하나의 파일로 다 모은다
    type_name = 'DrivePath'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    # B3_SURFACEMARK 에서 Kind가 5321인 데이터를 찾는다
    # 이 데이터가 횡단보도이다
    type_name = 'Crosswalk'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    # D3_SIDEWALK
    type_name = 'Sidewalk'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    type_name = 'RoadEdge'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name


    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])

    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        if os.path.exists(each_out):
            print('[WARNING] Removing an existing file... ({})'.format(each_out))
            os.remove(each_out)
        
        fileOpenMode = 'w'
        with open(each_out, fileOpenMode, newline='') as csvfile:
            continue
    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        print('[INFO] Created a new file: ({})'.format(each_out))

    # B2_SURFACELINEMARK에서 나오는 파일들
    for i in range(len(surf_line_list)):
        each_line = surf_line_list[i]

        # Type을 검사
        obj_type = each_line['geometry']['type']
        
        # Properties를 검사
        obj_prop = each_line['properties']

        # Key에 따른 각 파일에 작성
        kind_str = surfline_kind_code_to_str(obj_prop['Kind'])
        key = kind_str

        fileOpenMode = 'a'
        each_out = output_file_name_list[key]

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            coord_obj = each_line['geometry']['coordinates']

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(coord_obj)
            
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = coord_obj
                _write_single_line(writer, line, relative_loc, origin)

            else:
                # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)

    key = 'DrivePath'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]

    for i in range(len(a2_path_list)):
        each_line = a2_path_list[i]
        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            coord_obj = each_line['geometry']['coordinates']

            # coord_obj가
            # 선 1개로 된 경우가 있고 / 선 2개인 경우가 있다
            # 각 경우에 coord_obj가 의미하는 바가 다르기 때문에, 아래와 같이 체크한다
            is_single_line = _is_single_line_obj(coord_obj)
            
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = coord_obj
                _write_single_line(writer, line, relative_loc, origin)

            else:
                # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)


    key = 'Sidewalk'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]
    for i in range(len(d3_sidewalk)):
        each_obj = d3_sidewalk[i]

        # Type을 검사
        obj_type = each_obj['geometry']['type']
        
        # Properties를 검사
        obj_prop = each_obj['properties']

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            coord_obj = each_obj['geometry']['coordinates'][0] 
            # 대괄호가 하나 더 들어가 있어서, 분리가 안되기 때문에 한번더들어감
            # [ [ [ [ 354683.17, 4026737.68, 67.93 ], ..., [ 354683.17, 4026737.68, 67.93 ] ] ] ]
            is_single_line = _is_single_line_obj(coord_obj)
            
            if is_single_line:
                # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                line = coord_obj
                _write_single_line(writer, line, relative_loc, origin)

            else:
                # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)

    key = 'Crosswalk'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]
    for i in range(len(b4_crosswalk)):
        each_obj = b4_crosswalk[i]

        # Type을 검사
        obj_type = each_obj['geometry']['type']
        
        # Properties를 검사
        obj_prop = each_obj['properties']

        # Kind 값을 검사
        kind_value = obj_prop['Kind']
        if kind_value == '5321':
            with open(each_out, fileOpenMode, newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter = ',')
                coord_obj = each_obj['geometry']['coordinates'][0]

                is_single_line = _is_single_line_obj(coord_obj)
            
                if is_single_line:
                    # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                    line = coord_obj
                    _write_single_line(writer, line, relative_loc, origin)

                else:
                    # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                    for line in coord_obj:
                        _write_single_line(writer, line, relative_loc, origin)
    
    key = 'RoadEdge'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]
    for i in range(len(c3_roadedge)):
        each_obj = c3_roadedge[i]

        # Kind 값을 검사
        kind_value = each_obj['properties']['Type']
        if kind_value == '4':
            with open(each_out, fileOpenMode, newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter = ',')
                try:
                    coord_obj = each_obj['geometry']['coordinates']

                    is_single_line = _is_single_line_obj(coord_obj)
                
                    if is_single_line:
                        # print('[DEBUG] line type = {}, # of line = 1'.format(key))
                        line = coord_obj
                        _write_single_line(writer, line, relative_loc, origin)

                    else:
                        # print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                        for line in coord_obj:
                            _write_single_line(writer, line, relative_loc, origin)
                except:
                    print('[ERROR] geometry == null, # of line = {}'.format(each_obj['properties']['id']))


def _debug_plot(coord_obj, origin=None):
    import matplotlib.pyplot as plt
    print('----- [DEBUG PLOT] -----')
    
    obj = np.array(coord_obj)
    dim = obj.shape
    print('dimension: ', dim)

    if obj.shape[-1] != 3:
        raise BaseException('Unexpected dimension for each point')

    plt.figure()

    if len(obj.shape) == 3:
        for each_line_abs in coord_obj:
            if origin == None:
                each_line_rel_projected = np.array(each_line_abs)[:, 0:2] 

                x = np.array(each_line_abs)[:, 0] 
                y = np.array(each_line_abs)[:, 1] 
            else:
                each_line_rel = np.array(each_line_abs) - origin
                x = np.array(each_line_rel)[:, 0] 
                y = np.array(each_line_rel)[:, 1] 
                each_line_rel_projected = each_line_rel[:, 0:2] 

            # plt.plot(each_line_rel_projected, '-x')
            plt.scatter(x, y)

    else:
        raise BaseException('NOTIMPLMENTED for case other than len(obj.shape) == 3')
    
    plt.show()

def _is_single_line_obj_2(coord_obj):
    obj = np.array(coord_obj)
    if obj.shape[-1] != 3:
        raise BaseException('Unexpected dimension for each point')

    if len(obj.shape) == 2:
        return True
    elif len(obj.shape) == 3: 
        return False
    else:
        raise BaseException('NOTIMPLMENTED for case other than len(obj.shape) == 3')

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
    line = calculate_evenly_spaced_link_points(line, 1)
    for point in line:
        if relative_loc:
            point_rel = list()
            for i in range(len(point)):
                point_rel.append(point[i] - origin[i])
            csvwriter.writerow(point_rel)
            continue
        else:
            csvwriter.writerow(point)

def calculate_evenly_spaced_link_points(points, step_len):
    total_dist = 0
    new_step_len = step_len
    for i in range(len(points) - 1):
        point_now  = points[i]
        point_next  = points[i+1]
        dist_point = np.array(point_next) - np.array(point_now)
        dist = math.sqrt(pow(dist_point[0], 2) + pow(dist_point[1], 2) + pow(dist_point[2], 2))
        total_dist += dist
        if 0 < total_dist//step_len < step_len/2:
            new_step_len = total_dist/(total_dist//step_len)
        else:
            new_step_len = total_dist/(total_dist//step_len+1)
    new_points_all = points[0]
    # print(step_len, new_step_len, total_dist)

    skip_getting_new_point = False
    for i in range(len(points) - 1):
        # 시작점을 어디로 할 것인가를 결정
        # 만일 지난번 point에서 예를 들어
        # x = 0, 3, 6, 9 까지 만들고, 
        # 원래는 x = 10까지 와야하는 상황이었다.
        # 실제로 포인트는 x = 9에만 찍혀있다.
        # 따라서 여기부터 시작하는 것이 옳다.
        if not skip_getting_new_point:
            point_now  = points[i]


        point_next = points[i + 1]

        # 2. point_now에서 point_next까지 point를 생성한다
        # 2.1) 1 step 에 해당하는 벡터 
        dir_vector = np.array(point_next) - np.array(point_now)
        mag = np.linalg.norm(dir_vector, ord=2)
        unit_vect = dir_vector / mag
        step_vect = new_step_len * unit_vect
            
        # 2.2) 벡터를 몇 번 전진할 것인가
        cnt = (int)(np.floor(mag / new_step_len))
        if cnt == 0:
            # 마지막보다 이전이면, 즉 현재포인트와 다음 포인트가 너무 가깝다
            if i < len(points) - 2:
                #만일 이렇게 되면, 다음 포인트를 그냥 여기 포인트로 하는게 낫다
                # 현재 point_now를 그 다음 point_now로 그대로 사용한다
                skip_getting_new_point = True
                continue
            else:
                # 마지막인데, 진짜 마지막 포인트가 너무 짧은 거리에 있다
                # 그냥 붙여주고 끝낸다
                new_points_all = np.vstack((new_points_all, point_next))
                break
                

        # 2.3) 현재 위치는 포함하지 않고, 새로운 포인트를 cnt 수 만큼 생성, 전체 포인트에 연결
        new_points = _create_points_using_step(point_now, step_vect, cnt)
        new_points_all = np.vstack((new_points_all, new_points))

        # 2.4) 원래 있는 point 사이의 길이가 mag로 나눠서 딱 떨어지면
        #      마지막 포인트가 포함되었다. 이에 따라 처리가 달라짐
        if mag % new_step_len == 0:
            # 이렇게되면, 끝 점이 자동으로 포함될 것이다 
            pass
        else:
            #만일 이렇게 되면, 다음 포인트를 그냥 여기 포인트로 하는게 낫다
            skip_getting_new_point = True
            point_now = new_points_all[-1]

            # 2.5) 마지막인 경우, 진짜 마지막 포인트를 강제로 넣는다
            if i == len(points) - 2:
                new_points_all = np.vstack((new_points_all, point_next))

    return new_points_all

def _create_points_using_step(current_pos, xyz_step_size, step_num):
    next_pos = current_pos

    if step_num == 0:
        # raise Exception('[ERROR] Cannot connect the two points, check your unit\
        #     vector step length')
        ret = np.array(next_pos)

    else:
        for i in range(step_num):
                
            next_pos = [next_pos[0] + xyz_step_size[0],
                next_pos[1] + xyz_step_size[1],
                next_pos[2] + xyz_step_size[2]]
            if i == 0:
                ret = np.array(next_pos)
            else:
                ret = np.vstack((ret, next_pos))

    return ret

if __name__ == u'__main__':
    input_path = 'D:\\road_model_maker\\rsc\\map_data\\stryx_mdl201203_KAIST_3rd'
    export_lane(input_path)
    