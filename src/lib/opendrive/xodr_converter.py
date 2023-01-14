import os 
import sys
import rtree
from lib.mgeo.class_defs.junction_set import JunctionSet
from lib.mgeo.class_defs.crosswalk_set import CrossWalkSet
from lib.mgeo.class_defs.junction import Junction
from lib.mgeo.class_defs.singlecrosswalk_set import SingleCrosswalkSet
from lib.mgeo.class_defs.singlecrosswalk import SingleCrosswalk
from lib.mgeo.class_defs.crosswalk import Crosswalk
from lib.mgeo.class_defs.surface_marking import SurfaceMarking

from lib.mgeo.class_defs.surface_marking_set import SurfaceMarkingSet

current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import time
import vtk
import re
import numpy as np
import scipy.special as sc
import scipy.spatial as sp
import itertools as it
from lib.opendrive.xodr_parser import XodrParser
from lib.opendrive.mesh_utils import *
from lib.mgeo.mesh_gen.generate_mesh import write_obj

from lib.mgeo.class_defs.lane_boundary import LaneBoundary
from lib.mgeo.class_defs.lane_boundary_set import LaneBoundarySet
from lib.mgeo.class_defs.line_set import LineSet
from lib.mgeo.class_defs.link import Link
from lib.mgeo.class_defs.node import Node
from lib.mgeo.class_defs.node_set import NodeSet
from lib.mgeo.class_defs.road_polygon import RoadPolygon
from lib.mgeo.class_defs.road_polygon_set import RoadPolygonSet
from lib.mgeo.class_defs.signal_set import SignalSet
from lib.mgeo.class_defs.signal import Signal
from lib.mgeo.class_defs.intersection_controller_set import IntersectionControllerSet
from lib.mgeo.class_defs.intersection_controller import IntersectionController
from lib.mgeo.class_defs.mgeo import MGeo
from lib.common.centroid import calculate_centroid


def list_chunk(lst, n) :
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def isPolyIntersect(poly1, poly2, z_tolerance):
    if poly1.GetNumberOfCells() <= 0 or poly2.GetNumberOfCells() <= 0 :
        return False
    poly1 = shrink_polygon(poly1)
    poly2 = shrink_polygon(poly2)

    #poly1 = vtkBoundary(poly1)
    poly1 = vtkCleanPoly(poly1)
    poly1_3d = vtkMake3D(poly1, z_tolerance/2)

    #poly2 = vtkBoundary(poly2)
    poly2 = vtkCleanPoly(poly2)
    poly2_3d = vtkMake3D(poly2, z_tolerance/2)

    collision = vtk.vtkCollisionDetectionFilter()
    collision.SetCollisionModeToFirstContact()

    transform_0 = vtk.vtkTransform()
    collision.SetInputData(0, poly1_3d)
    collision.SetTransform(0, transform_0)

    transform_1 = vtk.vtkTransform()
    collision.SetInputData(1, poly2_3d)
    collision.SetTransform(1, transform_1)
    collision.Update()
    out = collision.GetContactsOutput()
    if out.GetNumberOfCells() == 0 :
        if out.GetNumberOfPoints() != 0 :
            print(out.GetNumberOfPoints())
    if out.GetNumberOfCells() > 0 :
        return True
    return False
    
#서로 겹치는 폴리곤끼리 그룹화
def group_by_clip(road_list, z_tolerance) :
    grouped_list = list()
    clip_cnt = -1

    for road in road_list :
        group = list()
        group.append(road)
        grouped_list.append(group)

    loop_limit = 100
    loop_cnt = 0
    while clip_cnt != 0 :
        #무한루프 방지
        if loop_cnt > loop_limit :
            print("Err")
            break
        loop_cnt += 1
        clip_cnt = 0
        new_grouped_list = list()
        check_grouped_idx = list()

        for i in range(len(grouped_list)) :
            if i in check_grouped_idx :
                continue
            new_list = list()
            new_list.extend(grouped_list[i])
            check_grouped_idx.append(i)
                
            for j in range(len(grouped_list)) :
                if i==j or j in check_grouped_idx:
                    continue
                is_clip = False
                for road in grouped_list[i] :
                    for road2 in grouped_list[j] :
                        if isPolyIntersect(road[0], road2[0], z_tolerance) :
                            is_clip = True
                            break
                    if is_clip :
                        break
                
                if is_clip : 
                    check_grouped_idx.append(j)
                    new_list.extend(grouped_list[j])
                    clip_cnt+=1
                    
            new_grouped_list.append(new_list)
        grouped_list = new_grouped_list
    return grouped_list

def get_item_by_s(list, s, last_s=False):
    ret_item = None
    for list_item in list:
        chk = list_item.s > s if last_s == False else list_item.s >= s
        if chk:
            break
        ret_item = list_item
    return ret_item

def get_item_idx_by_s(list, s, last_s=False):
    i = 0
    for i in range(len(list)) :
        list_item = list[i]
        chk = list_item.s > s if last_s == False else list_item.s >= s
        if chk:
            break
    return i

def polynomial(ds, a, b, c, d):
    return (a + b*ds + c*ds*ds + d*ds*ds*ds)

def gen_tri_strips(vertex_list):
    face_list = list()

    if not len(vertex_list)%2 == 0 :
        return None

    for i in range(int(len(vertex_list)/2) - 1) :
        face_list.append([2*i, 2*i + 2, 2*i + 1])
        face_list.append([2*i + 1, 2*i + 2, 2*i + 3])

    return face_list

def merge_mesh_data(vertex_a, face_a, vertex_b, face_b):
    vertex_merged = vertex_a + vertex_b
    vertex_offset = len(vertex_a)
    for idx in range(len(face_b)) :
        for idx2 in range(len(face_b[idx])) :
            face_b[idx][idx2] += vertex_offset

    face_merged = face_a + face_b
    return vertex_merged, face_merged

def odr_spiral(s, dot):
    a = 1.0/np.sqrt(np.fabs(dot))
    a *= np.sqrt(np.pi)

    f_s, f_c = sc.fresnel(s/a)

    x = f_c * a
    y = f_s * a

    if dot < 0.0 :
        y *= -1.0

    t = s*s*dot*0.5

    return x, y, t

def rotate_x(rad) :
    return np.matrix([[1, 0, 0], [0, np.cos(rad), -np.sin(rad)], [0, np.sin(rad), np.cos(rad)]])

def rotate_z(rad) :
    return np.matrix([[np.cos(rad), -np.sin(rad), 0], [np.sin(rad), np.cos(rad), 0], [0, 0, 1]])

def superelevation(ref_p, hdg, elev, p) :
    p_elev = p - ref_p
    p_elev = rotate_z(hdg) * rotate_x(elev) * rotate_z(-hdg) * p_elev
    p_elev = p_elev + ref_p
    return p_elev.item(0,0), p_elev.item(1,0), p_elev.item(2,0)

class XodrCrosswalkItemData:
    def __init__(self, type, points):
        self.type = type
        self.points = points

class XodrStopLineItemData :
    def __init__(self, points):
        self.centroid = calculate_centroid(points)
        self.points = points

class XodrLaneNodeItemData :
    def __init__(self):
        self.point_list = list()
        self.node = Node()
    def get_node_point(self) :
        return self.node.point
        
    def add_node_point(self, point) :
        length = len(self.point_list)
        if length == 0 :
            self.node.point = np.array(point)
        else :
            self.node.point = ((self.node.point*length) + point) / (length + 1)
        self.point_list.append(point)

class XodrNodeItemData:
    def __init__(self):
        self.from_items = list()
        self.to_items = list()
        self.left_node = None
        self.right_node = None
        self.center_node = None
        self.junction_id_list = list()

    def add_from_items(self, from_item):
        if from_item not in self.from_items :
            self.from_items.append(from_item)

    def add_to_items(self, to_item):
        if to_item not in self.to_items :
            self.to_items.append(to_item)

    def set_left_node(self, left_node):
        self.left_node = left_node

    def set_right_node(self, right_node):
        self.right_node = right_node

    def set_center_node(self, center_node):
        self.center_node = center_node

class XodrSignalItemData:
    def __init__(self, name, is_dynamic, country, z_offset, width, height, heading, point, sig_type, sig_subtype, orientation, link_list, sig_value=None) :
        self.name = name
        self.dynamic = is_dynamic
        self.country = country
        self.z_offset = z_offset
        self.width = width
        self.height = height
        self.heading = heading
        self.point = point
        self.type = sig_type
        self.subtype = sig_subtype
        self.orientation = orientation
        self.link_list = link_list
        self.mgeo_signal = None
        self.value = sig_value

class XodrSurfaceMarkingData:
    def __init__(self, name, points, type, subtype, lane_item_key) :
        self.name = name
        self.points = points
        self.type = type
        self.subtype = subtype
        self.lane_item_key = lane_item_key

class XodrLaneItemData:
    def __init__(self, road_id, lane_section_idx, lane_id, lane_type, left_vertices, right_vertices, center_vertices, ref_vertices, left_lane_item, right_lane_item, can_move_left, can_move_right, max_speed, junction_id="-1"):
        self.road_id = road_id
        self.lane_section_idx = lane_section_idx
        self.lane_id = lane_id
        self.lane_type = lane_type
        self.left_vertices = left_vertices
        self.right_vertices = right_vertices
        self.center_vertices = center_vertices
        self.ref_vertices = ref_vertices
        self.left_lane_item = left_lane_item
        self.right_lane_item = right_lane_item
        self.predecessor_list = list()
        self.successor_list = list()
        self.left_lanemarking = None
        self.right_lanemarking = None
        self.lane_link = None
        self.center_start_node = None
        self.center_end_node = None
        self.can_move_left = can_move_left
        self.can_move_right = can_move_right
        self.max_speed = max_speed
        self.center_vtx_s_idx = 0
        self.center_vtx_e_idx = len(center_vertices)

        self.junction_id = junction_id
        self.lane_type_set = None

    def add_predecessor(self, item_id):
        if item_id in self.predecessor_list:
            return
        self.predecessor_list.append(item_id)

    def add_successor(self, item_id):
        if item_id in self.successor_list:
            return
        self.successor_list.append(item_id)

    def remove_predecessor(self, item_id):
        if item_id in self.predecessor_list :
            self.predecessor_list.remove(item_id)

    def remove_successor(self, item_id) :
        if item_id in self.successor_list :
            self.successor_list.remove(item_id)

    def set_left_lanemarking(self, lanemarking):
        self.left_lanemarking = lanemarking

    def set_right_lanemarking(self, lanemarking):
        self.right_lanemarking = lanemarking

    def set_lane_link(self, lane_link):
        self.lane_link = lane_link

    def set_center_start_node(self, start_node):
        self.center_start_node = start_node

    def set_center_end_node(self, end_node):
        self.center_end_node = end_node

class XodrExtraObjectInfo :
    def __init__(self, xodr_obj):
        self.roadEdge_type = 0
        self.roadMark_type = 0
        self.roadMark_subtype = 0

        if xodr_obj.type == "roadEdge" :
            for user_data in xodr_obj.userdata_list :
                if user_data.code == "RE_TYPE" :
                    self.roadEdge_type = int(user_data.value)
        if xodr_obj.type == "roadMark" :
            for user_data in xodr_obj.userdata_list :
                if user_data.code == "RM_TYPE" :
                    self.roadMark_type = int(user_data.value)
                elif user_data.code == "RM_S_TYPE" :
                    self.roadMark_subtype = int(user_data.value)

