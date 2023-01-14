import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))

import json

def read_geojson_files(input_folder_path, filename_to_key_func=None):
    """
    input_folder_path 변수가
    - 파일 이름을 포함하고 있으면 >> #1a 가 실행
    - 폴더 이름이면              >> #1b 가 실행

    TODO(sjhan): list가 아니고, 그냥 파일 이름만 넘어오면, #1b가 실행되는 문제
    """

    
    # input_folder_path가 리스트로 넘어오면 리스트로 사용하고, path 설정
    if type(input_folder_path) == list:
        # ---------- Section #1a ----------
        file_list = []
        for f in input_folder_path:
            file_list.append(os.path.basename(f))
        input_folder_path = os.path.dirname(input_folder_path[0])
        # ---------- Section #1a ----------
    else:
        # ---------- Section #1b ----------
        file_list = os.listdir(input_folder_path)
        # ---------- Section #1b ----------

    

    data = {}
    filename_map = {}

    for each_file in file_list:
        file_full_path = os.path.join(input_folder_path, each_file)
        
        # 디렉토리는 Skip
        if os.path.isdir(file_full_path):
            continue
        
        # geojson인지 체크
        filename, file_extension = os.path.splitext(each_file)
        if file_extension == '.geojson':
            if filename_to_key_func is None:
                key = filename
            else:
                key = filename_to_key_func(filename)

            # 처리
            with open(file_full_path, 'r', encoding='UTF8') as input_file:
                data[key] = json.load(input_file)

                abs_filename = os.path.normpath(os.path.join(input_folder_path, each_file))
                filename_map[key] = abs_filename

    return data, filename_map


def get_first_geojson_point(node_features):
    '''
    해당 geojson에서 발견되는 첫번째 record의 첫번째 점의 위치를 origin으로 한다.
    '''
    # origin_x = node_features[0]['geometry']['coordinates']
    # origin_y = node_features[0]['geometry'].points[0][1]
    # origin_z = node_features[0]['geometry'].z[0]
    # origin = [origin_e, origin_n, origin_z]

    origin = node_features[0]['geometry']['coordinates']

    return origin