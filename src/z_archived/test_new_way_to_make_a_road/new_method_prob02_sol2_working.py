"""
new_method_case01_separate_triangle_plain.py에서 다루었던
문제를 심화하여, new_method_case01_refactored에서 구현한 함수가 
point가 더 많은 문제에 적용 가능한지 살펴본다. 

Case #01 문제는 다음과 같았다. 
- 바깥 외곽선     : 4개의 점
- 안쪽 외곽선 1개 : 4개의 점 

Case #02 문제는 다음과 같다.
도로의 Geometry는 같은데, point의 resolution을 늘렸다
- 바깥 외곽선     : 14개의 점
- 안쪽 외곽선 1개 : 10개의 점 

앞서 문제가 안 풀렸는데, (new_method_prob02_sol1_not_working.py)
이 문제를 그냥 수동으로 4개의 면을 나눌 수 있다고 가정하고 문제를 풀었다.
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import vtk
import numpy as np
from lib.common import display, file_io, vtk_utils

from ex_vtk_road3_01_all_have_thickness import _get_user_input, make_road, _plot_vtkPolyData
from new_method_prob01_refactored import calc_face_idx_list_to_make_triangle_meshes

if __name__ == '__main__':
    
    outer, inner = _get_user_input(resolution_up=True)  

    # 그냥 이렇게 4개의 면으로 나누어 풀면 (4개의 면으로 나눠주는 작업은 수동으로 해야한다)
    # 간단하게 풀린다
    def link_two_lines_point_idx(outer_idx, inner_idx):
        inner_idx.reverse()
        return outer_idx + inner_idx

    vertices = outer + inner
    face1 = link_two_lines_point_idx([0,1,2,3], [14,15,16])
    face2 = link_two_lines_point_idx([3,4,5,6,7], [16,17,18,19])
    face3 = link_two_lines_point_idx([7,8,9,10], [19,20,21])
    face4 = link_two_lines_point_idx([10, 11,12,13,0], [21,22,23,14])
    faces = [face1, face2, face3, face4]

    print('len(outer): ', len(outer))
    print('len(inner): ', len(inner))

    for i in range(len(faces)):
        print('face[{}] = '.format(i), faces[i])

    road_obj = make_road(vertices, faces)
    file_io.write_stl_and_obj(road_obj, 'test_road_200207_AM0300')
    _plot_vtkPolyData(road_obj, 'Red')