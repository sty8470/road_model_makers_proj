"""
test_auto_connect 보다 조금 더 다양한 문제를 시험할 수 있도록
시험용 코드 별도 작성
"""
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')

from shp_common import *
import shapefile
import csv

import numpy as np
import matplotlib.pyplot as plt

from lib_ngii_shp_ver2.shp_edit_funcs import UserInput, scr_zoom, create_mesh_creation_tool
from lib.mgeo.class_defs import *
from lib.mgeo.edit.funcs import edit_line

# from test_common_funcs import create_points_using_step


def _create_test_input(case, plot=True):
    """
    Case #1
    - line1 - line3 - line5 - line7
    - line0 - line2 - line4 - line6
    이렇게 2개의 선이 있는 케이스를 만들어보자

    Case #2 (intersection)
    line0,1|    | line2,3
    _______      _______
    _______      _______
    line4,5|    | line6,7
    
    Case #3 (test for vtkdelaunay)
            line0
    line3           line1
            line2
    
    Case #4 (smaller version of case3)
            line0
    line3           line1
            line2
    """

    if case == 1:
        # line0
        line0 = Line()
        edit_line.create_the_first_point(line0, [0,0,0]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line0,
            xyz_step_size=[1, 0.2, 0],
            step_num = 11)

        # line2
        line2 = Line()
        edit_line.create_the_first_point(line2, line0.points[-1]) # line0의 마지막 점과 같은 위치를 얻어온다
        edit_line.create_points_from_current_pos_using_step(
            line2,
            xyz_step_size=[0.5,0.15,0],
            step_num = 8)

        # line4
        line4 = Line()
        edit_line.create_the_first_point(line4, line2.points[-1]) # line2의 마지막 점과 같은 위치를 얻어온다
        edit_line.create_points_from_current_pos_using_step(
            line4,
            xyz_step_size=[0.5,0.4,0],
            step_num = 12)

        # line6
        line6 = Line()
        edit_line.create_the_first_point(line6, line4.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line6,
            xyz_step_size=[1,0.1,0],
            step_num = 10)

        # second line -----

        # line1
        line1 = Line()
        edit_line.create_the_first_point(line1, [0,2.5,0]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line1,
            xyz_step_size=[1, 0.2, 0],
            step_num = 11)

        # line3
        line3 = Line()
        edit_line.create_the_first_point(line3, line1.points[-1]) # line1의 마지막 점과 같은 위치를 얻어온다
        edit_line.create_points_from_current_pos_using_step(
            line3,
            xyz_step_size=[0.5,0.5,0],
            step_num = 8)

        # line5
        line5 = Line()
        edit_line.create_the_first_point(line5, line3.points[-1]) # line3의 마지막 점과 같은 위치를 얻어온다
        edit_line.create_points_from_current_pos_using_step(
            line5,
            xyz_step_size=[0.5,0.2,0],
            step_num = 12)


        # line7
        line7 = Line()
        edit_line.create_the_first_point(line7, line5.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line7,
            xyz_step_size=[1,0,0],
            step_num = 10)

    elif case == 2:
        # line0
        line0 = Line()
        edit_line.create_the_first_point(line0, [0,5,0]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line0,
            xyz_step_size=[0.5, 0, 0],
            step_num = 6)


        # line1
        line1 = Line()
        edit_line.create_the_first_point(line1, line0.points[-1]) # line0의 마지막 점과 같은 위치를 얻어온다
        edit_line.create_points_from_current_pos_using_step(
            line1,
            xyz_step_size=[0.1,0.5,0],
            step_num = 8)


        # line2
        line2 = Line()
        edit_line.create_the_first_point(line2, [10,10,0]) # 새로 시작
        edit_line.create_points_from_current_pos_using_step(
            line2,
            xyz_step_size=[0.1,-0.6,0],
            step_num = 7)


        # line3
        line3 = Line()
        edit_line.create_the_first_point(line3, line2.points[-1]) # line2 이어서
        edit_line.create_points_from_current_pos_using_step(
            line3,
            xyz_step_size=[0.5,0,0],
            step_num = 8)


        # line4
        line4 = Line()
        edit_line.create_the_first_point(line4, [15,3,0]) # 새로 시작
        edit_line.create_points_from_current_pos_using_step(
            line4,
            xyz_step_size=[-0.9, 0, 0],
            step_num = 6)


        # line5
        line5 = Line()
        edit_line.create_the_first_point(line5, line4.points[-1]) # line4의 마지막 점과 같은 위치를 얻어온다
        edit_line.create_points_from_current_pos_using_step(
            line5,
            xyz_step_size=[-0.1,-0.5,0],
            step_num = 5)


        # line6
        line6 = Line()
        edit_line.create_the_first_point(line6, [4,-1,0]) # 새로 시작
        edit_line.create_points_from_current_pos_using_step(
            line6,
            xyz_step_size=[-0.1,0.4,0],
            step_num = 9)


        # line7
        line7 = Line()
        edit_line.create_the_first_point(line7, line6.points[-1]) # line6 이어서
        edit_line.create_points_from_current_pos_using_step(
            line7,
            xyz_step_size=[-0.8,0.1,0],
            step_num = 4)

    elif case == 3:
        # line0
        line0 = Line()
        edit_line.create_the_first_point(line0, [-5,5,0]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line0,
            xyz_step_size=[1, 0, 0],
            step_num = 11)

        line1 = Line()
        edit_line.create_the_first_point(line1, line0.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line1,
            xyz_step_size=[0, -1, 0],
            step_num = 10)

        line2 = Line()
        edit_line.create_the_first_point(line2, line1.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line2,
            xyz_step_size=[-1, 0, 0],
            step_num = 11)

        line3 = Line()
        edit_line.create_the_first_point(line3, line2.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line3,
            xyz_step_size=[0, 1, 0],
            step_num = 10)

        # line4
        line4 = Line()
        edit_line.create_the_first_point(line4, [-11, 10, 2]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line4,
            xyz_step_size=[2, 0, 0],
            step_num = 11)

        line5 = Line()
        edit_line.create_the_first_point(line5, line4.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line5,
            xyz_step_size=[0, -2, 0],
            step_num = 10)

        line6 = Line()
        edit_line.create_the_first_point(line6, line5.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line6,
            xyz_step_size=[-2, 0, 0],
            step_num = 11)

        line7 = Line()
        edit_line.create_the_first_point(line7, line6.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line7,
            xyz_step_size=[0, 2, 0],
            step_num = 10)

    elif case == 4:
        # line0
        line0 = Line()
        edit_line.create_the_first_point(line0, [-5,5,0]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line0, 
            xyz_step_size=[1, 0, 1*random.random()],
            step_num = 3)

        line1 = Line()
        edit_line.create_the_first_point(line1, line0.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line1,
            xyz_step_size=[0, -1, 0],
            step_num = 3)

        line2 = Line()
        edit_line.create_the_first_point(line2, line1.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line2,
            xyz_step_size=[-1, 0, -1*random.random()],
            step_num = 3)

        line3 = Line()
        edit_line.create_the_first_point(line3, line2.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line3,
            xyz_step_size=[0, 1, 0],
            step_num = 3)

        # line4
        line4 = Line()
        edit_line.create_the_first_point(line4, [-6, 6, 2]) # 첫번째 점 설정
        edit_line.create_points_from_current_pos_using_step(
            line4,
            xyz_step_size=[1, 0, 0],
            step_num = 5)

        line5 = Line()
        edit_line.create_the_first_point(line5, line4.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line5,
            xyz_step_size=[0, -1, 0],
            step_num = 5)

        line6 = Line()
        edit_line.create_the_first_point(line6, line5.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line6,
            xyz_step_size=[-1, 0, 0],
            step_num = 5)

        line7 = Line()
        edit_line.create_the_first_point(line7, line6.points[-1])
        edit_line.create_points_from_current_pos_using_step(
            line7,
            xyz_step_size=[0, 1, 0],
            step_num = 5)


    line_set_obj = LineSet()
    line_set_obj.append_line(line0, create_new_key=True)
    line_set_obj.append_line(line1, create_new_key=True)
    line_set_obj.append_line(line2, create_new_key=True)
    line_set_obj.append_line(line3, create_new_key=True)
    line_set_obj.append_line(line4, create_new_key=True)
    line_set_obj.append_line(line5, create_new_key=True)
    line_set_obj.append_line(line6, create_new_key=True)
    line_set_obj.append_line(line7, create_new_key=True)

    if plot:
        line_set_obj.draw_plot()

    return line_set_obj
    

