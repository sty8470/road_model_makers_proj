"""
lane marking mesh를 생성하기 위한 csv 파일을 출력한다
lane marking 정보를 종류 별로 분리하여 csv 파일을 출력한다
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common')

from shp_common import *
import shapefile
import csv
from tkinter import filedialog


def _role_code_to_string(role_code):
    if role_code == '501':
        role = '중앙선'

    elif role_code == '5011':
        # 가변 차선인데, 그냥 일반 차선으로 분류
        role = '일반차선'

    elif role_code == '502':
        role = '유턴구역선'

    elif role_code == '503':
        # 일반 차선으로 분류
        role = '일반차선'

    elif role_code == '504':
        # 버스전용차선인데, 일반 차선으로 분류
        role = '버스전용차선'

    elif role_code == '505':
        # 가장자리
        role = '길가장자리구역선'

    elif role_code == '506':
        role = '진로변경제한선'

    elif role_code == '515':
        role = '주정차금지선'

    elif role_code == '525':
        role = '유도선'

    elif role_code == '530':
        role = '정지선'
    
    elif role_code == '531':
        role = '안전지대'
    
    elif role_code == '535':
        role = '자전거도로'

    else:
        role = '기타선'

    return role

def _color_code_to_string(color_code):
    color_code = int(color_code)

    if color_code == 1:
        return '황색'
    elif color_code == 2:
        return '백색'
    elif color_code == 3:
        return '청색'
    else:
        raise BaseException('[ERROR] Undefined color_code = {}'.format(color_code))
        
def _line_num_code_to_string(line_num_code):
    line_num_code = int(line_num_code)

    if line_num_code == 1:
        return '단선'
    elif line_num_code == 2:
        return '겹선'
    else:
        raise BaseException('[ERROR] Undefined line_num_code = {}'.format(line_num_code))

def _shape_code_to_string(shape_code):
    shape_code = int(shape_code)

    if shape_code == 1:
        return '실선'
    elif shape_code == 2:
        return '점선'
    elif shape_code == 3:
        return '좌점혼선'
    elif shape_code == 4:
        return '우점혼선'
    else:
        raise BaseException('[ERROR] Undefined shape_code = {}'.format(shape_code))

def main(dir_selection_using_gui):

    # 상대좌표로 뽑을 것인가를 결정
    relative_loc = True

    if dir_selection_using_gui:
        """INPUT/OUTPUT 경로를 GUI로 설정한다"""
        # 초기 경로
        input_init_dir = os.path.join(current_path, '../../rsc/map_data/')

        # 맵 로드할 경로
        input_path = filedialog.askdirectory(
            initialdir = input_init_dir,
            title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능   

        # 출력 초기 경로
        output_init_dir = os.path.join(current_path, '../../saved/csv/') 


        # csv 저장할 경로
        output_path = filedialog.askdirectory(
            initialdir = output_init_dir,
            title = 'Save files to') # defaultextension = 'json') 과 같은거 사용 가능
    else:
        """INPUT/OUTPUT 경로를 코드로 설정한다"""
        input_path = os.path.join(current_path, '../../rsc/map_data/ngii_shp_ver2_Daegu/SEC02_테크노폴리스/HDMap_UTM52N_타원체고')
        output_path = os.path.join(current_path, '../../saved/csv/대구테크노폴리스/B2_SURFACELINEMARK_개별라인분류') 

        input_path = os.path.normpath(input_path)
        output_path = os.path.normpath(output_path)
   
    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    # Get Map Information
    map_info = read_shp_files(input_path)
    if map_info is None:
        raise BaseException('[ERROR] There is no input data (input_path might be incorrect)')

    # Find origin, using A1_NODE
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)

    # 입력용 파일
    sf = map_info['B2_SURFACELINEMARK']
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields


    file_key_num_pair = dict()

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        
        # 선의 좌표 정보를 별도 list로 저장
        line_points = list()
        for k in range(len(shp_rec.points)):
            e = shp_rec.points[k][0] - origin[0]
            n = shp_rec.points[k][1] - origin[1]
            z = shp_rec.z[k] - origin[2]

            line_points.append([e,n,z])

        # 선의 타입 정보를 key로 변경
        role_code = dbf_rec['Kind']
        color_code = dbf_rec['Type'][0]
        line_num_code = dbf_rec['Type'][1]
        shape_code = line_num = dbf_rec['Type'][2]

        role = _role_code_to_string(role_code)
        color = _color_code_to_string(color_code)
        line_num = _line_num_code_to_string(line_num_code)
        shape = _shape_code_to_string(shape_code)
        
        file_key = role + '_' + color + '_' + line_num + '_' + shape
        print(file_key)

        if file_key in file_key_num_pair.keys():
            file_key_num_pair[file_key] += 1
            pass
        else:
            file_key_num_pair[file_key] = 0
            pass

        # 파일 이름
        # 차선의 종류 + 몇번째 라인인지
        output_file_name = file_key + '_{0:04d}'.format(file_key_num_pair[file_key])

        output_file = os.path.join(output_path, output_file_name) + '.csv'
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')
            writer.writerows(line_points)
        



    # for key in key_list:
    #     input_shape = map_info[key]
        
    #     # shp data -> exportable data
    #     export_data = to_csv_exportable_data(input_shape, origin)

    #     # exportable data -> csv file
    #     output_file = os.path.join(output_path, key) + '.csv'
    #     with open(output_file, 'w', newline='') as csvfile:
    #         writer = csv.writer(csvfile, delimiter = ',')
    #         writer.writerows(export_data)


    print('END')


if __name__ == u'__main__':
    main(dir_selection_using_gui=False)