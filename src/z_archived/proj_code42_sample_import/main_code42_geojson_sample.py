"""
Code42에서 제공한 geojson 포맷의 파일을 읽고,
3dmax 등에서 활용이 가능하도록 csv 파일로 만들어낸다.  
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import json
import csv
import numpy as np
from code42_geojson import * 
from ngii_shp_ver2_utils import surfline_kind_code_to_str, surfline_type_code_to_str


def main():
    input_path = '../../rsc/map_data/geojson_Code42_Sample/toGwacheonSample'
    output_path = '../../output/geojson_code42/toGwacheonSample'
    relative_loc = True

    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   

    # inputPath = os.path.normcase(inputPath)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)   

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get File List
    map_info = read_geojson_files(input_path)


    """
    참고: Code42 샘플 코드에 포함된 데이터의 종류는 다음과 같다
    """
    # map_info['A1_NODE']
    # map_info['A2_LINK']
    # map_info['A2_LINK_PATH']
    # map_info['B1_SAFETYSIGN']
    # map_info['B2_SURFACELINEMARK']
    # map_info['B3_SURFACEMARK']
    # map_info['C1_TRAFFICLIGHT']
    # map_info['C4_SPEEDBUMP']
    # map_info['C6_POSTPOINT']

    origin = get_origin(map_info)
    print('[INFO] Origin Set as: ', origin)

    surf_line_list = map_info['B2_SURFACELINEMARK']['features']
    a2_path_list = map_info['A2_LINK']['features']
    b3_surfmark_list = map_info['B3_SURFACEMARK']['features']
    c4_speedbump_list = map_info['C4_SPEEDBUMP']['features']

    """
    우선 surf_line_list에서 Type별로 파일 이름을 만든다
    """ 
    # B2_SURFACELINEMARK에서 나오는 파일들:surf_line_list[i]['properties']['Type']에 따라 나눈다
    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()
    for i in range(len(surf_line_list)):
        each_line = surf_line_list[i]
        obj_prop = each_line['properties']

        kind_str = surfline_kind_code_to_str(obj_prop['Kind'])
        if kind_str == 'Lane_Border' or kind_str == 'Lane_Center':
            # Border 이거나 CenterLine 이면 하나의 파일로 한다
            type_name = kind_str
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name

        else:
            # 아닌 경우는 형상 정보 (type_str) 까지 이용하여 구분한다
            type_str = surfline_type_code_to_str(obj_prop['Type'])
            type_name = kind_str + '_' + type_str 
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

    # C4_SPEEDBUMP에서 나오는 파일들: 하나의 파일로 다 모은다
    type_name = 'Speedbump'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name


    """
    이 output_file_name_list를 전부 절대 경로로 변경한다
    """
    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])

    """
    이 output_file_name_list에 해당하는 빈 파일을 전부 생성한다
    """
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



    """
    surf_line_list에 포함된 각 line을 구성하는 point 좌표를
    csv 파일에 기록한다
    이 때 line의 type을 보고, 해당 type의 파일에 point를 기록한다
    같은 종류의 라인이면, 같은 파일에 모두 기록된다 
    """
    # B2_SURFACELINEMARK에서 나오는 파일들
    for i in range(len(surf_line_list)):
        each_line = surf_line_list[i]

        # Type을 검사
        obj_type = each_line['geometry']['type']
        
        # Properties를 검사
        obj_prop = each_line['properties']

        # Key에 따른 각 파일에 작성
        kind_str = surfline_kind_code_to_str(obj_prop['Kind'])
        if kind_str == 'Lane_Border' or kind_str == 'Lane_Center':
            key = kind_str
        else:
            type_str = surfline_type_code_to_str(obj_prop['Type'])
            key = kind_str + '_' + type_str

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
                print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)

    # A2_LINK에서 나오는 파일들
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
                print('[DEBUG] line type = {}, # of line = {}'.format(key, len(coord_obj)))
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)

    # B3_SURFACEMARK에서 나오는 파일들
    key = 'Crosswalk'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]
    for i in range(len(b3_surfmark_list)):
        each_obj = b3_surfmark_list[i]

        # Type을 검사
        obj_type = each_obj['geometry']['type']
        
        # Properties를 검사
        obj_prop = each_obj['properties']

        # Kind 값을 검사
        kind_value = obj_prop['Kind']
        if kind_value == '5321':
            coord_obj = each_obj['geometry']['coordinates']
            # _debug_plot(coord_obj)

            with open(each_out, fileOpenMode, newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter = ',')
                coord_obj = each_obj['geometry']['coordinates']
                for line in coord_obj:
                    _write_single_line(writer, line, relative_loc, origin)

    # C$_SPEEDBUMP에서 나오는 파일 
    key = 'Speedbump'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]
    for i in range(len(c4_speedbump_list)):
        each_obj = c4_speedbump_list[i]

        coord_obj = each_obj['geometry']['coordinates']
        # _debug_plot(coord_obj)

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            coord_obj = each_obj['geometry']['coordinates']
            for line in coord_obj:
                _write_single_line(writer, line, relative_loc, origin)


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
    main()
    