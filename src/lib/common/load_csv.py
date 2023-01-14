import numpy as np

"""
np.genfromtxt를 사용하여 csv파일을 numpy의 structured array로 읽어오는 기능과, structured array를 사용하는데
필요한 기타 기능이 구현되어 있다.

csv 파일로 입력받는 데이터는 주로 column 기준으로 데이터가 정렬되어 있으므로, column 단위로 변수를 다루어야한다.

그런데, genfromtxt를 이용하여 반환되는 값은 2D array가 아닌 1D structured array 이고, 

이 타입은 indexing을 이용해서는 column 단위로 접근할 수 없다. 
  data 라는 변수가 있다고하면, 첫번째 column에 data[:][0]과 같은 식으로 접근이 불가능하다는 뜻이다.

대신, 구조체의 array이므로, '필드' 이름을 통해 column에 접근해야 한다. 다시 말해, 첫번쨰 column의 데이터는
모두 첫번째 필드로 저장되어 있고, 두번째 column의 데이터는 모두 두번째 필드로 저장되어 있다는 것이다.

column의 이름은 data.dtype.names에 tuple 형태로 저장되어 있어서, data.dtype.names[0], data.dtype.names[1],...
과 같이 접근할 수 있다. 기본은 'f0', 'f1', 'f2',... 이런식이다.
따라서 column 데이터를 얻으려면 data['f0'], data['f1'] 과 같이 입력되어야 하고, 코드로 전부 쓰면
data[data.dtype.name[0]]이 바로 첫번째 열 벡터이다.

그러므로 [열][행] 과 같은 형태로 접근하려면, 
data[data.dtype.name[열 번호]][행 번호] 이런 형태로 작성이 되어야 한다.

코드에서 이렇게 다 작성하면 가독성이 매우 떨어지므로, 아래 구현된 get_col 함수를 사용하도록 한다.
"""


def get_col(structured_array, col_num):
    """
    numpy.genfromtxt 함수를 이용하여 읽은 structured array의 각 column을 하나의 벡터처럼 접근할 수 있게 한다.
    """
    col_names = structured_array.dtype.names
    return structured_array[col_names[col_num]]


def read_csv_file_with_column_name(filename, delimiter=',', skip_header=0):
    return read_csv_file(filename, delimiter, names=True, skip_header=skip_header)


def read_csv_file_without_column_name(filename, delimiter=',', skip_header=0):
    return read_csv_file(filename, delimiter, names=None, skip_header=skip_header)


def read_csv_file(filename, delimiter=',', names=True, skip_header=0):
    """
    genfromtxt를 이용하여 csv파일을 읽고 structured array 형태로 반환한다.
    입력하는 csv파일에 각 column의 이름이 있는 경우 사용한다.
    [NOTE] 현재는 genfromtxt를 그대로 사용하고 있는데, 일반적인 환경에 좀 더 적합하게 기본값을 변경하였다. 향후 기능을 추가할 수도 있다.

    Parameters
    ----------
    filename : str
        읽을 csv 파일의 이름이다.
    delimiter : str, int, or sequence, optional
        읽을 csv 파일 내부에서 데이터를 구분하기 위해 사용되는 문자이다.
        주로 쉼표 (',') 또는 탭('\t')이 사용된다. 기본값은 쉼표이다.
        (genfromtxt의 디폴트는 None이며, None으로 설정 시 연속된 공백을 delimiter로 사용한다)
    names : {None, True, str, sequence}, optional
        파일 맨 앞의 skip_header만큼의 row를 무시한 다음 나타나는 첫 row가 각 column의 이름이면 skip_header를 True로 둔다.
        (True가 기본값) True로 설정하면, 반환된 데이터의 각 column에 column의 이름으로 접근이 가능하다.
        첫 row에 column의 이름이 없고 바로 데이터가 나올 경우, False 또는 None으로 설정한다.
    skip_header : int, optional
        읽을 csv 파일의 처음 몇 줄을 무시할 것인지를 나타낸다. csv 파일에 데이터가 있기 전 부가적인 정보가 기록되어 있으면
        이 parameter를 입력하여 해당 줄을 무시하도록 해야한다. 기본값은 0이다.

    Notes
    -----
    함수 입력 파일에 있는 각 열의 이름이 t, x, y 이라고 하고,
    함수 출력을 data라는 변수로 받았다고 하면,
    1) 열의 이름을 이용하여, 각 열에 접근이 가능하다.
       data['t'], data['x'], data['y'], ...
    2) 열의 이름을 열에 해당하는 index로 접근하고 싶을 경우, 다음으로 접근이 가능하다.
       data.dtype.names[0], data.dtype.names[1], ..

    References
    ----------
    https://docs.scipy.org/doc/numpy-1.14.0/reference/generated/numpy.genfromtxt.html
    """
    if names == False:
        names = None

    with open(filename) as f:
        data = np.genfromtxt(
            filename,
            dtype=None,
            delimiter=delimiter,
            skip_header=skip_header,
            usecols=None,
            names=names
        )
        return data