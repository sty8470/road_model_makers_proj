"""
inner, outer 점을 이용하여, 인접한 삼각형을 만들면서 도로를 생성한다
가장 간단하게 4개의 점으로 구성된, 
1) 바깥 사각형
2) 안쪽 사각형
총 8개의 점이 있는 경우에 대해 문제를 푼다.
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

if __name__ == '__main__':
    
    outer_upper, inner_upper = _get_user_input(resolution_up=False)  

    print('len(outer_upper): ', len(outer_upper))
    print('len(inner_upper): ', len(inner_upper))

    vertices = outer_upper + inner_upper
    print('vertices: ', vertices)

    idx_inner_start = len(outer_upper)
    # faces = [
    #     [0, 1, 4],
    #     [4, 1, 5],
    #     [5, 1, 2],
    #     [5, 2, 6],
    #     [6, 2, 3],
    #     [6, 3, 7],
    #     [7, 3, 0],
    #     [7, 0, 4]
    # ]

    start_of_out = 0
    end_of_out = 4

    start_of_in = 4
    end_of_in = 8

    out_ptr = start_of_out
    in_ptr = start_of_in

    faces_out = []
    for i in range(len(vertices)):

        if i % 2 == 0 :
            # 바깥쪽을 전진시켜서 삼각형을 만든다
            next_out = out_ptr + 1
            if next_out == end_of_out:
                next_out = start_of_out
            
            face = [out_ptr, next_out, in_ptr]
            out_ptr = next_out

        else:
            # 안쪽을 전진시켜서 삼각형을 만든다
            next_in = in_ptr + 1
            if next_in == end_of_in:
                next_in = start_of_in

            face = [in_ptr, next_in, out_ptr]
            face.reverse() # 안쪽을 전진시킬때는 뒤집어야한다 (그래야 모든 면의 normal이 같은 방향이다)
            in_ptr = in_ptr + 1

        faces_out.append(face)

    faces = faces_out
    road_obj = make_road(vertices, faces)
    file_io.write_stl_and_obj(road_obj, 'test_road_200207_AM0035')
    _plot_vtkPolyData(road_obj, 'Red')