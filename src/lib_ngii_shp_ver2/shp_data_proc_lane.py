import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')

from ngii_shp_ver2_utils import surfline_kind_code_to_str, surfline_type_code_to_str

import numpy as np
import math

# from class_defs_for_shp_edit import LineSet, Line
from lib.mgeo.class_defs import LineSet, Line


def proc_lane(sf, origin):
    '''
    Lane은 차선, 도로 경계 등 다양한 정보가 섞여있고, DBF Record를 통해
    어떤 데이터인지 확인을 우선 해야 한다.
    '''
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    line_set_obj = LineSet()

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')

    # 각 line의 양끝점을 모은 endpoints array 선언
    # endpoints = np.zeros((1, 5))
    # j = 0

    for i in range(len(shapes)):
        dbf_rec = records[i]
        shp_rec = shapes[i]

        # kind_val == 'Border' >> our interest
        kind_val = surfline_kind_code_to_str(dbf_rec['Kind'], lane_prefix=False)
        type_val = surfline_type_code_to_str(dbf_rec['Type'])

        if len(shp_rec.points) != len(shp_rec.z):
            print('[WARN] Skipping data at i={}: len(shp_rec.points)={}, where as len(shp_rec.z)={}'.format(
                i, len(shp_rec.points), len(shp_rec.z)))
            continue

        if len(shp_rec.points) == 0:
            print('[WARN] Skipping data at i={}: len(shp_rec.points)=0'.format(i))
            continue
        
        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin
             

        # 우선은 이 데이터를 가지고만 만들어본다
        if kind_val == 'Center':
            # points를 Line으로 만든다
            new_line = Line(shp_rec.points)
            line_set_obj.append_line(new_line, create_new_key=True)

    return line_set_obj


