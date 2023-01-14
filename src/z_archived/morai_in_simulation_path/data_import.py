#-*- coding: utf-8 -*-
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))

import numpy as np 
import matplotlib.pyplot as plt

from data_type_def import LineSet, Node, Link
from link_info import connection_info_list

def import_k_city_data(plot=False):
    input_path = 'k_city_sample_path/'
    
    # 절대 경로로 변경
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  
    print(input_path)

    # 내부에 있는 파일 리스트를 받아온다
    line_set_obj = LineSet()
    
    # 파일을 하나씩 읽고 데이터를 만든다
    idx_line = 0
    file_list = os.listdir(input_path)

    # Pre-allocate
    # NOTE: MGeo 쪽에서 삭제된 메소드임. 수정할 것.
    line_set_obj.preallocate_lines_list(len(file_list))
        
    for each_file in file_list:
        idx_str = each_file.replace('link (','')
        idx_str = idx_str.replace(').txt','')
        idx = int(idx_str)

        # print('each_file = {}, idx = {}'.format(each_file, idx))

        each_file_full_path = os.path.join(input_path, each_file)

        data = np.genfromtxt(
            fname=each_file_full_path,
            delimiter='\t',
            skip_header=0,
            usecols=None,
            names=None
        )

        if plot:
            # 우선 Plot을 해준다
            x = data[:,0]
            y = data[:,1]
            plt.plot(x, y, linewidth=0.5)

        # points를 Link로 만든다
        new_link = Link(id=idx, name_text=each_file)
        new_link.set_points(data)
        line_set_obj.lines[idx] = new_link

        # 다음 파일 인덱스
        idx_line += 1

    return line_set_obj


def get_current_link_connection_info(link):
    for connection_info in connection_info_list:
        link_id = connection_info[0]   
        if link.idx == link_id:
            return connection_info


def create_node_from_link_info(line_set_obj):
    """ 링크 정보가 있을 때 어떻게 처리할 것인가 """
    node_idx = 0
    nodes = list() 
    for connection_info in connection_info_list:
        current_link_id = connection_info[0]
        from_link_ids = connection_info[2]
        end_link_ids = connection_info[4]

        current_link = line_set_obj.lines[current_link_id]
        
        # start 방향에 노드가 없으면 생성한다
        if current_link.get_from_node() == None:
            # 그런데 직전 링크가 있는 경우
            if type(from_link_ids) == str:
                print('encountered END node')

            # 직전 링크가 있는 경우
            else:
                new_node = Node(node_idx)
                new_node.point = current_link.points[0]
                nodes.append(new_node)
                node_idx += 1

                # 현재 링크의 from node로 등록
                current_link.set_from_node(new_node)

                 # 직전 링크의 to node로 등록
                for idx in from_link_ids:
                    line_set_obj.lines[idx].set_to_node(new_node)


        # end 방향에 노드가 없으면 생성한다
        if current_link.get_to_node() == None:
            # 다음 링크가 없는 경우 
            if type(end_link_ids) == str:
                print('encountered END node')
            else:
                new_node = Node(node_idx)
                new_node.point = current_link.points[-1]
                nodes.append(new_node)
                node_idx += 1

                # 현재 링크의 to node로 등록
                current_link.set_to_node(new_node)

                # 다음 링크의 from node로 등록
                for idx in end_link_ids:
                    line_set_obj.lines[idx].set_from_node(new_node)

    """
    Start Node와 End Node인 부분을 찾아서 해결한다
    Start Node와 End Node로 연결된 링크는,
    링크와 링크 사이의 연결이 없는 경우이다. 
    connection_info_list에는 이를 END1, END2, ... 와 같이 표기해두었다. 
    같은 이름의 END[숫자]를 갖는 link를 찾아서, 모두가 하나의 노드에 연결되도록 해준다
    """
    for i in range(0, len(line_set_obj.lines)):
        current_link = line_set_obj.lines[i]

        if current_link.get_from_node() == None:
            connection_info = get_current_link_connection_info(current_link)
            current_link_from_link_ids = connection_info[2]
            
            new_node = Node(node_idx)
            new_node.point = current_link.points[0]
            nodes.append(new_node)
            node_idx += 1
            
            current_link.set_from_node(new_node)

            print('[DEBUG] Link={}, from={}'.format(i, current_link_from_link_ids))

            # 현재 노드와 같은 이름의 from_link를 갖는 다른 링크를 검색한다
            for k in range(0, len(line_set_obj.lines)):
                another_link = line_set_obj.lines[k]
                if another_link.idx != current_link.idx:
                    another_conn_info = connection_info = get_current_link_connection_info(another_link)
                    another_link_from_link_ids = connection_info[2]
                    
                    # 같으면 해당 링크에 이번에 만든 노드를 등록해준다
                    if current_link_from_link_ids == another_link_from_link_ids:
                        another_link.set_from_node(new_node)
                        print('[DEBUG] Link={}, from={}'.format(k, another_link_from_link_ids))


        if current_link.get_to_node() == None:
            connection_info = get_current_link_connection_info(current_link)
            current_link_to_link_ids = connection_info[4]

            new_node = Node(node_idx)
            new_node.point = current_link.points[-1]
            nodes.append(new_node)
            node_idx += 1

            current_link.set_to_node(new_node)

            print('[DEBUG] Link={}, to={}'.format(i, current_link_to_link_ids))

            # 현재 노드와 같은 이름의 to_link를 갖는 다른 링크를 검색한다
            for k in range(0, len(line_set_obj.lines)):
                another_link = line_set_obj.lines[k]
                if another_link.idx != current_link.idx:
                    another_conn_info = connection_info = get_current_link_connection_info(another_link)
                    another_link_to_link_ids = connection_info[4]
                    
                    # 같으면 해당 링크에 이번에 만든 노드를 등록해준다
                    if current_link_to_link_ids == another_link_to_link_ids:
                        another_link.set_to_node(new_node)
                        print('[DEBUG] Link={}, from={}'.format(k, another_link_from_link_ids))

    links = line_set_obj.lines
    print('[INFO] {} Nodes are created from {} Links'.format(len(nodes), len(links)))
    
    return nodes, links


if __name__ == u'__main__':
    """ HOW TO USE """
    line_set_obj = import_k_city_data()
    nodes, links = create_node_from_link_info(line_set_obj)
    print('[INFO] Ended Successfully')