import numpy as np


'''
두 벡터의 거리를 반환합니다.
'''
def get_vec_length(v1, v2) :
    dir_vir = v1 - v2
    return np.linalg.norm(np.array(dir_vir))

'''
단위 벡터를 반환합니다.
'''
def get_unit_vector(vec) :
    return vec / np.linalg.norm(vec, ord=2)

def is_up_face(l_list, r_list) :
    ret_value = False
    u_cnt = 0
    d_cnt = 0
    for i in range( len(l_list) - 1) :
        v1 = r_list[i + 0] - l_list[i + 0]
        v2 = l_list[i + 1] - r_list[i + 0]
        v1 = v1 / np.linalg.norm(v1, ord=2)
        v2 = v2 / np.linalg.norm(v2, ord=2)
        lr_axis = np.cross(v1, v2)
        if lr_axis[2] >= 0 :
            d_cnt += 1
        else :
            u_cnt += 1
    
    if d_cnt > u_cnt :
        ret_value = True

    return ret_value

'''
2차원 평면 폴리곤 안에 점이 존재하는지 검사하는 함수.
'''
def is_point_in_polygon(point, vertice_list) :
    ret_value = False
    cross_cnt = 0 # 교차 횟수.
    vertice_cnt = len(vertice_list)

    for i in range(vertice_cnt) :
        j = (i + 1 ) % vertice_cnt
        # 점(point)이 선분(vertice_list[i], vertice_list[j]) 의 y좌표 사이에 있음.
        if (vertice_list[i][1] > point[1]) != (vertice_list[j][1] > point[1]) :
            # at_x는 점을 지나는 수평선과 선문(vertice_list[i], vertice_list[j])의 교점
            at_x = ( ( (vertice_list[j][0] - vertice_list[i][0]) / (vertice_list[j][1] - vertice_list[i][1]) ) * (point[1] - vertice_list[i][1]) ) + vertice_list[i][0]
            # at_x가 오른쪽 반직선과의 교접이 맞으면 교점의 개수를 증가시킨다.
            if point[0] < at_x :
                cross_cnt += 1

        # 홀수면 내부, 짝수면 외부에 있음.
        if 0 == (cross_cnt % 2) :
            ret_value = False
        else :
            ret_value = True

    return ret_value


'''
    way 에 속한 node list에 node를 개수만큼 중간에 추가한다.
    (지금은 0번째 값 그대로 복사해서 넣어주고 있다.)
    '''
def add_way_poinst(way_list, add_count) :
    # 일단 0, 1 point 사이에 같은 간격으로 정점을 추가한다.
    first_point = way_list[0]
    second_point = way_list[1]
    v_len = get_vec_length(second_point, first_point)
    v_unit = get_unit_vector(second_point - first_point)
    step_len = v_len / (add_count + 1)
    
    for i in range(add_count) :
        add_point = first_point + (v_unit * (step_len * (1 + i)) )
        way_list.insert(1 + i, add_point)

def make_vertex_face_uv(left_points, right_points) :

    left_point_count = len(left_points)
    right_point_count = len(right_points)

    dif_count = left_point_count - right_point_count
    if dif_count > 0 :
        # 왼쪽라인 점이 많다. 오른쪽 라인에 점 추가.
        add_way_poinst(right_points, dif_count)
    elif dif_count < 0 :
        # 오른쪽라인 점이 많다. 왼쪽 라인에 점 추가.
        dif_count *= -1
        add_way_poinst(left_points, dif_count)
    else :
        # 같으면 추가 작업 없음.
        pass

    # left, right way 의 점들의 방향이 반대일 수 있다.
    foward_v = left_points[0] - right_points[0]
    reverse_v = left_points[0] - right_points[len(right_points) - 1]

    is_foward = True
    is_reverse_face = False

    foward_mag = np.linalg.norm(np.array(foward_v))
    reverse_mag = np.linalg.norm(np.array(reverse_v))
    if reverse_mag < foward_mag :
        # 반대방향이다.
        is_foward = False
    
    # 뒤집어진 face 찾기.
    left_point_list = list(left_points)
    right_point_list = None
    if is_foward : 
        right_point_list = list(right_points)
    else : 
        right_point_list = list(reversed(right_points))
    # 뒤집혔는가?
    is_reverse_face = is_up_face(left_point_list, right_point_list)

    mesh_gen_vertices = list()
    mesh_gen_vertex_subsets_for_each_face = list()

    face_cnt = 0
    for i in range(len(left_points)):
        v_l = left_point_list[i].tolist()
        v_r = right_point_list[i].tolist()

        new_v_l = None
        new_v_r = None
        if is_reverse_face == False :
            new_v_r = [float(v_l[0]), float(v_l[1]), float(v_l[2])]
            new_v_l = [float(v_r[0]), float(v_r[1]), float(v_r[2])]
        else :
            new_v_l = [float(v_l[0]), float(v_l[1]), float(v_l[2])]
            new_v_r = [float(v_r[0]), float(v_r[1]), float(v_r[2])]

        mesh_gen_vertices.append(new_v_l) 
        mesh_gen_vertices.append(new_v_r)

        if face_cnt > 0 :
            start_id = (face_cnt - 1) * 2
            face = [start_id + 0, start_id + 1, start_id + 3, start_id + 2]
            mesh_gen_vertex_subsets_for_each_face.append(face)

        face_cnt += 1

    return mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face, None

def make_intersection_polydata(boundary_points, triangles) :

    mesh_gen_vertices = list()
    mesh_gen_vertex_subsets_for_each_face = list()

    for t_iter in triangles.vertices :
        # triangle index
        i_1 = t_iter[0]
        i_2 = t_iter[1]
        i_3 = t_iter[2]

        face = [i_1, i_2, i_3]
        mesh_gen_vertex_subsets_for_each_face.append(face)

        # p_1 = boundary_points[i_1]
        # p_2 = boundary_points[i_2]
        # p_3 = boundary_points[i_3]

        # p_1_list = p_1.tolist()
        # p_2_list = p_2.tolist()
        # p_3_list = p_3.tolist()

        # p_1_list.append(0)
        # p_2_list.append(0)
        # p_3_list.append(0)

        # mesh_gen_vertices.append(p_1_list)
        # mesh_gen_vertices.append(p_2_list)
        # mesh_gen_vertices.append(p_3_list)

    for v_iter in triangles.points:
        p_list = v_iter.tolist()
        p_list.append(0)
        mesh_gen_vertices.append(p_list)

        

    return mesh_gen_vertices, mesh_gen_vertex_subsets_for_each_face, None

