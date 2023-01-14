#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from numpy import linalg as LA
import matplotlib.pyplot as plt
from lib.mgeo.edit.funcs import edit_line

# NOTE: 원래 여기에 Node, Line, Link가 중복으로 정의되어 있었음
# 삭제 후 테스트 안 했음. 테스트 필요
        
def create_sample_map():
    """
    노드 정의하기
    """
    nodes = []
    for i in range(0, 9):
        nodes.append(Node(i))

    nodes[0].point = np.array([0, 0, 0])
    nodes[1].point = np.array([10, 0, 0])
    nodes[2].point = np.array([30, 0, 0])
    
    nodes[3].point = np.array([0, 10, 0])
    nodes[4].point = np.array([10, 10, 0])
    nodes[5].point = np.array([30, 10, 0])
    
    nodes[6].point = np.array([0, 15, 0])
    nodes[7].point = np.array([10, 15, 0])
    nodes[8].point = np.array([30, 15, 0])


    """
    특정 노드에서 특정 노드로 가는 각각의 선을 정의
    """
    links = []
    
    # line0
    link = Link(0)
    edit_line.set_points_using_node(link, nodes[0], nodes[1], 1)
    links.append(link)

    # line1
    link = Link(1)
    edit_line.set_points_using_node(link, nodes[1], nodes[2], 1)
    links.append(link)

    # line2
    link = Link(2)
    edit_line.set_points_using_node(link,nodes[0], nodes[3], 1)
    links.append(link)

    # line3
    link = Link(3)
    edit_line.set_points_using_node(link,nodes[1], nodes[4], 1)
    links.append(link)

    # line4
    link = Link(4)
    edit_line.set_points_using_node(link,nodes[2], nodes[5], 1)
    links.append(link)

    # line5
    link = Link(5)
    edit_line.set_points_using_node(link,nodes[3], nodes[4], 1)
    links.append(link)

    # line6
    link = Link(6)
    edit_line.set_points_using_node(link,nodes[4], nodes[5], 1)
    links.append(link)

    # line7
    link = Link(7)
    edit_line.set_points_using_node(link,nodes[3], nodes[6], 1)
    links.append(link)

    # line8
    link = Link(8)
    edit_line.set_points_using_node(link,nodes[4], nodes[7], 1)
    links.append(link)

    # line9
    link = Link(9)
    edit_line.set_points_using_node(link,nodes[5], nodes[8], 1)
    links.append(link)
    
    # line10
    link = Link(10)
    edit_line.set_points_using_node(link,nodes[6], nodes[7], 1)
    links.append(link)

    # line11
    link = Link(11)
    edit_line.set_points_using_node(link,nodes[7], nodes[8], 1)
    links.append(link)

    return nodes, links


def test_sample_map(nodes, links):
    
    nodes[4].print_all_related_nodes_and_links()


    plt.figure()

    for node in nodes:
        plt.plot(node.point[0], node.point[1],
            markersize=10,
            marker='D',
            color='b')

    for line in links:
        plt.plot(line.points[:,0], line.points[:,1],
            markersize=5,
            marker='o',
            color='k')

    plt.show()


if __name__ == u'__main__':

    nodes, links = create_sample_map()
    test_sample_map(nodes, links)
    
