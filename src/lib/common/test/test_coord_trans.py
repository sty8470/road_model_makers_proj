import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))

from coord_trans_ll2tm import CoordTrans_LL2TM
from coord_trans_tm2ll import CoordTrans_TM2LL

from pyproj import Proj

import numpy as np

def print_tm(name, tm):
    print('[ {} ]'.format(name))
    print('  >> East = {:.4f}, North = {:.4f}'.format(tm[0], tm[1]))
    print('')
    # print('------------------------------')


def print_ll(name, ll):
    print('[ {} ]'.format(name))
    print('   >> Lat = {:.8f}, Long = {:.8f}'.format(ll[0], ll[1]))
    print('')
    # print('------------------------------')


def main():
    print('')
    P0_tm = np.array([313008.55819800857, 4161698.628368007])
    P0_loop_conv_website = np.array([313008.52, 4161698.64])
    error_loop_conv_website = P0_loop_conv_website - P0_tm

    print_tm('error_loop_conv_website', error_loop_conv_website)


    """
    p1 : 시뮬레이터 내 특정 위치

    p1_lat = 37.58492846055704
    p1_lon = 126.88409451582986
    p1_alt : 41.05110319382138

    pose_x : 166.77102661132812
    pose_y : 170.27838134765625
    pose_z : 4.634336948394775
    """


    """
    TEST #1 
    내 로직 체크,
    TM 좌표로 표현된 로컬 좌표계 원점을,
    LL 좌표로 변환했다가 다시 TM 좌표로 변환하여, 
    처음 값과 완전히 동일한지 확인한다
    """
    my_ll2tm = CoordTrans_LL2TM()
    my_tm2ll = CoordTrans_TM2LL()

    my_ll2tm.set_tm_params(
        spheroid='WGS84',
        latitude_of_origin=0,
        central_meridian=129,
        scale_factor=0.9996,
        false_easting=500000,
        false_northing=0)

    my_tm2ll.set_tm_params(
        spheroid='WGS84',
        latitude_of_origin=0,
        central_meridian=129,
        scale_factor=0.9996,
        false_easting=500000,
        false_northing=0)

    P0_myproj_ll = my_tm2ll.tm2ll(east=P0_tm[0], north=P0_tm[1])
    P0_loop_conv_myproj = my_ll2tm.ll2tm(lat=P0_myproj_ll[0], lon=P0_myproj_ll[1])
    error_loop_conv_myproj = P0_loop_conv_myproj - P0_tm

    print_ll('P0_myproj_ll', P0_myproj_ll)
    print_tm('error_loop_conv_myproj', error_loop_conv_myproj)

    """
    TEST #2
    pyproj를 사용
    """
    p = Proj('epsg:32652')
    
    P0_pyproj_ll = p(P0_tm[0], P0_tm[1], inverse=True) # 주의: 리턴값이 long, lat 순서임
    P0_loop_conv_pyproj = p(P0_pyproj_ll[0], P0_pyproj_ll[1]) # 주의: 입력값이 long, lat 순서임
    error_loop_conv_pyproj = P0_loop_conv_pyproj - P0_tm


    print('\n********** Reference 값 (pyproj로 계산) **********')
    print_ll('pyproj로 P0를 LL로 변환한 값',
        (P0_pyproj_ll[1], P0_pyproj_ll[0])) # long, lat 순서라 반대로 넣어주어야 함
    print_tm('pyproj로 P0를 LL로 변환하고, 다시 TM으로 변환하여 같은지 체크',
        error_loop_conv_pyproj)


    """
    비교 #1
    pyproj 과 myproj를 비교,
    p0 TM을 p0 LL로 변환한 결과를 비교함
    """
    print('\n********** myproj의 TM-LL 코드 검증 **********')
    print_ll('myproj로 P0를 LL로 변환한 값',
        P0_myproj_ll)  

    error_ll_pyproj_myproj = np.array(P0_myproj_ll) - np.array([P0_pyproj_ll[1], P0_pyproj_ll[0]])
    print_ll('myproj로 P0를 LL로 변환한 값을 pyproj 코드로 계산한 결과와 비교',
        error_ll_pyproj_myproj)


    """
    비교 #2
    pyproj 과 website 결과를 비교
    """
    # website: https://www.engineeringtoolbox.com/utm-latitude-longitude-d_1370.html
    print('\n********** 참고하는 website의 TM-LL 코드 검증 **********')
    P0_website_ll = np.array([37.583367, 126.882242])
    print_ll('website에서 P0를 LL로 변환한 값',
        P0_website_ll)

    error_ll_pyproj_website = np.array(P0_website_ll) - np.array([P0_pyproj_ll[1], P0_pyproj_ll[0]])
    print_ll('website로 P0를 LL로 변환한 값을 pyproj로 계산한 결과와 비교',
        error_ll_pyproj_website)
    


    #############################################################
    ##################### LL -> TM 변환 검증 #####################
    #############################################################

    # Pajou_ll = [37.58492846055704, 126.88409451582986]
    Pajou_ll = [37.584928, 126.884095]

    print('\n********** Reference 값 (pyproj로 계산) **********')
    Pajou_tm_pyproj = p(Pajou_ll[1], Pajou_ll[0]) # 주의: 입력값이 long, lat 순서임

    print_tm('아주대 로컬 point 위치', Pajou_tm_pyproj)

    
    print('\n********** myproj의 TM-LL 코드 검증 **********')
    Pajou_tm_myproj = my_ll2tm.ll2tm(Pajou_ll[0], Pajou_ll[1])
    print_tm('myproj로 아주대 로컬 point 위치를 TM으로 변환한 것', Pajou_tm_myproj)

    error_ll2tm_myproj = np.array(Pajou_tm_myproj) - np.array(Pajou_tm_pyproj)
    print_tm('myproj로 아주대 로컬 point 위치를 TM으로 변환한 것을 Pyproj로 계산한 것과 비교', error_ll2tm_myproj)


    print('\n********** 참고하는 website의 TM-LL 코드 검증 **********')
    # website: https://www.latlong.net/lat-long-utm.html >> 상대적으로 정확도 떨어지는 것 같음
    Pajou_tm_website = np.array([313176.05, 4161868.16])
    print_ll('website에서 아주대 로컬 point 위치를 TM으로 변환한 값',
        Pajou_tm_website)
        
    error_ll2tm_website = Pajou_tm_website - np.array(Pajou_tm_pyproj)
    print_tm('website에서 아주대 로컬 point 위치를 TM으로 변환한 것을 Pyproj로 계산한 것과 비교',
        error_ll2tm_website)


    ##########################################################################
    ##################### local tm좌표계로의 변환까지 검증 #####################
    ##########################################################################
    Pajou_local_pyproj = Pajou_tm_pyproj - P0_tm
    print_tm('pyproj를 이용해 아주대 로컬 point 위치를 로컬TM으로 변환한 값', Pajou_local_pyproj)


    Pajou_local_myproj = Pajou_tm_myproj - P0_tm
    print_tm('myproj를 이용해 아주대 로컬 point 위치를 로컬TM으로 변환한 값', Pajou_local_myproj)

    error_Pajou_local_myproj = Pajou_local_myproj - Pajou_local_pyproj
    print_tm('mypoint를 이용해 아주대 로컬 point 위치를 로컬TM으로 변환한 값을 Pyproj로 계산한 것과 비교',
        error_Pajou_local_myproj)


def another_test_case():
    '''
    RoadRunner Jeju Project
    
    '+proj=tmerc +lat_0=33.50211971401039 +lon_0=126.494539862743 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +geoidgrids=egm96_15.gtx +vunits=m +no_defs'
    '''
    jeju_coord = Proj('+proj=tmerc +lat_0=33.50211971401039 +lon_0=126.494539862743 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m')
    jeju_origin_tm_pyproj = jeju_coord(126.494539862743, 33.50211971401039) 
    print_tm('jeju_origin_tm_pyproj', jeju_origin_tm_pyproj)


    my_ll2tm = CoordTrans_LL2TM()
    my_ll2tm.set_tm_params(
        spheroid='WGS84',
        latitude_of_origin=33.50211971401039,
        central_meridian=126.494539862743,
        scale_factor=1.0,
        false_easting=0,
        false_northing=0)

    jeju_origin_tm_myproj = my_ll2tm.ll2tm(33.5021197, 126.4945399)
    print_tm('jeju_origin_tm_myproj', jeju_origin_tm_myproj)
    

if __name__ == '__main__':
    main()
    # another_test_case()