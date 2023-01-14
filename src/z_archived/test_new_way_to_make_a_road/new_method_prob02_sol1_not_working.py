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

이 코드는 실패한 코드로, 문제가 왜 안 풀리는지에 대해 기술하고 있다.
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
    
    """
    혹시라도 _get_user_input이 나중에 수정되어 제대로 문제가 재현되지 않는다면 아래 코드를 이용할 것
    """
    # outer = [[0, 0, 0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0], [30, 0, 0], [30.0, 10.0, 0.0], [30.0, 20.0, 0.0], [30.0, 30.0, 0.0], [30, 35, 0], [20.0, 35.0, 0.0], [10.0, 35.0, 0.0], [0, 35, 0], [0.0, 25.0, 0.0], [0.0, 15.0, 0.0], [0.0, 5.0, 0.0], [0, 0, 0]]
    # inner = [[10, 10, 0], [15.0, 10.0, 0.0], [20, 10, 0], [20.0, 15.0, 0.0], [20.0, 20.0, 0.0], [20, 25, 0], [15.0, 25.0, 0.0], [10, 25, 0], [10.0, 20.0, 0.0], [10.0, 15.0, 0.0], [10, 10, 0]]
    # outer, inner = _get_user_input(resolution_up=True)  

    print('len(outer): ', len(outer))
    print('len(inner): ', len(inner))

    # 기존의 코드 이걸로 풀면 안 풀린다.
    vertices, faces = calc_face_idx_list_to_make_triangle_meshes(outer, inner)
    
    # 디버깅용
    for i in range(len(faces)):
        print('face[{}] = '.format(i), faces[i])

    """
    [문제 분석]

    디버깅용으로 출력해보는 것.
    하나씩 point를 따라가다보면, face[15] =  [8, 22, 21] 이 부분부터, inner rim으로 정의된 영역을 넘어간다
    사실, [0,1,2,3], [14,15,16] 라인으로 만들어지는 면 다음부터, 이 방식에 문제가 있음을 알 수 있는데
    face[5] =  [3, 17, 16] 이 면이 만들어진다. 이는 calc_face_idx_list_to_make_triangle_meshes
    함수가 outer line을 하나씩 proceed 시키고, inner line엣서 proceed 시키는데
    
    [0,1,2,3], [14,15,16] 로 만들어지는 면을 첫번째라고 한다면, 
    outer line은 4개의 점으로 구성되고
    inner line은 3개의 점으로 구성된다.
    따라서, 이 그 다음에 자연스럽게 inner line을 proceed 시키면서  face[5] =  [3, 17, 16] 면을 만들게 된다.
    
    하지만 생각해보면, point의 geometry를 살펴보면, 이 부분은
    [3,4,5,6,7], [16,17,18,19] 점들로 구성되는 면인데,
    inner line을 proceed 시킬게 아니라, outer line을 한번 더 proceed 시켜서
    [3,4,16] 면이 만들어져야했다.

    이런식으로 outer line 대비 inner line이 point 수가 적은데 
    계속 outer line 1번, inner line 1번으로 proceed 시키니까
    나중에는 inner line에서 proceed 시킬 것이 없기도 하고, 
    geometry를 실제 살펴보면 적합하지 않은 
    면이 만들어지게 되는 것이다. 
    """

    road_obj = make_road(vertices, faces)
    file_io.write_stl_and_obj(road_obj, 'test_road_200207_AM0300')
    _plot_vtkPolyData(road_obj, 'Red')