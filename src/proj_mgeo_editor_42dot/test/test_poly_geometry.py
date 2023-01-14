
import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

import numpy as np
import matplotlib.pyplot as plt

from mgeo_odr_converter import MGeoToOdrDataConverter
from scipy.integrate import quad


def to_np_array(x, y):
    pt_array = list()

    for i in range(len(x)):
        pt = [x[i], y[i], 0]
        pt_array.append(pt)

    return np.array(pt_array)


def create_test_case_line_01(show=False):
    a = 5
    b = 1
    c = 0
    d = 0 

    def f1(x):
        y = d * x**3 + c * x**2 + b * x + a
        return y
    
    x = np.arange(0, 10, step=1)
    y = f1(x)

    if show:
        plt.figure()
        plt.plot(x,y)
        plt.show()
 
    return to_np_array(x, y)


def create_test_case_line_02(show=False):
    a = 0
    b = 1/2
    c = 0
    d = 0 

    def f1(x):
        y = d * x**3 + c * x**2 + b * x + a
        return y
    
    x = np.arange(0, 4, step=0.1)
    y = f1(x)

    if show:
        plt.figure()
        plt.plot(x,y)
        plt.show()
 
    return to_np_array(x, y)


def create_test_case_line_03(show=False):
    a = -2
    b = 1
    c = 0
    d = 0 

    def f1(x):
        y = d * x**3 + c * x**2 + b * x + a
        return y
    
    x = np.arange(4, 8, step=0.1)
    y = f1(x)

    if show:
        plt.figure()
        plt.plot(x,y)
        plt.show()
 
    return to_np_array(x, y)


def create_test_case_poly3_01(show=False):
    a = 20
    b = 0
    c = 0.0005
    d = 0.0001 

    def f1(x):
        y = d * x**3 + c * x**2 + b * x + a
        return y
    
    x = np.arange(-100, 100, step=1)
    y = f1(x)

    if show:
        plt.figure()
        plt.plot(x,y)
        plt.show()
 
    return to_np_array(x, y)


def create_test_case_poly3_02(show=False):
    a = 0
    b = 0
    c = 0.1
    d = 0

    def f1(x):
        y = d * x**3 + c * x**2 + b * x + a
        return y
    
    x = np.arange(0, 100, step=0.05)
    y = f1(x)

    if show:
        plt.figure()
        plt.plot(x,y)
        plt.show()
 
    return to_np_array(x, y)    


def create_test_case_poly3_03(show=False):
    a = 0
    b = 0
    c = 0.1
    d = 0

    def f1(x):
        y = d * x**3 + c * x**2 + b * x + a
        return y
    
    x = np.arange(0, 10, step=0.05)
    y = f1(x)

    xy = to_np_array(x, y)

    # rotate by 45deg
    converter = MGeoToOdrDataConverter.get_instance()
    xy = converter.coordinate_transform(45 * np.pi / 180, xy)

    # move origin to (10, 20)
    xy += np.array([10, 20])

    if show:
        plt.figure()
        plt.plot(xy[:,0], xy[:,1])
        plt.axis('equal')
        plt.show()
        
 
    return xy 


def create_test_case_poly3_circle_1(show=False):
    x = np.arange(10, 0, step=-0.1)
    y = np.sqrt(100 - x**2)

    xy = to_np_array(x, y)
    xy += np.array([10, 20, 0])
    
    if show:
        plt.figure()
        plt.plot(xy[:,0], xy[:,1])
        plt.axis('equal')
        plt.show()

    return xy 


def create_test_case_poly3_circle_2(show=False):
    x = np.arange(0, -10, step=-0.1)
    y = np.sqrt(100 - x**2)

    xy = to_np_array(x, y)
    xy += np.array([10, 20, 0])
    
    if show:
        plt.figure()
        plt.plot(xy[:,0], xy[:,1])
        plt.axis('equal')
        plt.show()

    return xy 


def create_test_case_poly3_circle_3(show=False):
    x = np.arange(-10, 0, step=0.1)
    y = -1* np.sqrt(100 - x**2)

    xy = to_np_array(x, y)
    xy += np.array([10, 20, 0])
    
    if show:
        plt.figure()
        plt.plot(xy[:,0], xy[:,1])
        plt.axis('equal')
        plt.show()

    return xy 


