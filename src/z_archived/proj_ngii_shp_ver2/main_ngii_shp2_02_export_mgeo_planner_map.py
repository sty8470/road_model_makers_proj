#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로
sys.path.append(current_path + '/../lib/common') # 프로젝트 Root 경로

from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt

from shp_common import *

from lib_ngii_shp_ver2.shp_edit_funcs import *
from lib.mgeo.class_defs import *
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save
import lib.mgeo.utils.error_fix as mgeo_error_fix
import lib.mgeo.utils.lane_change_link_creation as mgeo_lane_ch_link_gen

import ngii_shp_ver2_importer as importer


"""
국토지리정보원의 MGeo 데이터 중 다음을 MGeo로 저장하여
시뮬레이터에서 사용 가능하도록 한다.
이 때 각 데이터에 대해서 다음의 과정을 수행한다.

1) Node
   -> 특정 구간의 데이터만 남기고 잘라낸다
   -> 그대로 MGeo로 출력


2) Link
   -> 특정 구간의 데이터만 남기고 잘라낸다
   -> 차선 변경 링크를 생성
   -> 내부 point를 일정한 0.5m 간격으로 변경
   

3) Traffic Light
   [현재]
   3.a) Traffic Light 배치 csv 파일
   
   [향후]
   3.b) Traffic Light 배치 및 초기화용 json 파일
   >> 개발자 또는 사용자가 배치나 초기화용 값을 변경하면 여기에 저장된다.
   >> 개발자가 수정한 사항은 Editor에서 로드할 수 있고,
   >> 사용자가 수정한 값은 Play 중 로드할 수 있다. 


4) Traffic Sign
   [현재]
   4.a) Traffic Light 배치 csv 파일

   [향후]
   4.b) Traffic Sign 배치용 json 파일
   >> 개발자 또는 사용자가 배치를 변경하면 여기에 저장된다. 
   >> 개발자가 수정한 사항은 Editor에서 로드할 수 있고,
   >> 사용자가 수정한 값은 Play 중 로드할 수 있다. 
"""


def main(dir_selection_using_gui):
    if dir_selection_using_gui:
        """INPUT/OUTPUT 경로를 GUI로 설정한다"""
        # 초기 경로
        input_init_dir = os.path.join(current_path, '../../rsc/map_data/')

        # 맵 로드할 경로
        input_path = filedialog.askdirectory(
            initialdir = input_init_dir,
            title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능   

        # 출력 초기 경로
        output_init_dir = os.path.join(current_path, '../../saved/csv/') 


        # csv 저장할 경로
        output_path = filedialog.askdirectory(
            initialdir = output_init_dir,
            title = 'Save files to') # defaultextension = 'json') 과 같은거 사용 가능
    else:
        """NGII 데이터 import하기"""
        input_path = '../../rsc/map_data/ngii_shp_ver2_KCity/SEC01_UTM52N_ElipsoidHeight'
        output_path = '../../saved/mgeo_kcity_from_ngii_shp_ver2'

        input_path = os.path.join(current_path, input_path)
        input_path = os.path.normpath(input_path)   

        output_path = os.path.join(current_path, output_path)
        output_path = os.path.normpath(output_path)

    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    
    # Get Map Information
    map_info = read_shp_files(input_path)
    if map_info is None:
        raise BaseException('[ERROR] There is no input data (input_path might be incorrect)')


    """
    Origin이 되는 Point를 찾는다
    Origin은 현재는 A1_NODE에서 검색되는 첫번째 포인트로한다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)

    
    # 이제 여기서 NODE, LINK 파일을 읽어준다.
    shp_node = map_info['A1_NODE']
    shp_link = map_info['A2_LINK']


    # Node, 일반 Link, 차선 변경 Link 생성하는 코드
    node_set, junction_set = importer.create_node_set(shp_node, origin)
    link_set = importer.create_link_set(shp_link, origin, node_set)
    # lane_ch_link_set = importer.create_lane_change_link_set(shp_link, link_set) 

    # 일반 Link, 차선 변경 Link를 합쳐서 total_line_set 생성
    # link_set = LineSet.merge_two_sets(link_set, lane_ch_link_set)

    """ 차선 변경 링크 만들기 """
    create_link_ch_set = True
    auto_depth = True 
    if create_link_ch_set:
        # 차선 변경 link_set 만들기
        # 차선 변경 링크를 생성하기 전에 위에서 노드-링크에 오류가 없음이 확인되어야 한다
        if auto_depth:
            lane_ch_link_set = mgeo_lane_ch_link_gen.create_lane_change_link_auto_depth_using_length(
                link_set, method=1, min_length_for_lane_change=20)
        else:
            lane_ch_link_set = mgeo_lane_ch_link_gen.create_lane_change_link(
                link_set, max_lane_change=5)

        # 기존 링크셋과 차선 변경 링크셋을 합쳐준다
        link_set = LineSet.merge_two_sets(
            link_set, lane_ch_link_set)


    """ 모든 링크에 대한 cost 계산 """
    for var in link_set.lines:
        if isinstance(link_set.lines, dict):
            link = link_set.lines[var]
        else:
            link = var
        link.calculate_cost()


    """ 모든 링크의 display type 변경 """
    for var in link_set.lines:
        if isinstance(link_set.lines, dict):
            link = link_set.lines[var]
        else:
            link = var

        # 차선 변경 여부만 구분하도록
        if link.is_it_for_lane_change():
            link.set_vis_mode_manual_appearance(1, 'b')
        else:
            link.set_vis_mode_manual_appearance(1, 'k')


    # """ TEMP: 모든 차선변경링크가 아닌 일반 링크를 일정한 간격으로 변경해준다 """
    # for idx, link in link_set.lines.items():
    #     if not link.is_it_for_lane_change():
    #         step_len = 0.5
    #         link.fill_in_points_evenly(step_len)


    """ 뷰어 만들어주기 """
    fig_lane = plt.figure()
    ui = create_link_editor()
    ui.pass_down(output_path)
    ui.set_geometry_obj(link_set, node_set)

    xlim = [390, 750]
    ylim = [930, 1900]
    ui.set_absolute_bbox_for_plot(xlim, ylim)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)


    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    # 그려서 확인해보기
    plt.show()

    print('[INFO] Ended Successfully.')

    print('END')


if __name__ == u'__main__':
    # [USER OPTION]
    dir_selection_using_gui = False

    main(dir_selection_using_gui)