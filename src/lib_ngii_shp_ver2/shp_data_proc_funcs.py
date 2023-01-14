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

from lib.mgeo.class_defs import *


def proc_all_lines(sf, origin):
    return proc_c3_vehicle_protection_safety(sf, origin)


def proc_c3_vehicle_protection_safety(sf, origin):
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

    for i in range(len(shapes)):
        shp_rec = shapes[i]

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
             
        """
        NOTE: 현재는 C3_VEHICLEPROTECTIONSAFETY 모든 데이터를 사용한다
        만일 모든 데이터를 사용하지 않을 예정이면 DBF 데이터를 참고하여 적합한 데이터만 사용해야 한다
        """

        # points를 Line으로 만든다
        new_line = Line(shp_rec.points)
        line_set_obj.append_line(new_line, create_new_key=True)

    return line_set_obj


