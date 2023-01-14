class shp_transform:
    def __init__(self):
        self.init = False
        
        # East (move 50 km)
        self.offset_x = 50 * 1000
        
        # North (move -30 km)
        self.offset_y = -30 * 1000
        
        # ALT (move 100m)
        self.offset_z = 10 
        print('init')

        # transform option
        self.transform_opt = 'rot_180'
        pass


    def manual_init(self, origin):
        self.origin_east = origin[0]
        self.origin_north = origin[1]
        self.init = True
    
    @staticmethod
    def offset(self, shp_obj, offset):
        for i in range(0, len(shp_obj.points)):
            shp_obj.points[i][0] += offset[0]
            shp_obj.points[i][1] += offset[1]
            shp_obj.z[i] += offset[2]

    def transform(self, shp_obj):
        if not self.init:
            self.origin_east = shp_obj.points[0][0]
            self.origin_north = shp_obj.points[0][1]
            self.origin_alt = shp_obj.points[0][2]
            self.init = True

        for i in range(0, len(shp_obj.points)):
            # shp_obj.points[i][0] -= self.origin_north
            
            temp = shp_obj.points[i]
            x = temp[0]
            y = temp[1]

            shp_obj.points[i] = [0, 0]

            if self.transform_opt == 'Original':
                shp_obj.points[i][0] = temp[0]
                shp_obj.points[i][1] = temp[1]

            elif self.transform_opt == 'Mirror_y':
                # y 방향 mirrored (north임)
                shp_obj.points[i][0] = temp[0]
                shp_obj.points[i][1] = -1 * (temp[1] - self.origin_north) + self.origin_north

            elif self.transform_opt == 'Mirror_x':        
                # x 방향 mirrored (east임)
                shp_obj.points[i][0] = -1 * (temp[0] - self.origin_east) + self.origin_east 
                shp_obj.points[i][1] = temp[1]
            
            elif self.transform_opt == 'rot_180':
                # 첫번째 node 기준으로 180 deg 회전
                import math
                theta = math.pi # 회전 각도
                c = math.cos(theta)
                s = math.sin(theta)
                
                # 우선 로컬 좌표로 이동시킨다
                x_local = x - self.origin_east
                y_local = y - self.origin_north

                # 회전 시킨다
                x_local2 = c * x_local - s * y_local
                y_local2 = s * x_local + c * y_local
                
                # 다시 글로벌 좌표로 이동시킨다
                x_new = x_local2 + self.origin_east
                y_new = y_local2 + self.origin_north

                # 오프셋 적용
                x_new2 = x_new + self.offset_x 
                y_new2 = y_new + self.offset_y
                shp_obj.points[i] = [x_new2, y_new2]

                # z는 별도로 오프셋 적용
                shp_obj.z[i] = shp_obj.z[i] + self.offset_z

            else:
                raise BaseException('Undefined transform_opt variable')

        return shp_obj