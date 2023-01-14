class InitPosition():
    def __init__(self):
        self.initPositionMode = 'Absolute'
        self.pos = Position()
        self.rot = Rotation()        
        self.initLink = ''
        self.initLinkRatio = 0
        self.gear = 4
        self.vehicleSaveData = VehicleSaveData()

    def parse(self, json_data):
        self.initPositionMode = json_data['initPositionMode']

        self.pos = self.pos.parse(json_data['pos'])
        self.rot = self.rot.parse(json_data['rot'])

        self.initLink = json_data['initLink']
        self.initLinkRatio = json_data['initLinkRatio']
        self.gear = json_data['gear']
        
        if 'vehicleSaveData' in json_data:
            self.vehicleSaveData = self.vehicleSaveData.parse(json_data['vehicleSaveData'])

        return self

    def to_dict(self):
        dict = {
            'initPositionMode': self.initPositionMode,
            'pos': self.pos.to_dict(),
            'rot': self.rot.to_dict(),
            'initLink': self.initLink,
            'initLinkRatio': self.initLinkRatio,
            'gear': self.gear,
            'vehicleSaveData': self.vehicleSaveData.to_dict()
        }

        return dict

class Position():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def parse(self, json_data):
        self.x = json_data['x']
        self.y = json_data['y']
        self.z = json_data['z']

        return self

    def to_dict(self):
        dict = {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            '_x': str(round(self.x, 3)),
            '_y': str(round(self.y, 3)),
            '_z': str(round(self.z, 3))
        }

        return dict

class Rotation():
    def __init__(self):
        self.roll = 0
        self.pitch = 0
        self.yaw = 0

    def parse(self, json_data):
        self.roll = json_data['roll']
        self.pitch = json_data['pitch']
        self.yaw = json_data['yaw']

        return self

    def to_dict(self):
        dict = {
            'roll': self.roll,
            'pitch': self.pitch,
            'yaw': self.yaw
        }

        return dict

class Scale():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def parse(self, json_data):
        self.x = json_data['x']
        self.y = json_data['y']
        self.z = json_data['z']

        return self

    def to_dict(self):
        dict = {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            '_x': str(round(self.x, 3)),
            '_y': str(round(self.y, 3)),
            '_z': str(round(self.z, 3))
        }

        return dict

class Velocity():
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    def parse(self, json_data):
        self.x = json_data['x']
        self.y = json_data['y']
        self.z = json_data['z']

        return self

    def to_dict(self):
        dict = {
            'x': self.x,
            'y': self.y,
            'z': self.z
        }

        return dict

class LinkInfo():
    def __init__(self):
        self.link_idx = ''
        self.point_idx = 0

    def parse(self, json_data):
        self.link_idx = json_data['linkIdx']
        self.point_idx = json_data['pointIdx']

        return self

    def to_dict(self):
        dict = {
            'linkIdx': self.link_idx,
            'pointIdx': self.point_idx
        }

        return dict

class V2VUDPSessionInfo():
    def __init__(self):
        self.is_init = False
        self.v2v_config = V2VConfig()

    def parse(self, json_data):
        self.isInit = json_data['isInit']
        self.v2v_config = self.v2v_config.parse(json_data['v2vConfig'])

        return self

    def to_dict(self):
        dict = {
            'isInit': self.is_init,
            'v2vConfig': self.v2v_config.to_dict()
        }

        return dict

class V2VConfig():
    def __init__(self):
        self.hostIP = '127.0.0.1'
        self.Port = 5000
        self.receiveTimeout = 0
        self.BuffSize = 8196
        self.surroundVehiclePubTime = 100

    def parse(self, json_data):
        self.hostIP = json_data['hostIP']
        self.Port = json_data['Port']
        self.receiveTimeout = json_data['receiveTimeout']
        self.BuffSize = json_data['BuffSize']
        self.surroundVehiclePubTime = json_data['surroundVehiclePubTime']

        return self

    def to_dict(self):
        dict = {
            'hostIP': self.hostIP,
            'Port': self.Port,
            'receiveTimeout': self.receiveTimeout,
            'BuffSize': self.BuffSize,
            'surroundVehiclePubTime': self.surroundVehiclePubTime
        }

        return dict

