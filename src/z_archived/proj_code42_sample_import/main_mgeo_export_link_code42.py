#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # 프로젝트 Root 경로

from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt

from lib_ngii_shp_ver2.shp_edit_funcs import *
from lib.mgeo.class_defs import *
from lib.mgeo.utils import utils
from lib.mgeo.edit.funcs import edit_line
import lib.mgeo.save_load.mgeo_load as mgeo_load
import lib.mgeo.save_load.mgeo_save as mgeo_save
import lib.mgeo.utils.error_fix as mgeo_error_fix
import lib.mgeo.utils.lane_change_link_creation as mgeo_lane_ch_link_gen

from code42_geojson import * 


def convert_code42_geojson_to_mgeo_node_link_set():
    '''
    CODE42의 GeoJSON 데이터에서 mgeo Node & Link를 생성하고 저장한다
    '''
    input_path = '../../rsc/map_data/geojson_Code42_Sample/toGwacheonSample'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    init_dir = '../../saved/links/CODE42_과천'
    init_dir = os.path.join(current_path, init_dir)
    init_dir = os.path.normpath(init_dir)  

    # # Link Save할 경로
    # output_path = filedialog.askdirectory(
    #     initialdir = init_dir,
    #     title = 'Select a directory to save nodes & links to from')
    
    print('[INFO] input  path:', input_path)
    # print('[INFO] output path:', output_path)


    """ 파일 읽어와서 기본 node, link set 만들기 """
    map_info = read_geojson_files(input_path)
    
    origin = get_origin(map_info)
    print('[INFO] Origin Set as: ', origin)

    # node_set, link_set 만들기
    node_set, link_set = create_node_set_and_link_set(map_info, origin)


    """ 에러 체크하고 수정하기 """
    # 에러 체크 #1 (수정은 안 함. raise Exception)
    # node와 연결된 링크 중, link_set에 포함되지 않은 link가 있는지 확인
    mgeo_error_fix.check_for_node_connected_link_not_included_in_the_link_set(
        node_set, link_set)
        
    # 에러 체크 #2 (자동 수정)
    # 겹치는 노드 있는지 확인 & 수리 (대신 붙일 노드가 있으면 연결, 없으면 생성)
    overlapped_node_sets = mgeo_error_fix.search_overlapped_node(node_set, 0.1)
    nodes_of_no_use = mgeo_error_fix.repair_overlapped_node(overlapped_node_sets)
    mgeo_error_fix.delete_nodes_from_node_set(node_set, nodes_of_no_use)

    # NOTE: 단, 이걸로 완전히 해결되지 않는 문제들이 있다.
    # 따라서, 차선 변경 링크를 생성하지 않은 상태에서 simplify를 적용하여
    # 링크가 깨끗하게 만들어지는지 확인해야 한다

    
    """ 차선 변경 링크 만들기 """
    create_link_ch_set = False
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


    """ TEMP: 모든 차선변경링크가 아닌 일반 링크를 일정한 간격으로 변경해준다 """
    for idx, link in link_set.lines.items():
        if not link.is_it_for_lane_change():
            step_len = 0.5
            edit_line.fill_in_points_evenly(link, step_len)


    """ TEMP: Dijkstra 해결을 위해서 list type으로 변경한다 """
    convert_to_list = False
    if convert_to_list:
        node_set = mgeo_utils.node_set_dict_to_list(node_set)
        link_set = mgeo_utils.line_set_dict_to_list(link_set)


    """ MGeo 파일로 저장하기 """
    # 이를 바탕으로 mgeo_planner_map을 생성
    mgeo_planner_map = MGeo(node_set, link_set)
    mgeo_planner_map.set_origin(origin)

    save_path = filedialog.askdirectory(
        initialdir = init_dir, 
        title = 'Save in the folder below') # defaultextension = 'json') 과 같은거 사용 가능    
    
    mgeo_planner_map.to_json(save_path)


    # link_set display 속성 변경
    # link_set.set_vis_mode_all_different_color(True)


    """ 뷰어 만들어주기 """
    fig = plt.figure()

    # Link Editor 생성
    ui = create_link_editor() 
    ui.pass_down(init_dir)
    ui.set_geometry_obj(link_set, node_set)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)

    # 사용자 입력에 따른 콜백 등록
    cid_click = fig.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)
    fig.set_size_inches(9,9)

    plt.show()
    print('END')


def start_from_empty_link():
    '''
    CODE42의 GeoJSON 데이터에서 mgeo Node & Link를 생성하고 저장한다
    '''
    input_path = '../../rsc/map_data/geojson_Code42_Sample/toGwacheonSample'
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    init_dir = '../../saved/links/CODE42_과천'
    init_dir = os.path.join(current_path, init_dir)
    init_dir = os.path.normpath(init_dir)  

    link_set = LineSet()
    node_set = NodeSet()

    
    """ 뷰어 만들어주기 """
    fig = plt.figure()

    # Link Editor 생성
    ui = create_link_editor() 
    ui.pass_down(init_dir)
    ui.set_geometry_obj(link_set, node_set)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)

    # 사용자 입력에 따른 콜백 등록
    cid_click = fig.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)
    fig.set_size_inches(9,9)

    plt.show()
    print('END')


if __name__ == u'__main__':
    """ CODE42의 원본 데이터를 불러와서 편집하고 저장하는 모드""" 
    convert_code42_geojson_to_mgeo_node_link_set()

    """ 위에서 저장한 Node, Link를 확인하기 위한 모드 """
    # start_from_empty_link()