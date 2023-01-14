"""
앞선 문제의 사거리에, 높이를 추가하였다.


"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import vtk
import numpy as np 
import matplotlib.pyplot as plt 
from lib.common import display, file_io, vtk_utils

from ex_vtk_road3_01_all_have_thickness import _get_user_input, make_road, _plot_vtkPolyData
    

def move_xyz(current_pos, x_step_size, y_step_size, z_step_size, step_num):
    return move(current_pos, [x_step_size, y_step_size, z_step_size], step_num)


def move(current_pos, xyz_step_size, step_num):
    ret = list()
    next_pos = current_pos
    for i in range(step_num):
        next_pos = [next_pos[0] + xyz_step_size[0],
            next_pos[1] + xyz_step_size[1],
            next_pos[2] + xyz_step_size[2]]
        ret.append(next_pos)
    return ret


def debug_plot(line1):
    line1 = np.array(line1)
    x = line1[:,0]
    y = line1[:,1]
    ax = plt.plot(x,y,'b.')
    plt.axes().set_aspect('equal', 'datalim')


def create_input_data():
    """
    3개의 라인으로 구성된 데이터이다.
    """
    line1 = [[0,0,0]]
    line1 = line1 + move(line1[-1], [1,  0,   0], 1)
    line1 = line1 + move(line1[-1], [1, -1,  -0.20], 1) # 사거리에서부터 내리막길 (우회전할때)
    line1 = line1 + move(line1[-1], [0, -1,  -0.40], 1) # 내리막길
    line1 = line1 + move(line1[-1], [1,  0,   0.0], 3)
    line1 = line1 + move(line1[-1], [0,  1,   0.36], 1) # 다시 사거리로 진입하면서 오르막길
    line1 = line1 + move(line1[-1], [1,  1,   0.24], 1) # 사거리 내에서도 오르막길 (우회전시)
    line1 = line1 + move(line1[-1], [1,  0,   0.08], 10) # 오르막길

    # Line1의 끝점을 기준으로 [0, 3, 0] 진행한 위치에서 시작
    line2 = move(line1[-1], [0,  3,  0], 1)
    line2 = line2 + move(line2[-1], [-2, 0,  -0.16], 5) # 내리막길
    line2 = line2 + move(line2[-1], [-1, 1,   0.28], 1) # 우회전하는 구간 바로 다시 오르막길
    line2 = line2 + move(line2[-1], [ 0, 1,   0.48], 4) # 오르막길

    # Line2의 끝점을 기준으로 [-3, 0, 0] 진행한 위치에서 시작
    line3 = move(line2[-1], [-3, 0,  0], 1)
    line3 = line3 + move(line3[-1], [0,  -2,  -0.96], 2) # 내리막길
    line3 = line3 + move(line3[-1], [-1, -1,  -0.36], 1) # 우회전하는 구간 내리막길 (아까는 0.28 내려왔는데, 지금은 0.36 내려온다)
    line3 = line3 + move(line3[-1], [-1,  0,   0.08], 1) # 앞서 0.36 내려왔던 것 만큼 다시 0.08 올라가서 회복한다


    plt.figure()
    debug_plot(line1)
    debug_plot(line2)
    debug_plot(line3)
    plt.show()

    return line1, line2, line3


if __name__ == '__main__':
    line1, line2, line3 = create_input_data()

    # plt.figure()
    # debug_plot(line1)
    # debug_plot(line2)
    # debug_plot(line3)
    # plt.show()

    print('len(line1):', len(line1))
    print('len(line2):', len(line2))
    print('len(line3):', len(line3))

    # 우선은 전체를 하나의 그냥 큰 면으로 만드는 걸 시도해본다
    vertices = line1 + line2 + line3

    face1 = [0, 1, 33, 34]
    face2 = [1, 2, 7, 8, 24, 25, 32, 33]
    face3 = [2, 3, 4, 5, 6, 7]
    face4 = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    face5 = [25, 26, 27, 28, 29, 30, 31, 32]
    faces = [face1, face2, face3, face4, face5]

    road_obj = make_road(vertices, faces)
    file_io.write_stl_and_obj(road_obj, 'road_prob4_sol1_not_working')
    _plot_vtkPolyData(road_obj, 'Red')