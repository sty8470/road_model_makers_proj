import matplotlib.pyplot as plt
import numpy as np

point_array = np.array([[3.92417112e+05, 4.19430430e+06, 2.28662720e+02],
       [3.92421289e+05, 4.19430125e+06, 2.28579956e+02],
       [3.92421933e+05, 4.19430213e+06, 2.28556717e+02],
       [3.92417756e+05, 4.19430518e+06, 2.28611511e+02],
       [3.92417112e+05, 4.19430430e+06, 2.28662720e+02]])


def plot_test():
    new_point = _calculate_centeroid_in_polygon(point_array)
    x, y, z = point_array.T
    # plt.scatter(x, y, z)
    # plt.scatter(new_point[0], new_point[1], new_point[2])
    plt.scatter(x, y)
    plt.scatter(new_point[0], new_point[1])
    plt.show()

def _calculate_centeroid_in_polygon(point_list):
    '''
    polygon을 구성하는 점들로부터 centeroid를 계산한다.
    밀도가 균일하다면 center of mass와 동일하며,
    이 점은 각 좌표의 산술 평균이다.
    '''
    x = point_list[:,0]
    y = point_list[:,1]
    z = point_list[:,2]

    return np.array([np.mean(x), np.mean(y), np.mean(z)])


if __name__ == "__main__":
    plot_test()