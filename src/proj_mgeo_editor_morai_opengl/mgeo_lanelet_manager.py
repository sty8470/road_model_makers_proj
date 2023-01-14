import os

from lib.common import vtk_utils
from lib.lanelet.osm_utils import *
from lib.mgeo.class_defs import *
from lib.mgeo.class_defs.line_set import LineSet
from lib.mgeo.class_defs.link import Link
from lib.mgeo.class_defs.node import Node
from lib.mgeo.class_defs.lane_boundary import LaneBoundary
from lib.mgeo.class_defs.lane_boundary_set import LaneBoundarySet
from lib.mgeo.class_defs.road_polygon import RoadPolygon
from lib.mgeo.class_defs.road_polygon_set import RoadPolygonSet
from lib.mgeo.save_load.subproc_load_link_ver1 import load_node_and_link
from lib.opendrive.mesh_utils import *
from lib.opendrive.xodr_converter import group_by_clip
current_path = os.path.dirname(os.path.realpath(__file__))
import numpy
from lib.common.logger import Logger
from lib.common.singleton import Singleton
from lib.mgeo.class_defs.lane_boundary_set import LaneBoundarySet
from lib.mgeo.class_defs.mgeo import MGeo
from lib.mgeo.class_defs.node_set import NodeSet
from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
# from osm_node import OsmNodeData
from osm_data import *
from pyproj import Proj, Transformer, CRS, crs
from lib.common.coord_trans_ll2utm import CoordTrans_LL2UTM

from xml.etree.ElementTree import parse


