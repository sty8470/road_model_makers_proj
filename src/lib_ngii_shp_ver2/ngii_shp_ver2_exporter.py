import os
import sys
import csv
import numpy as np
import shapefile
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')
sys.path.append(current_path + '/../lib_ngii_shp_ver2/')
from shp_common import *
import math
# import ngii_shp2_to_mgeo
import lib.common.polygon_util as util

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj
from lib.mgeo.class_defs import *

from lib.stryx.stryx_load_geojson_lane import *
from lib.stryx.stryx_geojson import *

def load_file():
    input_path = '../../../rsc/map_data/ngii_shp_ver2_Seoul_Sangam/SEC01_UTM52N_ElipsoidHeight'
    output_path = '../../../rsc/map_data/ngii_shp_ver2_Seoul_Sangam/output'
    relative_loc = True

    # 절대 경로로 변경
    # input_path = os.path.normcase(input_path)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)   

    # 절대 경로로 변경
    # output_path = os.path.normcase(output_path)
    output_path = os.path.join(current_path, output_path)
    output_path = os.path.normpath(output_path)
  
    print('[INFO] input  path:', input_path)
    print('[INFO] output path:', output_path)

    map_info = read_shp_files(input_path, True)
    
    return map_info, input_path, output_path, relative_loc

def export_lane():
    map_info, input_path, output_path, relative_loc = load_file()

    map_info = map_info[0]

    # 입력용 파일
    sf = map_info['B2_SURFACELINEMARK']
    a2_path_list = map_info['A2_LINK']
    
    c3_roadedge = map_info['C3_VEHICLEPROTECTIONSAFETY']

    shapes = sf.shapes()
    # sf.encoding = 'utf-16'
    records  = sf.records()
    fields = sf.fields

    # Find origin, using A1_NODE

    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)

    file_key_num_pair = dict()

    output_file_name_prefix = ''
    output_file_name_suffix = '.csv'
    output_file_name_list = dict()
    type_name_list = list()

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # 선의 타입 정보를 key로 변경
        role_code = dbf_rec['Kind']
        
        kind_str = surfline_kind_code_to_str(role_code)

        if kind_str == 'Lane_Border' or kind_str == 'Lane_Center':
            # Border 이거나 CenterLine 이면 하나의 파일로 한다
            type_name = 'Lane_Center'
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name

        else:
            type_name = kind_str
            if not (type_name in type_name_list):
                type_name_list.append(type_name)
                output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
                output_file_name_list[type_name] = output_file_name
             
     # A2_LINK에서 나오는 파일들: 하나의 파일로 다 모은다
    type_name = 'DrivePath'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    # B3_SURFACEMARK 에서 Kind가 5321인 데이터를 찾는다
    # 이 데이터가 횡단보도이다
    type_name = 'Crosswalk'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    # D3_SIDEWALK
    type_name = 'Sidewalk'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name

    type_name = 'RoadEdge'
    type_name_list.append(type_name)
    output_file_name = output_file_name_prefix + type_name + output_file_name_suffix
    output_file_name_list[type_name] = output_file_name


    for key in output_file_name_list.keys():
        output_file_name_list[key] = os.path.join(
            output_path, output_file_name_list[key])

    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        if os.path.exists(each_out):
            print('[WARNING] Removing an existing file... ({})'.format(each_out))
            os.remove(each_out)
        
        fileOpenMode = 'w'
        with open(each_out, fileOpenMode, newline='') as csvfile:
            continue
    for key in output_file_name_list.keys():
        each_out = output_file_name_list[key]
        print('[INFO] Created a new file: ({})'.format(each_out))

    # B2_SURFACELINEMARK에서 나오는 파일들
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
       
        role_code = dbf_rec['Kind']
       
        # Key에 따른 각 파일에 작성
        kind_str = surfline_kind_code_to_str(role_code)
        key = kind_str

        fileOpenMode = 'a'

        each_out = output_file_name_list[key] if key != 'Lane_Border' else output_file_name_list['Lane_Center']

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            coord_obj = shp_rec.points

            _write_single_line(writer, coord_obj, relative_loc, origin)
            
    key = 'DrivePath'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]

    a2_shapes = a2_path_list.shapes()
    a2_records  = a2_path_list.records()
    a2_fields = a2_path_list.fields

    for i in range(len(a2_shapes)):
        shp_rec = a2_shapes[i]
        dbf_rec = a2_records[i]

        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        
        role_code = dbf_rec['LinkType']

        with open(each_out, fileOpenMode, newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter = ',')

            coord_obj = shp_rec.points

            _write_single_line(writer, coord_obj, relative_loc, origin)

    key = 'RoadEdge'
    fileOpenMode = 'a'
    each_out = output_file_name_list[key]
    c3_shapes = c3_roadedge.shapes()
    c3_records= c3_roadedge.records()
    c3_fields = c3_roadedge.fields

    for i in range(len(c3_shapes)):
        shp_rec = c3_shapes[i]
        dbf_rec = c3_records[i]

        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
       
        # Kind 값을 검사
        # kind_value = each_obj['properties']['Type']
        kind_value = dbf_rec['Type']
        if kind_value == '4':
            with open(each_out, fileOpenMode, newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter = ',')
                try:
                    # coord_obj = line_points
                    coord_obj = shp_rec.points
                    _write_single_line(writer, coord_obj, relative_loc, origin)

                except:
                    print('[ERROR] geometry == null, # of line = {}'.format(each_obj['properties']['id']))


    print('END')

