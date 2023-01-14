#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 

import numpy as np
import matplotlib.pyplot as plt
from tkinter import filedialog

# MGeo Module
from lib.mgeo.class_defs import Link
from lib.mgeo.class_defs import MGeo

from lib.mgeo.edit.core_select_funcs import MGeoEditCoreSelectFunc
from lib.mgeo.edit.tasks.path_planning_using_dijkstra_task import PathPlanningUsingDijkstraTask

# from save_load import *
from utils import file_io


class SimpleEventHandler:
    def __init__(self, fig=None):
        # 모든 matplotlib 단축키 해제
        for key, val in plt.rcParams.items():
            if 'keymap' in key:
                plt.rcParams[key] = ''

        # data container
        self.mgeo_planner_map = MGeo()

        # select function
        self.select_func = MGeoEditCoreSelectFunc()

        # path planning function
        self.path_planner = PathPlanningUsingDijkstraTask(
            self.mgeo_planner_map.node_set,
            self.mgeo_planner_map.link_set)
        self.path_planning_result = False
        self.path_planning_solution = {}


        # 어떤 edit mode 인지 저장한다
        self.multistep_edit_mode = ''
        
        self.annotation_text = None
        self.annotation_id = None

        self.selected_point_mark = None
        self.selected_line_mark = None
        
        self.marker_start_node = None
        self.marker_end_node = None

        # Plot 관련
        self.enable_node = False
        self.enable_signal = False
        self.abs_xlim = None # Plot할 때 해당 범위에 있지 않으면 아예 제외 
        self.abs_ylim = None # Plot할 때 해당 범위에 있지 않으면 아예 제외 

        # Mouse Right Click 시 옵션
        self.mouse_right_click_vis_option_node_idx = True
        self.mouse_right_click_vis_option_point_idx = False


        # matplotlib.pyplot 데이터
        if fig is None:
            """fig를 입력하지 않으면 임의로 생성한다"""
            fig = plt.figure()
            fig.set_size_inches(9,9)
        self.fig = fig

        # NOTE: FigureCanvas가 초기화된 다음에 connect를 해주어야만 동작한다 (mpl_canvas 참조)
        self.cid_click = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.cid_press = self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.cid_scroll = self.fig.canvas.mpl_connect('scroll_event', self.on_scr_zoom)


    def start_simple_ui(self):
        self.update_plot(self.fig, plt.gca(), draw=True)
        plt.show()


    def get_multistep_edit_mode(self):
        return self.multistep_edit_mode


    def set_multistep_edit_mode(self, mode):
        self.multistep_edit_mode = mode

    """MGeo 데이터셋 인스턴스에 대한 Get, Set Methods"""

    def get_node_set(self):
        return self.mgeo_planner_map.node_set


    def get_link_set(self):
        return self.mgeo_planner_map.link_set


    def get_ts_set(self):
        return self.mgeo_planner_map.sign_set


    def get_tl_set(self):
        return self.mgeo_planner_map.light_set


    """선택된 MGeo 인스턴스에 대한 Get, Set Methods"""

    def get_selected_node(self):
        return self.select_func.selected_node
    

    def get_selected_line(self):
        return self.select_func.selected_line


    def get_selected_point(self):
        return self.select_func.selected_point
    

    """UI 업데이트 핵심 기능"""

    def _update_point_display(self, fig, ax):
        # 아래에서 사용할 로컬 변수를 업데이트한다
        line_idx = self.get_selected_point()['idx_line'] 
        point_idx = self.get_selected_point()['idx_point'] 

        point_type = self.get_selected_point()['type']
        x = self.get_selected_point()['coord'][0]
        y = self.get_selected_point()['coord'][1]
        z = self.get_selected_point()['coord'][2]

        if point_type == 'start':
            node_ref = self.get_selected_point()['line_ref'].get_from_node()
            node_str = 'node={}'.format(node_ref.idx)
        elif point_type == 'end':
            node_ref = self.get_selected_point()['line_ref'].get_to_node()
            node_str = 'node={}'.format(node_ref.idx)
        else:
            node_str = ""
        
        # print(
        #     '[INFO] line id={}, type={} (node id = {}), '.format(line_idx, point_type) +
        #     'loc=[{:.1f}, {:.1f}, {:.1f}] '.format(x,y,z))

        # [STEP #2] show text around the selected node
        if self.annotation_text != None:
            self.annotation_text.remove()
            fig.canvas.draw()


        display_str = point_type + ', line={}'.format(line_idx)


        if self.mouse_right_click_vis_option_point_idx:
            display_str += ', point={}'.format(point_idx)


        if self.mouse_right_click_vis_option_node_idx and node_str != "":
            display_str += ", " + node_str

    
        self.annotation_text = ax.text(x + 1, y + 1, display_str)


        # [STEP #3] Draw a mark on the selected node
        if self.selected_point_mark != None:
            for prev_selected_point in self.selected_point_mark:
                prev_selected_point.remove()
            # self.selected_point_mark[0].remove()

            # NOTE: [VERY IMPORTANT]
            # https://stackoverflow.com/questions/4981815/how-to-remove-lines-in-a-matplotlib-plot
            # Vorticity의 답변 참조. self.selected_point_mark에 대한 reference가 다른 장소에 남아있다면
            # 마우스 우클릭을 할 때마다 생성되는 point 객체가 메모리 상에 상주하고 garbage collected 되지 않는다.
            # 따라서 self.selected_point_mark = [] 이를 명시적으로 호출해주어야 한다.
            # 물론, 이 글이 오래된 글이라 현재의 Matplotlib에서 같은 동작일지는 모르겠으나 일단 따라해놓는다.
            # ax.lines.remove(self.selected_point_mark)
            # self.selected_point_mark = []


        if point_type == 'start': # start
            self.selected_point_mark = ax.plot(x, y,
                marker='^',
                markersize=10,
                color='g')
            fig.canvas.draw()

        elif point_type == 'mid':
            self.selected_point_mark = ax.plot(x, y,
                marker='d',
                markersize=10,
                color='g')
            fig.canvas.draw()

        else: # end
            self.selected_point_mark = ax.plot(x, y,
                marker='v',
                markersize=10,
                color='g')
            fig.canvas.draw()
  

    def clear_start_end_marker(self):
        fig = plt.gcf()
        ax = plt.gca()

        # start/end 마커 지우기 (cancel시에는 marker가 None일 수 있다)  
        if (self.marker_start_node is not None) and (self.marker_start_node != []):
            ax.lines.remove(self.marker_start_node[0])
            del self.marker_start_node[0]
        
        if (self.marker_end_node is not None) and (self.marker_end_node != []):
            ax.lines.remove(self.marker_end_node[0])
            del self.marker_end_node[0]


    def clear_current_plot(self):
        # 현재 라인셋의 draw 설정 백업
        # line_set 인스턴스를 받은 다음 이 값을 설정해주어야 하기 때문
        if len(self.get_link_set().lines) > 0: # empty인 workspace에서 load하려고 하면, 이 값이 0이므로
            for idx in self.get_link_set().lines:
                line = self.get_link_set().lines[idx]
                vis_mode_all_different_color =\
                    line.get_vis_mode_all_different_color()
                break # 한번만 실행하면 되기 때문
        else:
            vis_mode_all_different_color = False

        # 기존에 있던 node_set, line_set 정리
        self.get_node_set().erase_plot()
        self.get_link_set().erase_plot()
        self.get_tl_set().erase_plot()
        self.get_ts_set().erase_plot()


    def update_plot(self, fig, ax, draw=False):
        '''
        현재 공간에서 xlim, ylim을 찾아서, 근처 범위에 있는 line, node만 그려준다
        '''

        enable_node = self.enable_node
        enable_signal = self.enable_signal

        if draw:               
            if self.abs_xlim is None or self.abs_ylim is None:
                # 설정이 안 되어 있으면 그냥 다 그린다

                self.get_node_set().erase_plot()
                self.get_link_set().erase_plot()
                self.get_ts_set().erase_plot()
                self.get_tl_set().erase_plot()

                self.get_node_set().draw_plot(ax)
                self.get_link_set().draw_plot(ax)
                self.get_ts_set().draw_plot(ax)
                self.get_tl_set().draw_plot(ax)

            else:
                # 설정이 되어 있으면, 해당 구간에 있는 것만 그린다

                # nodes가 list이든 dict이든 상관없이 적용할 수 있다.
                for idx, node in self.get_node_set().nodes.items():
                    if node.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    node.erase_plot()
                    node.draw_plot(ax)


                for idx, line in self.get_link_set().lines.items():
                    if line.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    line.erase_plot()
                    line.draw_plot(ax)

                for idx, ts in self.get_ts_set().signals.items():
                    if ts.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    ts.hide_plot() 
                    ts.unhide_plot()

                for idx, tl in self.get_tl_set().signals.items():
                    if tl.is_out_of_xy_range(self.abs_xlim, self.abs_ylim):
                        continue

                    tl.hide_plot() 
                    tl.unhide_plot()
                
            # ax.set_aspect('equal')

        # node disable이면 일단 전체를 disable 시킨다
        if not enable_node:
            for idx, node in self.get_node_set().nodes.items():
                node.hide_plot()

        if not enable_signal:
            for idx, ts in self.get_ts_set().signals.items():
                ts.hide_plot()
            for idx, tl in self.get_tl_set().signals.items():
                tl.hide_plot()
            
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # 현재 공간에서 margin을 준다
        margin = 2


        def _add_margin(lim, margin):
            mid = (lim[1] + lim[0])/2
            dist_from_mid = (lim[1] - lim[0])/2

            new_min = mid - dist_from_mid * margin
            new_max = mid + dist_from_mid * margin
            return (new_min, new_max)

        xlim = _add_margin(xlim, margin)
        ylim = _add_margin(ylim, margin)


        """danling node에 대한 hide/unhide 처리 별도로 함"""
        if enable_node:
            for idx, node in self.get_node_set().nodes.items():
                if node.is_dangling_node():
                    if node.is_out_of_xy_range(xlim, ylim):
                        node.hide_plot()
                    else:
                        node.unhide_plot()

                else:
                    # 특정 링크에 연결된 노드일 경우,
                    # 해당 링크의 bbox 여부로 hide/unhide 여부를 결정한다
                    continue


        """line, link 및 연결된 node에 대한 hide/unhide 처리"""
        for idx, line in self.get_link_set().lines.items():
            if line.is_out_of_xy_range(xlim, ylim):

                line.hide_plot()
                # 관련 node에도 적용
                if line.from_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                    line.from_node.hide_plot()
                if line.to_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                    line.to_node.hide_plot()
                continue
            else:
                line.unhide_plot()

            if enable_node:
                if line.from_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                    line.from_node.unhide_plot()
                if line.to_node is not None: # line 또는 link에 문제가 있는 경우 none일 수 있다.
                    line.to_node.unhide_plot()


        if enable_signal:
            for idx, ts in self.get_ts_set().signals.items():
                if ts.is_out_of_xy_range(xlim, ylim):
                    ts.hide_plot() 
                else:
                    ts.unhide_plot()

            for idx, tl in self.get_tl_set().signals.items():
                if tl.is_out_of_xy_range(xlim, ylim):
                    tl.hide_plot()
                else:
                    tl.unhide_plot()

        
        # plt.draw를 쓰면 동작하지 않는다.
        # 참조: https://stackoverflow.com/questions/30880358/matplotlib-figure-not-updating-on-data-change
        fig.canvas.draw()


    def set_absolute_bbox_for_plot(self, xlim, ylim):
        self.abs_xlim = xlim
        self.abs_ylim = ylim


    """Event Handler"""

    def on_click(self, event):
        '''
        Constants:
        MouseButton.LEFT = 1
        MouseButton.MIDDLE = 2
        MouseButton.RIGHT = 3
        '''
        fig = plt.gcf()

        # save clicked location
        if event.button == 3:  # MouseButton.RIGHT = 3
            ax = event.inaxes
            search_coord = np.array([event.xdata, event.ydata])
            
            # 선택된 객체 업데이트
            node = self.select_func.update_selected_objects_using_node_snap(search_coord)
            
            # 화면 출력 업데이트 (Point)
            self._update_point_display(fig, ax)

            # 화면 출력 업데이트 (Line/Link)  
            # 선택한 point가 포함된 선을 표시해줌
            if self.selected_line_mark != None:
                for prev_selected_line in self.selected_line_mark:
                    prev_selected_line.remove()
            self.selected_line_mark = ax.plot(
                self.get_selected_line().points[:,0],
                self.get_selected_line().points[:,1],
                marker='d',
                markersize=3,
                color='r',
                linewidth=1)

            fig.canvas.draw()


    def on_key(self, event):
        """
        [Help]
        F1     : print shortcut keys

        [Data Load]
        ctrl+l : load mgeo

        [Path Planning]
        q      : set start node for path planning
        w      : set end node for path planning
        enter  : find shortest path using dijkstra
        esc    : cancel path planning

        [Viewer Control]
        v      : update plot
        alt+v  : node   view on/off
        ctrl+v : signal view on/off 

        [Find/Highlight Data]
        """
        fig = plt.gcf()
        ax = plt.gca()


        # 입력된 key 출력하기 (up/down 입력에 대해서는 생략)
        # if ('up' not in event.key) and ('down' not in event.key):
        print_trace('Key pressed: {}'.format(event.key))


        if event.key == 'ctrl+alt+d':
            print('[DEBUG] Entered Debug Mode')
            print('[DEBUG] Exiting Debug Mode')

        elif event.key == 'f1':
            help_msg =\
                ("--------------------- [Help] ---------------------\n" +
                "[HELP]\n" +
                "F1               : print shortcut keys\n" +

                "\n[Data Load]\n" +
                "ctrl+l           : load mgeo\n" +

                "\n[Viewer Control]\n" +
                "(L) click + drag : pan (using matplotlib default control)\n"
                "(R) click + drag : axis zoom in/out\n" +
                "(R) click        : select node & connected link\n" +
                "v                : update plot\n" +
                "alt+v            : node   view on/off\n" +
                "ctrl+v           : signal view on/off\n" +

                "\n[Path Planning]\n" +
                "q                : set start node for path planning\n" +
                "w                : set end   node for path planning\n" +
                "enter            : find shortest path using dijkstra\n" +
                "esc              : cancel path planning\n" +
                
                "\n[Find/Highlight Data]\n" +
                "--------------------------------------------------")
            print(help_msg)

        elif event.key == 'ctrl+l':
            self.load_mgeo()


        elif event.key == 'up' or event.key == 'down':
            if event.key == 'up':
                self.select_func.update_selected_point(1)
            else:
                self.select_func.update_selected_point(-1)
            
            self._update_point_display(fig, ax)   


        elif event.key == 'ctrl+up' or event.key == 'ctrl+down':
            if event.key == 'ctrl+up':
                self.select_func.update_selected_point(5)
            else:
                self.select_func.update_selected_point(-5)
            
            self._update_point_display(fig, ax)   


        elif event.key == 'shift+up' or event.key == 'shift+down':
            if event.key == 'shift+up':
                self.select_func.update_selected_point(20)
            else:
                self.select_func.update_selected_point(-20)
            
            self._update_point_display(fig, ax)   


        elif event.key == 'shift+ctrl+up' or event.key == 'shift+ctrl+down':
            if event.key == 'shift+ctrl+up':
                self.select_func.update_selected_point(100)
            else:
                self.select_func.update_selected_point(-100)
            
            self._update_point_display(fig, ax)   


        elif event.key == 'enter':
            self.path_planning_task_ok()


        elif event.key == 'escape':
            self.path_planning_task_cancel()
            

        elif event.key == 'q':
            self.path_planning_task_init()
            self.path_planning_task_set_start_point()


        elif event.key == 'w':
            self.path_planning_task_set_end_point()
    

        elif event.key == 'v':
            print_info('Update line & node plot')
            self.update_plot(fig, ax, draw=False)


        elif event.key == 'alt+v':
            print_info('Toggle node view')
            
            # Toggle
            self.enable_node = not self.enable_node

            # Then, update
            self.update_plot(fig, ax, draw=False)


        elif event.key == 'ctrl+v':
            print_info('Toggle signal view')
            
            # Toggle
            self.enable_signal = not self.enable_signal

            # Then, update
            self.update_plot(fig, ax, draw=False)


        elif event.key == 'h':
            # highlight를 쳐줘서 찾아준다 (line or link)
            # NOTE: 디버그 모드에서만 현재는 사용한다
            
            def _highlight_line(highlight_obj_idx_list):
                for idx in self.get_link_set().lines:
                    line = self.get_link_set().lines[idx]
                    
                    if line.idx in highlight_obj_idx_list:
                        line.set_vis_mode_manual_appearance(3, 'b')
                    else:
                        line.set_vis_mode_manual_appearance(1, 'k')
            
            def _highlight_node(highlight_obj_idx_list):
                for idx in self.get_node_set().nodes:
                    node = self.get_node_set().nodes[idx]

                    if node.idx in highlight_obj_idx_list:
                        node.set_vis_mode_manual_appearance(7, 'r', no_text=False)
                    else:
                        node.set_vis_mode_manual_appearance(3, 'g', no_text=True)

            # [사용 방법]
            ## _highlight_line(['A219BA000137'])
            ## _highlight_node(['A119BA000142'])

            # redraw
            self.update_plot(fig, ax, draw=True)


        elif event.key == 'alt+h':
            # reset highlight
            for var in self.get_link_set().lines:
                line = self.get_link_set().lines[var]
                line.reset_vis_mode_manual_appearance()

            for var in self.get_node_set().nodes:
                node = self.get_node_set().nodes[var]
                node.reset_vis_mode_manual_appearance()

            # redraw
            self.update_plot(fig, ax, draw=True)
        

    def on_scr_zoom(self, event):
        # reference:
        # https://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel

        # get current axis limits
        ax = event.inaxes
        fig = plt.gcf()

        if ax.get_xlim() == None:
            raise Exception('[ERROR] Scroll with the mouse cursor on the axes')

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_xrange = (cur_xlim[1] - cur_xlim[0])*0.5
        cur_yrange = (cur_ylim[1] - cur_xlim[0])*0.5

        # recognize scroll event
        if event.button == 'up':
            # zoom in
            sf = 0.5
        elif event.button == 'down':
            # zoom out
            sf = 2
        else:
            # error
            raise Exception('Scroll error')

        # set new axis limits
        # ax.set_xlim([event.xdata - cur_xrange*sf, event.xdata + cur_xrange*sf])
        # ax.set_ylim([event.ydata - cur_yrange*sf, event.ydata + cur_yrange*sf])
        ax.set_xlim([event.xdata - (event.xdata - cur_xlim[0])*sf, event.xdata + (cur_xlim[1] - event.xdata)*sf])
        ax.set_ylim([event.ydata - (event.ydata - cur_ylim[0])*sf, event.ydata + (cur_ylim[1] - event.ydata)*sf])

        # redraw plot
        # plt.draw()
        fig.canvas.draw()

   
    """Path Planning"""

    def path_planning_task_init(self):
        self.path_planner = PathPlanningUsingDijkstraTask(
            self.get_node_set(),
            self.get_link_set())


    def path_planning_task_set_start_point(self):
        """사용자가 start point를 선택할 때의 동작, start marker를 표시한다"""
        fig = plt.gcf()
        ax = plt.gca()

        if self.get_selected_node() == None:
            print_error(' A node must be selected!')
            return

        start_node = self.get_selected_node()
        self.path_planner.set_start_node(start_node)

        # update start node marker
        if (self.marker_start_node is not None) and (self.marker_start_node != []):
            ax.lines.remove(self.marker_start_node[0])
        
        x = start_node.point[0]
        y = start_node.point[1]
        self.marker_start_node = ax.plot(x, y,
            marker='o',
            markersize=15,
            color='b')
        fig.canvas.draw()
        print_info('Start point selected.')        


    def path_planning_task_set_end_point(self):
        """사용자가 end point를 선택할 때의 동작, end marker를 표시한다"""
        fig = plt.gcf()
        ax = plt.gca()

        if self.get_selected_node() == None:
            print_error('A node must be selected!')
            return

        end_node = self.get_selected_node()
        self.path_planner.set_end_node(end_node)

        # update end node marker
        if self.marker_end_node != None and self.marker_end_node != []:
            ax.lines.remove(self.marker_end_node[0])

        x = end_node.point[0]
        y = end_node.point[1]
        self.marker_end_node = ax.plot(x, y,
            marker='P',
            markersize=15,
            color='b')
        fig.canvas.draw()
        print_info('End point selected.')


    def path_planning_task_ok(self):
        # 최근 결과가 Plot 되어있었으면 지운다
        if self.path_planning_result:
            for link_id in self.path_planning_solution['link_path']:
                link = self.get_link_set().lines[link_id]
                link.reset_vis_mode_manual_appearance()
        self.path_planning_result = False
        self.path_planning_solution = {}

        # path_planning 알고리즘을 이용하여 계산한 다음 이를 내부 변수에 저장한다.
        self.path_planning_result, self.path_planning_solution = self.path_planner.do()

        if self.path_planning_result:
            # string 출력
            print('---------- path (node id) ----------')
            for node_id in self.path_planning_solution['node_path']:
                print('  {}'.format(node_id))
            print('------------------------------------')

            print('---------- path (link id) ----------')
            for link_id in self.path_planning_solution['link_path']:
                link = self.get_link_set().lines[link_id]
                from_node_idx = link.from_node.idx
                to_node_idx = link.to_node.idx
                print(' {} -> {:30} -> {}'.format(from_node_idx, link_id, to_node_idx))
            print('------------------------------------')

            # 그려서 보여주기
            for link_id in self.path_planning_solution['link_path']:
                link = self.get_link_set().lines[link_id]
                link.set_vis_mode_manual_appearance(3, 'g')

        self.clear_start_end_marker()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)
        
        print_info('path_planning task finished')


    def path_planning_task_cancel(self):
        # 최근 결과가 Plot 되어있었으면 지운다
        if self.path_planning_result:
            for link_id in self.path_planning_solution['link_path']:
                link = self.get_link_set().lines[link_id]
                link.reset_vis_mode_manual_appearance()
        self.path_planning_result = False
        self.path_planning_solution = {}

        # path planner에서 cancel
        self.path_planner.cancel()

        self.clear_start_end_marker()

        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)
        
        print_info('path_planning task cancelled')
        

    """MGeo Load/Save"""

    def load_mgeo(self):
        root_dir = file_io.get_proj_root_dir()
        init_load_path = os.path.join(root_dir, 'saved/') 
        init_load_path = os.path.normpath(init_load_path)
        print_trace('init_load_path: {}'.format(init_load_path))

        load_path = filedialog.askdirectory(
            initialdir = init_load_path, 
            title = 'Load files from') # defaultextension = 'json') 과 같은거 사용 가능    
        
        if load_path == '' or load_path == None:
            print_info('MGeo Load operation cancelled')
            return

        # 데이터 로드하기
        mgeo_planner_map = MGeo.create_instance_from_json(load_path)

        # mgeo_planner_map 업데이트 전에 clear 시켜준다
        self.clear_current_plot()
        
        # Edit Core 업데이트
        self.mgeo_planner_map = mgeo_planner_map
        self.select_func.set_geometry_obj(
            self.get_node_set(),
            self.get_link_set(),
            self.get_ts_set(),
            self.get_tl_set())
        
        fig = plt.gcf()
        ax = plt.gca()
        self.update_plot(fig, ax, draw=True)

        print_info("MGeo data successfully loaded from: {}".format(load_path))


def print_info(msg):
    print('[INFO]', msg)

def print_warn(msg):
    print('[WARN] ', msg)

def print_error(msg):
    print('[ERROR]', msg)

def print_trace(msg):
    print('[TRACE]', msg)

def print_debug(mag):
    print('[DEBUG] ', msg)

