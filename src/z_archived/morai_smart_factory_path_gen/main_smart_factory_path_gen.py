#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # mgeo가 있는 경로를 추가한다.


from lib.mgeo.class_defs import *
import lib.mgeo.save_load.mgeo_load as mgeo_load
from lib_ngii_shp_ver2.shp_edit_funcs import scr_zoom, UserInput, create_link_editor
from lib.path_planning.dijkstra import Dijkstra


import time
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt


def first_run_load_txt():
    '''
    처음 전달받은 .txt파일을 불러와서, 
    초기 데이터를 보여준다. 그리고 alt+s 키를 눌러 앞으로 수정할 json 파일 형식으로 저장 
    '''
    # txt 파일 있는 경로
    input_dir = os.path.join(current_path, '../../rsc/map_data/smartfactory_link')
    input_dir = os.path.normpath(input_dir)


    # 출력 파일 있는 경로
    output_dir = os.path.join(current_path, '../../saved/links/SmartFactoryLink')
    output_dir = os.path.normpath(output_dir)
    
    
    # 모든 파일 리스트
    import glob
    files = glob.glob(input_dir + '/**/*.txt', recursive=True)

    line_set = LineSet()

    # 각 파일을 읽어서 link로 만들고... 
    for filename in files:
        # file을 읽어서, csv로 불러오면 된다.
        with open(filename) as f:
            data = np.genfromtxt(
                filename,
                dtype=None,
                delimiter='\t',
            )

        # 이 numpy array로 바로 line을 생성하면 된다.

        print('[INFO] Read: ', filename)
        link = Link()
        link.set_points(data)
        line_set.append_line(link, create_new_key=True)

    line_set.set_vis_mode_all_different_color(True)
    node_set = line_set.create_node_set_for_all_lines(dist_threshold=0.01)


    fig = plt.figure()

    # Link Editor 생성
    ui = create_link_editor() 
    ui.pass_down(output_dir)

    ui.set_geometry_obj(line_set, node_set)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)
    
    

    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)
    fig.set_size_inches(8,8)

    plt.show()

    print('END')
    pass


def main():
    # 출력 파일 있는 경로
    init_dir = os.path.join(current_path, '../../saved/links/SmartFactoryLink')
    init_dir = os.path.normpath(init_dir)

    # 맵 로드할 경로 받아오기
    load_path = filedialog.askdirectory(
        initialdir = init_dir,
        title = 'Load files from')
    
    # 맵 로드해주고 line_set (link_set) visualization 옵션 선택
    node_set, line_set = mgeo_load.load_node_and_link(load_path)
    line_set.set_vis_mode_all_different_color(True)

    # Disable a few keyboard shotcuts
    # NOTE: 다른 keymap 찾으려면 다음을 참고: https://matplotlib.org/tutorials/introductory/customizing.html
    plt.rcParams['keymap.save'] = 'ctrl+s' # 원래 s, ctrl+s로 동작하는데 s만 사용하도록
    plt.rcParams['keymap.pan'] = ''
    plt.rcParams['keymap.xscale'] = ''
    plt.rcParams['keymap.yscale'] = ''
    plt.rcParams['keymap.quit'] = ''
    plt.rcParams['keymap.quit_all'] = ''

    # figure 생성
    fig = plt.figure(1)

    # Link Editor 생성
    ui = create_link_editor() 
    ui.pass_down(init_dir)
    ui.set_geometry_obj(line_set, node_set)
    ui.update_plot(plt.gcf(), plt.gca(), enable_node=ui.enable_node, draw=True)

    # 사용자 입력에 따른 콜백 등록
    cid_click = fig.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)
    fig.set_size_inches(8,8)

    plt.show()


if __name__ == '__main__': 
    main()