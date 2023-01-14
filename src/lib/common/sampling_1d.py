
def _make_insert_list(org_list, step, start_point):
    last_index = len(org_list) - 1
    next_point = start_point + 1
    assert next_point <= last_index, 'There is no next_point index in this input list'

    insert_list = list()
    # do
    i = 1
    temp = org_list[start_point] + step * i
    while temp < org_list[next_point]:
        insert_list.append(temp)
        i += 1
        temp = org_list[start_point] + step * i

    return insert_list


def _insert_list(org_list, insert_list, offset):
    next_point = offset + len(insert_list) # default value

    for i in range(len(insert_list)):
        org_list.insert(offset + i, insert_list[i])
    
    return org_list, next_point


def _insert_to_every_point(org_list, step):
    start_point = 0
    for i in range(len(org_list) - 1):
        print('')
        print('---------- i = {} ----------'.format(i))
        print('1) calling: _make_insert_list, start_point =', start_point)
        insert_list = _make_insert_list(org_list, step, start_point)
        print('2) output : insert_list =',insert_list)

        offset = start_point + 1
        print('3) org_list(input)  =', org_list)
        org_list, start_point = _insert_list(org_list, insert_list, offset)
        print('4) org_list(output) =', org_list)            
        print('5) start_point      =', start_point)

    return org_list


def test_make_insert_list():
    # test case : Normal
    a = [0, 1, 3, 5]
    insert_list_actl = _make_insert_list(a, 0.25, 2)

    insert_list_expt = [3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75]
    assert insert_list_actl == insert_list_expt,\
        'Error @ _make_insert_list : insert_list output is not correct'

    # test case : Error
    try:
        a = [0, 1, 3, 5]
        insert_list_actl = _make_insert_list(a, 0.25, 3)
    except AssertionError as e:
        pass
    except BaseException as e:
        raise Exception('Unexpected exception: ', e)


def test_insert_list():
    output_list_expt = [1, 1.25, 1.5, 1.75, 2, 3, 4]

    input_list = [1,2,3,4]
    start_point = 0

    # argument
    step = 0.25
    insert_list = _make_insert_list(input_list, step, start_point)    

    offset = start_point + 1
    output_list, next_point = _insert_list(input_list, insert_list, offset)

    assert output_list == output_list_expt, 'Error @ _insert_list : output_list is not correct'
    assert next_point == 4, 'Error @ _insert_list : next_point is not correct'


def test_insert_to_every_point():
    list_input = [0, 1, 2, 3]
    list_output_expt = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3]
    list_output_actl = _insert_to_every_point(list_input, 0.25)
    assert list_output_expt == list_output_actl, 'Error @ _insert_to_every_point (Case 1)'

    list_input = [0, 1, 2, 3, 4]
    list_output_expt = [0, 0.4, 0.8, 1, 1.4, 1.8, 2, 2.4, 2.8, 3, 3.4, 3.8, 4]
    list_output_actl = _insert_to_every_point(list_input, 0.40)
    assert list_output_expt == list_output_actl, 'Error @ _insert_to_every_point (Case 2)'

    list_input = [10, 12, 13, 15, 18]
    list_output_expt = [10, 11.5, 12, 13, 14.5, 15, 16.5, 18.0]
    list_output_actl = _insert_to_every_point(list_input, 1.5)
    assert list_output_expt == list_output_actl, 'Error @ _insert_to_every_point (Case 3)'

if __name__ == '__main__':
    test_make_insert_list()
    test_insert_list()
    test_insert_to_every_point()