def create_test_case_poly3_circle_4(show=False):
    x = np.arange(0, 10, step=0.1)
    y = -1* np.sqrt(100 - x**2)

    xy = to_np_array(x, y)
    xy += np.array([10, 20, 0])
    
    if show:
        plt.figure()
        plt.plot(xy[:,0], xy[:,1])
        plt.axis('equal')
        plt.show()

    return xy 


def single_fit_test():
    
    """[USER OPTION] 아래 중에서 테스트 케이스 선택하여 주석 해제"""
    # 직선 케이스
    # data = create_test_case_line_01(show=False)

    # 곡선 케이스 (poly)
    # data = create_test_case_poly3_01(show=False) # fit 실패하는 케이스
    # data = create_test_case_poly3_02(show=False)
    # data = create_test_case_poly3_03(show=True)

    # 원형 트랙 케이스 (각각 1~4분면 중 하나를 반환)
    # data = create_test_case_poly3_circle_1(True)
    # data = create_test_case_poly3_circle_2(True)
    data = create_test_case_poly3_circle_3(True)
    # data = create_test_case_poly3_circle_4(True)

    converter = MGeoToOdrDataConverter.get_instance()

    init_coord, heading, arclength, poly_geo, uv_point =\
        converter.poly_geometry(data)

    u = uv_point[:,0]
    u_max = uv_point[-1][0]
    if u.max() != u_max:
        Logger.log_error('polyfit would not work for this lane section. u is not monotonically increasing.') 
        plt.figure()
        plt.plot(u)
        plt.show()

    a = poly_geo[0]
    b = poly_geo[1]
    c = poly_geo[2]
    d = poly_geo[3]
    def poly_fit_g(u):
        v = d * u**3 + c * u**2 + b * u + a
        return v

    v_fit = poly_fit_g(u)
    uv_fit = to_np_array(u, v_fit)
    xy_fit = converter.coordinate_transform(heading, uv_fit)
    xy_fit += init_coord

    unrotated_line = converter.coordinate_transform(heading, uv_point)


    plt.figure()

    # 원본 데이터
    plt.plot(data[:,0], data[:,1], 'r')

    # 추정한 데이터
    # plt.plot(uv_fit[:,0], uv_fit[:,1], 'b--')
    plt.plot(xy_fit[:,0], xy_fit[:,1], 'b--')

    plt.plot(uv_point[:,0], uv_point[:,1], 'g')
    # plt.plot(unrotated_line[:,0], unrotated_line[:,1], 'g')

    plt.axis('equal')
    plt.show()

    print('END')


def multiple_fit_test():
    
    """[USER OPTION] 아래 중에서 테스트 케이스 선택하여 주석 해제"""
    data_set = list()
    data1 = create_test_case_poly3_circle_1()
    data2 = create_test_case_poly3_circle_2()
    data3 = create_test_case_poly3_circle_3()
    data4 = create_test_case_poly3_circle_4()
    data_set.append(data1)
    data_set.append(data2)
    data_set.append(data3)
    data_set.append(data4)


    for data in data_set:
        converter = MGeoToOdrDataConverter.get_instance()

        init_coord, heading, arclength, poly_geo, uv_point =\
            converter.poly_geometry(data)

        u = uv_point[:,0]
        u_max = uv_point[-1][0]
        if u.max() != u_max:
            Logger.log_error('polyfit would not work for this lane section. u is not monotonically increasing.') 
            plt.figure()
            plt.plot(u)
            plt.show()

        a = poly_geo[0]
        b = poly_geo[1]
        c = poly_geo[2]
        d = poly_geo[3]

        def poly_fit_g(u):
            v = d * u**3 + c * u**2 + b * u + a
            return v

        v_fit = poly_fit_g(u)
        uv_fit = to_np_array(u, v_fit)
        xy_fit = converter.coordinate_transform(heading, uv_fit)
        xy_fit += init_coord
        
        unrotated_line = converter.coordinate_transform(heading, uv_point)

        plt.figure()

        # 원본 데이터
        plt.plot(data[:,0], data[:,1], 'r')

        # 추정한 데이터
        # plt.plot(uv_fit[:,0], uv_fit[:,1], 'b--')
        plt.plot(xy_fit[:,0], xy_fit[:,1], 'b--')

        plt.plot(uv_point[:,0], uv_point[:,1], 'g')
        # plt.plot(unrotated_line[:,0], unrotated_line[:,1], 'g')

        plt.axis('equal')
        plt.show()

        print('END')