class V2IInfo():
    def __init__(self):
        self.isAlive = False
        self.acceptIp = '127.0.0.1'
        self.acceptPort = 5000
        self.v2vIP = '127.0.0.1'

    def parse(self, json_data):
        self.isAlive = json_data['isAlive']
        self.acceptIp = json_data['acceptIp']
        self.acceptPort = json_data['acceptPort']
        self.v2vIP = json_data['v2vIP']

    def to_dict(self):
        dict = {
            'isAlive': self.isAlive,
            'acceptIp': self.acceptIp,
            'acceptPort': self.acceptPort,
            'v2vIP': self.v2vIP
        }

        return dict

class VehicleSaveData():
    def __init__(self):
        self.velocity = 0
        self.inputData = [0, 0, 0, 0, 0, 1, 4, 0, 0, 0]
        self.vehicle = Vehicle()
        self.wheels = [Wheel(), Wheel(), Wheel(), Wheel()]
        self.engine = Engine()
        self.gearbox = GearBox()
        self.lastVelocity = Velocity()

    def parse(self, json_data):
        if 'velocity' in json_data:
            self.velocity = json_data['velocity']

        if 'inputData' in json_data:
            self.inputData = json_data['inputData']

        if 'vehicle' in json_data:
            self.vehicle = self.vehicle.parse(json_data['vehicle'])

        if 'wheels' in json_data:
            self.wheels = []
            for wheel_item in json_data['wheels']:
                wheel = Wheel()
                wheel = wheel.parse(wheel_item)
                self.wheels.append(wheel)

        if 'engine' in json_data:
            self.engine = self.engine.parse(json_data['engine'])

        if 'gearbox' in json_data:
            self.gearbox = self.gearbox.parse(json_data['gearbox'])

        if 'lastVelocity' in json_data:
            self.lastVelocity = self.lastVelocity.parse(json_data['lastVelocity'])

        return self

    def to_dict(self):
        wheels = []

        for wheel_item in self.wheels:            
            wheels.append(wheel_item.to_dict())

        dict = {
            'velocity': self.velocity,
            'inputData': self.inputData,
            'vehicle': self.vehicle.to_dict(),
            'wheels': wheels,
            'engine': self.engine.to_dict(),
            'gearbox': self.gearbox.to_dict(),
            'lastVelocity': self.lastVelocity.to_dict()
        }

        return dict

class Vehicle():
    def __init__(self):
        self.time = 300
        self.lastVelocity = Velocity()
        self.lastImpactTime = 0.0

    def parse(self, json_data):
        self.time = json_data['time']
        self.lastVelocity = self.lastVelocity.parse(json_data['lastVelocity'])
        self.lastImpactTime = json_data['lastImpactTime']

        return self

    def to_dict(self):
        dict = {
            'time': self.time,
            'lastVelocity': self.lastVelocity.to_dict(),
            'lastImpactTime': self.lastImpactTime
        }

        return dict

class Wheel():
    def __init__(self):
        self.L = 0.0
        self.Tr = 0.0
        self.contactDepth = 0.0
        self.lastTireForce = TireForce()

    def parse(self, json_data):
        self.L = json_data['L']
        self.Tr = json_data['Tr']
        self.contactDepth = json_data['contactDepth']
        self.lastTireForce = self.lastTireForce.parse(json_data['lastTireForce'])

        return self

    def to_dict(self):
        dict = {
            'L': self.L,
            'Tr': self.Tr,
            'contactDepth': self.contactDepth,
            'lastTireForce': self.lastTireForce.to_dict()
        }

        return dict

class TireForce():
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def parse(self, json_data):
        self.x = json_data['x']
        self.y = json_data['y']

        return self

    def to_dict(self):
        dict = {
            'x': self.x,
            'y': self.y
        }

        return dict

