"""
이번 문제는 사거리같은 구조이다.
앞선 문제에서 inner를 정의하는 것이 현재 상태서 의미가 없다고 생각되어서, 
이번에는 그냥 point가 쭉 있다고 생각하고 문제를 풀어버린다.

사거리가 포함된, 전체적으로 십자가 비슷한 모양을 띄고 있는 closed loop을 
한번에 넣어버리면 역시 mesh가 제대로 생성되지 않는다
(not_working 쪽)

이를, prob2 sol2 에서 했던 것처럼, 사람이 직접 면을 나누어준다 가정하여
면을 분리해주어 해결하였다

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
from new_method_prob03_sol1_not_working import create_input_data

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


if __name__ == '__main__':
    line1, line2, line3 = create_input_data()

    plt.figure()
    debug_plot(line1)
    debug_plot(line2)
    debug_plot(line3)
    plt.show()

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
    file_io.write_stl_and_obj(road_obj, 'test_road_200207_AM0430')
    _plot_vtkPolyData(road_obj, 'Red')