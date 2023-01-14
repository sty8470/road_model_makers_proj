#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # mgeo가 있는 경로를 추가한다.


import lib.mgeo.save_load.mgeo_load as mgeo_load
from lib_ngii_shp_ver2.shp_edit_funcs import scr_zoom, UserInput
from lib.path_planning.dijkstra import Dijkstra


import time
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt


def _add_margin(lim, margin):
            mid = (lim[1] + lim[0])/2
            dist_from_mid = (lim[1] - lim[0])/2

            new_min = mid - dist_from_mid * margin
            new_max = mid + dist_from_mid * margin
            return (new_min, new_max)
        
            xlim = (x.min(), x.max())
            ylim = (y.min(), y.max())


def find_path_and_save_as_csv(dijkstra_obj, start_node_id, end_node_id, output_path):   
    # 최적 경로 찾기 + 계산 시간 측정
    print('[INFO] Start running shortest path algorithm. Node{} -> Node{}'.format(start_node_id, end_node_id))
    start_time = time.time()
    result, global_path = dijkstra_obj.find_shortest_path(start_node_id, end_node_id)
    if not result:
        raise BaseException('[ERROR] Dijkstra has filed to find a path for the given input')
    end_time = time.time()
    print('[INFO] Get the shortest path (took {} sec)'.format(end_time - start_time))

    global_path = np.array(global_path)


    # csv로 저장하기 (같은 경로에 저장, 파일 명은 global path로)
    file_name = 'path_from_N{}_to_N{}.csv'.format(start_node_id, end_node_id)
    with open(os.path.join(output_path, file_name), 'w') as f:
        f.write('X,Y,Z\n')
        np.savetxt(f, global_path, fmt='%.6f', delimiter=',') 

    return global_path


def create_one_plot_one(draw_plot=False):
    # 초기 경로
    init_dir = os.path.join(current_path, '../saved/links/')
    init_dir = os.path.normpath(init_dir)

    # 맵 로드할 경로
    data_path = filedialog.askdirectory(
        initialdir = init_dir,
        title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능   


    # 맵 로드하기 + 계산 시간 측정
    print('[INFO] Start to load map data')
    start_time = time.time() 
    node_set, line_set = mgeo_load.load_node_and_link(data_path)
    end_time = time.time()
    print('[INFO] Map loaded (took {} sec)'.format(end_time - start_time))


    # Dijkstra Object 생성 
    dijkstra_obj = Dijkstra(node_set.nodes, line_set.lines)


    # 경로 찾아서 csv로 저장하기
    print('[INFO] Start running shortest path algorithm')
    start_time = time.time() 
    global_path = find_path_and_save_as_csv(dijkstra_obj, 
        start_node_id=439,
        end_node_id=1436, 
        output_path=data_path)
    end_time = time.time()
    print('[INFO] Get the shortest path (took {} sec)'.format(end_time - start_time))


    # 계산된 global_path를 눈으로 보고 싶으면 다음을 이용하면 된다.
    if draw_plot:
        x = global_path[:,0]
        y = global_path[:,1]
        z = global_path[:,2]
        
        xlim = (x.min(), x.max())
        ylim = (y.min(), y.max())

        margin = 1.5
        xlim = _add_margin(xlim, margin)
        ylim = _add_margin(ylim, margin)

        
        import matplotlib.pyplot as plt
        fig = plt.figure()

        ui = UserInput()
        ui.pass_down(data_path)
        ui.set_geometry_obj(line_set, node_set)

        """ 사용자 입력에 따른 콜백 모음 """
        cid_click = fig.canvas.mpl_connect('button_press_event', ui.on_click)
        cid_press = fig.canvas.mpl_connect('key_press_event', ui.on_key)
        cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)

        fig.set_size_inches(10,10)
        ui.update_plot(fig, plt.gca(), ui.enable_node, draw=True)
        # line_set.draw_plot(plt.gca())

        plt.plot(x, y, 
            linewidth=5,
            color='r')

        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.show()


