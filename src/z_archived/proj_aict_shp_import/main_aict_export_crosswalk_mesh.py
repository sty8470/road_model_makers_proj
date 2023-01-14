"""
융기원에서 제공한 판교 맵에 대한 데이터(shape 포맷으로 되어있음)를
읽고 crosswalk mesh를 생성한다
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import lib.common.shp_common as shp_common
import lib.common.shp_csv_export as shp_csv_export
import lib_ngii_shp1.morai_sim_build_data_exporter as ngii_shp1_exporter
import lib_ngii_shp1.ngii_shp1_to_mgeo as ngii_shp1_to_mgeo

from lib.mgeo.mesh_gen.generate_mesh import make_road, write_obj

import shapefile
import csv
import numpy as np


def main():
    input_path = '../../rsc/map_data/aict_shp_pangyo/1st2ndIntg_TM_Mid'
    output_path = '../../output/aict_shp_pangyo/'

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

    """데이터 읽기"""
    cw_set, sm_set = ngii_shp1_to_mgeo.import_crowsswalk_and_surface_marking_data(input_path)

    """포인트 내부를 수정"""
    point_interval = 0.1
    for obj in sm_set.data.values():
        obj.fill_in_points_evenly(step_len=point_interval)

    for obj in cw_set.data.values():
        obj.fill_in_points_evenly(step_len=point_interval)

    """visualize 해서 확인하기"""
    __draw_plot(cw_set, sm_set)


    """이제 cw_set, sm_set에서 mesh를 만든다"""

    # 여기에, filename 을 idx로 접근하면, 다음의 데이터가 존재한다
    # 한가지 idx = speedbump를 예를 들면, 
    # 'vertex': 모든 speedbump를 구성하는 꼭지점의 리스트
    # 'faces': speedbump의 각 면을 구성하는 꼭지점 idx의 집합
    # 'cnt': 현재까지 등록된 speedbump 수
    vertex_face_sets = dict()

    """ 일반 Surface Marking 데이터에 대한 작업 """
    for idx, obj in sm_set.data.items():
        if obj.type == 7:
            file_name = 'speedbump'
        else:
            # 우선 과속방지턱이 아닌 대상은 우선 mesh 생성에서 제외한다.
            print('[WARNING] sm: {} skipped (currently not suppored type'.format(idx))
            continue
    
        # vertex, faces를 계산
        vertices, faces = obj.create_mesh_gen_points()

        # 해당 파일 이름으로 구성된 vertex_face_set에 추가한다
        # NOTE: 아래쪽 Crosswalk에 대한 작업도 동일
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


    """ Crosswalk 데이터에 대한 작업 (과정 흐름은 바로 위 Surface Marking에 대한 작업과 동일) """
    for idx, obj in cw_set.data.items():
        if obj.type == 4:
            file_name = 'crosswalk_pedestrian'
        elif obj.type == 6:
            file_name = 'crosswalk_bike'
        else:
            # 우선 과속방지턱이 아닌 대상은 우선 mesh 생성에서 제외한다.
            print('[WARNING] cw: {} skipped (currently not suppored type'.format(idx))
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

def __draw_plot(cw_set, sm_set):
    for obj in cw_set.data.values():
        if obj.type == 4:
            obj.vis_mode_line_color = 'b'
        elif obj.type == 6:
            obj.vis_mode_line_color = 'k'
        else:
            raise BaseException('Unexpected cw.type = {}'.format(obj.type))

        # TODO(sglee): 이 부분 개선하기:
        # 현재는 line width, line_color 모두 not None으로 설정되어 있어야
        # 해당 style로 그려준다. 향후 둘 중 하나라도 not None이면, 해당 style을 적용하도록 변경한다
        obj.vis_mode_line_width = 1 

    for obj in sm_set.data.values():
        if obj.type == 1:
            obj.vis_mode_line_color = 'r'    
        elif obj.type == 7:
            obj.vis_mode_line_color = 'g'
        else:
            raise BaseException('Unexpected sm.type = {}'.format(obj.type))

        # TODO(sglee): 이 부분 개선하기:
        # 현재는 line width, line_color 모두 not None으로 설정되어 있어야
        # 해당 style로 그려준다. 향후 둘 중 하나라도 not None이면, 해당 style을 적용하도록 변경한다
        obj.vis_mode_line_width = 1      

    # 그려본다
    import matplotlib.pyplot as plt
    plt.figure()

    # 전체 plot하기 
    cw_set.draw_plot(plt.gca())
    sm_set.draw_plot(plt.gca())    
    plt.show()


if __name__ == u'__main__':
    main()