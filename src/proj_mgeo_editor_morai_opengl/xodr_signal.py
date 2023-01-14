"""
OdrSignal Module
"""

import os 
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from lib.common.logger import Logger

import numpy as np
from scipy.integrate import quad

import mgeo_odr_converter
import lxml.etree as etree

from lib.tomtom.tomtom_converter import convert_sign

class OdrSignal(object):
    """
    OdrSignal
    """

    def __init__(self):
        self.s = 0
        self.t = 0
        self.id = ""
        self.name = ""
        self.dynamic = '' # yes or no
        self.orientation = '' # + or -
        self.z_offset = 0 # z offset from track level to bottom edge of the mgeo_signal
        self.country = '' # 나라 이름, 필수 값은 아님
        self.country_revision = '' # int or str
        self.type = ''  # int or str
        self.sub_type = '' # int or str         
        self.value = 0
        self.unit = ''
        self.width = 0
        self.height = 0
        self.h_offset = 0 # heading offset

        self.position_inertial_pos = np.array([0.0, 0.0, 0.0], dtype=np.float64) # x, y, z
        self.position_inertial_ori = np.array([0.0, 0.0, 0.0], dtype=np.float64) # roll, pitch, heading


    def ToXml(self, parent):
        xodr_road_signal = etree.SubElement(parent, 'signal')
        xodr_road_signal.set('s', '{:.16e}'.format(self.s))
        xodr_road_signal.set('t', '{:.16e}'.format(self.t))
        xodr_road_signal.set('id', '{}'.format(self.id))
        xodr_road_signal.set('name', '{}'.format(self.name))
        xodr_road_signal.set('dynamic', '{}'.format(self.dynamic))
        xodr_road_signal.set('orientation', '{}'.format('-'))
        # xodr_road_signal.set('orientation', '{}'.format(self.orientation))
        xodr_road_signal.set('zOffset', '{:.16e}'.format(self.z_offset))
        xodr_road_signal.set('country', '{}'.format(self.country))
        xodr_road_signal.set('countryRevision', '{}'.format(self.country_revision))
        xodr_road_signal.set('type', '{}'.format(self.type))
        xodr_road_signal.set('subtype', '{}'.format(self.sub_type))
        xodr_road_signal.set('value', '{:.16e}'.format(self.value))
        # xodr_road_signal.set('unit', '{}'.format(self.unit))
        xodr_road_signal.set('unit', '{}'.format('km/h'))
        xodr_road_signal.set('height', '{}'.format(self.height))
        xodr_road_signal.set('width', '{}'.format(self.width))
        xodr_road_signal.set('hOffset', '{:.16e}'.format(self.h_offset))
        
        position_inertial = etree.SubElement(xodr_road_signal, 'positionInertial')
        position_inertial.set('x', '{:.16e}'.format(self.position_inertial_pos[0]))
        position_inertial.set('y', '{:.16e}'.format(self.position_inertial_pos[1]))
        position_inertial.set('z', '{:.16e}'.format(self.position_inertial_pos[2]))
        position_inertial.set('hdg', '{:.16e}'.format(self.position_inertial_ori[2]))
        position_inertial.set('pitch', '{:.16e}'.format(self.position_inertial_ori[1]))
        position_inertial.set('roll', '{:.16e}'.format(self.position_inertial_ori[0]))   


    @staticmethod
    def MGeoSignalTypeToOdrSignalType(mgeo_signal, force_change_to_carla_supported_ones=False):
        """
        [USER_OPTION] CARLA에서는 신호등은 1000001, 표지판은 205 타입에 해당하는 Actor만 load를 지원한다.
            CARLA에서 출력해서 보기 위해 강제하려면 force_change_to_carla_supported_ones를 True로 입력한다.
            False로 주면, mgeo_signal에 담긴 값을 그대로 사용한다. 

        NOTE: False로 사용할 때 실제 의미가 있는 값은 sub_type 값이다. 42dot HD Map 포맷에서 신호등 또는
            표지판의 실제 형상을 나타내는 값은 sub_type이기 때문.
        """

        odr_signal_type = 205
        odr_signal_sub_type = 1
        odr_signal_value = 0
        odr_signal_unit = ''

        if force_change_to_carla_supported_ones:
            if mgeo_signal.dynamic == True:
                if mgeo_signal.type == 'pedestrian':
                    odr_signal_type = 1000002
                else:
                    odr_signal_type = 1000001
                    odr_signal_sub_type = len(mgeo_signal.sub_type)
            else:
                odr_signal_type = 205
        else:
            # tomtom 일 때
            if mgeo_signal.type_def == 'tomtom':
                odr_signal_type, odr_signal_sub_type, odr_signal_value, odr_signal_unit = convert_sign(mgeo_signal.type, mgeo_signal.sub_type)

            else:
                odr_signal_type = 205
                odr_signal_sub_type = 1
                odr_signal_value = 0
                odr_signal_unit = ''
                
        # 현재는 subtype을 변경할 일이 없다. 그대로 사용
        # odr_signal_sub_type = mgeo_signal.sub_type
        # >> Subtype identifier according to country code
        # odr_signal_sub_type = -1

        return odr_signal_type, odr_signal_sub_type, odr_signal_value, odr_signal_unit


    @staticmethod
    def CreateInstanceFromMGeoSignal(mgeo_signal, road, fix_road, candidate_roads=None):
        odr_signal = OdrSignal()
        cm_to_m = 100
        data_name = 'TL' if mgeo_signal.dynamic else 'TS'

        """ STEP #1 좌표 변환 관련 코드들 """

        # position inertial에서 위치는 mgeo signal의 위치를 그대로 사용하면 된다
        odr_signal.position_inertial_pos = mgeo_signal.point

        # 좌표 변환에 대해서, 경우의 수가 총 4가지가 있다
        # CASE #1 : 좌표 변환이 주어진 road에 대해 성공한 경우
        # CASE #2 : 좌표 변환이 주어진 road에 대해 실패했고, 다른 road에 대해 가능한지 확인하지 않는 경우
        # CASE #3 : 좌표 변환이 주어진 road에 대해 실패했고, 다른 road에 대해 가능한지 확인하여 성공한 경우
        # CASE #4 : 좌표 변환이 주어진 road에 대해 실패했고, 다른 road에 대해 가능한지 확인했지만 실패한 경우

        # position inertial에서 자세 정보는 s, t 좌표로 변환한 다음,
        # ref line에 수선의 발이 되는 점 Q를 찾고, 점Q에서의 heading을 계산하여 얻을 수 있다
        # 자세에서 pitch, roll은 0으로 둔다.
        ref_line_geometry = OdrSignal.GetRefLineGeometry(mgeo_signal, road)
        solution = OdrSignal.SignalCoordinateTranform(mgeo_signal.point[0:2], ref_line_geometry)
        if solution is not None:
            """
            CASE #1
            좌표 변환이 주어진 road에 대해 성공한 경우
            """

            # 현재 참조되어있는 road의 ref line에 수선의 발을 내릴 수 있어, 해를 구한 경우이다.
            # [USER_OPTION] >> positionInertial을 어차피 사용할 예정이므로, 그냥 임의의 값 (0, 1) 같은 값을 사용해도 된다.
            matching_odr_road_for_return = road
            odr_signal.s = solution['s']
            odr_signal.t = solution['t']
            odr_signal.position_inertial_ori[2] = solution['hdg']

            Logger.log_info('{}: {} coordinate transform done successfully. (road: {}, s: {:.4f}, t: {:.4f}, hdg: {:.4f} (deg))'.format(
                data_name, mgeo_signal.idx, road.road_id, solution['s'], solution['t'], solution['hdg'] * 180/np.pi))    

        else:
            # 주어진 road에서 찾는 것을 실패한 경우이다.
            if fix_road:
                # 현재 참조되어있는 road의 ref line에 수선의 발을 내릴 수 없는 경우이다.
                # 이 때는 road의 successor 되는 road 중에서 수선의 발을 내릴 수 있는 ref line이 있는지
                # 찾아보고, 찾아지면 거기서 heading을 계산한다.
            
                if candidate_roads is None:
                    # 처음 fail 되었을 때, 검색해야할 road 후보군을 만든다
                    candidate_roads = road.get_multi_depth_successor_roads(depth=5)

                # road 후보군에서 수선의 발을 내릴 수 있는 ref line을 찾아본다.
                result, solution, matching_road = OdrSignal.FindMatchingRoad(mgeo_signal, candidate_roads)
                if result:
                    """
                    CASE #3
                    좌표 변환이 주어진 road에 대해 실패했고, 다른 road에 대해 가능한지 확인하여 성공한 경우
                    """
                    log_msg = '{}: {} coordinate done successfully, but for another road.'.format(data_name, mgeo_signal.idx)
                    log_msg += ' (original road: {} -> matching road {}, '.format(road.road_id, matching_road.road_id)
                    log_msg += 's: {:.4f}, t: {:.4f}, hdg: {:.4f} (deg))'.format(solution['s'], solution['t'], solution['hdg'] * 180/np.pi)
                    
                    Logger.log_info(log_msg)
                    
                    # [USER_OPTION] 찾았으면, 이 solution에서 s,t를 가져다 쓸 수 있다. (대신 road도 같이 바뀌어야 함.)
                    # >> positionInertial을 어차피 사용할 예정이므로, 
                    # s, t 값은 활용하지 않고 (따라서 road에 대한 reference 또한 수정하지 않고)
                    # road에서 orientation만 이용해도 된다. 
                    matching_odr_road_for_return = matching_road
                    odr_signal.s = solution['s'] # [USER_OPTION] 바로 위 설명에 따라 0을 써도 된다
                    odr_signal.t = solution['t'] # [USER_OPTION] 바로 위 설명에 따라 0을 써도 된다
                    odr_signal.position_inertial_ori[2] = solution['hdg']

                    # mgeo signal의 road_id 또한 변경해준다 
                    mgeo_signal.road_id = matching_odr_road_for_return.road_id

                else:
                    """
                    CASE #4
                    좌표 변환이 주어진 road에 대해 실패했고, 다른 road에 대해 가능한지 확인했지만 실패한 경우
                    """
                    # 후보군에서도 ref line에 수직으로 발을 내릴 수 있는 road가 없다는 것
                    # orientation을 계산할 방법이 없으므로 그냥 0으로 둔다.
                    matching_odr_road_for_return = None
                    odr_signal.s = 0
                    odr_signal.t = 0 
                    odr_signal.position_inertial_ori[2] = 0.0
                    Logger.log_error('Failed to find s,t coordinate for {}: {} & road: {}'.format(data_name, mgeo_signal.idx, road.road_id))
                    
            else:
                """
                CASE #2
                좌표 변환이 주어진 road에 대해 실패했고, 다른 road에 대해 가능한지 확인하지 않는 경우
                """
                # orientation을 계산할 방법이 없으므로 그냥 0으로 둔다.
                matching_odr_road_for_return = None
                odr_signal.s = 0
                odr_signal.t = 0 
                odr_signal.position_inertial_ori[2] = 0.0
                Logger.log_error('Failed to find s,t coordinate for {}: {} & road: {}'.format(data_name, mgeo_signal.idx, road.road_id))


        # z_offset 값은 mgeo 데이터에서 전달된 데이터를 사용한다.
        odr_signal.z_offset = mgeo_signal.z_offset
        # solution 값이 있을 경우 road point를 이용해서
        
        if solution is not None:
            
            elev = solution['geo']['elev']
            e_curve = np.poly1d([elev[3], elev[2], elev[1], elev[0]])
            curve_z = np.polyval(e_curve, np.sqrt(np.power(solution['u'],2) + np.power(solution['v'], 2)))
            
            # tomtom 데이터 signal의 height값이 cm -> opendrive에서는 m 단위 변환 필요
            # (※ tomtom 원본 데이터에서 같은 표지판별로 width/height값이 일정하지 않음)
            if mgeo_signal.type_def == 'tomtom':
                # signal point 가 교통 표지판(바 제외)의 중앙값
                # z_offset = signal point(Z) - 도로의 높이 - (signal height(m)/2)로 계산한다.
                odr_signal.z_offset = mgeo_signal.point[2] - curve_z - (mgeo_signal.height/cm_to_m)/2
                mgeo_signal.z_offset = odr_signal.z_offset
            else:
                odr_signal.z_offset = mgeo_signal.z_offset
            # print('Z: {}, sign_height: {}, sign_z: {}'.format(curve_z, mgeo_signal.height/200, mgeo_signal.point[2]))

        odr_signal.orientation = mgeo_signal.orientation # NOTE: 42dot에서는 road가 단방향이므로, orientation은 항상 +이다.

        """ STEP #2 그 밖의 id, name, 타입 등 정보들 """

        odr_signal.id = mgeo_signal.idx
        odr_signal.name = mgeo_signal.idx # name은 id와 동일하게 설정
       
        odr_signal.dynamic = 'yes' if mgeo_signal.dynamic else 'no'
        
        odr_signal.country = mgeo_signal.country
        odr_signal.country_revision = '2014'
        
        # [USER_OPTION] Signal에 대해, CARLA에서 지원하는 타입만 사용하게 변경할 수 있다
        # force_change_to_carla_supported_ones 파라미터를 True/False로 중 선택
        # odr_signal_type, odr_signal_sub_type, odr_signal_value, odr_signal_unit = OdrSignal.MGeoSignalTypeToOdrSignalType(
        #     mgeo_signal, force_change_to_carla_supported_ones=False)

        odr_signal_type, odr_signal_sub_type, odr_signal_value, odr_signal_unit = OdrSignal.MGeoSignalTypeToOdrSignalType(
            mgeo_signal, force_change_to_carla_supported_ones=True)

        odr_signal.type = odr_signal_type
        odr_signal.sub_type = odr_signal_sub_type

        odr_signal.value = odr_signal_value
        odr_signal.unit = odr_signal_unit
        if mgeo_signal.type_def == 'tomtom':
            odr_signal.width = mgeo_signal.width / cm_to_m
            odr_signal.height = mgeo_signal.height / cm_to_m
        else:
            odr_signal.width = mgeo_signal.width
            odr_signal.height = mgeo_signal.height
        # mgeo 원본 데이터에 orientation 정보가 없으므로, heading offset 계산은 지원되지 않음
        odr_signal.h_offset = 0

        return odr_signal, matching_odr_road_for_return


    @staticmethod
    def FindMatchingRoad(mgeo_signal, candidate_roads):
        """candidate_roads에 속한 road 중에서 mgeo_signal이 수선의 발을 내릴 수 있는 road를 찾고, 그 때 s,t 값을 전달한다"""    
        for road in candidate_roads:
            
            ref_line_geometry = OdrSignal.GetRefLineGeometry(mgeo_signal, road)
            solution = OdrSignal.SignalCoordinateTranform(mgeo_signal.point[0:2], ref_line_geometry)
            if solution is not None:
                # solution을 찾은 것!
                return True, solution, road

        # solution을 찾지 못한 것
        return False, None, None
                

    @staticmethod
    def GetRefLineGeometry(mgeo_signal, road):
        """road의 polyfit 정보 받아와서 ref_line_geometry에 저장하기"""
        ref_line_geometry = list()
        
        # Logger.log_debug('--------- signal id {} ----------'.format(mgeo_signal.idx))
        for section_idx, lane_section in enumerate(road.get_lane_sections()):
            # Logger.log_debug('  section_idx = {}'.format(section_idx))
            for v_idx, vector in enumerate(lane_section.geometry):
                
                # init_s = lane_section.vector_s_offset[v_idx]
                # init_xy = lane_section.init_coord[v_idx]
                # init_hdg = lane_section.heading[v_idx]
                # length = lane_section.arclength[v_idx]

                # Logger.log_debug('    v_idx = {}'.format(v_idx))
                # Logger.log_debug('      s = {}'.format(init_s))
                # Logger.log_debug('      xy = {}'.format(init_xy))
                # Logger.log_debug('      hdg = {}'.format(init_hdg))
                # Logger.log_debug('      l = {}'.format(length))

                if road.is_line(lane_section.geometry[v_idx]):
                    model = 'line'
                elif len(lane_section.geometry[v_idx]) == 8:
                    model = 'paramPoly3'
                elif len(lane_section.geometry[v_idx]) == 4:
                    model = 'poly3'
                else:
                    Logger.log_error('Road ID {}, Signal ID {}'.format(road.road_id, mgeo_signal.id))
                    raise BaseException('[ERROR] Unexpected geometry type detected')

                ref_line_geometry.append(
                    {'model': model,
                     's': lane_section.vector_s_offset[v_idx],
                     'xy': lane_section.init_coord[v_idx],
                     'hdg': lane_section.heading[v_idx],
                     'len': lane_section.arclength[v_idx],
                     'params': lane_section.geometry[v_idx],
                     'u_max': lane_section.geometry_u_max[v_idx]
                    #  'elev': lane_section.elevation[v_idx]
                    })

        return ref_line_geometry


    @staticmethod
    def SignalCoordinateTranform(signal_pos, ref_line_geometry):
        converter = mgeo_odr_converter.MGeoToOdrDataConverter.get_instance()

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
            
            if geo["model"] =='poly3':
                a = geo['params'][0]
                b = geo['params'][1]
                c = geo['params'][2]
                d = geo['params'][3]
            elif geo["model"] =='paramPoly3':
                aU = geo['params'][0]
                bU = geo['params'][1]
                cU = geo['params'][2]
                dU = geo['params'][3]
                aV = geo['params'][4]
                bV = geo['params'][5]
                cV = geo['params'][6]
                dV = geo['params'][7]
            else:
                a = geo['params'][0]
                b = geo['params'][1]
                c = geo['params'][2]
                d = geo['params'][3]
            
            if geo["model"] =='paramPoly3':
                u_t = np.poly1d([dU, cU, bU, aU])
                v_t = np.poly1d([dV, cV, bV, aV])
                
                curve_dot_u = np.polyder(u_t)
                curve_dot_v = np.polyder(v_t)
                
                f = np.poly1d([dU, cU, bU, aU -sig_u]) ** 2 + np.poly1d([dV, cV, bV, aV - sig_v]) ** 2
                f_dot = np.polyder(f)
                
                all_roots = np.roots(f_dot)
                
                real_roots = all_roots[abs(all_roots.imag) < 1e-6]
                real_roots = real_roots.real
                for t in real_roots:
                    if t > 0 and t < 1:

                        # 이제 distance를 계산해본다
                        distance = np.polyval(f, t) ** 0.5

                        # curve에서 해당 위치
                        u = np.polyval(u_t, t)
                        v = np.polyval(v_t, t)
                        Q = np.array([u, v])

                        if distance < min_dist:
                            vect = np.array([1, np.polyval(curve_dot_v, t)/np.polyval(curve_dot_u, t)])
                            vect = vect / np.linalg.norm(vect) # unit vector화

                            qp_vect = np.array([sig_u - u, sig_v - v])
                            qp_vect = qp_vect / np.linalg.norm(qp_vect) # unit vector화

                            dot_prod = np.inner(vect, qp_vect)
                            angle_deg = np.arccos(dot_prod) * 180 / np.pi

                            # 90 deg에서 오차가 1 deg 보다 크면 문제가 있는 것으로 판단.
                            if abs(90 - angle_deg) > 1.0: 
                                # 이렇게 값이 나온다면 뭔가 이상한 것 >> 반드시 수직이어야 하는데??
                                Logger.log_warning('Unexpected result from min_dist calculation. QP vector ')

                            # qp_vect 방향이 s-t 좌표계 정의에 대해 +인지 -인지 확인한다
                            cross_prod = np.cross(vect, qp_vect)
                            if cross_prod > 0: 
                                t_sign = distance
                            elif cross_prod < 0:
                                t_sign = -1 * distance
                            else:
                                t_sign = 0

                            # s_vect로부터 heading 계산 (이 vector는 uv 좌표계에서 정의된 vector이므로 다시 inertial 좌표계로 회전시켜야 함)
                            vect_in_inertial = converter.coordinate_transform_point(geo['hdg'], vect)
                            hdg = np.arctan2(vect_in_inertial[1], vect_in_inertial[0])
                            # Logger.log_debug('hdg: {} (deg)'.format(hdg * 180 / np.pi))

                            min_dist = distance
                            min_solution = {
                                'geo_id': geo_id,
                                'geo': geo,
                                'u': u,
                                'v': v,
                                't': t_sign,
                                'hdg': hdg,
                                'param_t' : t
                            }
                    else:
                        continue
                
                if min_solution == None:
                    continue

            elif geo["model"] =='poly3':
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
                # Logger.log_debug('real_roots: ', real_roots)

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

                            # 90 deg에서 오차가 1 deg 보다 크면 문제가 있는 것으로 판단.
                            if abs(90 - angle_deg) > 1.0: 
                                # 이렇게 값이 나온다면 뭔가 이상한 것 >> 반드시 수직이어야 하는데??
                                Logger.log_warning('Unexpected result from min_dist calculation. QP vector ')

                            # qp_vect 방향이 s-t 좌표계 정의에 대해 +인지 -인지 확인한다
                            cross_prod = np.cross(s_vect, qp_vect)
                            if cross_prod > 0: 
                                t = distance
                            elif cross_prod < 0:
                                t = -1 * distance
                            else:
                                t = 0

                            # s_vect로부터 heading 계산 (이 vector는 uv 좌표계에서 정의된 vector이므로 다시 inertial 좌표계로 회전시켜야 함)
                            s_vect_in_inertial = converter.coordinate_transform_point(geo['hdg'], s_vect)
                            hdg = np.arctan2(s_vect_in_inertial[1], s_vect_in_inertial[0])
                            # Logger.log_debug('hdg: {} (deg)'.format(hdg * 180 / np.pi))

                            min_dist = distance
                            min_solution = {
                                'geo_id': geo_id,
                                'geo': geo,
                                'u': u,
                                'v': v,
                                't': t,
                                'hdg': hdg
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
                        Logger.log_debug('Skip this root (u = {} not in proper range)'.format(u))
        
        if min_solution is None:
            Logger.log_warning('Failed to find s,t coordinate of this signal for a given geometry')
            return

        # solution에서 정보 꺼내오기
        geo_id = min_solution['geo_id']
        geo = min_solution['geo']
        u = min_solution['u']
        v = min_solution['v']
        t = min_solution['t']
        if geo["model"] =='paramPoly3':
            param_t = min_solution['param_t']

        # 여기서 s를 구해야한다. s는 현재 곡선의 시작점으로부터 u까지 적분시 거리이다.
        """
        현재의 좌표게에서 곡선이 v = f(u)로 주어지고 있으므로, 
        곡선의 길이는 sqrt(1 + (dv/du)^2) 를 u에 대해 정적분하여 계산한다
        """
        
        def integrand_param(param_t, aU, bU, cU, dU, aV, bV, cV, dV):
            """적분 대상이 되는 함수이다"""
            return np.sqrt((3*dU*param_t**2 + 2*cU*param_t + bU) ** 2 + (3*dV*param_t**2 + 2*cV*param_t + bV) ** 2)

        def integrand(u, a, b, c, d):
            """적분 대상이 되는 함수이다"""
            return np.sqrt(1 + (3*d*u**2 + 2*c*u + b) ** 2)

        # scipy의 quad 함수를 이용하여 적분한다
        if geo["model"] =='paramPoly3':
            s, abs_error_estimate = quad(integrand_param, 0, param_t, args=(aU, bU, cU, dU, aV, bV, cV, dV))
            s += geo['s']
            min_solution['s'] = s
        else:
            s, abs_error_estimate = quad(integrand, 0, u, args=(a,b,c,d))
            s += geo['s']
            min_solution['s'] = s

        return min_solution