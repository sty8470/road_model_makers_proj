def surfline_kind_code_to_str(num, lane_prefix=True):
     
    if num == '501':
        retstr = 'Center'
    elif num == '503':
        retstr = 'Normal'
    elif num == '505':
        retstr = 'Border'
    elif num == '530':
        retstr = 'StopLine'
    elif num == '531':
        retstr = 'SafeArea'
    elif num == '515':
        retstr = 'NoParking'
    elif num == '599':
        retstr = 'Undef'
    else:
        retstr = 'Misc_' + num
        # raise BaseException('[ERROR] Undefined kind value')

    if lane_prefix:
        return 'Lane_' + retstr
    else:
        return retstr

def surfline_type_code_to_str(num):
    # Yellow/White - Single/Double - Solid/Broken

    if num == '111':
        return 'YSS'
    elif num == '112':
        return 'YSB'
    elif num == '113':
        return 'YellowUndef'
    elif num == '114':
        return 'YellowUndef'
    elif num == '121':
        return 'YDS'
    elif num == '122':
        return 'YDB'

    elif num == '211':
        return 'WSS'
    elif num == '212':
        return 'WSB'
    elif num == '213':
        return 'WhiteUndef'
    elif num == '214':
        return 'WhiteUndef'
    elif num == '221':
        return 'WDS'
    elif num == '222':
        return 'WDB'

    elif num == '999':
        return 'Undef'
    else:
        return 'Misc_' + num
        # raise BaseException('[ERROR] Undefined type value')