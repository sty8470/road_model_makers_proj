"""
new_method_case01_separate_triangle_plain.py 코드의 리팩토링 버전이다.

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


def calc_face_idx_list_to_make_triangle_meshes(outer, inner):
    '''
    가정:
        1) outer와 inner의 리스트는 CCW로 이미 정렬된 상태이다.
        2) 처음 선택한 index가 [0, 1, 4]가 되는데,
           이걸로 만든 mesh가 inner에 의해 정의되는 안쪽 공간을 침범하지 않는다
           이는 처음에 선택한 index 0, 4에 선택된 point의 위치가 적절했기 때문.
    '''

    vertices = outer + inner
    print('vertices: ', vertices)

    start_of_out = 0
    end_of_out = start_of_out + len(outer)

    start_of_in = len(outer)
    end_of_in = start_of_in + len(inner)

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

    return vertices, faces_out

if __name__ == '__main__':
    
    outer, inner = _get_user_input(resolution_up=False)  

    print('len(outer): ', len(outer))
    print('len(inner): ', len(inner))

    vertices, faces = calc_face_idx_list_to_make_triangle_meshes(outer, inner)

    road_obj = make_road(vertices, faces)
    file_io.write_stl_and_obj(road_obj, 'test_road_200207_AM0050')
    _plot_vtkPolyData(road_obj, 'Red')