def __create_geometry(data_set):
    ref_line_geometry = list()
    init_s = 0
    for data in data_set:
        converter = MGeoToOdrDataConverter.get_instance()

        # poly fit을 수행
        init_coord, heading, arclength, poly_geo, uv_point =\
            converter.poly_geometry(data)

        # 추가로 저장해야할 u_max 값 계산
        u = uv_point[:,0]
        u_max = uv_point[-1][0]
        if u.max() != u_max:
            Logger.log_error('polyfit would not work for this lane section. u is not monotonically increasing.') 
            plt.figure()
            plt.plot(u)
            plt.show()

        geo = {
            'data': data,
            's': init_s,
            'xy': init_coord,
            'hdg': heading,
            'model': 'poly3',
            'len': arclength,
            'params': poly_geo,
            'uv_point': uv_point,
            'u_max': u_max}

        ref_line_geometry.append(geo)
        init_s += arclength

        # a = geo['params'][0]
        # b = geo['params'][1]
        # c = geo['params'][2]
        # d = geo['params'][3]

        # def poly_fit_g(u):
        #     v = d * u**3 + c * u**2 + b * u + a
        #     return v

        # v_fit = poly_fit_g(geo['uv_point'][:,0])
        # uv_fit = to_np_array(geo['uv_point'][:,0], v_fit)
        # xy_fit = converter.coordinate_transform(geo['hdg'], uv_fit)
        # xy_fit += init_coord
        
        # unrotated_line = converter.coordinate_transform(geo['hdg'], uv_point)

        # plt.figure()

        # # 원본 데이터
        # plt.plot(data[:,0], data[:,1], 'r')

        # # 추정한 데이터
        # # plt.plot(uv_fit[:,0], uv_fit[:,1], 'b--')
        # plt.plot(xy_fit[:,0], xy_fit[:,1], 'b--')

        # plt.plot(uv_point[:,0], uv_point[:,1], 'g')
        # # plt.plot(unrotated_line[:,0], unrotated_line[:,1], 'g')

        # plt.axis('equal')
        # plt.show()

    return ref_line_geometry


def __create_geometry_set_circle(signal_case):
    data_set = list()
    data1 = create_test_case_poly3_circle_1()
    data2 = create_test_case_poly3_circle_2()
    data3 = create_test_case_poly3_circle_3()
    data4 = create_test_case_poly3_circle_4()
    data_set.append(data1)
    data_set.append(data2)
    data_set.append(data3)
    data_set.append(data4)


    if signal_case == 1:
        signal_pos = np.array([15, 15])
    else:
        signal_pos = np.array([20, 30])

    plt.figure()
    for data in data_set:
        plt.plot(data[:,0], data[:,1])
    plt.plot(signal_pos[0], signal_pos[1], 'D')
    plt.xlim(-10, 30)
    plt.ylim(0, 40)
    plt.show()
    
    ref_line_geometry = __create_geometry(data_set)
    
    return signal_pos, ref_line_geometry


def __create_goemetry_set_1st_order_case(signal_case):
    data_set = list()
    line1 = create_test_case_line_02()
    line2 = create_test_case_line_03()
    data_set.append(line1)
    data_set.append(line2)


    # y = -2x + 5 위를 지나는 점이도록 한다
    # 그러면 line1의 (2,1)에서 수직한 점이 나온다
    if signal_case == 1:
        signal_pos = np.array([0, 5])
    else:
        signal_pos = np.array([4, -3])


    plt.figure()
    for data in data_set:
        plt.plot(data[:,0], data[:,1])
    plt.plot(signal_pos[0], signal_pos[1], 'D')
    plt.xlim(-10, 30)
    plt.ylim(0, 40)
    plt.show()


    ref_line_geometry = __create_geometry(data_set)

    return signal_pos, ref_line_geometry


