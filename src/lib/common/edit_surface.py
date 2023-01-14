import vtk


# TODO(sglee): Refactor This. MyEx03_vtkIdList에도 정의되어 있다.
def _flip_id_list(vtkIdList_obj):
    # 그냥 일반적인 파이썬 리스트로 변경한다
    pyList_obj = []
    for i in range(vtkIdList_obj.GetNumberOfIds()):
        pyList_obj.append(vtkIdList_obj.GetId(i))

    # 그리고 이 리스트를 뒤집는다
    pyList_obj.reverse()

    # 입력된 vtkIdList의 값을 다시 설정한다
    for i in range(vtkIdList_obj.GetNumberOfIds()):
        vtkIdList_obj.SetId(i, pyList_obj[i])


def _make_vtkCellArray_with_original_cell_plus_flipped_cell(vtkCellArray_obj):
    """
    참고: _make_vtkCellArray_with_each_cell_flipped와 구현이 거의 동일.
    핵심 차이점은 여기서는 새로운 vtkCellArray 객체에
    1) 기존 idList를 추가하고, 2) idList를 뒤집은 것을 추가하고
    를 반복하는데, _make_vtkCellArray_with_each_cell_flipped 에서는 1) 을 생략한다.
    :param vtkCellArray_obj:
    :return:
    """
    # 반환될 값
    new_vtkCellArray_obj = vtk.vtkCellArray()

    # vtkCellArray의 각 Cell을 받아 (vtkIdList 타입의 변수) 이를 뒤집고,
    # 이를 반환할 vtkCellArray에 넣어준다
    vtkCellArray_obj.InitTraversal()
    for i in range(0, vtkCellArray_obj.GetNumberOfCells()):
        # while True: # TODO(sglee): GetNumberOfCells 같은 것으로 무한 루프에 빠지지 않도록 해주자
        idList = vtk.vtkIdList()
        ret = vtkCellArray_obj.GetNextCell(idList)

        # while 루프 종료 조건
        if ret != 1:
            error_msg = '[ERROR] vtkCellArray_obj.GetNextCell(idList) has returned {}'.format(ret)
            print(error_msg)
            raise BaseException(error_msg)

        # 차이점: 기존의 idList를 추가한다. (따라서 기존 방향의 surface도 유지가된다)
        new_vtkCellArray_obj.InsertNextCell(idList)

        # 그 다음 뒤집은 idList를 만들어 새로운 CellArray에 추가한다
        idListFlip = vtk.vtkIdList()
        idListFlip.DeepCopy(idList)
        _flip_id_list(idListFlip)
        new_vtkCellArray_obj.InsertNextCell(idListFlip)

    return new_vtkCellArray_obj


def _make_vtkCellArray_with_each_cell_flipped(vtkCellArray_obj):
    """
    참고: _make_vtkCellArray_with_original_cell_plus_flipped_cell과 구현이 거의 동일.
    핵심 차이점은 여기서는 새로운 vtkCellArray 객체에 idList를 뒤집은 것만 반복 추가하는데,
    _make_vtkCellArray_with_each_cell_flipped 에서는 기존 idList 또한 추가한다.

    따라서 여기서는 각 Cell이 뒤집히기만 하는 것이고,
    _make_vtkCellArray_with_original_cell_plus_flipped_cell에서는 기존 것을 유지한 채로
    뒤집힌 것이 추가되는 것이다.
    :param vtkCellArray_obj:
    :return:
    """
    # 반환될 값
    new_vtkCellArray_obj = vtk.vtkCellArray()

    # vtkCellArray의 각 Cell을 받아 (vtkIdList 타입의 변수) 이를 뒤집고,
    # 이를 반환할 vtkCellArray에 넣어준다
    vtkCellArray_obj.InitTraversal()
    for i in range(0, vtkCellArray_obj.GetNumberOfCells()):
        # while True: # TODO(sglee): GetNumberOfCells 같은 것으로 무한 루프에 빠지지 않도록 해주자
        idList = vtk.vtkIdList()
        ret = vtkCellArray_obj.GetNextCell(idList)

        # while 루프 종료 조건
        if ret != 1:
            error_msg = '[ERROR] vtkCellArray_obj.GetNextCell(idList) has returned {}'.format(ret)
            print(error_msg)
            raise BaseException(error_msg)

        # 현재 받아온 idList를 뒤집고, 이를 새로운 CellArray에 추가한다
        _flip_id_list(idList)
        new_vtkCellArray_obj.InsertNextCell(idList)

    return new_vtkCellArray_obj


def flip_vtkPolyData_surface(vtkPolyData_obj):
    # vtkPolyData는 surface이고, 이 surface를 구성하는 각 Cell에 대한 정보를 담고 있는 배열을 받아온다
    vtkCellArray_obj = vtkPolyData_obj.GetPolys()

    # 이 배열의 각 배열의 index를 뒤집어서 새로운 vtkCellArray를 만든다
    new_vtkCellArray_obj = _make_vtkCellArray_with_each_cell_flipped(vtkCellArray_obj)

    # 새로 만든 vtkCellArray (각 Cell의 normal vector가 뒤집힌 것)으로 vtkPolyData_obj의 Cell 정보를 변경한다
    vtkPolyData_obj.SetPolys(new_vtkCellArray_obj)


def make_two_sided_vtkPolyData_surface(vtkPolyData_obj):
    # vtkPolyData는 surface이고, 이 surface를 구성하는 각 Cell에 대한 정보를 담고 있는 배열을 받아온다
    vtkCellArray_obj = vtkPolyData_obj.GetPolys()

    # 이 배열에 각 배열의 index를 뒤집은 배열을 넣은
    new_vtkCellArray_obj = _make_vtkCellArray_with_original_cell_plus_flipped_cell(vtkCellArray_obj)

    # 새로 만든 vtkCellArray (각 Cell의 normal vector가 뒤집힌 것)으로 vtkPolyData_obj의 Cell 정보를 변경한다
    vtkPolyData_obj.SetPolys(new_vtkCellArray_obj)