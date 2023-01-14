"""
Reference code was written in MATLAB: https://kr.mathworks.com/matlabcentral/fileexchange/45699-ll2utm-and-utm2ll
Refactored & Written into Python by MORAI Inc. 
"""

import coord_trans_utils as utils
import numpy as np


class CoordTrans_LL2TM:
    def __init__(self):
        self.is_param_init = False
        
        # rad to deg 
        self.D0 = 180.0 / np.pi

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

        self.C2 = utils.proj_coef_2(self.E1)

        self.is_param_init = True

    def ll2tm(self, lat, lon):
        p1 = lat / self.D0  # Phi = Latitude(rad)
        l1 = lon / self.D0  # Lambda = Longitude(rad)

        es = self.E1 * np.sin(p1)
        L = np.log( np.tan(np.pi/4.0 + p1/2.0) * 
                    np.power( ((1 - es) / (1 + es)), (self.E1 / 2)))

        z = np.complex(
            np.arctan(np.sinh(L) / np.cos(l1 - self.L0)),
            np.log(np.tan(np.pi / 4.0 + np.arcsin(np.sin(l1 - self.L0) / np.cosh(L)) / 2.0))
        )

        Z = self.N * self.C2[0] * z \
            + self.N * (self.C2[1] * np.sin(2.0 * z)
            + self.C2[2] * np.sin(4.0 * z)
            + self.C2[3] * np.sin(6.0 * z)
            + self.C2[4] * np.sin(8.0 * z))

        east = Z.imag + self.X0
        north = Z.real + self.YS
        return [east, north]


def CoordTrans_LL2TM_Test():
    """Test Case #1"""
    coord_trans = CoordTrans_LL2TM()
    coord_trans.set_tm_params(
        spheroid='GRS80',
        latitude_of_origin=38.0,
        central_meridian=127.5,
        scale_factor=0.9996,
        false_easting=1000000,
        false_northing=2000000)

    tm = coord_trans.ll2tm(
        lat=37.229222,
        lon=126.769125)
    east = tm[0]
    north = tm[1]

    print('east : {0:10.9f}'.format(east))
    print('north: {0:10.9f}'.format(north))


    # """Test Case #2"""
    # coord_trans = CoordTrans_LL2TM()
    # coord_trans.set_tm_params(
    #     spheroid='WGS84',
    #     latitude_of_origin=38.0,
    #     central_meridian=127.5,
    #     scale_factor=0.9996,
    #     false_easting=1000000,
    #     false_northing=2000000)

    # tm = coord_trans.ll2tm(
    #     lat=37.239636,
    #     lon=126.773466)
    # east = tm[0]
    # north = tm[1]
    
    # print('east : {0:10.2f}'.format(east))
    # print('north: {0:10.2f}'.format(north))

if __name__ == '__main__':
    CoordTrans_LL2TM_Test()