def export_cw():
    map_info, input_path, output_path, relative_loc = load_file()

    map_info = map_info[0]

    """
    Origin이 되는 Point를 찾는다
    """
    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)
    
    cw_set = CrossWalkSet()

    sf = map_info['B3_SURFACEMARK']
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    # cross walk
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        cw_id = dbf_rec['ID']
        cw_type = dbf_rec['Kind']

        cw = CrossWalk(points=shp_rec.points, idx=cw_id)
        cw.type_code_def = 'NGII_SHP2'
        cw.type = cw_type

        cw_set.append_data(cw)

    # speed bump
    sb = map_info['C4_SPEEDBUMP']
    shapes = sb.shapes()
    records  = sb.records()
    fields = sb.fields

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]
        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        cw_id = dbf_rec['ID']
        cw_type = '7'

        cw = CrossWalk(points=shp_rec.points, idx=cw_id)
        cw.type_code_def = 'NGII_SHP2'
        cw.type = cw_type

        cw_set.append_data(cw)


    """이제 cw_set에서 mesh를 만든다"""

    # 여기에, filename 을 idx로 접근하면, 다음의 데이터가 존재한다
    # 한가지 idx = speedbump를 예를 들면, 
    # 'vertex': 모든 speedbump를 구성하는 꼭지점의 리스트
    # 'faces': speedbump의 각 면을 구성하는 꼭지점 idx의 집합
    # 'cnt': 현재까지 등록된 speedbump 수
    vertex_face_sets = dict()

    """ Crosswalk 데이터에 대한 작업 """
    for idx, obj in cw_set.data.items():
        if obj.type == '5321':
            file_name = 'crosswalk_pedestrian'
        elif obj.type == '534':
            file_name = 'crosswalk_bike'
        elif obj.type == '533':
            file_name = 'crosswalk_plateau_pedestrian'
        # elif obj.type == '522':
        #     file_name = 'yield_sign'
        elif obj.type == '7':
            file_name = 'speedbump'
        elif obj.type == '97':
            file_name = 'parking_lot'
        elif obj.type == '98':
            file_name = 'speed_symbol'
        
        else:
            print('[WARNING] cw: {} skipped (currently not suppored type: {}'.format(idx, obj.type))
            continue

        # vertex, faces를 계산
        vertices, faces = obj.create_mesh_gen_points()

        # 해당 파일 이름으로 구성된 vertex_face_set에 추가한다
        # NOTE: 위쪽 일반 Surface Marking에 대한 작업도 동일
        if file_name in vertex_face_sets.keys():
            vertex_face = vertex_face_sets[file_name]

            exiting_num_vertices = len(vertex_face['vertex'])

            # 그 다음, face는 index 번호를 변경해주어야 한다
            faces = np.array(faces) # 상수를 쉽게 더하기 위해서 np array로 변경한다
            faces += exiting_num_vertices # vertex 리스트의 index가, 기존 vertex의 개수만큼 밀리게 되므로 이렇게 더해준다
            
            # 둘 다 리스트이므로, +로 붙여주면 된다.
            vertex_face['vertex'] += vertices # 그냥 리스트이므로 이렇게 붙여준다
            vertex_face['face'] += faces.tolist()
            vertex_face['cnt'] += 1

        else:
            vertex_face_sets[file_name] = {'vertex': vertices, 'face': faces, 'cnt':1}


    for file_name, vertex_face in vertex_face_sets.items():
        print('file: {}, num of lane objects: {}'.format(file_name, vertex_face['cnt']))
        file_name = os.path.normpath(os.path.join(output_path, file_name))  

        mesh_gen_vertices = vertex_face['vertex']
        mesh_gen_vertex_subsets_for_each_face = vertex_face['face']

        poly_obj = make_road(mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face)
        write_obj(poly_obj, file_name)


    print('END')


