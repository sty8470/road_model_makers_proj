import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')


from lib_ngii_shp_ver2.shp_edit_funcs import UserInput, scr_zoom
from data_type_def import LineSet, Node, Link
from data_import import *

def test_visualize_raw_data():
    fig_lane = plt.figure(1)

    """ 사용자 입력에 따른 콜백을 처리하기 위한 클래스 인스턴스 """
    ui = UserInput()

    """ 파일 읽어주기 """
    node_set_obj = None
    line_set_obj = import_k_city_data(plot=True)
    ui.set_geometry_obj(line_set_obj, node_set_obj)
     
    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    nodes, links = create_node_from_link_info(line_set_obj)
    
    fig_lane.set_size_inches(12,12)
    plt.show()
    print('[INFO] Ended Successfully.')


def test_visualize_nodes_and_links():
    fig_lane = plt.figure(1)

    """ 사용자 입력에 따른 콜백을 처리하기 위한 클래스 인스턴스 """
    ui = UserInput()

    """ 파일 읽어주기 """
    node_set_obj = None
    line_set_obj = import_k_city_data(plot=False)
    ui.set_geometry_obj(line_set_obj, node_set_obj)
     
    """ 사용자 입력에 따른 콜백 모음 """
    cid_click = fig_lane.canvas.mpl_connect('button_press_event', ui.on_click)
    cid_press = fig_lane.canvas.mpl_connect('key_press_event', ui.on_key)
    cid_scroll = fig_lane.canvas.mpl_connect('scroll_event', scr_zoom)

    nodes, links = create_node_from_link_info(line_set_obj)

    for node in nodes:
        plt.plot(node.point[0], node.point[1],
            markersize=3,
            marker='D',
            color='b')
        plt.gca().text(node.point[0], node.point[1], node.idx,
            fontsize=20)

    for line in links:
        plt.plot(line.points[:,0], line.points[:,1],
            markersize=1,
            marker='o',
            color='g',
            linewidth=1)


    fig_lane.set_size_inches(12,12)
    plt.show()
    print('[INFO] Ended Successfully.')


if __name__ == u'__main__':
    test_visualize_nodes_and_links()