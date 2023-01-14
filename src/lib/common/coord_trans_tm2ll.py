"""
Reference code was written in MATLAB: https://kr.mathworks.com/matlabcentral/fileexchange/45699-ll2utm-and-utm2ll
Refactored & Written into Python by MORAI.Inc
"""

import coord_trans_utils as utils
import numpy as np


class CoordTrans_TM2LL:
    def __init__(self):
        self.is_param_init = False
        
        # rad to deg 
        self.D0 = 180.0 / np.pi

        self.max_iter = 100
        self.eps = 1e-11

    def set_tm_params(self,
        spheroid, latitude_of_origin, central_meridian, scale_factor,
        false_easting, false_northing):

        # spheroid
        if spheroid == "WGS84":
            self.A1 = 6378137.0
            self.F1 = 298.257223563
        elif spheroid == "GRS80":
            self.A1 = 6378137.0
            self.F1 = 298.257222101
        else:
            raise BaseException("Invalid spheroid is passed (your input = {})".format(spheroid))


        # 여기까지가 공통인 파라미터
        self.P0 = latitude_of_origin / 180.0 * np.pi
        self.L0 = central_meridian / 180.0 * np.pi # longitude of origin

        self.K0 = scale_factor

        self.X0 = false_easting
        self.Y0 = false_northing
        

        # 이 아래부터는 위에서 설정한 값으로 자동으로 계산된다.
        # Ellipsoid Eccentricity
        self.B1 = self.A1 * (1 - 1 / self.F1)
        self.E1 = np.sqrt((self.A1**2 - self.B1**2) / (self.A1**2))
        self.N = self.K0 * self.A1

        # Mercator Transverse Proj Params
        self.C0 = utils.proj_coef_0(self.E1) # self.YS를 계산하는데에만 사용함
        self.YS = self.Y0 - self.N * (
            self.C0[0] * self.P0
            + self.C0[1] * np.sin(2 * self.P0)
            + self.C0[2] * np.sin(4 * self.P0)
            + self.C0[3] * np.sin(6 * self.P0)
            + self.C0[4] * np.sin(8 * self.P0))

        self.C1 = utils.proj_coef_1(self.E1)

        self.is_param_init = True

    def tm2ll(self, east, north):
        # [STEP1] Calculate L & LS value
        zt = np.complex(
            (north - self.YS) / self.N / self.C1[0],
            (east - self.X0) / self.N / self.C1[0])
        z = zt - self.C1[1] * np.sin(2.0 * zt) - self.C1[2] * np.sin(4.0 * zt) - self.C1[3] * np.sin(6.0 * zt) - self.C1[4] * np.sin(8.0 * zt)

        L = z.real
        LS = z.imag

        # [STEP2] longitude is very simply calculated
        l = self.L0 + np.arctan(np.sinh(LS) / np.cos(L))
        lon = l * self.D0

        # [STEP3] initial value of latitude
        p = np.arcsin(np.sin(L) / np.cosh(LS))

        # [STEP4] calculates latitude from the isometric latitude
        L = np.log(np.tan(np.pi / 4.0 + p / 2.0))
        p = 2.0 * np.arctan(np.exp(L)) - np.pi / 2.0

        for n in range(self.max_iter):
            p_prev = p
            es = self.E1 * np.sin(p_prev)

            p = 2.0 * np.arctan(
                np.power(((1 + es) / (1 - es)), (self.E1 / 2.0)) * np.exp(L)) - np.pi / 2.0

            if np.abs(p - p_prev) <= self.eps:
                break

        # Assign
        lat = p * self.D0        
        return [lat, lon]


if __name__ == '__main__':

    """Test Case 01 (TM중부)"""
    coord_trans = CoordTrans_TM2LL()
    coord_trans.set_tm_params(
        spheroid='GRS80',
        latitude_of_origin=38.0,
        central_meridian=127.5,
        scale_factor=0.9996,
        false_easting=1000000,
        false_northing=2000000)

    ll = coord_trans.tm2ll(
        east=9.3516487166160834e+05,
        north=1.9147363928760968e+06
    )
    lat = ll[0]
    lon = ll[1]
    print('lat, lon = {:.6f}, {:.6f}'.format(lat, lon))


    """Test Case 02 (UTM52N)"""
    coord_trans = CoordTrans_TM2LL()
    coord_trans.set_tm_params(
        spheroid='WGS84',
        latitude_of_origin=0,
        central_meridian=129,
        scale_factor=0.9996,
        false_easting=500000,
        false_northing=0)

    ll = coord_trans.tm2ll(
        east=313477.29,
        north=4161595.38
    )
    lat = ll[0]
    lon = ll[1]
    print('lat, lon = {:.6f}, {:.6f}'.format(lat, lon))