def export_ts():
    map_info, input_path, output_path, relative_loc = load_file()

    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'

    map_info = map_info[0]

    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)

    sf = map_info['B1_SAFETYSIGN']
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    nodeSet, junctionSet = __create_node_and_junction_set(map_info['A1_NODE'], origin)
    linkSet =__create_link_set(map_info['A2_LINK'], origin, nodeSet)
    to_csv_list = []

    traffic_set = util.__create_traffic_sign_set_from_shp(sf, origin, linkSet)
  
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        idx = dbf_rec['ID']
        point = [shp_rec.points[0][0], shp_rec.points[0][1], shp_rec.z[0]]
        point = np.array(point)
        point -= origin
       
        signal_type = dbf_rec['Type']

        result, file_path, file_name =\
            __get_traffic_sign_asset_path_and_name(traffic_set.signals[idx])

        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = os.path.join(asset_path_root, file_path)

        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        linkID = dbf_rec['LinkID']
        orientation_string = '0.0/0.0/0.0'
        orientation_string = '0.0/{:.6f}/0.0'.format(util.calculate_heading(traffic_set))
        
        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'traffic_sign_ALL.csv')

    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)

def export_tl():
    map_info, input_path, output_path, relative_loc = load_file()

    map_info = map_info[0]

    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Prefabs/'

    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)
    sf = map_info['C1_TRAFFICLIGHT']
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    nodeSet, junctionSet = __create_node_and_junction_set(map_info['A1_NODE'], origin)
    linkSet = __create_link_set(map_info['A2_LINK'], origin, nodeSet)
    to_csv_list = []

    traffic_set = util.__create_traffic_light_set_from_shp(sf, origin, linkSet)

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        idx = dbf_rec['ID']
        point = [shp_rec.points[0][0], shp_rec.points[0][1], shp_rec.z[0]]
        point = np.array(point)
        point -= origin
       
        signal_type = dbf_rec['Type']

        result, file_path, file_name =\
            get_traffic_light_asset_path_and_name(signal_type, idx)

        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue

        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path =  os.path.join(asset_path_root, file_path)

        # INFO #2
        pos = point
        pos = local_utm_to_sim_coord(pos) # 시뮬레이터 좌표계로 변환이 필요
        position_string = '{:.6f}/{:.6f}/{:.6f}'.format(pos[0], pos[1], pos[2])

        # INFO #3
        linkID = dbf_rec['LinkID']
        orientation_string = '0.0/0.0/0.0'
        orientation_string = '0.0/{:.6f}/0.0'.format(util.calculate_heading(traffic_set))
       
        # csv 파일 출력을 위한 리스트로 추가
        to_csv_list.append([file_path, file_name, position_string, orientation_string, idx])

    # 신호등 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'traffic_light_ALL.csv')

    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)



