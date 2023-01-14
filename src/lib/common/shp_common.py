import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))

import shapefile
import numpy as np
import platform


def get_first_shp_point(sf):
    '''
    해당 shape에서 발견되는 첫번째 record의 첫번째 점의 위치를 origin으로 한다.
    '''
    shapes = sf.shapes()
    origin_e = shapes[0].points[0][0]
    origin_n = shapes[0].points[0][1]
    origin_z = shapes[0].z[0]
    origin = [origin_e, origin_n, origin_z]
    return origin


def read_shp_files(input_path, encoding_ansi=False, filename_to_key_func=None):
    """
    input_folder_path 변수가
    - 파일 이름을 포함하고 있으면 >> #1a 가 실행
    - 폴더 이름이면              >> #1b 가 실행

    TODO(sjhan): list가 아니고, 그냥 파일 이름만 넘어오면, #1b가 실행되는 문제
    """

    # input_path가 리스트로 넘어오면 리스트로 사용하고, path 설정
    if type(input_path) == list:
        # ---------- Section #1a (begins) ----------
        file_list = []
        for f in input_path:
            file_list.append(os.path.basename(f))
        input_path = os.path.dirname(input_path[0])
        # ---------- Section #1a (ends) ----------
    else:
        # ---------- Section #1b (begins) ----------
        file_list = os.listdir(input_path)
        # ---------- Section #1b (ends) ----------

    data = {}
    filename_map = {}

    for each_file in file_list:
        # 디렉토리는 Skip
        if os.path.isdir(each_file):
            continue

        # DBF 파일인지 체크 => DBF 파일일 때 실행한다
        filename, file_extension = os.path.splitext(each_file)
        if file_extension != '.dbf':
            continue

        abs_filename = os.path.normpath(os.path.join(input_path, filename))

        if filename_to_key_func is None:
            key = filename
        else:
            key = filename_to_key_func(filename)

        if encoding_ansi:
            if platform.system() =='Darwin': # Mac 에서는 ANSI가 지원되지 않음
                raise BaseException('In Mac OS, reading shp files with ansi encoding is not supported.')
            else:
                data[key] = shapefile.Reader(abs_filename, encoding='ansi')
                # data[key] = shapefile.Reader(abs_filename, encoding='ms949')
                # NOTE(hjp): expand encoding support
                filename_map[key] = abs_filename

        else:    
            # 일반적으로는 shapefile Reader의 기본 지원 인코딩으로 읽으면 된다.
            # 한글로 기록되어 있는 데이터를 파싱할 필요가 없기 때문
            data[key] = shapefile.Reader(abs_filename)
            filename_map[key] = abs_filename
                
    return data, filename_map


    
