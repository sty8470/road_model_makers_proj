import os
import datetime


def to_abs_path(current_path, rel_path):
    rel_path = os.path.join(current_path, rel_path)
    rel_path = os.path.normpath(rel_path)
    if not os.path.exists(rel_path):
        raise BaseException('path={} does not exist.'.format(rel_path))
    return rel_path


def win_path_to_unix_path(win_style_path):
    return win_style_path.replace('\\', '/')


def make_dir_if_not_exist(dir):
    """
    폴더 경로를 입력 받아, 해당 경로를 만든다 (recursively)
    만약 입력받은 경로에 확장자가 붙어있으면 파일 경로로 생각하고 오류를 발생시킨다.
    """
    _, filename = os.path.split(dir)
    if '.' in filename:
        # TODO(sglee): 여기 import 해결하기
        pass # 임시로 pass 사용함
        # raise MyException.MyException('PathUtils:make_dir_if_not_exist:invalid_arg',
        #                   '[ERROR] Path of a directory (or a folder) must be passed. Your input seems like a path of a file = {}'.format(dir))

    if not os.path.exists(dir):
        os.makedirs(dir) # recursive하게 os.mkdir을 호출한다


def make_dir_of_file_if_not_exist(filepath):
    """
    파일 경로를 입력 받아, 파일이 위치해야 할 폴더 경로를 만든다 (recursively)
    """
    dirpath, filename = os.path.split(filepath)
    make_dir_if_not_exist(dirpath)


def get_file_list(dirpath, append_to_dirpath=True):
    """
    :param dirpath: 체크하려는 directory 경로. 만약 상대경로로 입력할 경우, os.getcwd()에 대한 경로로 입력해야한다.
        상대경로를 입력할 때에는 맨 처음에 slash로 시작하지 않도록 주의한다. slash로 시작할 경우 Unix에서의 절대 경로로 인식하는 것 같다.
    :return:
    """
    # window 스타일로 넘겨줬으면 unix 스타일로 변경해준다
    dirpath = win_path_to_unix_path(dirpath)

    # 리스트를 받아온다. 이는 파일명 또는 폴더명이다.
    dir_and_file_list = os.listdir(dirpath)

    ret_list = []
    for dir_or_file in dir_and_file_list:
        # 전체 경로로 만들어준다 (그래야 os.path.isdir 등에 의해 체크가 가능하다)
        fulldir = dirpath + '/' + dir_or_file
        if not os.path.isdir(fulldir):

            # append_to_dir_path가
            # True 이면 -> 전체 경로를 반환하는 것
            # 아니면    -> 폴더 이름만 반환 (다른 곳에 사용 할 수 있도록
            if append_to_dirpath:
                ret_list.append(fulldir)
            else:
                ret_list.append(dir_or_file)

    return ret_list


def get_folder_list(dirpath, append_to_dirpath=True):
    """
    :param dirpath: 체크하려는 directory 경로. 만약 상대경로로 입력할 경우, os.getcwd()에 대한 경로로 입력해야한다.
        상대경로를 입력할 때에는 맨 처음에 slash로 시작하지 않도록 주의한다. slash로 시작할 경우 Unix에서의 절대 경로로 인식하는 것 같다.
    :return:
    """
    # window 스타일로 넘겨줬으면 unix 스타일로 변경해준다
    dirpath = win_path_to_unix_path(dirpath)

    # 리스트를 받아온다. 이는 파일명 또는 폴더명이다.
    dir_and_file_list = os.listdir(dirpath)

    ret_list = []
    for dir_or_file in dir_and_file_list:
        # 전체 경로로 만들어준다 (그래야 os.path.isdir 등에 의해 체크가 가능하다)
        fulldir = dirpath + '/' + dir_or_file
        if os.path.isdir(fulldir):

            # append_to_dir_path가
            # True 이면 -> 전체 경로를 반환하는 것
            # 아니면    -> 폴더 이름만 반환 (다른 곳에 사용 할 수 있도록
            if append_to_dirpath:
                ret_list.append(fulldir)
            else:
                ret_list.append(dir_or_file)

    return ret_list


def get_now_str(include_sec=False):
    return get_datetime_str(datetime.datetime.now(), include_sec)


def get_datetime_str(datetime_now, include_sec=False):
    """
    파일 이름에 사용할 수 있게 '날짜_시간'을 반환한다.
    이름을 이용해 시간 순으로 정렬될 수 있도록 AM12, PM12는 AM00, PM00으로 변환된다.
    """
    #str_now = datetime_now.strftime('%y%m%d_%p%I%M%S')
    if include_sec:
       str_now = datetime_now.strftime('%y%m%d_%p%I%M%S')
    else:
        str_now = datetime_now.strftime('%y%m%d_%p%I%M')

    if 'AM12' in str_now:
        str_now = str_now.replace('AM12', 'AM00')

    if 'PM12' in str_now:
        str_now = str_now.replace('PM12', 'PM00')

    return str_now


def get_valid_parent_path(abs_path, recursive_call_num_max=5, recursive_call_num=0):
    """
    현재 path를 기준으로, path가 존재하지 않을 경우 한 단계씩 상위 폴더로 이동하면서 valid한 폴더를 찾는다
    최대 recursvie call 호출 수를 넘어서면 그냥 False를 리턴한다
    """
    if not os.path.isabs(abs_path):
        raise BaseException('Error @ get_valid_parent_path: argument abs_path must be an absolute path (input: {})'.format(abs_path))

    if os.path.exists(abs_path):
        return True, abs_path   

    # 최대 recursive call 호출 수가 되었는데 현재 path가 존재하지 않으면, 
    # parent path를 더 검색하지 않고 False리턴
    if recursive_call_num == recursive_call_num_max:
        return False, ''
    
    else:
        parent_path = os.path.normpath(os.path.join(abs_path, '../'))
        recursive_call_num += 1
        return get_valid_parent_path(parent_path, recursive_call_num_max, recursive_call_num)


class DatetimeForFilename:
    def __init__(self):
        self._str_now = ''

    def set(self):
        self._str_now = get_now_str()

    def get(self):
        if self._str_now == '':
            # TODO(sglee): 여기에 아래를 message 라는 필드로 넘겨주도록 하는 방법 고민 또는 임의의 Exception 클래스를 만들어 활용
            raise Exception('[ERROR] You need to call DatetimeForFilename.set method before calling this!')

        return self._str_now

    def is_set(self):
        if self._str_now == '':
            return False
        else:
            return True

    def reset(self):
        self._str_now = ''



