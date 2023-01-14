from pyproj import Proj
import numpy as np 


def print_tm(name, tm):
    print('[ {} ]'.format(name))
    print('  >> East = {:.6f}, North = {:.6f}'.format(tm[0], tm[1]))
    print('')


def pyproj_example(p0_tm, p1_ll, projection):
    p1_tm = projection(p1_ll[1], p1_ll[0])
    p1_tm = np.array(p1_tm) # 계산 편의를 위해 numpy.array로 변경

    p1_local = p1_tm - p0_tm
    # print_tm('p1_local', p1_local)

    return p1_tm, p1_local


def test_pyproj_UTM52N():
    '''
    EPSG code를 이용하여 init하는 방법
    '''
    proj_A = Proj('epsg:32652') # UTM52N 좌표에 대한 projection
    proj_B = Proj('+proj=utm +zone=52 +datum=WGS84 +units=m +no_defs') # https://epsg.io/?format=json&q=32652 

    # 로컬 좌표계 원점 P0의 UTM52N 에서의 위치
    p0_tm = np.array([313008.55819800857, 4161698.628368007])

    # 임의의 위치 P1에서 GPS로 받은 Lat, Lon 값
    p1_ll = np.array([37.58492846055704, 126.88409451582986])

    p1_tm_A, p1_local_A = pyproj_example(p0_tm, p1_ll, proj_A)
    p1_tm_B, p1_local_B = pyproj_example(p0_tm, p1_ll, proj_B)

    print_tm('test_pyproj_UTM52N / error_local_AB', p1_local_A - p1_local_B)


def test_pyproj_TMMid():
    '''
    EPSG code를 이용하여 init하는 방법
    '''
    proj_A = Proj('epsg:5186') # UTM52N 좌표에 대한 projection
    proj_B = Proj('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs') # https://epsg.io/?format=json&q=5186

    # 로컬 좌표계 원점 P0의 UTM52N 에서의 위치
    p0_tm = np.array([313008.55819800857, 4161698.628368007])

    # 임의의 위치 P1에서 GPS로 받은 Lat, Lon 값
    p1_ll = np.array([37.58492846055704, 126.88409451582986])


    p1_tm_A, p1_local_A = pyproj_example(p0_tm, p1_ll, proj_A)
    p1_tm_B, p1_local_B = pyproj_example(p0_tm, p1_ll, proj_B)

    print_tm('test_pyproj_TMMid / error_local_AB', p1_local_A - p1_local_B)


if __name__ == '__main__':
    test_pyproj_UTM52N()
    test_pyproj_TMMid()