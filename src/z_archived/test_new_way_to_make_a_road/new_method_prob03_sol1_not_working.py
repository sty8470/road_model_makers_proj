"""
이번 문제는 사거리같은 구조이다.
앞선 문제에서 inner를 정의하는 것이 현재 상태서 의미가 없다고 생각되어서, 
이번에는 그냥 point가 쭉 있다고 생각하고 문제를 풀어버린다.

사거리가 포함된, 전체적으로 십자가 비슷한 모양을 띄고 있는 closed loop을 
한번에 넣어버리면 역시 mesh가 제대로 생성되지 않는다
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
    line1 = line1 + move(line1[-1], [1,  0,  0], 1)
    line1 = line1 + move(line1[-1], [1, -1,  0], 1)
    line1 = line1 + move(line1[-1], [0, -1,  0], 1)
    line1 = line1 + move(line1[-1], [1,  0,  0], 3)
    line1 = line1 + move(line1[-1], [0,  1,  0], 1)
    line1 = line1 + move(line1[-1], [1,  1,  0], 1)
    line1 = line1 + move(line1[-1], [1,  0,  0], 10)

    line2 = move(line1[-1], [0,  3,  0], 1)
    line2 = line2 + move(line2[-1], [-2, 0,  0], 5)
    line2 = line2 + move(line2[-1], [-1, 1,  0], 1)
    line2 = line2 + move(line2[-1], [ 0, 1,  0], 4)


    line3 = move(line2[-1], [-3, 0,  0], 1)
    line3 = line3 + move(line3[-1], [0, -2,  0], 2)
    line3 = line3 + move(line3[-1], [-1, -1,  0], 1)
    line3 = line3 + move(line3[-1], [-1, 0,  0], 1)


    # plt.figure()
    # debug_plot(line1)
    # debug_plot(line2)
    # debug_plot(line3)
    # plt.show()

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

    face1 = np.arange(len(vertices))
    face1 = face1.tolist()
    faces = [face1]

    road_obj = make_road(vertices, faces)
    file_io.write_stl_and_obj(road_obj, 'test_road_200207_AM0400')
    _plot_vtkPolyData(road_obj, 'Red')