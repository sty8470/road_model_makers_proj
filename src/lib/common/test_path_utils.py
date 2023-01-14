from path_utils import *

def get_folder_list_test():
    print("CHECK DIR #1 (using absolute dir)")
    check_dir = r'C:\Users\user\workspace\medi_projects\vmtk_proj_001'
    dir_list = get_folder_list(check_dir)
    for i in range(len(dir_list)):
        print('Folder #{:02d} = {}'.format(i, dir_list[i]))

    print("CHECK DIR #2 (using relative dir. w.r.t to os.getcwd = {})".format(os.getcwd()))
    check_dir = '../vmtk_proj_001'
    print('os.path.isabs(check_dir) = {} (False가 나와야 함. True가 나오면 테스트 입력값을 잘못 준 것'.format(
        os.path.isabs(check_dir)))
    dir_list = get_folder_list(check_dir)
    for i in range(len(dir_list)):
        print('Folder #{:02d} = {}'.format(i, dir_list[i]))


def get_file_list_test():
    print("CHECK DIR #1 (using absolute dir)")
    check_dir = r'C:\Users\user\workspace\medi_projects\vmtk_proj_001'
    filelist = get_file_list(check_dir)
    for i in range(len(filelist)):
        print('Folder #{:02d} = {}'.format(i, filelist[i]))

    print("CHECK DIR #2 (using relative dir. w.r.t to os.getcwd = {})".format(os.getcwd()))
    check_dir = '../vmtk_proj_001'
    print('os.path.isabs(check_dir) = {} (False가 나와야 함. True가 나오면 테스트 입력값을 잘못 준 것'.format(
        os.path.isabs(check_dir)))
    filelist = get_file_list(check_dir)
    for i in range(len(filelist)):
        print('Folder #{:02d} = {}'.format(i, filelist[i]))


def test_get_datetime_str():
    """
    get_datetime_str 대한 테스트
    """
    am12 = datetime.datetime(2018, 1, 31, 0, 10, 20, 0)
    print('Result: {}'.format('180131_AM001020' == get_datetime_str(am12)))

    pm12 = datetime.datetime(2018, 1, 31, 12, 10, 20, 0)
    print('Result: {}'.format('180131_PM001020' == get_datetime_str(pm12)))


def test_DatetimeForFilename():
    """
    DatetimeForFilename 에 대한 테스트
    """
    from time import sleep

    datetime_obj = DatetimeForFilename()
    try:
        datetime_obj.get()
    except BaseException as e:
        pass

    print('------ set here -----')
    datetime_obj.set()
    for i in range(5):
        print('datetime_obj.get() = {}'.format(datetime_obj.get()))
        sleep(0.5)

    print('------ set here -----')
    datetime_obj.set()
    for i in range(5):
        print('datetime_obj.get() = {}'.format(datetime_obj.get()))
        sleep(0.5)

    # print('------ reset here -----')
    datetime_obj.reset()
    try:
        datetime_obj.get()
    except BaseException as e:
        print('Exception')
        print(e)


if __name__ == '__main__':
    get_file_list_test()

