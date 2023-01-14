import numpy as np

# PS: Pedestrian Signal, 보행자용 신호등
# CW: Crosswalk, 횡단보도

def estimate_ps_direction(a, b):
    """
    a: PS → 반대쪽 PS로 향하는 벡터, 평면에서 정의 (z값 생략)
    b: PS가 참조하는 CW의 꼭지점 i에서 i+1로 향하는 벡터 중 (단 z값을 생략한 벡터)
    길이가 가장 긴 벡터.
    """
    mag_b = np.linalg.norm(b, ord=2) # 벡터 b의 크기
    
    proj_a_to_b = np.inner(a,b) / (mag_b**2) * b # 벡터 a를 벡터 b 방향으로 projection한 것

    unit_proj_a_to_b = proj_a_to_b / np.linalg.norm(proj_a_to_b, ord=2) # 벡터 a의 방향 벡터
    
    return unit_proj_a_to_b


def test_estimate_ps_direction():
    """
    테스트용 데이터22222222222222222
    보행자 신호등 PS1, PS2의 좌표
    """
    ps1 = np.array([1, 5, 0.1]) # z값은 임의로 0.1로 넣음
    ps2 = np.array([5, -1, 0.2]) # z값은 임의로 0.2로 넣음

    a1 = ps2[0:2] - ps1[0:2] # 보행자 신호등 PS1에서 PS2로 향하는 벡터 (z값 제외)
    a2 = ps1[0:2] - ps2[0:2] # 보행자 신호등 PS1에서 PS2로 향하는 벡터 (z값 제외)

    """
    테스트용 데이터
    PS가 참조하는 CW를 구성하는 꼭지점 i에서 i+1로 향하는 벡터 중 (단, z값을 제외한 벡터로) 
    길이가 가장 긴 벡터를 b 벡터로 한다.
    """
    b1 = np.array([0, 4]) 
    b2 = np.array([0, -4]) # 횡단보도를 구성하는 꼭지점의 정의 순서가 반대로 된 경우를 가정


    """ Test Case #1 """
    a = a1
    b = b1

    ps_direction_actual = estimate_ps_direction(a, b)
    ps_direction_expected = [0, -1]

    # 테스트가 결과가 정상이면 AssertionError가 발생
    None_expected = np.testing.assert_array_equal(ps_direction_actual, ps_direction_expected)

    # 별도 unittest framework 등에서 활용하려면 리턴값이 None인지 확인하면 됨
    test_result = 'OK' if None_expected is None else 'ERROR'

    print('Test Case #1:', test_result)


    """ Test Case #2 """

    a = a1
    b = b2

    ps_direction_actual = estimate_ps_direction(a, b)
    ps_direction_expected = [0, -1]

    # 테스트가 결과가 정상이면 AssertionError가 발생
    None_expected = np.testing.assert_array_equal(ps_direction_actual, ps_direction_expected)

    # 별도 unittest framework 등에서 활용하려면 리턴값이 None인지 확인하면 됨
    test_result = 'OK' if None_expected is None else 'ERROR'

    print('Test Case #2:', test_result)


    """ Test Case #3 """

    a = a2
    b = b1

    ps_direction_actual = estimate_ps_direction(a, b)
    ps_direction_expected = [0, 1]

    # 테스트가 결과가 정상이면 AssertionError가 발생
    None_expected = np.testing.assert_array_equal(ps_direction_actual, ps_direction_expected)

    # 별도 unittest framework 등에서 활용하려면 리턴값이 None인지 확인하면 됨
    test_result = 'OK' if None_expected is None else 'ERROR'

    print('Test Case #3:', test_result)


    """ Test Case #4 """

    a = a2
    b = b2

    ps_direction_actual = estimate_ps_direction(a, b)
    ps_direction_expected = [0, 1]

    # 테스트가 결과가 정상이면 AssertionError가 발생
    None_expected = np.testing.assert_array_equal(ps_direction_actual, ps_direction_expected)

    # 별도 unittest framework 등에서 활용하려면 리턴값이 None인지 확인하면 됨
    test_result = 'OK' if None_expected is None else 'ERROR'

    print('Test Case #4:', test_result)
    
    
if __name__ == '__main__':
    test_estimate_ps_direction()