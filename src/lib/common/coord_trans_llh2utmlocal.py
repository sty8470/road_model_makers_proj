from coord_trans_ll2utm import CoordTrans_LL2UTM

class CoordTrans_LLH2UTMLocal:
    def __init__(self, zone, origin):
        self.ll2utm_obj = CoordTrans_LL2UTM(zone)
        self.origin = origin

    def llh2utmlocal(self, lat, lon, alt):
        east, north = self.ll2utm_obj.ll2utm(lat, lon)

        east = east - self.origin[0]
        north = north - self.origin[1]
        alt = alt - self.origin[2]
        return east, north, alt