class MgeoToLanenetDataManager(Singleton) :

    def __init__(self):
        '''
        self.node_id_dic = dict() # key : mgeo node idx, value : osm id
        self.link_id_dic = dict() # key : mgeo link idx, value : list() - 링크에 속한 points 순서대로 osm id 를 부여.       위 두개는 osm node id만 가지고 있음.
        self.mgeo_link_to_osm_way_id_dic = dict()
        
        self.lane_node_id_dic = dict()
        self.lane_marking_id_dic = dict() # 위 두개는 osm node id만 가지고 있음.

        self.node_dic = dict()
        self.lane_node_dic = dict()
        '''

        ## refactoring.
        # node
        # way
        # relation - lanelet
        """
        범용성 있도록, 구조를 다시 잡아보자.
        """
        # osm 노드 key : mgeo id, value : OsmNodeData
        self.osm_node_dic = dict()
        self.osm_node_list = list()
        self.osm_way_dic = dict()
        self.osm_lanelet_list = list()

    def clear_Data(self) :
        self.osm_node_dic.clear()
        self.osm_node_list.clear()
        self.osm_way_dic.clear()
        self.osm_lanelet_list.clear()


    def start_convert(self, mgeo_data) :
        self.clear_Data()

        self.set_Mgeo_Data(mgeo_data)
        self.initGlobalPosition(mgeo_data)
        self.organizeLaneNode()
        self.organizeLanelet()


    def set_Mgeo_Data(self, mgeo_data) :
        self.mgeo_data = mgeo_data


    def initGlobalPosition(self, mgeo_data):
        # 위도, 경도
        self.orig_x = mgeo_data.local_origin_in_global[0]
        self.orig_y = mgeo_data.local_origin_in_global[1]
        self.orig_z = mgeo_data.local_origin_in_global[2]
        self.coord_system = mgeo_data.global_coordinate_system
        
        # 초기화 방법: https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj.Proj.__init__
        # proj_obj = Proj('epsg:32652') # UTM52N 좌표의 EPSG 코드 (32652)를 이용하여 초기화
        # 또는 PROJ string을 이용하는 것도 가능하다
        # 아래 PROJ string은 https://epsg.io/?format=json&q=32652 를 통해 받아올 수 있음
        self.proj_obj = Proj(self.coord_system)
        
    def convert_wgs84_coodinate(self, pos_x, pos_y, pos_z) :
        # lat, lon = utm.to_latlon(pos_x + self.orig_x, pos_y + self.orig_y, 52, 'U') # tjjung. 이거 정확하게 zone 가져오는 거 해야합니당.
        ele = pos_z                                                                         # 그대로 넣어 줍니다.
        lon, lat = self.proj_obj(pos_x + self.orig_x, pos_y + self.orig_y, inverse=True)
        return lat, lon, ele
    

    def organizeLaneNode(self) :
        lane_boundary_set = self.mgeo_data.lane_boundary_set.lanes
        lane_node_set = self.mgeo_data.lane_node_set.nodes

        osm_node_id = 1
        osm_way_id = 1
        for l_k, l_v in lane_boundary_set.items() :
            from_node_idx = l_v.from_node.idx # from node, to node 는 있다는 가정 하에 작업합니다.
            to_node_idx = l_v.to_node.idx
            points = l_v.points

            points_len = len(points)
            points_idx = 0


            type = "line_thin"
            if 0.15 < l_v.lane_width:
                type = "line_thick"

            sub_type = "solid"
            if l_v.lane_type == 530 :
                sub_type = "stop_line"
            elif 'Broken' in l_v.lane_shape:
                sub_type = "dashed"
        
            

            osm_way_data = OsmWayData()
            osm_way_data.id = osm_way_id
            osm_way_data.type = type
            osm_way_data.subtype = sub_type

            for p_i in points:
                mgeo_id = 0
                if (points_idx == 0) and (from_node_idx in lane_node_set) :
                    mgeo_id = from_node_idx
                elif (points_idx == points_len - 1) and (to_node_idx in lane_node_set) :
                    mgeo_id = to_node_idx
                else :
                    mgeo_id = l_k + str('_') + str(points_idx)

                lat, lon, ele = self.convert_wgs84_coodinate(p_i[0], p_i[1], p_i[2])
                osm_node = OsmNodeData()
                osm_node.setNodeData(osm_node_id, lat, lon, ele)
                osm_node.mgeo_id = mgeo_id

                # way에 node 추가.
                osm_way_data.addNodeId(osm_node.id)
                
                # node 추가.
                self.osm_node_list.append(osm_node)

                # node idx 증가
                osm_node_id += 1
                # points idx 증가
                points_idx += 1

            # way 한개 생성 추가.
            self.osm_way_dic[l_k] = osm_way_data
            # way idx 증가
            osm_way_id += 1

    
    def organizeLanelet(self) :
        link_set = self.mgeo_data.link_set.lines

        way_id = 1
        for l_k, l_v in link_set.items() :
            
            # if (l_v.link_type == 'Driving') == False : continue # 자동차 주행도로만 구성하도록.

            lane_left = l_v.lane_mark_left
            lane_right = l_v.lane_mark_right

            osm_left = self.osm_way_dic[lane_left[0].idx]
            osm_right = self.osm_way_dic[lane_right[0].idx]

            osm_lanelet_data = OsmLaneletData()
            osm_lanelet_data.id = way_id
            osm_lanelet_data.left = osm_left.id
            osm_lanelet_data.right = osm_right.id
            
            self.osm_lanelet_list.append(osm_lanelet_data)
            way_id += 1



class LaneletStructure :
    def __init__(self) :
        self.left_points = None
        self.right_points = None
        self.center_points = None
        self.from_node = None
        self.to_node = None
        self.left_from_node = None
        self.left_to_node = None
        self.right_from_node = None
        self.right_to_node = None

