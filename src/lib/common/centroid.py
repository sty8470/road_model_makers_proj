import numpy as np

def calculate_centroid(points):
    sx = sy= sz = sL = 0
    for i in range(len(points)):
        x0, y0, z0 = points[i - 1]     # in Python points[-1] is last element of points
        x1, y1, z1 = points[i]
        L = ((x1 - x0)**2 + (y1 - y0)**2 + (z1-z0)**2) ** 0.5
        sx += (x0 + x1)/2 * L
        sy += (y0 + y1)/2 * L
        sz += (z0 + z1)/2 * L
        sL += L
        
    centroid_x = sx / sL
    centroid_y = sy / sL
    centroid_z = sz / sL

    # print('cent x = %f, cent y = %f, cent z = %f'%(centroid_x, centroid_y, centroid_z))

    # TODO: 계산하는 공식 추가하기
    return np.array([centroid_x,centroid_y, centroid_z])

def sorted_points(points):
    xs = []
    xy = []
    for i in points:
        xs.append(i[0])
        xy.append(i[1])

    harf_x = (max(xs) + min(xs)) / 2 
    
    # 겹치는 x값이 있는지 확인
    if harf_x in xs:
        harf_x = harf_x + 0.001
    
    y_right = []
    y_left = []

    #harf_x보다 x값이 작은 좌표집합과 큰 좌표집합으로 분리
    for i in points:
        if i[0] < harf_x:
            y_left.append(i)
        else: 
            y_right.append(i)

    y_left.sort(key=lambda x : x[1] , reverse = False)
    y_right.sort(key=lambda x : x[1] , reverse = True)

    return np.array(y_left + y_right)
