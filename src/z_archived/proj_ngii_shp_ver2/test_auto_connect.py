"""
간단한 문제를 만들어, 아주 가깝게 위치한 line들을 자동으로 연결해주는 로직을 검증한다
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

from lib_ngii_shp_ver2.shp_edit_funcs import UserInput, scr_zoom
from lib_ngii_shp_ver2.class_defs_for_shp_edit import LineSet, Line, Node
from lib.mgeo.edit.funcs import edit_line

from test_common_funcs import create_points_using_step


def _create_test_input():
    """
    Case #1
    - line1 - line3 - line5
    - line0 - line2 - line4
    이렇게 2개의 선이 있는 케이스를 만들어보자
    """

    # line0
    line0 = Line()
    edit_line.create_the_first_point(line0, [0,0,0]) # 첫번째 점 설정
    edit_line.create_points_from_current_pos_using_step(
        line0,
        xyz_step_size=[2, 0, 0],
        step_num=5)
    plt.plot(line0.points[:,0], line0.points[:,1],
        markersize='3',
        marker='o')

    # line2
    line2 = Line()
    edit_line.create_the_first_point(line2, line0.points[-1]) # line0의 마지막 점과 같은 위치를 얻어온다
    edit_line.create_points_from_current_pos_using_step(
        line2,
        xyz_step_size=[1,0.2,0],
        step_num = 8)
    plt.plot(line2.points[:,0], line2.points[:,1],
        markersize='3',
        marker='o')

    # line4
    line4 = Line()
    edit_line.create_the_first_point(line4, line2.points[-1]) # line2의 마지막 점과 같은 위치를 얻어온다
    edit_line.create_points_from_current_pos_using_step(
        line4,
        xyz_step_size=[1,0,0],
        step_num = 12)
    plt.plot(line4.points[:,0], line4.points[:,1],
        markersize='3',
        marker='o')


    # line1
    line1 = Line()
    edit_line.create_the_first_point(line1, [0,2.5,0]) # 첫번째 점 설정
    edit_line.create_points_from_current_pos_using_step(
        line1,
        xyz_step_size=[1.5, 0, 0],
        step_num=5)
    plt.plot(line1.points[:,0], line1.points[:,1],
        markersize='3',
        marker='o')

    # line3
    line3 = Line()
    edit_line.create_the_first_point(line3, line1.points[-1]) # line1의 마지막 점과 같은 위치를 얻어온다
    edit_line.create_points_from_current_pos_using_step(
        line3,
        xyz_step_size=[1,0.15,0],
        step_num = 10)
    plt.plot(line3.points[:,0], line3.points[:,1],
        markersize='3',
        marker='o')

    # line5
    line5 = Line()
    edit_line.create_the_first_point(line5, line3.points[-1]) # line3의 마지막 점과 같은 위치를 얻어온다
    edit_line.create_points_from_current_pos_using_step(
        line5,
        xyz_step_size=[1,0,0],
        step_num = 12)
    plt.plot(line5.points[:,0], line5.points[:,1],
        markersize='3',
        marker='o')

    line_set_obj = LineSet()
    line_set_obj.append_line(line0, create_new_key=True)
    line_set_obj.append_line(line1, create_new_key=True)
    line_set_obj.append_line(line2, create_new_key=True)
    line_set_obj.append_line(line3, create_new_key=True)
    line_set_obj.append_line(line4, create_new_key=True)
    line_set_obj.append_line(line5, create_new_key=True)
    return line_set_obj

    

def main():
    print('[INFO] Starts')

    # Figure 생성
    fig_lane = plt.figure(1) # 차선 가장 바깥 선을 도시하는 figure는 1번으로 설정

    """ 사용자 입력에 따른 콜백을 처리하기 위한 클래스 인스턴스 """
    ui = UserInput()

    """ 테스트용 line_set_obj를 생성한다 """
    line_set_obj = _create_test_input()

    ui.set_geometry_obj(line_set_obj)

    # 테스트해야 하는 함수 (구현 방식1)
    node_set_obj = line_set_obj.create_node_set_for_all_lines()

    # 테스트해야 하는 함수 (구현 방식2: 기존 구현)
    # node_set_obj = ui.node_create()

    for node in node_set_obj.nodes:
        plt.plot(node.point[0], node.point[1],
            markersize=5,
            marker='D',
            color='b')
        plt.gca().text(node.point[0], node.point[1]+0.1,
            node.idx,
            fontsize=12)



    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    plt.show()    

    print('[INFO] Ended successfully.')


if __name__ == u'__main__':
    main()