class OsmConverter :
    def __init__(self, osm_file_path):
        self.osm_file_path = osm_file_path

        self.zone = None
        # node dic
        self.dic_node = dict()
        # way dic
        self.dic_way = dict()
        # relation dic
        self.dic_relation = dict()
        # offset
        self.offset_coord = list()
        # lanelet dictionary
        self.lanelet_dict = dict()
        self.road_poly_list = list()
        self.node_list = list()
        self.lanenode_list = list()
        self.crosswalk_dict = dict()

        #TODO : 추후에 설정할 수 있도록 바꿀 필요가 있음
        self.z_tolerance = 0.5

    def parse(self) :
        if not os.path.isfile(self.osm_file_path):
            return False

        tree = etree.parse(self.osm_file_path)
        root = tree.getroot()        
        # node
        nodes = root.findall("node")

        # offset
        first_node = root.find("node")
        self.create_offset_coord(first_node)

        for node_element in nodes :
            node_id = node_element.attrib["id"]
            node_lat = node_element.attrib["lat"]
            node_lon = node_element.attrib["lon"]

            tags = node_element.findall("tag")
            ele = '0'
            for t_iter in tags :
                k = t_iter.attrib["k"]
                v = t_iter.attrib["v"]
                if k == "ele" :
                    ele = v 

            node_data = OsmNodeData()
            node_data.setNodeData(node_id, node_lat, node_lon, ele)

            self.dic_node[node_id] = node_data

        # way
        ways = root.findall("way")

        for way_element in ways :
            way_data = OsmWayData()
            way_id = way_element.attrib["id"]
            way_data.id = way_id

            node_list = way_element.findall("nd")
            for nd in node_list :
                node_id = nd.attrib["ref"]
                way_data.addNodeId(node_id)
            
            self.dic_way[way_id] = way_data

        # relation
        relations = root.findall("relation")

        for relation_element in relations :
            # lanelet type인지 체크.
            tags = relation_element.findall("tag")
            is_lanelet = False
            is_way = True
            turn_dir = None
            type = None
            subtype = None
            for t_iter in tags :
                k = t_iter.attrib["k"]
                v = t_iter.attrib["v"]
                if k == "type" :
                    type = v
                    if v == "lanelet" :
                        is_lanelet = True
                elif k == "subtype" :
                    subtype = v
                elif k == "turn_direction" :
                    # 교차로.
                    turn_dir = v

                # if k == "subtype" and v == "road" :
                #     is_way = True

            if is_lanelet == False or is_way == False:
                continue
            
            r_id = relation_element.attrib["id"]
            
            lanelet_data = OsmLaneletData()
            if type != None :
                lanelet_data.type = type
            if subtype != None :
                lanelet_data.subtype = subtype
                
            lanelet_data.id = r_id
            if turn_dir != None :
                lanelet_data.turn_dir = turn_dir

            member_list = relation_element.findall("member")
            for m_iter in member_list :
                type = m_iter.attrib["type"]
                role = m_iter.attrib["role"]
                ref = m_iter.attrib["ref"]

                if type == "way" and role == "left" :
                    lanelet_data.left = ref
                elif type == "way" and role == "right" :
                    lanelet_data.right = ref

            self.dic_relation[r_id] = lanelet_data

            
        return True

    def create_offset_coord(self, node) :
        node_lat = node.attrib["lat"]
        node_lon = node.attrib["lon"]
        tags = node.findall("tag")
        ele = '0'
        for t_iter in tags :
            k = t_iter.attrib["k"]
            v = t_iter.attrib["v"]
            if k == "ele" :
                ele = v 
        node_point = [float(node_lat), float(node_lon), float(ele)]
        self.zone = self.utm_zone(node_point)
        obj = CoordTrans_LL2UTM(self.zone)
        east, north = obj.ll2utm(node_point[0], node_point[1])

        self.offset_coord.append(east)
        self.offset_coord.append(north)

    def utm_zone(self, point):
        lat = point[0]
        lon = point[1]
        num = 180 + lon
        zone_con = int(num//6)
        return zone_con+1

    def convert_point(self, point):
        zone = self.utm_zone(point)
        obj = CoordTrans_LL2UTM(zone)
        east, north = obj.ll2utm(point[0], point[1])

        new_data_point = [east - self.offset_coord[0], north - self.offset_coord[1], point[2]]
        return numpy.array(new_data_point)

    def find_lanenode_by_point(self, point, tolerance) :
        return self.find_node_by_point(point, tolerance, self.lanenode_list)

    def find_node_by_point(self, point, tolerance, node_list=None) :
        ret = None
        if node_list == None :
            node_list = self.node_list

        for node in node_list :
            diff = node.point - point
            if np.linalg.norm(np.array(diff)) < tolerance :
                ret = node
                break
        return ret

    def round_point(self, point, digit) :
        point[0] = round(point[0], digit)
        point[1] = round(point[1], digit)
        point[2] = round(point[2], digit)

        return point

    def gen_center_points(self, left_points, right_points) :
        left_total_length = 0
        for i in range(len(left_points) - 1) :
            mag = np.linalg.norm(np.array(left_points[i] - left_points[i + 1]))
            left_total_length += mag

        right_total_length = 0
        for i in range(len(right_points) - 1) :
            mag = np.linalg.norm(np.array(right_points[i] - right_points[i + 1]))
            right_total_length += mag

        if left_total_length < right_total_length :
            length_ratio = left_total_length/right_total_length
            pivot_points = right_points
            target_points = left_points
        else :
            length_ratio = right_total_length/left_total_length
            pivot_points = left_points
            target_points = right_points

        center_points = list()
        pivot_length = 0.0
        for i in range(len(pivot_points)) :
            if i == 0 :
                center_point = (pivot_points[i] + target_points[i]) / 2
                center_point = self.round_point(center_point, 12)
                center_points.append(center_point)
            elif i == len(pivot_points)-1 :
                center_point = (pivot_points[-1] + target_points[-1]) / 2
                center_point = self.round_point(center_point, 12)
                center_points.append(center_point)
            else :
                pivot_length += np.linalg.norm(np.array(pivot_points[i] - pivot_points[i - 1]))
                remain_length = pivot_length * length_ratio
                for j in range(len(target_points) - 1) :
                    mag = np.linalg.norm(np.array(target_points[j] - target_points[j + 1]))
                    if mag >= remain_length :
                        match_point = target_points[j] + ((target_points[j + 1] - target_points[j]) * (remain_length / mag))
                        center_point = (pivot_points[i] + match_point) / 2
                        center_point = self.round_point(center_point, 12)
                        center_points.append(center_point)
                        break
                    else :
                        remain_length -= mag

        return center_points

    def sum_of_cross(self, left_points, right_points) :
        sum_of_cross = np.array([0.0,0.0,0.0])
        for i in range(len(left_points) - 1) :
            sum_of_cross += np.cross(left_points[i], left_points[i + 1])
        sum_of_cross += np.cross(left_points[-1], right_points[0])
        for i in range(len(right_points) - 1) :
            sum_of_cross += np.cross(right_points[i], right_points[i + 1])
        sum_of_cross += np.cross(right_points[-1], left_points[0])
        
        return sum_of_cross

    def gen_lanelet_data(self):
        for key, value in self.dic_relation.items() :
            left_way_id = value.left
            right_way_id = value.right
            
            left_way = self.dic_way[left_way_id]
            right_way = self.dic_way[right_way_id]

            left_points = list()
            right_points = list()

            for ld_id in left_way.node_list :
                if ld_id in self.dic_node :
                    node_data = self.dic_node[ld_id]
                    point = numpy.array([float(node_data.lat), float(node_data.lon), float(node_data.ele)])
                    point = self.convert_point(point)
                    point = self.round_point(point, 12)
                    left_points.append(point)

            for ld_id in right_way.node_list :
                if ld_id in self.dic_node :
                    node_data = self.dic_node[ld_id]
                    point = numpy.array([float(node_data.lat), float(node_data.lon), float(node_data.ele)])
                    point = self.convert_point(point)
                    point = self.round_point(point, 12)
                    right_points.append(point)

            # 구조체 담기.
            # left, right way 의 점들의 방향이 반대일 수 있다.
            seg_1 = [left_points[0], right_points[0]]
            seg_2 = [left_points[-1], right_points[-1]]

            intersect_point = get_intersect_point2D_with_segment(seg_1, seg_2)
            is_right_reversed = False
            if intersect_point != None :
                is_right_reversed = True
            else :
                foward_v = left_points[0] - right_points[0]
                reverse_v = left_points[0] - right_points[-1]
                foward_mag = np.linalg.norm(np.array(foward_v))
                reverse_mag = np.linalg.norm(np.array(reverse_v))
                if foward_mag > reverse_mag :
                    is_right_reversed = True
            
            # 뒤집어진 face 찾기.
            left_point_list = list(left_points)
            right_point_list = None

            #오른쪽을 반대방향으로
            if is_right_reversed : 
                right_point_list = list(right_points)
            else : 
                right_point_list = list(reversed(right_points))
            
            # 뒤집혔는가?
            sum_of_cross = self.sum_of_cross(left_point_list, right_point_list)
            if sum_of_cross[2] > 0 :
                right_point_list = list(reversed(right_point_list))
                left_point_list = list(reversed(left_point_list))

            if value.type == "lanelet" :
                vertices = list()
                vertices.extend(left_point_list)
                vertices.extend(right_point_list)

                if value.subtype == "crosswalk" :
                    self.crosswalk_dict[value.id] = np.array(vertices)
                elif value.subtype in ["road", "lane"] :    
                    center_points = self.gen_center_points(left_point_list, list(reversed(right_point_list)))

                    lanelet_structure = LaneletStructure()
                    lanelet_structure.left_points = left_point_list
                    lanelet_structure.right_points = right_point_list
                    lanelet_structure.center_points = center_points

                    node_from = self.find_node_by_point(center_points[0], 0.1)
                    if node_from == None :
                        node_from = Node()
                        node_from.point = np.array(center_points[0])
                        self.node_list.append(node_from)
                    lanelet_structure.from_node = node_from
                    
                    node_to = self.find_node_by_point(center_points[-1], 0.1)
                    if node_to == None :
                        node_to = Node()
                        node_to.point = np.array(center_points[-1])
                        self.node_list.append(node_to)
                    lanelet_structure.to_node = node_to

                    leftnode_from = self.find_lanenode_by_point(left_points[0], 0.1)
                    if leftnode_from == None :
                        leftnode_from = Node()
                        leftnode_from.point = np.array(left_points[0])
                        self.lanenode_list.append(leftnode_from)
                    lanelet_structure.left_from_node = leftnode_from

                    leftnode_to = self.find_lanenode_by_point(left_points[-1], 0.1)
                    if leftnode_to == None :
                        leftnode_to = Node()
                        leftnode_to.point = np.array(left_points[-1])
                        self.lanenode_list.append(leftnode_to)
                    lanelet_structure.left_to_node = leftnode_to

                    rightnode_from = self.find_lanenode_by_point(right_points[0], 0.1)
                    if rightnode_from == None :
                        rightnode_from = Node()
                        rightnode_from.point = np.array(right_points[0])
                        self.lanenode_list.append(rightnode_from)
                    lanelet_structure.right_from_node = rightnode_from

                    rightnode_to = self.find_lanenode_by_point(right_points[-1], 0.1)
                    if rightnode_to == None :
                        rightnode_to = Node()
                        rightnode_to.point = np.array(right_points[-1])
                        self.lanenode_list.append(rightnode_to)
                    lanelet_structure.right_to_node = rightnode_to

                    lane_poly = vtkPolyByPoints(vertices)
                    lane_poly = vtkTrianglePoly(lane_poly)
                    self.lanelet_dict[key] = lanelet_structure
                    self.road_poly_list.append([lane_poly, vertices])

    '''
    MGeo 생성 함수.
    '''
    def convert_to_mgeo(self):
        self.parse()
        self.gen_lanelet_data()

        #Node Set
        nodeset = NodeSet()
        for node in self.node_list :
            nodeset.append_node(node, True)

        #Lane Node Set
        lanenodeset = NodeSet()
        for lanenode in self.lanenode_list :
            lanenodeset.append_node(lanenode, True)

        #crosswalk
        cw_set = CrossWalkSet()
        scw_set = SingleCrosswalkSet()

        for idx in self.crosswalk_dict :
            cw_vertices = self.crosswalk_dict[idx]
            scw_idx = "SCW_" + str(idx)
            cw_idx = "CW_" + str(idx)
            scw = SingleCrosswalk(cw_vertices, scw_idx, "5321")
            scw.ref_crosswalk_id = cw_idx

            cw = Crosswalk(cw_idx)
            cw.append_single_scw_list(scw)

            scw_set.append_data(scw, False)
            cw_set.append_data(cw)

        #주행경로 Link / LaneBoundary
        linkset = LineSet()
        laneboundaryset = LaneBoundarySet()
        for key, lanelet in self.lanelet_dict.items() :
            #주행경로 링크
            link = Link(np.array(lanelet.center_points))
            linkset.append_line(link, True)
            lanelet.from_node.add_to_links(link)
            lanelet.to_node.add_from_links(link)

            #좌측 laneboundary
            laneboundary = LaneBoundary(np.array(lanelet.left_points))
            laneboundaryset.append_line(laneboundary, True)
            lanelet.left_from_node.add_to_links(laneboundary)
            lanelet.left_to_node.add_from_links(laneboundary)

            #우측 laneboundary
            laneboundary = LaneBoundary(np.array(lanelet.right_points))
            laneboundaryset.append_line(laneboundary, True)
            lanelet.right_from_node.add_to_links(laneboundary)
            lanelet.right_to_node.add_from_links(laneboundary)

        #roadpoly
        road_poly_set = RoadPolygonSet()
        """
        #메쉬 병합하지 않고 출력
        for i in range(len(self.road_poly_list)) :
            poly = self.road_poly_list[i][0]
            points, faces = vtkPoly_to_MeshData(poly)
            road_poly = RoadPolygon(points, faces, None, "road")
            road_poly_set.append_data(road_poly, True)
        """
        grouped_list = group_by_clip(self.road_poly_list, self.z_tolerance)
        for i in range(len(grouped_list)) :
            #길이가 1 이면 그냥 append, 아니면 union
            if len(grouped_list[i]) == 1:
                
                # 반시계방향으로 변경해준다. noraml  방향을 맞추기 위해서.
                vertices = grouped_list[i][0][1][::-1]
                vtk_poly = vtkPolyByPoints(vertices)
                vtk_poly = vtkTrianglePoly(vtk_poly)
                points, faces = vtkPoly_to_MeshData(vtk_poly)
                #points, faces = vtkPoly_to_MeshData(grouped_list[i][0][0])
                road_poly = RoadPolygon(points, faces, None, "road")
                road_poly_set.append_data(road_poly, True)
            else :
                uinon_bound = UnionMeshBound(self.z_tolerance)
                for road_data in grouped_list[i] :
                    road_bound = road_data[1]
                    uinon_bound.add(road_bound)
                uinon_bound.process(True)

                for result in uinon_bound.result_list :
                    if len(result) < 4 :
                        continue
                    vtk_vertices = vtk.vtkPoints()  # 점 정보
                    vtk_faces = vtk.vtkCellArray()
                    vtk_faces.InsertNextCell(len(result))
                    
                    for point in result :
                        point_id = vtk_vertices.InsertNextPoint(point)
                        vtk_faces.InsertCellPoint(point_id)

                    poly_result = vtk.vtkPolyData()
                    poly_result.SetPoints(vtk_vertices)
                    poly_result.SetPolys(vtk_faces)
                    poly_result = vtkTrianglePoly(poly_result)
                    points, faces = vtkPoly_to_MeshData(poly_result)

                    road_poly = RoadPolygon(points, faces, None, "road")
                    road_poly_set.append_data(road_poly, True)

        # mgeo = MGeo(node_set=nodeset, link_set=linkset, lane_boundary_set=lanemarkingset, lane_node_set=lanenodeset, road_polygon_set=road_poly_set, sign_set=sign_set, light_set=light_set, intersection_controller_set=mgeo_controller_set)
        mgeo = MGeo(node_set=nodeset, link_set=linkset, lane_boundary_set=laneboundaryset, lane_node_set=lanenodeset, road_polygon_set=road_poly_set, scw_set=scw_set, cw_set=cw_set)

        # mgeo.global_coordinate_system
        porj4_lat_0 = ' +lat_0={}'.format(0)
        porj4_lon_0 = ' +lon_0={}'.format((self.zone - 0.5) * 6 - 180)
        porj4_k = ' +k={}'.format(0.9996)
        porj4_x_0 = ' +x_0={}'.format(500000)
        porj4_y_0 = ' +y_0={}'.format(0)
        proj4_datum = ' +ellps={}'.format('WGS84')

        mgeo.global_coordinate_system = '+proj=tmerc'  + porj4_lat_0 + porj4_lon_0 + porj4_k + porj4_x_0 + porj4_y_0 + proj4_datum + ' +units=m +no_defs'

        return mgeo
