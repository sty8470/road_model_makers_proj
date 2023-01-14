import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(os.path.normpath(os.path.join(current_path, '../../')))

import coord_trans_utils as utils
import numpy as np

class CoordTrans_LL2UTM:
    def __init__(self, zone):
        self.zone = zone

        # rad to deg 
        self.D0 = 180 / np.pi

        # WGS84
        self.A1 = 6378137.0
        self.F1 = 298.257223563

        # Scale Factor
        self.K0 = 0.9996

        # False East & North 
        self.X0 = 500000
        if (zone > 0):
            self.Y0 = 0.0
        else:
            self.Y0 = 1e7

        # UTM origin latitude & longitude
        self.P0 = 0 / self.D0
        self.L0 = (6 * abs(zone) - 183) / self.D0

        # ellipsoid eccentricity
        self.B1 = self.A1 * (1 - 1 / self.F1)
        self.E1 = np.sqrt((self.A1**2 - self.B1**2) / (self.A1**2))
        self.N = self.K0 * self.A1

        # mercator transverse proj params
        self.C = np.zeros(5)
        self.C = utils.proj_coef_0(self.E1)

        self.YS = self.Y0 - self.N * (
            self.C[0] * self.P0
            + self.C[1] * np.sin(2 * self.P0)
            + self.C[2] * np.sin(4 * self.P0)
            + self.C[3] * np.sin(6 * self.P0)
            + self.C[4] * np.sin(8 * self.P0))

        self.C = utils.proj_coef_2(self.E1, )

    def ll2utm(self, lat, lon):
        p1 = lat / self.D0  # Phi = Latitude(rad)
        l1 = lon / self.D0  # Lambda = Longitude(rad)

        es = self.E1 * np.sin(p1)
        L = np.log( np.tan(np.pi/4.0 + p1/2.0) * 
                    np.power( ((1 - es) / (1 + es)), (self.E1 / 2)))

        z = np.complex(
            np.arctan(np.sinh(L) / np.cos(l1 - self.L0)),
            np.log(np.tan(np.pi / 4.0 + np.arcsin(np.sin(l1 - self.L0) / np.cosh(L)) / 2.0))
        )

        Z = self.N * self.C[0] * z \
            + self.N * (self.C[1] * np.sin(2.0 * z)
            + self.C[2] * np.sin(4.0 * z)
            + self.C[3] * np.sin(6.0 * z)
            + self.C[4] * np.sin(8.0 * z))

        east = Z.imag + self.X0
        north = Z.real + self.YS
        return east, north

def CoordTrans_LL2UTM_Test():

    """ Test Case 1 """
    obj = CoordTrans_LL2UTM(52)
    lat = 37.239636
    lon = 126.773466
    east, north = obj.ll2utm(lat, lon)

    print('east : {0:10.2f}'.format(east))
    print('north: {0:10.2f}'.format(north))
