from pyproj import Proj
import numpy as np 


def print_tm(name, tm):
    print('[ {} ]'.format(name))
    print('  >> East = {:.6f}, North = {:.6f}'.format(tm[0], tm[1]))
    print('')


def pyproj_example():
    # 로컬 좌표계 원점 p0의 UTM52N에서의 위치
    p0_tm = np.array([313008.55819800857, 4161698.628368007])

    # 차량에 탑재된 GPS의 위치 p1
    p1_lat = 37.58492846055704
    p1_lon = 126.88409451582986

    '''
    TM <-> LL 사이의 좌표 변환을 제공하는 Proj 클래스
    https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj-proj
    '''

    # 초기화 방법: https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj.Proj.__init__
    projection_obj = Proj('epsg:32652') # UTM52N 좌표의 EPSG 코드 (32652)를 이용하여 초기화

    # 또는 PROJ string을 이용하는 것도 가능하다
    # 아래 PROJ string은 https://epsg.io/?format=json&q=32652 를 통해 받아올 수 있음
    # projection_obj = Proj('+proj=utm +zone=52 +datum=WGS84 +units=m +no_defs')

    # 호출하여 좌표 변환하기
    p1_tm = projection_obj(p1_lon, p1_lat) # 주의: longitude, latitude 순서로 입력
    
    # 이후 계산 편의를 위해 numpy.array로 변경
    p1_tm = np.array(p1_tm)

    # p1의 위치를 로컬 좌표계에서 나타낸 것
    p1_local = p1_tm - p0_tm
    print_tm('p1_local', p1_local)

    # *참고* pos_x, pos_y (문의 사항으로 전달주신 값)
    pos_xy = np.array([166.77102661132812, 170.27838134765625])
    print_tm('error w.r.t pose_x, pose_y from the simulator', pos_xy - p1_local)


if __name__ == '__main__':
    pyproj_example()