def main():
    print('[INFO] Program Start')
    
    output_path = '../../saved/'
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)

    # case = input('Choose test case: 1) straight road / 2) intersection: ')
    # case = int(case)
    case = 2

    
    # Disable a few keyboard shotcuts
    # NOTE: 다른 keymap 찾으려면 다음을 참고:
    # https://matplotlib.org/tutorials/introductory/customizing.html
    plt.rcParams['keymap.home'] = ''
    plt.rcParams['keymap.back'] = ''
    plt.rcParams['keymap.forward'] = ''
    plt.rcParams['keymap.pan'] = ''
    plt.rcParams['keymap.save'] = 'ctrl+s' # 원래 s, ctrl+s로 동작하는데 s만 사용하도록
    plt.rcParams['keymap.quit'] = ''
    plt.rcParams['keymap.quit_all'] = ''
    plt.rcParams['keymap.yscale'] = ''
    plt.rcParams['keymap.xscale'] = ''
    plt.rcParams['keymap.copy'] = 'ctrl+c' # alt+c 해제


    # Figure 생성
    fig_lane = plt.figure(1) # 차선 가장 바깥 선을 도시하는 figure는 1번으로 설정

    """ 사용자 입력에 따른 콜백을 처리하기 위한 클래스 인스턴스 """
    ui = create_mesh_creation_tool()
    ui.pass_down(output_path)


    """ 테스트용 line_set_obj에서 시작하는 경우 """
    line_set_obj = _create_test_input(case, plot=False)
    node_set_obj = line_set_obj.create_node_set_for_all_lines()
    
    
    """ 이미 만들어둔 node_set, line_set 파일이 있어서, 빈 상태로 시작하는 경우 """
    # line_set_obj = LineSet()
    # node_set_obj = NodeSet()
    ui.set_geometry_obj(line_set_obj, node_set_obj)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)


    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    fig_lane.set_size_inches(12,12)
    fig_lane.axes[0].axis('equal')



    # 아래를 호출하면 다 지워짐
    # line_set_obj.erase_plot()
    # node_set_obj.erase_plot()

    plt.show()    
 
    print('[INFO] Ended successfully.')


if __name__ == u'__main__':
    main()