def signal_tranform(signal_pos, ref_line_geometry):
    converter = MGeoToOdrDataConverter.get_instance()

    candidate_points = list()
    min_dist = np.inf
    min_solution = None

    for geo_id, geo in enumerate(ref_line_geometry):

        # 현재 geometry의 uv 평면으로 signal을 이동시킨다
        # translation
        sig_uv = signal_pos - geo['xy'] 
        # rotation
        sig_uv = converter.coordinate_transform_point(-1 * geo['hdg'], sig_uv)


        # 이제 이 공간에서 가장 가까운 포인트를 찾는다
        sig_u = sig_uv[0]
        sig_v = sig_uv[1]
        a = geo['params'][0]
        b = geo['params'][1]
        c = geo['params'][2]
        d = geo['params'][3]

        
        """
        [Algorithm Summary]
        점 Q(u, du^3 + cu^2 + bu + a) >> referece line
        점 P(sig_u, sig_v)            >> signal
        두 점 QP 사이의 거리를 minimize 하는 점을 찾는다.

        거리의 minimize 문제이므로, 거리의 제곱을 minimize한다.
        즉 QP 사이의 거리의 제곱을 미분한 함수 = 0 이 되는 u를 우선 찾는다

        QP 사이의 거리의 제곱은 아래와 같고, 
        f  = np.poly1d([1, -sig_u]) ** 2 + np.poly1d([d, c, b, a - sig_v]) ** 2

        QP 사이의 거리의 제곱을 아래와 같이 미분한다
        f_dot = np.polyder(f)

        f_dot(u) = 0을 만족하는 값을 찾는다. 

        이를 만족하는 u가 여러개 나오므로, sqrt(f(u))로 거리를 계산하여,
        그 중에서 최소가 되는 f(u)를 선택하면 된다.

        단, fit된 곡선이 유한하지 않고 u = [0, u_max] 구간에서 정의되므로,
        해당 구간에 존재하지 않는 u는 버린다. 

        min QP 문제이기만 했다면 u의 boundary인 0, u_max 값에서도 거리를 계산해봐야하지만,
        현재는 수직인 지점만 찾는 문제이므로 boundary에서 체크할 필요가 없다.
        """
        curve = np.poly1d([d, c, b, a])
        curve_dot = np.polyder(curve)

        # QP 사이의 거리의 제곱을 나타내는 polynomial
        f = np.poly1d([1, -sig_u]) ** 2 + np.poly1d([d, c, b, a - sig_v]) ** 2

        # 위 polynomial을 미분하고, 0이 되는 해를 찾는다
        f_dot = np.polyder(f)
        all_roots = np.roots(f_dot)

        # 이 중에서 실수인 해만 찾는다
        # NOTE: complex part가 완전히 0일 때만 real root으로 고려할지, 
        #       complex part가 충분히 작으면 그냥 real root으로 고려할지 고민.
        # real_roots = all_roots[np.isreal(all_roots)] # imag value가 완전히 0일때만 real root으로 고려
        real_roots = all_roots[abs(all_roots.imag) < 1e-6] # imag value가 1e-6 미만이면 real root으로 고려

        # 여전히 위 값은 complex value이므로, real part만 남긴다
        real_roots = real_roots.real
        # print('real_roots: ', real_roots)


        # 찾은 해 중에서 적절한 u 범위에 존재하는 u에 대해서,
        # 거리를 계산하여 최소 거리를 만드는 u를 찾는다.
        # 그리고 해당 위치에서 실제 수직한지 체크하고 (double check)
        # t의 방향을 계산한다 (s에 대해 반시계 방향에 존재할 때 + 방향)
        for u in real_roots:
            
            # 현재 u를 정의하는 구간에 존재하는 point인지 확인해야 한다
            if u > 0 and u < geo['u_max']:

                # 이제 distance를 계산해본다
                distance = np.polyval(f, u) ** 0.5

                # curve에서 해당 위치
                v = np.polyval(curve, u)
                Q = np.array([u, v])

                if distance < min_dist:
                    # 아래 과정은 한번 더 검증을 거치는 차원에서 실행해본다
                    # 정말 수직으로 나오는가? 

                    # Q(u, du^3 + cu^2 + bu + a) 에서 P(sig_u, sig_v)로 향하는 벡터가 
                    # refrence line과 수직인지 검사한다
                    # curve위에서의 벡터를 s_vect
                    # curve위에서 P로 향하는 벡터를 qp_vect
                    
                    s_vect = np.array([1, np.polyval(curve_dot, u)])
                    s_vect = s_vect / np.linalg.norm(s_vect) # unit vector화

                    qp_vect = np.array([sig_u - u, sig_v - v])
                    qp_vect = qp_vect / np.linalg.norm(qp_vect) # unit vector화

                    dot_prod = np.inner(s_vect, qp_vect)
                    angle_deg = np.arccos(dot_prod) * 180 / np.pi
                    if abs(90 - angle_deg) < 1.0: # 90 deg에서 오차가 1deg 미만이면 충분히 수직하다고 판단한다
                        print('Found! (geo id = {}), (u = {})'.format(geo_id, u))

                    else:
                        # 이렇게 값이 나온다면 뭔가 이상한 것 >> 반드시 수직이어야 하는데??
                        print('[WARNING] Unexpected result from min_dist calculation. QP vector ')


                    # qp_vect 방향이 s-t 좌표계 정의에 대해 +인지 -인지 확인한다
                    cross_prod = np.cross(s_vect, qp_vect)
                    if cross_prod > 0: 
                        t = distance
                    elif cross_prod < 0:
                        t = -1 * distance
                    else:
                        t = 0

                    min_dist = distance
                    min_solution = {
                        'geo_id': geo_id,
                        'geo': geo,
                        'u': u,
                        'v': v,
                        't': t
                    }
                    # NOTE: t는 s_vect, qp_vect를 여기서 계산한 김에 계산을 했는데,
                    #       s는 min_solution을 완전히 찾은 다음 (이 루프가 종료된 다음) 계산하면 되어서, 밖에서 계산한다.


                    """그래프로 그려서 검증하기 (개별 케이스 검증)"""
                    # # fit된 곡선 그리기 위해서 계산
                    # def poly_fit_g(u_in):
                    #     v = d * u_in**3 + c * u_in**2 + b * u_in + a
                    #     return v
                    
                    # v_fit = poly_fit_g(geo['uv_point'][:,0])
                    # uv_fit = to_np_array(geo['uv_point'][:,0], v_fit)
                    # xy_fit = converter.coordinate_transform(geo['hdg'], uv_fit)
                    # xy_fit += geo['xy']

                    # point_Q = np.array([u, v])
                    # point_Q = converter.coordinate_transform_point(geo['hdg'], point_Q)
                    # point_Q += geo['xy']

                    # plt.figure()

                    # # xy 좌표
                    # # plt.plot(geo['data'][:,0], geo['data'][:,1], 'r') # 원본
                    # plt.plot(xy_fit[:,0], xy_fit[:,1], 'b--') # fit 결과 (uv좌표에서 fit -> xy로 변환)
                    # plt.plot(signal_pos[0], signal_pos[1], 'D', markersize=10) # signal 좌표
                    # plt.plot(point_Q[0], point_Q[1], 's', markersize=10) # 가장 가까운 점 좌표

                    # # uv 좌표에서 그리려면
                    # # plt.plot(geo['uv_point'][:,0], geo['uv_point'][:,1], 'g') #원본 좌표 변환 결과
                    # # plt.plot(uv_fit[:,0], uv_fit[:,1], 'b--') # fit 결과 (uv좌표에서)
                    # # plt.plot(sig_uv[0], sig_uv[1], 'D', markersize=10) #signal (uv 좌표에서)  
                    # # plt.plot(u, v, 's', markersize=10) #signal에서 가장 가까운 점

                    # plt.axis('equal')
                    # plt.show()
            else:
                print('Skip this root (u = {} not in proper range)'.format(u))


    if min_solution is None:
        # Logger.log_error('Failed to find s,t coordinate of this signal for a given geometry')
        return


    # solution에서 정보 꺼내오기
    geo_id = min_solution['geo_id']
    geo = min_solution['geo']
    u = min_solution['u']
    v = min_solution['v']
    t = min_solution['t']

    a = geo['params'][0]
    b = geo['params'][1]
    c = geo['params'][2]
    d = geo['params'][3]


    # 여기서 s를 구해야한다. s는 현재 곡선의 시작점으로부터 u까지 적분시 거리이다.
    """
    현재의 좌표게에서 곡선이 v = f(u)로 주어지고 있으므로, 
    곡선의 길이는 sqrt(1 + (dv/du)^2) 를 u에 대해 정적분하여 계산한다
    """
    def integrand(u, a, b, c, d):
        """적분 대상이 되는 함수이다"""
        return np.sqrt(1 + (3*d*u**2 + 2*c*u + b) ** 2)

    # scipy의 quad 함수를 이용하여 적분한다
    s, abs_error_estimate = quad(integrand, 0, u, args=(a,b,c,d))
    s += geo['s']

    min_solution['s'] = s

    return min_solution


