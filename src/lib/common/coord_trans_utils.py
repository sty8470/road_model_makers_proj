"""
Reference code was written in MATLAB: https://kr.mathworks.com/matlabcentral/fileexchange/45699-ll2utm-and-utm2ll
Refactored & Written into Python by MORAI.Inc
"""

import numpy as np

def polyval(p, p_size, x):
    if (p_size < 1):
        # ERROR Case
        return 0
    
    ret = 0 
    for i in range(0, p_size):
        ret += p[i] * (x ** (p_size - 1 - i))

    return ret

def proj_coef_0(e):
    c0_transverse_mercator = np.array([
        [ -175 / 16384.0, 0.0,  -5 / 2560.0, 0.0, -3 / 64.0 , 0.0, -1 / 4.0, 0.0, 1.0],
        [ -105 / 40960.0, 0.0, -45 / 1024.0, 0.0, -3 / 32.0 , 0.0, -3 / 8.0, 0.0, 0.0],
        [  525 / 16384.0, 0.0,  45 / 1024.0, 0.0, 15 / 256.0, 0.0,      0.0, 0.0, 0.0],
        [ -175 / 12288.0, 0.0, -35 / 3072.0, 0.0,        0.0, 0.0,      0.0, 0.0, 0.0],
        [ 315 / 131072.0, 0.0,          0.0, 0.0,        0.0, 0.0,      0.0, 0.0, 0.0]
    ])

    c_out = np.zeros(5)

    for i in range(0,5):
        c_out[i] = polyval(c0_transverse_mercator[i,:], 9, e)

    return c_out

def proj_coef_1(e):
    c0_transverse_mercator_reverse_coefficients = np.array([
        [    -175 / 16384.0, 0.0,   -5 / 256.0, 0.0,  -3 / 64.0, 0.0, -1 / 4.0, 0.0, 1.0 ],
        [       1 / 61440.0, 0.0,   7 / 2048.0, 0.0,   1 / 48.0, 0.0,  1 / 8.0, 0.0, 0.0 ],
        [    559 / 368640.0, 0.0,   3 / 1280.0, 0.0,  1 / 768.0, 0.0,      0.0, 0.0, 0.0 ],
        [    283 / 430080.0, 0.0, 17 / 30720.0, 0.0,        0.0, 0.0,      0.0, 0.0, 0.0 ],
        [ 4397 / 41287680.0, 0.0,          0.0, 0.0,        0.0, 0.0,      0.0, 0.0, 0.0 ]
    ])

    c_out = np.zeros(5)

    for i in range(0,5):
        c_out[i] = polyval(c0_transverse_mercator_reverse_coefficients[i,:], 9, e)

    return c_out

    
def proj_coef_2(e):
    c0_merdian_arc = np.array([
        [ -175 / 16384.0    , 0.0, -5 / 256.0  , 0.0,  -3 / 64.0, 0.0, -1 / 4.0, 0.0, 1.0 ],
        [ -901 / 184320.0   , 0.0, -9 / 1024.0 , 0.0,  -1 / 96.0, 0.0,  1 / 8.0, 0.0, 0.0 ],
        [ -311 / 737280.0   , 0.0, 17 / 5120.0 , 0.0, 13 / 768.0, 0.0,      0.0, 0.0, 0.0 ],
        [ 899 / 430080.0    , 0.0, 61 / 15360.0, 0.0,        0.0, 0.0,      0.0, 0.0, 0.0 ],
        [ 49561 / 41287680.0, 0.0,          0.0, 0.0,        0.0, 0.0,      0.0, 0.0, 0.0 ]
    ])

    c_out = np.zeros(5)

    for i in range(0,5):
        c_out[i] = polyval(c0_merdian_arc[i,:], 9, e)

    return c_out