def export_sm():
    map_info, input_path, output_path, relative_loc = load_file()

    map_info = map_info[0]

    origin = get_first_shp_point(map_info['A1_NODE'])
    origin = np.array(origin)
    np.set_printoptions(suppress=True)
    print('[INFO] Origin =', origin)

    """ 우선 Node, Link를 로드해야 한다 (링크의 최고 속도 등 부가적인 정보를 찾기 위함) """
    node_set, junction_set = __create_node_and_junction_set(map_info['A1_NODE'], origin)
    link_set = __create_link_set( map_info['A2_LINK'], origin, node_set)
    
    """ [STEP #1] 표지판 정보 """ 
    # 표지판 정보가 포함된 시뮬레이터 프로젝트 내 Path
    asset_path_root = 'Assets/1_Module/Map/MapManagerModule/RoadObject/Models/'

    # csv 작성을 위한 리스트
    to_csv_list = []

    sf = map_info['B3_SURFACEMARK']
    shapes = sf.shapes()
    # sf.encoding = 'utf-16'
    records  = sf.records()
    fields = sf.fields

    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # Kind 값으로, 로드해야 할 모델명을 찾아준다
        result, file_path, file_name =\
            get_surface_marking_asset_path_and_name(dbf_rec['Kind'], inspect_model_exists=True)
        if not result:
            # 자동 생성으로 넣어야 할 표지판이 없는 경우 warning을 내부적으로 발생시킨다
            continue
        
        # 파일 경로는 시뮬레이터 프로젝트 내 경로로 변경해준다
        file_path = asset_path_root + file_path

        """ 좌표 정보 찾기 """
        # B3_SURFACEMARK는 Polygon이다
        # assert each_obj['geometry']['type'] == 'Point'

        # 좌표 정보
        shp_rec.points -= origin

        # simulator 좌표계로 변경
        # pos = local_utm_to_sim_coord(shp_rec.points)
        centeroid = util.calculate_centroid(shp_rec.points[0:-1])
        pos = local_utm_to_sim_coord(centeroid)

        """ csv로 기록 """
        # 현재 포맷
        # FolderPath, PrefabName, InitPos, InitRot
        # 예시) Assets/Resources/Vehicle,KiaNiro.prefab,10.0/0.0/0.0,0.0/90.0/0.0
        position_string = '{}/{}/{}'.format(pos[0], pos[1], pos[2])
        orientation_string = '0.0/0.0/0.0'
        to_csv_list.append([file_path, file_name, position_string, orientation_string, dbf_rec['ID']])
    
    # 표지판 정보를 csv로 출력
    output_file_name = os.path.join(output_path, 'surface_marking_info.csv')
    with open(output_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(to_csv_list)



def _is_single_line_obj(coord_obj):
    """
    [NOTE] Point가 실제 어디서 나오는지 확인해야 한다.
    ----------
    Case #1 >> Type = 121과 같은 경우, 겹선으로 예상되는데,
    이 때는 실제 라인이 2개이므로, coord_obj가 실제로는 선의 list 이고, 
    coord_obj[0], coord_obj[1]이 각 선을 이루는 point의 집합이 되는 구조이다. 
    즉, line0 = coord_obj[0]라고 둔다면,
    coord_obj[0][0] 가 point0가 되고, len(coord_obj[0][0])이 3이 되고, type(coord_obj[0][0][0])이 float이다.
    ----------
    Case #2 >> 그 밖의 Case에서는, 
    coord_obj가 실제 point의 집합이 된다
    즉, line0 = coord_obj이다. (위에서는 coord_obj[0]이었음!)
    coord_obj[0] 가 point0가 되고, len(coord_obj[0])이 3이 되고, type(coord_obj[0][0])이 float이다.
    ----------
    결론 >> coord_obj[0][0] 의 type이 list인지, float인지 확인하면 된다.
    """

    if type(coord_obj[0][0]) is float:
        # Case #2 같은 경우임 (일반적인 경우)
        # 즉, coord_obj 1가 유일한 선이고,
        # coord_obj[0]    이 첫번째 point이고,
        # coord_obj[0][0] 이 첫번째 point의 x좌표인것
        point0 = coord_obj[0]
        if len(point0) != 3:
            raise BaseException('[ERROR] @ len(point0) != 3')
        return True

    elif type(coord_obj[0][0]) is list:
        # Case #1 같은 경우임
        # 즉, coord_obj[0], coord_obj[1] 각각이 선이다
        # coord_obj[0]       이 첫번째 line이고,
        # coord_obj[0][0]    이 첫번째 line의 첫번째 point이고
        # coord_obj[0][0][0] 이 첫번째 line의 첫번째 point의 x좌표인 것
        point0 = coord_obj[0][0]
        if len(point0) != 3:
            raise BaseException('[ERROR] @ len(point0) != 3')

        return False
    else:
        raise BaseException('[ERROR] Unexpected type for coord_obj[0][0] = {}'.format(type(coord_obj[0][0])))


def _write_single_line(csvwriter, line, relative_loc, origin=None):
    line = calculate_evenly_spaced_link_points(line, 1)
    for point in line:
        if relative_loc:
            point_rel = list()
            for i in range(len(point)):
                point_rel.append(point[i] - origin[i])
            csvwriter.writerow(point_rel)
            continue
        else:
            csvwriter.writerow(point)

def surfline_kind_code_to_str(num):
    if num == '501':
        return 'Lane_Center'
    elif num == '502':
        return 'Lane_Uturn'
    elif num == '503':
        return 'Lane_Normal'
    elif num == '504': # 버스전용차선인데 일반차선으로 분류
        return 'Lane_Normal'
    elif num == '505':
        return 'Lane_Border'
    elif num == '506':
        return 'Lane_Normal'
    elif num == '515':
        return 'Lane_NoParking'
    elif num == '525':
        return 'Lane_Guide'
    elif num == '530':
        return 'Lane_StopLine'
    elif num == '531':
        return 'Lane_SafeArea'
    elif num == '535':
        return 'Lane_Undef'
    elif num == '599':
        return 'Lane_Undef'
    else:
        raise BaseException('[ERROR] Undefined kind value')
    
def calculate_evenly_spaced_link_points(points, step_len):
    if len(points) == 0:
        return points
    total_dist = 0
    new_step_len = step_len
    for i in range(len(points) - 1):
        point_now  = points[i]
        point_next  = points[i+1]
        dist_point = np.array(point_next) - np.array(point_now)
        dist = math.sqrt(pow(dist_point[0], 2) + pow(dist_point[1], 2) + pow(dist_point[2], 2))
        total_dist += dist
        if 0 < total_dist//step_len < step_len/2:
            new_step_len = total_dist/(total_dist//step_len)
        else:
            new_step_len = total_dist/(total_dist//step_len+1)
    new_points_all = points[0]
    # print(step_len, new_step_len, total_dist)

    skip_getting_new_point = False
    for i in range(len(points) - 1):
        # 시작점을 어디로 할 것인가를 결정
        # 만일 지난번 point에서 예를 들어
        # x = 0, 3, 6, 9 까지 만들고, 
        # 원래는 x = 10까지 와야하는 상황이었다.
        # 실제로 포인트는 x = 9에만 찍혀있다.
        # 따라서 여기부터 시작하는 것이 옳다.
        if not skip_getting_new_point:
            point_now  = points[i]


        point_next = points[i + 1]

        # 2. point_now에서 point_next까지 point를 생성한다
        # 2.1) 1 step 에 해당하는 벡터 
        dir_vector = np.array(point_next) - np.array(point_now)
        mag = np.linalg.norm(dir_vector, ord=2)
        unit_vect = dir_vector / mag
        step_vect = new_step_len * unit_vect
            
        # 2.2) 벡터를 몇 번 전진할 것인가
        cnt = (int)(np.floor(mag / new_step_len))
        if cnt == 0:
            # 마지막보다 이전이면, 즉 현재포인트와 다음 포인트가 너무 가깝다
            if i < len(points) - 2:
                #만일 이렇게 되면, 다음 포인트를 그냥 여기 포인트로 하는게 낫다
                # 현재 point_now를 그 다음 point_now로 그대로 사용한다
                skip_getting_new_point = True
                continue
            else:
                # 마지막인데, 진짜 마지막 포인트가 너무 짧은 거리에 있다
                # 그냥 붙여주고 끝낸다
                new_points_all = np.vstack((new_points_all, point_next))
                break
                

        # 2.3) 현재 위치는 포함하지 않고, 새로운 포인트를 cnt 수 만큼 생성, 전체 포인트에 연결
        new_points = _create_points_using_step(point_now, step_vect, cnt)
        new_points_all = np.vstack((new_points_all, new_points))

        # 2.4) 원래 있는 point 사이의 길이가 mag로 나눠서 딱 떨어지면
        #      마지막 포인트가 포함되었다. 이에 따라 처리가 달라짐
        if mag % new_step_len == 0:
            # 이렇게되면, 끝 점이 자동으로 포함될 것이다 
            pass
        else:
            #만일 이렇게 되면, 다음 포인트를 그냥 여기 포인트로 하는게 낫다
            skip_getting_new_point = True
            point_now = new_points_all[-1]

            # 2.5) 마지막인 경우, 진짜 마지막 포인트를 강제로 넣는다
            if i == len(points) - 2:
                new_points_all = np.vstack((new_points_all, point_next))

    return new_points_all

def _create_points_using_step(current_pos, xyz_step_size, step_num):
    next_pos = current_pos

    if step_num == 0:
        # raise Exception('[ERROR] Cannot connect the two points, check your unit\
        #     vector step length')
        ret = np.array(next_pos)

    else:
        for i in range(step_num):
                
            next_pos = [next_pos[0] + xyz_step_size[0],
                next_pos[1] + xyz_step_size[1],
                next_pos[2] + xyz_step_size[2]]
            if i == 0:
                ret = np.array(next_pos)
            else:
                ret = np.vstack((ret, next_pos))

    return ret

def get_traffic_light_asset_path_and_name(prop_type, idx):

    if prop_type == '1': # 삼색등
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_R_Y_SG.prefab'

    elif prop_type == '2': # 사색등A	2
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Hor_R_Y_LG_SG.prefab'

    elif prop_type == '11':
        # 보행자 신호등 (NGII)
        file_path = '01_MapCommon_PS'
        file_name = 'PS_RG.prefab'
        
    else:
        file_path = '01_MapCommon_TL'
        file_name = 'TL_Misc_NGII_Shp2_{}.prefab'.format(prop_type)
        print('[ERROR] @ __get_traffic_light_asset_path_and_name: unexpected prop_type! (you passed = {} (tl id = {}))'.format(prop_type, idx))

    return True, file_path, file_name

def __get_traffic_sign_asset_path_and_name(ts):
    """NGII Shp Ver2 포맷으로 제공된 표지판 정보를 담고있는 MGeo Signal 인스턴스에서 시뮬레이터 배치용 csv 파일을 생성하는 메소드"""
    prop_type = ts.type
    prop_sub_type = ts.sub_type
    prop_value = ts.value

    # UPDATE(sglee): 지원 안 되는 prop_sub_type 지속적으로 업데이트
    if prop_sub_type in ['199', '299', '399', '499', '225']:
        # 225: 최저 속도 제한 >> 최저 속도 값을 link에서 받아와야 모델을 특정할 수 있는데, link에 최저 속도 값이 없음 

        print('[WARNING] @ __get_traffic_sign_asset_path_and_name: no supported model for this prop_sub_type = {} (ts id = {})'.format(prop_sub_type, ts.idx))
        return False, '', ''

    # NOTE: 현재 prop_type 2와 3이 반대로 되어있는 것 같음
    # if prop_type == '2':
    #     prop_type = '3'
    # elif prop_type == '3':
    #     prop_type = '2' 


    if prop_type == '1':
        file_path = '01_MapCommon_Signs/01_Caution_Beam'
        file_name = '01_Caution_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '2':
        file_path = '01_MapCommon_Signs/02_Restriction_Beam'
        
        if prop_sub_type == '224':
            if (prop_value is None) or (prop_value is '') or (prop_value is 0):
                raise BaseException('[WARNING] @ __get_traffic_sign_asset_path_and_name: value is not set for traffic sign object with sub_type = {} (ts id = {})'.format(prop_sub_type, ts.idx))
            # prop_subtype을 변경해준다
            prop_sub_type = '{}_{}kph'.format(prop_sub_type, prop_value)
        
        file_name = '02_Restriction_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '3':
        file_path = '01_MapCommon_Signs/03_Indication_Beam'
        file_name = '03_Indication_{}_Beam.prefab'.format(prop_sub_type)


    elif prop_type == '4':
        file_path = '01_MapCommon_Signs/04_Aux_Beam'
        file_name = '04_Aux_{}_Beam.prefab'.format(prop_sub_type)

    else:
        raise BaseException('[ERROR] @ __get_traffic_sign_asset_path_and_name: unexpected prop_type! (you passed = {}) (ts id = {})'.format(prop_type, ts.idx))

    return True, file_path, file_name

def local_utm_to_sim_coord(local_utm):
    # Local UTM  X, Y, Z = East, North, Up
    # Simulation X, Y, Z = West, Up, South
    
    sim_x = -1 * local_utm[0]
    sim_y = local_utm[2]
    sim_z = -1 * local_utm[1]

    return np.array([sim_x, sim_y, sim_z])

def __create_node_and_junction_set(sf, origin):
    node_set = NodeSet()
    junction_set = JunctionSet()
    
    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields
    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')
    
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        shp_rec.points -= origin

        # node로 추가
        node = Node(dbf_rec['ID'])
        node.point = shp_rec.points[0]
        node.node_type = dbf_rec['NodeType']
        its_id = dbf_rec['ITSNodeID']

        # junction 존재 여부 판단 및 추가
        if its_id is not '':
            if its_id in junction_set.junctions.keys():
                # junction exists in set
                junction_set.junctions[its_id].add_jc_node(node)
            else:
                # junction is completely new
                junction = Junction(its_id)
                junction.add_jc_node(node)

                junction_set.append_junction(junction)

        # node를 node_set에 포함
        node_set.nodes[node.idx] = node

    return node_set, junction_set


def __create_link_set(sf, origin, node_set):
    line_set = LineSet()

    shapes = sf.shapes()
    records  = sf.records()
    fields = sf.fields

    if len(shapes) != len(records):
        raise BaseException('[ERROR] len(shapes) != len(records)')


    # [파일 내부 오류로 인한 체크]
    # dbf 파일 내부 L_LinkID 또는 R_LinkID에 오타가 있는 경우가 있다
    # 때문에 L_LinkID, R_LinkID라고 생각되는 필드 이름을 검색해서 찾아준다
    global key_L_LINKID, key_R_LINKID
    
    for i in range(len(sf.fields)):
        each_field_def = sf.fields[i]
        field_name = each_field_def[0]
        if field_name in ['L_LinkID', 'L_LinKID']: # 필드 이름이 이 리스트에 있는 것 중 하나면 적합한 필드라고 간주한다
            key_L_LINKID = field_name
            break

        if i == len(sf.fields):
            # field_name 이 생각한 옵션에 걸렸으면, 이 부분이 실행이 안 된다
            # 이 부분이 실행이 된다는 것은 결국 Left Link ID로 생각되는 필드가 없다는 것
            raise BaseException('Cannot find dbf key for Left Link ID')
    
    for i in range(len(sf.fields)):
        each_field_def = sf.fields[i]
        field_name = each_field_def[0]
        if field_name in ['R_LinkID', 'R_LinKID']: # 필드 이름이 이 리스트에 있는 것 중 하나면 적합한 필드라고 간주한다
            key_R_LINKID = field_name
            break
        
        if i == len(sf.fields):
            # field_name 이 생각한 옵션에 걸렸으면, 이 부분이 실행이 안 된다
            # 이 부분이 실행이 된다는 것은 결국 Left Link ID로 생각되는 필드가 없다는 것
            raise BaseException('Cannot find dbf key for Right Link ID')
        
    # 우선 링크셋을 만든다
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        # Convert to numpy array
        shp_rec.points = np.array(shp_rec.points)
        shp_rec.z = np.array(shp_rec.z)

        # Point에 z축 값도 그냥 붙여버리자
        shp_rec.points = np.c_[shp_rec.points, shp_rec.z]

        # origin 무조건 전달, 상대좌표로 변경
        # shp_rec.points -= origin

        line_points = list()
        for k in range(len(shp_rec.points)):
            e = shp_rec.points[k][0] - origin[0]
            n = shp_rec.points[k][1] - origin[1]
            z = shp_rec.z[k] - origin[2]

            line_points.append([e,n,z])

        shp_rec.points = np.array(line_points)


        # 현재는 전부 바로 point가 init되는 Link를 생성
        link_id = dbf_rec['ID']
        link = Link(points=shp_rec.points, idx=link_id, lazy_point_init=False)
    
        if dbf_rec['FromNodeID'] not in node_set.nodes.keys():           
            # FromNodeID에 해당하는 노드가 없는 경우이다.
            # 새로운 노드를 생성해서 해결
            idx = dbf_rec['FromNodeID']
            print('[WARN] FromNode (id={}) does not exist. (for Link id={}) Thus one is automatically created.'.format(idx, link_id))            
            node = Node(idx)
            node.point = shp_rec.points[0] 
            node_set.append_node(node)
            from_node = node
        else:
            from_node = node_set.nodes[dbf_rec['FromNodeID']]

        if dbf_rec['ToNodeID'] not in node_set.nodes.keys():
            # ToNodeID에 해당하는 노드가 없는 경우이다.
            # 새로운 노드를 생성해서 해결
            idx = dbf_rec['ToNodeID']
            print('[WARN] ToNode (id={}) does not exist. (for Link id={})  Thus one is automatically created.'.format(idx, link_id))            
            node = Node(idx)
            node.point = shp_rec.points[0] 
            node_set.append_node(node)
            to_node = node
        else:
            to_node = node_set.nodes[dbf_rec['ToNodeID']]

        link.set_from_node(from_node)
        link.set_to_node(to_node)
        
        # 차선 변경 여부를 결정하는데 사용한다
        # 1: 교차로내 주행경로, 2 & 3: 톨게이트차로(하이패스, 비하이패스)
        link.link_type = dbf_rec['LinkType']

        # Max Speed 추가
        link.set_max_speed_kph(dbf_rec['MaxSpeed'])

        # link_set에 추가
        line_set.lines[link.idx] = link


    # 차선 변경을 위해, 좌/우에 존재하는 링크에 대한 Reference를 추가한다
    # 단, 좌/우에 존재하는 링크라고해서 반드시 차선 변경이 가능한 것은 아니다
    for i in range(len(shapes)):
        shp_rec = shapes[i]
        dbf_rec = records[i]

        link = line_set.lines[dbf_rec['ID']]

        # 양옆 차선 속성도 dbf 데이터로부터 획득
        if dbf_rec[key_R_LINKID] is not '': # NOTE: 일부 파일에는 소문자 k에 오타가 있어 R_LinKID로 조회해야할 수 있다. 
            lane_ch_link_right = line_set.lines[dbf_rec[key_R_LINKID]] # NOTE: 일부 파일에는 소문자 k에 오타가 있어 R_LinKID로 조회해야할 수 있다. 
            link.lane_ch_link_right = lane_ch_link_right

        if dbf_rec[key_L_LINKID] is not '': # NOTE: 일부 파일에는 소문자 k에 오타가 있어 L_LinKID로 조회해야할 수 있다. 
            lane_ch_link_left = line_set.lines[dbf_rec[key_L_LINKID]] # NOTE: 일부 파일에는 소문자 k에 오타가 있어 L_LinKID로 조회해야할 수 있다. 
            link.lane_ch_link_left = lane_ch_link_left

    return line_set 



if __name__ == u'__main__':
    export_lane()
    # export_ts()
    # export_tl()
    # export_cw()
    # export_sm()