def __draw_plot_to_check_solution(min_solution, signal_pos):
    converter = MGeoToOdrDataConverter.get_instance()

    geo_id = min_solution['geo_id']
    geo = min_solution['geo']
    u = min_solution['u']
    v = min_solution['v']

    a = geo['params'][0]
    b = geo['params'][1]
    c = geo['params'][2]
    d = geo['params'][3]


    # fit된 곡선 그리기 위해서 계산
    def poly_fit_g(u_in):
        v = d * u_in**3 + c * u_in**2 + b * u_in + a
        return v

    v_fit = poly_fit_g(geo['uv_point'][:,0])
    uv_fit = to_np_array(geo['uv_point'][:,0], v_fit)
    xy_fit = converter.coordinate_transform(geo['hdg'], uv_fit)
    xy_fit += geo['xy']


    # fit된 곡선에서 signal과 가장 가까운 점 Q의 위치
    point_Q = np.array([u, v])
    point_Q = converter.coordinate_transform_point(geo['hdg'], point_Q)
    point_Q += geo['xy']


    # 이제 plot한다
    plt.figure()

    # xy 좌표
    # plt.plot(geo['data'][:,0], geo['data'][:,1], 'r') # 원본
    plt.plot(xy_fit[:,0], xy_fit[:,1], 'b--') # fit 결과 (uv좌표에서 fit -> xy로 변환)
    plt.plot(signal_pos[0], signal_pos[1], 'D', markersize=10) # signal 좌표
    plt.plot(point_Q[0], point_Q[1], 's', markersize=10) # 가장 가까운 점 좌표

    # uv 좌표에서 그리려면
    # plt.plot(geo['uv_point'][:,0], geo['uv_point'][:,1], 'g') #원본 좌표 변환 결과
    # plt.plot(uv_fit[:,0], uv_fit[:,1], 'b--') # fit 결과 (uv좌표에서)
    # plt.plot(sig_uv[0], sig_uv[1], 'D', markersize=10) #signal (uv 좌표에서)  
    # plt.plot(u, v, 's', markersize=10) #signal에서 가장 가까운 점

    plt.axis('equal')
    plt.show()


if __name__ == '__main__':

    # single_fit_test()
    # multiple_fit_test()


    """ """
    # signal_case = 1 >> 원 안쪽에 존재
    # signal_pos, ref_line_geometry = __create_geometry_set_circle(signal_case=1)


    # signal_case = 2 >> 원 바깥에 존재
    # signal_pos, ref_line_geometry = __create_geometry_set_circle(signal_case=2)


    """Linear, +t 케이스"""
    # s = np.sqrt(2^2 + 1^2) = 2.236 << Q(2,1)
    # t = np.sqrt(2^2 + 4^2) = 4.472
    # signal_pos, ref_line_geometry = __create_goemetry_set_1st_order_case(signal_case=1) 


    """Linear, -t 케이스"""
    # s = np.sqrt(2^2 + 1^2) = 2.236   << Q(2,1)
    # t = -1 * np.sqrt(2^2 + 4^2) = -4.472
    signal_pos, ref_line_geometry = __create_goemetry_set_1st_order_case(signal_case=2)


    solution = signal_tranform(signal_pos, ref_line_geometry)
    
    print('---------- solution ---------')
    print('s : {}'.format(solution['s']))
    print('t : {}'.format(solution['t']))

    __draw_plot_to_check_solution(solution, signal_pos)