class XodrConverter:
    def __init__(self, xodr_file_path):
        self.xodr_file_path = xodr_file_path
        self.sidewalk_height = 0.0
        self.lanemarking_height = 0.03
        self.vertex_distance = 2.0
        self.z_tolerance = 0.1
        self.lane_item_dict = dict()
        self.sig_item_dict = dict()
        self.sm_item_dict = dict()
        self.dir = "right"
        self.road_dict = dict()
        self.controller_dict = dict()
        self.lanemarking_dict = dict()
        self.geo_reference = None
        self.extra_lanemarking = dict()
        self.extra_lanemarking_info = dict()
        self.crosswalk_dict = dict()
        self.union_junction = True
        self.clean_link = False
        self.project_lm = False
        self.stop_line_dict = dict()
        #--------두 list 인덱스 같게 유지할 것-------
        self.lanenode_KDTreeData = list()
        self.lanenode_data = list()
        #------------------------------------------

        #--------두 list 인덱스 같게 유지할 것-------
        self.node_KDTreeData = list()
        self.node_data = list()
        #------------------------------------------

    def set_project_lm(self, project_lm) :
        self.project_lm = project_lm

    def set_traffic_direction(self, dir):
        self.dir = dir
        
    def set_vertex_distance(self, dist):
        self.vertex_distance = dist

    def set_sidewalk_height(self, height):
        self.sidewalk_height = height

    def set_lanemarking_height(self, height):
        self.lanemarking_height = height
    
    def set_z_tolerance(self, z_tolerance):
        self.z_tolerance = z_tolerance

    def set_union_junction(self, union_junction):
        self.union_junction = union_junction

    def set_clean_link(self, clean_link):
        self.clean_link = clean_link

    def set_generate_mesh(self, gen_mesh) :
        self.generate_mesh = gen_mesh

    def get_lane_offset(self, road, lane_list, lane_id, lane_section_s, current_s_offset, is_last=False) :
        current_s = lane_section_s + current_s_offset
        lane_offset = float(0)
        if lane_id != 0 :
            #lane_list 는 id 기준으로 정렬되어있음
            for lane in lane_list:
                #lane width 계산
                lane_width_item = get_item_by_s(lane.width_list, current_s_offset)
                lane_width = polynomial(current_s_offset - lane_width_item.s, lane_width_item.a, lane_width_item.b, lane_width_item.c, lane_width_item.d)

                if np.abs(lane_width) < np.finfo(float).eps :
                    lane_width = np.finfo(float).eps

                if lane_width < 0 : 
                    lane_width = -lane_width                    

                lane_offset += lane_width

                if lane.id == lane_id:
                    break

        #laneOffset 계산
        extra_lane_offset = float(0)
        lane_offset_item = get_item_by_s(road.lane_offset_list, current_s, is_last)
        if not lane_offset_item == None :
            extra_lane_offset = polynomial(current_s - lane_offset_item.s, lane_offset_item.a, lane_offset_item.b, lane_offset_item.c, lane_offset_item.d)

        offset = float(0)
        if int(lane_id) < 0 : 
            offset = lane_offset - extra_lane_offset
        else :
            offset = lane_offset + extra_lane_offset
        return offset

    def apply_superelevation(self, road, ref_point_info, current_s, left_point, right_point) :
        ref_point = ref_point_info[0]
        hdg = ref_point_info[1]
        ref_x = ref_point[0]
        ref_y = ref_point[1]
        ref_z = ref_point[2]

        #super elevation
        super_elev_item = get_item_by_s(road.super_elevation_list, current_s)
        if super_elev_item != None :
            super_elev = polynomial(current_s - super_elev_item.s, super_elev_item.a, super_elev_item.b, super_elev_item.c, super_elev_item.d)
            p_ref = np.array([[ref_x], [ref_y], [ref_z]])

            p_right = np.array([[right_point[0]], [right_point[1]], [right_point[2]]])
            p_left = np.array([[left_point[0]], [left_point[1]], [left_point[2]]])

            pos_x_right, pos_y_right, pos_z_right = superelevation(p_ref, hdg, super_elev, p_right)
            pos_x_left, pos_y_left, pos_z_left = superelevation(p_ref, hdg, super_elev, p_left)

            right_point = [pos_x_right, pos_y_right, pos_z_right]
            left_point = [pos_x_left, pos_y_left, pos_z_left]

        return left_point, right_point

    def gen_lanemarking_vertices(self, road, lane_section_idx, lane_list, lane_section_s, length, side, vertex_dict, has_left=False, has_right=False) :
        vertex_distance = 1.0
        double_line_interval = 0.1
        broken_line_length = 3
        broken_line_interval = 3
        length_threshold = 0.5
        default_roadmark_width = 0.15

        for lane in lane_list :
            for roadmark_idx in range(len(lane.road_mark_list)) :
                roadmark = lane.road_mark_list[roadmark_idx]
                roadmark_width = roadmark.width
                if roadmark.color == "none" :
                    continue
                if roadmark.width is None or roadmark.width == 0.0 :
                    roadmark_width = default_roadmark_width

                roadmark_length = float(0.0)
                if roadmark_idx == len(lane.road_mark_list) - 1 :
                    roadmark_length = length - roadmark.s
                else :
                    roadmark_next = lane.road_mark_list[roadmark_idx + 1]
                    roadmark_length = roadmark_next.s - roadmark.s

                if lane_section_s + roadmark_length > length :
                    roadmark_length = length - roadmark.s
                    #print("s exceeded : road_id : {}, lanesection_idx : {}, lane_id : {}".format(road.id, lane_section_s, lane.id))

                if roadmark_length < length_threshold :
                    continue

                if roadmark.type not in ["solid", "broken", "solid solid", "solid broken", "broken solid", "broken broken"]:
                    continue

                lanemarking_vertices_0 = list()
                lanemarking_vertices_1 = list()

                loop_total_cnt = int(np.ceil(roadmark_length/vertex_distance)) + 1

                for loop_cnt in range(loop_total_cnt):
                    break_flag = False
                    loop_offset = loop_cnt * vertex_distance
                    if loop_cnt == loop_total_cnt-1 :
                        loop_offset = roadmark_length
                    elif loop_cnt == loop_total_cnt-2 :
                        #마지막 포인트가 가까이 있으면 붙여준다
                        if roadmark_length - loop_offset < length_threshold :
                            loop_offset = roadmark_length
                            break_flag = True

                    current_s_offset = roadmark.s + loop_offset
                    ref_point_info = self.get_point(road, lane_section_s + current_s_offset, 0)
                    current_s = lane_section_s + current_s_offset

                    lane_offset = self.get_lane_offset(road, lane_list, lane.id, lane_section_s, current_s_offset, current_s_offset==length)
                    if lane.id == lane_list[-1].id :
                        if side == "left" or (side == "center" and has_right == False and has_left == True) :
                            lane_offset += 0.2
                        elif side == "right" or (side == "center" and has_right == True and has_left == False) :
                            lane_offset -= 0.2
                    #else :
                        #if side == "right" :
                            #lane_offset += 0.2
                        #elif side == "left" :
                            #lane_offset -= 0.2
                    if roadmark.type in ["solid", "broken"] :
                        t_left = lane_offset + (roadmark_width/2)
                        t_right = lane_offset - (roadmark_width/2)
                        if side == "right" :
                            t_left, t_right = -t_right, -t_left

                        right_point = (self.get_point(road, lane_section_s + current_s_offset, t_right))[0]
                        left_point = (self.get_point(road, lane_section_s + current_s_offset, t_left))[0]

                        left_point, right_point = self.apply_superelevation(road, ref_point_info, current_s, left_point, right_point)

                        right_point[2] = right_point[2] + self.lanemarking_height
                        left_point[2] = left_point[2] + self.lanemarking_height

                        lanemarking_vertices_0.append(right_point)
                        lanemarking_vertices_0.append(left_point)

                    elif roadmark.type in ["solid solid", "solid broken", "broken solid", "broken broken"] :
                        #0이 바깥쪽, 1이 안쪽
                        t_left_0 = lane_offset + roadmark_width + (double_line_interval/2)
                        t_right_0 = lane_offset + (double_line_interval/2)
                        t_left_1 = lane_offset - (double_line_interval/2)
                        t_right_1 = lane_offset - roadmark_width - (double_line_interval/2)
                        if side == "right" :
                            t_left_0, t_right_0 = -t_right_0, -t_left_0
                            t_left_1, t_right_1 = -t_right_1, -t_left_1

                        right_point_0 = (self.get_point(road, lane_section_s + current_s_offset, t_right_0))[0]
                        left_point_0 = (self.get_point(road, lane_section_s + current_s_offset, t_left_0))[0]
                        left_point_0, right_point_0 = self.apply_superelevation(road, ref_point_info, current_s, left_point_0, right_point_0)

                        right_point_0[2] = right_point_0[2] + self.lanemarking_height
                        left_point_0[2] = left_point_0[2] + self.lanemarking_height

                        lanemarking_vertices_0.append(right_point_0)
                        lanemarking_vertices_0.append(left_point_0)

                        right_point_1 = (self.get_point(road, lane_section_s + current_s_offset, t_right_1))[0]
                        left_point_1 = (self.get_point(road, lane_section_s + current_s_offset, t_left_1))[0]
                        left_point_1, right_point_1 = self.apply_superelevation(road, ref_point_info, current_s, left_point_1, right_point_1)
                        
                        right_point_1[2] = right_point_1[2] + self.lanemarking_height
                        left_point_1[2] = left_point_1[2] + self.lanemarking_height

                        lanemarking_vertices_1.append(right_point_1)
                        lanemarking_vertices_1.append(left_point_1)
                    if break_flag :
                        break

                roadmark_vertices = list()
                roadmark_types = roadmark.type.split()
                roadmark_type_0 = None
                roadmark_type_1 = None
                if len(roadmark_types) == 1 :
                    roadmark_type_0 = roadmark_types[0]
                elif len(roadmark_types) == 2 :
                    roadmark_type_0 = roadmark_types[0]
                    roadmark_type_1 = roadmark_types[1]

                if roadmark_type_0 != None and len(lanemarking_vertices_0) >= 4 :
                    if roadmark_type_0 == "solid" :
                        roadmark_vertices.append(lanemarking_vertices_0)
                    elif roadmark_type_0 == "broken" :
                        vertex_cnt = 2*(int(np.ceil(broken_line_interval/vertex_distance)) + 1)
                        interval_cnt = 2*(int(np.ceil(broken_line_length/vertex_distance)) - 1)
                        if interval_cnt < 0 :
                            interval_cnt = 0

                        vertices_chunk = list_chunk(lanemarking_vertices_0, vertex_cnt + interval_cnt)
                        for vertices in vertices_chunk :
                            rm_vertices = vertices[0:vertex_cnt]
                            if len(rm_vertices) < 4 or int(len(rm_vertices)/2 - 1) <= int(np.ceil((vertex_cnt/2 - 1)/2)) :
                                continue
                            roadmark_vertices.append(vertices[0:vertex_cnt])

                if roadmark_type_1 != None and len(lanemarking_vertices_1) >= 4 :
                    if roadmark_type_1 == "solid" :
                        roadmark_vertices.append(lanemarking_vertices_1)
                    elif roadmark_type_1 == "broken" :
                        vertex_cnt = 2*(int(np.ceil(broken_line_interval/vertex_distance)) + 1)
                        interval_cnt = 2*(int(np.ceil(broken_line_length/vertex_distance)) - 1)
                        if interval_cnt < 0 :
                            interval_cnt = 0

                        vertices_chunk = list_chunk(lanemarking_vertices_1, vertex_cnt + interval_cnt)
                        for vertices in vertices_chunk :
                            rm_vertices = vertices[0:vertex_cnt]
                            if len(rm_vertices) < 4 or int(len(rm_vertices)/2 - 1) <= int(np.ceil((vertex_cnt/2 - 1)/2)) :
                                continue
                            roadmark_vertices.append(vertices[0:vertex_cnt])

                if len(roadmark_vertices) > 0 :
                    dict_key = (road.id, lane_section_idx, lane.id)
                    if dict_key not in vertex_dict :
                        vertex_dict[dict_key] = list()
                    vertex_dict[dict_key].append([roadmark.color, roadmark_vertices])
        
        return vertex_dict

    def get_geo_point_line(self, geometry_item, geo_s_begin, geo_s_end) :
        point_list = list()

        len_total = geo_s_end - geo_s_begin

        loop_cnt = int(np.ceil(len_total/self.vertex_distance)) + 1
        s_offset = geo_s_begin

        hdg = geometry_item.hdg

        for i in range(loop_cnt) :
            if s_offset > geo_s_end :
                s_offset = geo_s_end
            eps = 0.0
            if geometry_item.length == geo_s_end and i == loop_cnt - 1 :
                eps = -np.finfo(float).eps
            pos_x = geometry_item.x + np.cos(hdg) * s_offset
            pos_y = geometry_item.y + np.sin(hdg) * s_offset

            remain_length = geo_s_end - s_offset
            if not (i >= 1 and i == loop_cnt - 2 and remain_length < self.vertex_distance/4) :
                point_list.append([geometry_item.s + s_offset, hdg, pos_x, pos_y, eps])

            s_offset += self.vertex_distance
            
        return point_list

    def get_geo_point_arc(self, geometry_item, geo_s_begin, geo_s_end) :
        point_list = list()
        radius = 1.0/geometry_item.arc_curvature

        len_total = geo_s_end - geo_s_begin

        loop_cnt = int(np.ceil(len_total/self.vertex_distance)) + 1
        s_offset = geo_s_begin

        for i in range(loop_cnt) :
            if s_offset > geo_s_end :
                s_offset = geo_s_end

            eps = 0.0
            if geometry_item.length == geo_s_end and i == loop_cnt - 1 :
                eps = -np.finfo(float).eps

            hdg = geometry_item.hdg + s_offset * geometry_item.arc_curvature
            pos_x = geometry_item.x + radius*(np.cos(geometry_item.hdg + np.pi/2.0) - np.cos(hdg + np.pi/2.0))
            pos_y = geometry_item.y + radius*(np.sin(geometry_item.hdg + np.pi/2.0) - np.sin(hdg + np.pi/2.0))

            #마지막 구간이 짧으면 안넣도록
            remain_length = geo_s_end - s_offset
            if not (i >= 1 and i == loop_cnt - 2 and remain_length < self.vertex_distance/4) :
                point_list.append([geometry_item.s + s_offset, hdg, pos_x, pos_y, eps])
            
            s_offset += self.vertex_distance

        return point_list

    def get_geo_point_spiral(self, geometry_item, geo_s_begin, geo_s_end) :
        point_list = list()

        len_total = geo_s_end - geo_s_begin

        loop_cnt = int(np.ceil(len_total/self.vertex_distance)) + 1
        s_offset = geo_s_begin

        for i in range(loop_cnt) :
            if s_offset > geo_s_end :
                s_offset = geo_s_end
                
            eps = 0.0
            if geometry_item.length == geo_s_end and i == loop_cnt - 1 :
                eps = -np.finfo(float).eps

            curve_dot = (geometry_item.spiral_curvEnd - geometry_item.spiral_curvStart) / geometry_item.length
            spiral_s_o = geometry_item.spiral_curvStart / curve_dot
            spiral_s = s_offset + spiral_s_o

            x, y, t = odr_spiral(spiral_s, curve_dot)
            x_o, y_o, t_o = odr_spiral(spiral_s_o, curve_dot)

            x = x - x_o
            y = y - y_o
            t = t - t_o

            angle = geometry_item.hdg - t_o
            pos_x = geometry_item.x + x * np.cos(angle) - y * np.sin(angle)
            pos_y = geometry_item.y + y * np.cos(angle) + x * np.sin(angle)
            hdg = geometry_item.hdg + t

            #마지막 구간이 짧으면 안넣도록
            remain_length = geo_s_end - s_offset
            if not (i >= 1 and i == loop_cnt - 2 and remain_length < self.vertex_distance/4) :
                point_list.append([geometry_item.s + s_offset, hdg, pos_x, pos_y, eps])

            s_offset += self.vertex_distance

        return point_list

    def get_geo_point_paramPoly3(self, geometry_item, geo_s_begin, geo_s_end) :
        point_list = list()

        len_total = geo_s_end - geo_s_begin

        loop_cnt = int(np.ceil(len_total/self.vertex_distance)) + 1
        s_offset = geo_s_begin

        for i in range(loop_cnt) :
            if s_offset > geo_s_end :
                s_offset = geo_s_end

            eps = 0.0
            if geometry_item.length == geo_s_end and i == loop_cnt - 1 :
                eps = -np.finfo(float).eps

            bU = geometry_item.paramPoly3_bU
            cU = geometry_item.paramPoly3_cU
            dU = geometry_item.paramPoly3_dU
            bV = geometry_item.paramPoly3_bV
            cV = geometry_item.paramPoly3_cV
            dV = geometry_item.paramPoly3_dV

            u,v,p = geometry_item.get_point_by(s_offset)
            tan = (bV + 2*cV*p + 3*dV*p*p) / (bU + 2*cU*p + 3*dU*p*p)
            hdg_uv = np.arctan2(tan, 1.0)

            hdg = hdg_uv + geometry_item.hdg
            pos_x = geometry_item.x + u * np.cos(geometry_item.hdg) - v * np.sin(geometry_item.hdg)
            pos_y = geometry_item.y + v * np.cos(geometry_item.hdg) + u * np.sin(geometry_item.hdg)

            #마지막 구간이 짧으면 안넣도록
            remain_length = geo_s_end - s_offset
            if not (i >= 1 and i == loop_cnt - 2 and remain_length < self.vertex_distance/4) :
                point_list.append([geometry_item.s + s_offset, hdg, pos_x, pos_y, eps])

            s_offset += self.vertex_distance

        return point_list


    #작업중 코드
    def gen_lane_vertices2(self, road, lane_list, lane_section_s, length, side) :
        if len(lane_list) == 0 :
            return dict()
        geo_point_list = list()

        for geometry_item in road.geometry_list :
            geo_s_begin = 0
            geo_s_end = geometry_item.length
            if (geometry_item.s + geometry_item.length) <= lane_section_s :
                continue
            elif geometry_item.s >= lane_section_s + length :
                break
            else :
                if geometry_item.s < lane_section_s :
                    geo_s_begin = lane_section_s - geometry_item.s
                if geometry_item.s + geometry_item.length > lane_section_s + length :
                    geo_s_end = lane_section_s + length - geometry_item.s

            if geometry_item.geo_type == "line":
                geo_point_list.append(self.get_geo_point_line(geometry_item, geo_s_begin, geo_s_end))
            elif geometry_item.geo_type == "arc":
                geo_point_list.append(self.get_geo_point_arc(geometry_item, geo_s_begin, geo_s_end))
            elif geometry_item.geo_type == "sprial":
                geo_point_list.append(self.get_geo_point_spiral(geometry_item, geo_s_begin, geo_s_end))
            elif geometry_item.geo_type == "poly3":
                """
                TODO : poly3
                """
            elif geometry_item.geo_type == "paramPoly3":
                geo_point_list.append(self.get_geo_point_paramPoly3(geometry_item, geo_s_begin, geo_s_end))

        ref_points = list()
        for i in range(len(geo_point_list)) :
                        
            if i == len(geo_point_list) - 1 :
                ref_points.extend(geo_point_list[i])
            else :
                ref_points.extend(geo_point_list[i][:-1])
            """

            if i == 0 :
                ref_points.extend(geo_point_list[i][:-1])
            else :
                cur_points = geo_point_list[i]
                prev_points = geo_point_list[i - 1]

                cur_s = cur_points[0][0] + cur_points[0][3]
                prev_s = prev_points[-1][0] + prev_points[-1][3]
                mean_s = (cur_s + prev_s) / 2

                cur_hdg = cur_points[0][1]
                prev_hdg = prev_points[-1][1]
                mean_hdg = np.arctan2(np.sin(cur_hdg) + np.sin(prev_hdg), np.cos(cur_hdg) + np.cos(prev_hdg))

                cur_coord = [cur_points[0][2], cur_points[0][3]]
                prev_coord = [prev_points[-1][2], prev_points[-1][3]]
                mean_coord = [(cur_coord[0] + prev_coord[0]) / 2, (cur_coord[1] + prev_coord[1]) / 2]
                
                ref_points.append([mean_s, mean_hdg, mean_coord[0], mean_coord[1], 0.0])
                ref_points.extend(geo_point_list[i][1:-1])

            if i == len(geo_point_list) - 1 :
                ref_points.append(geo_point_list[i][-1])
            """

        lane_vertex_dict = dict()
        for i in range(len(ref_points)) :
            ref_point = ref_points[i]

            last_s = False
            if i == len(ref_points) - 1 :
                last_s = True

            ref_s = ref_point[0]
            ref_hdg = ref_point[1]
            ref_x = ref_point[2]
            ref_y = ref_point[3]
            ref_z = float(0.0)
            eps = ref_point[4]

            lane_s_offset = ref_s - lane_section_s

            #elevation 계산
            elevation_item = get_item_by_s(road.elevation_list, ref_s + eps, last_s)
            if not elevation_item == None:
                ref_z += polynomial(ref_s - elevation_item.s, elevation_item.a, elevation_item.b, elevation_item.c, elevation_item.d)

            #laneOffset 계산
            lane_offset_item = get_item_by_s(road.lane_offset_list, ref_s + eps, last_s)
            if not lane_offset_item == None :
                extra_lane_offset = polynomial(ref_s - lane_offset_item.s, lane_offset_item.a, lane_offset_item.b, lane_offset_item.c, lane_offset_item.d)
                ref_x = ref_x + extra_lane_offset * (-np.sin(ref_hdg))
                ref_y = ref_y + extra_lane_offset * (np.cos(ref_hdg))

            lane_offset = float(0.0)
            for lane in lane_list:
                if lane.id not in lane_vertex_dict :
                    lane_vertex_dict[lane.id] = list()
                #height 계산
                pos_z_inside = ref_z
                pos_z_outside = ref_z
                height_item = get_item_by_s(lane.height_list, lane_s_offset)
                if not height_item == None :
                    pos_z_inside += height_item.inner
                    pos_z_outside += height_item.outer

                if (self.sidewalk_height != 0.0) and (lane.type == "sidewalk"):
                    pos_z_inside += self.sidewalk_height
                    pos_z_outside += self.sidewalk_height

                #lane width 계산
                lane_width_item = get_item_by_s(lane.width_list, lane_s_offset)
                lane_width = polynomial(lane_s_offset - lane_width_item.s, lane_width_item.a, lane_width_item.b, lane_width_item.c, lane_width_item.d)
                

                if np.abs(lane_width) < np.finfo(float).eps :
                    lane_width = np.finfo(float).eps    

                if lane_width < 0 : 
                    lane_width = -lane_width

                #lane 의 양쪽 좌표 계산
                x_factor = -1 if side == "left" else 1
                y_factor = 1 if side == "left" else -1
                pos_x_inside = ref_x + lane_offset * (np.sin(ref_hdg)) * x_factor
                pos_y_inside = ref_y + lane_offset * (np.cos(ref_hdg)) * y_factor

                pos_x_outside = ref_x + (lane_offset + lane_width) * (np.sin(ref_hdg)) * x_factor
                pos_y_outside = ref_y + (lane_offset + lane_width) * (np.cos(ref_hdg)) * y_factor

                #super elevation
                super_elev_item = get_item_by_s(road.super_elevation_list, ref_s + eps, last_s)
                if super_elev_item != None :
                    super_elev = polynomial(ref_s - super_elev_item.s, super_elev_item.a, super_elev_item.b, super_elev_item.c, super_elev_item.d)
                    p_ref = np.array([[ref_x], [ref_y], [ref_z]])
                    p_inside = np.array([[pos_x_inside], [pos_y_inside], [pos_z_inside]])
                    p_outside = np.array([[pos_x_outside], [pos_y_outside], [pos_z_outside]])

                    pos_x_inside, pos_y_inside, pos_z_inside = superelevation(p_ref, ref_hdg, super_elev, p_inside)
                    pos_x_outside, pos_y_outside, pos_z_outside = superelevation(p_ref, ref_hdg, super_elev, p_outside)
                
                pos_inside = [round(pos_x_inside, 12), round(pos_y_inside, 12), round(pos_z_inside, 12)]
                pos_outside = [round(pos_x_outside, 12), round(pos_y_outside, 12), round(pos_z_outside, 12)]

                #일정한 방향으로 Triangle strip 을 만들기 위해 : 오른쪽 -> 왼쪽 순서로 넣는다
                if side == "left" :
                    lane_vertex_dict[lane.id].append(pos_inside)
                    lane_vertex_dict[lane.id].append(pos_outside)
                else :
                    lane_vertex_dict[lane.id].append(pos_outside)
                    lane_vertex_dict[lane.id].append(pos_inside)

                lane_offset += lane_width

        return lane_vertex_dict
        
    def gen_lane_vertices(self, road, lane_list, lane_section_s, length, side) :
        vertex_distance = self.vertex_distance
        #if road.id in ["19730"] :
            #vertex_distance = vertex_distance/2
        #elif road.id in ["13714", "1668"] :
            #vertex_distance = 2.5
        loop_total_cnt = int(np.ceil(length/vertex_distance)) + 1
        current_s_offset = 0
        lane_vertex_dict = dict()

        for lane in lane_list:
            lane_vertex_dict[lane.id] = list()

        for loop_cnt in range(loop_total_cnt):
            last_s = False

            if current_s_offset > length :
                current_s_offset = length
            if loop_cnt == (loop_total_cnt-1) :
                last_s = True

            lane_offset = float(0)
            #lane_list 는 id 기준으로 정렬되어있음
            for lane in lane_list:
                current_s = lane_section_s + current_s_offset

                geometry_item = get_item_by_s(road.geometry_list, current_s, last_s)
                geometry_s_offset = current_s - geometry_item.s
                pos_x = float(0)
                pos_y = float(0)
                pos_z = float(0)
                hdg = float(0)

                #reference line 좌표 계산
                if geometry_item.geo_type == "line":
                    hdg = geometry_item.hdg
                    pos_x = geometry_item.x + np.cos(hdg) * geometry_s_offset
                    pos_y = geometry_item.y + np.sin(hdg) * geometry_s_offset
                elif geometry_item.geo_type == "arc":
                    radius = 1.0/geometry_item.arc_curvature
                    hdg = geometry_item.hdg + geometry_s_offset * geometry_item.arc_curvature
                    pos_x = geometry_item.x + radius*(np.cos(geometry_item.hdg + np.pi/2.0) - np.cos(hdg + np.pi/2.0))
                    pos_y = geometry_item.y + radius*(np.sin(geometry_item.hdg + np.pi/2.0) - np.sin(hdg + np.pi/2.0))
                elif geometry_item.geo_type is "spiral":
                    curve_dot = (geometry_item.spiral_curvEnd - geometry_item.spiral_curvStart) / geometry_item.length
                    spiral_s_o = geometry_item.spiral_curvStart / curve_dot
                    spiral_s = geometry_s_offset + spiral_s_o

                    x, y, t = odr_spiral(spiral_s, curve_dot)
                    x_o, y_o, t_o = odr_spiral(spiral_s_o, curve_dot)

                    x = x - x_o
                    y = y - y_o
                    t = t - t_o

                    angle = geometry_item.hdg - t_o
                    pos_x = geometry_item.x + x * np.cos(angle) - y * np.sin(angle)
                    pos_y = geometry_item.y + y * np.cos(angle) + x * np.sin(angle)
                    hdg = geometry_item.hdg + t
                elif geometry_item.geo_type is "poly3":
                    """
                    TODO : poly3
                    """
                elif geometry_item.geo_type is "paramPoly3":
                    bU = geometry_item.paramPoly3_bU
                    cU = geometry_item.paramPoly3_cU
                    dU = geometry_item.paramPoly3_dU
                    bV = geometry_item.paramPoly3_bV
                    cV = geometry_item.paramPoly3_cV
                    dV = geometry_item.paramPoly3_dV

                    u,v,p = geometry_item.get_point_by(geometry_s_offset)
                    tan = (bV + 2*cV*p + 3*dV*p*p) / (bU + 2*cU*p + 3*dU*p*p)
                    hdg_uv = np.arctan2(tan, 1.0)

                    hdg = hdg_uv + geometry_item.hdg
                    pos_x = geometry_item.x + u * np.cos(geometry_item.hdg) - v * np.sin(geometry_item.hdg)
                    pos_y = geometry_item.y + v * np.cos(geometry_item.hdg) + u * np.sin(geometry_item.hdg)

                #elevation 계산
                elevation_item = get_item_by_s(road.elevation_list, current_s, last_s)
                if not elevation_item == None:
                    pos_z += polynomial(current_s - elevation_item.s, elevation_item.a, elevation_item.b, elevation_item.c, elevation_item.d)

                #reference point
                ref_x = pos_x
                ref_y = pos_y
                ref_z = pos_z

                #laneOffset 계산
                lane_offset_item = get_item_by_s(road.lane_offset_list, current_s, last_s)
                if not lane_offset_item == None :
                    extra_lane_offset = polynomial(current_s - lane_offset_item.s, lane_offset_item.a, lane_offset_item.b, lane_offset_item.c, lane_offset_item.d)
                    pos_x = pos_x + extra_lane_offset * (-np.sin(hdg))
                    pos_y = pos_y + extra_lane_offset * (np.cos(hdg))

                #height 계산
                pos_z_inside = pos_z
                pos_z_outside = pos_z
                height_item = get_item_by_s(lane.height_list, current_s_offset)
                if not height_item == None :
                    pos_z_inside += height_item.inner
                    pos_z_outside += height_item.outer
    
                if (self.sidewalk_height != 0.0) and (lane.type == "sidewalk"):
                    pos_z_inside += self.sidewalk_height
                    pos_z_outside += self.sidewalk_height

                #lane width 계산
                lane_width_item = get_item_by_s(lane.width_list, current_s_offset)
                lane_width = polynomial(current_s_offset - lane_width_item.s, lane_width_item.a, lane_width_item.b, lane_width_item.c, lane_width_item.d)

                if np.abs(lane_width) < np.finfo(float).eps :
                    lane_width = np.finfo(float).eps    

                if lane_width < 0 : 
                    lane_width = -lane_width
                    #print("minus width : road_id : {}, lane_id : {}, sOffset : {}".format(road.id, lane.id, current_s_offset))

                #lane 의 양쪽 좌표 계산
                x_factor = -1 if side == "left" else 1
                y_factor = 1 if side == "left" else -1

                pos_x_inside = pos_x + lane_offset * (np.sin(hdg)) * x_factor
                pos_y_inside = pos_y + lane_offset * (np.cos(hdg)) * y_factor

                pos_x_outside = pos_x + (lane_offset + lane_width) * (np.sin(hdg)) * x_factor
                pos_y_outside = pos_y + (lane_offset + lane_width) * (np.cos(hdg)) * y_factor

                #super elevation
                super_elev_item = get_item_by_s(road.super_elevation_list, current_s, last_s)
                if super_elev_item != None :
                    super_elev = polynomial(current_s - super_elev_item.s, super_elev_item.a, super_elev_item.b, super_elev_item.c, super_elev_item.d)
                    p_ref = np.array([[ref_x], [ref_y], [ref_z]])
                    p_inside = np.array([[pos_x_inside], [pos_y_inside], [pos_z_inside]])
                    p_outside = np.array([[pos_x_outside], [pos_y_outside], [pos_z_outside]])

                    pos_x_inside, pos_y_inside, pos_z_inside = superelevation(p_ref, hdg, super_elev, p_inside)
                    pos_x_outside, pos_y_outside, pos_z_outside = superelevation(p_ref, hdg, super_elev, p_outside)
                
                pos_inside = [round(pos_x_inside, 12), round(pos_y_inside, 12), round(pos_z_inside, 12)]
                pos_outside = [round(pos_x_outside, 12), round(pos_y_outside, 12), round(pos_z_outside, 12)]

                #일정한 방향으로 Triangle strip 을 만들기 위해 : 오른쪽 -> 왼쪽 순서로 넣는다
                if side == "left" :
                    lane_vertex_dict[lane.id].append(pos_inside)
                    lane_vertex_dict[lane.id].append(pos_outside)
                else :
                    lane_vertex_dict[lane.id].append(pos_outside)
                    lane_vertex_dict[lane.id].append(pos_inside)

                lane_offset += lane_width

            current_s_offset += vertex_distance

        return lane_vertex_dict

    def to_linked_lane_id(self, current_lane_id, linked_lane_id, lane_marking_idx, is_equal_direction) :
        if not linked_lane_id == None :
            is_change = False
            is_diff_side = (linked_lane_id > 0 and current_lane_id < 0) or (linked_lane_id < 0 and current_lane_id > 0)
            if is_diff_side :
                is_change = not is_change

            if lane_marking_idx == 0 : 
                is_change = not is_change

            if not is_equal_direction :
                is_change = not is_change

            if is_change :
                if linked_lane_id < 0 :
                    linked_lane_id += 1
                elif linked_lane_id > 0 :
                    linked_lane_id -= 1
        return linked_lane_id

    def find_linked_lane_id(self, current_lane, lane_marking_idx, find_type, is_equal_direction) :
        linked_lane_id = None
        if not current_lane == None :
            if find_type == "predecessor" :
                linked_lane_id = current_lane.predecessor
            else :
                linked_lane_id = current_lane.successor

        linked_lane_id = self.to_linked_lane_id(current_lane.id, linked_lane_id, lane_marking_idx, is_equal_direction)

        return linked_lane_id

    def find_linked_lane(self, road_dict, junction_dict, lanemarking_key):
        road_id = lanemarking_key[0]
        lane_section_idx = lanemarking_key[1]
        lane_id = lanemarking_key[2]

        current_lane = None
        pre_lane_key_list = list()
        suc_lane_key_list = list()

        if lane_id > 0 :
            lane_list = road_dict[road_id].lane_section_list[lane_section_idx].left_lane_list
            for lane in lane_list :
                if lane.id == lane_id :
                    current_lane = lane
                    break
        elif lane_id < 0 :
            lane_list = road_dict[road_id].lane_section_list[lane_section_idx].right_lane_list
            for lane in lane_list :
                if lane.id == lane_id :
                    current_lane = lane
                    break
        else :
            if len(road_dict[road_id].lane_section_list[lane_section_idx].left_lane_list) > 0 :
                current_lane = road_dict[road_id].lane_section_list[lane_section_idx].left_lane_list[0]
            elif len(road_dict[road_id].lane_section_list[lane_section_idx].right_lane_list) > 0 :
                current_lane = road_dict[road_id].lane_section_list[lane_section_idx].right_lane_list[0]

        #predecessor
        #lane_section 간의 연결인 경우
        if lane_section_idx > 0 :
            pre_road_id = road_id
            pre_lane_section_idx = lane_section_idx - 1
            pre_lane_id = self.find_linked_lane_id(current_lane, lane_id, "predecessor", True)

            if not pre_lane_id == None :
                pre_lane_key = (pre_road_id, pre_lane_section_idx, pre_lane_id, "end")
                pre_lane_key_list.append(pre_lane_key)
        #road 또는 junction 과의 연결
        else:
            if not road_dict[road_id].predecessor == None :
                pre_type = road_dict[road_id].predecessor.elementType
                pre_contact_point = road_dict[road_id].predecessor.contactPoint

                if pre_type == "road" and (not pre_contact_point == None):
                    pre_road_id = road_dict[road_id].predecessor.elementId
                    if pre_contact_point == "start" :
                        pre_lane_section_idx = 0
                        is_equal_direction = False
                    else :
                        pre_lane_section_idx = len(road_dict[pre_road_id].lane_section_list) - 1
                        is_equal_direction = True
                    pre_lane_id = self.find_linked_lane_id(current_lane, lane_id, "predecessor", is_equal_direction)

                    if not pre_lane_id == None :
                        pre_lane_key = (pre_road_id, pre_lane_section_idx, pre_lane_id, pre_contact_point)
                        pre_lane_key_list.append(pre_lane_key)
                elif pre_type == "junction" :
                    pre_junc_id = road_dict[road_id].predecessor.elementId
                    junc = junction_dict[pre_junc_id]
                    connection_list = junc.connection_list

                    for conn in connection_list:
                        if conn.incoming_road == road_id :
                            conn_road_id = conn.connecting_road
                            conn_contact_point = conn.contact_point

                            if conn_contact_point == "start" :
                                conn_lane_section_idx = 0
                                is_equal_direction = False
                            else :
                                conn_lane_section_idx = len(road_dict[conn_road_id].lane_section_list) - 1
                                is_equal_direction = True

                            for lane_link in conn.lane_link_list :
                                if lane_link.from_link == current_lane.id :
                                    conn_lane_id = self.to_linked_lane_id(current_lane.id, lane_link.to_link, lane_id, is_equal_direction)
                                    con_lane_key = (conn_road_id, conn_lane_section_idx, conn_lane_id, conn_contact_point)
                                    pre_lane_key_list.append(con_lane_key)

        #successor
        if lane_section_idx < (len(road_dict[road_id].lane_section_list) - 1) :
            suc_road_id = road_id
            suc_lane_section_idx = lane_section_idx + 1
            suc_lane_id = self.find_linked_lane_id(current_lane, lane_id, "successor", True)

            if not suc_lane_id == None :
                suc_lane_key = (suc_road_id, suc_lane_section_idx, suc_lane_id, "start")
                suc_lane_key_list.append(suc_lane_key)
        else:
            if not road_dict[road_id].successor == None :
                suc_type = road_dict[road_id].successor.elementType
                suc_contact_point = road_dict[road_id].successor.contactPoint

                if suc_type == "road" and (not suc_contact_point == None):
                    suc_road_id = road_dict[road_id].successor.elementId
                    if suc_contact_point == "start" :
                        suc_lane_section_idx = 0
                        is_equal_direction = True
                    else :
                        suc_lane_section_idx = len(road_dict[suc_road_id].lane_section_list) - 1
                        is_equal_direction = False
                    suc_lane_id = self.find_linked_lane_id(current_lane, lane_id, "successor", is_equal_direction)

                    if not suc_lane_id == None :
                        
                        suc_lane_key = (suc_road_id, suc_lane_section_idx, suc_lane_id, suc_contact_point)
                        suc_lane_key_list.append(suc_lane_key)
                elif suc_type == "junction" :
                    suc_junc_id = road_dict[road_id].successor.elementId
                    junc = junction_dict[suc_junc_id]
                    connection_list = junc.connection_list

                    for conn in connection_list:
                        if conn.incoming_road == road_id :
                            conn_road_id = conn.connecting_road
                            conn_contact_point = conn.contact_point

                            if conn_contact_point == "start" :
                                conn_lane_section_idx = 0
                                is_equal_direction = True
                            else :
                                conn_lane_section_idx = len(road_dict[conn_road_id].lane_section_list) - 1
                                is_equal_direction = False

                            for lane_link in conn.lane_link_list :
                                if lane_link.from_link == current_lane.id :
                                    conn_lane_id = self.to_linked_lane_id(current_lane.id, lane_link.to_link, lane_id, is_equal_direction)
                                    con_lane_key = (conn_road_id, conn_lane_section_idx, conn_lane_id, conn_contact_point)
                                    suc_lane_key_list.append(con_lane_key)
            
        return pre_lane_key_list, suc_lane_key_list

    def gen_idx_from_key(self, key):
        #idx = "__" + "_".join(map(str, key)) + "__"
        idx_str_list = list()
        for key_item_idx in range(len(key)) :
            key_item = key[key_item_idx]
            if (key_item_idx == 2) and (type(key_item) is int) :
                if key_item < 0 :
                    key_str = "R" + str(np.abs(key_item))
                else :
                    key_str = "L" + str(np.abs(key_item))
            elif key_item_idx == 3 :
                if key_item == "start" :
                    key_str = "S"
                else :
                    key_str = "E"
            else :
                key_str = str(key_item)
            idx_str_list.append(key_str)

        idx = "_" + "_".join(map(str, idx_str_list)) + "_"

        return idx

    def find_from_item_points(self, from_item_key) :
        from_item = self.lane_item_dict[(from_item_key[0], from_item_key[1], from_item_key[2])]
        from_contact_point = from_item_key[3]
        if from_contact_point == "end" :
            left_point = from_item.left_vertices[-1]
            right_point = from_item.right_vertices[-1]
        else : 
            left_point = from_item.right_vertices[0]
            right_point = from_item.left_vertices[0]

        lane_side = "left"
        if from_item_key[2] < 0 :
            lane_side = "right"
        if lane_side != self.dir :
            left_point, right_point = right_point, left_point

        return left_point, right_point

    def find_to_item_points(self, to_item_key) :
        to_item = self.lane_item_dict[(to_item_key[0], to_item_key[1], to_item_key[2])]
        to_contact_point = to_item_key[3]
        if to_contact_point == "start" :
            left_point = to_item.left_vertices[0]
            right_point = to_item.right_vertices[0]
        else : 
            left_point = to_item.right_vertices[-1]
            right_point = to_item.left_vertices[-1]

        lane_side = "left"
        if to_item_key[2] < 0 :
            lane_side = "right"
        if lane_side != self.dir :
            left_point, right_point = right_point, left_point

        return left_point, right_point

    
    def update_node(self, node) :
        point = node.point
        near_nodes = self.nodeKdTree.query_ball_point(vertexTo2D(point), 0.1)
        point_mean = np.array([0.0,0.0,0.0])
        point_cnt = 0
        connected_items = list()
        for near_node_idx in near_nodes :
            item_key = self.node_data[near_node_idx][0]
            side = self.node_data[near_node_idx][1]
            contact_point = self.node_data[near_node_idx][2]    #start or end

            near_lane_item = self.lane_item_dict[item_key]
            near_center_vertices = near_lane_item.center_vertices

            if side == "center" :
                if contact_point == "start" :
                    if near_lane_item.lane_link.from_node == None:
                        if np.linalg.norm(node.point[2] - np.array(near_center_vertices[0][2])) < self.z_tolerance :
                            node.add_to_links(near_lane_item.lane_link)
                            point_mean += near_lane_item.lane_link.points[0]
                            point_cnt += 1
                            connected_items.append(near_node_idx)
                else :
                    if near_lane_item.lane_link.to_node == None :
                        if np.linalg.norm(node.point[2] - np.array(near_center_vertices[-1][2])) < self.z_tolerance :
                            node.add_from_links(near_lane_item.lane_link)
                            point_mean += near_lane_item.lane_link.points[-1]
                            point_cnt += 1
                            connected_items.append(near_node_idx)

        #노드 좌표 및 연결 지점 업데이트
        point_mean = point_mean/point_cnt
        point_mean[0] = round(point_mean[0], 12)
        point_mean[1] = round(point_mean[1], 12)
        point_mean[2] = round(point_mean[2], 12)

        node.point = point_mean

        for near_node_idx in connected_items :
            item_key = self.node_data[near_node_idx][0]
            side = self.node_data[near_node_idx][1]
            contact_point = self.node_data[near_node_idx][2]    #start or end

            near_lane_item = self.lane_item_dict[item_key]

            if side == "center" :
                if contact_point == "start" :
                    near_lane_item.lane_link.points[0] = point_mean
                else :
                    near_lane_item.lane_link.points[-1] = point_mean

    def update_lanenode(self, node) :
        point = node.point
        near_nodes = self.kdTree.query_ball_point(vertexTo2D(point), 0.1)
        point_mean = np.array([0.0,0.0,0.0])
        point_cnt = 0
        connected_items = list()
        for near_node_idx in near_nodes :
            item_key = self.lanenode_data[near_node_idx][0]
            side = self.lanenode_data[near_node_idx][1]             #left or right
            contact_point = self.lanenode_data[near_node_idx][2]    #start or end

            near_lane_item = self.lane_item_dict[item_key]

            if side == "left" :
                if contact_point == "start" :
                    if near_lane_item.left_lanemarking.from_node == None:
                        if np.linalg.norm(node.point[2] - np.array(near_lane_item.left_vertices[0][2])) < self.z_tolerance :
                            node.add_to_links(near_lane_item.left_lanemarking)
                            point_mean += near_lane_item.left_lanemarking.points[0]
                            point_cnt += 1
                            connected_items.append(near_node_idx)
                else :
                    if near_lane_item.left_lanemarking.to_node == None :
                        if np.linalg.norm(node.point[2] - np.array(near_lane_item.left_vertices[-1][2])) < self.z_tolerance :
                            node.add_from_links(near_lane_item.left_lanemarking)
                            point_mean += near_lane_item.left_lanemarking.points[-1]
                            point_cnt += 1
                            connected_items.append(near_node_idx)
            else :
                if contact_point == "start" :
                    if near_lane_item.right_lanemarking.from_node == None :
                        if np.linalg.norm(node.point[2] - np.array(near_lane_item.right_vertices[0][2])) < self.z_tolerance :
                            node.add_to_links(near_lane_item.right_lanemarking)
                            point_mean += near_lane_item.right_lanemarking.points[0]
                            point_cnt += 1
                            connected_items.append(near_node_idx)
                else :
                    if near_lane_item.right_lanemarking.to_node == None :
                        if np.linalg.norm(node.point[2] - np.array(near_lane_item.right_vertices[-1][2])) < self.z_tolerance :
                            node.add_from_links(near_lane_item.right_lanemarking)
                            point_mean += near_lane_item.right_lanemarking.points[-1]
                            point_cnt += 1
                            connected_items.append(near_node_idx)

        #노드 좌표 및 연결 지점 업데이트
        point_mean = point_mean/point_cnt
        point_mean[0] = round(point_mean[0], 12)
        point_mean[1] = round(point_mean[1], 12)
        point_mean[2] = round(point_mean[2], 12)

        node.point = point_mean

        for near_node_idx in connected_items :
            item_key = self.lanenode_data[near_node_idx][0]
            side = self.lanenode_data[near_node_idx][1]             #left or right
            contact_point = self.lanenode_data[near_node_idx][2]    #start or end

            near_lane_item = self.lane_item_dict[item_key]

            if side == "left" :
                if contact_point == "start" :
                    near_lane_item.left_lanemarking.points[0] = point_mean
                    near_lane_item.left_vertices[0] = point_mean.tolist()
                else :
                    near_lane_item.left_lanemarking.points[-1] = point_mean
                    near_lane_item.left_vertices[-1] = point_mean.tolist()
            else :
                if contact_point == "start" :
                    near_lane_item.right_lanemarking.points[0] = point_mean
                    near_lane_item.right_vertices[0] = point_mean.tolist()
                else :
                    near_lane_item.right_lanemarking.points[-1] = point_mean
                    near_lane_item.right_vertices[-1] = point_mean.tolist()

    def convert_to_mgeo(self):
        self.process()
        #Lanemarking set, link
        lanemarkingset = LaneBoundarySet()
        lanenodeset = NodeSet()
        linkset = LineSet()
        nodeset = NodeSet()
        road_poly_set = RoadPolygonSet()

        lane_change_left_dict = dict()
        lane_change_right_dict = dict()

        for lane_item_key in self.lane_item_dict :
            lane_item = self.lane_item_dict[lane_item_key]
            lane_link_idx = self.gen_idx_from_key(lane_item_key)
            left_lane_item = None
            right_lane_item = None

            if lane_item.left_lane_item != None and lane_item.left_lane_item in self.lane_item_dict:
                left_lane_item = self.lane_item_dict[lane_item.left_lane_item]
            if lane_item.right_lane_item != None and lane_item.right_lane_item in self.lane_item_dict:
                right_lane_item = self.lane_item_dict[lane_item.right_lane_item]

            #Lanemarking
            left_vertices = lane_item.left_vertices[:]
            right_vertices = lane_item.right_vertices[:]

            if self.clean_link  :
                left_vertices = self.check_last_point(left_vertices)
                right_vertices = self.check_last_point(right_vertices)
                left_vertices = clean_vertices(left_vertices, self.z_tolerance)
                right_vertices = clean_vertices(right_vertices, self.z_tolerance)
                left_vertices = clean_vertices3(left_vertices)
                right_vertices = clean_vertices3(right_vertices)

            left_vertices = np.array(left_vertices)
            right_vertices = np.array(right_vertices)
            
            left_lanemarking = LaneBoundary(left_vertices, lane_link_idx + "L_")
            if lane_item_key[2] == -1 and '0' in lane_item.lane_type_set.lanes:
                left_lane = lane_item.lane_type_set.lanes['0']
                left_lanemarking.lane_type = left_lane.lane_type
                left_lanemarking.lane_shape = left_lane.lane_shape
                left_lanemarking.lane_color = left_lane.lane_color
                left_lanemarking.lane_type_offset = left_lane.lane_type_offset

            right_lanemarking = LaneBoundary(right_vertices, lane_link_idx + "R_")
            if str(lane_item_key[2]) in lane_item.lane_type_set.lanes:
                right_lane = lane_item.lane_type_set.lanes[str(lane_item_key[2])]
                right_lanemarking.lane_type = right_lane.lane_type
                right_lanemarking.lane_shape = right_lane.lane_shape
                right_lanemarking.lane_color = right_lane.lane_color
                right_lanemarking.lane_type_offset = right_lane.lane_type_offset

            if left_lane_item != None:
                chk_lanemarking = left_lane_item.right_lanemarking
                if chk_lanemarking != None and np.array_equal(chk_lanemarking.points, left_lanemarking.points) :
                    lane_item.set_left_lanemarking(chk_lanemarking)

            if right_lane_item != None:
                chk_lanemarking = right_lane_item.left_lanemarking
                if chk_lanemarking != None and np.array_equal(chk_lanemarking.points, right_lanemarking.points) :
                    lane_item.set_right_lanemarking(chk_lanemarking)

            if lane_item.left_lanemarking == None :            
                lane_item.set_left_lanemarking(left_lanemarking)
                left_lanemarking.lane_type_def = 'OpenDRIVE'
                lanemarkingset.append_line(left_lanemarking, False)

            if lane_item.right_lanemarking == None :            
                lane_item.set_right_lanemarking(right_lanemarking)
                right_lanemarking.lane_type_def = 'OpenDRIVE'
                lanemarkingset.append_line(right_lanemarking, False)

            #주행경로 Link
            lane_side = "left"
            if lane_item.lane_id < 0 :
                lane_side = "right"

            #if lane_item.lane_type == "driving" :
            center_vertices = lane_item.center_vertices[lane_item.center_vtx_s_idx:lane_item.center_vtx_e_idx]
            if self.clean_link  :
                center_vertices = clean_vertices(center_vertices, self.z_tolerance)
                center_vertices = clean_vertices3(center_vertices)
            center_vertices = np.array(center_vertices)
            if lane_side != self.dir :
                center_vertices = center_vertices[::-1]

            lane_item.center_vertices = center_vertices

            if len(center_vertices) > 1 :
                lane_link = Link(center_vertices, lane_link_idx, False)
                lane_link.road_id = lane_item.road_id
                lane_link.ego_lane = int(lane_item.lane_id)
                lane_link.link_type = lane_item.lane_type
                lane_link.link_type_def = "OpenDRIVE"
                if lane_item.max_speed == None :
                    lane_link.max_speed = 50
                else :
                    lane_link.max_speed = int(lane_item.max_speed)
                lane_link.speed_unit = "kph"

                if lane_side == self.dir :
                    if lane_item.left_lanemarking != None :
                        lane_link.set_lane_mark_left(lane_item.left_lanemarking)
                    if lane_item.right_lanemarking != None :
                        lane_link.set_lane_mark_right(lane_item.right_lanemarking)
                else :
                    if lane_item.left_lanemarking != None :
                        lane_link.set_lane_mark_right(lane_item.left_lanemarking)
                    if lane_item.right_lanemarking != None :
                        lane_link.set_lane_mark_left(lane_item.right_lanemarking)
                        
                can_move_left = False
                can_move_right = False
                left_link_key = None
                right_link_key = None

                if left_lane_item != None :
                    if lane_item.can_move_left :
                        can_move_left = True
                    left_link_key = lane_item.left_lane_item
                if right_lane_item != None :
                    if lane_item.can_move_right :
                        can_move_right = True
                    right_link_key = lane_item.right_lane_item

                if lane_side != self.dir :
                    can_move_left, can_move_right = can_move_right, can_move_left
                    left_link_key, right_link_key = right_link_key, left_link_key

                lane_link.can_move_left_lane = can_move_left
                lane_link.can_move_right_lane = can_move_right

                if left_link_key != None : 
                    left_lane_side = ""
                    if self.lane_item_dict[left_link_key].lane_id > 0 :
                        left_lane_side = "left"
                    elif self.lane_item_dict[left_link_key].lane_id < 0 :
                        left_lane_side = "right"
                    if left_lane_side == lane_side :
                        lane_change_left_dict[lane_item_key] = left_link_key
                if right_link_key != None : 
                    right_lane_side = ""
                    if self.lane_item_dict[right_link_key].lane_id > 0 :
                        right_lane_side = "left"
                    elif self.lane_item_dict[right_link_key].lane_id < 0 :
                        right_lane_side = "right"
                    if right_lane_side == lane_side :
                        lane_change_right_dict[lane_item_key] = right_link_key

                lane_item.set_lane_link(lane_link)
                linkset.append_line(lane_link, False)

            #노드 정보
            if lane_item.lane_link != None :
                self.node_KDTreeData.append(vertexTo2D(lane_item.center_vertices[0]))
                self.node_data.append((lane_item_key,"center","start"))
                self.node_KDTreeData.append(vertexTo2D(lane_item.center_vertices[-1]))
                self.node_data.append((lane_item_key,"center","end"))

        self.kdTree = sp.KDTree(self.lanenode_KDTreeData)
        self.nodeKdTree = sp.KDTree(self.node_KDTreeData)
        junction_node_dict = dict()

        for lane_item_key in self.lane_item_dict :
            lane_item = self.lane_item_dict[lane_item_key]
            if lane_item.lane_link != None :
                if lane_item.lane_link.from_node == None : 
                    link_from_node = Node()
                    link_from_node.point = np.array(lane_item.center_vertices[0])
                    self.update_node(link_from_node)
                    nodeset.append_node(link_from_node, True)

                if lane_item.lane_link.to_node == None : 
                    link_to_node = Node()
                    link_to_node.point = np.array(lane_item.center_vertices[-1])
                    self.update_node(link_to_node)
                    nodeset.append_node(link_to_node, True)
                if lane_item.junction_id != "-1" :
                    if lane_item.junction_id not in junction_node_dict :
                        junction_node_dict[lane_item.junction_id] = list()

                    if lane_item.lane_link.to_node not in junction_node_dict[lane_item.junction_id] :
                        junction_node_dict[lane_item.junction_id].append(lane_item.lane_link.to_node)
                    if lane_item.lane_link.from_node not in junction_node_dict[lane_item.junction_id] :
                        junction_node_dict[lane_item.junction_id].append(lane_item.lane_link.from_node)

            if lane_item.left_lanemarking.from_node == None :
                left_from_node = Node()
                left_from_node.point = np.array(lane_item.left_vertices[0])

                self.update_lanenode(left_from_node)
                lanenodeset.append_node(left_from_node, True)

            if lane_item.left_lanemarking.to_node == None :
                left_to_node = Node()
                left_to_node.point = np.array(lane_item.left_vertices[-1])

                self.update_lanenode(left_to_node)
                lanenodeset.append_node(left_to_node, True)

            if lane_item.right_lanemarking.from_node == None :
                right_from_node = Node()
                right_from_node.point = np.array(lane_item.right_vertices[0])

                self.update_lanenode(right_from_node)
                lanenodeset.append_node(right_from_node, True)

            if lane_item.right_lanemarking.to_node == None :
                right_to_node = Node()
                right_to_node.point = np.array(lane_item.right_vertices[-1])

                self.update_lanenode(right_to_node)
                lanenodeset.append_node(right_to_node, True)

        for lane_item_key in lane_change_left_dict :
            left_item_key = lane_change_left_dict[lane_item_key]

            if lane_item_key in self.lane_item_dict and left_item_key in self.lane_item_dict:
                lane_item = self.lane_item_dict[lane_item_key]
                left_item = self.lane_item_dict[left_item_key]
                
                if left_item.lane_link != None and lane_item.lane_link != None :
                    lane_item.lane_link.set_left_lane_change_dst_link(left_item.lane_link)

        for lane_item_key in lane_change_right_dict :
            right_item_key = lane_change_right_dict[lane_item_key]

            if lane_item_key in self.lane_item_dict and right_item_key in self.lane_item_dict:
                lane_item = self.lane_item_dict[lane_item_key]
                right_item = self.lane_item_dict[right_item_key]
                
                if right_item.lane_link != None and lane_item.lane_link != None :
                    lane_item.lane_link.set_right_lane_change_dst_link(right_item.lane_link)

        #MGeo Junction
        mgeo_junction_set = JunctionSet()
        for junction_id in junction_node_dict :
            if junction_id == "-1":
                continue
            node_list = junction_node_dict[junction_id]
            mgeo_junction = Junction(junction_id)
            for node in node_list :
                mgeo_junction.add_jc_node(node)
            mgeo_junction_set.append_junction(mgeo_junction)

        #노드 정보로부터 노드 생성
        #주행경로 노드
        
        """
        mgeo_junction_set = JunctionSet()
        mgeo_junction_dict = dict()
        
        for node_item in center_node_item_list :
            center_point = None
            if len(node_item.from_items) == 0 and len(node_item.to_items) == 0 :
                continue
            elif len(node_item.from_items) > 0 :
                from_item = self.lane_item_dict[(node_item.from_items[0][0], node_item.from_items[0][1], node_item.from_items[0][2])]
                center_point = from_item.center_vertices[from_item.center_vtx_e_idx-1]
            elif len(node_item.to_items) > 0 :
                to_item = self.lane_item_dict[(node_item.to_items[0][0], node_item.to_items[0][1], node_item.to_items[0][2])]
                center_point = to_item.center_vertices[to_item.center_vtx_s_idx]

            if center_point == None :
                continue

            center_node = None

            if node_item.center_node == None :
                center_node = Node()
                center_node.point = np.array(center_point)
                node_item.set_center_node(center_node)

                for mgeo_junction_id in node_item.junction_id_list :
                    if mgeo_junction_id == "-1":
                        continue
                    if mgeo_junction_id not in mgeo_junction_dict :
                        mgeo_junction = Junction(mgeo_junction_id)
                        mgeo_junction_dict[mgeo_junction_id] = mgeo_junction
                        mgeo_junction_set.append_junction(mgeo_junction)
                    else :
                        mgeo_junction = mgeo_junction_dict[mgeo_junction_id]
                    mgeo_junction.add_jc_node(center_node)
            else :
                center_node = node_item.center_node

            for from_item_key in node_item.from_items :
                lane_item_key = (from_item_key[0], from_item_key[1], from_item_key[2])
                lane_item = self.lane_item_dict[lane_item_key]

                lane_side = "left"
                if from_item_key[2] < 0 :
                    lane_side = "right"
                
                if lane_side == self.dir :
                    if lane_item.lane_link != None and lane_item.lane_link.to_node == None :
                        center_node.add_from_links(lane_item.lane_link)
                else :
                    if lane_item.lane_link != None and lane_item.lane_link.from_node == None :
                        center_node.add_to_links(lane_item.lane_link)

            for to_item_key in node_item.to_items :
                lane_item_key = (to_item_key[0], to_item_key[1], to_item_key[2])
                lane_item = self.lane_item_dict[lane_item_key]

                lane_side = "left"
                if to_item_key[2] < 0 :
                    lane_side = "right"

                if lane_side == self.dir :
                    if lane_item.lane_link != None and lane_item.lane_link.from_node == None :
                        center_node.add_to_links(lane_item.lane_link)
                else :
                    if lane_item.lane_link != None and lane_item.lane_link.to_node == None :
                        center_node.add_from_links(lane_item.lane_link)

            if len(center_node.from_links) > 0 or len(center_node.to_links) > 0 :
                nodeset.append_node(center_node, True)
        """
        if self.generate_mesh :
            mesh_dict = self.to_mesh_data()
            for point_key in mesh_dict :
                if point_key[0] == "ROAD" :
                    poly_idx = "_ROAD" + self.gen_idx_from_key(point_key[1:])
                else :
                    poly_idx = "_JUNCTION_" + str(point_key[1]) + "_" + str(point_key[2]) + "_"
                    
                points = mesh_dict[point_key][0]
                faces = mesh_dict[point_key][1]

                road_poly = RoadPolygon(np.array(points), faces, None, "road", poly_idx)
                road_poly_set.append_data(road_poly, False)

            rtree_index, triangle_list = self.build_rtree_from_road_poly_set(road_poly_set)
        
            for lm_key in self.lanemarking_dict :
                lanemarking_list = self.lanemarking_dict[lm_key]
                for lm_idx in range(len(lanemarking_list)) :
                    lanemarking = lanemarking_list[lm_idx]
                    color = lanemarking[0]
                    vertices_list = lanemarking[1]
                    for vertex_idx in range(len(vertices_list)) :
                        poly_idx = "_LM" + self.gen_idx_from_key(lm_key) + str(lm_idx) + "_" + str(vertex_idx) + "_"
                        lm_vertices = vertices_list[vertex_idx]

                        if self.project_lm :
                            lm_vertices = self.project_lm_vertices(lm_vertices, rtree_index, triangle_list, self.lanemarking_height)

                        left_vertices = lm_vertices[1::2]
                        right_vertices = lm_vertices[0::2]

                        left_vertices, right_vertices = clean_vertices2(left_vertices, right_vertices)
                        lm_vertices = list(it.chain(*zip(right_vertices, left_vertices)))

                        lm_faces = gen_tri_strips(lm_vertices)
                        lm_uv = list()
                        uv_loop_cnt = int(len(lm_vertices) / 2)
                        if uv_loop_cnt < 2 :
                            continue
                        
                        for i in range(uv_loop_cnt) :
                            lm_u = 1.0 * i
                            lm_uv.append([lm_u, 0.0])
                            lm_uv.append([lm_u, 1.0])

                        lm_poly = RoadPolygon(np.array(lm_vertices), lm_faces, lm_uv, "lm_" + color, poly_idx)
                        road_poly_set.append_data(lm_poly, False)
            
            for stop_line_idx in self.stop_line_dict :
                #if stop_line_idx in ["7909", "20964", "3316", "6959", "27050", "2197", "26368", "18654","26677","26712","26385","26386","26301","26346","26304","26205","26181","26167","1204","7873","21033","21159","10765","1507","20960","26570","21032","12349","12348","13090","629","26111","26110","13616","11458","21158","26589","13460","11390","26122","26832","26095","17378","12011","8586","12000","21034","21031","8721","12435","11987","21030","3142","3032","3030","4131","2930","2934","20398","2538","11344","2509","17136","25926","26899","8737","26898","600","532","654","612","125"] :
                    #continue
                stop_line = self.stop_line_dict[stop_line_idx]
                stop_line_points = stop_line.points[0:-1]
                stop_line_points = stop_line_points[::-1]       #반시계 방향
                stop_line_faces = [[0, 1, 2], [0, 2, 3]]
                stop_line_uv = [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0]]

                #stop_line.centroid
                #stop_line.points
                #if len(stop_line.points) != 5 :
                    #print("stop_line_idx : {}".format(stop_line_idx))
                #stop_line_poly = vtkPolyByPoints(stop_line.points)
                #stop_line_poly = vtkTrianglePoly(stop_line_poly)

                #points, faces = vtkPoly_to_MeshData(stop_line_poly)
                
                road_poly = RoadPolygon(np.array(stop_line_points), stop_line_faces, stop_line_uv, "stop_line", "_STOP_LINE_" + stop_line_idx)
                road_poly_set.append_data(road_poly, False)
        for lm_type in self.extra_lanemarking :
            if lm_type in ["ConstantSlopeBarrier", "GuardRail", "ChevronRegion"] :
                typedef = "RoadRunner_Object"
            else :
                typedef = "Autoever_Object"
            obj_dict = self.extra_lanemarking[lm_type]

            for obj_id in obj_dict :
                obj_points = obj_dict[obj_id]
                if len(obj_points) > 0 :
                    vertices = np.array(obj_points[:])
                    lb_idx = "_" + str(lm_type).replace(" ", "") + "_" + str(obj_id) + "_"

                    lanemarking = LaneBoundary(vertices, lb_idx)
                    lanemarking.lane_color = "Undefined"
                    lanemarking.lane_shape = ["Solid"]

                    lanemarking.lane_type_def = typedef
                    if lm_type == "structure A" :
                        lanemarking.lane_type = [1]
                    elif lm_type == "structure B" :
                        lanemarking.lane_type = [2]
                    elif lm_type == "structure C" :
                        lanemarking.lane_type = [3]
                    elif lm_type == "roadEdge" :
                        lanemarking.lane_type = [101]
                    elif lm_type == "ConstantSlopeBarrier" :
                        lanemarking.lane_type = [1]
                    elif lm_type == "GuardRail" :
                        lanemarking.lane_type = [2]

                    #노드 추가
                    from_lane_node = Node(lb_idx + "from_")
                    to_lane_node = Node(lb_idx + "to_")
                    from_lane_node.point = np.array(obj_points[0])
                    to_lane_node.point = np.array(obj_points[-1])

                    lanenodeset.append_node(from_lane_node, False)
                    lanenodeset.append_node(to_lane_node, False)

                    lanemarking.set_from_node(from_lane_node)
                    lanemarking.set_to_node(to_lane_node)
                    
                    if obj_id in self.extra_lanemarking_info :
                        re_type = self.extra_lanemarking_info[obj_id].roadEdge_type
                        if re_type != 0 :
                            lanemarking.lane_sub_type = re_type
                    lanemarking.lane_type_def = 'OpenDRIVE'
                    lanemarkingset.append_line(lanemarking, False)

        sign_set = SignalSet()
        light_set = SignalSet()
        for sig_key in self.sig_item_dict :
            sig_item = self.sig_item_dict[sig_key]
            
            if sig_item.name == "StopLine" :
                closest_node = None
                closest_distance = None
                #TODO : 시간 많이 걸리니 KD tree 같은걸로 바꾸자
                for node_id in nodeset.nodes :
                    chk_node = nodeset.nodes[node_id]
                    chk_distance = np.linalg.norm(np.array(sig_item.point) - chk_node.point)
                    if closest_node == None or chk_distance < closest_distance :
                        closest_node = chk_node
                        closest_distance = chk_distance
                if closest_node != None :
                    #print("{}, {}".format(closest_node.idx, sig_key)) 
                    closest_node.on_stop_line = True
            else :
                sig = Signal()
                sig.idx = sig_key
                sig.dynamic = sig_item.dynamic
                sig.point = np.array(sig_item.point)
                sig.country = sig_item.country
                sig.z_offset = sig_item.z_offset
                sig.width = sig_item.width
                sig.height = sig_item.height
                sig.heading = sig_item.heading
                sig.orientation = sig_item.orientation
                sig.type = sig_item.type
                sig.sub_type = sig_item.subtype
                sig.value = sig_item.value

                for lane_key in sig_item.link_list :
                    if lane_key in self.lane_item_dict :
                        lane_item = self.lane_item_dict[lane_key]
                        lane_link = lane_item.lane_link
                        if (lane_link != None) :
                            sig.add_link_ref(lane_link)
                            sig.link_id_list.append(lane_link.idx)
                            
                if sig.dynamic == True and (sig.type == "car" or sig.type == "pedestrian" or sig.type == "bus") :
                    light_set.append_signal(sig)
                else :
                    sign_set.append_signal(sig)
                sig_item.mgeo_signal = sig

        sm_set = SurfaceMarkingSet()
        for sm_key in self.sm_item_dict :
            sm_item = self.sm_item_dict[sm_key]
            sm = SurfaceMarking(sm_item.points)
            
            # sm.points = np.array(sm_item.points)
            sm.type = sm_item.type
            sm.sub_type = sm_item.subtype
            sm.idx = sm_key
            if (sm_item.lane_item_key != None) and (sm_item.lane_item_key in self.lane_item_dict) and self.lane_item_dict[sm_item.lane_item_key].lane_link != None :
                sm_lane_link = self.lane_item_dict[sm_item.lane_item_key].lane_link
                sm.add_link_ref(sm_lane_link)
                sm.link_id_list.append(sm_lane_link.idx)
            sm_set.append_data(sm, create_new_key=False)
            
            #에디터 확인용
            #temp = LaneBoundary(sm.points, sm_key)
            #lanemarkingset.append_line(temp)

        cw_set = CrossWalkSet()
        scw_set = SingleCrosswalkSet()
        for crosswalk_key in self.crosswalk_dict:
            crosswalk_item = self.crosswalk_dict[crosswalk_key]
            scw_idx = "SCW_" + str(crosswalk_key)
            
            scw = SingleCrosswalk(np.array(crosswalk_item.points), scw_idx, crosswalk_item.type)
            # scw.ref_crosswalk_id = cw_idx
            scw_set.append_data(scw, create_new_key=False)
            
            # cw = Crosswalk()
            # cw.append_single_scw_list(scw)
            # cw_set.append_data(cw)

        #controller
        #TODO : synced signal 끼리 묶도록 해야함(무엇을 기준으로?)
        mgeo_controller_set = IntersectionControllerSet()
        for controller_id in self.controller_dict :
            controller = self.controller_dict[controller_id]
            if controller.name in mgeo_controller_set.intersection_controllers:
                mgeo_controller = mgeo_controller_set.intersection_controllers[controller.name]
            else:
                mgeo_controller = IntersectionController(id=controller.name)
                mgeo_controller_set.append_controller(mgeo_controller)
                
            mgeo_controller.new_synced_signal()
            for control in controller.control_list :
                signal_id = control.signal_id
                if signal_id in self.sig_item_dict:
                    mgeo_signal = self.sig_item_dict[signal_id].mgeo_signal
                    if mgeo_signal != None :
                        mgeo_controller.append_signal(mgeo_signal)
            
        mgeo = MGeo(node_set=nodeset, link_set=linkset, lane_boundary_set=lanemarkingset, lane_node_set=lanenodeset, junction_set=mgeo_junction_set, road_polygon_set=road_poly_set, sign_set=sign_set, light_set=light_set, intersection_controller_set=mgeo_controller_set, sm_set=sm_set, scw_set=scw_set, cw_set=cw_set)
        if self.geo_reference != None :
            mgeo.global_coordinate_system = self.geo_reference
            
        if self.geo_offset != None :
            origin = np.array([float(self.geo_offset['x']), float(self.geo_offset['y']), float(self.geo_offset['z'])])
            mgeo.set_origin(origin)

        return mgeo

    def build_rtree_from_road_poly_set(self, road_poly_set) :
        rtree_property = rtree.index.Property()
        rtree_property.dimension = 2
        rtree_index = rtree.index.Index(properties=rtree_property)
        triangle_list = list()

        for road_poly_idx in road_poly_set.data :
            road_poly = road_poly_set.data[road_poly_idx]

            for face in road_poly.faces :
                triangle_3d = list()
                min_x = None
                min_y = None
                max_x = None
                max_y = None

                for face_vertex_idx in face :
                    face_vertex = road_poly.points[face_vertex_idx]
                    triangle_3d.append(face_vertex)
                    if min_x is None or face_vertex[0] < min_x :
                        min_x = face_vertex[0]
                    if min_y is None or face_vertex[1] < min_y :
                        min_y = face_vertex[1]

                    if max_x is None or face_vertex[0] > max_x :
                        max_x = face_vertex[0]
                    if max_y is None or face_vertex[1] > max_y :
                        max_y = face_vertex[1]

                bbox = [min_x, min_y, max_x, max_y]
                if None in bbox :
                    continue

                if bbox[0] == bbox[2] :
                    bbox[0] -= np.finfo(float).eps
                    bbox[2] += np.finfo(float).eps

                if bbox[1] == bbox[3] :
                    bbox[1] -= np.finfo(float).eps
                    bbox[3] += np.finfo(float).eps
                
                triangle_id = len(triangle_list)
                triangle_list.append(triangle_3d)

                rtree_index.insert(triangle_id, bbox)

        #rtree 는 2차원 데이터, triangle 은 3차원 데이터
        return rtree_index, triangle_list

    def is_point_inside_triangle(self, point, triangle) :
        line_list = list()
        line_list.append([triangle[0], triangle[1]])
        line_list.append([triangle[1], triangle[2]])
        line_list.append([triangle[2], triangle[0]])

        intersect_count = 0
        for line in line_list :
            if line[1][0] != line[0][0] :
                t = (point[0] - line[0][0]) / (line[1][0] - line[0][0])

                if t >= 0 and t < 1 :
                    check_point = (np.array(line[1]) - np.array(line[0])) * t + np.array(line[0])
                    if check_point[1] > point[1] :
                        intersect_count += 1
                    elif check_point[1] == point[1] :
                        return True
            elif point[0] == line[1][0] :
                if point[1] < max(line[1][1], line[0][1]) and point[1] > min(line[1][1], line[0][1]) :
                    return True

        return intersect_count == 1

    def calc_projected_z(self, triangle_3d, vertex_2d, add_height) :
        face_normal = np.cross((triangle_3d[1] - triangle_3d[0]), (triangle_3d[2] - triangle_3d[0]))
        if face_normal[2] == 0 :
            return None
        plane_p = np.inner(face_normal, triangle_3d[0])
        new_z = (plane_p - np.inner(face_normal[0:2], vertex_2d)) / face_normal[2]

        return new_z + add_height

    def project_lm_vertices(self, vertices, rtree_index, triangle_list, height) :
        new_vertices = list()
        
        for vertex in vertices :
            vertex_2d = np.array(vertex[0:2])
            vertex_min_x = vertex[0] - np.finfo(float).eps
            vertex_max_x = vertex[0] + np.finfo(float).eps
            vertex_min_y = vertex[1] - np.finfo(float).eps
            vertex_max_y = vertex[1] + np.finfo(float).eps
            vertex_bbox = [vertex_min_x, vertex_min_y, vertex_max_x, vertex_max_y]
            
            hits = rtree_index.intersection(vertex_bbox, objects=False)

            min_diff_z = None
            new_z = None
            for triangle_idx in hits :
                triangle_3d = np.array(triangle_list[triangle_idx])

                if self.is_point_inside_triangle(vertex_2d, triangle_3d) :
                    projected_z = self.calc_projected_z(triangle_3d, vertex_2d, height)
                    z_diff = np.abs(projected_z - vertex[2])
                    if min_diff_z is None or z_diff < min_diff_z :
                        min_diff_z = z_diff
                        new_z = projected_z

            if new_z is not None :
                new_vertex = np.array([vertex[0], vertex[1], new_z])
                new_vertices.append(new_vertex)
            else :
                new_vertices.append(vertex)

        return new_vertices

    def check_last_point(self, points) :
        if len(points) > 2 :
            dis = line2_magnitute(lineTo2D([points[-1], points[-2]]))
            if dis < self.z_tolerance/4 :
                last_point = points[-1]
                points = points[:-2]
                points.append(last_point)
        return points

    def to_mesh_data(self) :
        data_dict = dict()
        road_dict = self.road_dict

        for road_id in road_dict :
            #if road_id != "61" : 
                #continue
            road = road_dict[road_id]
            
            if self.union_junction == True and road.junction != "-1" :
                continue

            for lane_section_idx in range(len(road.lane_section_list)):
                lane_section = road.lane_section_list[lane_section_idx]
                #left_vertex_data = self.gen_lane_vertices(road, lane_section.left_lane_list, lane_section.s, lane_section.length, "left")
                #right_vertex_data = self.gen_lane_vertices(road, lane_section.right_lane_list, lane_section.s, lane_section.length, "right")

                poly_road = vtk.vtkPolyData()
                for lane in lane_section.left_lane_list :
                    lane_item_key = (road_id, lane_section_idx, lane.id)
                    lane_item = self.lane_item_dict[lane_item_key]

                    left_vertices = lane_item.left_lanemarking.points.tolist()
                    right_vertices = lane_item.right_lanemarking.points.tolist()

                    vertices = list()
                    vertices.extend(right_vertices)
                    vertices.extend(list(reversed(left_vertices)))

                    vtk_poly = vtkPolyByPoints(vertices)
                    vtk_poly = vtkTrianglePoly(vtk_poly)
                    poly_road = vtkAppend(poly_road, vtk_poly)

                for lane in lane_section.right_lane_list :
                    lane_item_key = (road_id, lane_section_idx, lane.id)
                    lane_item = self.lane_item_dict[lane_item_key]

                    left_vertices = lane_item.left_lanemarking.points.tolist()
                    right_vertices = lane_item.right_lanemarking.points.tolist()

                    vertices = list()
                    vertices.extend(right_vertices)
                    vertices.extend(list(reversed(left_vertices)))

                    vtk_poly = vtkPolyByPoints(vertices)
                    vtk_poly = vtkTrianglePoly(vtk_poly)
                    poly_road = vtkAppend(poly_road, vtk_poly)

                poly_road = vtkCleanPoly(poly_road)
                road_points, road_faces = vtkPoly_to_MeshData(poly_road)
                if len(road_points) < 4 :
                    continue
                data_key = ("ROAD", road_id, lane_section_idx)
                data_dict[data_key] = [road_points, road_faces]
        
        if self.union_junction == True :
            junction_dict = self.junction_dict
            for junction_id in junction_dict:
                #continue
                #if junction_id not in ["1000010", "1000001","1000008","1000006","1000005","1000019"] :
                #if junction_id not in ["1000001"] :
                    #continue
                junction = junction_dict[junction_id]

                road_list = list()
                road_chk = dict()
                for connection in junction.connection_list:
                    if connection.connecting_road in road_dict:
                        road = road_dict[connection.connecting_road]
                        #중복제거
                        if road.id in road_chk and road_chk[road.id] == True :
                            continue
                        road_chk[road.id] = True
                        union_bound = UnionMeshBound(self.z_tolerance)

                        for lane_section_idx in range(len(road.lane_section_list)):
                            lane_section = road.lane_section_list[lane_section_idx]
                            if (len(lane_section.left_lane_list) == 0) and (len(lane_section.right_lane_list) == 0) :
                                continue

                            for lane in lane_section.left_lane_list :
                                lane_item_key = (road.id, lane_section_idx, lane.id)
                                lane_item = self.lane_item_dict[lane_item_key]

                                left_vertices = lane_item.left_lanemarking.points.tolist()
                                right_vertices = lane_item.right_lanemarking.points.tolist()
                                right_vertices.reverse()
                                union_bound.add(right_vertices[-1:] + left_vertices + right_vertices[:-1])

                            for lane in lane_section.right_lane_list :
                                lane_item_key = (road.id, lane_section_idx, lane.id)
                                lane_item = self.lane_item_dict[lane_item_key]

                                left_vertices = lane_item.left_lanemarking.points.tolist()
                                right_vertices = lane_item.right_lanemarking.points.tolist()
                                right_vertices.reverse()
                                union_bound.add(right_vertices[-1:] + left_vertices + right_vertices[:-1])

                        union_bound.process()
                        for lane_boundary in union_bound.result_list :
                            points = lane_boundary[:]
                            points.reverse()
                            # face = list()
                            # for point_idx in range(len(points)) :
                            #     face.append(point_idx)
                            # faces = list()
                            # faces.append(face)
                            # lane_poly = vtkPoly(points, faces)
                            lane_poly = vtkDelaunay2DTriangulation(points, list())
                            #lane_poly = vtkTrianglePoly(lane_poly)
                            road_list.append([lane_poly, lane_boundary])

                #겹치지 않고 한 점에서만 폴리곤이 만나는 경우에는 vtkTriangleFilter 가 제대로 동작하지 않을 수 있으므로
                #겹치는 폴리곤끼리 그룹화 하여 따로 처리하도록 함
                grouped_list = group_by_clip(road_list, self.z_tolerance)

                for i in range(len(grouped_list)) :
                    data_key = ("JUNCTION", junction_id, i)
                    #길이가 1 이면 그냥 append, 아니면 union
                    if len(grouped_list[i]) == 1:
                        points, faces = vtkPoly_to_MeshData(grouped_list[i][0][0])
                        data_dict[data_key] = [points, faces]
                    else :
                        uinon_bound = UnionMeshBound(self.z_tolerance, self.vertex_distance, VtkTriMethod.DELAUNAY)
                        for road_data in grouped_list[i] :
                            road_bound = road_data[1]
                            uinon_bound.add(road_bound)
                        uinon_bound.process(True)
                        union_result = uinon_bound.get_poly_result()

                        points, faces = vtkPoly_to_MeshData(union_result)

                        if len(points) < 4 :
                            continue
                        data_dict[data_key] = [points, faces]

        return data_dict

    def to_lane_vertices(self, lane_vertex_list) :
        left_vertices = lane_vertex_list[1::2]
        right_vertices = lane_vertex_list[0::2]
        center_vertices = list()
        for left_vertex, right_vertex in zip(left_vertices, right_vertices) :
            v_x = round((left_vertex[0] + right_vertex[0]) / 2, 12)
            v_y = round((left_vertex[1] + right_vertex[1]) / 2, 12)
            v_z = round((left_vertex[2] + right_vertex[2]) / 2, 12)
            center_vertex = [v_x, v_y, v_z]
            center_vertices.append(center_vertex)

        return left_vertices, right_vertices, center_vertices

    def odr_sigtype_to_mgeo(self, name, country, type, subtype, is_dynamic) :
        ret_type = None
        ret_subtype = None
        ret_orientation = None
        ret_value = None

        #dynamic 일 때 기본값
        if is_dynamic :
            ret_type = "car"
            ret_orientation = "horizontal"
            ret_subtype = ['red', 'yellow', 'straight']

        if country == "OpenDRIVE" :
            if name.startswith("Signal_4Light") : #4색등
                ret_type = "car"
                ret_orientation = "horizontal"
                ret_subtype = ['red', 'yellow', 'left', 'straight']
            elif name.startswith("Walk_Light") : #보행자신호등
                ret_type = "pedestrian"
                ret_orientation = "+"
                ret_subtype = None
            elif type == "1000001" :  #삼색등
                ret_type = "car"
                ret_orientation = "horizontal"
                ret_subtype = ['red', 'yellow', 'straight']
            elif type == "1000002" :  #보행등
                ret_orientation = "+"
                ret_type = "pedestrian"
                
                if subtype == "10" :
                    ret_subtype = ['red']
                elif subtype == "20" :
                    ret_subtype = ['straight']
                else :
                    ret_subtype = None

            elif type == "1000007" : #보행등+자전거
                ret_orientation = "+"
                ret_type = "pedestrian"
                
                if subtype == "10" :
                    ret_subtype = ['red']
                elif subtype == "20" :
                    ret_subtype = ['yellow']
                elif subtype == "30" :
                    ret_subtype = ['straight']
                else :
                    ret_subtype = None

            elif type == "1000009" :  #이색등
                ret_type = "car"
                ret_orientation = "horizontal"
                if subtype == "10" :
                    ret_subtype = ['red', 'yellow']
                elif subtype == "20" :
                    ret_subtype = ['yellow', 'straight']
                elif subtype == "30" :
                    ret_subtype = ['red', 'straight']
                else :
                    ret_type = None

            elif type == "1000010" :  #이색등
                ret_type = "car"
                ret_orientation = "horizontal"
                if subtype == "10" :
                    ret_subtype = ['yellow', 'left']
                elif subtype == "20" :
                    ret_subtype = ['yellow', 'right']
                else :
                    ret_type = None

            elif type == "1000011" :  #삼색등
                ret_type = "car"
                ret_orientation = "horizontal"
                if subtype == "10" :
                    ret_subtype = ['red', 'yellow', 'left']
                elif subtype == "20" :
                    ret_subtype = ['red', 'yellow', 'right']
                elif subtype == "30" :
                    ret_subtype = ['red', 'yellow', 'straight']
                elif subtype == "40" :
                    ret_subtype = ['red', 'yellow', 'left', 'straight']
                elif subtype == "50" :
                    ret_subtype = ['red', 'yellow', 'right', 'straight']
                else :
                    ret_type = None
        #TODO : 현재는 오토에버 형식으로 처리. 추후에 벤더로 구분하도록 수정 필요할 수 있음
        elif country == "KOR" : 
            if type == "1" :                #최고 속도 제한
                ret_type = "2"              #규제
                ret_subtype = "224"         #최고 속도제한
                ret_value = subtype
            elif type == "2" :              #최저 속도 제한
                ret_type = "2"              #규제
                ret_subtype = "225"         #최고 속도제한
                ret_value = subtype
            elif type == "3" :              #경고
                ret_type = "1"              #주의표지
                ret_subtype = "140"         #위험표지
            elif type == "4" :              #정지
                ret_type = "2"              #규제표지
                ret_subtype = "227"         #일시정지
            elif type == "5" :              #양보
                ret_type = "2"              #규제표지
                ret_subtype = "228"         #양보
            elif type == "6" :              #추월금지
                ret_type = "2"              #규제표지
                ret_subtype = "217"         #앞지르기금지
            #elif type == "7" :              #추월금지 끝
                #ret_type = ""              #
                #ret_subtype = ""           #
            #elif type == "8" :              #제한구역 끝
                #ret_type = ""              #
                #ret_subtype = ""           #
            elif type == "9" :              #진입금지
                ret_type = "2"              #규제표자
                ret_subtype = "211"         #진입금지
            elif type == "10" :             #통행금지
                ret_type = "2"              #규제표지
                ret_subtype = "201"         #통행금지
            elif type == "99" :             #기타
                ret_type = "1"              #주의표지
                ret_subtype = "199"         #기타주의
        # MGeo -> OpenDRIVE -> Import
        elif country == "KR" :
            ret_orientation = "horizontal"
            if type == "1000001" :     
                ret_type = "car"
                if subtype == "3":
                    ret_subtype = ['red', 'yellow', 'straight']
                else:
                    ret_subtype = ['red', 'yellow', 'left', 'straight']
            if type == "1000002" :
                ret_type = "pedestrian"    
            
        return ret_type, ret_subtype, ret_orientation, ret_value

    def get_point(self, road, s, t_point) :
        geometry_item = get_item_by_s(road.geometry_list, s)
        geometry_s_offset = s - geometry_item.s
        pos_x = float(0)
        pos_y = float(0)
        pos_z = float(0)
        hdg = float(0)

        #reference line 좌표 계산
        if geometry_item.geo_type == "line":
            hdg = geometry_item.hdg
            pos_x = geometry_item.x + np.cos(hdg) * geometry_s_offset
            pos_y = geometry_item.y + np.sin(hdg) * geometry_s_offset
        elif geometry_item.geo_type == "arc":
            radius = 1.0/geometry_item.arc_curvature
            hdg = geometry_item.hdg + geometry_s_offset * geometry_item.arc_curvature
            pos_x = geometry_item.x + radius*(np.cos(geometry_item.hdg + np.pi/2.0) - np.cos(hdg + np.pi/2.0))
            pos_y = geometry_item.y + radius*(np.sin(geometry_item.hdg + np.pi/2.0) - np.sin(hdg + np.pi/2.0))
        elif geometry_item.geo_type is "spiral":
            curve_dot = (geometry_item.spiral_curvEnd - geometry_item.spiral_curvStart) / geometry_item.length
            spiral_s_o = geometry_item.spiral_curvStart / curve_dot
            spiral_s = geometry_s_offset + spiral_s_o

            x, y, t = odr_spiral(spiral_s, curve_dot)
            x_o, y_o, t_o = odr_spiral(spiral_s_o, curve_dot)

            x = x - x_o
            y = y - y_o
            t = t - t_o

            angle = geometry_item.hdg - t_o
            pos_x = geometry_item.x + x * np.cos(angle) - y * np.sin(angle)
            pos_y = geometry_item.y + y * np.cos(angle) + x * np.sin(angle)
            hdg = geometry_item.hdg + t
        elif geometry_item.geo_type is "poly3":
            """
            TODO : poly3
            """
        elif geometry_item.geo_type is "paramPoly3":
            bU = geometry_item.paramPoly3_bU
            cU = geometry_item.paramPoly3_cU
            dU = geometry_item.paramPoly3_dU
            bV = geometry_item.paramPoly3_bV
            cV = geometry_item.paramPoly3_cV
            dV = geometry_item.paramPoly3_dV

            u,v,p = geometry_item.get_point_by(geometry_s_offset)
            tan = (bV + 2*cV*p + 3*dV*p*p) / (bU + 2*cU*p + 3*dU*p*p)
            hdg_uv = np.arctan2(tan, 1.0)

            hdg = hdg_uv + geometry_item.hdg
            pos_x = geometry_item.x + u * np.cos(geometry_item.hdg) - v * np.sin(geometry_item.hdg)
            pos_y = geometry_item.y + v * np.cos(geometry_item.hdg) + u * np.sin(geometry_item.hdg)

        #elevation 계산
        elevation_item = get_item_by_s(road.elevation_list, s)
        if not elevation_item == None:
            pos_z += polynomial(s - elevation_item.s, elevation_item.a, elevation_item.b, elevation_item.c, elevation_item.d)

        #좌표 계산
        pos_x = pos_x + t_point * (-np.sin(hdg))
        pos_y = pos_y + t_point * (np.cos(hdg))

        return [pos_x, pos_y, pos_z], hdg
        
    def process_signal_ref(self, signal_ref, road) :
        link_list = list()
        lanesection_idx = get_item_idx_by_s(road.lane_section_list, signal_ref.s)

        left_lane_list = road.lane_section_list[lanesection_idx].left_lane_list
        right_lane_list = road.lane_section_list[lanesection_idx].right_lane_list

        for lane in left_lane_list :
            if signal_ref.validity_list == None or len(signal_ref.validity_list) == 0 :
                link_list.append((road.id, lanesection_idx, lane.id))
            else :
                for validity in signal_ref.validity_list :
                    if ((validity.from_lane <= lane.id) and (validity.to_lane >= lane.id)) or (validity.from_lane >= lane.id) and (validity.to_lane <= lane.id):
                        link_list.append((road.id, lanesection_idx, lane.id))

        for lane in right_lane_list :
            if signal_ref.validity_list == None or len(signal_ref.validity_list) == 0:
                link_list.append((road.id, lanesection_idx, lane.id))
            else :
                for validity in signal_ref.validity_list :
                    if ((validity.from_lane <= lane.id) and (validity.to_lane >= lane.id)) or (validity.from_lane >= lane.id) and (validity.to_lane <= lane.id):
                        link_list.append((road.id, lanesection_idx, lane.id))

        return link_list

    def process_signal(self, signal, road) :
        #dynamic
        is_dynamic = False
        if signal.dynamic == "yes" :
            is_dynamic = True

        country = signal.country
        z_offset = signal.z_offset
        width = signal.width
        height = signal.height
        point, hdg = self.get_point(road, signal.s, signal.t)
        if z_offset != None :
            point[2] = point[2] + z_offset
        #if signal.orientation == "+" :
        heading = 180 * (signal.h_offset + np.pi + hdg) / np.pi 
        #else :
            #heading = 180 * (signal.h_offset + hdg) / np.pi 

        if heading > 360 :
            heading = heading - 360
        elif heading < 0 :
            heading = heading + 360

        #type, subtype
        sig_type, sig_subtype, sig_orientation, sig_value = self.odr_sigtype_to_mgeo(signal.name, signal.country, signal.type, signal.subtype, is_dynamic)
        if sig_type == None :
            sig_type = signal.type
            sig_subtype = signal.subtype

        #orientation
        orientation = signal.orientation
        """
        if orientation == "-" : 
            heading = heading + 180
        #0 ~ 360 으로...
        if heading > 360 :
            heading = heading - 360
        elif heading < 0 :
            heading = heading + 360
        """
        if is_dynamic :
            orientation = sig_orientation

        #link list
        lanesection_idx = get_item_idx_by_s(road.lane_section_list, signal.s)
        left_lane_list = road.lane_section_list[lanesection_idx].left_lane_list
        right_lane_list = road.lane_section_list[lanesection_idx].right_lane_list

        link_list = list()

        for lane in left_lane_list :
            if signal.validity_list == None or len(signal.validity_list) == 0 :
                link_list.append((road.id, lanesection_idx, lane.id))
            else :
                for validity in signal.validity_list :
                    if ((validity.from_lane <= lane.id) and (validity.to_lane >= lane.id)) or (validity.from_lane >= lane.id) and (validity.to_lane <= lane.id):
                        link_list.append((road.id, lanesection_idx, lane.id))

        for lane in right_lane_list :
            if signal.validity_list == None or len(signal.validity_list) == 0:
                link_list.append((road.id, lanesection_idx, lane.id))
            else :
                for validity in signal.validity_list :
                    if ((validity.from_lane <= lane.id) and (validity.to_lane >= lane.id)) or (validity.from_lane >= lane.id) and (validity.to_lane <= lane.id):
                        link_list.append((road.id, lanesection_idx, lane.id))

        sig_item = XodrSignalItemData(signal.name, is_dynamic, country, z_offset, width, height, heading, point, sig_type, sig_subtype, orientation, link_list, sig_value)
        self.sig_item_dict[signal.id] = sig_item

    def get_direction_by_points(self, hdg, points) :
        ret = "left"

        if line3_magnitute([points[0], points[1]]) > line3_magnitute([points[1], points[2]]) :
            rad = adapt_range(calc_line_vector_rad([points[0], points[1]]))
        else :
            rad = adapt_range(calc_line_vector_rad([points[1], points[2]]))

        ref_hdg = adapt_range(hdg)

        if np.abs(adapt_range(ref_hdg - rad)) > np.pi/2 :
            rad = adapt_range(np.pi + rad)

        if adapt_range(ref_hdg - rad) > 0 : 
            ret = "right"
        
        return ret

    def from_AutoEverRM_to_SMCode(self, obj_info, hdg, obj_point_list) :
        sm_type = None
        sm_subtype = None

        if obj_info.roadMark_type == 3 :#화살표
            sm_type = "1"
            if obj_info.roadMark_subtype == 1 :             #직진
                sm_subtype = "5371"
            elif obj_info.roadMark_subtype == 2 :           #좌회전
                sm_subtype = "5372"
            elif obj_info.roadMark_subtype == 3 :           #우회전
                sm_subtype = "5373"
            elif obj_info.roadMark_subtype == 4 :           #직-좌회전
                sm_subtype = "5381"
            elif obj_info.roadMark_subtype == 5 :           #직-우회전
                sm_subtype = "5382"
            elif obj_info.roadMark_subtype == 6 :           #유턴
                sm_subtype = "5391"
            elif obj_info.roadMark_subtype == 7 :           #유턴-직진
                sm_subtype = "5383"
            elif obj_info.roadMark_subtype == 8 :           #유턴-좌회전
                sm_subtype = "5392"
            elif obj_info.roadMark_subtype == 9 :           #좌-우회전
                sm_subtype = "5374"
            elif obj_info.roadMark_subtype == 10 :          #좌회전금지
                sm_subtype = "511"
            elif obj_info.roadMark_subtype == 11 :          #우회전금지
                sm_subtype = "510"
            elif obj_info.roadMark_subtype == 12 :          #직진금지
                sm_subtype = "512"
            elif obj_info.roadMark_subtype == 13 :          #유턴금지
                sm_subtype = "514"
            elif obj_info.roadMark_subtype == 14 :          #P턴 금지
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 15 :          #직진금지-좌회전
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 16 :          #직진금지-우회전
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 17 :          #직진금지-좌회전금지
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 18 :          #직진금지-우회전금지
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 19 :          #좌회전금지-우회전
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 20 :          #좌회전금지-직진
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 21 :          #좌회전금지-직진금지
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 22 :          #좌회전금지-우회전금지
                sm_subtype = "513"
            elif obj_info.roadMark_subtype == 23 :          #우회전금지-직진
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 24 :          #우회전금지-좌회전
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 25 :          #우회전금지-직진금지
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 26 :          #우회전금지-좌회전금지
                sm_subtype = "598"                          #기타 규제표시
            elif obj_info.roadMark_subtype == 27 :          #좌회전-직진-우회전
                sm_subtype = "5379"
            elif obj_info.roadMark_subtype == 28 :          #차로진입
                dir = self.get_direction_by_points(hdg, obj_point_list)
                if dir == "left" :
                    sm_subtype = "5431"                         #좌로 합류
                else :
                    sm_subtype = "5432"                         #우로 합류
            elif obj_info.roadMark_subtype == 29 :          #유턴금지-좌회전금지
                sm_subtype = "598"                          #기타 규제표시
        elif obj_info.roadMark_type == 4 :                  #숫자
            num = None
            if obj_info.roadMark_subtype == 128 : #숫자 5
                num = "5"
            elif obj_info.roadMark_subtype >= 129 and obj_info.roadMark_subtype <= 140 : #숫자 10~120
                num = str((obj_info.roadMark_subtype - 128) * 10)
            elif obj_info.roadMark_subtype >= 141 and obj_info.roadMark_subtype <= 151 : #숫자 15~115
                num = str((obj_info.roadMark_subtype - 140) * 10 + 5)
            if num != None : 
                sm_type = "2"
                #sm_subtype = "517"
                sm_subtype = "517" + "_" + num
        elif obj_info.roadMark_type == 5 :                  #문자
            """
            sm_type = "3"
            sm_subtype = "0"
            """
        elif obj_info.roadMark_type == 6 :                  #도형
            """
            sm_type = "4"
            sm_subtype = "0"
            if obj_info.roadMark_subtype == 257 :           #자전거
                sm_subtype = "535"
            """
            """
            elif obj_info.roadMark_subtype == 256 :           #보행자
                sm_subtype = ""
            """
        elif obj_info.roadMark_type == 1 :
            if obj_info.roadMark_subtype == 256 :             #보행자
                sm_type = "5321"
                sm_subtype = "0"
            elif obj_info.roadMark_subtype == 257 :             #자전거
                sm_type = "534"
                sm_subtype = "0"
        elif obj_info.roadMark_type == 7 :                  #정지선
            sm_type = "530"
            sm_subtype = "0"
            #if sm_type == None or sm_subtype == None :
            #print("{}, {}".format(obj_info.roadMark_type, obj_info.roadMark_subtype))
        return sm_type, sm_subtype

    def get_driving_lane_id_from_st(self, road, s, t) :
        lane_section_idx = get_item_idx_by_s(road.lane_section_list, s, False)
        lane_section_s = road.lane_section_list[lane_section_idx].s
        left_lane_list = road.lane_section_list[lane_section_idx].left_lane_list
        right_lane_list = road.lane_section_list[lane_section_idx].right_lane_list

        lane_id = 0
        current_s_offset = s - lane_section_s
        
        if len(left_lane_list) > 0 and t >= 0 :
            lane_width_total = 0
            for lane in left_lane_list :
                lane_width_item = get_item_by_s(lane.width_list, current_s_offset)
                if lane_width_item == None :
                    lane_id = left_lane_list[0].id
                    break
                lane_width = polynomial(current_s_offset - lane_width_item.s, lane_width_item.a, lane_width_item.b, lane_width_item.c, lane_width_item.d)
                
                if np.abs(lane_width) < np.finfo(float).eps :
                    lane_width = np.finfo(float).eps

                if lane_width < 0 : 
                    lane_width = -lane_width

                lane_width_total += lane_width
                lane_id = lane.id
                if t < lane_width_total :
                    break
        elif len(right_lane_list) > 0 and t <= 0 :
            lane_width_total = 0
            for lane in right_lane_list :
                lane_width_item = get_item_by_s(lane.width_list, current_s_offset)
                if lane_width_item == None :
                    lane_id = right_lane_list[0].id
                    break
                lane_width = polynomial(current_s_offset - lane_width_item.s, lane_width_item.a, lane_width_item.b, lane_width_item.c, lane_width_item.d)

                if np.abs(lane_width) < np.finfo(float).eps :
                    lane_width = np.finfo(float).eps

                if lane_width < 0 : 
                    lane_width = -lane_width

                lane_width_total += lane_width
                lane_id = lane.id
                if np.abs(t) < lane_width_total :
                    break
        elif len(left_lane_list) > 0 :
            lane_id = left_lane_list[0].id
        elif len(right_lane_list) > 0 :
            lane_id = right_lane_list[0].id
        else :
            return None
            
        return (road.id, lane_section_idx, lane_id)

    def process_object(self, xodr_obj, road) :
        #dynamic
        is_dynamic = False
        country = "OpenDRIVE"
        z_offset = xodr_obj.z_offset
        width = xodr_obj.width
        height = xodr_obj.height
        point, hdg = self.get_point(road, xodr_obj.s, xodr_obj.t)
        if z_offset != None :
            point[2] = point[2] + z_offset

        orientation = xodr_obj.orientation
        #if signal.orientation == "+" :
        heading_rad = (xodr_obj.hdg + np.pi + hdg)
        heading = 180 * heading_rad / np.pi 
        #else :
            #heading = 180 * (signal.h_offset + hdg) / np.pi 

        if heading > 360 :
            heading = heading - 360
        elif heading < 0 :
            heading = heading + 360

        re_stencil = re.compile("Stencil_\w+")
        #re_speedlimit = re.compile("Speed_Limit_\d+_\w+")

        if re_stencil.match(xodr_obj.name) :
            re_arrow = re.compile("Stencil_Arrow\w+")
            re_speed = re.compile("Stencil_\d+_\w+")
            sm_type = None
            sm_subtype = None
            if re_arrow.match(xodr_obj.name) :
                sm_type = "1"          #화살표
                if xodr_obj.name in ["Stencil_ArrowType1Long","Stencil_ArrowType1Medium","Stencil_ArrowType1Short","Stencil_ArrowType5"]:
                    sm_subtype = "5371"    #직진
                elif xodr_obj.name in ["Stencil_ArrowType3L","Stencil_ArrowType4L"]:
                    sm_subtype = "5372"    #좌회전
                elif xodr_obj.name in ["Stencil_ArrowType3R","Stencil_ArrowType4R"]:
                    sm_subtype = "5373"    #우회전
                elif xodr_obj.name in ["Stencil_ArrowType2B","Stencil_ArrowType8"]:
                    sm_subtype = "5379"    #전방향
                elif xodr_obj.name in ["Stencil_ArrowType2L","Stencil_ArrowType7L"]:
                    sm_subtype = "5381"    #직진및 좌회전
                elif xodr_obj.name in ["Stencil_ArrowType2R","Stencil_ArrowType7R"]:
                    sm_subtype = "5382"    #직진및 우회전
                elif xodr_obj.name == "Stencil_ArrowType3B":
                    sm_subtype = "5374"    #좌우회전
                elif xodr_obj.name == "Stencil_ArrowUTurn":
                    sm_subtype = "5391"    #유턴
                elif xodr_obj.name == "Stencil_ArrowType6L":
                    sm_subtype = "5431"    #차로변경(좌로합류)
                elif xodr_obj.name == "Stencil_ArrowType6R":
                    sm_subtype = "5432"    #차로변경(우로합류)
                elif xodr_obj.name == "Stencil_HovLane":
                    sm_subtype = "529"     #횡단보도예고
            elif re_speed.match(xodr_obj.name) :
                name_split = xodr_obj.name.split("_")
                speed = name_split[1]
                sm_type = "2"          #속도제한
                sm_subtype = "517_" + speed

            x1 = np.cos(heading_rad) * xodr_obj.length/2
            y1 = np.sin(heading_rad) * xodr_obj.length/2

            x2 = np.cos(heading_rad - np.pi/2) * xodr_obj.width/2
            y2 = np.sin(heading_rad - np.pi/2) * xodr_obj.width/2

            p_left_bottom_x = point[0] - x1 - x2
            p_left_bottom_y = point[1] - y1 - y2

            p_left_top_x = point[0] + x1 - x2
            p_left_top_y = point[1] + y1 - y2

            p_right_bottom_x = point[0] - x1 + x2
            p_right_bottom_y = point[1] - y1 + y2

            p_right_top_x = point[0] + x1 + x2
            p_right_top_y = point[1] + y1 + y2

            points = list()
            points.append([p_left_bottom_x, p_left_bottom_y, point[2]])
            points.append([p_right_bottom_x, p_right_bottom_y, point[2]])
            points.append([p_right_top_x, p_right_top_y, point[2]])
            points.append([p_left_top_x, p_left_top_y, point[2]])
            points.append([p_left_bottom_x, p_left_bottom_y, point[2]])

            lane_item_key = self.get_driving_lane_id_from_st(road, xodr_obj.s, xodr_obj.t)
            sm_data = XodrSurfaceMarkingData(xodr_obj.name, points, sm_type, sm_subtype, lane_item_key)
            self.sm_item_dict["OBJ_" + str(xodr_obj.id)] = sm_data
        #Autoever 데이터 형식 지원
        elif xodr_obj.type in ["structure A", "structure B", "structure C", "roadEdge", "roadMark", "crosswalk"] or xodr_obj.name in ["ConstantSlopeBarrier", "GuardRail", "ChevronRegion", "Crosswalk", "ContinentalCrosswalk", "LadderCrosswalk", "SimpleCrosswalk"]:
            obj_point_list = list()
            is_reverse = False
            is_AutoEver = False
            type_name = xodr_obj.type
            if xodr_obj.type in ["structure A", "structure B", "structure C", "roadEdge", "roadMark"] :
                is_AutoEver = True
            if (is_AutoEver == False) and xodr_obj.name != None :
                type_name = xodr_obj.name
            if len(xodr_obj.corner_road_list) > 0 :
                for cornerRoad in xodr_obj.corner_road_list :
                    if cornerRoad.t > 0 :
                        is_reverse = True
                    point, obj_hdg = self.get_point(road, cornerRoad.s, cornerRoad.t)
                    point[2] += xodr_obj.z_offset
                    obj_point_list.append(point)
            elif len(xodr_obj.corner_local_list) > 0 :
                if xodr_obj.t > 0 :
                    is_reverse = True
                if xodr_obj.s != None and xodr_obj.t != None :
                    point, hdg = self.get_point(road, xodr_obj.s, xodr_obj.t)
                    obj_hdg = hdg + xodr_obj.hdg
                    u_max = None
                    u_min = None
                    for cornerLocal in xodr_obj.corner_local_list :
                        if not is_AutoEver:         #roadrunner 포맷
                            pos_x1 = np.cos(obj_hdg) * cornerLocal.u
                            pos_y1 = np.sin(obj_hdg) * cornerLocal.u

                            pos_x2 = np.cos(obj_hdg + np.pi/2) * cornerLocal.v
                            pos_y2 = np.sin(obj_hdg + np.pi/2) * cornerLocal.v

                            pos_x = point[0] + pos_x1 + pos_x2
                            pos_y = point[1] + pos_y1 + pos_y2
                            pos_z = point[2] + cornerLocal.z + xodr_obj.z_offset
                            if xodr_obj.name == "GuardRail" :
                                pos_z = pos_z - 0.3302
                        else :                      #오토에버
                            if u_max == None or u_max < cornerLocal.u :
                                u_max = cornerLocal.u

                            if u_min == None or u_min > cornerLocal.u  :
                                u_min = cornerLocal.u
                            pos_x1 = np.cos(obj_hdg - np.pi/2) * cornerLocal.u
                            pos_y1 = np.sin(obj_hdg - np.pi/2) * cornerLocal.u

                            pos_x2 = np.cos(obj_hdg) * cornerLocal.v
                            pos_y2 = np.sin(obj_hdg) * cornerLocal.v

                            pos_x = point[0] + pos_x1 + pos_x2
                            pos_y = point[1] + pos_y1 + pos_y2
                            pos_z = point[2] + cornerLocal.z + xodr_obj.z_offset

                        obj_point_list.append([pos_x, pos_y, pos_z])

            if type_name not in self.extra_lanemarking :
                self.extra_lanemarking[type_name] = dict()

            if xodr_obj.type == "roadMark" :
                obj_info = XodrExtraObjectInfo(xodr_obj)
                sm_type, sm_subtype = self.from_AutoEverRM_to_SMCode(obj_info, hdg, obj_point_list)
                if sm_type != None and sm_subtype != None :
                    if sm_type in ["5321", "534"] :
                        self.crosswalk_dict[xodr_obj.id] = XodrCrosswalkItemData(sm_type, obj_point_list)

                    if sm_type == "530" :
                        if u_max - u_min > 0.4 :
                            u_mid = (u_max + u_min)/2
                            obj_point_list = list()
                            for cornerLocal in xodr_obj.corner_local_list :
                                u_val = cornerLocal.u
                                #if u_val > u_mid :
                                    #u_val -= 0.2
                                #else :
                                    #u_val += 0.2
                                pos_x1 = np.cos(obj_hdg - np.pi/2) * u_val
                                pos_y1 = np.sin(obj_hdg - np.pi/2) * u_val

                                pos_x2 = np.cos(obj_hdg) * cornerLocal.v
                                pos_y2 = np.sin(obj_hdg) * cornerLocal.v

                                pos_x = point[0] + pos_x1 + pos_x2
                                pos_y = point[1] + pos_y1 + pos_y2
                                if xodr_obj.z_offset > 0 :
                                    pos_z = point[2] + cornerLocal.z + xodr_obj.z_offset
                                else :
                                    pos_z = point[2] + cornerLocal.z + self.lanemarking_height # + xodr_obj.z_offset

                                if u_val > u_mid :
                                    pos_x = pos_x + np.cos(obj_hdg + np.pi/2) * 0.25
                                    pos_y = pos_y + np.sin(obj_hdg + np.pi/2) * 0.25
                                else :
                                    pos_x = pos_x + np.cos(obj_hdg - np.pi/2) * 0.25
                                    pos_y = pos_y + np.sin(obj_hdg - np.pi/2) * 0.25

                                obj_point_list.append([pos_x, pos_y, pos_z])


                        stop_line_item = XodrStopLineItemData(obj_point_list)
                        self.stop_line_dict[xodr_obj.id] = stop_line_item
                        """"""
                        #TODO :  node 에 on_stop_line 설정
                    else :
                        if is_reverse :
                            obj_point_list.reverse()
                        lane_item_key = self.get_driving_lane_id_from_st(road, xodr_obj.s, xodr_obj.t)
                        sm_data = XodrSurfaceMarkingData(xodr_obj.name, obj_point_list, sm_type, sm_subtype, lane_item_key)
                        self.sm_item_dict["OBJ_" + str(xodr_obj.id)] = sm_data
            elif xodr_obj.type == "crosswalk" or xodr_obj.name in ["Crosswalk", "ContinentalCrosswalk", "LadderCrosswalk", "SimpleCrosswalk"] :
                self.crosswalk_dict[xodr_obj.id] = XodrCrosswalkItemData("5321", obj_point_list)
            else :
                if is_reverse :
                    obj_point_list.reverse()
                if xodr_obj.type == "roadEdge" :
                    self.extra_lanemarking_info[xodr_obj.id] = XodrExtraObjectInfo(xodr_obj)
                self.extra_lanemarking[type_name][xodr_obj.id] = obj_point_list
        else :
            sig_type = None
            sig_subtype = None
            sig_value = None

            if xodr_obj.name in ["StopSign", "Sign_Stop"] :
                sig_type = "2"          #규제표지
                sig_subtype = "227"     #일시정지
            elif xodr_obj.name in ["YieldSign", "Sign_Yield"] :
                sig_type = "2"          #규제표지
                sig_subtype = "228"     #양보
            elif xodr_obj.name == "Sign_BikeLane" :
                sig_type = "3"          #지시표지
                sig_subtype = "302"     #자전거전용도로
            elif xodr_obj.name == "Sign_CrossroadAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "101"     #십자교차로
            elif xodr_obj.name == "Sign_DividedHighwayBegins" :
                sig_type = "1"          #주의표지
                sig_subtype = "123"     #중앙분리대시작
            elif xodr_obj.name == "Sign_DividedHighwayEnds" :
                sig_type = "1"          #주의표지
                sig_subtype = "124"     #중앙분리대끝
            elif xodr_obj.name == "Sign_DoNotBlockIntersection" :
                sig_type = "2"          #규제표지
                sig_subtype = "218"     #정차주차금지
            elif xodr_obj.name == "Sign_DoNotEnter" :
                sig_type = "2"          #규제표지
                sig_subtype = "211"     #진입금지
            elif xodr_obj.name == "Sign_DoNotPass" :
                sig_type = "2"          #규제표지
                sig_subtype = "201"     #통행금지
            elif xodr_obj.name == "Sign_DoubleLeftLaneNoUTurn" :
                sig_type = "2"          #규제표지
                sig_subtype = "216"     #유턴금지
            elif xodr_obj.name == "Sign_KeepRightOfMedian" :
                sig_type = "1"          #주의표지
                sig_subtype = "121"     #유턴금지
            elif xodr_obj.name == "Sign_LaneReductionAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "119"     #우측차로없어짐
            elif xodr_obj.name == "Sign_LeftCurveAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "112"     #좌로굽은도로
            elif xodr_obj.name == "Sign_LeftOrThrough" :
                sig_type = "3"          #지시표지
                sig_subtype = "309"     #직진좌회전
            elif xodr_obj.name == "Sign_LeftOrUTurn" :
                sig_type = "3"          #지시표지
                sig_subtype = "3092"    #좌회전유턴
            elif xodr_obj.name == "Sign_LeftReverseAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "114"     #좌우로이중굽은도로
            elif xodr_obj.name == "Sign_LeftTurn" :
                sig_type = "3"          #지시표지
                sig_subtype = "307"     #좌회전
            elif xodr_obj.name == "Sign_LeftTurnAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "112"     #좌로굽은도로
            elif xodr_obj.name == "Sign_NoLeftTurn" :
                sig_type = "2"          #규제표지
                sig_subtype = "214"     #좌회전 금지
            elif xodr_obj.name in ["Sign_NoParking", "Sign_NoParkingTime"] :
                sig_type = "2"          #규제표지
                sig_subtype = "219"     #주차 금지
            elif xodr_obj.name == "Sign_NoPedestrians" :
                sig_type = "2"          #규제표지
                sig_subtype = "230"     #보행자 금지
            elif xodr_obj.name == "Sign_NoRightTurn" :
                sig_type = "2"          #규제표지
                sig_subtype = "213"     #우회전 금지
            elif xodr_obj.name == "Sign_NoStopping" :
                sig_type = "2"          #규제표지
                sig_subtype = "218"     #주정차 금지
            elif xodr_obj.name == "Sign_NoTrucksOver6000" :
                sig_type = "2"          #규제표지
                sig_subtype = "203"     #화물차 금지
            elif xodr_obj.name == "Sign_NoUTurn" :
                sig_type = "2"          #규제표지
                sig_subtype = "216"     #유턴 금지
            elif xodr_obj.name == "Sign_PedestrianCrossingAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "132"     #횡단보도
            elif xodr_obj.name in ["Sign_Roundabout", "Sign_RoundaboutAhead"] :
                sig_type = "3"          #지시표지
                sig_subtype = "304"     #회전교차로
            elif xodr_obj.name == "Sign_SchoolCrossing" :
                sig_type = "1"          #주의표지
                sig_subtype = "133"     #어린이보호
            elif xodr_obj.name == "Sign_MergingRightLaneAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "107"     #우합류도로
            elif xodr_obj.name == "Sign_SideRoadRightAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "104"     #ㅏ형 교차로
            elif xodr_obj.name == "Sign_SignalAhead" :
                sig_type = "1"          #주의표지
                sig_subtype = "125"     #신호기
            elif xodr_obj.name == "Sign_ThroughOnly" :
                sig_type = "3"          #지시
                sig_subtype = "328"     #일방통행
            elif xodr_obj.name == "Sign_TIntersectionAhead" :
                sig_type = "1"          #주의
                sig_subtype = "102"     #T 형 교차로
            elif xodr_obj.name == "Sign_YIntersectionAhead" :
                sig_type = "1"          #주의
                sig_subtype = "103"     #Y 형 교차로
            elif xodr_obj.name == "Sign_TwoWayTraffic" :
                sig_type = "1"          #주의
                sig_subtype = "115"     #2방향통행
            elif xodr_obj.name.startswith("Sign_SpeedLimit_") :
                sig_type = "2"          #규제
                sig_subtype = "224"     #속도제한
                name_split = xodr_obj.name.split("_")
                sig_value = name_split[2]
            elif xodr_obj.name.startswith("Speed_Limit_") :
                sig_type = "2"          #규제
                sig_subtype = "224"     #속도제한
                name_split = xodr_obj.name.split("_")
                sig_value = name_split[2]

            if sig_type != None and sig_subtype != None :
                link_list = list()
                sig_item = XodrSignalItemData(xodr_obj.name, is_dynamic, country, z_offset, width, height, heading, point, sig_type, sig_subtype, orientation, link_list, sig_value)
                self.sig_item_dict["OBJ_" + str(xodr_obj.id)] = sig_item

    def calc_vtx_slice_idx(self, left_vertices, right_vertices, width_threshold) :
        start_idx = 0
        end_idx = len(left_vertices)

        if len(left_vertices) == len(right_vertices) :
            for i in range(len(left_vertices)) :
                if line3_magnitute([left_vertices[i], right_vertices[i]]) < width_threshold :
                    start_idx += 1
                else :
                    break

            for i in range(len(left_vertices)) :
                if line3_magnitute([left_vertices[-(i+1)], right_vertices[-(i+1)]]) < width_threshold :
                    end_idx -= 1
                else :
                    break

        return start_idx, end_idx

    def process(self):
        parser = XodrParser(self.xodr_file_path)
        ret = parser.parse()
        if(not ret) :
            return

        self.geo_reference = parser.geo_reference
        self.geo_offset = parser.geo_offset

        road_dict = parser.road_data
        self.road_dict = road_dict
        self.controller_dict = parser.controller_data
        sig_ref_dict = dict()
        
        for road_id in road_dict : 
            #if road_id != "61" :
                #continue
            road = road_dict[road_id]
            if road.junction == None :
                road_junction_id = "-1"
            else :
                road_junction_id = road.junction

            for signal in road.signal_list :
                self.process_signal(signal, road)
            
            for road_obj in road.object_list :
                self.process_object(road_obj, road)

            for signal_ref in road.signal_ref_list :
                sig_ref_list = self.process_signal_ref(signal_ref, road)
                if signal_ref.id in sig_ref_dict :
                    sig_ref_dict[signal_ref.id].extend(sig_ref_list)
                else :
                    sig_ref_dict[signal_ref.id] = sig_ref_list

            for lane_section_idx in range(len(road.lane_section_list)):
                #max_speed 기본값
                max_speed = 50
                if len(road.type_list) > 0 :
                    lane_section_s = road.lane_section_list[lane_section_idx].s
                    road_type = get_item_by_s(road.type_list, lane_section_s)
                    if road_type != None :
                        if road_type.speed_unit == "mph" : 
                            max_speed = road_type.speed_max * 1.609344
                        elif road_type.speed_unit == "km/h" : 
                            max_speed = road_type.speed_max
                        elif road_type.speed_unit == "m/s" : 
                            max_speed = road_type.speed_max * 60 * 60 / 1000

                pre_road_id = None
                pre_lane_section_idx = None
                pre_contact_point = None

                if lane_section_idx > 0 :
                    pre_road_id = road_id
                    pre_lane_section_idx = lane_section_idx - 1
                    pre_contact_point = "end"
                else :
                    if road.predecessor != None and road.predecessor.elementType == "road" :
                        pre_road_id = road.predecessor.elementId
                        if pre_road_id in road_dict :
                            pre_road = road_dict[pre_road_id]
                            pre_lane_section_idx = len(pre_road.lane_section_list) - 1
                            pre_contact_point = "end"
                            if road.predecessor.contactPoint == "start" :
                                pre_contact_point = "start"
                                pre_lane_section_idx = 0

                suc_road_id = None
                suc_lane_section_idx = None
                suc_contact_point = None

                if lane_section_idx < (len(road.lane_section_list) - 1) :
                    suc_road_id = road_id
                    suc_lane_section_idx = lane_section_idx + 1
                    suc_contact_point = "start"
                else :
                    if road.successor != None and road.successor.elementType == "road" :
                        suc_road_id = road.successor.elementId
                        if suc_road_id in road_dict :
                            suc_road = road_dict[suc_road_id]
                            suc_lane_section_idx = 0
                            suc_contact_point = "start"
                            if road.successor.contactPoint == "end" :
                                suc_lane_section_idx = len(suc_road.lane_section_list) - 1
                                suc_contact_point = "end"

                lane_section = road.lane_section_list[lane_section_idx]
                
                left_vertex_data = self.gen_lane_vertices(road, lane_section.left_lane_list, lane_section.s, lane_section.length, "left")
                right_vertex_data = self.gen_lane_vertices(road, lane_section.right_lane_list, lane_section.s, lane_section.length, "right")

                self.gen_lanemarking_vertices(road, lane_section_idx, lane_section.left_lane_list, lane_section.s, lane_section.length, "left", self.lanemarking_dict)
                self.gen_lanemarking_vertices(road, lane_section_idx, [lane_section.center_lane], lane_section.s, lane_section.length, "center", self.lanemarking_dict, len(lane_section.left_lane_list) > 0, len(lane_section.right_lane_list) > 0)
                self.gen_lanemarking_vertices(road, lane_section_idx, lane_section.right_lane_list, lane_section.s, lane_section.length, "right", self.lanemarking_dict)

                lane_type_set = LaneBoundarySet()

                lane_center_line = lane_section.center_lane
                lane_idx = str(lane_section.center_lane.id)
                lane = LaneBoundary(idx=lane_idx)
                for road_mark in lane_center_line.road_mark_list:
                    lane.lane_width = road_mark.width
                    lane.pass_restr = road_mark.lane_change
                    if road_mark.color is None:
                        lane.lane_color.append('none')
                    else:
                        lane.lane_color.append(road_mark.color)
                    lane.lane_type.append(0)
                    lane.lane_type_offset.append(road_mark.s)
                    if road_mark.color is None:
                        lane.lane_shape.append('none')
                    else:
                        lane.lane_shape.append(road_mark.type)
                lane_type_set.append_line(lane)

                lane_right_lines = lane_section.right_lane_list
                for right_lane in lane_right_lines:
                    lane_idx = str(right_lane.id)
                    lane = LaneBoundary(idx=lane_idx)
                    for road_mark in right_lane.road_mark_list:
                        lane.lane_width = road_mark.width
                        lane.pass_restr = road_mark.lane_change
                        if road_mark.color is None:
                            lane.lane_color.append('none')
                        else:
                            lane.lane_color.append(road_mark.color)
                        lane.lane_type.append(0)
                        lane.lane_type_offset.append(road_mark.s)
                        if road_mark.color is None:
                            lane.lane_shape.append('none')
                        else:
                            lane.lane_shape.append(road_mark.type)
                    lane_type_set.append_line(lane)


                for i in range(len(lane_section.left_lane_list)) :
                    ref_vertices = left_vertex_data[lane_section.left_lane_list[0].id][0::2]
                    lane = lane_section.left_lane_list[i]
                    lane_vertex_list = left_vertex_data[lane.id]
                    left_vertices, right_vertices, center_vertices = self.to_lane_vertices(lane_vertex_list)
                    
                    left_lane_id = None
                    right_lane_id = None
                    
                    if i < len(lane_section.left_lane_list)-1 :
                        left_lane_id = lane_section.left_lane_list[i + 1].id
                    if i > 0 :
                        right_lane_id = lane_section.left_lane_list[i - 1].id
                    else :
                        if (lane_section.right_lane_list != None) and (len(lane_section.right_lane_list) > 0) :
                            right_lane_id = lane_section.right_lane_list[0].id

                    left_lane_item = (road_id, lane_section_idx, left_lane_id) if left_lane_id != None else None
                    right_lane_item = (road_id, lane_section_idx, right_lane_id) if right_lane_id != None else None

                    pre_lane_item = None
                    if pre_road_id != None and pre_lane_section_idx != None and pre_contact_point != None and lane.predecessor != None :
                        pre_lane_item = (pre_road_id, pre_lane_section_idx, lane.predecessor, pre_contact_point)

                    suc_lane_item = None
                    if suc_road_id != None and suc_lane_section_idx != None and suc_contact_point != None and lane.successor != None :
                        suc_lane_item = (suc_road_id, suc_lane_section_idx, lane.successor, suc_contact_point)

                    can_move_left = False
                    can_move_right = False
                    
                    if i == 0 and lane_section.center_lane.lane_change_right :
                        can_move_right = True
                    elif i > 0 and lane_section.left_lane_list[i-1].lane_change_right :
                        can_move_right = True

                    if lane.lane_change_left :
                        can_move_left = True

                    lane_item_key = (road_id, lane_section_idx, lane.id)

                    self.lanenode_KDTreeData.append(vertexTo2D(left_vertices[0]))
                    self.lanenode_data.append((lane_item_key,"left","start"))
                    self.lanenode_KDTreeData.append(vertexTo2D(left_vertices[-1]))
                    self.lanenode_data.append((lane_item_key,"left","end"))
                    self.lanenode_KDTreeData.append(vertexTo2D(right_vertices[0]))
                    self.lanenode_data.append((lane_item_key,"right","start"))
                    self.lanenode_KDTreeData.append(vertexTo2D(right_vertices[-1]))
                    self.lanenode_data.append((lane_item_key,"right","end"))
                    
                    s_idx, e_idx = self.calc_vtx_slice_idx(left_vertices, right_vertices, 2.0)
                    
                    lane_item = XodrLaneItemData(road_id, lane_section_idx, lane.id, 
                                    lane.type, left_vertices, right_vertices, center_vertices, 
                                    ref_vertices, left_lane_item, right_lane_item, 
                                    can_move_left, can_move_right, max_speed, road_junction_id)
                    lane_item.center_vtx_s_idx = s_idx
                    lane_item.center_vtx_e_idx = e_idx
                    lane_item.lane_type_set = lane_type_set
                    
                    if pre_lane_item != None : 
                        lane_item.add_predecessor(pre_lane_item)
                    if suc_lane_item != None :
                        lane_item.add_successor(suc_lane_item)
                    self.lane_item_dict[lane_item_key] = lane_item

                for i in range(len(lane_section.right_lane_list)) :
                    ref_vertices = right_vertex_data[lane_section.right_lane_list[0].id][1::2]
                    lane = lane_section.right_lane_list[i]
                    lane_vertex_list = right_vertex_data[lane.id]
                    left_vertices, right_vertices, center_vertices = self.to_lane_vertices(lane_vertex_list)

                    left_lane_id = None
                    right_lane_id = None

                    if i < len(lane_section.right_lane_list)-1 :
                        right_lane_id = lane_section.right_lane_list[i + 1].id

                    if i > 0 :
                        left_lane_id = lane_section.right_lane_list[i - 1].id
                    else :
                        if (lane_section.left_lane_list != None) and (len(lane_section.left_lane_list) > 0) :
                            left_lane_id = lane_section.left_lane_list[0].id

                    left_lane_item = (road_id, lane_section_idx, left_lane_id) if left_lane_id != None else None
                    right_lane_item = (road_id, lane_section_idx, right_lane_id) if right_lane_id != None else None

                    pre_lane_item = None
                    if pre_road_id != None and pre_lane_section_idx != None and pre_contact_point != None and lane.predecessor != None :
                        pre_lane_item = (pre_road_id, pre_lane_section_idx, lane.predecessor, pre_contact_point)

                    suc_lane_item = None
                    if suc_road_id != None and suc_lane_section_idx != None and suc_contact_point != None and lane.successor != None :
                        suc_lane_item = (suc_road_id, suc_lane_section_idx, lane.successor, suc_contact_point)

                    can_move_left = False
                    can_move_right = False
                    
                    if i == 0 and lane_section.center_lane.lane_change_left :
                        can_move_left = True
                    elif i > 0 and lane_section.right_lane_list[i-1].lane_change_left :
                        can_move_left = True

                    if lane.lane_change_right :
                        can_move_right = True

                    lane_item_key = (road_id, lane_section_idx, lane.id)

                    self.lanenode_KDTreeData.append(vertexTo2D(left_vertices[0]))
                    self.lanenode_data.append((lane_item_key,"left","start"))
                    self.lanenode_KDTreeData.append(vertexTo2D(left_vertices[-1]))
                    self.lanenode_data.append((lane_item_key,"left","end"))
                    self.lanenode_KDTreeData.append(vertexTo2D(right_vertices[0]))
                    self.lanenode_data.append((lane_item_key,"right","start"))
                    self.lanenode_KDTreeData.append(vertexTo2D(right_vertices[-1]))
                    self.lanenode_data.append((lane_item_key,"right","end"))

                    s_idx, e_idx = self.calc_vtx_slice_idx(left_vertices, right_vertices, 2.0)

                    lane_item = XodrLaneItemData(road_id, lane_section_idx, lane.id, 
                            lane.type, left_vertices, right_vertices, center_vertices, 
                            ref_vertices, left_lane_item, right_lane_item, 
                            can_move_left, can_move_right, max_speed, road_junction_id)
                    lane_item.center_vtx_s_idx = s_idx
                    lane_item.center_vtx_e_idx = e_idx
                    lane_item.lane_type_set = lane_type_set

                    if pre_lane_item != None : 
                        lane_item.add_predecessor(pre_lane_item)
                    if suc_lane_item != None :
                        lane_item.add_successor(suc_lane_item)
                    self.lane_item_dict[lane_item_key] = lane_item

        for sig_id in sig_ref_dict :
            if sig_id in self.sig_item_dict :
                sig_item = self.sig_item_dict[sig_id]
                sig_ref_list = sig_ref_dict[sig_id]
                for sig_ref_key in sig_ref_list :
                    sig_item.link_list.append(sig_ref_key)

        junction_dict = parser.junction_data
        self.junction_dict = junction_dict

        for junction_id in junction_dict:
            #continue
            junction = junction_dict[junction_id]
            for connection in junction.connection_list:
                if connection.connecting_road in road_dict:
                    incoming_road = None
                    if (connection.incoming_road != None) and (connection.incoming_road in road_dict) :
                        incoming_road = road_dict[connection.incoming_road]
                    connecting_road = road_dict[connection.connecting_road]
                    to_contact_point = connection.contact_point

                    to_lane_section_idx = None
                    if to_contact_point == "start" :
                        to_lane_section_idx = 0
                    elif to_contact_point == "end" :
                        to_lane_section_idx = len(connecting_road.lane_section_list) - 1

                    from_lane_section_idx = None
                    from_contact_point = None
                    if incoming_road != None :
                        if incoming_road.predecessor != None and incoming_road.predecessor.elementType == "junction" and incoming_road.predecessor.elementId == junction_id : 
                            from_lane_section_idx = 0
                            from_contact_point = "start"
                        if incoming_road.successor != None and incoming_road.successor.elementType == "junction" and incoming_road.successor.elementId == junction_id : 
                            from_lane_section_idx = len(incoming_road.lane_section_list) - 1
                            from_contact_point = "end"

                    if from_lane_section_idx != None and to_lane_section_idx != None:
                        for lane_link in connection.lane_link_list :
                            from_item_key = (connection.incoming_road, from_lane_section_idx, lane_link.from_link)
                            to_item_key = (connection.connecting_road, to_lane_section_idx, lane_link.to_link)

                            if from_item_key in self.lane_item_dict :
                                lane_item = self.lane_item_dict[from_item_key]
                                to_lane_item = (connection.connecting_road, to_lane_section_idx, lane_link.to_link, to_contact_point)
                                if from_contact_point == "start" :
                                    lane_item.add_predecessor(to_lane_item)
                                else :
                                    lane_item.add_successor(to_lane_item)

                            if to_item_key in self.lane_item_dict :
                                lane_item = self.lane_item_dict[to_item_key]
                                from_lane_item = (connection.incoming_road, from_lane_section_idx, lane_link.from_link, from_contact_point)
                                if to_contact_point == "start" :
                                    lane_item.add_predecessor(from_lane_item)
                                else :
                                    lane_item.add_successor(from_lane_item)