def main(draw_plot=False):
    # 초기 경로
    init_dir = os.path.join(current_path, '../saved/links/')
    init_dir = os.path.normpath(init_dir)

    # 맵 로드할 경로
    data_path = filedialog.askdirectory(
        initialdir = init_dir,
        title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능   


    # 맵 로드하기 + 계산 시간 측정
    print('[INFO] Start to load map data')
    start_time = time.time() 
    node_set, line_set = mgeo_load.load_node_and_link(data_path)
    end_time = time.time()
    print('[INFO] Map loaded (took {} sec)'.format(end_time - start_time))

    """ 한번 확인용으로 그려보기 """
    # fig = plt.figure()
    # node_set.draw_plot(plt.gca())
    # line_set.draw_plot(plt.gca())
    # plt.show()

    # Dijkstra Object 생성 
    # dijkstra_obj = Dijkstra(node_set.nodes, line_set.lines)


    # 찾아야할 경로의 리스트
    svehicle_path_list = [
        (439, 1436),
        # (439, 203),
        # (437, 356),
        # (138, 320),
        # (440, 318),
        # (300, 203),
        # (476, 243),
        # (236, 244),
        # (237, 245),
        # (448, 230),
        # (451, 245),
        # (299, 306),      
        
        
        # (222, 245), # (227, 245), # NOTE: 227로 시작하던 경로를 이걸로 바꿈
        # (223, 1436), # (228, 1436), # NOTE: 228로 시작하던 경로를 이걸로 바꿈
    ]
    global_path_list = []


    # 경로 찾아서 csv로 저장하기
    for i in range(len(svehicle_path_list)):
        dijkstra_obj = Dijkstra(node_set.nodes, line_set.lines)

        start = svehicle_path_list[i][0]
        end = svehicle_path_list[i][1]

        start_time = time.time() 
        global_path = find_path_and_save_as_csv(dijkstra_obj, 
            start_node_id=start,
            end_node_id=end, 
            output_path=data_path)
        end_time = time.time()

        global_path_list.append(global_path)

    

    # 계산된 global_path를 눈으로 보고 싶으면 다음을 이용하면 된다.
    if draw_plot:
        fig = plt.figure()

        print('[INFO] Start to load UI')
        start_time = time.time() 
    
        ui = UserInput()
        ui.pass_down(data_path)
        ui.set_geometry_obj(line_set, node_set)

        # 이 범위에 있는 대상을 처음 plot시부터 아예 제외하도록
        #xlim = (-50, 950)
        xlim = [-50, 750]
        ylim = [-650, 250]
        ui.set_absolute_bbox_for_plot(xlim, ylim)



        """ 사용자 입력에 따른 콜백 모음 """
        cid_click = fig.canvas.mpl_connect('button_press_event', ui.on_click)
        cid_press = fig.canvas.mpl_connect('key_press_event', ui.on_key)
        cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)

        fig.set_size_inches(10,10)
        ui.update_plot(fig, plt.gca(), ui.enable_node, draw=True)

        end_time = time.time()
        print('[INFO] UI loaded (took {} sec)'.format(end_time - start_time))

        for i in range(len(global_path_list)):
            global_path = global_path_list[i]
            x = global_path[:,0]
            y = global_path[:,1]
            z = global_path[:,2]

            print('x.shape: ', x.shape)
            
            # 처음 경로가 ego-vehicle이 따라갈 경로이기 때문에,
            # 처음 경로를 기준으로 xlim, ylim을 잡아준다
            if i == 0:
                xlim = (x.min(), x.max())
                ylim = (y.min(), y.max())
                margin = 1.5
                xlim = _add_margin(xlim, margin)
                ylim = _add_margin(ylim, margin)

                plt.xlim(xlim)
                plt.ylim(ylim)
                
                plt.plot(x, y, 
                    linewidth=3,
                    marker='',
                    markersize=4,
                    color='g')
                plt.gca().plot(x[0], y[0],
                    markersize=12,
                    marker='o',
                    color='k')
                plt.gca().plot(x[-1], y[-1],
                    markersize=12,
                    marker='P',
                    color='k')
            
            else:
                plt.plot(x, y, 
                    linewidth=3,
                    marker='',
                    markersize=4,
                    color='r')
                plt.gca().plot(x[0], y[0],
                    markersize=12,
                    marker='o',
                    color='k')
                plt.gca().plot(x[-1], y[-1],
                    markersize=12,
                    marker='P',
                    color='k')

        plt.show()
        

    
            



if __name__ == '__main__':
    # create_one_plot_one(draw_plot=True)
    main(draw_plot=True)
