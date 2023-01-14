"""
Reference: https://pyproj4.github.io/pyproj/stable/index.html
Example written by MORAI Inc.
"""


from pyproj import Proj # How to install: https://pyproj4.github.io/pyproj/stable/installation.html
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


def pyproj_example():
    # 테스트 데이터: 차량에 탑재된 GPS의 위치 p1
    p1_ll_expected = [37.5828, 126.8889]
    print_ll('LL Position of P1', p1_ll_expected)

    """
    TM <-> LL 사이의 좌표 변환을 제공하는 Proj 클래스 생성하기
    https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj-proj
    """
    # 초기화 방법: https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj.Proj.__init__
    proj_obj = Proj('epsg:32652') # UTM52N 좌표의 EPSG 코드 (32652)를 이용하여 초기화

    # 또는 PROJ string을 이용하는 것도 가능하다
    # 아래 PROJ string은 https://epsg.io/?format=json&q=32652 를 통해 받아올 수 있음
    # proj_obj = Proj('+proj=utm +zone=52 +datum=WGS84 +units=m +no_defs')


    """ LL -> TM """
    # Coordinate Transform, LL -> TM
    p1_lon = p1_ll_expected[1]
    p1_lat = p1_ll_expected[0]
    p1_tm = proj_obj(p1_lon, p1_lat) # [NOTE] 주의!!! long, lat 순서로 입력
    
    # [NOTE] 결과가 np.ndarray가 아님! (tuple 이다). 따라서 np.ndarray로 변환하는 것을 추천 
    p1_tm = np.array(p1_tm)
    print_tm('LL -> TM Result', p1_tm)


    """ TM -> LL """
    # Coordinate Transform, TM -> LL
    p1_lon_actual, p1_lat_actual =\
        proj_obj(p1_tm[0], p1_tm[1], inverse=True) # [NOTE] 주의!!! long, lat 순서로 리턴
    
    # [NOTE] 결과가 lon, lat 순서이므로, np.ndarray로 변환 시 순서도 반대로 입력하는 것에 유의
    p1_ll_actual = np.array([p1_lat_actual, p1_lon_actual])
    print_ll('LL -> TM -> LL Result', p1_ll_actual)


    """ Check Error in the Conversion """
    error = p1_ll_actual - p1_ll_expected
    error_threshold = 1e-8
    assert np.abs(error[0]) < error_threshold, 'Error in the latitude is too large'
    assert np.abs(error[1]) < error_threshold, 'Error in the longitude is too large'


if __name__ == '__main__':
    pyproj_example()