class Engine():
    def __init__(self):
        self.L = 30.0
        self.Treaction = -30.0
        self.rpmLimiterActive = False
        self.rpmLimiterTime = 0.0
        self.tcsActivationTime = -1.0

    def parse(self, json_data):
        self.L = json_data['L']
        self.Treaction = json_data['Treaction']
        self.rpmLimiterActive = json_data['rpmLimiterActive']
        self.rpmLimiterTime = json_data['rpmLimiterTime']
        self.tcsActivationTime = json_data['tcsActivationTime']

        return self

    def to_dict(self):
        dict = {
            'L': self.L,
            'Treaction': self.Treaction,
            'rpmLimiterActive': self.rpmLimiterActive,
            'rpmLimiterTime': self.rpmLimiterTime,
            'tcsActivationTime': self.tcsActivationTime,
        }

        return dict

class GearBox():
    def __init__(self):
        self.L = 0.06
        self.manualGear = 0
        self.manualRatio = 0.0
        self.engaged = False
        self.lastEngagedTime = 0.0
        self.lastAutoShiftTime = 0.0
        self.vehicleMoving = False
        self.gearMode = 4
        self.automaticGear = 1
        self.automaticRatio = 3.0
        self.transition = False
        self.transitionStartedTime = 280
        self.fromGear = 2
        self.toGear = 1
        self.fromRatio = 2
        self.toRatio = 3
        self.transitionRatio = 3.6

    def parse(self, json_data):
        self.L = json_data['L']
        self.manualGear = json_data['manualGear']
        self.manualRatio = json_data['manualRatio']
        self.engaged = json_data['engaged']
        self.lastEngagedTime = json_data['lastEngagedTime']
        self.lastAutoShiftTime = json_data['lastAutoShiftTime']
        self.vehicleMoving = json_data['vehicleMoving']
        self.gearMode = json_data['gearMode']
        self.automaticGear = json_data['automaticGear']
        self.automaticRatio = json_data['automaticRatio']
        self.transition = json_data['transition']
        self.transitionStartedTime = json_data['transitionStartedTime']
        self.fromGear = json_data['fromGear']
        self.toGear = json_data['toGear']
        self.fromRatio = json_data['fromRatio']
        self.toRatio = json_data['toRatio']
        self.transitionRatio = json_data['transitionRatio']

        return self

    def to_dict(self):
        dict = {
            'L': self.L,
            'manualGear': self.manualGear,
            'manualRatio': self.manualRatio,
            'engaged': self.engaged,
            'lastEngagedTime': self.lastEngagedTime,
            'lastAutoShiftTime': self.lastAutoShiftTime,
            'vehicleMoving': self.vehicleMoving,
            'gearMode': self.gearMode,
            'automaticGear': self.automaticGear,
            'automaticRatio': self.automaticRatio,
            'transition': self.transition,
            'transitionStartedTime': self.transitionStartedTime,
            'fromGear': self.fromGear,
            'toGear': self.toGear,
            'fromRatio': self.fromRatio,
            'toRatio': self.toRatio,
            'transitionRatio': self.transitionRatio
        }

        return dict

class MapInfo():
    def __init__(self):
        self.mapName = ''
        self.eastOffset = 0
        self.northOffset = 0
        self.globalCoordinateSystem = ''
        self.scenarioCoordinateSystem = ''

    def parse(self, json_data):
        self.mapName = json_data['mapName']
        self.eastOffset = json_data['eastOffset']
        self.northOffset = json_data['northOffset']
        self.globalCoordinateSystem = json_data['globalCoordinateSystem']
        self.scenarioCoordinateSystem = json_data['scenarioCoordinateSystem']

        return self

    def to_dict(self):
        dict = {
            'mapName': self.mapName,
            'eastOffset': self.eastOffset,
            'northOffset': self.northOffset,
            'globalCoordinateSystem': self.globalCoordinateSystem,
            'scenarioCoordinateSystem': self.scenarioCoordinateSystem,
        }

        return dict